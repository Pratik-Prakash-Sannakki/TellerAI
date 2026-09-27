"""The replay engine: sync (`run_capability`) and async (`run_capability_async`) versions.

Ported from ``notebooks/04_replay_engine.py`` Sections 1-4 (sync) and 7-9 (async), unmodified.
Zero LLM in the loop (D6, 3.3): a `Capability` (``cua.schema``) is data; this module only walks
it against a `ReplaySurface`/`AsyncReplaySurface` implementation. The real, Playwright-backed
surface is ``cua.live.PlaywrightReplaySurface``; tests use a hand-built ``FakeSurface``/
``AsyncFakeSurface`` (``tests/test_replay.py``), so nothing here imports Playwright.

See DECISIONS.md D9/D10/D26/D27/D38/D39 (the original design), D77 (why a parallel async engine
exists, and the two pure helpers `_target_locators`/`_find_outcome_rule` shared by both engines),
and D85 (the fix making `escalate`'s return value, not a side effect inside it, decide whether a
risky click happens).
"""

from __future__ import annotations

import inspect
import re
from typing import Any, Callable, Protocol, runtime_checkable

from cua.schema import Capability, Condition, Failure, ReplayResult, Target, _TEMPLATE

__all__ = [
    "ReplaySurface",
    "AsyncReplaySurface",
    "TransientFailure",
    "ResolutionError",
    "InputValidationError",
    "describe_locator",
    "describe_target",
    "resolve_target",
    "resolve_target_async",
    "matches_value_type",
    "validate_inputs",
    "render",
    "parse_amount",
    "condition_matches",
    "run_capability",
    "run_capability_async",
    "SecretResolver",
]

SecretResolver = Callable[[str], str]


# ---------- ReplaySurface protocol and exceptions (Section 2) ----------
@runtime_checkable
class ReplaySurface(Protocol):
    """What a real Playwright-backed surface implements (``cua.live.PlaywrightReplaySurface``)."""
    def navigate(self, path: str) -> None: ...
    def resolve(self, locator) -> Any | None: ...
    def click(self, ref) -> None: ...
    def type_text(self, ref, value: str) -> None: ...
    def select_option(self, ref, value: str) -> None: ...
    def read_value(self, ref) -> str: ...
    def current_url(self) -> str: ...
    def page_text(self) -> str: ...


def describe_locator(loc) -> str:
    """One line naming what a locator is looking for -- used to build a clear Failure.expected."""
    if loc.strategy == "role":
        return f"role={loc.role!r} name={loc.name!r}"
    if loc.strategy == "label":
        return f"label={loc.label!r}"
    if loc.strategy == "text":
        return f"text={loc.text!r}"
    if loc.strategy == "structure":
        return f"{loc.nth}th <{loc.tag}> within {loc.within.role!r}"
    if loc.strategy == "labeled_value":
        return f"labeled_value label={loc.label!r}"
    return loc.strategy


def describe_target(target: Target) -> str:
    parts = [f"primary: {describe_locator(target.primary)}"]
    if target.fallback is not None:
        parts.append(f"fallback: {describe_locator(target.fallback)}")
    return "; ".join(parts)


class TransientFailure(Exception):
    """A surface raises this for a step that should be retried (D26): the page was not ready
    yet. Only steps the engine treats as retryable (everything except a risky click) retry."""


class ResolutionError(Exception):
    """Neither the primary nor the fallback locator resolved to an element."""
    def __init__(self, target: Target):
        self.target = target
        super().__init__(describe_target(target))


class InputValidationError(Exception):
    """A caller-supplied input is missing, mistyped, or does not match its declared pattern."""


# ---------- resolve_target, template substitution, input validation (Section 3) ----------
def _target_locators(target: Target) -> list[tuple[str, Any]]:
    """Pure: the try-order for a target -- primary, then fallback if present (D63). No surface
    call, no logging. Shared by resolve_target (sync) and resolve_target_async so the sync and
    async engines can never disagree about which locator is tried, or in which order (D77)."""
    locs = [("primary", target.primary)]
    if target.fallback is not None:
        locs.append(("fallback", target.fallback))
    return locs


