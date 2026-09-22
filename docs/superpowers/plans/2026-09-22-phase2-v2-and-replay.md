# Phase 2 v2 + Phase 4: simplified artifact schema, and the replay engine

> **For agentic workers:** REQUIRED SUB-SKILL: superpowers:subagent-driven-development or
> superpowers:executing-plans, task-by-task. Checkbox (`- [ ]`) syntax tracks steps.
>
> This is pure Python throughout (Task A and Task B). No browser, no network, no API key. The
> sub-agent runs both notebooks as scripts (`uv run python notebooks/0N_*.py`) to prove each task
> passes; the user re-runs them as notebooks afterwards.

**Goal:** (A) Rebuild `notebooks/02_artifact_schema.py` with the simplified schema agreed in
conversation (locators: primary + one optional fallback, not a ranked list; multi-tenant fields
cut; `routes` derived, not stored; `when_to_use` folded into `description`). (B) Build a new
`notebooks/04_replay_engine.py`: a deterministic, no-LLM engine that walks a `Capability`'s steps
against a fake surface, proven against the two rebuilt example artifacts end to end.

**Architecture:** Task A rebuilds one notebook in the same layered order as before: locators/
steps/rules, then `Capability` + cross-checks + YAML, then `tool_contract`, then `ReplayResult`
(unchanged). Task B is a new notebook that `exec`s Task A's non-check cells into its own
namespace (the same technique `03_recorder.py` already uses for `02_artifact_schema.py`), then
adds a `ReplaySurface` protocol, `resolve_target`, template substitution, and `run_capability`,
tested with a hand-built `FakeSurface`.

**Tech Stack:** Python 3.12, Pydantic v2, PyYAML, jupytext, uv. No new dependency.

**Spec:** the CONTEXT block agreed with the user (cut/keep table), applied on top of
`DECISIONS.md` D7-D12, D20, D26, D27, D29, D32-D34, D37-D40 (being superseded here), D50-D62
(Phase 1 safety/escalation, reused conceptually for the `escalate` seam). Brief 3.2, 3.3.

**Verified:** every code block below, and the full engine + both example artifacts, were run
together with `uv run python` in a scratch file on 2026-09-22 (Python 3.12, Pydantic 2.13.5,
PyYAML 6.0.3): all model/Capability/contract/result checks passed, all 8+ replay-engine scenarios
passed, and both `get_account_balance` and `transfer_funds` ran through `run_capability` with a
`FakeSurface` end to end (happy path, business outcome, and over-limit approval for the risky one).

## Global Constraints

- Pure Python. No `import playwright`, no `deepagents`, no network, no API key, anywhere in
  either notebook. Do not touch `agent.ipynb`, `03_recorder.py/.ipynb`, or `01_*`.
- Unknown keys stay errors (`extra="forbid"`), same as before.
- `ReplayResult` (D27) is reused unmodified — imported by running Task A's Section 4 cell in
  Task B's namespace, never redefined.
- Follow red-then-green: append the checks cell, run and confirm a clear `NameError`, then add
  the implementation cell above it, run and confirm it passes, then commit.
- `git status --short` before every commit; `.env` must never appear. Both `.ipynb` files carry
  no outputs (`nbstripout`).

---

## What changes in the schema (source of truth: the table agreed in conversation)

| Piece | Verdict |
|---|---|
| Typed inputs/outputs, steps, checkpoint (both signals) | KEEP, unchanged in spirit |
| `risk_level` + per-step risk + `amount_input` | KEEP |
| `outcome_rules`, business/recoverable/hard shape | KEEP |
| `secrets` (names only), `status` | KEEP |
| Locators: ranked list of ~3 | **-> exactly one `primary` + one optional `fallback`**, each with `strategy`, its fields, `stability`, and a now-**required** `note`. `structure` still needs `within`. `labeled_value` still extract-only. |
| `app.id`, `app.vendor`, `base`, `overrides` | **CUT.** Replaced by a single top-level `base_url: str` field. Multi-tenant reuse stays a REPORT.md design discussion (3.7 says design, not build). |
| `routes` (stored list) | **CUT as a field.** `derived_routes(cap) -> list[str]` computes it from `navigate` steps. |
| `when_to_use` | **CUT, folded into `description`.** One field. |
| `tool_contract()` | KEEP the concept; its `description` is now just `cap.description`. |

