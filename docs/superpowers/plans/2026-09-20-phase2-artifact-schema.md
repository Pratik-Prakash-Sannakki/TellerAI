# Phase 2: Artifact Schema Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.
>
> **Working style set by the user:** one phase at a time, notebook first, production code only in Phase 9. Stop after each task and wait.
>
> **One exception to the CLAUDE.md rule "sub-agent never runs the notebook":** this notebook is pure Python (no browser, no network, no API key). The sub-agent runs it as a script, `uv run python notebooks/02_artifact_schema.py`, to prove each task passes. The user then re-runs it in the notebook.

**Goal:** Define the capability artifact as strict, typed Pydantic models with a YAML format, plus the result contract that replay returns. No browser, no LLM.

**Architecture:** One notebook, `notebooks/02_artifact_schema.py`, builds the models in layers: locators and steps, then the `Capability` with cross-field checks, then YAML load/save, then the calling agent's tool contract, then `ReplayResult`. Two hand-written example artifacts (`get_account_balance`, `transfer_funds`) prove the schema fits both a safe read flow and a risky money flow.

**Tech Stack:** Python 3.12, Pydantic v2, PyYAML, jupytext (already installed), uv.

**Spec:** `DECISIONS.md` (D7 YAML, D8 ranked locators, D9 checkpoint, D10 error rules, D12 extract, D21 base/overrides, D27 result contract, D29 typed inputs, D32 secret references, D33 risky steps) and `notebooks/FINDINGS.md` "Carry forward" (phase 2 row). Assignment section 3.2: steps, how each element is identified, typed inputs, typed outputs, checkpoint, versioned and reviewable. "Focal point of the evaluation."

**Verified:** every code block in this plan was run together in a scratch environment on 2026-09-20 (Python 3.12, Pydantic 2.13.5, PyYAML 6.0.3): 25 rejection checks and all positive checks passed.

## Global Constraints

- Python >= 3.12. Pydantic v2 models. PyYAML `safe_load` / `safe_dump` only.
- **Unknown keys are errors** (`extra="forbid"` on every model). A typo in a YAML file must never pass silently.
- **Secrets are names, never values** (`{{secret:password}}`). Values live in `.env` (D32).
- Locators are **ranked** most to least stable. A **page-wide index is forbidden**: a structure locator must sit inside a container (D8).
- The checkpoint needs **both** a URL signal and a content signal (D9).
- Business outcomes, recoverable conditions, and hard failures are three distinct rule kinds (D10).
- No browser, no network, no API key in this phase. Do not import Playwright or deepagents.
- Never commit `.env`. Notebook outputs are stripped by `nbstripout` on commit.

---

## Schema at a glance

| Piece | What it says | Why (decision) |
|---|---|---|
| `Capability` | name, version, status (`draft`/`verified`), description, `when_to_use`, app, risk level, inputs, outputs, secrets, routes, steps, checkpoint, outcome rules | 3.2 contract; a calling agent can pick it by name (D7) |
| `Target` = ranked `locators` | role+name, label, text, structure (inside a container), labeled value | Survives redesign; no page-wide index (D8) |
| Steps | `navigate`, `click`, `type`, `select`, `extract` | The five things Phase 1 tools do |
| `{{input}}` / `{{secret:name}}` | Typed inputs and named secrets in step text | D29, D32. Checked: every reference must be declared |
| `Click.risk` + `amount_input` | Marks the point of no return and which input holds the money | D20, D33. The limit itself stays in config |
| `outcome_rules` | `when` page shows X, it is a `business` outcome (with a name), a `recoverable` condition (with an action), or a `hard` failure | D10 |
| `checkpoint` | URL contains and text present | D9 |
| `routes` | Pages the capability may touch | Feeds the allowlist (D15) |
| `base` / `overrides` | Specialize a shared capability per tenant | D21. Stored now, applied later |
| `status` | `draft` until a no-LLM replay proves it | D23 |
| `ReplayResult` | `SUCCESS` / `BUSINESS_OUTCOME` / `NEEDS_APPROVAL` / `FAILED`, with the fields each needs | D27 |
| `tool_contract()` | What a calling agent sees: inputs, outputs, business outcomes, may-need-approval | 3.2 "a calling agent can understand what it needs and returns" |