def resolve_target(surface: ReplaySurface, target: Target, *, logger: Callable[[str], None] = lambda m: None):
    """Try the primary locator, then the fallback if there is one and the primary did not
    resolve. Raises ResolutionError, naming what was expected, if neither resolves."""
    for which, loc in _target_locators(target):
        ref = surface.resolve(loc)
        if ref is not None:
            if which == "primary":
                logger(f"resolved via primary ({loc.strategy})")
            else:
                logger(f"primary failed, resolved via fallback ({loc.strategy})")
            return ref
    raise ResolutionError(target)


def matches_value_type(value: str, type_: str) -> bool:
    """Basic format check for a declared ValueType. Used for both inputs (D29) and outputs
    (D12): an extracted value that does not match its type is a hard failure, never a silently
    wrong SUCCESS."""
    if type_ == "integer":
        return bool(re.fullmatch(r"-?\d+", value))
    if type_ == "number":
        try:
            float(value)
            return True
        except ValueError:
            return False
    if type_ == "currency":
        return bool(re.fullmatch(r"\$?-?\d+(\.\d{2})?", value.replace(",", "")))
    if type_ == "boolean":
        return value.strip().lower() in ("true", "false")
    return True   # string: anything


def validate_inputs(cap: Capability, raw_inputs: dict[str, str]) -> dict[str, str]:
    """Type/pattern-validate caller-supplied inputs before they are ever substituted into a step
    (D29). Raises InputValidationError listing every problem, never silently coerces."""
    problems: list[str] = []
    values: dict[str, str] = {}
    declared = {i.name: i for i in cap.inputs}
    for name, param in declared.items():
        if name not in raw_inputs:
            if param.required:
                problems.append(f"missing required input {name!r}")
            continue
        value = str(raw_inputs[name])
        if not matches_value_type(value, param.type):
            problems.append(f"input {name!r} = {value!r} is not a valid {param.type}")
        elif param.pattern and not re.fullmatch(param.pattern, value):
            problems.append(f"input {name!r} = {value!r} does not match pattern {param.pattern!r}")
        else:
            values[name] = value
    extra = set(raw_inputs) - set(declared)
    if extra:
        problems.append(f"undeclared inputs given: {sorted(extra)}")
    if problems:
        raise InputValidationError("; ".join(problems))
    return values


def render(text: str, values: dict[str, str], secrets: SecretResolver) -> str:
    """{{input_name}} from validated caller inputs; {{secret:name}} from the SecretResolver.
    Reuses the exact template syntax and regex from the Phase 2 schema (D29, D32)."""
    def repl(m):
        is_secret, name = bool(m.group(1)), m.group(2)
        return secrets(name) if is_secret else values[name]
    return _TEMPLATE.sub(repl, text)


# ---------- run_capability: the sync engine loop (Section 4) ----------
def parse_amount(raw: str) -> float:
    """An amount we cannot parse is treated as infinite -- it always needs approval, it is
    never silently auto-approved."""
    try:
        return float(raw.replace("$", "").replace(",", "").strip())
    except ValueError:
        return float("inf")


def condition_matches(cond: Condition, url: str, text: str) -> bool:
    if cond.url_contains and cond.url_contains not in url:
        return False
    if cond.text_present and cond.text_present not in text:
        return False
    return True


def _fail(step_index: int, step_action: str, expected: str, observed: str) -> Failure:
    return Failure(step_index=step_index, step_action=step_action, expected=expected, observed=observed)


def _find_outcome_rule(cap: Capability, url: str, text: str):
    """Pure: the first outcome rule (in declared order) whose condition matches (D10 -- first
    match wins). No escalate call, no logging. Shared by _check_outcomes (sync) and
    _check_outcomes_async so the sync and async engines can never pick a different rule (D77)."""
    for rule in cap.outcome_rules:
        if condition_matches(rule.when, url, text):
            return rule
    return None


