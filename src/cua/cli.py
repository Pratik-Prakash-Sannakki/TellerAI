"""The ``cua`` command: ``cua discover "<goal>"``, ``cua replay <capability.yaml>`` and
``cua eval <capability.yaml> --runs N`` (replay N times in one session, report stability).

Wired exactly like the two notebooks (``notebooks/discovery/discovery.py``,
``notebooks/replay/replay.py``): one browser session per command, closed at the end.
:func:`main` is the only place in the package that calls ``asyncio.run``; everything else is async.
"""

from __future__ import annotations

import argparse
import asyncio
from collections.abc import Sequence
from pathlib import Path

import yaml
from langchain_core.language_models import BaseChatModel
from pydantic import JsonValue

from cua.browser import Session, check_viewport, close_session, open_session
from cua.config import (
    BrowserConfig,
    DiscoveryConfig,
    ReplayConfig,
    _repo_root,
    load_site,
    secret_values,
)
from cua.discovery.agent.build import build_agent
from cua.discovery.evidence import save_evidence as save_discovery_evidence
from cua.discovery.goal import run_goal
from cua.discovery.recorder import (
    NotSaved,
    build_capability,
    check_savable,
    crops_for,
    describe,
    save_artifact,
)
from cua.discovery.wiring import attach as discovery_attach
from cua.eval import (
    EvalReport,
    missing_inputs,
    render,
    run_rows,
    save_report,
    sends_data,
    summarize,
)
from cua.evidence import run_info
from cua.llm import make_chat_model
from cua.replay.engine import replay
from cua.replay.evidence import save_evidence as save_replay_evidence
from cua.replay.wiring import attach as replay_attach
from cua.schema import Capability, Event, ReplayResult

EVIDENCE = Path("evidence")
SITE_HELP = "site profile name in configs/ (default: the only one there)"


def default_site(root: Path | None = None) -> str:
    """The site profile to use without ``--site``: the only ``configs/*.yaml`` there is."""
    names = sorted(p.stem for p in ((root or _repo_root()) / "configs").glob("*.yaml"))
    if len(names) != 1:
        raise SystemExit(f"cua: pass --site, one of: {', '.join(names) or 'none found'}")
    return names[0]


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(prog="cua", description="Discover or replay a capability.")
    sub = parser.add_subparsers(dest="command", required=True)
    d = sub.add_parser("discover", help="let the agent learn a goal and save it as a capability")
    d.add_argument("goal", help="what to do, in plain words")
    d.add_argument("--site", help=SITE_HELP)
    d.add_argument("--out", type=Path, default=Path("artifacts"), help="where to save the YAML")
    r = sub.add_parser("replay", help="run a saved capability, no LLM")
    r.add_argument("capability", type=Path, help="the capability YAML")
    r.add_argument(
        "--input", dest="inputs", action="append", default=[], metavar="KEY=VALUE",
        help="an input value (repeatable); missing inputs are asked in the control window",
    )  # fmt: skip
    r.add_argument("--site", help=SITE_HELP)
    r.add_argument("--evidence", action="store_true", help="save evidence under evidence/replay")
    e = sub.add_parser("eval", help="replay a capability N times and report its stability")
    e.add_argument("capability", type=Path, help="the capability YAML")
    e.add_argument("--runs", type=_positive, default=3, help="how many replays (default 3)")
    e.add_argument(
        "--input", dest="inputs", action="append", default=[], metavar="KEY=VALUE",
        help="an input value (repeatable); every input is required, so the runs are unattended",
    )  # fmt: skip
    e.add_argument("--site", help=SITE_HELP)
    e.add_argument("--evidence", action="store_true", help="also save each run's replay evidence")
    return parser.parse_args(argv)


def _positive(text: str) -> int:
    n = int(text)
    if n < 1:
        raise argparse.ArgumentTypeError(f"--runs must be 1 or more, got {n}")
    return n


def parse_inputs(pairs: Sequence[str]) -> dict[str, str]:
    """``["amount=10"]`` -> ``{"amount": "10"}``. Splits on the first ``=`` only."""
    out: dict[str, str] = {}
    for pair in pairs:
        key, eq, value = pair.partition("=")
        if not eq or not key.strip():
            raise ValueError(f"--input must be key=value, got {pair!r}")
        out[key.strip()] = value
    return out


async def _close(session: Session) -> None:
    await close_session(session)


