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
def resolve_target(surface: ReplaySurface, target: "Target", *, logger: Callable[[str], None] = lambda m: None):
    """Try the primary locator, then the fallback if there is one and the primary did not
    resolve. Raises ResolutionError, naming what was expected, if neither resolves."""
    ref = surface.resolve(target.primary)
    if ref is not None:
        logger(f"resolved via primary ({target.primary.strategy})")
        return ref
    if target.fallback is not None:
        ref = surface.resolve(target.fallback)
        if ref is not None:
            logger(f"primary failed, resolved via fallback ({target.fallback.strategy})")
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


def _check_outcomes(cap, step_index, url, text, escalate, base, logger):
    """First matching rule wins, in declared order (D10's documented order rule)."""
    for rule in cap.outcome_rules:
        if not condition_matches(rule.when, url, text):
            continue
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
    exercised in tests by a fake."""
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
                            if escalate is not None:
                                escalate(reason, {"capability": cap.name, "step_index": i, "amount": amount, "limit": auto_approve_limit})
                            return ReplayResult(**base(status="NEEDS_APPROVAL", pending_step=i, reason=reason))
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
