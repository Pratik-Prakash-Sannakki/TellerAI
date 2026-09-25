# Phase 3 v2: rebuild the recorder against the current schema and agent

> **For agentic workers:** REQUIRED SUB-SKILL: superpowers:subagent-driven-development or
> superpowers:executing-plans, task-by-task. Checkbox (`- [ ]`) syntax tracks steps.
>
> Task A (COMPILE) is pure Python. Run it as `uv run python notebooks/03_recorder.py` against a
> harness that execs only the `OFFLINE`-prefixed cells (same technique `04_replay_engine.py` uses
> to load `02_artifact_schema.py`). Task B (CAPTURE) needs a real browser + API key; it is written
> here but **never run** by the agent — the user runs it.

**Goal:** the existing `notebooks/03_recorder.py` targets a schema that no longer exists
(`Target(locators=[...])`, `Capability(app=..., when_to_use=..., routes=...)`) and copies browser
tools from before every Phase 1 safety fix. Rebuild it from scratch against the CURRENT
`02_artifact_schema.py` (D63-D68: `primary`/`fallback` locators, no `app`/`routes`/`when_to_use`,
`base_url` only) and the CURRENT `agent.ipynb` (D50-D69: the lock, the approval gate inside
`click()`, `request_missing_values`, the login attempt guard).

**Architecture:** same two-part split as before (D41). Part A (COMPILE) is a pure function
`events + declared inputs -> Capability`, tested entirely with hand-made fixture events. Part B
(CAPTURE) copies agent.ipynb's current setup/scanner/tools/safety cells verbatim, then adds capture
as an outer wrapper around each tool's `.coroutine` (never touching the tool's own body), plus two
small new tools the compiler needs that agent.ipynb has no reason to carry itself:
`extract_value` (D46) and `finish_business_outcome` (D47), and `open_path` (D47) for reaching a
page no link points to.

**Tech Stack:** unchanged — Python 3.12, Pydantic v2, PyYAML, jupytext, uv. No new dependency.

**Spec:** `DECISIONS.md` D7-D12 (locators/checkpoint concepts), D32-D34 (login split, value
grounding), D41-D49 (original Phase 3 decisions -- **superseded by this plan**, see below),
D50-D69 (Phase 1 safety/UX built through live testing), D63-D68 (Phase 2 schema simplification,
including D68's stated `label`/`labeled_value` scoping gap, which this rebuild must test for,
not close). Brief 3.2, 3.3, 3.4.

**Verified:** every OFFLINE cell was run with `uv run python` against a harness that execs only
`OFFLINE`-prefixed cells from `notebooks/03_recorder.py` (Python 3.12, Pydantic 2.13.5, PyYAML
6.0.3) on 2026-09-25. Exact output lines are in the final report, not reproduced here since the
plan is written before the run in the usual red/green order; the harness and its output are not
part of the committed notebook (temporary, scratchpad-only).

## Global constraints

- Never run a browser, Playwright, or ParaBank/API-key code. `page`, `browser`, `playwright` must
  never be imported or referenced by any `OFFLINE` cell.
- Do not modify `agent.ipynb`, `02_artifact_schema.py/.ipynb`, `04_replay_engine.py/.ipynb`, or
  `PHASE1.md`/`PHASE2.md`/`PHASE3.md`. Read-only.
- Import Phase 2 models by `exec`-ing `02_artifact_schema.py`'s non-check cells into this
  notebook's namespace (the technique `04_replay_engine.py` already uses) -- never redefine
  `Capability`, `Target`, `Locator`, etc.
- `git status --short` before every commit; `.env` must never appear. Only `git add` the files
  this plan actually touches -- other files in the working tree (`agent.ipynb`, `pyproject.toml`,
  `uv.lock`, `.env.example`, `notebooks/FINDINGS.md`, `PHASE*.md`) are mid-flight from other work
  and are not this plan's concern; never stage them.
- `.ipynb` carries no outputs (`nbstripout` is active project-wide).

---

## What D41-D49 got wrong, and why (superseded, not deleted)

D41 (event-log capture, pure-Python compile) and D43/D44/D45 (clean-up rules, parameterisation,
login split) are correct in **spirit** and are kept. What is superseded, concretely:

