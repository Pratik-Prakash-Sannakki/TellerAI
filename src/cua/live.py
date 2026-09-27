"""Wires the async replay engine (`cua.replay.run_capability_async`) to a REAL Playwright browser.

Ported from ``notebooks/05_replay_live.py``: `PlaywrightReplaySurface` (an `AsyncReplaySurface`
implementation, D78), `make_escalate` (a real human-approval decision bar, D79/D85), and
`gather_missing_inputs`/`missing_required_inputs` (the pre-flight input gate, D91).

Where the notebook duplicates agent.ipynb's `PlaywrightSurface`, lock JS, and `human_takeover`
verbatim (a necessary duplication there, since a notebook cell exec context cannot import another
notebook), this module just imports `cua.agent.DiscoveryAgent` directly -- a real package can
share code a notebook cannot. `PlaywrightReplaySurface` is built from a `DiscoveryAgent` instance
(reusing its `.surface`, `.human_takeover`, `.needs_human`, `.current_value`, `.approval_info`),
exactly matching the task's own instruction (D78) to "reuse or closely mirror... never invent a
third way." A replay run never calls any of `DiscoveryAgent`'s LLM-tool methods (`click`,
`type_text`, ...); it only reuses the lower-level browser-control mechanics underneath them, the
same subset 05_replay_live.py's own "Setup 6" comment calls out by name.

Evidence capture (D92, saving a run under `evidence/replay/`) is a separate, concurrent task's own
addition to the notebook (`replay_live`'s opt-in `evidence_dir` parameter) and is intentionally
not ported here -- see `/evidence/` for a full recorded run once that work lands.
"""

from __future__ import annotations

import asyncio
import pathlib
import re
from dataclasses import dataclass

from cua.agent import DESCRIBE_JS, DECISION_JS, DiscoveryAgent, HEADING_JS, READ_LABELED_JS
from cua.config import BASE, host_allowed, resolve_secret
from cua.replay import (
    AsyncReplaySurface,
    InputValidationError,
    resolve_target_async,
    run_capability_async,
)
from cua.schema import Capability, InputParam, ReplayResult, from_yaml

__all__ = [
    "LabeledValueRef",
    "PlaywrightReplaySurface",
    "make_escalate",
    "missing_required_inputs",
    "gather_missing_inputs",
    "replay_live",
]


@dataclass(frozen=True)
class LabeledValueRef:
    """A `resolve()` result for a `labeled_value` locator: not a numbered element ref -- a
    labeled-value read never depends on page position (D46) -- just the label text, re-read live
    by `read_value` every time it is needed."""
    label: str