### Locators: how "at most one fallback" is enforced

`Target` becomes `primary: Locator`, `fallback: Locator | None`. This is a type-level choice, not
a runtime length check: with two named, singular fields there is no list to put a third locator
into, so a third locator is **not representable**, not merely rejected. A stray extra key (e.g.
`third: {...}`) is still caught, but by the pre-existing `extra="forbid"` base, the same mechanism
that already catches a typo'd field name — no new validator needed. The stability-ordering check
that used to walk a list now compares exactly two ranks: `fallback` must not be strictly more
stable than `primary`.

### `base_url` shape

A single field on `Capability`: `base_url: str = Field(pattern=r"^https?://")`. No wrapper `App`
object — with only one field left, a wrapper adds a nesting level for nothing (compare the old
`app: {id, base_url, vendor}` block to one line — that comparison is the point of this exercise).

### `derived_routes`

```python
def derived_routes(cap: Capability) -> list[str]:
    """The pages this capability may touch, derived from its own navigate steps (D65) instead of
    a separately-maintained list. First-appearance order, no duplicates, query string dropped."""
    routes: list[str] = []
    for s in cap.steps:
        if s.action == "navigate":
            route = s.path.split("?")[0]
            if route not in routes:
                routes.append(route)
    return routes
```
Verified: `derived_routes(bal) == ["/activity.htm"]`, `derived_routes(xfer) == ["/transfer.htm"]`.

---

## File structure

```
artifacts/examples/get_account_balance.yaml    # Task A: rewritten to the simplified shape
artifacts/examples/transfer_funds.yaml         # Task A: rewritten, shows primary+fallback
notebooks/02_artifact_schema.py (+ .ipynb)     # Task A: rebuilt
notebooks/04_replay_engine.py (+ .ipynb)       # Task B: new
DECISIONS.md                                   # Task A: section O (D63-D66); supersede notes on D37-D40
CLAUDE.md                                      # Task A/B: phase notebook list
docs/superpowers/plans/2026-09-22-*.md         # this plan
```

---

## Task A: rebuild `02_artifact_schema.py`

- [ ] **Step 1: Section 1 + 1b (locators, conditions, steps, rules)** — same models as before
  (`Strict`, `Within`, the five `*Locator` classes, `Condition`, `Checkpoint`, the five `Step`
  classes, `OutcomeRule`), with two changes: every locator's `note` becomes
  `Field(min_length=1)` (required), and `Target` becomes:

  ```python
  class Target(Strict):
      primary: Locator
      fallback: Locator | None = None

      @model_validator(mode="after")
      def _ranked(self):
          if self.fallback is not None and _RANK[self.fallback.stability] < _RANK[self.primary.stability]:
              raise ValueError("locators must be ordered from most to least stable (primary, then fallback)")
          return self

      def locators(self) -> list:
          return [self.primary] + ([self.fallback] if self.fallback else [])
  ```
  `locators()` keeps `locator_strings`/`_no_labeled_value` one-liners unchanged (they iterate
  `target.locators()` instead of `target.locators`).

  Checks cell first (confirm `NameError: Target`), then implementation, confirm `models: all
  checks passed`: a primary+fallback `Target` builds; fallback-more-stable-than-primary is
  rejected; a locator with no `note` is rejected; `primary`+`fallback`+a third key is rejected
  with `Extra inputs are not permitted` (the "3rd locator has no slot" check); `structure` (needs
  `within`), `Checkpoint` (needs both signals), `OutcomeRule` shape, `Navigate` path all still
  reject as before.

  Commit: `feat(schema): locators simplified to primary+fallback, required note (D63)`