**Known limits (state them in the report, do not hide them):**
- `overrides` and `base` are validated for shape only. Applying them is a later phase.
- `labeled_value` ("the value next to a label") is defined here; the replay engine gives it behavior in Phase 4.
- The business-outcome text in `get_account_balance.yaml` ("Could not find account") is **illustrative**. The real wording comes from a bad-input probe in Phase 3.
- `currency` inputs and outputs are typed as strings with an optional `pattern`. Format checks happen at replay (Phase 4/5).

## File structure

```
artifacts/examples/get_account_balance.yaml    # Task 1 (hand-written example, safe read flow)
artifacts/examples/transfer_funds.yaml         # Task 1 (hand-written example, risky money flow)
notebooks/02_artifact_schema.py                # Tasks 1-5: the notebook (jupytext percent format)
notebooks/02_artifact_schema.ipynb             # Task 6: generated pair
DECISIONS.md                                   # Task 6: new section L
CLAUDE.md                                      # Task 6: phase notebook list
pyproject.toml, uv.lock                        # Task 1: dependencies
```

Notebook cells are separated by `# %%`. Each task adds cells in order; **checks always sit after the code they test**, so "run all" passes. To keep the red-then-green habit, write and run the checks cell first (it fails with `NameError`), then add the implementation cell above it.

---

### Task 1: Dependencies, example artifacts, notebook skeleton

**Files:**
- Modify: `pyproject.toml`, `uv.lock`
- Create: `artifacts/examples/get_account_balance.yaml`, `artifacts/examples/transfer_funds.yaml`, `notebooks/02_artifact_schema.py`

**Interfaces:**
- Produces: two example files that later tasks load by path.

- [ ] **Step 1: Add dependencies**

```bash
cd ~/Documents/interface-ai-cua-v2
uv add pydantic pyyaml
uv run python -c "import pydantic, yaml; print(pydantic.VERSION, yaml.__version__)"
```

Expected: prints two version numbers (Pydantic 2.x, PyYAML 6.x).

- [ ] **Step 2: Create `artifacts/examples/get_account_balance.yaml`**

```yaml
# Illustrative example, written by hand. Phase 3 will produce real artifacts from discovery runs.
schema_version: 1
name: get_account_balance
version: 1
status: draft
description: Read the current balance of one account.
when_to_use: A caller needs the balance of a specific account and can name it by account id.
app:
  id: parabank
  base_url: https://parabank.parasoft.com/parabank
  vendor: Parasoft
risk_level: safe
inputs:
  - name: account_id
    type: string
    description: The account number.
    pattern: '^[0-9]{4,10}$'
outputs:
  - name: balance
    type: currency
    description: Current balance, for example $1,200.00.
secrets: []
routes:
  - /activity.htm
steps:
  - action: navigate
    why: Open the account detail page directly by id.
    path: /activity.htm?id={{account_id}}
  - action: extract
    why: The balance is the value shown next to the "Balance:" label.
    target:
      locators:
        - strategy: labeled_value
          label: 'Balance:'
          stability: medium
          note: Label text is stable across this vendor's tenants; position is not.
    save_as: balance
checkpoint:
  url_contains: activity.htm
  text_present: Balance
outcome_rules:
  - when:
      text_present: Could not find account
    kind: business
    outcome: ACCOUNT_NOT_FOUND
    message: No account with that id. Illustrative text; confirm the real wording with a bad-input probe in discovery.
  - when:
      text_present: Customer Login
    kind: recoverable
    action: relogin
    message: The session expired. Log in again and continue.
  - when:
      text_present: An internal error has occurred
    kind: hard
    message: The application reported an internal error.
```

- [ ] **Step 3: Create `artifacts/examples/transfer_funds.yaml`**