class PlaywrightReplaySurface:
    """Implements `AsyncReplaySurface` (`cua.replay`) against the real browser. Wraps a
    `DiscoveryAgent`'s own `PlaywrightSurface`/lock mechanism -- nothing here is a second
    implementation of clicking, typing, selecting, or locking (D78)."""

    # D88: a bounded poll budget for resolve()'s own real-page timing, separate from and
    # unrelated to the engine's step-level TransientFailure retry (D26). ParaBank's own Accounts
    # Overview page renders its table body via an AJAX call that runs AFTER the page's `load`
    # event, so a single immediate `resolve()` attempt can race it.
    _RESOLVE_POLL_INTERVAL_S = 0.4
    _RESOLVE_POLL_BUDGET_S = 5.0

    def __init__(self, agent: DiscoveryAgent):
        self.agent = agent
        self.page = agent.page

    async def navigate(self, path: str) -> None:
        url = BASE + path
        if not host_allowed(url):
            # D80: the engine's step loop only catches ResolutionError/TransientFailure -- there
            # is no "policy blocked" bucket to return a FAILED ReplayResult through. Raising here
            # propagates uncaught, an honestly documented gap rather than a silent off-host
            # navigation (D15 forbids the latter outright).
            raise PermissionError(f"host not allowed by ALLOWED_HOSTS: {url}")
        await self.page.goto(url)

    async def _resolve_once(self, locator):
        """One resolution attempt, no retry -- the exact logic `resolve()` used before D88."""
        if locator.strategy == "labeled_value":
            res = await self.page.evaluate(READ_LABELED_JS, locator.label)
            return LabeledValueRef(label=locator.label) if res["value"] else None

        obs = await self.agent.surface.observe()
        for el in obs.elements:
            desc = await self.page.evaluate(DESCRIBE_JS, el["ref"])
            if desc is not None and self._matches(locator, desc):
                return el["ref"]
        return None

    async def resolve(self, locator):
        """D78: for `labeled_value`, go straight to READ_LABELED_JS (no numbered scan at all).
        For every other strategy, run the SAME numbered scan `PlaywrightSurface.observe()` does,
        then match each candidate's descriptor against the locator. D88: bounded poll/retry
        applied to both branches -- a miss is retried every `_RESOLVE_POLL_INTERVAL_S` up to
        `_RESOLVE_POLL_BUDGET_S` (wall clock) before finally reporting `None`."""
        loop = asyncio.get_event_loop()
        deadline = loop.time() + self._RESOLVE_POLL_BUDGET_S
        while True:
            found = await self._resolve_once(locator)
            if found is not None:
                return found
            if loop.time() >= deadline:
                return None
            await asyncio.sleep(self._RESOLVE_POLL_INTERVAL_S)

    @staticmethod
    def _container_matches(within, container: dict | None) -> bool:
        if within is None:
            return True
        if container is None:
            return False
        if container.get("role") != within.role:
            return False
        return within.name is None or container.get("name") == within.name

    def _matches(self, locator, desc: dict) -> bool:
        strategy = locator.strategy
        if strategy == "role":
            return (desc["role"] == locator.role and desc["name"] == locator.name
                    and self._container_matches(locator.within, desc.get("container")))
        if strategy == "label":
            # D68's own stated gap: no `within` slot exists on this strategy. The first matching
            # descriptor wins -- not newly introduced, not closed, here either.
            return desc.get("label") == locator.label
        if strategy == "text":
            return (desc.get("text") == locator.text
                    and self._container_matches(locator.within, desc.get("container")))
        if strategy == "structure":
            return (self._container_matches(locator.within, desc.get("container"))
                    and desc.get("tag") == locator.tag and desc.get("nth") == locator.nth)
        return False   # labeled_value never reaches here -- handled directly in resolve() above

    async def click(self, ref) -> None:
        await self.agent.surface.click(ref)

    async def type_text(self, ref, value: str) -> None:
        await self.agent.surface.type_text(ref, value)

    async def select_option(self, ref, value: str) -> None:
        from cua.agent import _unlocked

        await _unlocked(self.page, self.page.locator(f'[data-cua-ref="{ref}"]').select_option(label=value, timeout=5000, force=True))

    async def read_value(self, ref) -> str:
        if isinstance(ref, LabeledValueRef):
            res = await self.page.evaluate(READ_LABELED_JS, ref.label)
            if not res["value"]:
                raise LookupError(f"no value found next to the label {ref.label!r}")
            return res["value"]
        value = await self.agent.current_value(ref)
        if value:
            return value
        # Not a form control -- e.g. a `text`-strategy extract target such as transfer_funds'
        # "Transfer Complete!" confirmation heading (D81).
        try:
            return (await self.page.locator(f'[data-cua-ref="{ref}"]').inner_text(timeout=1000)).strip()
        except Exception:
            return ""

    async def current_url(self) -> str:
        return self.page.url

    async def page_text(self) -> str:
        return (await self.page.inner_text("body"))[:4000]


async def _show_decision(page, title: str, details: str) -> str:
    """Runs the SAME DECISION_JS bar `DiscoveryAgent.click()` shows. The general lock is already
    active by default, so a human cannot act on the real page while this bar is up (D57)."""
    return await page.evaluate(DECISION_JS, {"title": title, "details": details})


def make_escalate(cap: Capability, agent: DiscoveryAgent, live_surface: PlaywrightReplaySurface):
    """Returns an `escalate(reason, ctx)` closure for this one capability. Passed as
    `run_capability_async`'s `escalate=` argument.

    D85: for the risky-click case, this closure only shows the decision bar and REPORTS the
    human's choice -- it must never click anything itself. The engine is what resolves the
    target and clicks it, and only when this returns exactly the string "approve"."""

    async def escalate(reason: str, ctx: dict) -> str | None:
        step_index = ctx.get("step_index")
        step = cap.steps[step_index] if step_index is not None else None

        if step is not None and getattr(step, "action", None) == "click" and step.risk == "risky":
            ref = await resolve_target_async(live_surface, step.target)
            info = agent.approval_info({"ref": ref})
            info["details"] = f"Reason: {reason}"   # TYPED is empty during replay; show the real reason instead
            choice = await _show_decision(agent.page, info["title"], info["details"])
            if choice == "a":
                print(f"[escalate] APPROVED -- ref={ref} ({agent.surface.name_of(ref)!r}); the engine will click it")
                return "approve"
            elif choice == "r":
                print(f"[escalate] REJECTED -- no action taken. reason: {reason}")
                return None
            else:
                report = await agent.human_takeover(question="", auto_on_navigate=True, block_risky=False)
                print(f"[escalate] TAKE OVER -- a human acted directly. {report}")
                return None   # a human took over; the engine must not also click on our say-so

        # A hard failure (checkpoint / outcome-rule / resolution / retries-exhausted). Nothing to
        # click here -- run_capability_async already returns FAILED regardless of what a human
        # does with this bar; it exists only to make the failure visible in the live browser.
        await _show_decision(agent.page, "REPLAY needs your attention", reason)
        print(f"[escalate] acknowledged: {reason} | context: {ctx}")
        return None

    return escalate


