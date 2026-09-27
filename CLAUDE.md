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
  **2026-09-26 fix (3):** a human-entered value that matches no already-declared input is no longer
  kept as a hardcoded literal — `_declare_human_input` auto-declares a new `string` input for it,
  named from the field's own label (never its value, so fields that coincidentally share a
  throwaway discovery value never collapse into one input), and the step's value becomes
  `{{that_name}}`. An agent's own unmatched literal is completely unaffected (still a reported
  constant). `artifacts/pay_bill.yaml` was regenerated again: its 5 human-entered fields
  (address/city/state/zip_code/phone) are now declared inputs, not literals. See DECISIONS.md
  section U (D90).
  **2026-09-27 fix:** BROWSER 12's `create_deep_agent(...)` call was missing its own import
  (`from deepagents import create_deep_agent`, present in `agent.ipynb`'s STEP 4, never copied
  over) — found running the CAPTURE half live end to end for the first time this session. See
  DECISIONS.md D95.

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
  **2026-09-26 fix:** `replay_live()` now runs a pre-flight gate (`gather_missing_inputs`) before
  `run_capability_async` is ever called — any required input missing from the caller's own dict is
  now interactively prompted for (via `input()`, with `.pattern` retry, bounded), instead of the
  whole run dying on a raw `InputValidationError` traceback. `04_replay_engine.py`'s own
  `validate_inputs` is completely unchanged; a no-human production replay still fails fast and
  loudly. See DECISIONS.md D91.
  **2026-09-26 fix (2, Phase 8):** `replay_live()` also takes one new, opt-in `evidence_dir`
  parameter (default `None` = unchanged behavior) that saves a `evidence/replay/` folder via the
  new `save_replay_evidence` helper. See below and DECISIONS.md D92.

## Phase 8: evidence
- `evidence/` — the assignment's own required deliverable (Section 6): a saved artifact + logs from
  a discovery run and a replay run. `evidence/README.md` explains the layout, the five error-demo
  scenarios (D30), and the exact live runs still needed to fill it in — none run yet, by design
  (never run by an agent). `notebooks/evidence_capture.py` — two small, additive, offline-tested
  helpers, `save_discovery_evidence`/`save_replay_evidence`, pure Python, no browser import. See
  DECISIONS.md D92.

## Phase 9: `src/cua/` port, CLI, tests, README, REPORT
- `src/cua/` — a real, importable, pip/uv-installable package: `schema.py` (Section 1/D63-D66
  Capability models), `recorder.py` (COMPILE half only — pure Python, no Playwright import),
  `replay.py` (sync + async engines, D77/D85), `agent.py` (the discovery agent as a
  `DiscoveryAgent` class + `build_agent()` factory, D2-D69), `live.py` (`PlaywrightReplaySurface`,
  `make_escalate`, the D91 pre-flight gate), `cli.py` (`cua discover`/`cua replay`, with the
  recorder's CAPTURE-half event-wrapping glue living here rather than in `cua.recorder`, per this
  phase's own scoping), and a new shared `config.py` deduplicating `BASE`/`SECRETS`/`host_allowed`
  across what used to be three separate notebook copies. `pyproject.toml` gained a
  `[project.scripts] cua = "cua.cli:main"` entry point and `[tool.pytest.ini_options] testpaths =
  ["tests"]` (found necessary live: unscoped pytest discovery picked up a git-ignored
  `notebooks/scratch/*_test.py` file that launches a real browser on import). `tests/` is a real
  pytest suite (143 tests) porting every notebook's offline check, zero API key/browser/network.
  A genuine, pre-existing, unrelated bug was found (not fixed, per this phase's own rule not to
  touch notebook logic): `02_artifact_schema.py`'s own Section 2b checks crash with `IndexError`
  today, since an example artifact they index into was simplified by the later D63-D66 rebuild.
  See DECISIONS.md section W (D93), and `REPORT.md` (the assignment's own 7-heading report) /
  `README.md` (setup + demo path) at the repo root.