```yaml
# Illustrative example, written by hand. Shows a risky step and a typed money input.
schema_version: 1
name: transfer_funds
version: 1
status: draft
description: Move money between two accounts of the same customer.
when_to_use: A caller wants to transfer a stated amount from one of the customer's accounts to another.
app:
  id: parabank
  base_url: https://parabank.parasoft.com/parabank
  vendor: Parasoft
risk_level: risky
inputs:
  - name: from_account
    type: string
    description: Account number to take the money from.
    pattern: '^[0-9]{4,10}$'
  - name: to_account
    type: string
    description: Account number to put the money in.
    pattern: '^[0-9]{4,10}$'
  - name: amount
    type: currency
    description: Amount to move, for example 20.00.
    pattern: '^\$?[0-9]+(\.[0-9]{2})?$'
outputs:
  - name: confirmation
    type: string
    description: The confirmation message shown after the transfer.
secrets: []
routes:
  - /transfer.htm
steps:
  - action: navigate
    path: /transfer.htm
    expect:
      text_present: Transfer Funds
  - action: type
    target:
      locators:
        - strategy: label
          label: 'Amount:'
          stability: medium
    value: '{{amount}}'
  - action: select
    target:
      locators:
        - strategy: label
          label: 'From account #:'
          stability: medium
    option: '{{from_account}}'
  - action: select
    target:
      locators:
        - strategy: label
          label: 'To account #:'
          stability: medium
    option: '{{to_account}}'
  - action: click
    why: The point of no return. Replay asks a human unless policy allows this amount.
    risk: risky
    amount_input: amount
    target:
      locators:
        - strategy: role
          role: button
          name: Transfer
          stability: high
  - action: extract
    target:
      locators:
        - strategy: text
          text: Transfer Complete!
          stability: medium
    save_as: confirmation
checkpoint:
  url_contains: transfer.htm
  text_present: Transfer Complete
outcome_rules:
  - when:
      text_present: Customer Login
    kind: recoverable
    action: relogin
    message: The session expired. Log in again and continue.
```

- [ ] **Step 4: Create the notebook skeleton `notebooks/02_artifact_schema.py`**

```python
# %% [markdown]
# # Phase 2: the capability artifact
# Pure Python. No browser, no network, no API key. Run cells top to bottom.
# Builds: locators and steps, then Capability (with cross-checks), YAML load/save,
# the calling agent's tool contract, and the replay result contract.
```

- [ ] **Step 5: Commit**

```bash
git add pyproject.toml uv.lock artifacts/examples notebooks/02_artifact_schema.py
git commit -m "feat(schema): deps, example artifacts, notebook skeleton"
```

---

### Task 2: Locators, conditions, steps, error rules

**Files:**
- Modify: `notebooks/02_artifact_schema.py` (append Sections 1 and 1b)

**Interfaces:**
- Produces: `Strict`, `Name`, `Target`, `RoleLocator`, `LabelLocator`, `TextLocator`, `StructureLocator`, `LabeledValueLocator`, `Within`, `Condition`, `Checkpoint`, `Navigate`, `Click`, `TypeText`, `Select`, `Extract`, `Step`, `OutcomeRule`, `Dismiss`, `template_refs(text) -> list[tuple[bool, str]]`, `malformed_template(text) -> bool`, `locator_strings(loc) -> list[str]`.

- [ ] **Step 1: Append the checks cell first**

```python
# %% Section 1b: checks for locators, conditions, steps, rules
def raises(fn, expect: str):
    """Run fn and require a validation error whose message contains `expect`."""
    try:
        fn()
    except (ValidationError, ValueError) as err:
        assert expect in str(err), f"expected {expect!r} in:\n{err}"
        return
    raise AssertionError("was NOT rejected")


# a good target passes
Target(locators=[RoleLocator(role="button", name="Log In"), TextLocator(text="Log In")])

raises(lambda: Target(locators=[TextLocator(text="x", stability="low"), LabelLocator(label="x", stability="high")]),
       "ordered from most to least stable")
raises(lambda: StructureLocator(tag="td", nth=18), "within")            # a page-wide index has no container
raises(lambda: Condition(), "needs url_contains or text_present")
raises(lambda: Checkpoint(url_contains="activity.htm"), "needs both")
raises(lambda: OutcomeRule(when=Condition(text_present="x"), kind="business", message="m"), "UPPER_SNAKE")
raises(lambda: OutcomeRule(when=Condition(text_present="x"), kind="hard", action="retry", message="m"), "hard rules carry only a message")
raises(lambda: Click(target=Target(locators=[LabeledValueLocator(label="Balance:")])), "only allowed in extract steps")
raises(lambda: Navigate(path="overview.htm"), "String should match pattern")     # must start with '/'
assert template_refs("id={{account_id}} pw={{secret:password}}") == [(False, "account_id"), (True, "password")]
assert malformed_template("{{Account}}") and not malformed_template("{{account_id}}")
print("models: all checks passed")
```

