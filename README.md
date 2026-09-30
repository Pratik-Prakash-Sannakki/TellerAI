# interface.ai take-home: computer-use automation (pure visual)

An AI agent learns a banking task on a real web app (ParaBank) by looking at screenshots and
using the mouse and keyboard. At the end of the run it writes a **capability**: a YAML recipe
plus a few small cropped images. A separate **replay** notebook runs that recipe again with
plain code and no LLM.

```
discovery.ipynb (LLM + browser)  ->  capability.yaml + crops/  ->  replay.ipynb (no LLM, browser)
```

Design and trade-offs: `REPORT.md`. Every decision: `notebooks/discovery/decisions.md`
(Q7-Q21) and `notebooks/replay/DECISIONS.md` (R1-R18). This README covers setup and running.

> The older DOM-based stack (`src/cua/cli.py`, `cua discover` / `cua replay`, the numbered
> notebooks `01_`-`05_`, `DECISIONS.md` D1-D102, `PHASE1-5.md`) is superseded by the two
> notebooks below. It is still in the repo. Only `src/cua/models.py` (the model factory),
> `src/cua/config.py` and `cua.recorder.value_matches_type` are used by the new notebooks.

## How to set up and run it

Needs Python 3.12+, [`uv`](https://docs.astral.sh/uv/), and a desktop with a display (the
browser runs visibly). Built and tested on macOS.

```bash
uv sync --group discovery                # + RapidOCR, onnxruntime, numpy (dev group comes by default)
uv run playwright install chromium
uv run python -m ipykernel install --user --name banker-agent --display-name "BankerAgent (.venv)"
cp .env.example .env                     # then fill in the keys below
```

`.env` (git-ignored):

| Key | Needed for | Notes |
|---|---|---|
| `PARABANK_USERNAME` / `PARABANK_PASSWORD` | discovery and replay | a ParaBank demo user (fake data only). Typed by `type_secret`; the model sees the name, never the value |
| `ILIAD_API_KEY` | discovery only | every LLM call goes through the Iliad gateway (`src/cua/models.py`). If unset, falls back to `ANTHROPIC_API_KEY` |
| `ILIAD_BASE_URL`, `ILIAD_SONNET_MODEL`, `SSL_CERT_FILE` | optional | gateway overrides / corporate CA bundle |

Replay needs no LLM key at all.

### Running without live services

The offline tests need no key, no browser and no network. They load the notebooks' own cells
(via `ast`) and drive them against fake pages:

```bash
.venv/bin/python -m pytest -q tests/discovery tests/replay     # 132 passed (2026-09-29)
```

They cover the send gates and mismatch check, the "nothing stored" rule, evidence masking,
artifact save, the rungs, replay's step engine, take-over evidence, and a round trip
(discovery's `build_capability` -> `save_artifact` -> replay's `load_capability`, unchanged).

`.venv/bin/python -m pytest -q tests` also runs the old stack's tests. Today that gives
`310 passed, 7 errors`: the 7 errors are in `tests/test_live.py`, which reads
`artifacts/pay_bill.yaml`, a file removed in this working tree.

## Demo path

Both notebooks are jupytext pairs: the `.py` is the source, the `.ipynb` is what you open.

### 1. Discover (agent on a goal)

1. Open `notebooks/discovery/discovery.ipynb` in Jupyter / VS Code, kernel **"BankerAgent (.venv)"**.
2. **Run all.** A Chromium window opens at a fixed 1280x800 page with two tabs: the ParaBank
   site tab and an "Agent control" tab. The Browser cell refuses to go on if the screenshot is
   not exactly 1280x800.
3. The `## Run` section has three cells. Run them in order:
   - `answer = await run_goal("...")` - the agent works. Edit the goal string to pick a task,
     e.g. *"Log in, open Accounts Overview, and save the first account's balance with
     extract_value as 'first_balance'. Then log out."* When the agent needs you, the control tab
     comes to the front: answer a question, fill a form, or approve/edit a send at the two
     gates. If you take over, the site unlocks for you; click **Done** in the control tab to
     hand back.
   - `save_artifact(build_capability(...), crops_for(...))` - writes
     `artifacts/visual/<name>.yaml` + `crops/<name>/s<i>.png` (relative to the kernel's working
     directory, normally `notebooks/discovery/`). It refuses a run that had a take-over.
   - `save_evidence(capability=path)` - writes a masked `evidence/discovery/<UTC>-<goal>/` folder.

Saved examples from earlier runs: `notebooks/discovery/artifacts/visual/` (`transfer_funds.yaml`,
`pay_bill_to_payee.yaml`, ...).

### 2. Replay the artifact (no LLM)

1. Open `notebooks/replay/replay.ipynb` (same kernel).
2. In the `## Run` cell set `cap_path` to the YAML from step 1, e.g.
   `ROOT / "notebooks" / "discovery" / "artifacts" / "visual" / "transfer_funds.yaml"`.
3. **Run all.** Replay loads and checks the YAML, opens `base_url`, then shows **one form** in
   the control tab asking every input the capability needs (e.g. amount, from/to account). It
   walks the steps; any send still stops at Gate 1 and Gate 2 for you.
4. The cell prints `result.summary` (e.g. `SUCCESS`, or `SUCCESS (human intervened at step 5)`),
   the outputs, the drift log (which rung found each step), and the path of the masked
   `evidence/replay/<UTC>-<name>/` folder.

Note: `replay(path)` takes no inputs from code today; they come from the form. Passing inputs
from a calling agent is in progress (see `REPORT.md`, Determinism).

## Repo layout (new system)

```
notebooks/discovery/   discovery.py/.ipynb, decisions.md, discovery_architecture.md, artifacts/visual/
notebooks/replay/      replay.py/.ipynb, DECISIONS.md, replay_architecture.md, PLAN.md
tests/discovery/       offline tests for discovery's cells
tests/replay/          offline tests for replay's cells, incl. the discovery -> replay round trip
src/cua/models.py      the one place a chat model is built (Iliad gateway)
evidence/              discovery/ and replay/ run folders (older folders there are from the DOM stack)
```

## Rules this code keeps

- Only host allowed: `parabank.parasoft.com`. Fake data only.
- Secrets live in `.env` only: never in the YAML (names only), the logs, or the model's context.
- No value a human typed or gave is stored. Evidence is masked (`***` in text, black boxes in PNGs).
