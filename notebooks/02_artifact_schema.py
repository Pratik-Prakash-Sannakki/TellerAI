# %% [markdown]
# # Phase 2 (v2): the capability artifact, simplified
# Pure Python. No browser, no network, no API key. Run cells top to bottom.
#
# Rebuilt with the simplification agreed after the original Phase 2 (see DECISIONS.md section O,
# D63-D66): locators are now exactly one `primary` + one optional `fallback` (not a ranked list
# of ~3), multi-tenant fields (`app.id`, `app.vendor`, `base`, `overrides`) are cut in favor of a
# single `base_url`, `routes` is derived from `navigate` steps instead of stored, and
# `when_to_use` is folded into `description`. `ReplayResult` (D27) is unchanged.
#
# Builds: locators and steps, then Capability (with cross-checks), YAML load/save,
# the calling agent's tool contract, and the replay result contract.

# %% Section 1: locators, conditions, steps, error rules
import re
from typing import Annotated, Any, Literal, Union

from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator, model_validator


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


# %% Section 1b: checks for locators, conditions, steps, rules
def raises(fn, expect: str):
    """Run fn and require a validation error whose message contains `expect`."""
    try:
        fn()
    except (ValidationError, ValueError) as err:
        assert expect in str(err), f"expected {expect!r} in:\n{err}"
        return
    raise AssertionError("was NOT rejected")


# a good target (primary + fallback, D63) passes
Target(
    primary=RoleLocator(role="button", name="Log In", note="Accessible role+name; the most stable signal we have."),
    fallback=TextLocator(text="Log In", note="Visible text as a backup if the accessible name ever changes."),
)

raises(lambda: Target(
    primary=TextLocator(text="x", stability="low", note="n"),
    fallback=LabelLocator(label="x", stability="high", note="n"),
), "ordered from most to least stable")
raises(lambda: StructureLocator(tag="td", nth=18, note="n"), "within")            # a page-wide index has no container
raises(lambda: RoleLocator(role="button", name="Log In"), "note")                  # note is required (D63)
raises(lambda: Target(
    primary=RoleLocator(role="button", name="Log In", note="n"),
    fallback=TextLocator(text="Log In", note="n"),
    third={"strategy": "text", "text": "x", "note": "n"},
), "Extra inputs are not permitted")                                                # a 3rd locator has no slot (D63)
raises(lambda: Condition(), "needs url_contains or text_present")
raises(lambda: Checkpoint(url_contains="activity.htm"), "needs both")
raises(lambda: OutcomeRule(when=Condition(text_present="x"), kind="business", message="m"), "UPPER_SNAKE")
raises(lambda: OutcomeRule(when=Condition(text_present="x"), kind="hard", action="retry", message="m"), "hard rules carry only a message")
raises(lambda: Click(target=Target(primary=LabeledValueLocator(label="Balance:", note="n"))), "only allowed in extract steps")
raises(lambda: Navigate(path="overview.htm"), "String should match pattern")     # must start with '/'
assert template_refs("id={{account_id}} pw={{secret:password}}") == [(False, "account_id"), (True, "password")]
assert malformed_template("{{Account}}") and not malformed_template("{{account_id}}")
print("models: all checks passed")

# %% Section 2: Capability and cross-field checks
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


# %% Section 2a: YAML load and save
import yaml


def to_yaml(cap: Capability) -> str:
    """Stable, human-readable YAML. Keys keep the model's field order."""
    return yaml.safe_dump(cap.model_dump(mode="json", exclude_none=True), sort_keys=False, allow_unicode=True, width=100)


def from_yaml(text: str) -> Capability:
    return Capability.model_validate(yaml.safe_load(text))


# %% Section 2b: checks for Capability and YAML
import copy, pathlib

# 1. both examples load and validate
ROOT = pathlib.Path.cwd()
if not (ROOT / "artifacts").exists():        # a notebook kernel usually starts inside notebooks/
    ROOT = ROOT.parent
EX = ROOT / "artifacts" / "examples"
bal = from_yaml((EX / "get_account_balance.yaml").read_text())
xfer = from_yaml((EX / "transfer_funds.yaml").read_text())
assert bal.name == "get_account_balance" and xfer.risk_level == "risky"
print("examples load: ok")

# D65: routes are derived from navigate steps, not stored
assert derived_routes(bal) == ["/activity.htm"]
assert derived_routes(xfer) == ["/transfer.htm"]
print("derived routes: ok")