- [ ] **Step 2: Run it and confirm it fails**

Run: `uv run python notebooks/02_artifact_schema.py`
Expected: FAIL with `NameError: name 'Target' is not defined`.

- [ ] **Step 3: Add the implementation cell above the checks cell**

```python
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


# ---------- locators (D8): how a control is found again, ranked from most to least stable ----------
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
    note: str | None = None


class LabelLocator(Strict):
    strategy: Literal["label"] = "label"
    label: str
    stability: Stability = "medium"
    note: str | None = None


class TextLocator(Strict):
    strategy: Literal["text"] = "text"
    text: str
    within: Within | None = None
    stability: Stability = "medium"
    note: str | None = None


class StructureLocator(Strict):
    """'The nth <tag> inside a container'. `within` is required: a page-wide index breaks when anything is added."""
    strategy: Literal["structure"] = "structure"
    tag: str
    within: Within
    nth: int = Field(ge=1)
    stability: Stability = "low"
    note: str | None = None


class LabeledValueLocator(Strict):
    """The value shown next to a label, e.g. the cell after 'Balance:'. Only valid in extract steps."""
    strategy: Literal["labeled_value"] = "labeled_value"
    label: str
    stability: Stability = "medium"
    note: str | None = None


Locator = Annotated[
    Union[RoleLocator, LabelLocator, TextLocator, StructureLocator, LabeledValueLocator],
    Field(discriminator="strategy"),
]


class Target(Strict):
    locators: list[Locator] = Field(min_length=1)

    @model_validator(mode="after")
    def _ranked(self):
        ranks = [_RANK[loc.stability] for loc in self.locators]
        if ranks != sorted(ranks):
            raise ValueError("locators must be ordered from most to least stable")
        return self


def locator_strings(loc) -> list[str]:
    """Every text field of a locator that may contain a {{template}}."""
    return [getattr(loc, f) for f in ("name", "label", "text") if getattr(loc, f, None)]


def _no_labeled_value(target: Target) -> Target:
    if any(loc.strategy == "labeled_value" for loc in target.locators):
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
    path: str = Field(pattern=r"^/")      # relative to app.base_url


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
```

- [ ] **Step 4: Run and confirm it passes**

Run: `uv run python notebooks/02_artifact_schema.py`
Expected: `models: all checks passed`

- [ ] **Step 5: Commit**

```bash
git add notebooks/02_artifact_schema.py
git commit -m "feat(schema): locators, conditions, steps, error rules"
```

---

### Task 3: Capability, cross-checks, YAML load and save

**Files:**
- Modify: `notebooks/02_artifact_schema.py` (append Sections 2 and 2b)

**Interfaces:**
- Consumes: everything from Task 2.
- Produces: `Capability`, `App`, `BaseRef`, `Override`, `InputParam`, `OutputParam`, `to_yaml(cap: Capability) -> str`, `from_yaml(text: str) -> Capability`.

The `Capability` validator collects **every** problem and reports them together, so a reviewer fixes a file in one pass.

- [ ] **Step 1: Append the checks cell first**