# ---------------------------------------------------------------------------
# Pre-flight input gate (D91): prompts for missing required inputs before anything starts.
# ---------------------------------------------------------------------------
_PREFLIGHT_MAX_ATTEMPTS = 5   # bounded -- never loops forever


def missing_required_inputs(cap: Capability, inputs: dict[str, str]) -> list[InputParam]:
    """Pure, standalone, offline-testable: which of `cap.inputs` are `.required` and have no real
    value in `inputs`, in `cap.inputs`' own declared order. "No real value" covers both a name
    absent from `inputs` entirely and one present but empty or whitespace-only. Never looks at
    `cap.secrets` -- secrets are a separate mechanism (D32) this function does not touch."""
    missing = []
    for param in cap.inputs:
        if not param.required:
            continue
        value = inputs.get(param.name)
        if value is None or not str(value).strip():
            missing.append(param)
    return missing


def _prompt_for_missing_input(param: InputParam, *, input_fn=input,
                               max_attempts: int = _PREFLIGHT_MAX_ATTEMPTS) -> str:
    """Prompt for exactly one missing required input, showing its own `.description` as the
    prompt text. Validates each answer against the input's own `.pattern` with the SAME
    `re.fullmatch` call `validate_inputs` (`cua.replay`) already uses. Up to `max_attempts` tries,
    never unbounded; raises InputValidationError, naming the field, once the budget is exhausted."""
    for attempt in range(1, max_attempts + 1):
        raw = input_fn(f"{param.name} -- {param.description}\n> ")
        value = (raw or "").strip()
        if not value:
            print(f"  '{param.name}' cannot be empty. ({attempt}/{max_attempts})")
            continue
        if param.pattern and not re.fullmatch(param.pattern, value):
            print(f"  {value!r} does not match the required pattern for {param.name!r} "
                  f"({param.pattern!r}). ({attempt}/{max_attempts})")
            continue
        return value
    raise InputValidationError(f"gave up after {max_attempts} attempts for required input {param.name!r}")


def gather_missing_inputs(cap: Capability, inputs: dict[str, str], *, input_fn=input,
                           max_attempts: int = _PREFLIGHT_MAX_ATTEMPTS) -> dict[str, str]:
    """The pre-flight gate itself (D91). Runs BEFORE anything else in `replay_live` -- no browser
    action, no login, no step, has happened yet when this is called. Always returns a NEW dict
    (the caller's own `inputs` is never mutated, matching `compile_run`'s own defensive-copy
    discipline, D90).

    A true no-op -- no printing, no prompting, `input_fn` never called even once -- when nothing
    is missing."""
    missing = missing_required_inputs(cap, inputs)
    gathered = dict(inputs)
    if not missing:
        return gathered
    print("You have not entered these fields. Please enter these fields.")
    for param in missing:
        print(f"  - {param.name}")
    for param in missing:
        gathered[param.name] = _prompt_for_missing_input(param, input_fn=input_fn, max_attempts=max_attempts)
    return gathered


async def replay_live(cap_path, inputs: dict[str, str], agent: DiscoveryAgent, *,
                       auto_approve_limit: float = 500.0) -> ReplayResult:
    """Load a capability YAML and replay it for real, printing the result. `secrets` is always
    `resolve_secret` (D32): a secret VALUE is never printed, logged, or placed in anything this
    function returns or prints -- only its NAME ever appears, if at all.

    `gather_missing_inputs` runs BEFORE `run_capability_async`, before any browser action, before
    login, before any step runs (D91). A no-op when nothing is missing."""
    cap = from_yaml(pathlib.Path(cap_path).read_text())
    inputs = gather_missing_inputs(cap, inputs)
    live_surface = PlaywrightReplaySurface(agent)
    result = await run_capability_async(
        cap, live_surface, inputs, resolve_secret,
        auto_approve_limit=auto_approve_limit, escalate=make_escalate(cap, agent, live_surface), logger=print,
    )
    print("REPLAY RESULT:", result.status, result.outputs or result.outcome or result.reason or result.failure)
    return result