def _is_approved(decision: Any) -> bool:
    """Pure: what a risky click's `escalate(reason, ctx)` return value means (D85). Exactly the
    string `"approve"` means "proceed with this click"; anything else means "no decision, stay
    NEEDS_APPROVAL". Shared by run_capability's and run_capability_async's risky-click branches."""
    return decision == "approve"


def _check_outcomes(cap, step_index, url, text, escalate, base, logger):
    """First matching rule wins, in declared order (D10's documented order rule)."""
    rule = _find_outcome_rule(cap, url, text)
    if rule is None:
        return None
    if rule.kind == "business":
        logger(f"step {step_index}: business outcome {rule.outcome}")
        return ReplayResult(**base(status="BUSINESS_OUTCOME", outcome=rule.outcome))
    if rule.kind == "hard":
        failure = _fail(step_index, "outcome_rule", "no hard-failure text on the page", text[:200])
        if escalate is not None:
            escalate(rule.message, {"capability": cap.name, "step_index": step_index})
        return ReplayResult(**base(status="FAILED", failure=failure))
    # recoverable: logged, then replay continues to the next step. Known limit: actually
    # performing the action (dismiss a popup, wait, re-run a login capability) needs a live
    # surface and, for relogin, capability composition -- both are next-step work, not built here.
    logger(f"step {step_index}: recoverable condition matched (action={rule.action}): {rule.message}")
    return None


