"""The replay engine: walk the steps, judge each (R17), retry a failed check once (never a send or a
secret), a human rescues or stops it, cleanup always runs, and the run is wiped after (R7).

Moved from notebooks/replay/replay.py 440-449 (``RAW_ERROR``/``error_page``) and 1371-1562
(``login_steps`` ... ``replay``). Bodies unchanged; globals -> ``ctx`` (first parameter). The step
functions are looked up as ``steps.ACTIONS`` / ``steps.find`` / ``steps.shows`` at call time, and
``rescue``/``open_start`` likewise, so a test can swap one (as the notebook tests swapped
globals). ``LAST_RUN`` is ``ctx.last`` (see :mod:`cua.replay.run`).
"""

from __future__ import annotations

import re
from dataclasses import replace
from pathlib import Path

from pydantic import JsonValue, ValidationError

from cua.replay import loader, steps
from cua.replay import rescue as rescue_mod
from cua.replay.context import Ctx, wipe
from cua.replay.loader import (
    fill,
    given_inputs,
    load_capability,
    load_outcomes,
    secret_name,
    seen_outcome,
)
from cua.replay.wiring import look, snap
from cua.safety.redact import hide_secrets, norm
from cua.schema import Capability, ReplayResult, Step, Stop
from cua.vision import decode

Drift = list[dict[str, JsonValue]]
RAW_ERROR = re.compile(r'^\s*\{\s*"title"\s*:|"status"\s*:\s*[45]\d\d')


def error_page(ctx: Ctx, after: str) -> Stop | None:
    """R17 FAILED before any outcome rule: an HTTP error status, or a raw JSON error body."""
    http = ctx.run.http
    if http and http[0] >= 400:  # noqa: PLR2004
        return Stop("FAILED", f"page returned HTTP {http[0]}", "an HTTP 2xx page", http[1])
    if RAW_ERROR.search(after):
        return Stop("FAILED", "page is a raw error response", "a normal page", after[:200])
    return None


READS = ("extract", "extract_table", "extract_options")
SITE_ACTION = {"extract_options": "extract"}  # a dropdown's options are a read, like extract


def action_allowed(ctx: Ctx, step: Step) -> Stop | None:
    """Assignment 3.4: a step whose action type the site does not allow FAILS before acting."""
    if SITE_ACTION.get(step.action, step.action) in ctx.site.allowed_actions:
        return None
    return Stop("FAILED", f"action '{step.action}' is not in allowed_actions")


def starts_with_login(cap: Capability) -> bool:
    """A secret is typed before the first click: the capability logs in itself."""
    for s in cap.steps:
        if s.action == "click":
            return False
        if s.action == "type" and secret_name(s.value):
            return True
    return False


def login_steps(cap: Capability) -> list[Step]:
    """The steps up to and including the first click, when a secret is typed before it."""
    head = next((cap.steps[: n + 1] for n, s in enumerate(cap.steps) if s.action == "click"), [])
    return head if starts_with_login(cap) else []


def login_came_back(cap: Capability, i: int, before: str, after: str) -> bool:
    """Mid-run, the login form's label appeared with this step: the site logged the run out."""
    login = login_steps(cap)
    anchor = login[0].target.anchor if login else None  # type: ignore[union-attr]
    label = norm(anchor.label) if anchor else ""
    return (
        i >= len(login) > 0 and bool(label) and label not in norm(before) and label in norm(after)
    )


async def judge(  # noqa: PLR0913 (constraints allow 6)
    ctx: Ctx, i: int, before: str, cap: Capability, crops: Path | None, *, drift: Drift
) -> bool:
    """R17 after a step. BUSINESS_OUTCOME / FAILED stop; RECOVER logs in again once. True =
    retry."""
    run = ctx.run
    after = run.look.text if run.look else ""
    if err := error_page(ctx, after):  # BUSINESS_OUTCOME only ever comes from a normal page
        raise err
    rule = seen_outcome(before, after, run.outcomes)
    if rule is None and login_came_back(cap, i, before, after):
        rule = {"text": "login page", "status": "RECOVER", "meaning": "the site logged the run out"}
    if rule is None:
        return False
    if rule["status"] == "RECOVER" and not run.sent and run.recoveries == 0:
        run.recoveries += 1
        drift.append({"step": i, "action": "relogin", "rung": "recover", "outcome": rule["text"]})
        for j, s in enumerate(login_steps(cap)):
            await run_step(ctx, j, s, cap, crops, drift=drift)
        run.step, run.action = i, cap.steps[i].action
        return True
    status = "BUSINESS_OUTCOME" if rule["status"] == "BUSINESS_OUTCOME" else "FAILED"
    raise Stop(status, rule["meaning"], f"step {i + 1} without '{rule['text']}'", after[:200])


