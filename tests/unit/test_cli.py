"""cua.cli: argument parsing, --input parsing, and main() as the only asyncio.run caller.

No browser, no LLM: every async entry point and package call is monkeypatched.
"""

from __future__ import annotations

import ast
import asyncio
from collections.abc import Coroutine
from pathlib import Path
from types import SimpleNamespace

import pytest

from cua import cli
from cua.schema import ReplayResult

SRC = Path(__file__).parents[2] / "src/cua"


def test_discover_args_and_defaults() -> None:
    a = cli.parse_args(["discover", "Log in and read a balance"])
    assert (a.command, a.goal, a.site, a.out) == (
        "discover",
        "Log in and read a balance",
        None,
        Path("artifacts"),
    )


def test_the_default_site_is_the_only_profile_in_configs() -> None:
    assert cli.default_site() == "parabank"


def test_several_profiles_need_an_explicit_site(tmp_path: Path) -> None:
    (tmp_path / "configs").mkdir()
    for name in ("a", "b"):
        (tmp_path / "configs" / f"{name}.yaml").write_text("")
    with pytest.raises(SystemExit, match="--site"):
        cli.default_site(tmp_path)


def test_discover_takes_site_and_out() -> None:
    a = cli.parse_args(["discover", "g", "--site", "other", "--out", "x/y"])
    assert (a.site, a.out) == ("other", Path("x/y"))


def test_replay_args_and_defaults() -> None:
    a = cli.parse_args(["replay", "artifacts/pay_bill.yaml"])
    assert (a.command, a.capability, a.inputs, a.site, a.evidence) == (
        "replay",
        Path("artifacts/pay_bill.yaml"),
        [],
        None,
        False,
    )


def test_replay_takes_repeated_inputs_and_evidence() -> None:
    argv = ["replay", "c.yaml", "--input", "amount=10", "--input", "to=1", "--evidence"]
    a = cli.parse_args(argv)
    assert (a.inputs, a.evidence) == (["amount=10", "to=1"], True)


def test_a_command_is_required() -> None:
    with pytest.raises(SystemExit):
        cli.parse_args([])


def test_there_is_no_eval_command() -> None:
    with pytest.raises(SystemExit):
        cli.parse_args(["eval", "c.yaml"])


def test_inputs_split_on_the_first_equals_only() -> None:
    assert cli.parse_inputs(["amount=10", "memo=a=b", "empty="]) == {
        "amount": "10",
        "memo": "a=b",
        "empty": "",
    }


@pytest.mark.parametrize("bad", ["amount", "=10", " =1"])
def test_a_bad_input_is_refused(bad: str) -> None:
    with pytest.raises(ValueError, match="key=value"):
        cli.parse_inputs([bad])


def _record_run(monkeypatch: pytest.MonkeyPatch) -> list[str]:
    names: list[str] = []
    real = asyncio.run

    def run(coro: Coroutine[object, object, object]) -> object:
        names.append(coro.cr_code.co_name)
        return real(coro)

    monkeypatch.setattr(cli.asyncio, "run", run)
    return names


def test_main_runs_discover_through_asyncio_run(monkeypatch: pytest.MonkeyPatch) -> None:
    seen: list[tuple[object, ...]] = []

    async def discover(goal: str, site: str, out: Path) -> Path:
        seen.append((goal, site, out))
        return out / "x.yaml"

    names = _record_run(monkeypatch)
    monkeypatch.setattr(cli, "discover", discover)
    assert cli.main(["discover", "read a balance", "--out", "o"]) == 0
    assert names == ["discover"]
    assert seen == [("read a balance", "parabank", Path("o"))]


def _result(status: str) -> ReplayResult:
    return ReplayResult(status, {}, [])


@pytest.mark.parametrize(("status", "code"), [("SUCCESS", 0), ("FAILED", 1)])
def test_main_runs_replay_through_asyncio_run(
    monkeypatch: pytest.MonkeyPatch, status: str, code: int
) -> None:
    seen: list[tuple[object, ...]] = []

    async def run_replay(cap: Path, inputs: dict[str, str], site: str, evidence: bool) -> object:
        seen.append((cap, inputs, site, evidence))
        return _result(status)

    names = _record_run(monkeypatch)
    monkeypatch.setattr(cli, "run_replay", run_replay)
    assert cli.main(["replay", "c.yaml", "--input", "amount=10", "--evidence"]) == code
    assert names == ["run_replay"]
    assert seen == [(Path("c.yaml"), {"amount": "10"}, "parabank", True)]


def test_a_bad_input_exits_before_any_browser(monkeypatch: pytest.MonkeyPatch) -> None:
    names = _record_run(monkeypatch)
    with pytest.raises(SystemExit):
        cli.main(["replay", "c.yaml", "--input", "oops"])
    assert names == []


def test_only_main_calls_asyncio_run() -> None:
    callers = []
    for path in SRC.rglob("*.py"):
        tree = ast.parse(path.read_text())
        for fn in ast.walk(tree):
            if not isinstance(fn, ast.FunctionDef | ast.AsyncFunctionDef | ast.Module):
                continue
            for node in ast.walk(fn):
                if isinstance(node, ast.Call) and ast.unparse(node.func) == "asyncio.run":
                    callers.append((path.name, getattr(fn, "name", "<module>")))
    assert set(callers) == {("cli.py", "main"), ("cli.py", "<module>")}


# --- wiring: the same calls, in the same order, as the notebooks ------------------------------


class _Session(SimpleNamespace):
    async def goto(self, url: str) -> None:
        self.calls.append(("goto", url))