```python
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

# 3. each kind of mistake is rejected, with a message that says what is wrong
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
rejects("navigate outside routes", lambda d: d["steps"][0].update(path="/admin.htm"), "outside routes")
rejects("duplicate input", lambda d: d["inputs"].append(copy.deepcopy(d["inputs"][0])), "duplicate input name")
rejects("checkpoint missing text", lambda d: d["checkpoint"].pop("text_present"), "a checkpoint needs both")
rejects("business rule without outcome", lambda d: d["outcome_rules"][0].pop("outcome"), "business rules need an UPPER_SNAKE outcome")
rejects("recoverable rule without action", lambda d: d["outcome_rules"][1].pop("action"), "recoverable rules need an action")
rejects("hard rule with an action", lambda d: d["outcome_rules"][2].update(action="retry"), "hard rules carry only a message")
rejects("bad input regex", lambda d: d["inputs"][0].update(pattern="["), "pattern is not a valid regex")
rejects("secret used as a plain input", lambda d: d["steps"][0].update(path="/activity.htm?id={{secret:password}}"), "only allowed as a typed value")

# steps and locators
def bad_click(d):
    d["steps"].insert(1, {"action": "click", "target": {"locators": [{"strategy": "labeled_value", "label": "Balance:"}]}})
rejects("labeled_value in a click", bad_click, "only allowed in extract steps")

def bad_order(d):
    d["steps"][1]["target"]["locators"] = [
        {"strategy": "text", "text": "Balance:", "stability": "low"},
        {"strategy": "label", "label": "Balance:", "stability": "high"},
    ]
rejects("locators out of order", bad_order, "ordered from most to least stable")

def page_wide_index(d):
    d["steps"][1]["target"]["locators"] = [{"strategy": "structure", "tag": "td", "nth": 18}]
rejects("page-wide index (no container)", page_wide_index, "within")

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
```

- [ ] **Step 2: Run it and confirm it fails**

Run: `uv run python notebooks/02_artifact_schema.py`
Expected: FAIL with `NameError: name 'from_yaml' is not defined` (or `Capability`).

- [ ] **Step 3: Add the implementation cells above the checks cell**

```python
# %% Section 2: Capability and cross-field checks
class App(Strict):
    id: Name                              # the vendor product, e.g. parabank. Shared by many tenants (D21).
    base_url: str = Field(pattern=r"^https?://")
    vendor: str | None = None


class BaseRef(Strict):
    """D21: this capability specializes another. Stored now, applied in a later phase."""
    name: Name
    version: int = Field(ge=1)


class Override(Strict):
    path: str                             # e.g. "steps[1].target.locators[0].name"
    value: Any


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
    description: str
    when_to_use: str                      # lets a calling agent choose this capability by name
    app: App
    base: BaseRef | None = None
    overrides: list[Override] = []
    risk_level: Risk
    inputs: list[InputParam] = []
    outputs: list[OutputParam] = []
    secrets: list[Name] = []              # names only. Values live in .env (D32).
    routes: list[str]                     # the pages this capability may touch; feeds the allowlist (D15)
    steps: list[Step] = Field(min_length=1)
    checkpoint: Checkpoint
    outcome_rules: list[OutcomeRule] = []

    @field_validator("routes")
    @classmethod
    def _routes(cls, v):
        if not v or any(not r.startswith("/") for r in v):
            raise ValueError("routes must be a non-empty list of paths starting with '/'")
        return v

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
                if not any(s.path.startswith(r) for r in self.routes):
                    problems.append(f"{where}: path {s.path!r} is outside routes {self.routes}")
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
                for loc in s.target.locators:
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
```

```python
# %% Section 2a: YAML load and save
import yaml


def to_yaml(cap: Capability) -> str:
    """Stable, human-readable YAML. Keys keep the model's field order."""
    return yaml.safe_dump(cap.model_dump(mode="json", exclude_none=True), sort_keys=False, allow_unicode=True, width=100)


def from_yaml(text: str) -> Capability:
    return Capability.model_validate(yaml.safe_load(text))
```

- [ ] **Step 4: Run and confirm it passes**

Run: `uv run python notebooks/02_artifact_schema.py`
Expected, after the Task 2 line: `examples load: ok`, then 19 lines starting `rejected ok:` (typo in a key, unknown input reference, malformed template, output never extracted, extract into undeclared output, navigate outside routes, duplicate input, checkpoint missing text, business rule without outcome, recoverable rule without action, hard rule with an action, bad input regex, secret used as a plain input, labeled_value in a click, locators out of order, page-wide index (no container), risky step but risk_level safe, safe capability marked risky, amount_input not declared), then `yaml round trip: ok` and `capability: all checks passed`.

- [ ] **Step 5: Commit**

