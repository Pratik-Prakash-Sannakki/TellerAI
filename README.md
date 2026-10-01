# interface.ai take-home: computer-use automation (pure visual)

An AI agent learns a banking task on a real web app (ParaBank) by looking at screenshots and
using the mouse and keyboard. At the end of the run it writes a **capability**: a YAML recipe
plus a few small cropped images. A separate **replay** engine runs that recipe again with plain
code and no LLM.

```
discover (agent + browser)  ->  artifacts/<name>.yaml + crops/  ->  replay (no LLM, browser)
```

Design and trade-offs: `REPORT.md`. Every decision: `notebooks/discovery/decisions.md` (Q1-Q21)
and `notebooks/replay/DECISIONS.md` (R1-R21). This README covers setup and running.

## How to set up and run it

Needs Python 3.12+, [`uv`](https://docs.astral.sh/uv/), and a desktop with a display (the
browser runs visibly). Built and tested on macOS.

```bash
uv sync                                  # add --extra typesafe for the optional tool/model router
uv run playwright install chromium
uv run python -m ipykernel install --user --name banker-agent --display-name "BankerAgent (.venv)"
cp .env.example .env                     # then fill in the keys below
```

`.env` (git-ignored):

| Key | Needed for | Notes |
|---|---|---|
| `PARABANK_USERNAME` / `PARABANK_PASSWORD` | discovery and replay | a ParaBank demo user (fake data only). Typed by `type_secret`; the model sees the name, never the value |
| `ILIAD_API_KEY` | discovery only | every LLM call goes through the Iliad gateway (`src/cua/llm.py`). If unset, falls back to `ANTHROPIC_API_KEY` |
| `ILIAD_BASE_URL`, `ILIAD_SONNET_MODEL`, `ILIAD_HAIKU_MODEL`, `SSL_CERT_FILE` | optional | gateway overrides / corporate CA bundle |
| `TYPESAFE_API_KEY` | optional | turns on TypeSafe tool-selection + model routing for discovery (off by default) |

Replay needs no LLM key at all.

### Running without live services

The test suite needs no key, no browser and no network:

```bash
.venv/bin/python -m pytest -q tests     # 720 passed (2026-10-01)
```

It covers the send gates and mismatch check, the "nothing stored" rule, evidence masking,
artifact save/load, the targeting rungs, replay's step engine, take-over evidence, the import
rules between packages, the `cua` CLI (argument parsing + wiring, monkeypatched), and a round
trip (discovery's `build_capability` -> `save_artifact` -> replay's `load_capability`,
unchanged). `tests/unit/test_llm.py` covers the model factory.

## Demo path

Two ways to run the same system: thin notebooks (to watch each step) or the `cua` CLI (one
command).

### Notebooks

Both notebooks are jupytext pairs: the `.py` is the source, the `.ipynb` is what you open. They
are thin demos over the `cua` package — the real logic lives in `src/cua/`.

**1. Discover (agent on a goal).**

1. Open `notebooks/discovery/discovery.ipynb`, kernel **"BankerAgent (.venv)"**.
2. **Run all.** A Chromium window opens at a fixed 1280x800 page with two tabs: the ParaBank
   site tab and an "Agent control" tab.
3. The `## Run` cell runs the agent on a goal, e.g. *"Log in, open Accounts Overview, and save
   the first account's balance with extract_value as 'first_balance'. Then log out."* When the
   agent needs you, the control tab comes to the front: answer a question, fill a form, or
   approve/edit a send at the two gates. If you take over, the site unlocks for you; click
   **Done** in the control tab to hand back.
4. `## Save artifact` writes `artifacts/<name>.yaml` + `artifacts/crops/<name>/s<i>.png`. It
   refuses a run that had a take-over.
5. `## Evidence` writes a masked `evidence/discovery/<UTC>-<goal>/` folder.

Saved examples from earlier runs: `artifacts/` (`transfer_money.yaml`, `pay_bill.yaml`,
`pay_bill_to_payee.yaml`, `get_all_account_balances.yaml`,
`get_para_bank_phone_number.yaml`).

**2. Replay the artifact (no LLM).**

1. Open `notebooks/replay/replay.ipynb` (same kernel).
2. The `## Run` cell points at a YAML, e.g. `ROOT / "artifacts" / "get_all_account_balances.yaml"`.
3. **Run all.** Replay loads and checks the YAML, opens `base_url`, then shows **one form** in
   the control tab asking every input the capability needs. It walks the steps; any send still
   stops at Gate 1 and Gate 2 for you.
4. The cell prints `result.summary` (e.g. `SUCCESS`), the outputs, the drift log (which rung
   found each step), and the path of the masked `evidence/replay/<UTC>-<name>/` folder.

### CLI

The same two flows as one command each, once `uv sync` installs `cua` as a script:

```bash
.venv/bin/cua discover "Log in and read the first account's balance" --out artifacts
.venv/bin/cua replay artifacts/get_all_account_balances.yaml --evidence
.venv/bin/cua replay artifacts/transfer_money.yaml \
  --input amount=10 --input from_account=12345 --input to_account=67890
```

`--site` picks a profile from `configs/` (defaults to the only one there: `parabank`).
`cua replay` exits 1 unless the result is `SUCCESS`.

## Repo layout

```
src/cua/               the package (see src/cua/README.md for read order and import rules)
  config.py            SiteProfile (from configs/<site>.yaml), BrowserConfig/DiscoveryConfig/
                       ReplayConfig, resolve_secret/secret_values, host_allowed, Iliad gateway env
  llm.py               make_chat_model
  schema/              the contract: Capability, value types, results, events
  vision/              pixels -> text: screenshots, OCR, canvas math, crops, table reader
  browser/             Playwright session, site lock, input, native dropdowns
  safety/              SendGuard (Gate 1/2), mismatch check, redaction, host allow-list
  handoff/             the "Agent control" tab, hand-back extension calls, take-over loop
  discovery/           the agent: tools, prompt/middleware, recorder (events -> Capability), evidence
  replay/              the engine: loader, locate (rungs), steps, run, rescue, evidence
  cli.py               `cua discover` / `cua replay`
configs/parabank.yaml  start_url, allowed hosts, secret env names, deny/login words, outcomes.
                       The ONLY place ParaBank lives.
artifacts/<name>.yaml  saved capabilities; artifacts/crops/<name>/ their template crops
notebooks/discovery/   discovery.py/.ipynb (thin demo), decisions.md, discovery_architecture.md
notebooks/replay/      replay.py/.ipynb (thin demo), DECISIONS.md, replay_architecture.md
extensions/handback/   Chrome toolbar extension for handing control back
tests/
  unit/                mirrors src/cua/; tests/fakes.py holds shared fakes
  integration/         notebook parity checks, discovery -> replay round trip, saved artifacts
evidence/              discovery/ and replay/ run folders (see evidence/README.md)
```

## Rules this code keeps

- Only host allowed: `parabank.parasoft.com`. Fake data only.
- Secrets live in `.env` only: never in the YAML (names only), the logs, or the model's context.
- No value a human typed or gave is stored. Evidence is masked (`***` in text, black boxes in PNGs).