async def run_step(  # noqa: PLR0913 (constraints allow 6)
    ctx: Ctx, i: int, step: Step, cap: Capability, crops: Path | None, *, drift: Drift
) -> None:
    run = ctx.run
    run.step, run.action = i, step.action
    if refused := action_allowed(ctx, step):
        raise refused
    attempt = 0
    while attempt < 2:  # noqa: PLR2004
        attempt += 1
        target = getattr(step, "target", None)
        if (hit := await steps.find(ctx, target, crops) if target else (None, "-")) is None:
            break
        run.sent, run.verdict, run.rung = False, "", hit[1]
        before = run.look.text if run.look else ""
        ok = await steps.ACTIONS[step.action](ctx, step, hit[0], cap)  # type: ignore[arg-type]
        drift.append(
            {
                "step": i,
                "action": step.action,
                "rung": hit[1],
                "point": hit[0],  # type: ignore[dict-item]
                "attempt": attempt,
                "checked": ok,
            }
        )
        status = run.verdict.split(":")[0]
        if status in ("STUCK", "DECLINED"):
            raise Stop(status, run.verdict)
        if await judge(ctx, i, before, cap, crops, drift=drift):
            attempt -= 1  # the re-login does not use up the step's retry
            continue
        if ok:
            return
        if run.sent or secret_name(getattr(step, "value", "")):
            break  # R15/D26: a send is never retried; R5: nor a secret
        await look(ctx)
    why = "target not found" if hit is None else "the step's check failed"
    evidence = await rescue_mod.rescue(ctx, i, step, why)
    drift.append({"step": i, "action": step.action, "rung": "human", **evidence})


def took_over_to_checkpoint(ctx: Ctx, i: int, cap: Capability, before: str) -> bool:
    """Step i ended in a take-over, and the human went on to the final screen: the checkpoint
    text is on screen now and was not before the take-over."""
    run = ctx.run
    want = norm(fill(cap.checkpoint, run.values))
    last = run.human[-1] if run.human else {}
    helped = last.get("step") == i and last.get("kind") != "option"  # a choice is no take-over
    return (
        helped and want not in norm(before) and run.look is not None and want in norm(run.look.text)
    )


def is_cleanup(step: Step) -> bool:
    return bool(getattr(step, "cleanup", False))


def read_only_done(ctx: Ctx, cap: Capability, missing: list[str]) -> bool:
    """R17: a read-only run whose last main step read the last output, and every output was read.
    Its checkpoint was picked after the cleanup (e.g. the login page after Log Out): accept it."""
    main = [s for s in cap.steps if not is_cleanup(s)]
    last_reads = bool(main) and main[-1].action in READS
    return bool(cap.outputs) and not missing and not ctx.run.gated and last_reads


async def _main_steps(ctx: Ctx, cap: Capability, crops: Path | None, drift: Drift) -> None:
    reached = False  # a human's take-over already got to the checkpoint: nothing left to act on
    for i, step in enumerate(cap.steps):
        if is_cleanup(step):
            continue
        if reached and step.action not in READS:  # reads still run: they never send, and they
            drift.append({"step": i, "action": step.action, "rung": "skipped"})  # read outputs
            continue
        before = ctx.run.look.text if ctx.run.look else ""
        await run_step(ctx, i, step, cap, crops, drift=drift)
        reached = reached or took_over_to_checkpoint(ctx, i, cap, before)


async def walk(ctx: Ctx, cap: Capability, crops: Path | None, drift: Drift) -> ReplayResult:
    """The main steps (every step not marked cleanup), then the checkpoint and the outputs."""
    await _main_steps(ctx, cap, crops, drift)
    run = ctx.run
    run.step, run.action = len(cap.steps), "checkpoint"
    missing = sorted({o.name for o in cap.outputs} - set(run.outputs))
    reason = ""
    if not await steps.shows(ctx, cap.checkpoint):
        if not read_only_done(ctx, cap, missing):
            raise Stop(
                "FAILED",
                "checkpoint text not on the final screen",
                cap.checkpoint,
                run.look.text[:200] if run.look else "",
            )
        reason = "checkpoint looked for after cleanup; all outputs read"
    if missing:
        raise Stop("FAILED", f"outputs not read: {missing}")
    return ReplayResult(
        "SUCCESS", dict(run.outputs), drift, reason, list(run.human), recoveries=run.recoveries
    )