# D64: base_url is minimal and still shape-checked
raises(lambda: Capability.model_validate({**yaml.safe_load((EX / "get_account_balance.yaml").read_text()), "base_url": "not-a-url"}),
       "String should match pattern")
print("base_url check: ok")


# 2. each kind of mistake is rejected, with a message that says what is wrong
def rejects(name: str, mutate, expect: str, source: str = "bal"):
    data = copy.deepcopy(yaml.safe_load((EX / ("get_account_balance.yaml" if source == "bal" else "transfer_funds.yaml")).read_text()))
    mutate(data)
    try:
        Capability.model_validate(data)
    except ValidationError as err:
        assert expect in str(err), f"{name}: expected {expect!r} in:\n{err}"
        print(f"rejected ok: {name}")
        return
    raise AssertionError(f"{name}: was NOT rejected")

rejects("typo in a key", lambda d: d.update(descripton="x"), "Extra inputs are not permitted")
rejects("unknown input reference", lambda d: d["steps"][0].update(path="/activity.htm?id={{acount_id}}"), "unknown input 'acount_id'")
rejects("malformed template", lambda d: d["steps"][0].update(path="/activity.htm?id={{Account}}"), "malformed template")
rejects("output never extracted", lambda d: d["steps"].pop(1), "must be produced by exactly one extract step")
rejects("extract into undeclared output", lambda d: d["steps"][1].update(save_as="total"), "is not a declared output")
rejects("duplicate input", lambda d: d["inputs"].append(copy.deepcopy(d["inputs"][0])), "duplicate input name")
rejects("checkpoint missing text", lambda d: d["checkpoint"].pop("text_present"), "a checkpoint needs both")
rejects("business rule without outcome", lambda d: d["outcome_rules"][0].pop("outcome"), "business rules need an UPPER_SNAKE outcome")
rejects("recoverable rule without action", lambda d: d["outcome_rules"][1].pop("action"), "recoverable rules need an action")
rejects("hard rule with an action", lambda d: d["outcome_rules"][2].update(action="retry"), "hard rules carry only a message")
rejects("bad input regex", lambda d: d["inputs"][0].update(pattern="["), "pattern is not a valid regex")
rejects("secret used as a plain input", lambda d: d["steps"][0].update(path="/activity.htm?id={{secret:password}}"), "only allowed as a typed value")

# steps and locators
def bad_click(d):
    d["steps"].insert(1, {"action": "click", "target": {"primary": {"strategy": "labeled_value", "label": "Balance:", "note": "n"}}})
rejects("labeled_value in a click", bad_click, "only allowed in extract steps")

def bad_order(d):
    d["steps"][1]["target"] = {
        "primary": {"strategy": "text", "text": "Balance:", "stability": "low", "note": "n"},
        "fallback": {"strategy": "label", "label": "Balance:", "stability": "high", "note": "n"},
    }
rejects("locators out of order", bad_order, "ordered from most to least stable")

def page_wide_index(d):
    d["steps"][1]["target"] = {"primary": {"strategy": "structure", "tag": "td", "nth": 18, "note": "n"}}
rejects("page-wide index (no container)", page_wide_index, "within")

def missing_note(d):
    d["steps"][1]["target"] = {"primary": {"strategy": "text", "text": "Balance:"}}
rejects("locator missing note", missing_note, "note")

# risk
rejects("risky step but risk_level safe", lambda d: d.update(risk_level="safe"), "risky but risk_level is 'safe'", "xfer")
rejects("safe capability marked risky", lambda d: d.update(risk_level="risky"), "no step is marked risky")
def bad_amount(d): d["steps"][4]["amount_input"] = "cash"
rejects("amount_input not declared", bad_amount, "is not a declared input", "xfer")


# YAML round trip is lossless
for cap in (bal, xfer):
    assert from_yaml(to_yaml(cap)) == cap
print("yaml round trip: ok")
print("capability: all checks passed")

# %% Section 3: tool contract for a calling agent
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


# %% Section 3b: checks for the tool contract
# what a calling agent sees
import json

contract = tool_contract(xfer)
assert contract["input_schema"]["required"] == ["from_account", "to_account", "amount"]
assert contract["returns"]["may_need_approval"] is True
assert tool_contract(bal)["returns"]["business_outcomes"] == ["ACCOUNT_NOT_FOUND"]
assert contract["description"] == xfer.description and "when_to_use" not in contract   # D66: one field, not two
print(json.dumps(tool_contract(bal), indent=2))

print("io: all checks passed")