| Old decision | What changed under it | Why it breaks today |
|---|---|---|
| D42 (locator derivation) | `Target(locators=[...])`, a ranked list of up to ~3 | `Target` is now `primary` + one optional `fallback` (D63); `Target(locators=...)` is not a valid constructor call any more |
| D45 (login split / capability shape) | `Capability(app=App(**APP), when_to_use=..., routes=_routes(paths))` | `app`, `when_to_use`, `routes` do not exist on `Capability` (D64-D66); `base_url` is the only surface field left |
| D46 (extraction) | `Target(locators=[LabeledValueLocator(...)])` | same `locators=` problem; also the old `LabeledValueLocator` had no required `note` |
| D47 (business outcome, `open_path`) | its own from-scratch `finish(summary, outcome, proof_text)` tool | agent.ipynb's current `finish(summary, values)` has neither field; adding them to `finish` itself would mean respelling agent.ipynb's tool, not importing it. This rebuild adds a **separate** `finish_business_outcome` tool instead (see below) |
| D48 (value grounding) | referenced the OLD recorder's own from-scratch tools' grounding checks | agent.ipynb's current `type_text`/`select_option` already ground values against `GIVEN["text"]` (copied verbatim here); nothing to redo |
| D49 (risk/checkpoint/save guards) | correct in spirit, but written against the old `Target`/`Capability` shape throughout | re-derived below against the current shape; the "last kept step's page" checkpoint rule and the "never overwrite verified" save guard are unchanged in substance |

None of D41-D49's *reasoning* about D23 (what "worked and mattered" means), D29 (leftover-literal
refusal), D32 (login split), or D10 (three-way outcome taxonomy) is wrong -- only the code shape
they were written against. This plan keeps the reasoning and rewrites the code. D68 (the
label/labeled_value scoping gap) is explicitly **not** closed here: this rebuild adds the
duplicate-detection and the flag, per D68's own stated fix ("the recorder... must check during
discovery whether a candidate name/label is duplicated... and, if so, either add a `within` scope
or pick a different strategy" -- for role/text, done; for label/labeled_value, flagged, not solved,
since the schema still has no `within` slot for them).

---

## Event shape (the contract between CAPTURE and COMPILE)

```
{
  "i": int, "tool": str, "args": dict,          # tool name + kwargs, never a secret VALUE
  "message": str,                                # first line of the tool's own text result
  "status": "ok"|"denied"|"declined"|"blocked"|"skip"|"not_yet"|"stop"|"failed"|"handoff",
  "before": {"url": str, "heading": str}, "after": {"url": str, "heading": str},
  "approved": bool,                              # click only: went through the decision bar and was approved
  "el": {role, name, name_source, label, text, tag, type, submit, options,
         container: {role, name} | None, nth, name_count, label_count} | None,
  "value": str | None,        # typed text / selected option / secret NAME (never secret value)
  "label": str | None, "save_as": str | None, "value_type": str | None, "description": str | None,
  "outcome": str | None, "proof": str | None,    # finish_business_outcome only
  "summary": str | None, "values": dict | None,  # finish only
}
```

`status` is computed from the exact prefixes agent.ipynb's tools return, read from the tool code
directly, not guessed: `DENIED:` (click, deny-listed link), `DECLINED` (click, human rejected),
`BLOCKED:` (click, off-site or login-blocked), `SKIP:` (`_ask_for_value`, field already filled),
`NOT YET:` (`ask_human`/`request_value`/`request_missing_values` on a start page), `STOP:` (click,
login attempt guard tripped -- D69), `"A human "` prefix on the success text of any handoff-based
tool (`_ask_for_value`'s non-skip branch, `ask_human`, `request_missing_values`, click's take-over
branch) -> `handoff`; `CLICK FAILED`/`TYPE FAILED`/`SELECT FAILED`/`FAILED for`/`UNKNOWN SECRET`/
`REFUSED:` -> `failed`; anything else -> `ok`.

`el.name_count`/`el.label_count` (D68): how many currently-visible elements on the page share this
exact (role, name) or this exact label. Computed by a small, additive, capture-only JS helper
(`DESCRIBE_JS`) that reads the same `data-cua-ref` attributes agent.ipynb's `OBSERVE_JS` already
sets -- it does not change what the model sees, only what the recorder logs.

---

## Part A: COMPILE (pure Python, `OFFLINE` cells)

1. **Schema loader** (`OFFLINE 1`) -- `exec` `02_artifact_schema.py`'s Section 1/1b/2/2a cells into
   this namespace, same technique as `04_replay_engine.py`.