```bash
git add notebooks/02_artifact_schema.py
git commit -m "feat(schema): Capability with cross-field checks and YAML round trip"
```

---

### Task 4: The calling agent's tool contract

**Files:**
- Modify: `notebooks/02_artifact_schema.py` (append Sections 3 and 3b)

**Interfaces:**
- Consumes: `Capability`, and the `bal` and `xfer` variables loaded in Task 3's checks.
- Produces: `tool_contract(cap: Capability) -> dict` with keys `name`, `description`, `input_schema`, `returns`.

- [ ] **Step 1: Append the checks cell first**

```python
# %% Section 3b: checks for the tool contract
# what a calling agent sees
import json

import json
contract = tool_contract(xfer)
assert contract["input_schema"]["required"] == ["from_account", "to_account", "amount"]
assert contract["returns"]["may_need_approval"] is True
assert tool_contract(bal)["returns"]["business_outcomes"] == ["ACCOUNT_NOT_FOUND"]
print(json.dumps(tool_contract(bal), indent=2))

print("io: all checks passed")
```

- [ ] **Step 2: Run it and confirm it fails**

Run: `uv run python notebooks/02_artifact_schema.py`
Expected: FAIL with `NameError: name 'tool_contract' is not defined`.

- [ ] **Step 3: Add the implementation cell above the checks cell**

```python
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
        "description": f"{cap.description} Use when: {cap.when_to_use}",
        "input_schema": {"type": "object", "properties": props, "required": required, "additionalProperties": False},
        "returns": {
            "outputs": {o.name: {"type": _JSON_TYPE[o.type], "description": o.description} for o in cap.outputs},
            "business_outcomes": sorted({r.outcome for r in cap.outcome_rules if r.kind == "business"}),
            "may_need_approval": cap.risk_level == "risky",
        },
    }
```

- [ ] **Step 4: Run and confirm it passes**

Run: `uv run python notebooks/02_artifact_schema.py`
Expected: after Task 3's output, a printed JSON contract for `get_account_balance` (with `input_schema.required == ["account_id"]`, `returns.business_outcomes == ["ACCOUNT_NOT_FOUND"]`, `returns.may_need_approval == false`), then `io: all checks passed`.

- [ ] **Step 5: Commit**

```bash
git add notebooks/02_artifact_schema.py
git commit -m "feat(schema): tool contract for calling agents"
```

---

### Task 5: The replay result contract

**Files:**
- Modify: `notebooks/02_artifact_schema.py` (append Sections 4 and 4b)

**Interfaces:**
- Consumes: `Capability`, `Strict`, `Name`, and `bal` from Task 3.
- Produces: `Failure`, `ReplayResult`, `check_result(cap: Capability, result: ReplayResult) -> None` (raises `ValueError` on a mismatch).

- [ ] **Step 1: Append the checks cell first**

```python
# %% Section 4b: checks for the result contract
# the replay result contract
def ok(**kw):
    base = dict(run_id="r1", capability="get_account_balance", capability_version=1)
    return ReplayResult(**base, **kw)

check_result(bal, ok(status="SUCCESS", outputs={"balance": "$1,200.00"}))
check_result(bal, ok(status="BUSINESS_OUTCOME", outcome="ACCOUNT_NOT_FOUND"))
ok(status="NEEDS_APPROVAL", pending_step=4, reason="amount above the auto-approve limit")
ok(status="FAILED", failure=Failure(step_index=1, step_action="extract", expected="a value next to 'Balance:'", observed="no such label on the page", evidence="evidence/r1/step1.png"))

def result_rejects(name, fn, expect):
    try:
        fn()
    except (ValidationError, ValueError) as err:
        assert expect in str(err), f"{name}: expected {expect!r} in {err}"
        print(f"rejected ok: {name}")
        return
    raise AssertionError(f"{name}: was NOT rejected")

result_rejects("FAILED without failure", lambda: ok(status="FAILED"), "FAILED needs a failure")
result_rejects("BUSINESS_OUTCOME without outcome", lambda: ok(status="BUSINESS_OUTCOME"), "needs an outcome")
result_rejects("NEEDS_APPROVAL without reason", lambda: ok(status="NEEDS_APPROVAL", pending_step=1), "needs pending_step and reason")
result_rejects("SUCCESS with an outcome", lambda: ok(status="SUCCESS", outcome="X"), "SUCCESS carries only outputs")
result_rejects("undeclared outcome", lambda: check_result(bal, ok(status="BUSINESS_OUTCOME", outcome="MADE_UP")), "is not declared")
result_rejects("missing output", lambda: check_result(bal, ok(status="SUCCESS", outputs={})), "!= declared outputs")
print("\nALL CHECKS PASSED")
```

