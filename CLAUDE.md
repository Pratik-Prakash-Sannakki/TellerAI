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
- `README.md` — setup and demo path. `REPORT.md` — design and trade-offs.
- `notebooks/discovery/decisions.md` (Q*) and `notebooks/replay/DECISIONS.md` (R*) — every decision.
- `notebooks/discovery/discovery_architecture.md`, `notebooks/replay/replay_architecture.md`.

## How we work
- One task at a time. No parallel work.
- **The user runs the BROWSER cells.** A sub-agent never launches a browser; it verifies with the
  offline suite (`.venv/bin/python -m pytest -q tests`), which loads notebook cells via `ast`.
- Notebook code is production design: no notebook-only shortcuts. Only test fixtures are test-only.
- Notebooks are jupytext pairs: the `.py` (`# %%` cells) is the source; re-sync the `.ipynb` with
  `.venv/bin/jupytext --to ipynb --update <file>.py` after editing.

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
- Login is done by the agent with `type_secret` (model sees the name, never the value). 
- Agent = deep agents (discovery only). Replay = plain code, no LLM.
- Every LLM call goes through `cua.models.make_chat_model` (Iliad gateway; see `.env.example`).
- Don't touch the old repo `~/Documents/interface-ai-computer-use`.

## The system (pure visual)
- `notebooks/discovery/` — `discovery.py`/`.ipynb`: a deep agent learns a task from screenshots
  (OCR, site lock, control tab, send gates, take-over) and writes a capability:
  `artifacts/visual/<name>.yaml` + `crops/<name>/s<i>.png`. Also `decisions.md`, `PLAN.md`.
- `notebooks/replay/` — `replay.py`/`.ipynb`: runs a capability with plain code, no LLM
  (rungs: table cell / OCR text / anchor / template), same gates. Also `DECISIONS.md`, `PLAN.md`.
- `extensions/handback/` — Chrome toolbar extension for handing control back after a take-over.
- `src/cua/` — only `config.py` (site, secret names, host gate, gateway settings) and
  `models.py` (chat-model factory). Imported by the notebooks.
- `tests/discovery/`, `tests/replay/` — offline suites; `tests/test_models.py` — model factory.
- `evidence/` — masked discovery/replay run folders (layout in `evidence/README.md`).
- The earlier DOM-based stack (numbered notebooks, `cua discover`/`cua replay`, D1-D102,
  `PHASE*.md`) was removed on 2026-10-01; it is in git history before that date.

## graphify

This project has a knowledge graph at graphify-out/ with god nodes, community structure, and cross-file relationships.

Rules:
- For codebase questions, first run `graphify query "<question>"` when graphify-out/graph.json exists. Use `graphify path "<A>" "<B>"` for relationships and `graphify explain "<concept>"` for focused concepts. These return a scoped subgraph, usually much smaller than GRAPH_REPORT.md or raw grep output.
- If graphify-out/wiki/index.md exists, use it for broad navigation instead of raw source browsing.
- Read graphify-out/GRAPH_REPORT.md only for broad architecture review or when query/path/explain do not surface enough context.
- After modifying code, run `graphify update .` to keep the graph current (AST-only, no API cost).
