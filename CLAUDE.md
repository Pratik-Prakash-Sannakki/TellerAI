# CLAUDE.md

Computer-use automation take-home (interface.ai). Python + uv. Target: ParaBank.

## Every task: the 4-step workflow (standing rule, user-mandated)
Follow these in order for every request, no exceptions:
1. **Query the graph first.** Your first instinct is `graphify query "<question>"` (plus
   `graphify explain "<node>"` / `graphify path "<A>" "<B>"`) to learn where things are.
2. **Then semantic search.** Use your own search (Grep/Glob/LSP/Explore) to find the exact code.
3. **Implement it.**
4. **Update the graph after implementing.** Run `graphify update .` so the graph stays current.

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

## Role: orchestrator (standing rule)
- Fan out a sub-agent for every user request. Discovery queries always go to a sub-agent.
- Main thread plans, delegates, and relays. Sub-agents do the digging.
- Every sub-agent starts from graphify (`graphify query` / `path` / `explain`) for past work.
  Raw file browsing comes only after the graph runs dry.
- Every sub-agent that builds anything uses superpowers skills (via the Skill tool), in this order:
  - Design not settled yet → `superpowers:brainstorming`.
  - Design settled → `superpowers:writing-plans`, then stop for the user's review.
  - Plan approved → `superpowers:executing-plans` or `superpowers:subagent-driven-development`,
    with `superpowers:test-driven-development` for code.
  - Before saying "done" → `superpowers:verification-before-completion`.
- Put this rule in every build sub-agent's prompt, by name.

## How to talk to the user
- Crisp. Bullets over paragraphs. Short sentences, plain English.
- Summarise what was done. Leave out implementation walk-throughs.
- The user already knows HTML, CSS, scraping, and this project's own code. Use those terms freely.
- Explain only truly unfamiliar terms: one line plus an example, or a short note at the end.
  If a term adds nothing, drop it.
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
  **2026-09-27 fix (D101):** the D89/D97/D100 "labeled_value resolves to a table HEADER, not a
  value" bug, made general. `READ_LABELED_JS` (BROWSER 8) now also reports `label_header`/
  `value_header` — purely structural (`<th>`/`role=columnheader`/`<thead>` ancestor, never any
  cell's own text) — and `compile_run` (`_extract_target`, OFFLINE 3) refuses a `labeled_value`
  step whose captured resolution is itself a header cell. Known, stated limit: `src/cua/cli.py`'s
  own capture path (what `cua discover` actually uses) is not yet ported to compute these flags —
  see DECISIONS.md D101 for the exact follow-up needed.
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
  **2026-09-27 fix:** the first-ever real `cua discover` run crashed immediately —
  `build_agent()` constructed `DiscoveryAgent(page, goal_text=goal_text, ...)`, but the class's
  own field is named `given_text`. One-line fix; never caught by the 143-test suite since
  `build_agent` (needs a real browser) is correctly untested offline. See DECISIONS.md D96, which
  also flags a separate, unfixed UX gap: a discovery goal that doesn't explicitly say "use
  extract_value" compiles into a syntactically valid but practically useless capability.
  **2026-09-27 fix (2):** `cua replay` gained a `--login <path>` flag — each invocation otherwise
  launches its own fresh, logged-out browser, so a capability with no login step of its own (D45's
  login split — nearly every real one) had no way to get an already-logged-in session from the CLI
  at all. `--login` replays that capability first, in the SAME browser/session, before the main
  one. Also fixed, again: a freshly-discovered `get_account_balance`-shaped capability hit D89's
  exact same "Balance" header trap a second time (repointed to `Total`); the underlying pattern —
  nothing validates a `labeled_value` extract's live type at compile time — is still open. See
  DECISIONS.md D97.
  **2026-09-27 fix (3):** `cli.py`'s own `extract_value`/`open_path` were missing the same
  `one_at_a_time` lock every one of `agent.py`'s own base tools already carries — restored, locking
  on the identical `agent._act_lock`. See DECISIONS.md D98 (part of an ongoing investigation into a
  separate, still-open `extract_value`-called-repeatedly bug; this fix did not close it).
  **2026-09-27 fix (4):** the real cause of that bug — `03_recorder.py`'s BROWSER 11/12 TypeSafe
  tool-router/model-router middleware (D50, D52, D76) was never ported to `src/cua/` at all. `cli.py`'s
  `_run_discover` called `build_langchain_agent(tools, system_prompt=RECORDER_SYSTEM_PROMPT)` with no
  `middleware` argument, so `cua discover` ran with neither layer, on every invocation, regardless of
  `TYPESAFE_API_KEY`. `agent.py` gained `job_tool_names`/`confidence_gate`/`NEVER_HIDE`/
  `JOB_EXTRA_TOOLS`/`JOB_CRITERIA` (ported verbatim from `03_recorder.py`'s OFFLINE 13b) and a new
  `build_typesafe_middleware()` that reproduces BROWSER 12's construction exactly; `cli.py` now calls
  it and passes the result through. Still off by default (unchanged behavior with no key). See
  DECISIONS.md D99, including what this fix's offline tests do and do not prove.
  **2026-09-27 fix (5, D101):** `src/cua/recorder.py`'s `_extract_target`/`build_steps` now refuse a
  `labeled_value` extract step whose captured event says its resolution is structurally a table/grid
  header cell (`value_header`, a new optional event field) — the general form of D89/D97/D100's
  recurring "Balance" header trap. Kept in sync with `03_recorder.py`'s COMPILE half, as this port
  always does; the CAPTURE side that would need to populate `value_header` for real `cua discover`
  runs lives in `cli.py`/`agent.py`, both out of this fix's scope — see DECISIONS.md D101 for the
  exact follow-up still needed there.
  **2026-09-27 fix (6, D102):** D101's own follow-up, closed. `src/cua/agent.py`'s `READ_LABELED_JS`
  now carries the identical `label_header`/`value_header` structural fields as `03_recorder.py`'s
  copy (byte-identical, tested), and `cli.py`'s `_wrap_extract_value` threads both onto the real
  `cua discover` capture event; `_new_tools`'s own `extract_value` tool also gained D101's bonus
  live refusal. `cua discover` is now actually protected against the D89/D97/D100 header trap, not
  just `03_recorder.py` captures. See DECISIONS.md D102.

## graphify

This project has a knowledge graph at graphify-out/ with god nodes, community structure, and cross-file relationships.

Rules:
- For codebase questions, first run `graphify query "<question>"` when graphify-out/graph.json exists. Use `graphify path "<A>" "<B>"` for relationships and `graphify explain "<concept>"` for focused concepts. These return a scoped subgraph, usually much smaller than GRAPH_REPORT.md or raw grep output.
- If graphify-out/wiki/index.md exists, use it for broad navigation instead of raw source browsing.
- Read graphify-out/GRAPH_REPORT.md only for broad architecture review or when query/path/explain do not surface enough context.
- After modifying code, run `graphify update .` to keep the graph current (AST-only, no API cost).