- [ ] **Step 2: rewrite the two example YAML files** to the simplified shape: no `app:` block
  (`base_url:` top-level), no `when_to_use:` (merged into `description:`), no `routes:` block,
  and every locator under `target.primary:` / `target.fallback:` with a `note:`.
  `transfer_funds.yaml`'s `type` step (the amount field) gets a `fallback` (a `structure` locator
  inside the form) — this is the concrete "primary + fallback" example. Full text verified
  loading correctly is in the scratch run; see the checked-in files for the final text.

  Commit: `feat(schema): rewrite example artifacts to the simplified shape`

- [ ] **Step 3: Section 2 + 2a + 2b (`Capability`, YAML, cross-checks)** — same `InputParam`/
  `OutputParam`; `App`/`BaseRef`/`Override` classes are deleted entirely; `Capability` drops
  `app`, `base`, `overrides`, `routes`, `when_to_use`, keeping `description` and adding
  `base_url: str = Field(pattern=r"^https?://")`. The `_consistent` cross-check drops the
  "navigate outside routes" branch (nothing to check against any more) and otherwise is
  unchanged (duplicate names, malformed templates, unknown input/secret refs, one-extract-per-
  output, risk_level agreement, `amount_input` checks) — now iterating `s.target.locators()`.
  Add `derived_routes` (above) alongside `to_yaml`/`from_yaml`.

  Checks first (`NameError: Capability`), then implementation, confirm `capability: all checks
  passed`: the same ~19 `rejected ok:` lines as before minus the routes one (nothing left to
  violate), plus `derived routes: ok`, `base_url check: ok`, and `rejected ok: locator missing
  note`. YAML round-trip stays lossless for both examples.

  Commit: `feat(schema): Capability without app/base/overrides/routes/when_to_use (D64, D65, D66)`

- [ ] **Step 4: Section 3 + 3b (`tool_contract`)** — unchanged function body except
  `"description": cap.description` (no `Use when: ...` suffix, since there is only one field now).
  Checks confirm `input_schema.required`, `may_need_approval`, `business_outcomes` all still
  compute correctly, plus a new assertion that the contract has no `when_to_use` echo.

  Commit: `feat(schema): tool contract reads description only (D66)`

- [ ] **Step 5: Section 4 + 4b (`ReplayResult`)** — copied over completely unchanged (D27 does
  not change). Checks: same 6 `rejected ok:` lines as the original Phase 2 notebook, ending
  `ALL CHECKS PASSED`.

  Commit: `feat(schema): replay result contract (unchanged, D27)`

- [ ] **Step 6: notebook pair + decisions + CLAUDE.md**
  - `uv run jupytext --to ipynb notebooks/02_artifact_schema.py`
  - Append **section O** to `DECISIONS.md` (after section J, the last section in the file) with
    D63-D66, one row of the cut table each (locators, multi-tenant, routes, when_to_use), same
    Question/Options/Chosen/Reasoning/Brief-ref shape as the rest of the file.
  - Add an `> **Update:** superseded by D63-D66, see section O.` line under each of D37, D38,
    D39, D40's own heading, matching the existing "superseded"/"REMOVED, see" pattern used
    elsewhere in the file (e.g. D11/D17, D51) — the original text stays, only the update line is
    added.
  - Update `CLAUDE.md`'s Phase 2 line to note the rebuild.
  - `git status --short` (no `.env`), commit: `docs(schema): rebuild complete, decisions D63-D66`

---

## Task B: `notebooks/04_replay_engine.py`