def run_capability(
    cap: Capability,
    surface: ReplaySurface,
    inputs: dict[str, str],
    secrets: SecretResolver,
    *,
    run_id: str = "run",
    auto_approve_limit: float = 500.0,
    escalate: Callable[[str, dict], Any] | None = None,
    max_retries: int = 2,
    logger: Callable[[str], None] = lambda m: None,
) -> ReplayResult:
    """Run every step of `cap` against `surface`, no LLM in the loop (D6, 3.3). `escalate`, when
    given, is called for NEEDS_APPROVAL and for an unrecoverable hard failure.

    For a risky click at/above `auto_approve_limit`, `escalate`'s return value is consulted
    (D85): exactly the string `"approve"` means resolve the target and click it for real, then
    continue to the remaining steps; anything else (including the default `None`) means stay
    `NEEDS_APPROVAL`. `escalate` itself must never perform the click."""
    values = validate_inputs(cap, inputs)
    outputs: dict[str, str] = {}

    def base(**kw):
        return dict(run_id=run_id, capability=cap.name, capability_version=cap.version, **kw)

    for i, step in enumerate(cap.steps):
        action = step.action
        retryable = not (action == "click" and step.risk == "risky")   # D26: never retry a risky click
        attempts = 0
        while True:
            try:
                if action == "navigate":
                    surface.navigate(render(step.path, values, secrets))
                elif action == "click":
                    if step.risk == "risky":
                        amount = parse_amount(values.get(step.amount_input, "")) if step.amount_input else float("inf")
                        if amount >= auto_approve_limit:
                            reason = f"amount {amount} is at or above the auto-approve limit {auto_approve_limit}"
                            ctx = {"capability": cap.name, "step_index": i, "amount": amount, "limit": auto_approve_limit}
                            decision = escalate(reason, ctx) if escalate is not None else None
                            if not _is_approved(decision):   # D85: unchanged NEEDS_APPROVAL behavior
                                return ReplayResult(**base(status="NEEDS_APPROVAL", pending_step=i, reason=reason))
                            # D85: escalate approved this click -- fall through to the exact same
                            # resolve-then-click a non-risky (or under-limit) click step already
                            # uses below, and let the loop continue to the remaining steps.
                    ref = resolve_target(surface, step.target, logger=logger)
                    surface.click(ref)
                elif action == "type":
                    ref = resolve_target(surface, step.target, logger=logger)
                    surface.type_text(ref, render(step.value, values, secrets))
                elif action == "select":
                    ref = resolve_target(surface, step.target, logger=logger)
                    surface.select_option(ref, render(step.option, values, secrets))
                elif action == "extract":
                    ref = resolve_target(surface, step.target, logger=logger)
                    raw_value = surface.read_value(ref)
                    out_param = next(o for o in cap.outputs if o.name == step.save_as)
                    if not matches_value_type(raw_value, out_param.type):
                        failure = _fail(i, action, f"a value matching type {out_param.type!r}", repr(raw_value))
                        if escalate is not None:
                            escalate("extracted value failed its declared type", {"capability": cap.name, "step_index": i})
                        return ReplayResult(**base(status="FAILED", failure=failure))
                    outputs[step.save_as] = raw_value
                else:
                    raise AssertionError(f"unknown action {action!r}")
                break   # step succeeded, no transient failure
            except ResolutionError as exc:
                failure = _fail(i, action, str(exc), "neither primary nor fallback resolved")
                if escalate is not None:
                    escalate("could not resolve the target element", {"capability": cap.name, "step_index": i})
                return ReplayResult(**base(status="FAILED", failure=failure))
            except TransientFailure as exc:
                attempts += 1
                logger(f"step {i} ({action}): transient failure ({exc}), attempt {attempts}")
                if not retryable or attempts > max_retries:
                    failure = _fail(i, action, "the step to succeed", f"transient failure after {attempts} attempt(s): {exc}")
                    if escalate is not None:
                        escalate("step failed after retries", {"capability": cap.name, "step_index": i})
                    return ReplayResult(**base(status="FAILED", failure=failure))
                continue   # retry the same step

        url, text = surface.current_url(), surface.page_text()
        if step.expect is not None and not condition_matches(step.expect, url, text):
            failure = _fail(i, action, f"url_contains={step.expect.url_contains!r} text_present={step.expect.text_present!r}",
                             f"url={url!r} text={text[:200]!r}")
            if escalate is not None:
                escalate("a step's own expect condition did not hold", {"capability": cap.name, "step_index": i})
            return ReplayResult(**base(status="FAILED", failure=failure))

        outcome_result = _check_outcomes(cap, i, url, text, escalate, base, logger)
        if outcome_result is not None:
            return outcome_result

    url, text = surface.current_url(), surface.page_text()
    if not condition_matches(cap.checkpoint, url, text):
        failure = _fail(len(cap.steps) - 1, "checkpoint",
                         f"url_contains={cap.checkpoint.url_contains!r} text_present={cap.checkpoint.text_present!r}",
                         f"url={url!r} text={text[:200]!r}")
        if escalate is not None:
            escalate("checkpoint did not match after all steps ran", {"capability": cap.name})
        return ReplayResult(**base(status="FAILED", failure=failure))

    declared = {o.name for o in cap.outputs}
    if set(outputs) != declared:
        failure = _fail(len(cap.steps) - 1, "extract", f"outputs {sorted(declared)}", f"got {sorted(outputs)}")
        return ReplayResult(**base(status="FAILED", failure=failure))

    return ReplayResult(**base(status="SUCCESS", outputs=outputs))


# ---------- AsyncReplaySurface, the async engine (Sections 7-9) ----------
@runtime_checkable
class AsyncReplaySurface(Protocol):
    """The async twin of ReplaySurface. Same method names, same meanings -- every method is
    `async def` instead, because the real implementation (``cua.live.PlaywrightReplaySurface``)
    wraps Playwright, which has no usable sync API inside an already-running asyncio event loop."""
    async def navigate(self, path: str) -> None: ...
    async def resolve(self, locator) -> Any | None: ...
    async def click(self, ref) -> None: ...
    async def type_text(self, ref, value: str) -> None: ...
    async def select_option(self, ref, value: str) -> None: ...
    async def read_value(self, ref) -> str: ...
    async def current_url(self) -> str: ...
    async def page_text(self) -> str: ...


