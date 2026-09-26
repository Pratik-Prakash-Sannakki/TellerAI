# %% [markdown]
# # Phase 4: the replay engine
# Pure Python. No browser, no network, no API key, no `import playwright`. Run cells top to bottom.
#
# A `Capability` (Phase 2 v2, `notebooks/02_artifact_schema.py`) is data: ordered steps, locators,
# a checkpoint, outcome rules. This notebook is the engine that **walks** that data against a
# `ReplaySurface`, with no LLM anywhere in the loop (D6, 3.3). Every check below runs against a
# hand-built `FakeSurface` -- a dict-based fake DOM the test itself controls.
#
# **The seam this plugs into later (Phase 9, not built here):** the real `ReplaySurface`
# implementation will *wrap* agent.ipynb's own `PlaywrightSurface` (STEP 1) and its
# lock/banner/`human_takeover`/decision-bar mechanism (STEP 2/3). Replay is a new, **non-LLM
# caller** of that exact same Surface and safety layer -- it is not reinventing browser
# automation, and this notebook never touches Playwright to prove that the engine logic itself
# (locator resolution, template substitution, the risk gate, outcome rules, the checkpoint) is
# correct on its own, independent of any browser.
#
# The `escalate` hook plays the same role `human_takeover`/the decision bar plays in agent.ipynb:
# a place to hand control to a person. Here it is just a callable the tests can fake; Phase 9
# wires it to the real mechanism.

# %% Section 1: load the Phase 2 (v2) schema
# The Phase 2 models are NOT copied. We run the model cells of 02_artifact_schema.py in this
# namespace -- the same technique notebooks/03_recorder.py already uses. `ReplayResult`, `Failure`,
# `check_result`, `Capability`, `Target`, and friends all come from there, unmodified.
import pathlib
import re
from typing import Any, Callable, Protocol, runtime_checkable


def _find_repo() -> pathlib.Path:
    here = pathlib.Path(globals().get("__file__", ".")).resolve()
    for p in [pathlib.Path.cwd(), *pathlib.Path.cwd().parents, here.parent, *here.parents]:
        if (p / "notebooks" / "02_artifact_schema.py").exists():
            return p
    raise FileNotFoundError("cannot find notebooks/02_artifact_schema.py. Start the kernel in the repo.")


REPO = _find_repo()
EX = REPO / "artifacts" / "examples"


def load_schema(wanted=("Section 1:", "Section 2:", "Section 2a:", "Section 3:", "Section 4:")) -> None:
    """Run the non-check cells of the Phase 2 notebook in this namespace. Cells whose header does
    not start with exactly one of `wanted` (every `*b`-suffixed checks cell) are skipped."""
    text = (REPO / "notebooks" / "02_artifact_schema.py").read_text()
    for cell in re.split(r"(?m)^# %%", text)[1:]:
        header, _, body = cell.partition("\n")
        if header.strip().startswith(wanted):
            exec(compile(body, f"02_artifact_schema.py [{header.strip()}]", "exec"), globals())


load_schema()
print("schema loaded:", Capability.__name__, "|", ReplayResult.__name__, "| repo:", REPO.name)

# %% Section 2: ReplaySurface protocol and exceptions
@runtime_checkable
class ReplaySurface(Protocol):
    """What a real Playwright-backed surface will implement in Phase 9 (see the markdown cell
    above). A `navigate` step needs a way to change the page -- the brief's own method list for
    this Protocol did not include one, but every other step type has nothing to dispatch to
    without it, so it is added here; a small, easily-reversible Protocol addition, not a fork."""
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


def describe_target(target: "Target") -> str:
    parts = [f"primary: {describe_locator(target.primary)}"]
    if target.fallback is not None:
        parts.append(f"fallback: {describe_locator(target.fallback)}")
    return "; ".join(parts)


class TransientFailure(Exception):
    """A surface raises this for a step that should be retried (D26): the page was not ready
    yet. Only steps the engine treats as retryable (everything except a risky click) retry."""


class ResolutionError(Exception):
    """Neither the primary nor the fallback locator resolved to an element."""
    def __init__(self, target: "Target"):
        self.target = target
        super().__init__(describe_target(target))


class InputValidationError(Exception):
    """A caller-supplied input is missing, mistyped, or does not match its declared pattern."""


# %% Section 2b: checks for the protocol and exceptions
class _MinimalSurface:
    """The smallest object that satisfies ReplaySurface -- just to prove the Protocol's shape."""
    def navigate(self, path): pass
    def resolve(self, locator): return None
    def click(self, ref): pass
    def type_text(self, ref, value): pass
    def select_option(self, ref, value): pass
    def read_value(self, ref): return ""
    def current_url(self): return "/"
    def page_text(self): return ""


assert isinstance(_MinimalSurface(), ReplaySurface)
for exc_cls in (TransientFailure, ResolutionError, InputValidationError):
    assert issubclass(exc_cls, Exception)
try:
    raise ResolutionError(Target(primary=RoleLocator(role="button", name="Log In", note="n")))
except ResolutionError as exc:
    assert "primary" in str(exc), exc
print("protocol + exceptions: all checks passed")

# %% Section 3: resolve_target, template substitution, input validation
def _target_locators(target: "Target") -> list[tuple[str, "Any"]]:
    """Pure: the try-order for a target -- primary, then fallback if present (D63). No surface
    call, no logging. Shared by resolve_target (sync, right below) and resolve_target_async
    (Section 8) so the sync and async engines can never disagree about which locator is tried, or
    in which order (D77)."""
    locs = [("primary", target.primary)]
    if target.fallback is not None:
        locs.append(("fallback", target.fallback))
    return locs


def resolve_target(surface: ReplaySurface, target: "Target", *, logger: Callable[[str], None] = lambda m: None):
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


SecretResolver = Callable[[str], str]


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