- [ ] **Step 1: schema loader + `ReplaySurface` + exceptions**

  ```python
  def load_schema(wanted=("Section 1:", "Section 2:", "Section 2a:", "Section 3:", "Section 4:")):
      text = (REPO / "notebooks" / "02_artifact_schema.py").read_text()
      for cell in re.split(r"(?m)^# %%", text)[1:]:
          header, _, body = cell.partition("\n")
          if header.strip().startswith(wanted):
              exec(compile(body, f"02_artifact_schema.py [{header.strip()}]", "exec"), globals())
  load_schema()
  ```
  This is the same technique `03_recorder.py` already uses — `wanted` prefixes exclude every
  `*b`-suffixed checks cell, so only models, `Capability`, YAML, `tool_contract`, and
  `ReplayResult`/`Failure`/`check_result` land in this notebook's namespace. Nothing is redefined.

  A markdown cell documents the seam plainly: the real Phase 9 surface wraps agent.ipynb's own
  `PlaywrightSurface` plus its lock/banner/`human_takeover` mechanism (STEP 2/3 there); replay is
  a new, non-LLM **caller** of that same Surface and safety layer, not a reinvention of browser
  automation.

  ```python
  class ReplaySurface(Protocol):
      def navigate(self, path: str) -> None: ...
      def resolve(self, locator) -> Any | None: ...
      def click(self, ref) -> None: ...
      def type_text(self, ref, value: str) -> None: ...
      def select_option(self, ref, value: str) -> None: ...
      def read_value(self, ref) -> str: ...
      def current_url(self) -> str: ...
      def page_text(self) -> str: ...

  class TransientFailure(Exception): ...      # a surface raises this to simulate a flaky/slow step
  class ResolutionError(Exception): ...        # neither primary nor fallback resolved
  class InputValidationError(Exception): ...   # a caller input is missing/mistyped/pattern-mismatched
  ```

  **Deviation, noted up front:** the brief's `ReplaySurface` method list omits `navigate`, but a
  `navigate` step has no other way to change the page, and a Playwright surface needs this call
  regardless. Adding it to the Protocol is small and reversible, so it is added rather than raised
  as a blocking question.

  Checks: `NameError: ReplaySurface` first; then a minimal object satisfying the Protocol
  type-checks, and each exception class is a plain `Exception` subclass.

  Commit: `feat(replay): schema loader, ReplaySurface protocol, exception types`

- [ ] **Step 2: `resolve_target` + template substitution + input validation**

  ```python
  def resolve_target(surface, target, *, logger=lambda m: None):
      ref = surface.resolve(target.primary)
      if ref is not None:
          logger(f"resolved via primary ({target.primary.strategy})"); return ref
      if target.fallback is not None:
          ref = surface.resolve(target.fallback)
          if ref is not None:
              logger(f"primary failed, resolved via fallback ({target.fallback.strategy})"); return ref
      raise ResolutionError(target)
  ```
  Plus `describe_locator`/`describe_target` (human-readable "what was expected", used in
  `Failure.expected`), `matches_value_type(value, type_) -> bool` (basic format check per
  `ValueType`, shared by input validation and output validation), `validate_inputs(cap, raw) ->
  dict[str,str]` (type + pattern check, raises `InputValidationError` naming every problem), and
  `render(text, values, secrets)` (substitutes `{{input}}`/`{{secret:name}}` using the *same*
  `_TEMPLATE` regex object loaded from the schema — not a re-implementation).

  Checks: primary-hit, fallback-hit (and logged), both-miss raises `ResolutionError` naming
  primary and fallback; `render` substitutes both kinds of reference; `validate_inputs` accepts a
  good value, rejects a bad pattern, rejects a bad type, rejects an undeclared extra input.

  Commit: `feat(replay): resolve_target, template substitution, input validation`

