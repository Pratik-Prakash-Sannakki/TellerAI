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
