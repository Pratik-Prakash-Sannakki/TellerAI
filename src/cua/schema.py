"""The capability artifact schema (Pydantic models), YAML round-trip, the calling-agent tool
contract, and the replay result contract.

Ported from ``notebooks/02_artifact_schema.py``'s non-check cells (Sections 1, 2, 2a, 3, 4). This
is a straight port: every model, validator, and helper function below is unchanged from the
notebook -- only the module-level `# %%` cell structure and the inline offline assertions are
gone (the assertions now live in ``tests/test_schema.py``, calling into these exact classes).

See DECISIONS.md sections O (D63-D66, the v2 simplification: one `primary` + one optional
`fallback` locator, `base_url` replacing `app`/`base`/`overrides`, derived `routes`, `description`
absorbing `when_to_use`) and D27/D39 (the replay result contract) for the design reasoning.
Pure Python: no browser, no network, no API key.
"""

from __future__ import annotations

import re
from typing import Annotated, Literal, Union

import yaml
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

__all__ = [
    "Strict",
    "ValueType",
    "Risk",
    "Stability",
    "Name",
    "template_refs",
    "malformed_template",
    "Within",
    "RoleLocator",
    "LabelLocator",
    "TextLocator",
    "StructureLocator",
    "LabeledValueLocator",
    "Locator",
    "Target",
    "locator_strings",
    "Condition",
    "Checkpoint",
    "StepBase",
    "Navigate",
    "Click",
    "TypeText",
    "Select",
    "Extract",
    "Step",
    "Dismiss",
    "OutcomeRule",
    "InputParam",
    "OutputParam",
    "Capability",
    "derived_routes",
    "to_yaml",
    "from_yaml",
    "tool_contract",
    "Failure",
    "ReplayResult",
    "check_result",
]


class Strict(BaseModel):
    """Base for every model. Unknown keys are errors, so a typo in a YAML file cannot pass silently."""
    model_config = ConfigDict(extra="forbid")


ValueType = Literal["string", "integer", "number", "currency", "boolean"]
Risk = Literal["safe", "risky"]
Stability = Literal["high", "medium", "low"]
Name = Annotated[str, Field(pattern=r"^[a-z][a-z0-9_]*$")]      # inputs, outputs, secrets, capability names
_RANK = {"high": 0, "medium": 1, "low": 2}

# {{account_id}} is an input reference. {{secret:password}} is a secret reference (a NAME, never a value).
_TEMPLATE = re.compile(r"\{\{\s*(secret:)?([a-z][a-z0-9_]*)\s*\}\}")


def template_refs(text: str) -> list[tuple[bool, str]]:
    """Return (is_secret, name) for every {{...}} reference in text."""
    return [(bool(m.group(1)), m.group(2)) for m in _TEMPLATE.finditer(text)]


def malformed_template(text: str) -> bool:
    """True if text contains a '{{' that is not a valid reference, e.g. {{Account}}."""
    return text.count("{{") != len(template_refs(text))


# ---------- locators (D8, simplified by D63): one primary + at most one fallback, ranked ----------
class Within(Strict):
    """Scope a locator to a container, e.g. the login form."""
    role: str
    name: str | None = None


class RoleLocator(Strict):
    strategy: Literal["role"] = "role"
    role: str
    name: str
    within: Within | None = None
    stability: Stability = "high"
    note: str = Field(min_length=1)       # required: why we trust it (D63)


class LabelLocator(Strict):
    strategy: Literal["label"] = "label"
    label: str
    stability: Stability = "medium"
    note: str = Field(min_length=1)


class TextLocator(Strict):
    strategy: Literal["text"] = "text"
    text: str
    within: Within | None = None
    stability: Stability = "medium"
    note: str = Field(min_length=1)


class StructureLocator(Strict):
    """'The nth <tag> inside a container'. `within` is required: a page-wide index breaks when anything is added."""
    strategy: Literal["structure"] = "structure"
    tag: str
    within: Within
    nth: int = Field(ge=1)
    stability: Stability = "low"
    note: str = Field(min_length=1)


