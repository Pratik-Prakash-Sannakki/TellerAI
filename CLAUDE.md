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
  needs (`extract_value`, `open_path`, `finish_business_outcome`). See DECISIONS.md section P
  (D70-D75); D41-D49 (original Phase 3) are marked superseded there.

## Phase 4 notebook
- `04_replay_engine.py` — the replay engine. Loads the Phase 2 v2 schema, resolves primary/fallback
  locators, substitutes `{{input}}`/`{{secret:name}}`, walks a capability's steps with no LLM, and
  gates risky clicks on a configurable auto-approve limit. Pure Python, tested against a hand-built
  `FakeSurface`; no browser, no Playwright import. The real `ReplaySurface` (Phase 9) wraps
  agent.ipynb's own `PlaywrightSurface` and `human_takeover`/decision-bar mechanism.
