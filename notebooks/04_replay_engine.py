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
