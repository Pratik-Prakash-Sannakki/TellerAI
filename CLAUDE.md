# CLAUDE.md

Computer-use automation take-home (interface.ai). Python + uv. Target: ParaBank.

## Read first
- `DECISIONS.md` — every design decision (D1–D31).
- `docs/superpowers/plans/2026-09-19-roadmap-and-phase1.md` — roadmap + Phase 1 plan.

## How we work
- One phase at a time. No parallel work.
- Notebook first. Production code only in Phase 9.
- **Each phase runs in a fresh sub-agent.** Fan one out per phase.
- Sub-agent writes the notebook. **The user runs it.** Sub-agent never runs it.
- Stop after each notebook. Wait for the user before the next one.
- Notebooks are jupytext `.py` files (`# %%` cells) in `notebooks/`.

## How to talk to the user
- Short. Simple English. No long paragraphs.
- Explain jargon in one line, with an example.
- Ask one question at a time.

## Rules
- Only host allowed: `parabank.parasoft.com`. Fake data only.
- Secrets live in `.env` (git-ignored). Never in the repo, logs, or model context.
- Plain Playwright + our own tools. No Playwright MCP.
- No ParaBank-specific code in agent tools. ParaBank values live in config or ground-truth cells only.
- Login is done by the agent with `type_secret` (model sees the name, never the value). See D32.
- Agent = deep agents (discovery only). Replay = plain code, no LLM.
- Model from `MODEL` env var (`anthropic:claude-sonnet-5`).
- Don't touch the old repo `~/Documents/interface-ai-computer-use`.

## Phase 1 notebooks
1. `01_browser_and_observe.py` — browser, secrets config, numbered screenshot. No LLM.
2. `02_agent_happy_path.py` — tools (incl. `type_secret`) + deep agent, logs in and reads a balance.
3. `03_stress_and_pause.py` — stuck goal, tool misuse, pause/approve/reject, findings.

## Phase 2 notebook
- `02_artifact_schema.py` — artifact schema (Pydantic + YAML), tool contract, replay result contract. Pure Python.
  Rebuilt (simplified) 2026-09-22: locators are one `primary` + one optional `fallback` (not a ranked list);
  `app`/`base`/`overrides`/`routes` cut, `base_url` is now a single field, routes are derived from `navigate`
  steps; `when_to_use` folded into `description`. See DECISIONS.md section O (D63-D66).

## Phase 3 notebook
- `03_recorder.py` — the recorder, rebuilt 2026-09-25 against the current schema (D63-D68) and the
  current `agent.ipynb` (D50-D69). Part A, COMPILE (`OFFLINE` cells): pure Python, `events +
  declared inputs -> Capability`, tested entirely offline with hand-made fixtures shaped from
  agent.ipynb's own tool-result prefixes. Part B, CAPTURE (`BROWSER` cells): copies agent.ipynb's
  current setup/scanner/tools/safety cells verbatim (a deliberate, temporary duplication, Phase 9
  consolidates), wraps each tool to log an event, and adds three small new tools the compiler
  needs (`extract_value`, `open_path`, `finish_business_outcome`). Also carries agent.ipynb's
  TypeSafe tool-selection/model-router middleware (`STEP 3d`/`3e`, the TypeSafe half of `STEP 4`),
  copied verbatim and off by default, with one additive extension (D76) so this notebook's own new
  tools always survive tool-selection. See DECISIONS.md section P (D70-D76); D41-D49 (original
  Phase 3) are marked superseded there.
  **2026-09-26 fix:** a `request_value`/`request_missing_values` handoff (a KNOWN, specific field
  opened for a human) is now recordable — `synthesize_human_entries` turns the field's live value,
  read right after hand-back, into a proper `type_text`/`select_option` event with a reviewer-facing
  `why` note, and `compile_run` only hard-refuses the genuinely unstructured handoffs (`ask_human`,
  a take-over click). See DECISIONS.md section Q (D82-D84) and
  `docs/superpowers/plans/2026-09-26-recorder-human-entry-fix.md`.
  **2026-09-26 fix (2):** a premature, failed risky click (e.g. a "Send Payment" submit that fired
  before every required field was filled) no longer survives compilation as a second point of no
  return — `drop_detours` no longer blanket-excludes risky clicks, and a new
  `drop_dead_end_risky_clicks` drops a risky click proven (same target retried later, no state
  change) to be a dead end, refusing outright rather than guessing when two same-target risky
  clicks both look real. `artifacts/pay_bill.yaml` was regenerated from the fixed compiler. See
  DECISIONS.md section S (D86).

## Phase 4 notebooks
- `04_replay_engine.py` — the replay engine. Loads the Phase 2 v2 schema, resolves primary/fallback
  locators, substitutes `{{input}}`/`{{secret:name}}`, walks a capability's steps with no LLM, and
  gates risky clicks on a configurable auto-approve limit. Pure Python, tested against a hand-built
  `FakeSurface`; no browser, no Playwright import. Also carries an async mirror
  (`AsyncReplaySurface`/`run_capability_async`, D77), added because Playwright is async-only and
  cannot be bridged into a sync call from inside a Jupyter kernel that already runs its own event
  loop. Identical business logic to the sync engine, tested offline the same way (`AsyncFakeSurface`).
- `05_replay_live.py` — wires `run_capability_async` to the REAL browser: a `PlaywrightReplaySurface`
  that wraps agent.ipynb's own numbered scanner and lock/force-bypass mechanism (D78, D81), and a
  real `escalate` implementation wired to agent.ipynb's own Approve/Reject/Take-over decision bar
  (D79). Imports Playwright and needs a real browser + `.env` — never run by an agent, only the
  user runs it; only a syntax check (`ast.parse`) is ever performed on it.