- [ ] **Step 2: Run it and confirm it fails**

Run: `uv run python notebooks/02_artifact_schema.py`
Expected: FAIL with `NameError: name 'ReplayResult' is not defined`.

- [ ] **Step 3: Add the implementation cell above the checks cell**

```python
# %% Section 4: replay result contract
class Failure(Strict):
    step_index: int = Field(ge=0)
    step_action: str
    expected: str
    observed: str
    evidence: str | None = None           # path to the screenshot / page snapshot


class ReplayResult(Strict):
    """What replay returns to the caller (D27)."""
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
```

- [ ] **Step 4: Run and confirm it passes**

Run: `uv run python notebooks/02_artifact_schema.py`
Expected: 6 lines starting `rejected ok:` (FAILED without failure, BUSINESS_OUTCOME without outcome, NEEDS_APPROVAL without reason, SUCCESS with an outcome, undeclared outcome, missing output), then `ALL CHECKS PASSED`.

- [ ] **Step 5: Commit**

```bash
git add notebooks/02_artifact_schema.py
git commit -m "feat(schema): replay result contract"
```

---

### Task 6: Notebook pair, decisions, hand back

**Files:**
- Create: `notebooks/02_artifact_schema.ipynb`
- Modify: `DECISIONS.md`, `CLAUDE.md`

- [ ] **Step 1: Run the whole notebook once more, from `notebooks/` as well as the repo root**

```bash
uv run python notebooks/02_artifact_schema.py | tail -3
(cd notebooks && uv run python 02_artifact_schema.py | tail -3)
```

Expected: both end with `ALL CHECKS PASSED`.

- [ ] **Step 2: Generate the notebook pair**

```bash
uv run jupytext --to ipynb notebooks/02_artifact_schema.py
```

Expected: `notebooks/02_artifact_schema.ipynb` exists. It has no outputs (nbstripout).

- [ ] **Step 3: Add section L to `DECISIONS.md`**, right after section K and before "## H. Assumptions and defaults":

```markdown
## L. Phase 2 decisions (artifact schema)

### D37 — Strict, layered artifact schema

**Question:** What shape is the artifact so both a human reviewer and a calling agent can rely on it?

**Options:** (a) Free-form YAML with a light check. (b) Strict Pydantic models: unknown keys rejected, every cross-reference checked.

**Chosen:** (b).

**Reasoning:**
- 3.2 makes the schema "a focal point of the evaluation". A typo (`descripton`) or a reference to a missing input must fail loudly at load time, not at 3 a.m. during replay.
- The `Capability` check collects every problem at once, so a reviewer fixes a file in one pass.
- Locators are ranked, and a page-wide index is forbidden (a structure locator needs a container). That encodes the Phase 1 lesson that global indexes break when anything is added.
- Text fields accept only `{{input}}` and `{{secret:name}}`. Secrets are names, never values, and are allowed only as typed values (D32).
- The checkpoint needs both a URL signal and a content signal (D9).

**Brief ref:** 3.2, 3.3.

### D38 — Risk is in the artifact; the limit is in config

**Chosen:** a click step is `safe` or `risky`. A risky step names which input holds the money (`amount_input`). The capability's `risk_level` must agree with its steps. The dollar limit (D20) stays in config, not in the artifact.

**Reasoning:** the artifact says *what is risky*; policy says *how much is allowed*. That way one artifact works under different limits per tenant, and a reviewer sees the point of no return in the file.

**Applies to any money step, bill payment included.** Replay of a recorded payment needs no human to navigate or fill values (the caller supplies typed inputs), and no human for amounts up to the limit. Above the limit it stops before the final click and returns `NEEDS_APPROVAL`. Recording a flow makes it repeatable; it does not make a payment safe, which is why the irreversible step is judged by policy each time. Upgrade path, described in the report and not built: also require a previously used payee before auto-approving.

**Brief ref:** 3.4, 3.6.

### D39 — Result contract and tool contract

**Chosen:** `ReplayResult` has four statuses (`SUCCESS`, `BUSINESS_OUTCOME`, `NEEDS_APPROVAL`, `FAILED`), each requiring exactly its own fields. `check_result` checks a result against the capability: outputs must match the declared outputs, and a business outcome must be one the capability declares. `tool_contract()` derives what a calling agent sees: description, input schema, outputs, business outcomes, may-need-approval.

**Reasoning:** the brief asks that a calling agent understand what a capability needs and returns, and that business outcomes are never mixed up with failures (D10, D27). Making the shape checkable stops replay from returning ambiguous results.

**Brief ref:** 3.2, 3.3.

### D40 — Multi-tenant fields stored, not applied

**Chosen:** `app.id`, `base`, and `overrides` exist in the schema and are shape-checked. Applying an override is not built.

**Reasoning:** 3.7 asks that the core abstractions not paint us into a corner. The fields cost almost nothing now and avoid a schema change later; building the override machinery is explicitly not rewarded.

**Brief ref:** 3.7.
```

