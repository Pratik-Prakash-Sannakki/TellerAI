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