def _fake_session(calls: list[tuple[object, ...]]) -> SimpleNamespace:
    page = _Session(calls=calls)

    async def close() -> None:
        calls.append(("close",))

    async def stop() -> None:
        calls.append(("stop",))

    return SimpleNamespace(
        page=page, context=SimpleNamespace(close=close), pw=SimpleNamespace(stop=stop)
    )


def _patch_session(monkeypatch: pytest.MonkeyPatch, calls: list[tuple[object, ...]]) -> object:
    session = _fake_session(calls)

    async def open_session(site: object, cfg: object, **kw: object) -> object:
        calls.append(("open_session", site, kw))
        return session

    async def check_viewport(s: object) -> None:
        calls.append(("check_viewport",))

    monkeypatch.setattr(cli, "load_site", lambda name: SimpleNamespace(name=name, start_url="U"))
    monkeypatch.setattr(cli, "open_session", open_session)
    monkeypatch.setattr(cli, "check_viewport", check_viewport)
    monkeypatch.setattr(cli, "secret_values", lambda site: {"username": ""})
    return session


def test_discover_wires_like_the_notebook(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    calls: list[tuple[object, ...]] = []
    _patch_session(monkeypatch, calls)
    run = SimpleNamespace(goal="g", log=["ev"])
    ctx = SimpleNamespace(run=run)
    model = SimpleNamespace(model="M")

    async def attach(session: object, cfg: object, secrets: object) -> object:
        calls.append(("attach", secrets))
        return ctx

    async def run_goal(c: object, agent: object, goal: str) -> str:
        calls.append(("run_goal", agent, goal))
        return "done"

    async def describe(goal: str, log: object, m: object) -> str:
        calls.append(("describe", goal, m))
        return "META"

    monkeypatch.setattr(cli, "discovery_attach", attach)
    monkeypatch.setattr(cli, "make_chat_model", lambda kind: model)
    monkeypatch.setattr(cli, "build_agent", lambda c, m: "AGENT")
    monkeypatch.setattr(cli, "run_goal", run_goal)
    monkeypatch.setattr(cli, "describe", describe)
    monkeypatch.setattr(cli, "check_savable", lambda log: None)
    monkeypatch.setattr(cli, "build_capability", lambda log, meta: "CAP")
    monkeypatch.setattr(cli, "crops_for", lambda log, cap: {})
    monkeypatch.setattr(cli, "save_artifact", lambda cap, crops, out: out / "c.yaml")
    monkeypatch.setattr(
        cli,
        "save_discovery_evidence",
        lambda c, out, capability, model: calls.append(("evidence", capability, model)) or out,
    )
    path = asyncio.run(cli.discover("g", "parabank", tmp_path))
    assert path == tmp_path / "c.yaml"
    assert [c[0] for c in calls] == [
        "open_session",
        "goto",
        "check_viewport",
        "attach",
        "run_goal",
        "describe",
        "evidence",
        "close",
        "stop",
    ]
    assert calls[0][2] == {"profile_prefix": "cua-discovery-"}
    assert calls[4][1:] == ("AGENT", "g")
    assert calls[6][1:] == (tmp_path / "c.yaml", "M")


def test_replay_wires_like_the_notebook(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[tuple[object, ...]] = []
    _patch_session(monkeypatch, calls)

    async def attach(session: object, site: object, cfg: object) -> object:
        calls.append(("attach",))
        return "CTX"

    async def replay(ctx: object, path: Path, inputs: dict[str, str]) -> ReplayResult:
        calls.append(("replay", path, inputs))
        return _result("SUCCESS")

    monkeypatch.setattr(cli, "replay_attach", attach)
    monkeypatch.setattr(cli, "replay", replay)
    monkeypatch.setattr(
        cli,
        "save_replay_evidence",
        lambda ctx, r, cap, out: calls.append(("evidence", cap, out)) or out,
    )
    result = asyncio.run(cli.run_replay(Path("c.yaml"), {"a": "1"}, "parabank", True))
    assert result.status == "SUCCESS"
    assert [c[0] for c in calls] == [
        "open_session",
        "attach",
        "replay",
        "evidence",
        "close",
        "stop",
    ]
    assert calls[0][2] == {"profile_prefix": "cua-replay-"}
    assert calls[2][1:] == (Path("c.yaml"), {"a": "1"})
    assert calls[3][1:] == (Path("c.yaml"), Path("evidence/replay"))


def test_replay_without_evidence_saves_none(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[tuple[object, ...]] = []
    _patch_session(monkeypatch, calls)

    async def attach(*a: object) -> object:
        return "CTX"

    async def replay(*a: object) -> ReplayResult:
        return _result("SUCCESS")

    monkeypatch.setattr(cli, "replay_attach", attach)
    monkeypatch.setattr(cli, "replay", replay)
    monkeypatch.setattr(cli, "save_replay_evidence", lambda *a: calls.append(("evidence",)))
    asyncio.run(cli.run_replay(Path("c.yaml"), {}, "parabank", False))
    assert ("evidence",) not in calls


def test_a_run_that_cannot_be_saved_prints_why_and_never_asks_the_model(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Live: a take-over run crashed with a traceback after a wasted describe() call."""
    asked: list[str] = []

    async def describe(*_: object) -> None:
        asked.append("describe")

    monkeypatch.setattr(cli, "describe", describe)
    log = [{"tool": "start", "args": {}, "result": "", "url": "", "point": None},
           {"tool": "take_over", "args": {}, "result": "handed back", "url": "", "point": None,
            "recordable": False}]
    assert asyncio.run(cli._save(log, "g", object(), tmp_path)) is None   # type: ignore[arg-type]
    out = capsys.readouterr().out
    assert "not saved: a human take-over happened" in out
    assert "Traceback" not in out
    assert asked == []                                 # refused before the model was asked