def validate_inputs(cap: "Capability", raw_inputs: dict[str, str]) -> dict[str, str]:
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
    Reuses the exact template syntax and regex from the Phase 2 schema (D29, D32) -- `_TEMPLATE`
    is the same compiled pattern object loaded by Section 1, not a re-implementation."""
    def repl(m):
        is_secret, name = bool(m.group(1)), m.group(2)
        return secrets(name) if is_secret else values[name]
    return _TEMPLATE.sub(repl, text)


# %% Section 3b: checks for resolve_target, template substitution, input validation
class _DictSurface:
    """Just enough of a surface to test resolve_target in isolation: resolve(locator) looks up a
    fixed dict by (strategy, ...) key."""
    def __init__(self, hits: dict[tuple, Any]):
        self.hits = hits
    def resolve(self, locator):
        if locator.strategy == "role":
            return self.hits.get(("role", locator.role, locator.name))
        if locator.strategy == "text":
            return self.hits.get(("text", locator.text))
        return None


primary = RoleLocator(role="button", name="Log In", note="n")
fallback = TextLocator(text="Log In", note="n")
target = Target(primary=primary, fallback=fallback)

# primary resolves -> used directly, logged
log: list[str] = []
assert resolve_target(_DictSurface({("role", "button", "Log In"): 1}), target, logger=log.append) == 1
assert any("primary" in line for line in log)

# primary misses, fallback resolves -> still works, logged as a fallback
log.clear()
assert resolve_target(_DictSurface({("text", "Log In"): 2}), target, logger=log.append) == 2
assert any("fallback" in line for line in log)

# both miss -> ResolutionError naming both
try:
    resolve_target(_DictSurface({}), target)
    raise AssertionError("was NOT rejected")
except ResolutionError as exc:
    assert "primary" in str(exc) and "fallback" in str(exc)

# template substitution: {{input}} and {{secret:name}}
assert render("id={{account_id}}, pw={{secret:password}}", {"account_id": "42"}, lambda name: f"SECRET[{name}]") \
    == "id=42, pw=SECRET[password]"

# matches_value_type: basic format checks per declared type
assert matches_value_type("42", "integer") and not matches_value_type("x", "integer")
assert matches_value_type("$1,200.00", "currency") and not matches_value_type("free", "currency")
assert matches_value_type("anything", "string")

# validate_inputs: type/pattern-checked, extras and missing required both refused
CHECK_CAP = Capability.model_validate({
    "schema_version": 1, "name": "check_cap", "version": 1, "status": "draft",
    "description": "d", "base_url": "https://x.example", "risk_level": "safe",
    "inputs": [{"name": "n", "type": "string", "description": "d", "pattern": "^[0-9]+$"}],
    "outputs": [], "secrets": [],
    "steps": [{"action": "navigate", "path": "/x"}],
    "checkpoint": {"url_contains": "x", "text_present": "x"},
})
assert validate_inputs(CHECK_CAP, {"n": "7"}) == {"n": "7"}
for bad_inputs, why in [({"n": "abc"}, "pattern"), ({}, "missing"), ({"n": "1", "extra": "y"}, "undeclared")]:
    try:
        validate_inputs(CHECK_CAP, bad_inputs)
        raise AssertionError(f"was NOT rejected ({why})")
    except InputValidationError:
        pass

print("resolve_target + templates + input validation: all checks passed")

# %% Section 4: run_capability -- the engine loop
def parse_amount(raw: str) -> float:
    """An amount we cannot parse is treated as infinite -- it always needs approval, it is
    never silently auto-approved."""
    try:
        return float(raw.replace("$", "").replace(",", "").strip())
    except ValueError:
        return float("inf")


def condition_matches(cond: "Condition", url: str, text: str) -> bool:
    if cond.url_contains and cond.url_contains not in url:
        return False
    if cond.text_present and cond.text_present not in text:
        return False
    return True


def _fail(step_index: int, step_action: str, expected: str, observed: str) -> "Failure":
    return Failure(step_index=step_index, step_action=step_action, expected=expected, observed=observed)


def _find_outcome_rule(cap: "Capability", url: str, text: str):
    """Pure: the first outcome rule (in declared order) whose condition matches (D10 -- first
    match wins). No escalate call, no logging. Shared by _check_outcomes (sync, right below) and
    _check_outcomes_async (Section 9) so the sync and async engines can never pick a different
    rule (D77)."""
    for rule in cap.outcome_rules:
        if condition_matches(rule.when, url, text):
            return rule
    return None


def _is_approved(decision: Any) -> bool:
    """Pure: what a risky click's `escalate(reason, ctx)` return value means (D82). Exactly the
    string `"approve"` means "proceed with this click"; anything else -- `None` (every existing
    fake escalate's implicit return, unchanged), a rejection string, a coroutine's other result --
    means "no decision, stay NEEDS_APPROVAL". Shared by run_capability's and run_capability_async's
    risky-click branches so the two engines can never disagree about what counts as approval,
    the same pattern D77 already used for `_target_locators`/`_find_outcome_rule`."""
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
    # surface and, for relogin, capability composition -- both are Phase 9 work. Neither
    # example artifact's outcome rules exercise this path mid-run.
    logger(f"step {step_index}: recoverable condition matched (action={rule.action}): {rule.message}")
    return None


def run_capability(
    cap: "Capability",
    surface: ReplaySurface,
    inputs: dict[str, str],
    secrets: SecretResolver,
    *,
    run_id: str = "run",
    auto_approve_limit: float = 500.0,
    escalate: Callable[[str, dict], Any] | None = None,
    max_retries: int = 2,
    logger: Callable[[str], None] = lambda m: None,
) -> "ReplayResult":
    """Run every step of `cap` against `surface`, no LLM in the loop (D6, 3.3). `escalate`, when
    given, is called for NEEDS_APPROVAL and for an unrecoverable hard failure -- Phase 9 wires it
    to agent.ipynb's real human_takeover/decision-bar mechanism; here it is only a seam,
    exercised in tests by a fake.

    For a risky click at/above `auto_approve_limit`, `escalate`'s return value is now consulted
    (D82): exactly the string `"approve"` means resolve the target and click it for real, then
    continue to the remaining steps; anything else (including the default `None`) means stay
    `NEEDS_APPROVAL`, unchanged from before. `escalate` itself must never perform the click."""
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
                            if not _is_approved(decision):   # D82: unchanged NEEDS_APPROVAL behavior
                                return ReplayResult(**base(status="NEEDS_APPROVAL", pending_step=i, reason=reason))
                            # D82: escalate approved this click -- fall through to the exact same
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


# %% Section 4b: checks for run_capability -- the 8 required scenarios, plus 3 extra
def _locator_key(loc) -> tuple:
    if loc.strategy == "role":
        return ("role", loc.role, loc.name)
    if loc.strategy == "label":
        return ("label", loc.label)
    if loc.strategy == "text":
        return ("text", loc.text)
    if loc.strategy == "structure":
        return ("structure", loc.tag, loc.nth, loc.within.role)
    if loc.strategy == "labeled_value":
        return ("labeled_value", loc.label)
    raise ValueError(f"unknown strategy {loc.strategy}")


class FakeSurface:
    """A dict-based fake DOM: pages by url, a locator registry per url, and per-ref state. No
    browser, no network -- everything is set up by the test itself."""

    def __init__(self):
        self.url = "/start"
        self.pages: dict[str, str] = {}
        self.registry: dict[str, dict[tuple, int]] = {}
        self.values: dict[int, str] = {}
        self.click_effects: dict[int, Callable[["FakeSurface"], None]] = {}
        self.clicked: list[int] = []
        self.typed: dict[int, str] = {}
        self.selected: dict[int, str] = {}
        self.navigated: list[str] = []
        self.transient: dict[tuple, int] = {}

    def set_page(self, url: str, text: str) -> None:
        self.pages[url] = text

    def register(self, url: str, locator, ref: int) -> None:
        self.registry.setdefault(url, {})[_locator_key(locator)] = ref

    def set_value(self, ref: int, value: str) -> None:
        self.values[ref] = value

    def fail_next(self, action: str, key, times: int) -> None:
        self.transient[(action, key)] = times

    def _maybe_fail(self, action: str, key) -> None:
        left = self.transient.get((action, key), 0)
        if left > 0:
            self.transient[(action, key)] = left - 1
            raise TransientFailure(f"{action} not ready yet ({key!r})")

    def navigate(self, path: str) -> None:
        self._maybe_fail("navigate", path)
        self.navigated.append(path)
        self.url = path

    def resolve(self, locator):
        return self.registry.get(self.url, {}).get(_locator_key(locator))

    def click(self, ref: int) -> None:
        self._maybe_fail("click", ref)
        self.clicked.append(ref)
        effect = self.click_effects.get(ref)
        if effect:
            effect(self)

    def type_text(self, ref: int, value: str) -> None:
        self._maybe_fail("type", ref)
        self.typed[ref] = value

    def select_option(self, ref: int, value: str) -> None:
        self._maybe_fail("select", ref)
        self.selected[ref] = value

    def read_value(self, ref: int) -> str:
        return self.values.get(ref, "")

    def current_url(self) -> str:
        return self.url

    def page_text(self) -> str:
        return self.pages.get(self.url, "")


def no_secrets(name: str) -> str:
    raise AssertionError(f"no secret should be needed in this test, asked for {name!r}")


TEST_CAP = Capability.model_validate({
    "schema_version": 1, "name": "test_flow", "version": 1, "status": "draft",
    "description": "A tiny capability used only to test the replay engine.",
    "base_url": "https://fake.example", "risk_level": "safe",
    "inputs": [{"name": "item_id", "type": "string", "description": "id", "pattern": "^[0-9]+$"}],
    "outputs": [{"name": "value", "type": "integer", "description": "extracted value"}],
    "secrets": [],
    "steps": [
        {"action": "navigate", "path": "/item.htm?id={{item_id}}"},
        {"action": "click", "target": {
            "primary": {"strategy": "role", "role": "button", "name": "Show", "note": "n"},
            "fallback": {"strategy": "text", "text": "Show", "note": "n"},
        }},
        {"action": "extract", "target": {
            "primary": {"strategy": "labeled_value", "label": "Value:", "note": "n"}},
            "save_as": "value"},
    ],
    "checkpoint": {"url_contains": "item.htm", "text_present": "Value:"},
    "outcome_rules": [
        {"when": {"text_present": "Not Found"}, "kind": "business", "outcome": "ITEM_NOT_FOUND", "message": "no such item"},
        {"when": {"text_present": "Internal Error"}, "kind": "hard", "message": "internal error"},
    ],
})

RISKY_CAP = Capability.model_validate({
    "schema_version": 1, "name": "test_pay", "version": 1, "status": "draft",
    "description": "A tiny risky capability used only to test the replay engine.",
    "base_url": "https://fake.example", "risk_level": "risky",
    "inputs": [{"name": "amount", "type": "currency", "description": "amount", "pattern": r"^\$?[0-9]+(\.[0-9]{2})?$"}],
    "outputs": [], "secrets": [],
    "steps": [
        {"action": "navigate", "path": "/pay.htm"},
        {"action": "click", "risk": "risky", "amount_input": "amount", "target": {
            "primary": {"strategy": "role", "role": "button", "name": "Pay", "note": "n"}}},
    ],
    "checkpoint": {"url_contains": "pay.htm", "text_present": "Paid"},
    "outcome_rules": [],
})


def new_happy_surface() -> FakeSurface:
    s = FakeSurface()
    url = "/item.htm?id=42"
    s.set_page(url, "Item page. Value: 99")
    s.register(url, TEST_CAP.steps[1].target.primary, 1)
    s.register(url, TEST_CAP.steps[1].target.fallback, 1)   # both resolve normally; test 3 removes the primary
    s.register(url, TEST_CAP.steps[2].target.primary, 2)
    s.set_value(2, "99")
    return s


# (1) happy path -> SUCCESS with correct outputs
result = run_capability(TEST_CAP, new_happy_surface(), {"item_id": "42"}, no_secrets)
assert result.status == "SUCCESS" and result.outputs == {"value": "99"}, result
print("test 1 (happy path): ok")

# (2) a business-outcome page state -> BUSINESS_OUTCOME with the declared outcome name
surface = FakeSurface()
url = "/item.htm?id=99"
surface.set_page(url, "Not Found: no such item")
surface.register(url, TEST_CAP.steps[1].target.primary, 1)
result = run_capability(TEST_CAP, surface, {"item_id": "99"}, no_secrets)
assert result.status == "BUSINESS_OUTCOME" and result.outcome == "ITEM_NOT_FOUND", result
print("test 2 (business outcome): ok")

# (3) primary locator fails, fallback succeeds -> still SUCCESS, and this is observable/logged
surface = new_happy_surface()
url = "/item.htm?id=42"
del surface.registry[url][_locator_key(TEST_CAP.steps[1].target.primary)]   # primary can't resolve
log = []
result = run_capability(TEST_CAP, surface, {"item_id": "42"}, no_secrets, logger=log.append)
assert result.status == "SUCCESS", result
assert any("fallback" in line for line in log), log
print("test 3 (fallback observed):", [l for l in log if "fallback" in l][0])

# (4) both locators fail -> FAILED with step/expected/observed detail
surface = FakeSurface()
url = "/item.htm?id=1"
surface.set_page(url, "Item page. Value: 1")   # click's target is never registered at all
result = run_capability(TEST_CAP, surface, {"item_id": "1"}, no_secrets)
assert result.status == "FAILED", result
assert result.failure.step_index == 1 and result.failure.step_action == "click"
assert "primary" in result.failure.expected and "fallback" in result.failure.expected
print("test 4 (both locators fail):", result.failure.expected, "|", result.failure.observed)

# (5) risky step with amount below the limit -> proceeds automatically, SUCCESS
surface = FakeSurface()
surface.register("/pay.htm", RISKY_CAP.steps[1].target.primary, 7)
surface.click_effects[7] = lambda s: s.set_page("/pay.htm", "Paid. Thank you.")
result = run_capability(RISKY_CAP, surface, {"amount": "100.00"}, no_secrets, auto_approve_limit=500.0)
assert result.status == "SUCCESS", result
assert surface.clicked == [7]
print("test 5 (risky under limit, auto-approved): ok")

# (6) risky step with amount at/above the limit -> NEEDS_APPROVAL, escalate called, no click
surface = FakeSurface()
surface.register("/pay.htm", RISKY_CAP.steps[1].target.primary, 7)
calls = []
result = run_capability(RISKY_CAP, surface, {"amount": "600.00"}, no_secrets,
                         auto_approve_limit=500.0, escalate=lambda reason, ctx: calls.append((reason, ctx)))
assert result.status == "NEEDS_APPROVAL" and result.pending_step == 1, result
assert len(calls) == 1 and "500" in calls[0][0]
assert 7 not in surface.clicked
print("test 6 (risky at limit, escalated, not clicked): ok")

# (7) checkpoint fails after all steps ran -> FAILED
surface = new_happy_surface()
surface.set_page("/item.htm?id=42", "Item page, no value shown here")   # no 'Value:' text -> checkpoint fails
result = run_capability(TEST_CAP, surface, {"item_id": "42"}, no_secrets)
assert result.status == "FAILED" and result.failure.step_action == "checkpoint", result
print("test 7 (checkpoint fails):", result.failure.observed)

# (8) a declared output whose extracted value fails its declared type/format -> FAILED
surface = new_happy_surface()
surface.set_value(2, "not-a-number")   # declared type is 'integer'
result = run_capability(TEST_CAP, surface, {"item_id": "42"}, no_secrets)
assert result.status == "FAILED" and result.failure.step_action == "extract", result
print("test 8 (bad output type/format):", result.failure.observed)

# bonus: transient failure retried, then succeeds (D26)
surface = new_happy_surface()
surface.fail_next("click", 1, times=2)
result = run_capability(TEST_CAP, surface, {"item_id": "42"}, no_secrets)
assert result.status == "SUCCESS", result
print("bonus (retried transient failure): ok")

# bonus: transient failure past the retry bound -> FAILED, never silently retried forever
surface = new_happy_surface()
surface.fail_next("click", 1, times=5)
result = run_capability(TEST_CAP, surface, {"item_id": "42"}, no_secrets, max_retries=2)
assert result.status == "FAILED" and "transient failure" in result.failure.observed, result
print("bonus (retries exhausted): ok")

# bonus: a risky click is NEVER retried on a transient failure (D26), even under the limit
surface = FakeSurface()
surface.register("/pay.htm", RISKY_CAP.steps[1].target.primary, 7)
surface.fail_next("click", 7, times=1)
result = run_capability(RISKY_CAP, surface, {"amount": "10.00"}, no_secrets)
assert result.status == "FAILED", result
print("bonus (risky click never retried): ok")

print("replay engine: all offline checks passed")

# %% Section 5: integration check -- both REAL example artifacts through the engine
# This is the check that proves Task A's simplified schema and Task B's engine actually agree
# with each other end to end: it builds a FakeSurface for each example by registering exactly
# the locators that artifact's own YAML declares (not a stand-in shape), then replays it.
bal = from_yaml((EX / "get_account_balance.yaml").read_text())
xfer = from_yaml((EX / "transfer_funds.yaml").read_text())


def resolve_secret(name: str) -> str:
    raise AssertionError("no secret is used by either example artifact")


# ---- get_account_balance ----
bal_surface = FakeSurface()
bal_url = "/activity.htm?id=13344"
bal_surface.set_page(bal_url, "Account Details\nBalance: $1,200.00")
bal_extract = next(s for s in bal.steps if s.action == "extract")
bal_surface.register(bal_url, bal_extract.target.primary, 1)
bal_surface.set_value(1, "$1,200.00")

bal_result = run_capability(bal, bal_surface, {"account_id": "13344"}, resolve_secret, run_id="evidence-1")
assert bal_result.status == "SUCCESS", bal_result
assert bal_result.outputs == {"balance": "$1,200.00"}
check_result(bal, bal_result)   # cross-check against the capability itself (D39)
print("integration (get_account_balance):", bal_result.status, bal_result.outputs)

# same artifact, bad account id -> the business outcome declared in its own outcome_rules
bad_surface = FakeSurface()
bad_url = "/activity.htm?id=00000"
bad_surface.set_page(bad_url, "Could not find account 00000")
bad_result = run_capability(bal, bad_surface, {"account_id": "00000"}, resolve_secret, run_id="evidence-1b")
assert bad_result.status == "BUSINESS_OUTCOME" and bad_result.outcome == "ACCOUNT_NOT_FOUND", bad_result
check_result(bal, bad_result)
print("integration (get_account_balance, bad id):", bad_result.status, bad_result.outcome)

# ---- transfer_funds ----
xfer_surface = FakeSurface()
xurl = "/transfer.htm"
xfer_surface.set_page(xurl, "Transfer Funds\nAmount: From account #: To account #:")
xfer_type, xfer_sel1, xfer_sel2, xfer_click, xfer_extract = (s for s in xfer.steps if s.action != "navigate")
xfer_surface.register(xurl, xfer_type.target.primary, 10)
xfer_surface.register(xurl, xfer_type.target.fallback, 10)
xfer_surface.register(xurl, xfer_sel1.target.primary, 11)
xfer_surface.register(xurl, xfer_sel2.target.primary, 12)
xfer_surface.register(xurl, xfer_click.target.primary, 13)
xfer_surface.register(xurl, xfer_extract.target.primary, 14)
xfer_surface.set_value(14, "Transfer Complete!")
xfer_surface.click_effects[13] = lambda s: s.set_page(xurl, "Transfer Complete! $20.00 has moved.")

xfer_inputs = {"from_account": "13344", "to_account": "13355", "amount": "20.00"}
xfer_result = run_capability(xfer, xfer_surface, xfer_inputs, resolve_secret, run_id="evidence-2", auto_approve_limit=500.0)
assert xfer_result.status == "SUCCESS", xfer_result
assert xfer_result.outputs == {"confirmation": "Transfer Complete!"}
assert xfer_surface.typed[10] == "20.00" and xfer_surface.selected[11] == "13344" and xfer_surface.selected[12] == "13355"
assert xfer_surface.clicked == [13]
check_result(xfer, xfer_result)
print("integration (transfer_funds, under limit):", xfer_result.status, xfer_result.outputs)

# same artifact, amount at/above the limit -> NEEDS_APPROVAL, the Transfer button never clicked
xfer_surface2 = FakeSurface()
xfer_surface2.set_page(xurl, "Transfer Funds\nAmount: From account #: To account #:")
xfer_surface2.register(xurl, xfer_type.target.primary, 10)
xfer_surface2.register(xurl, xfer_sel1.target.primary, 11)
xfer_surface2.register(xurl, xfer_sel2.target.primary, 12)
xfer_surface2.register(xurl, xfer_click.target.primary, 13)
approvals = []
xfer_result2 = run_capability(
    xfer, xfer_surface2, {"from_account": "13344", "to_account": "13355", "amount": "999.00"},
    resolve_secret, run_id="evidence-3", auto_approve_limit=500.0,
    escalate=lambda reason, ctx: approvals.append((reason, ctx)),
)
assert xfer_result2.status == "NEEDS_APPROVAL" and xfer_result2.pending_step == 4, xfer_result2
assert 13 not in xfer_surface2.clicked
assert len(approvals) == 1
print("integration (transfer_funds, over limit):", xfer_result2.status, xfer_result2.reason)

# D82 fix: over-limit click, escalate returns "approve" -> the engine clicks the target itself,
# continues to the remaining steps (extract, checkpoint), reaches SUCCESS with the real
# confirmation. This is the exact real-world shape the bug was in (a risky click followed by an
# extract step and a checkpoint), same fixture as the two tests just above.
xfer_surface3 = FakeSurface()
xfer_surface3.set_page(xurl, "Transfer Funds\nAmount: From account #: To account #:")
xfer_surface3.register(xurl, xfer_type.target.primary, 10)
xfer_surface3.register(xurl, xfer_sel1.target.primary, 11)
xfer_surface3.register(xurl, xfer_sel2.target.primary, 12)
xfer_surface3.register(xurl, xfer_click.target.primary, 13)
xfer_surface3.register(xurl, xfer_extract.target.primary, 14)
xfer_surface3.set_value(14, "Transfer Complete!")
xfer_surface3.click_effects[13] = lambda s: s.set_page(xurl, "Transfer Complete! $999.00 has moved.")
approve_calls = []
xfer_result3 = run_capability(
    xfer, xfer_surface3, {"from_account": "13344", "to_account": "13355", "amount": "999.00"},
    resolve_secret, run_id="evidence-4", auto_approve_limit=500.0,
    escalate=lambda reason, ctx: (approve_calls.append((reason, ctx)), "approve")[1],
)
assert xfer_result3.status == "SUCCESS", xfer_result3
assert xfer_result3.outputs == {"confirmation": "Transfer Complete!"}
assert xfer_surface3.clicked == [13]
assert len(approve_calls) == 1
check_result(xfer, xfer_result3)
print("integration (transfer_funds, escalate approves over-limit click):", xfer_result3.status, xfer_result3.outputs)

# D82: escalate approves, but the target cannot be resolved at that point -> FAILED, not a silent
# success and not NEEDS_APPROVAL. The Transfer button is deliberately never registered.
xfer_surface4 = FakeSurface()
xfer_surface4.set_page(xurl, "Transfer Funds\nAmount: From account #: To account #:")
xfer_surface4.register(xurl, xfer_type.target.primary, 10)
xfer_surface4.register(xurl, xfer_sel1.target.primary, 11)
xfer_surface4.register(xurl, xfer_sel2.target.primary, 12)
xfer_result4 = run_capability(
    xfer, xfer_surface4, {"from_account": "13344", "to_account": "13355", "amount": "999.00"},
    resolve_secret, run_id="evidence-5", auto_approve_limit=500.0,
    escalate=lambda reason, ctx: "approve",
)
assert xfer_result4.status == "FAILED" and xfer_result4.failure.step_action == "click", xfer_result4
assert 13 not in xfer_surface4.clicked
print("integration (transfer_funds, escalate approves but target unresolvable):",
      xfer_result4.status, xfer_result4.failure.observed)

# D82: escalate returns a plain non-"approve" string ("reject") -> unchanged NEEDS_APPROVAL, click
# never called -- same contract the None-returning fake above already proved, with a different
# non-"approve" value.
xfer_surface5 = FakeSurface()
xfer_surface5.set_page(xurl, "Transfer Funds\nAmount: From account #: To account #:")
xfer_surface5.register(xurl, xfer_type.target.primary, 10)
xfer_surface5.register(xurl, xfer_sel1.target.primary, 11)
xfer_surface5.register(xurl, xfer_sel2.target.primary, 12)
xfer_surface5.register(xurl, xfer_click.target.primary, 13)
xfer_result5 = run_capability(
    xfer, xfer_surface5, {"from_account": "13344", "to_account": "13355", "amount": "999.00"},
    resolve_secret, run_id="evidence-6", auto_approve_limit=500.0,
    escalate=lambda reason, ctx: "reject",
)
assert xfer_result5.status == "NEEDS_APPROVAL" and xfer_result5.pending_step == 4, xfer_result5
assert 13 not in xfer_surface5.clicked
print("integration (transfer_funds, escalate returns non-approve string):", xfer_result5.status, xfer_result5.reason)

print("\nINTEGRATION CHECKS PASSED")

# %% [markdown]
# ## Section 6 -- the async mirror, and why it exists
#
# Everything from here down (Sections 7-10) is a **parallel async engine**, not a rewrite of the
# sync one above. It exists for one reason: `notebooks/agent.ipynb`'s real browser control is
# entirely `async` -- Playwright's Python API has no sync mode usable inside a Jupyter kernel, and
# the kernel already runs its own asyncio event loop. Bridging a sync engine that needs to call
# into that async browser layer (something like
# `asyncio.get_event_loop().run_until_complete(...)`) breaks with "this event loop is already
# running" the moment it is tried from inside a kernel that is already running one. So
# `run_capability` (Sections 1-5, above) is left exactly as it is -- unmodified, its 11+ tests
# still passing unchanged (confirmed by running this whole file top to bottom after every edit
# below), still the real, already-verified cross-phase integration with Phase 3's saved YAML
# output -- and `run_capability_async` is added ALONGSIDE it for `notebooks/05_replay_live.py` to
# call against a real Playwright-backed surface.
#
# **This is not new business logic.** `run_capability_async` makes the same decisions, in the
# same order, for the same reasons, as `run_capability`: same input validation before anything
# touches the page, same primary-then-fallback target resolution, same risky-click gate checked
# BEFORE the click (never after), same outcome-rule order (first declared match wins), same
# bounded retries (never for a risky click), same checkpoint/output checks, same four
# `ReplayResult` statuses. Two small, PURE (no surface call, no escalate call) helpers --
# `_target_locators` (which locator to try, in which order -- Section 3) and `_find_outcome_rule`
# (which outcome rule matches first -- Section 4) -- were factored out of the existing sync cells
# so the sync and async engines call the exact same decision logic instead of two copies that
# could silently drift apart. The one genuine difference is `escalate`: `run_capability_async`
# awaits it if it returns something awaitable (Section 8's `_call_escalate`), since handing
# control to a real person is inherently an awaitable action in a real browser, and the entire
# point of this mirror existing is to let that finish before the function returns. See D77 in
# DECISIONS.md for the full reasoning, including why this one asymmetry does not count as a
# business-logic change.
#
# **Any future change to `run_capability`'s business logic must also be made to
# `run_capability_async`** (or, if the two are drifting apart in ways that are hard to keep in
# sync by hand, the shared pure logic should be factored out further at that time, the same way
# `_target_locators`/`_find_outcome_rule` were factored out now).

# %% Section 7: AsyncReplaySurface protocol (mirrors Section 2, all methods async)
@runtime_checkable
class AsyncReplaySurface(Protocol):
    """The async twin of ReplaySurface (Section 2). Same method names, same meanings -- every
    method is `async def` instead, because the real implementation
    (`notebooks/05_replay_live.py`) wraps Playwright, which has no usable sync API inside a
    Jupyter kernel that already runs its own asyncio event loop (see the markdown cell above).
    This is not a new contract: a class satisfying ReplaySurface and a class satisfying
    AsyncReplaySurface are asked to do exactly the same eight things, awaited instead of called
    directly."""
    async def navigate(self, path: str) -> None: ...
    async def resolve(self, locator) -> Any | None: ...
    async def click(self, ref) -> None: ...
    async def type_text(self, ref, value: str) -> None: ...
    async def select_option(self, ref, value: str) -> None: ...
    async def read_value(self, ref) -> str: ...
    async def current_url(self) -> str: ...
    async def page_text(self) -> str: ...


# %% Section 7b: checks for AsyncReplaySurface
class _MinimalAsyncSurface:
    """The smallest object that satisfies AsyncReplaySurface -- the async twin of _MinimalSurface
    (Section 2b)."""
    async def navigate(self, path): pass
    async def resolve(self, locator): return None
    async def click(self, ref): pass
    async def type_text(self, ref, value): pass
    async def select_option(self, ref, value): pass
    async def read_value(self, ref): return ""
    async def current_url(self): return "/"
    async def page_text(self): return ""


# Note: like Section 2b's isinstance check, a runtime_checkable Protocol only checks that the
# NAMES exist, not that they are async -- so a plain sync _MinimalSurface would also pass this
# isinstance check. This is a known Python limitation (Protocol does not inspect coroutine-ness),
# not something either notebook works around, and it is the same in both places for consistency.
assert isinstance(_MinimalAsyncSurface(), AsyncReplaySurface)
print("async protocol: all checks passed")

# %% Section 8: resolve_target_async, and the escalate-awaiting helper
import inspect


async def resolve_target_async(surface: AsyncReplaySurface, target: "Target", *,
                                logger: Callable[[str], None] = lambda m: None):
    """Async twin of resolve_target (Section 3). Same try-order (`_target_locators`, Section 3 --
    a PURE function with no surface calls, shared by both engines so they can never disagree
    about which locator is tried first), same log wording -- only the resolve call itself is
    awaited."""
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
    plain sync escalate -- every offline test's fake, unchanged from the sync engine -- returns
    None or a plain value, which is not awaitable, so this is a complete no-op difference for
    every existing test (D77). This is the ONE place run_capability_async's behavior genuinely
    differs from run_capability's: escalate here may be an async callable, because handing
    control to a real person is an inherently awaitable action, and the whole reason this mirror
    exists is to let that finish before run_capability_async returns.

    Returns whatever `escalate` (or the coroutine it returned) itself returned -- `None` for every
    prior caller here, which all discard the return value, exactly as before. The risky-click
    branch (D82) is the one caller that now reads this to decide whether `escalate` said
    `"approve"`."""
    if escalate is None:
        return None
    result = escalate(reason, ctx)
    if inspect.isawaitable(result):
        return await result
    return result


# %% Section 8b: checks for resolve_target_async and _call_escalate
import asyncio


class _AsyncDictSurface:
    """Async twin of _DictSurface (Section 3b)."""
    def __init__(self, hits: dict[tuple, Any]):
        self.hits = hits

    async def resolve(self, locator):
        if locator.strategy == "role":
            return self.hits.get(("role", locator.role, locator.name))
        if locator.strategy == "text":
            return self.hits.get(("text", locator.text))
        return None


def _run(coro):
    return asyncio.run(coro)


# primary resolves -> used directly, logged (reuses `target` built in Section 3b)
_alog: list[str] = []
assert _run(resolve_target_async(_AsyncDictSurface({("role", "button", "Log In"): 1}), target, logger=_alog.append)) == 1
assert any("primary" in line for line in _alog)

# primary misses, fallback resolves -> still works, logged as a fallback
_alog.clear()
assert _run(resolve_target_async(_AsyncDictSurface({("text", "Log In"): 2}), target, logger=_alog.append)) == 2
assert any("fallback" in line for line in _alog)

# both miss -> ResolutionError naming both
try:
    _run(resolve_target_async(_AsyncDictSurface({}), target))
    raise AssertionError("was NOT rejected")
except ResolutionError as exc:
    assert "primary" in str(exc) and "fallback" in str(exc)

# _call_escalate: a sync fake's un-awaitable return is a no-op difference from calling it directly
_sync_calls: list = []
_run(_call_escalate(lambda r, c: _sync_calls.append((r, c)), "why", {"k": 1}))
assert _sync_calls == [("why", {"k": 1})]


# _call_escalate: an async fake IS awaited before _call_escalate returns
_async_calls: list = []


async def _fake_async_escalate(reason, ctx):
    await asyncio.sleep(0)
    _async_calls.append((reason, ctx))


_run(_call_escalate(_fake_async_escalate, "why2", {"k": 2}))
assert _async_calls == [("why2", {"k": 2})]

print("resolve_target_async + _call_escalate: all checks passed")

# %% Section 9: run_capability_async -- the async engine loop
async def _check_outcomes_async(cap, step_index, url, text, escalate, base, logger):
    """Async twin of _check_outcomes (Section 4). Uses the SAME `_find_outcome_rule` (Section 4,
    a pure function with no surface or escalate calls) to decide which rule matches, so the sync
    and async engines can never disagree about which rule fires first. Only the escalate call for
    a hard rule is awaited (via `_call_escalate`)."""
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
    cap: "Capability",
    surface: AsyncReplaySurface,
    inputs: dict[str, str],
    secrets: SecretResolver,
    *,
    run_id: str = "run",
    auto_approve_limit: float = 500.0,
    escalate: Callable[[str, dict], Any] | None = None,
    max_retries: int = 2,
    logger: Callable[[str], None] = lambda m: None,
) -> "ReplayResult":
    """Async twin of run_capability (Section 4). IDENTICAL behavior -- every surface call is
    awaited, and `escalate` is awaited too if it returns something awaitable (Section 8's
    `_call_escalate`, D77). No business logic differs: same input validation, same per-step
    resolution order, same risky-click gate BEFORE the click, same outcome-rule order, same retry
    bound (never for a risky click), same checkpoint/output checks, same four statuses. See the
    markdown cell at the top of Section 6.

    Same D82 approval contract as run_capability: a risky click's `escalate` return value of
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
                            if not _is_approved(decision):   # D82: unchanged NEEDS_APPROVAL behavior
                                return ReplayResult(**base(status="NEEDS_APPROVAL", pending_step=i, reason=reason))
                            # D82: escalate approved this click -- fall through to the exact same
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


# %% Section 9b: checks for run_capability_async -- the 8 required scenarios, plus 3 extra (async)
class AsyncFakeSurface:
    """Async twin of FakeSurface (Section 4b). Identical state and behavior -- every method is
    `async def`. `click_effects` callables stay plain sync functions: they only mutate the fake's
    own dict state, so there is nothing inside them that needs to be awaited."""

    def __init__(self):
        self.url = "/start"
        self.pages: dict[str, str] = {}
        self.registry: dict[str, dict[tuple, int]] = {}
        self.values: dict[int, str] = {}
        self.click_effects: dict[int, Callable[["AsyncFakeSurface"], None]] = {}
        self.clicked: list[int] = []
        self.typed: dict[int, str] = {}
        self.selected: dict[int, str] = {}
        self.navigated: list[str] = []
        self.transient: dict[tuple, int] = {}

    def set_page(self, url: str, text: str) -> None:
        self.pages[url] = text

    def register(self, url: str, locator, ref: int) -> None:
        self.registry.setdefault(url, {})[_locator_key(locator)] = ref

    def set_value(self, ref: int, value: str) -> None:
        self.values[ref] = value

    def fail_next(self, action: str, key, times: int) -> None:
        self.transient[(action, key)] = times

    def _maybe_fail(self, action: str, key) -> None:
        left = self.transient.get((action, key), 0)
        if left > 0:
            self.transient[(action, key)] = left - 1
            raise TransientFailure(f"{action} not ready yet ({key!r})")

    async def navigate(self, path: str) -> None:
        self._maybe_fail("navigate", path)
        self.navigated.append(path)
        self.url = path

    async def resolve(self, locator):
        return self.registry.get(self.url, {}).get(_locator_key(locator))

    async def click(self, ref: int) -> None:
        self._maybe_fail("click", ref)
        self.clicked.append(ref)
        effect = self.click_effects.get(ref)
        if effect:
            effect(self)

    async def type_text(self, ref: int, value: str) -> None:
        self._maybe_fail("type", ref)
        self.typed[ref] = value

    async def select_option(self, ref: int, value: str) -> None:
        self._maybe_fail("select", ref)
        self.selected[ref] = value

    async def read_value(self, ref: int) -> str:
        return self.values.get(ref, "")

    async def current_url(self) -> str:
        return self.url

    async def page_text(self) -> str:
        return self.pages.get(self.url, "")


def new_happy_async_surface() -> AsyncFakeSurface:
    s = AsyncFakeSurface()
    url = "/item.htm?id=42"
    s.set_page(url, "Item page. Value: 99")
    s.register(url, TEST_CAP.steps[1].target.primary, 1)
    s.register(url, TEST_CAP.steps[1].target.fallback, 1)
    s.register(url, TEST_CAP.steps[2].target.primary, 2)
    s.set_value(2, "99")
    return s


async def _run_async_checks() -> None:
    # (1) happy path -> SUCCESS with correct outputs
    result = await run_capability_async(TEST_CAP, new_happy_async_surface(), {"item_id": "42"}, no_secrets)
    assert result.status == "SUCCESS" and result.outputs == {"value": "99"}, result
    print("async test 1 (happy path): ok")

    # (2) a business-outcome page state -> BUSINESS_OUTCOME with the declared outcome name
    surface = AsyncFakeSurface()
    url = "/item.htm?id=99"
    surface.set_page(url, "Not Found: no such item")
    surface.register(url, TEST_CAP.steps[1].target.primary, 1)
    result = await run_capability_async(TEST_CAP, surface, {"item_id": "99"}, no_secrets)
    assert result.status == "BUSINESS_OUTCOME" and result.outcome == "ITEM_NOT_FOUND", result
    print("async test 2 (business outcome): ok")

    # (3) primary locator fails, fallback succeeds -> still SUCCESS, observable/logged
    surface = new_happy_async_surface()
    url = "/item.htm?id=42"
    del surface.registry[url][_locator_key(TEST_CAP.steps[1].target.primary)]
    log: list[str] = []
    result = await run_capability_async(TEST_CAP, surface, {"item_id": "42"}, no_secrets, logger=log.append)
    assert result.status == "SUCCESS", result
    assert any("fallback" in line for line in log), log
    print("async test 3 (fallback observed):", [l for l in log if "fallback" in l][0])

    # (4) both locators fail -> FAILED with step/expected/observed detail
    surface = AsyncFakeSurface()
    url = "/item.htm?id=1"
    surface.set_page(url, "Item page. Value: 1")
    result = await run_capability_async(TEST_CAP, surface, {"item_id": "1"}, no_secrets)
    assert result.status == "FAILED", result
    assert result.failure.step_index == 1 and result.failure.step_action == "click"
    assert "primary" in result.failure.expected and "fallback" in result.failure.expected
    print("async test 4 (both locators fail):", result.failure.expected, "|", result.failure.observed)

    # (5) risky step with amount below the limit -> proceeds automatically, SUCCESS
    surface = AsyncFakeSurface()
    surface.register("/pay.htm", RISKY_CAP.steps[1].target.primary, 7)
    surface.click_effects[7] = lambda s: s.set_page("/pay.htm", "Paid. Thank you.")
    result = await run_capability_async(RISKY_CAP, surface, {"amount": "100.00"}, no_secrets, auto_approve_limit=500.0)
    assert result.status == "SUCCESS", result
    assert surface.clicked == [7]
    print("async test 5 (risky under limit, auto-approved): ok")

    # (6) risky step with amount at/above the limit -> NEEDS_APPROVAL, escalate awaited, no click
    surface = AsyncFakeSurface()
    surface.register("/pay.htm", RISKY_CAP.steps[1].target.primary, 7)
    calls: list = []

    async def _fake_escalate(reason, ctx):
        calls.append((reason, ctx))

    result = await run_capability_async(RISKY_CAP, surface, {"amount": "600.00"}, no_secrets,
                                         auto_approve_limit=500.0, escalate=_fake_escalate)
    assert result.status == "NEEDS_APPROVAL" and result.pending_step == 1, result
    assert len(calls) == 1 and "500" in calls[0][0]
    assert 7 not in surface.clicked
    print("async test 6 (risky at limit, escalated [async fake], not clicked): ok")

    # (7) checkpoint fails after all steps ran -> FAILED
    surface = new_happy_async_surface()
    surface.set_page("/item.htm?id=42", "Item page, no value shown here")
    result = await run_capability_async(TEST_CAP, surface, {"item_id": "42"}, no_secrets)
    assert result.status == "FAILED" and result.failure.step_action == "checkpoint", result
    print("async test 7 (checkpoint fails):", result.failure.observed)

    # (8) a declared output whose extracted value fails its declared type/format -> FAILED
    surface = new_happy_async_surface()
    surface.set_value(2, "not-a-number")
    result = await run_capability_async(TEST_CAP, surface, {"item_id": "42"}, no_secrets)
    assert result.status == "FAILED" and result.failure.step_action == "extract", result
    print("async test 8 (bad output type/format):", result.failure.observed)

    # bonus: transient failure, then it recovers
    surface = new_happy_async_surface()
    surface.fail_next("click", 1, times=2)
    result = await run_capability_async(TEST_CAP, surface, {"item_id": "42"}, no_secrets)
    assert result.status == "SUCCESS", result
    print("async bonus (retried transient failure): ok")

    # bonus: transient failure past the retry limit
    surface = new_happy_async_surface()
    surface.fail_next("click", 1, times=5)
    result = await run_capability_async(TEST_CAP, surface, {"item_id": "42"}, no_secrets, max_retries=2)
    assert result.status == "FAILED" and "transient failure" in result.failure.observed, result
    print("async bonus (retries exhausted): ok")

    # bonus: risky click never retried
    surface = AsyncFakeSurface()
    surface.register("/pay.htm", RISKY_CAP.steps[1].target.primary, 7)
    surface.fail_next("click", 7, times=1)
    result = await run_capability_async(RISKY_CAP, surface, {"amount": "10.00"}, no_secrets)
    assert result.status == "FAILED", result
    print("async bonus (risky click never retried): ok")


asyncio.run(_run_async_checks())
print("async replay engine: all offline checks passed")

# %% Section 10: async integration check -- both REAL example artifacts through the async engine
async def _run_async_integration() -> None:
    bal2 = from_yaml((EX / "get_account_balance.yaml").read_text())
    xfer2 = from_yaml((EX / "transfer_funds.yaml").read_text())

    # ---- get_account_balance ----
    bal_surface = AsyncFakeSurface()
    bal_url = "/activity.htm?id=13344"
    bal_surface.set_page(bal_url, "Account Details\nBalance: $1,200.00")
    bal_extract = next(s for s in bal2.steps if s.action == "extract")
    bal_surface.register(bal_url, bal_extract.target.primary, 1)
    bal_surface.set_value(1, "$1,200.00")

    bal_result = await run_capability_async(bal2, bal_surface, {"account_id": "13344"}, resolve_secret, run_id="async-evidence-1")
    assert bal_result.status == "SUCCESS", bal_result
    assert bal_result.outputs == {"balance": "$1,200.00"}
    check_result(bal2, bal_result)
    print("async integration (get_account_balance):", bal_result.status, bal_result.outputs)

    # same artifact, bad account id -> the business outcome declared in its own outcome_rules
    bad_surface = AsyncFakeSurface()
    bad_url = "/activity.htm?id=00000"
    bad_surface.set_page(bad_url, "Could not find account 00000")
    bad_result = await run_capability_async(bal2, bad_surface, {"account_id": "00000"}, resolve_secret, run_id="async-evidence-1b")
    assert bad_result.status == "BUSINESS_OUTCOME" and bad_result.outcome == "ACCOUNT_NOT_FOUND", bad_result
    check_result(bal2, bad_result)
    print("async integration (get_account_balance, bad id):", bad_result.status, bad_result.outcome)

    # ---- transfer_funds ----
    xfer_surface = AsyncFakeSurface()
    xurl = "/transfer.htm"
    xfer_surface.set_page(xurl, "Transfer Funds\nAmount: From account #: To account #:")
    xfer_type, xfer_sel1, xfer_sel2, xfer_click, xfer_extract = (s for s in xfer2.steps if s.action != "navigate")
    xfer_surface.register(xurl, xfer_type.target.primary, 10)
    xfer_surface.register(xurl, xfer_type.target.fallback, 10)
    xfer_surface.register(xurl, xfer_sel1.target.primary, 11)
    xfer_surface.register(xurl, xfer_sel2.target.primary, 12)
    xfer_surface.register(xurl, xfer_click.target.primary, 13)
    xfer_surface.register(xurl, xfer_extract.target.primary, 14)
    xfer_surface.set_value(14, "Transfer Complete!")
    xfer_surface.click_effects[13] = lambda s: s.set_page(xurl, "Transfer Complete! $20.00 has moved.")

    xfer_inputs = {"from_account": "13344", "to_account": "13355", "amount": "20.00"}
    xfer_result = await run_capability_async(xfer2, xfer_surface, xfer_inputs, resolve_secret, run_id="async-evidence-2", auto_approve_limit=500.0)
    assert xfer_result.status == "SUCCESS", xfer_result
    assert xfer_result.outputs == {"confirmation": "Transfer Complete!"}
    assert xfer_surface.typed[10] == "20.00" and xfer_surface.selected[11] == "13344" and xfer_surface.selected[12] == "13355"
    assert xfer_surface.clicked == [13]
    check_result(xfer2, xfer_result)
    print("async integration (transfer_funds, under limit):", xfer_result.status, xfer_result.outputs)

    # same artifact, amount at/above the limit -> NEEDS_APPROVAL, the Transfer button never clicked
    xfer_surface2 = AsyncFakeSurface()
    xfer_surface2.set_page(xurl, "Transfer Funds\nAmount: From account #: To account #:")
    xfer_surface2.register(xurl, xfer_type.target.primary, 10)
    xfer_surface2.register(xurl, xfer_sel1.target.primary, 11)
    xfer_surface2.register(xurl, xfer_sel2.target.primary, 12)
    xfer_surface2.register(xurl, xfer_click.target.primary, 13)
    approvals: list = []

    async def _fake_escalate2(reason, ctx):
        approvals.append((reason, ctx))

    xfer_result2 = await run_capability_async(
        xfer2, xfer_surface2, {"from_account": "13344", "to_account": "13355", "amount": "999.00"},
        resolve_secret, run_id="async-evidence-3", auto_approve_limit=500.0,
        escalate=_fake_escalate2,
    )
    assert xfer_result2.status == "NEEDS_APPROVAL" and xfer_result2.pending_step == 4, xfer_result2
    assert 13 not in xfer_surface2.clicked
    assert len(approvals) == 1
    print("async integration (transfer_funds, over limit):", xfer_result2.status, xfer_result2.reason)

    # D82 fix: over-limit click, escalate returns "approve" -> the engine clicks the target
    # itself, continues to the remaining steps (extract, checkpoint), reaches SUCCESS with the
    # real confirmation. Same fixture as the two tests just above.
    xfer_surface3 = AsyncFakeSurface()
    xfer_surface3.set_page(xurl, "Transfer Funds\nAmount: From account #: To account #:")
    xfer_surface3.register(xurl, xfer_type.target.primary, 10)
    xfer_surface3.register(xurl, xfer_sel1.target.primary, 11)
    xfer_surface3.register(xurl, xfer_sel2.target.primary, 12)
    xfer_surface3.register(xurl, xfer_click.target.primary, 13)
    xfer_surface3.register(xurl, xfer_extract.target.primary, 14)
    xfer_surface3.set_value(14, "Transfer Complete!")
    xfer_surface3.click_effects[13] = lambda s: s.set_page(xurl, "Transfer Complete! $999.00 has moved.")
    approve_calls: list = []

    async def _fake_escalate3(reason, ctx):
        approve_calls.append((reason, ctx))
        return "approve"

    xfer_result3 = await run_capability_async(
        xfer2, xfer_surface3, {"from_account": "13344", "to_account": "13355", "amount": "999.00"},
        resolve_secret, run_id="async-evidence-4", auto_approve_limit=500.0,
        escalate=_fake_escalate3,
    )
    assert xfer_result3.status == "SUCCESS", xfer_result3
    assert xfer_result3.outputs == {"confirmation": "Transfer Complete!"}
    assert xfer_surface3.clicked == [13]
    assert len(approve_calls) == 1
    check_result(xfer2, xfer_result3)
    print("async integration (transfer_funds, escalate approves over-limit click):", xfer_result3.status, xfer_result3.outputs)

    # D82: escalate approves, but the target cannot be resolved at that point -> FAILED, not a
    # silent success and not NEEDS_APPROVAL. The Transfer button is deliberately never registered.
    xfer_surface4 = AsyncFakeSurface()
    xfer_surface4.set_page(xurl, "Transfer Funds\nAmount: From account #: To account #:")
    xfer_surface4.register(xurl, xfer_type.target.primary, 10)
    xfer_surface4.register(xurl, xfer_sel1.target.primary, 11)
    xfer_surface4.register(xurl, xfer_sel2.target.primary, 12)

    async def _fake_escalate4(reason, ctx):
        return "approve"

    xfer_result4 = await run_capability_async(
        xfer2, xfer_surface4, {"from_account": "13344", "to_account": "13355", "amount": "999.00"},
        resolve_secret, run_id="async-evidence-5", auto_approve_limit=500.0,
        escalate=_fake_escalate4,
    )
    assert xfer_result4.status == "FAILED" and xfer_result4.failure.step_action == "click", xfer_result4
    assert 13 not in xfer_surface4.clicked
    print("async integration (transfer_funds, escalate approves but target unresolvable):",
          xfer_result4.status, xfer_result4.failure.observed)

    # D82: escalate returns a plain non-"approve" string ("reject") -> unchanged NEEDS_APPROVAL,
    # click never called -- same contract the None-returning fake above already proved, with a
    # different non-"approve" value.
    xfer_surface5 = AsyncFakeSurface()
    xfer_surface5.set_page(xurl, "Transfer Funds\nAmount: From account #: To account #:")
    xfer_surface5.register(xurl, xfer_type.target.primary, 10)
    xfer_surface5.register(xurl, xfer_sel1.target.primary, 11)
    xfer_surface5.register(xurl, xfer_sel2.target.primary, 12)
    xfer_surface5.register(xurl, xfer_click.target.primary, 13)

    async def _fake_escalate5(reason, ctx):
        return "reject"

    xfer_result5 = await run_capability_async(
        xfer2, xfer_surface5, {"from_account": "13344", "to_account": "13355", "amount": "999.00"},
        resolve_secret, run_id="async-evidence-6", auto_approve_limit=500.0,
        escalate=_fake_escalate5,
    )
    assert xfer_result5.status == "NEEDS_APPROVAL" and xfer_result5.pending_step == 4, xfer_result5
    assert 13 not in xfer_surface5.clicked
    print("async integration (transfer_funds, escalate returns non-approve string):", xfer_result5.status, xfer_result5.reason)


asyncio.run(_run_async_integration())
print("\nASYNC INTEGRATION CHECKS PASSED")