class LabeledValueLocator(Strict):
    """The value shown next to a label, e.g. the cell after 'Balance:'. Only valid in extract steps."""
    strategy: Literal["labeled_value"] = "labeled_value"
    label: str
    stability: Stability = "medium"
    note: str = Field(min_length=1)


Locator = Annotated[
    Union[RoleLocator, LabelLocator, TextLocator, StructureLocator, LabeledValueLocator],
    Field(discriminator="strategy"),
]


class Target(Strict):
    """Exactly one primary locator, one optional fallback (D63). A third locator is not
    representable by this type at all -- there is no list to extend, only two named slots."""
    primary: Locator
    fallback: Locator | None = None

    @model_validator(mode="after")
    def _ranked(self):
        if self.fallback is not None and _RANK[self.fallback.stability] < _RANK[self.primary.stability]:
            raise ValueError("locators must be ordered from most to least stable (primary, then fallback)")
        return self

    def locators(self) -> list:
        """All locators in try-order: primary, then fallback if present."""
        return [self.primary] + ([self.fallback] if self.fallback else [])


def locator_strings(loc) -> list[str]:
    """Every text field of a locator that may contain a {{template}}."""
    return [getattr(loc, f) for f in ("name", "label", "text") if getattr(loc, f, None)]


def _no_labeled_value(target: Target) -> Target:
    if any(loc.strategy == "labeled_value" for loc in target.locators()):
        raise ValueError("labeled_value locators are only allowed in extract steps")
    return target


# ---------- conditions (D9) ----------
class Condition(Strict):
    url_contains: str | None = None
    text_present: str | None = None

    @model_validator(mode="after")
    def _one(self):
        if not (self.url_contains or self.text_present):
            raise ValueError("a condition needs url_contains or text_present")
        return self


class Checkpoint(Condition):
    """The final success check. Both signals must agree (D9)."""

    @model_validator(mode="after")
    def _both(self):
        if not (self.url_contains and self.text_present):
            raise ValueError("a checkpoint needs both url_contains and text_present")
        return self


# ---------- steps ----------
class StepBase(Strict):
    why: str | None = None                # short note for the human reviewer
    expect: Condition | None = None       # optional check right after this step


class Navigate(StepBase):
    action: Literal["navigate"] = "navigate"
    path: str = Field(pattern=r"^/")      # relative to base_url


class Click(StepBase):
    action: Literal["click"] = "click"
    target: Target
    risk: Risk = "safe"                   # risky = changes data; replay asks a human unless policy allows (D20, D33)
    amount_input: Name | None = None      # for risky steps: the input holding the money amount

    _v = field_validator("target")(_no_labeled_value)


class TypeText(StepBase):
    action: Literal["type"] = "type"
    target: Target
    value: str                            # may hold {{input}} or {{secret:name}}

    _v = field_validator("target")(_no_labeled_value)


class Select(StepBase):
    action: Literal["select"] = "select"
    target: Target
    option: str                           # visible text of the option; may hold {{input}}

    _v = field_validator("target")(_no_labeled_value)


class Extract(StepBase):
    action: Literal["extract"] = "extract"
    target: Target
    save_as: Name                         # must be a declared output


Step = Annotated[Union[Navigate, Click, TypeText, Select, Extract], Field(discriminator="action")]


# ---------- error handling rules (D10) ----------
class Dismiss(Strict):
    target: Target


class OutcomeRule(Strict):
    """When `when` matches after a step, treat the page as a business outcome, a recoverable condition, or a hard failure."""
    when: Condition
    kind: Literal["business", "recoverable", "hard"]
    outcome: str | None = Field(default=None, pattern=r"^[A-Z][A-Z0-9_]*$")
    action: Literal["dismiss", "retry", "wait", "relogin"] | None = None
    dismiss: Target | None = None
    message: str

    @model_validator(mode="after")
    def _shape(self):
        if self.kind == "business":
            if not self.outcome:
                raise ValueError("business rules need an UPPER_SNAKE outcome")
            if self.action or self.dismiss:
                raise ValueError("business rules take no action")
        elif self.kind == "recoverable":
            if self.outcome:
                raise ValueError("only business rules carry an outcome")
            if not self.action:
                raise ValueError("recoverable rules need an action")
            if self.action == "dismiss" and not self.dismiss:
                raise ValueError("action 'dismiss' needs a dismiss target")
            if self.action != "dismiss" and self.dismiss:
                raise ValueError("a dismiss target is only for action 'dismiss'")
        else:
            if self.outcome or self.action or self.dismiss:
                raise ValueError("hard rules carry only a message")
        return self