async def resolve_target_async(surface: AsyncReplaySurface, target: Target, *,
                                logger: Callable[[str], None] = lambda m: None):
    """Async twin of resolve_target. Same try-order (`_target_locators`, a PURE function with no
    surface calls, shared by both engines so they can never disagree about which locator is tried
    first), same log wording -- only the resolve call itself is awaited."""
    for which, loc in _target_locators(target):
        ref = await surface.resolve(loc)
        if ref is not None:
            if which == "primary":
                logger(f"resolved via primary ({loc.strategy})")
            else:
                logger(f"primary failed, resolved via fallback ({loc.strategy})")
            return ref
    raise ResolutionError(target)


async def _call_escalate(escalate: Callable[[str, dict], Any] | None, reason: str, ctx: dict) -> Any:
    """Call `escalate` and, if it returns something awaitable (a real live implementation that
    shows a decision bar and waits for a human is exactly this), await it before continuing. A
    plain sync escalate (every offline test's fake) returns None or a plain value, which is not
    awaitable, so this is a complete no-op difference for every existing test (D77). Returns
    whatever `escalate` (or the coroutine it returned) itself returned -- the risky-click branch
    (D85) is the one caller that reads this to decide whether `escalate` said `"approve"`."""
    if escalate is None:
        return None
    result = escalate(reason, ctx)
    if inspect.isawaitable(result):
        return await result
    return result


async def _check_outcomes_async(cap, step_index, url, text, escalate, base, logger):
    """Async twin of _check_outcomes. Uses the SAME `_find_outcome_rule` (a pure function with no
    surface or escalate calls) to decide which rule matches, so the sync and async engines can
    never disagree about which rule fires first. Only the escalate call for a hard rule is
    awaited (via `_call_escalate`)."""
    rule = _find_outcome_rule(cap, url, text)
    if rule is None:
        return None
    if rule.kind == "business":
        logger(f"step {step_index}: business outcome {rule.outcome}")
        return ReplayResult(**base(status="BUSINESS_OUTCOME", outcome=rule.outcome))
    if rule.kind == "hard":
        failure = _fail(step_index, "outcome_rule", "no hard-failure text on the page", text[:200])
        await _call_escalate(escalate, rule.message, {"capability": cap.name, "step_index": step_index})
        return ReplayResult(**base(status="FAILED", failure=failure))
    logger(f"step {step_index}: recoverable condition matched (action={rule.action}): {rule.message}")
    return None