2. **Helpers** (`OFFLINE 2`) -- `norm_url`, `path_only`, word-boundary literal matching
   (`contains_literal`, `substitute`), `same_value` ($20.00 == 20). Carried over from D44 verbatim
   in spirit (already correct).
3. **Locator derivation** (`OFFLINE 3`) -- `derive_target(el, inputs) -> Target(primary=..., fallback=...)`.
   - `primary`: `role` (high) if `name_source` is accessible (`aria`/`label`/`value`/`text`) and
     role is not generic; else `label` (medium); else `text` (medium).
   - `fallback`: one weaker-but-independent signal when it exists and is not data-dependent (a
     `structure` locator only when a real `container` was captured; never built from a name/label/
     text that itself contains `{{...}}`, per D42's original "no positional fallback for
     data-dependent elements" reasoning, kept unchanged).
   - **Duplicate-name scoping (D68):** if the chosen `role`/`text` locator's name has
     `name_count > 1` and a `container` was captured, attach `within=Within(role=container.role,
     name=container.name)`. If `name_count > 1` and there is no container to scope with, the
     locator is still saved but the compiler appends a clear warning line to the report (cannot
     silently fabricate a container that was never captured).
   - If the only available strategy is `label` (or, for `extract`, `labeled_value`) and
     `label_count > 1`, **refuse that locator** with a `CompileError` naming the label and saying
     plainly that the schema has no `within` slot for `label`/`labeled_value` (D68's stated gap) --
     never save it silently ambiguous.
   - `note` is always a real sentence (never a placeholder), one per strategy, matching the style
     of the two example artifacts.
4. **Clean-up** (`OFFLINE 4`) -- `clean_events` drops non-action tools (`observe`, `page_text`),
   anything whose `status` is not `ok` (this covers `denied`/`declined`/`blocked`/`skip`/`not_yet`/
   `failed` in one rule, per the exact prefixes above), and an identical consecutive repeat on the
   same page (D43). `drop_detours` removes a click-away/click-back pair with nothing meaningful in
   between. `trim_tail` drops link clicks after the last meaningful step (typed/selected/extracted/
   approved-click/submit-button).
   - **Top-level refusal, before any cleanup runs:** if any event has `status == "stop"` (D69's
     login attempt guard fired) or the run's `finish` event's `summary` starts with `STUCK:` or
     `DECLINED:`, `compile_run` raises `CompileError` immediately and produces nothing. This is the
     literal hard rule ("a run blocked by the login attempt guard... must never be compiled into a
     capability at all").
   - Any event with `status == "handoff"` also refuses the whole run (D43: "a hand-typed step
     cannot be recorded").
5. **Login split** (`OFFLINE 5`) -- `split_login`: events up to and including the first `click`
   after the last `type_secret` become the separate `login_<app>` capability (D32/D45), with
   `{{secret:username}}`/`{{secret:password}}` values. The task capability gets zero secret steps
   and starts with a `navigate` to wherever it actually began.
6. **Steps + Capability assembly** (`OFFLINE 6`) -- `build_steps` turns kept events into
   `Navigate`/`Click`/`TypeText`/`Select`/`Extract` steps against the CURRENT step classes.
   `extract_value` events become `Extract(target=Target(primary=LabeledValueLocator(...)),
   save_as=...)`. Parameterisation matches declared input literals to `{{name}}` (whole-value
   match first, then substring with word-boundary matching); typed values matching no input are
   reported as constants, never refused. `find_leftovers` walks the dumped `Capability` (minus
   `inputs`) for any declared literal still present -- refuses the save if found (D29/D44).
   Checkpoint: `url_contains` = last kept step's page's last path segment, `text_present` = that
   event's own `after.heading` (captured at record time); refuse if the heading is empty (D9/D49).
   Risk: a `click` event with `approved: True` becomes `risk: risky`; `amount_input` is the single
   declared `currency`/`number` input, or one named `*amount*`, matching D38's original rule.
   `risk_level` is derived the same way the schema itself checks it.
7. **Business outcome from a probe** (`OFFLINE 6` cont.) -- `rule_from_probe(events, probe_inputs)`
   reads the run's `finish_business_outcome` event (`outcome`, `proof`), cuts the probe's literal
   value out of the proof text (so the rule matches for any input), and builds a `business`
   `OutcomeRule`. `compile_run` refuses outright if the run's terminal event is
   `finish_business_outcome` -- that is a probe, not a task run; use `rule_from_probe` and merge
   the rule into a *different* run's `compile_run(..., extra_rules=[...])` call.
8. **Save** (`OFFLINE 7`) -- `save_capability`: `Capability.model_validate`, refuse if any
   resolved secret VALUE (never printed) appears in the rendered YAML text, refuse to overwrite a
   `status: verified` file, write with a `# DRAFT` comment header, via `to_yaml` only.

---

## Part B: CAPTURE (browser-facing, `BROWSER` cells, never run by the agent)

Copied **verbatim**, cell for cell, from the CURRENT `agent.ipynb` (checked cell-by-cell on
2026-09-25, agent.ipynb having 15 real code cells at that time): `Setup 1/4` (config+secrets),
`Setup 2/4` (browser), `Setup 3/4` (domain guard), `Setup 4/4` (`PlaywrightSurface`/`OBSERVE_JS`/
`Observation`), `STEP 1` (scanner patch: options + submit flag), `STEP 2` (banner, lock, takeover,
decision bar), `STEP 3` (all ten browser tools, `ACT_LOCK`, `needs_human`, `login_check`/
`LOGIN_ATTEMPTS`/`LOGIN_BLOCKED`, `_ask_for_value`, `_describe`). **Not copied:** `STEP 3d`/`STEP
3e` (the TypeSafe `Choice` tool-selection middleware) and the TypeSafe half of `STEP 4` (the model
router) -- these are an optional third-party performance layer (D50/D52), not a safety mechanism,
and are out of scope for a discovery/capture run; the capture notebook uses `MODEL` only, same as
agent.ipynb does with no `TYPESAFE_API_KEY` set. `web_search` is also left out of the capture
agent's tool list, per D48's original reasoning (unchanged): it sends goal/page text to a third
party outside the allowlist, and capture does not need outside facts.

A markdown cell states this plainly as a deliberate, temporary duplication (Phase 9 consolidates
into one shared module) and names the exact six source cells above.

**Additive, capture-only cells (new, small, never touching agent.ipynb's own tools' bodies):**

- `DESCRIBE_JS(ref)` -- one-element descriptor (`role`, `name`, `name_source`, `label`, `text`,
  `tag`, `type`, `submit`, `options`, `container`, `nth`, `name_count`, `label_count`), read from
  the same `data-cua-ref` attributes `OBSERVE_JS` already sets. Never shown to the model.
- `HEADING_JS`/`current_heading()` -- the same "first visible `h1`, else `.title`, else `h2`, else
  page title" rule D49 already specified, used only to fill `event.before/after.heading`.
- `READ_LABELED_JS`/`read_labeled_value(label)` -- the value shown next to a label (the cell after
  it, the input a `<label>` points at, or the next sibling). Used by the new `extract_value` tool.
- **Event capture wrapper**: for every tool in the copied `BROWSER_TOOLS` list plus the two new
  ones below, replace `tool_obj.coroutine` with a wrapper that records `before`/`el`/`args`, calls
  the **original** coroutine unchanged, records `after`/`message`/`status`, and returns the
  original result completely unmodified. This is the literal mechanism for "wrap the relevant
  tools... without changing any tool's existing behavior or return value."
- **`extract_value(ref, label, save_as, value_type, description)`** (new tool, D46) -- reads
  `read_labeled_value(label)`, checks it against `value_matches_type` for the declared
  `value_type`, and returns the new page state. The event stores `label`/`save_as`/`value_type`/
  `description`, never the value itself (D46/D16).
- **`open_path(path)`** (new tool, D47) -- GET-navigate within the allowed host only, same
  deny-word check as `click`, every query value must already be grounded (a declared input value
  or a whole word/number in the goal, reusing `GIVEN["text"]`). Needed because agent.ipynb's tools
  can only click what is already a link; reaching a bad-input page for the probe run otherwise has
  no path.
- **`finish_business_outcome(outcome, proof_text)`** (new tool, D47) -- refuses unless `proof_text`
  literally appears in the current page text; on success records `RESULT` with `outcome`/`proof`
  so `rule_from_probe` can read it, and is a **separate** tool from agent.ipynb's own `finish`
  (never redefines it).

A "how the user tests this" markdown block precedes `BROWSER 1`, naming: the exact cells in order;
a good balance-lookup goal starting logged out (so login is captured); a bad-account goal for the
probe (`finish_business_outcome`); the exact expected print lines at each stage (mirroring the
table style the old recorder's intro used); and which two files should appear under `artifacts/`
afterward.

---

## Offline fixtures and checks (all run by the agent, `uv run python`)

Each fixture is a short hand-built `events` list "shaped like what agent.ipynb's tools actually
return" (i.e. built directly from the literal message prefixes read out of `agent.ipynb`, not
invented text), plus a `spec` dict of declared inputs.

| # | Fixture | Asserts |
|---|---|---|
| 1 | Good balance-lookup, starting logged out | `compile_run` returns a `login_parabank` capability with 2 secret steps and a `get_account_balance`-style task capability with 0 secret steps; both `Capability.model_validate` clean; YAML round-trips |
| 2 | Same, with one dead-end click inserted (a link clicked, then clicked back with nothing in between) | the dead-end pair is in `report["dropped"]`, not in the compiled steps |
| 3 | Two elements sharing a role+name, one captured with a `container` | its `Target.primary` (or `.fallback`) carries a `within` matching the container |
| 4 | An element identifiable only by a duplicated `label` (`label_count=2`, no accessible name) | `derive_target` raises `CompileError` naming the label; the run is never compiled |
| 5 | A typed value equal to a declared input's literal, left un-substituted in one place on purpose | `find_leftovers`/`save_capability` refuses, naming the input and the location, never the value |
| 6 | A `click` event with `approved: True` and one declared `currency` input | the compiled `Click` step has `risk: risky` and a matching `amount_input`; `Capability.risk_level == "risky"` |
| 7 | A probe run ending in `finish_business_outcome` | `rule_from_probe` returns a `business` `OutcomeRule` with an `UPPER_SNAKE` outcome and the probe's literal value cut from the proof text; `compile_run` on the probe's own events (as a task) refuses |
| 8 | A run whose last `click` event has `status: "stop"` (login attempt guard) | `compile_run` refuses immediately, before any cleanup, with a clear message; nothing is written |

Plus the pre-existing helper-level checks carried over unchanged in spirit from D43/D44 (word-
boundary literal matching, `same_value`, `norm_url`).

---

## Tasks

- [ ] T1: this plan, committed.
- [ ] T2: `OFFLINE 1`-`OFFLINE 3` (schema loader, helpers, locator derivation incl. D68 scoping/flag)
      + their checks. Commit.
- [ ] T3: `OFFLINE 4`-`OFFLINE 5` (clean-up incl. top-level STOP/handoff/STUCK/DECLINED refusal,
      login split) + their checks. Commit.
- [ ] T4: `OFFLINE 6`-`OFFLINE 7` (steps/Capability assembly, checkpoint, risk, probe outcome rule,
      leftover check, save) + fixtures 1, 2, 3, 5, 6, 7, 8 above. Commit.
- [ ] T5: fixture 4 (duplicate-label refusal) + a final "ALL OFFLINE CHECKS PASSED" cell. Commit.
- [ ] T6: `BROWSER` cells (verbatim copy + additive capture cells, `extract_value`, `open_path`,
      `finish_business_outcome`) + the how-to-test markdown block. `uv run jupytext --to ipynb`.
      Commit.
- [ ] T7: `DECISIONS.md` (supersede notes on D41-D49, new D70+) and `CLAUDE.md` (Phase 3 line).
      `git status --short`, commit.
- [ ] Stop. Report to the user with exact output lines, `git log --oneline`, and the six agent.ipynb
      source cells the capture half was derived from.

---

## Self-review

- **3.2** (typed I/O, per-element identification with robustness reasoning, checkpoint): every
  derived locator keeps a real `note`; checkpoint always has both signals or the save is refused. ✓
- **3.3** (deterministic replay agrees with what was recorded): every produced `Capability` is
  `Capability.model_validate`-clean and is the exact shape `04_replay_engine.py` already consumes
  — no new engine changes needed. ✓
- **3.4** (safety, never persist secrets): events never carry a secret value, only its name; the
  save guard re-checks the rendered YAML text as a second line of defense. ✓
- **3.6** (escalation): a run containing any human handoff is refused outright rather than silently
  producing a capability with a gap where a person once stood. ✓
- **3.7** (heterogeneity): D68's `label`/`labeled_value` scoping gap is tested for and flagged, not
  quietly assumed away — an honest limit, not a hidden one.
- Not built here, by design: Phase 9 consolidation of the duplicated setup/scanner/tool cells; any
  fix to the `label`/`labeled_value` schema gap itself (D68); a live browser run (the user's job).