# ---------- Capability ----------
class InputParam(Strict):
    name: Name
    type: ValueType
    description: str
    required: bool = True
    pattern: str | None = None            # regex the caller's value must match

    @field_validator("pattern")
    @classmethod
    def _compiles(cls, v):
        if v is not None:
            try:
                re.compile(v)
            except re.error as exc:                 # re.error is not a ValueError, so wrap it
                raise ValueError(f"pattern is not a valid regex: {exc}") from exc
        return v


class OutputParam(Strict):
    name: Name
    type: ValueType
    description: str


class Capability(Strict):
    schema_version: Literal[1] = 1
    name: Name
    version: int = Field(ge=1)
    status: Literal["draft", "verified"] = "draft"     # verified = proven by a no-LLM replay (D23)
    description: str                      # also covers "when to use" (D66); one field, not two
    base_url: str = Field(pattern=r"^https?://")        # D64: all that is left of app/base/overrides
    risk_level: Risk
    inputs: list[InputParam] = []
    outputs: list[OutputParam] = []
    secrets: list[Name] = []              # names only. Values live in .env (D32).
    steps: list[Step] = Field(min_length=1)
    checkpoint: Checkpoint
    outcome_rules: list[OutcomeRule] = []

    @model_validator(mode="after")
    def _consistent(self):
        problems: list[str] = []
        in_names = [i.name for i in self.inputs]
        out_names = [o.name for o in self.outputs]
        for label, names in (("input", in_names), ("output", out_names), ("secret", self.secrets)):
            for n in {n for n in names if names.count(n) > 1}:
                problems.append(f"duplicate {label} name {n!r}")

        def check(text: str, where: str, allow_secret: bool = False):
            if malformed_template(text):
                problems.append(f"{where}: malformed template in {text!r}")
            for is_secret, name in template_refs(text):
                if is_secret and not allow_secret:
                    problems.append(f"{where}: secret {name!r} is only allowed as a typed value")
                elif is_secret and name not in self.secrets:
                    problems.append(f"{where}: unknown secret {name!r}")
                elif not is_secret and name not in in_names:
                    problems.append(f"{where}: unknown input {name!r}")

        extracted: list[str] = []
        for i, s in enumerate(self.steps):
            where = f"steps[{i}] ({s.action})"
            if s.action == "navigate":
                check(s.path, where)
            elif s.action == "type":
                check(s.value, where, allow_secret=True)
            elif s.action == "select":
                check(s.option, where)
            elif s.action == "extract":
                extracted.append(s.save_as)
                if s.save_as not in out_names:
                    problems.append(f"{where}: save_as {s.save_as!r} is not a declared output")
            elif s.action == "click":
                if s.amount_input and s.risk != "risky":
                    problems.append(f"{where}: amount_input only belongs on risky clicks")
                if s.amount_input and s.amount_input not in in_names:
                    problems.append(f"{where}: amount_input {s.amount_input!r} is not a declared input")
            if s.action != "navigate":
                for loc in s.target.locators():
                    for text in locator_strings(loc):
                        check(text, f"{where} locator")
        for n in out_names:
            if extracted.count(n) != 1:
                problems.append(f"output {n!r} must be produced by exactly one extract step (found {extracted.count(n)})")

        has_risky = any(s.action == "click" and s.risk == "risky" for s in self.steps)
        if has_risky and self.risk_level != "risky":
            problems.append("a step is risky but risk_level is 'safe'")
        if not has_risky and self.risk_level == "risky":
            problems.append("risk_level is 'risky' but no step is marked risky")
        if problems:
            raise ValueError("; ".join(problems))
        return self