async def _cleanup_step(  # noqa: PLR0913 (constraints allow 6)
    ctx: Ctx, i: int, step: Step, cap: Capability, crops: Path | None, *, drift: Drift
) -> str:
    """One cleanup step, one retry. "" = done, else the failure."""
    if refused := action_allowed(ctx, step):
        return f"failed: {refused.reason}"
    for attempt in (1, 2):
        try:
            target = getattr(step, "target", None)
            hit = await steps.find(ctx, target, crops) if target else (None, "-")
            ok = hit is not None and await steps.ACTIONS[step.action](ctx, step, hit[0], cap)  # type: ignore[arg-type]
        except Stop as s:
            return f"failed: {s.reason}"
        drift.append(
            {
                "step": i,
                "action": step.action,
                "rung": hit[1] if hit else "miss",
                "point": hit[0] if hit else None,  # type: ignore[dict-item]  # tuple->JSON
                "attempt": attempt,
                "checked": ok,
                "cleanup": True,
            }
        )
        if ok:
            break
        if ctx.run.sent or attempt == 2:  # noqa: PLR2004
            return "failed: target not found" if hit is None else "failed: the step's check failed"
        await look(ctx)
    return ""


async def run_cleanup(ctx: Ctx, cap: Capability, crops: Path | None, drift: Drift) -> str:
    """Cleanup steps (e.g. Log Out): best-effort, one retry, no rescue panel. Never changes the
    status."""
    todo = [(i, s) for i, s in enumerate(cap.steps) if is_cleanup(s)]
    if not todo:
        return ""
    for i, step in todo:
        if failed := await _cleanup_step(ctx, i, step, cap, crops, drift=drift):
            return failed
    return "done"


async def stopped(ctx: Ctx, s: Stop, drift: Drift) -> ReplayResult:
    """A run that stopped: its status, the failure detail (R17) and the final screen for
    evidence."""
    ctx.last.final = await snap(ctx)
    run, hide = ctx.run, ctx.secrets
    failure: dict[str, JsonValue] = {
        "step": run.step,
        "action": run.action,
        "expected": s.expected,
        "observed": hide_secrets(s.observed or s.reason, hide),
    }
    return ReplayResult(
        s.status,
        dict(run.outputs),
        drift,
        hide_secrets(s.reason, hide),
        list(run.human),
        failure,
        run.recoveries,
    )


async def finish(ctx: Ctx, cap: Capability, crops: Path | None, drift: Drift) -> ReplayResult:
    """Main steps -> checkpoint -> outputs, then the cleanup steps, ALWAYS (the run is logged
    in)."""
    try:
        res = await walk(ctx, cap, crops, drift)
    except Stop as s:
        res = await stopped(ctx, s, drift)
    finally:
        done = await run_cleanup(ctx, cap, crops, drift)
    return replace(res, cleanup=hide_secrets(done, ctx.secrets))


async def open_start(ctx: Ctx, cap: Capability) -> None:
    page = ctx.page
    if starts_with_login(cap):
        await page.context.clear_cookies()  # start logged out, as the recording did
    await page.goto(cap.base_url)
    shot = decode(await page.screenshot())
    if (shot.shape[1], shot.shape[0]) != tuple(cap.viewport):  # R3: no scaling
        raise Stop(
            "FAILED", f"screenshot is {shot.shape[1]}x{shot.shape[0]}, expected {cap.viewport}"
        )
    await look(ctx)


async def _run(
    ctx: Ctx, path: str | Path, inputs: dict[str, str] | None, drift: Drift
) -> ReplayResult:
    cap, crops = load_capability(path, ctx.site, ctx.bcfg)
    ctx.run.outcomes = load_outcomes(path, ctx.site)
    given = given_inputs(cap, inputs or {})  # an unknown key stops before the site opens
    await open_start(ctx, cap)
    ctx.run.values = await loader.ask_inputs(ctx, cap, given)
    ctx.run.given = list(ctx.run.values.values())
    return await finish(ctx, cap, crops, drift)  # from here on, cleanup always runs


async def replay(ctx: Ctx, path: str | Path, inputs: dict[str, str] | None = None) -> ReplayResult:
    """Replay a saved capability. Outputs go to the caller only; the drift log holds rungs, never
    values. ``ctx.last`` keeps the mask set and final screen for :func:`save_evidence`."""
    drift: Drift = []
    ctx.last.values, ctx.last.final = set(), None
    try:
        return await _run(ctx, path, inputs, drift)
    except Stop as s:
        return await stopped(ctx, s, drift)
    except ValidationError as e:
        where = e.errors()[0]
        return ReplayResult(
            "FAILED", {}, drift, f"invalid capability at {where['loc']}: {where['msg']}"
        )
    finally:
        run = ctx.run
        ctx.last.values = {v for v in (*run.values.values(), *run.given) if v}  # masking only
        wipe(ctx)  # R7: nothing kept
