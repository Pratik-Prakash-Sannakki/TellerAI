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
