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
# # Visual discovery
# The agent sees only a screenshot with numbered OCR boxes. A human answers in a control window.
# A thin demo over the `cua` package: the code lives in `src/cua/discovery/` (read its
# `README.md`); the design notes stay beside this notebook (`discovery_architecture.md`,
# `decisions.md`, `PLAN.md`). `# OFFLINE` cells are pure; `# BROWSER` cells open a real browser
# and are run only by the user.

# %% [markdown]
# ## Setup
# Imports and the site profile (`configs/parabank.yaml`); secrets come from `.env`, by name only.
# Then one visible Chromium at a fixed page size (Q10) plus the "Agent control" tab, the send
# guard, and the deep agent with the model from the Iliad gateway. Re-run safe: an open browser
# is reused.

# %%
# OFFLINE
from pathlib import Path

from cua.browser import check_viewport, open_session
from cua.config import BrowserConfig, DiscoveryConfig, load_site
from cua.discovery.agent.build import build_agent
from cua.discovery.evidence import save_evidence
from cua.discovery.goal import run_goal
from cua.discovery.recorder import build_capability, crops_for, describe, save_artifact
from cua.discovery.wiring import attach
from cua.llm import make_chat_model
from cua.replay.wiring import secret_values

ROOT = next(p for p in (Path.cwd(), *Path.cwd().parents) if (p / "pyproject.toml").exists())
site = load_site("parabank")
print("base:", site.base_url, "| secrets set:", sorted(n for n, v in secret_values(site).items() if v))

# %%
# BROWSER
session = await open_session(site, BrowserConfig(), existing=globals().get("session"),
                             profile_prefix="cua-discovery-")
await session.page.goto(site.start_url)
await check_viewport(session)
ctx = await attach(session, DiscoveryConfig(), secret_values(site))
model = make_chat_model("sonnet")
agent = build_agent(ctx, model)
print("opened:", session.page.url, "| page", session.cfg.viewport, "| model:", model.model)

# %% [markdown]
# ## Run
# Log in and read a balance. Approve clicks in the control tab when asked.

# %%
# BROWSER
answer = await run_goal(ctx, agent, "Log in, open Accounts Overview, and save the first account's "
                        "balance with extract_value as 'first_balance'. Then log out.")
print(answer)
print("saved:", ctx.run.saved, "| events:", len(ctx.run.log))

# %% [markdown]
# ## Save artifact
# The event log becomes a capability YAML + crops that replay loads as is (R10-R16), under the
# top-level `artifacts/` folder. Steps come from the log; only the name and descriptions come from
# the model. Labels, points, crops and input names only: no typed, selected or secret value.

# %%
# BROWSER
meta = await describe(ctx.run.goal, ctx.run.log, model)
cap = build_capability(ctx.run.log, meta)
print(path := save_artifact(cap, crops_for(ctx.run.log, cap), ROOT / "artifacts"))

# %% [markdown]
# ## Evidence
# One folder per run under `evidence/discovery/` (spec 6.3, 3.6): the goal, every event, the
# take-over screenshots, the step crops, the answer, a summary and `run.json`. Every run value and
# secret is masked: `***` in text, a black box over its OCR text in a PNG.

# %%
# BROWSER
print(save_evidence(ctx, ROOT / "evidence" / "discovery", capability=globals().get("path"),
                    model=model.model))