async def discover(goal: str, site_name: str, out: Path) -> Path | None:
    """The discovery notebook's cells: setup, run, save artifact, evidence."""
    site = load_site(site_name)
    session = await open_session(site, BrowserConfig(), profile_prefix="cua-discovery-")
    path: Path | None = None
    try:
        await session.page.goto(site.start_url)
        await check_viewport(session)
        ctx = await discovery_attach(session, DiscoveryConfig(), secret_values(site))
        model = make_chat_model("sonnet")
        try:
            agent = build_agent(ctx, model)  # a CompiledStateGraph; run_goal types it as Agent
            print(await run_goal(ctx, agent, goal))  # type: ignore[arg-type]
            path = await _save(ctx.run.log, ctx.run.goal, model, out)
        finally:  # evidence after any run, successful or not
            folder = save_discovery_evidence(
                ctx, EVIDENCE / "discovery", capability=path, model=getattr(model, "model", None)
            )
            print("evidence:", folder)
    finally:
        await _close(session)
    return path


async def _save(log: list[Event], goal: str, model: BaseChatModel, out: Path) -> Path | None:
    """Save the run as a capability, or say plainly why not. Checked before the model is asked."""
    try:
        check_savable(log)
        cap = build_capability(log, await describe(goal, log, model))
    except NotSaved as e:
        print(f"not saved: {e}")
        print("The run's evidence is still written below. Fix the cause and run again.")
        return None
    path = save_artifact(cap, crops_for(log, cap), out)
    print("saved:", path)
    return path


def _print_result(cap: Path, result: ReplayResult) -> None:
    print("capability:", cap)
    print(
        "status:", result.summary, result.reason, f"| recoveries: {result.recoveries}",
        f"| cleanup: {result.cleanup or 'none'}",
    )  # fmt: skip
    print(result.outputs_line)
    for row in result.drift:
        print({k: v for k, v in row.items() if k != "shots"})


async def run_replay(
    cap: Path, inputs: dict[str, str], site_name: str, evidence: bool
) -> ReplayResult:
    """The replay notebook's cells: setup, run, evidence (when asked)."""
    site = load_site(site_name)
    session = await open_session(site, BrowserConfig(), profile_prefix="cua-replay-")
    try:
        ctx = await replay_attach(session, site, ReplayConfig())
        result = await replay(ctx, cap, inputs)
        _print_result(cap, result)
        if evidence:
            print("evidence:", save_replay_evidence(ctx, result, cap, EVIDENCE / "replay"))
        return result
    finally:
        await _close(session)


async def run_eval(
    cap: Path, inputs: dict[str, str], site_name: str, runs: int, evidence: bool
) -> EvalReport:
    """Replay ``runs`` times in ONE browser session, re-attaching per run like ``run_replay``."""
    site = load_site(site_name)
    session = await open_session(site, BrowserConfig(), profile_prefix="cua-eval-")
    results: list[ReplayResult] = []
    masks: list[set[str]] = []
    info: dict[str, JsonValue] = {}
    try:
        for n in range(1, runs + 1):
            ctx = await replay_attach(session, site, ReplayConfig())
            result = await replay(ctx, cap, inputs)
            print(f"run {n}/{runs}:", result.summary)
            results.append(result)
            masks.append(set(ctx.last.values) | {v for v in ctx.secrets.values() if v})
            info = run_info(None, None, (ctx.bcfg, ctx.cfg), ctx.site)
            if evidence:
                print("evidence:", save_replay_evidence(ctx, result, cap, EVIDENCE / "replay"))
    finally:
        await _close(session)
    report = summarize(results)
    print(render(report))
    folder = save_report(report, run_rows(results, masks), _cap_name(cap), EVIDENCE / "eval", info)
    print("eval report:", folder)
    return report


def _cap_name(cap: Path) -> str:
    return str(yaml.safe_load(cap.read_text()).get("name", cap.stem))


def _load_cap(path: Path) -> Capability:
    data = yaml.safe_load(path.read_text())
    data.pop("outcomes", None)  # replay's own optional key, as the loader does
    return Capability.model_validate(data)


def check_eval(path: Path, inputs: dict[str, str]) -> None:
    """Refuse before any browser when an input is missing; warn when each run will hit gates."""
    cap = _load_cap(path)
    if missing := missing_inputs(cap, inputs):
        raise SystemExit(
            f"cua eval: eval needs every input via --input so the runs are unattended: "
            f"missing {missing}"
        )
    if sends_data(cap):
        print("warning: this capability sends data; each run will stop at the two gates "
              "for your approval")  # fmt: skip


def main(argv: Sequence[str] | None = None) -> int:
    """Parse the command line and run it. The only ``asyncio.run`` in the package."""
    args = parse_args(argv)
    site = args.site or default_site()
    if args.command == "discover":
        asyncio.run(discover(args.goal, site, args.out))
        return 0
    try:
        inputs = parse_inputs(args.inputs)
    except ValueError as e:
        raise SystemExit(f"cua {args.command}: {e}") from e
    if args.command == "eval":
        check_eval(args.capability, inputs)
        report = asyncio.run(run_eval(args.capability, inputs, site, args.runs, args.evidence))
        return 0 if report.all_success else 1
    result = asyncio.run(run_replay(args.capability, inputs, site, args.evidence))
    return 0 if result.status == "SUCCESS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