def derived_routes(cap: Capability) -> list[str]:
    """The pages this capability may touch, derived from its own navigate steps (D65) instead of
    a separately-maintained list. Order of first appearance, no duplicates, query string dropped."""
    routes: list[str] = []
    for s in cap.steps:
        if s.action == "navigate":
            route = s.path.split("?")[0]
            if route not in routes:
                routes.append(route)
    return routes


# ---------- YAML load and save ----------
def to_yaml(cap: Capability) -> str:
    """Stable, human-readable YAML. Keys keep the model's field order."""
    return yaml.safe_dump(cap.model_dump(mode="json", exclude_none=True), sort_keys=False, allow_unicode=True, width=100)


def from_yaml(text: str) -> Capability:
    return Capability.model_validate(yaml.safe_load(text))


# ---------- tool contract for a calling agent ----------
_JSON_TYPE = {"string": "string", "integer": "integer", "number": "number", "currency": "string", "boolean": "boolean"}


def tool_contract(cap: Capability) -> dict:
    """What a calling agent sees: what this capability does, what it needs, what it returns."""
    props, required = {}, []
    for i in cap.inputs:
        p = {"type": _JSON_TYPE[i.type], "description": i.description}
        if i.pattern:
            p["pattern"] = i.pattern
        props[i.name] = p
        if i.required:
            required.append(i.name)
    return {
        "name": cap.name,
        "description": cap.description,       # D66: when_to_use folded in, nothing to append
        "input_schema": {"type": "object", "properties": props, "required": required, "additionalProperties": False},
        "returns": {
            "outputs": {o.name: {"type": _JSON_TYPE[o.type], "description": o.description} for o in cap.outputs},
            "business_outcomes": sorted({r.outcome for r in cap.outcome_rules if r.kind == "business"}),
            "may_need_approval": cap.risk_level == "risky",
        },
    }


# ---------- replay result contract (D27) ----------
class Failure(Strict):
    step_index: int = Field(ge=0)
    step_action: str
    expected: str
    observed: str
    evidence: str | None = None           # path to the screenshot / page snapshot


class ReplayResult(Strict):
    """What replay returns to the caller (D27). Unchanged by the schema simplification."""
    run_id: str
    capability: Name
    capability_version: int = Field(ge=1)
    status: Literal["SUCCESS", "BUSINESS_OUTCOME", "NEEDS_APPROVAL", "FAILED"]
    outputs: dict[str, str] = {}
    outcome: str | None = None            # BUSINESS_OUTCOME: e.g. ACCOUNT_NOT_FOUND
    pending_step: int | None = None       # NEEDS_APPROVAL: the step waiting for a human
    reason: str | None = None             # NEEDS_APPROVAL: why
    failure: Failure | None = None        # FAILED: step, expected, observed

    @model_validator(mode="after")
    def _shape(self):
        s = self.status
        if s == "SUCCESS" and (self.outcome or self.failure or self.reason):
            raise ValueError("SUCCESS carries only outputs")
        if s == "BUSINESS_OUTCOME" and (not self.outcome or self.failure):
            raise ValueError("BUSINESS_OUTCOME needs an outcome and no failure")
        if s == "NEEDS_APPROVAL" and (self.pending_step is None or not self.reason or self.failure):
            raise ValueError("NEEDS_APPROVAL needs pending_step and reason, and no failure")
        if s == "FAILED" and (not self.failure or self.outcome):
            raise ValueError("FAILED needs a failure and no outcome")
        return self


def check_result(cap: Capability, result: ReplayResult) -> None:
    """Check a result against the capability that produced it. Raises ValueError on a mismatch."""
    if result.capability != cap.name or result.capability_version != cap.version:
        raise ValueError("result is for a different capability or version")
    declared = {o.name for o in cap.outputs}
    if result.status == "SUCCESS" and set(result.outputs) != declared:
        raise ValueError(f"SUCCESS outputs {sorted(result.outputs)} != declared outputs {sorted(declared)}")
    if result.status == "BUSINESS_OUTCOME":
        allowed = {r.outcome for r in cap.outcome_rules if r.kind == "business"}
        if result.outcome not in allowed:
            raise ValueError(f"outcome {result.outcome!r} is not declared. Declared: {sorted(allowed)}")
