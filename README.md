# interface.ai take-home: computer-use automation

An AI agent discovers how to do a task on a real banking web app (ParaBank), the run is compiled
into a typed, reviewable **capability** (a YAML recipe), and a separate, deterministic **replay
engine** — no LLM in the loop — runs that recipe again later, safely and repeatably.

```
discover (LLM + browser) -> compile (pure Python) -> capability.yaml -> replay (no LLM, real browser)
```

For the full design story — every decision, every trade-off, every bug found and fixed against
the real site — see `REPORT.md` and `DECISIONS.md`. `PHASE1.md`–`PHASE5.md` are the plain-English,
phase-by-phase write-ups this project was built in (notebooks first, package second). This README
is only setup + how to run things.

## Setup

Requires Python 3.12+ and [`uv`](https://docs.astral.sh/uv/).

```bash
git clone <this repo>
cd interface-ai-cua-v2
uv sync                       # installs src/cua as an editable package + all dependencies
cp .env.example .env          # fill in real values only for the live demo (see below)
uv run playwright install chromium   # only needed for the live demo, not for tests
```

`.env` (git-ignored) holds:

| Var | Needed for | Notes |
|---|---|---|
| `ANTHROPIC_API_KEY` | `cua discover`, notebooks 1–3 | discovery uses a real LLM (D4) |
| `MODEL` | optional | defaults to `anthropic:claude-sonnet-5` |
| `PARABANK_USERNAME` / `PARABANK_PASSWORD` | `cua discover`, `cua replay` | a ParaBank test user (fake data only, see CLAUDE.md) |
| `TYPESAFE_API_KEY` | optional | an experimental model/tool router (D50/D52), off unless set |

Nothing above is needed to run the test suite.

## Demo path 1: run the test suite (no key, no browser, no network)

```bash
uv run pytest
```

Expect something like:

```
143 passed in 0.24s
```

This is the whole load-bearing logic — the artifact schema, the recorder's compile pipeline, and
both replay engines — exercised against hand-built fixtures and the two real example artifacts in
`artifacts/examples/`. Nothing here launches a browser or calls an LLM (`src/cua/recorder.py` and
`src/cua/replay.py` have no `import playwright` anywhere in them; `pyproject.toml` scopes pytest's
own discovery to `tests/` so a fresh clone can't accidentally pick up anything else).

## Demo path 2: the notebooks (where all of this was actually designed and live-tested)

`src/cua/` is a Phase 9 **port** of five notebooks in `notebooks/`, not a rewrite — the notebooks
remain the source of truth for the live-tested logic and are unmodified by this port:

| Notebook | What it is | Needs |
|---|---|---|
| `agent.ipynb` | The discovery agent (deep agents + Playwright), live-tested extensively | API key, browser |
| `02_artifact_schema.py` | The capability schema (Pydantic + YAML) | nothing — `uv run python notebooks/02_artifact_schema.py` |
| `03_recorder.py` | Turns a real run into a capability YAML (COMPILE half is pure; CAPTURE half needs a browser) | COMPILE: nothing. CAPTURE: API key, browser |
| `04_replay_engine.py` | The replay engine (sync + async), tested against a fake browser | nothing — `uv run python notebooks/04_replay_engine.py` |
| `05_replay_live.py` | Wires replay to a real browser + a real human-approval bar | browser, `.env` (no API key) |

Run the two pure ones directly to see their own "ALL CHECKS PASSED" output (`04_replay_engine.py`
does; `02_artifact_schema.py` currently does not — see the note below). The other three are
notebooks in the literal sense: meant to be stepped through cell by cell in Jupyter, not run
top-to-bottom as a script, since several cells open a real, visible browser window and wait for a
human.

**One honestly-stated finding from this port:** `notebooks/02_artifact_schema.py`'s own offline
checks currently crash with `IndexError` (`uv run python notebooks/02_artifact_schema.py`) — two
of its Section 2b cells assume `artifacts/examples/get_account_balance.yaml` still has 3
`outcome_rules`, which was true when that cell was written but no longer is, after the example was
simplified in the D63–D66 schema rebuild. This is a real, pre-existing bug, not introduced by this
port (`tests/test_schema.py` tests the identical two validation rules against a fixture built to
have the shape they need, so nothing in the ported package is affected). See `REPORT.md`'s Cuts
section.

## Demo path 3: a real discovery + replay run (needs an API key and ParaBank test credentials)

```bash
# 1. Discover a capability against the real site (opens a visible browser).
uv run cua discover "Log in and read the balance of account 14232. Use extract_value to save it as 'balance'." \
  --name get_account_balance --input account_id=14232

# 2. Replay the saved capability, no LLM this time.
uv run cua replay artifacts/get_account_balance.yaml --input account_id=14232
```

`cua discover` needs `ANTHROPIC_API_KEY` and a real browser: it runs the actual discovery agent
(`src/cua/agent.py`), wraps every tool call into an event (mirroring `03_recorder.py`'s CAPTURE
half), and compiles the recording via `src/cua/recorder.py`'s `compile_run`. `cua replay` needs
**no API key** — replay has no LLM in the loop (D6); it only needs Playwright and `.env` for
secrets (D32). Both need `uv run playwright install chromium` first and a real, reachable
`parabank.parasoft.com`.

The CLI's `--input key=value` flags are a deliberate simplification over the notebooks' own
richer, hand-written `spec` dict (exact type/pattern/description per input) — see `REPORT.md`'s
Cuts section for what this trades away.

For a full recorded run (a saved artifact + logs from both a discovery run and a replay run,
including one that hits an error), see `/evidence/` — built by a separate, concurrent piece of
this project's own work, not part of this package.

## Repo layout

```
src/cua/            the ported package (this phase's own deliverable)
  schema.py          capability artifact schema (Pydantic + YAML), tool contract, ReplayResult
  recorder.py        COMPILE half: events + declared inputs -> Capability (pure Python)
  replay.py          the replay engine, sync + async (pure Python, no Playwright import)
  agent.py           the discovery agent: deep agents + Playwright + safety/lock/takeover
  live.py            wires the async replay engine to a real Playwright browser
  cli.py             `cua discover` / `cua replay`
tests/               pytest suite calling into src/cua/ (zero key, zero browser, zero network)
notebooks/           the original, unmodified notebooks this package is ported from
artifacts/           capability YAML files (examples/, hand-written; top-level, real captures)
docs/superpowers/    planning docs from earlier phases
DECISIONS.md         every design decision (D1-D9x), the primary source for REPORT.md
PHASE1.md..PHASE5.md plain-English write-ups of each phase
REPORT.md            the assignment's required 7-heading report
```

## Notes on scope

- Only host ever allowed: `parabank.parasoft.com`. Fake data only, respecting the target site
  (CLAUDE.md, Section 9 of the assignment brief).
- Secrets live in `.env` only, never in the repo, logs, or model context (D32).
- `evidence/` is owned by a separate, concurrent piece of this project's work and is intentionally
  not touched or duplicated here.