async def run_capability_async(
    cap: Capability,
    surface: AsyncReplaySurface,
    inputs: dict[str, str],
    secrets: SecretResolver,
    *,
    run_id: str = "run",
    auto_approve_limit: float = 500.0,
    escalate: Callable[[str, dict], Any] | None = None,
    max_retries: int = 2,
    logger: Callable[[str], None] = lambda m: None,
) -> ReplayResult:
    """Async twin of run_capability. IDENTICAL behavior -- every surface call is awaited, and
    `escalate` is awaited too if it returns something awaitable (`_call_escalate`, D77). No
    business logic differs: same input validation, same per-step resolution order, same
    risky-click gate BEFORE the click, same outcome-rule order, same retry bound (never for a
    risky click), same checkpoint/output checks, same four statuses.

    Same D85 approval contract as run_capability: a risky click's `escalate` return value of
    exactly `"approve"` resolves the target and clicks it for real, then continues; anything else
    stays `NEEDS_APPROVAL`, unchanged."""
    values = validate_inputs(cap, inputs)
    outputs: dict[str, str] = {}

    def base(**kw):
        return dict(run_id=run_id, capability=cap.name, capability_version=cap.version, **kw)

    for i, step in enumerate(cap.steps):
        action = step.action
        retryable = not (action == "click" and step.risk == "risky")   # D26: never retry a risky click
        attempts = 0
        while True:
            try:
                if action == "navigate":
                    await surface.navigate(render(step.path, values, secrets))
                elif action == "click":
                    if step.risk == "risky":
                        amount = parse_amount(values.get(step.amount_input, "")) if step.amount_input else float("inf")
                        if amount >= auto_approve_limit:
                            reason = f"amount {amount} is at or above the auto-approve limit {auto_approve_limit}"
                            ctx = {"capability": cap.name, "step_index": i, "amount": amount, "limit": auto_approve_limit}
                            decision = await _call_escalate(escalate, reason, ctx)
                            if not _is_approved(decision):   # D85: unchanged NEEDS_APPROVAL behavior
                                return ReplayResult(**base(status="NEEDS_APPROVAL", pending_step=i, reason=reason))
                            # D85: escalate approved this click -- fall through to the exact same
                            # resolve-then-click a non-risky (or under-limit) click step already
                            # uses below, and let the loop continue to the remaining steps.
                    ref = await resolve_target_async(surface, step.target, logger=logger)
                    await surface.click(ref)
                elif action == "type":
                    ref = await resolve_target_async(surface, step.target, logger=logger)
                    await surface.type_text(ref, render(step.value, values, secrets))
                elif action == "select":
                    ref = await resolve_target_async(surface, step.target, logger=logger)
                    await surface.select_option(ref, render(step.option, values, secrets))
                elif action == "extract":
                    ref = await resolve_target_async(surface, step.target, logger=logger)
                    raw_value = await surface.read_value(ref)
                    out_param = next(o for o in cap.outputs if o.name == step.save_as)
                    if not matches_value_type(raw_value, out_param.type):
                        failure = _fail(i, action, f"a value matching type {out_param.type!r}", repr(raw_value))
                        await _call_escalate(escalate, "extracted value failed its declared type", {"capability": cap.name, "step_index": i})
                        return ReplayResult(**base(status="FAILED", failure=failure))
                    outputs[step.save_as] = raw_value
                else:
                    raise AssertionError(f"unknown action {action!r}")
                break   # step succeeded, no transient failure
            except ResolutionError as exc:
                failure = _fail(i, action, str(exc), "neither primary nor fallback resolved")
                await _call_escalate(escalate, "could not resolve the target element", {"capability": cap.name, "step_index": i})
                return ReplayResult(**base(status="FAILED", failure=failure))
            except TransientFailure as exc:
                attempts += 1
                logger(f"step {i} ({action}): transient failure ({exc}), attempt {attempts}")
                if not retryable or attempts > max_retries:
                    failure = _fail(i, action, "the step to succeed", f"transient failure after {attempts} attempt(s): {exc}")
                    await _call_escalate(escalate, "step failed after retries", {"capability": cap.name, "step_index": i})
                    return ReplayResult(**base(status="FAILED", failure=failure))
                continue   # retry the same step

        url, text = await surface.current_url(), await surface.page_text()
        if step.expect is not None and not condition_matches(step.expect, url, text):
            failure = _fail(i, action, f"url_contains={step.expect.url_contains!r} text_present={step.expect.text_present!r}",
                             f"url={url!r} text={text[:200]!r}")
            await _call_escalate(escalate, "a step's own expect condition did not hold", {"capability": cap.name, "step_index": i})
            return ReplayResult(**base(status="FAILED", failure=failure))

        outcome_result = await _check_outcomes_async(cap, i, url, text, escalate, base, logger)
        if outcome_result is not None:
            return outcome_result

    url, text = await surface.current_url(), await surface.page_text()
    if not condition_matches(cap.checkpoint, url, text):
        failure = _fail(len(cap.steps) - 1, "checkpoint",
                         f"url_contains={cap.checkpoint.url_contains!r} text_present={cap.checkpoint.text_present!r}",
                         f"url={url!r} text={text[:200]!r}")
        await _call_escalate(escalate, "checkpoint did not match after all steps ran", {"capability": cap.name})
        return ReplayResult(**base(status="FAILED", failure=failure))

    declared = {o.name for o in cap.outputs}
    if set(outputs) != declared:
        failure = _fail(len(cap.steps) - 1, "extract", f"outputs {sorted(declared)}", f"got {sorted(outputs)}")
        return ReplayResult(**base(status="FAILED", failure=failure))

    return ReplayResult(**base(status="SUCCESS", outputs=outputs))
