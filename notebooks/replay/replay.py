# ---
# jupyter:
#   jupytext:
#     formats: ipynb,py:percent
#     text_representation:
#       extension: .py
#       format_name: percent
#       format_version: '1.3'
#       jupytext_version: 1.19.5
#   kernelspec:
#     display_name: BankerAgent (.venv)
#     language: python
#     name: banker-agent
# ---

# %% [markdown]
# # Visual replay
# Runs a capability saved by discovery with plain code, no LLM. Every send meets both human gates.
# A thin demo over the `cua` package: the code lives in `src/cua/replay/` (read its `README.md`);
# the design notes stay beside this notebook (`replay_architecture.md`, `DECISIONS.md`,
# `PLAN.md`). `# OFFLINE` cells are pure; `# BROWSER` cells open a real browser and are run only
# by the user.

# %% [markdown]
# ## Setup
# Imports and the site profile (`configs/parabank.yaml`); secrets come from `.env`, by name only.
# No model: replay only follows the saved steps. Then one visible Chromium at the fixed page size
# plus the "Agent control" tab, and the send guard. Re-run safe: an open browser is reused.

# %%
# OFFLINE
from pathlib import Path

from cua.browser import open_session
from cua.config import BrowserConfig, ReplayConfig, load_site
from cua.replay.engine import replay
from cua.replay.evidence import save_evidence
from cua.replay.wiring import attach, secret_values

ROOT = next(p for p in (Path.cwd(), *Path.cwd().parents) if (p / "pyproject.toml").exists())
site = load_site("parabank")
print("secrets set:", sorted(n for n, v in secret_values(site).items() if v))

# %%
# BROWSER
session = await open_session(site, BrowserConfig(), existing=globals().get("session"),
                             profile_prefix="cua-replay-")
ctx = await attach(session, site, ReplayConfig())
print("browser open | page", session.cfg.viewport)

# %% [markdown]
# ## Run
# Replay a saved capability. Outputs go to the caller only; the drift log holds rungs, never values.

# %%
# BROWSER
cap_path = ROOT / "artifacts" / "get_all_account_balances.yaml"
result = await replay(ctx, cap_path, inputs={})   # e.g. {"amount": "10"}; the rest is asked
print("capability:", cap_path)
print("status:", result.summary, result.reason, f"| recoveries: {result.recoveries}",
      f"| cleanup: {result.cleanup or 'none'}")
print(result.outputs_line)
for row in result.drift:
    print({k: v for k, v in row.items() if k != "shots"})

# %% [markdown]
# ## Evidence
# One folder per run under `evidence/replay/` (spec 3.5, 6.3): summary, drift, failure, the final
# screen, take-over shots, a copy of the capability and `run.json`. Every value the human gave and
# every secret is masked: `***` in text, a black box over its OCR text in a PNG.

# %%
# BROWSER
print(save_evidence(ctx, result, cap_path, ROOT / "evidence" / "replay"))