- [ ] **Step 3: `run_capability` (the engine loop)**

  Dispatches by `step.action`. Per action:
  - `navigate`: `surface.navigate(render(step.path, ...))`.
  - `click`, `risk == "risky"`: parse `amount_input`'s value (`parse_amount`, unparsable ->
    `inf`, i.e. always needs approval); `< auto_approve_limit` -> resolve + `surface.click(ref)`;
    `>= limit` -> **return `NEEDS_APPROVAL` immediately, without resolving or clicking**, calling
    `escalate(reason, context)` first if given.
  - `click`, safe / `type` / `select`: resolve, then the matching surface call.
  - `extract`: resolve, `surface.read_value(ref)`, check `matches_value_type` against the
    declared output's type — a mismatch is `FAILED`, not a silently-wrong `SUCCESS`.
  - After a step's own `expect` (if set) and after every step, evaluate `outcome_rules` **in
    declared order, first match wins**: `business` -> `BUSINESS_OUTCOME`; `hard` -> `FAILED`
    (`escalate` called if given); `recoverable` -> logged, run continues (known limit below).
  - Retries: only for steps that are not a risky click (D26), bounded at `max_retries` (default
    2), only on `TransientFailure`. A `ResolutionError` is never retried.
  - After the last step: check `checkpoint` against `surface.current_url()`/`page_text()` ->
    `FAILED` if it does not hold; else build `SUCCESS` with the collected `outputs`.

  **Known limit (markdown cell, not hidden):** a matched `recoverable` rule is logged and replay
  moves on; it does not yet perform `dismiss`/`wait`/`relogin` itself — that needs a live surface
  or capability composition, both Phase 9 concerns. Neither example artifact exercises this path.

  Checks — all 8 required scenarios plus 3 extra (retry-then-succeed, retry-exhausted, risky
  click never retried) and one input-rejection check, against a small hand-built `FakeSurface`
  (dict-based: pages by url, a locator registry per url, per-ref values, `click_effects` for a
  click that changes the current page's text without changing its url):

  1. happy path -> `SUCCESS`, correct `outputs`
  2. business-outcome page state -> `BUSINESS_OUTCOME` with the declared name
  3. primary fails, fallback succeeds -> `SUCCESS`, logged (`"...resolved via fallback..."`)
  4. both fail -> `FAILED`, `failure.expected` names primary and fallback, `.observed` says so
  5. risky click under the limit -> proceeds automatically, `SUCCESS`
  6. risky click at/above the limit -> `NEEDS_APPROVAL`, `escalate` called once, `ref not in
     surface.clicked`
  7. checkpoint fails after all steps ran -> `FAILED`, `step_action == "checkpoint"`
  8. extracted value fails its declared type -> `FAILED`, `step_action == "extract"`, not
     `SUCCESS`

  Commit: `feat(replay): run_capability engine, offline tests for all 8 required scenarios`

- [ ] **Step 4: integration check — both example artifacts through the engine**

  Build one `FakeSurface` per example, registering exactly the locators each artifact's own
  `target.primary`/`.fallback` declare (so this is checking the *real* files, not a stand-in):
  - `get_account_balance`: good id -> `SUCCESS` with `outputs == {"balance": "$1,200.00"}`,
    cross-checked with `check_result`; bad id -> its own declared `ACCOUNT_NOT_FOUND`
    `BUSINESS_OUTCOME`.
  - `transfer_funds`: under the limit -> `SUCCESS`, `outputs == {"confirmation": "Transfer
    Complete!"}`, and the fake surface's `typed`/`selected`/`clicked` state matches what the
    steps declared; at/above the limit -> `NEEDS_APPROVAL`, `escalate` called once, the Transfer
    button's ref never in `surface.clicked`.

  This is the check that proves Task A's simplified schema and Task B's engine actually agree
  with each other end to end, per the brief.

  Commit: `feat(replay): integration check, both example artifacts through the engine`

- [ ] **Step 5: notebook pair + CLAUDE.md**
  - `uv run jupytext --to ipynb notebooks/04_replay_engine.py`
  - Add a "Phase 4 notebook" line to `CLAUDE.md`.
  - `git status --short` (no `.env`), commit: `docs(replay): notebook pair, CLAUDE.md phase 4 line`
  - Stop. Do not start Phase 3 recorder rebuild or Phase 9. Report to the user.

---

## Self-review

- **3.2** (typed I/O, per-element identification with robustness reasoning, checkpoint,
  versioned/reviewable): Task A, now with a *required* note per locator — a stronger version of
  the robustness-reasoning requirement than before, since it can no longer be left blank. ✓
- **3.3** (deterministic replay, no LLM, business/recoverable/hard separated, structured
  step/expected/observed result): Task B `run_capability` + `Failure`. ✓
- **3.4** (risky steps handled conservatively): the risky-click amount gate, checked before any
  resolution or click. ✓
- **3.6** (escalation seam): the `escalate` hook, explicitly documented as the Phase 9 wire point
  to `human_takeover`, not a UI built here. ✓
- **3.7** (no painting into a corner): `base_url` is the only surface-specific field left; nothing
  about `ReplaySurface` or `run_capability` assumes ParaBank. ✓
- Not in this task, by design: applying the (removed) override machinery — moot, since the fields
  are gone; a live login/relogin capability composition; any browser or network code.