- [ ] **Step 4: Update `CLAUDE.md`**: under "Phase 1 notebooks" add a new heading and line:

```markdown
## Phase 2 notebook
- `02_artifact_schema.py` — artifact schema (Pydantic + YAML), tool contract, replay result contract. Pure Python.
```

- [ ] **Step 5: Confirm no secret is staged, then commit**

```bash
git add notebooks/02_artifact_schema.ipynb DECISIONS.md CLAUDE.md
git status --short
git commit -m "docs(schema): phase 2 complete, decisions D37-D40"
```

`.env` must not appear in `git status`.

- [ ] **Step 6: Stop and hand back to the user.** Report what passes. Do not start Phase 3. The user reads the two example files first; they are the best way to review the schema.

---

## Self-review

**Spec coverage (Phase 2 scope).**
- 3.2 ordered steps, per-element identification with robustness (stability and note), typed inputs, typed outputs, checkpoint, versioned, reviewable → Tasks 2-3, examples in Task 1. ✓
- D7 YAML, backed by Pydantic → Task 3. ✓
- D8 ranked locators, no page-wide index → Task 2 (`Target`, `StructureLocator`). ✓
- D9 URL and content checkpoint → Task 2 (`Checkpoint`). ✓
- D10 business, recoverable, hard rules, with the outcome name and action → Task 2 (`OutcomeRule`). ✓
- D12 typed extract outputs → Tasks 2-3 (`Extract`, output cross-check, `labeled_value`). ✓
- D21 `base` and `overrides` fields → Task 3, D40. ✓
- D27 result contract → Task 5. ✓
- D29 declared typed inputs (the leftover-literal check itself is Phase 3) → Task 3. ✓
- D32 secrets by name → Tasks 2-3. ✓
- D33 / D20 risky step marker → Task 3, D38. ✓
- Phase 1 carry-forward for Phase 2 ("`{{secret:name}}` references and typed inputs; express 'needs human approval'") → covered. ✓
- Not in this phase, by design: the recorder (3), replay engine (4-5), applying overrides, real business-outcome text (Phase 3 probe), safety config (6).

**Placeholder scan.** No `TBD`, no `TODO`. The example artifacts say their outcome text is illustrative, and the plan says so in "Known limits".

**Type consistency.** `Capability`, `ReplayResult`, `Failure`, `Target`, `Step`, `OutcomeRule`, `to_yaml`, `from_yaml`, `tool_contract`, `check_result`, `template_refs`, `malformed_template`, `locator_strings`, `raises`, `rejects`, `bal`, `xfer` are each defined once and used with the same signatures. Cell order: Task 2 cells, Task 3 (Capability, YAML, checks), Task 4 (contract, checks), Task 5 (result, checks).
