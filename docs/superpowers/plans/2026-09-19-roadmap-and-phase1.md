# Computer-Use Automation System — Roadmap + Phase 1 (Deep Agent + Playwright) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.
>
> **Working style set by the user:** strictly sequential, one phase at a time, no parallel work. Everything is built in a **notebook first**, then ported to production code in the last phase. Stop at the end of every task and wait for the user before starting the next one.

**Goal:** Build the interface.ai computer-use system in small, controllable phases. This document holds the roadmap for all phases and the full step-by-step plan for **Phase 1 only**: a deep agent that drives a real ParaBank browser session and completes a goal.

**Architecture:** A deep agent (Claude Sonnet 5) is given our own Playwright tools. Each tool returns a screenshot with numbered red boxes plus a text list of the numbered elements. The agent picks elements by number; our code resolves the number to a real element. The browser is owned by our process (a notebook kernel in Phase 1), not by the agent, so it survives pauses.

**Tech Stack:** Python 3.12, uv, `deepagents` 0.7.x, `langchain-anthropic`, `playwright` (async API), `python-dotenv`, `jupytext` + `ipykernel` (notebook authoring).

**Spec:** `DECISIONS.md` (D1–D31) at the repo root, and the assignment PDF `Assignment A — Computer-Use Automation System.pdf`. Executors read both.

## Global Constraints

Copied from `DECISIONS.md`; every task obeys these.

- Target app is **ParaBank** only: `https://parabank.parasoft.com/parabank` (D1). Allowed host: `parabank.parasoft.com` (D15). Be polite: few runs, no real data or credentials (Section 9).
- Language **Python ≥ 3.12**, packages managed with **uv** (D3).
- Agent framework is **deep agents** for discovery only; replay is never an agent (D4, D6). Fallback if it fights Playwright: custom LangGraph graph with the same tools.
- Browser tools are **plain Playwright + our own tools**. No Playwright MCP (D5).
- Perception is **screenshot + numbered element list**; the model points at numbers; **pixels and numbers are never persisted** in artifacts (D2, D8).
- Model is **`anthropic:claude-sonnet-5`**, read from `MODEL` env var (D6b).
- **Secrets never go in the repo or the model context.** Credentials live in `.env` (git-ignored) and are typed by our login helper before the agent starts; the agent never sees them (D11/D17).
- Defaults: 25-step goal limit, 3 repeats = stuck, 2 retries on slow page, $500 transfer limit (Section H of DECISIONS.md). Phase 1 uses a graph `recursion_limit` of 40 as its step guard.
- No LLM in replay; no queues, services, or multi-tenant plumbing (D6, D25).

---

## Part A — Roadmap (what is logical, in order)

**Why the agent comes first.** Everything downstream depends on what the agent's tools look like: the recorder captures the agent's tool calls, the artifact schema describes what those calls identified, and replay re-executes them. Also the single biggest technical risk in `DECISIONS.md` (Section J) is *"deep agents + Playwright fit"*. Phase 1 tests that risk before anything is built on top of it.

Each phase ends in something you can run and look at. **Only Phase 1 is planned in detail below.** Each later phase gets its own plan, written after the previous phase's findings, because what we learn changes the next step.

| Phase | Builds | Done when | Decisions |
|---|---|---|---|
| **1** | Deep agent + Playwright tools (screenshot + numbered list), login helper, step trace, stuck guard, pause/resume smoke test | Agent reads a real balance on ParaBank; a deliberate impossible goal stops cleanly; a click can be paused, approved, and resumed on the same live browser; go/no-go on deep agents recorded | D2, D4, D5, D6b, D11/17, D15 (minimal), D19 (step limit) |
| **2** | Artifact schema in Pydantic + YAML round-trip (no browser) | A hand-written `get_account_balance.yaml` loads, validates, rejects bad variants | D7, D8, D9, D10, D12, D21 (fields), D27 |
| **3** | Recorder: agent tool calls → ranked locators → clean steps → YAML; input parameterisation and leftover-literal check | Phase 1 run produces a valid artifact with `{{account_id}}` and no hardcoded value | D8, D12, D23, D29 |
| **4** | Replay engine, happy path, no LLM, via a `Surface` seam | Replay of the recorded artifact returns `SUCCESS` with `balance`, verified against the page | D6, D9, D22, D26 |
| **5** | Error buckets, business-outcome rules, waits/retries, result contract, verify-after-record | `ACCOUNT_NOT_FOUND`, slow page, expired session, missing element each give the right status | D10, D23, D26, D27 |
| **6** | Safety: `allowlist.yaml` (domains/actions/routes), `redact()`, screenshot covering, risk classification, $500 rule | Off-list URL blocked; secrets never in logs; $5,000 transfer returns `NEEDS_APPROVAL` | D15, D16, D18, D20 |
| **7** | Escalation: all six stuck triggers, `ask_human`, control state, intervention request, `page.pause()` wrapper, human-action capture | Stuck run pauses, human acts in the live window, run resumes, human actions in log | D14, D19, D28 |
| **8** | `transfer_funds` flow end to end + all five error demos saved to `evidence/` | `evidence/` has artifacts and logs for both flows, both phases, all five cases | D13, D24, D30 |
| **9** | Port notebook → `src/cua/`, CLI (`cua discover`, `cua replay`), pytest suite, `README.md`, `REPORT.md` | Fresh clone: `uv run pytest` passes with no key; README demo path works | D25, D31, Section 6 |

**Known design issues found while planning (carry into later phases):**

1. **Data cells are not clickable, so they get no number.** A balance sits in a plain table cell. Phase 1 lets the agent read it with a `page_text` tool. Phase 3 needs a way for the agent to *mark* a value for extraction so the recorder can build a "cell next to label *Balance*" locator (D12). Expect a `mark_text` tool.
2. **`data-cua-ref` is a temporary attribute** we inject to resolve numbers to elements. The recorder must never save it as a locator (D8).
3. **Deep agents ships 8 built-in tools** we do not want (`ls`, `read_file`, `write_file`, `edit_file`, `delete`, `glob`, `grep`, `task`) and they cannot be removed via the API we inspected. Phase 1 tells the agent not to use them and counts any misuse (Task 7).
4. **Planning (`write_todos`) is not on by default** in the installed version. Decide in Phase 1 findings whether a plan step is worth adding.
5. **Async Playwright in a notebook.** Jupyter already runs an event loop, so use `playwright.async_api` with top-level `await`. The browser lives in the kernel; restarting the kernel closes it.

---

## Amendment 1 — agent-driven login (D32). Overrides any conflicting task text below.

- **No `login()` helper.** The agent logs in itself with a `type_secret` tool.
- **Config (notebook 1):** add `SECRETS = {"username": "PARABANK_USERNAME", "password": "PARABANK_PASSWORD"}` and `resolve_secret(name) -> str` (raises on unknown name). Write its assert checks first.
- **Task 2:** keep register-by-hand (ParaBank leaves the browser logged in afterwards). Keep `first_account_id` and `read_balance_ground_truth`, labelled *ParaBank-only grader, not product code*. Drop `login()` and the verify-login cell.
- **Task 4 verify:** also clear cookies, open `index.htm`, observe, save `observe_login.png`. Expect `textbox` username/password and a `Log In` button in the list.
- **Task 5 (notebook 2):** add tool `type_secret(ref: int, name: str)`. Refuse if name unknown, host not allowed, or target is not an input. Never put the value in any return text.
- **Task 6 (notebook 2):** prompt says "log in with `type_secret` names `username` and `password`". First goal starts logged out: "Log in, open the first account listed, report its id and balance."
- **Task 7 (notebook 3):** add a check that `type_secret` refuses on an off-list host.

---

## Part B — Phase 1 detailed plan

### How verification works in Phase 1 (read this first)

Phase 1 is exploratory notebook work, so classic red/green pytest does not fit. Instead every task has a **verify cell** with an **exact expected output**. Pure helper functions (`host_allowed`, `format_elements`) get `assert` cells written *before* the implementation so we still go red → green. Real pytest arrives in Phase 9 when the code moves to `src/`.

The notebook is a **jupytext "percent" `.py` file**: cells are separated by `# %%`. It opens as a notebook in VS Code (Jupyter) and diffs cleanly in git. Run cells in order, top to bottom, in one kernel.

### File structure

```
interface-ai-cua-v2/
  pyproject.toml                       # exists; Task 1 adds deps
  DECISIONS.md                         # exists
  .gitignore                           # Task 1
  .env.example                         # Task 1 (committed, fake values)
  .env                                 # Task 1/2 (NOT committed, real values)
  notebooks/
    01_agent_playwright.py             # Tasks 1-8: the Phase 1 notebook (one responsibility: agent + browser)
    FINDINGS.md                        # Task 9: what we learned; go/no-go
  docs/superpowers/plans/…             # this plan
```

The notebook grows by appending sections; each task says which section it adds.

---

### Task 1: Project setup and notebook skeleton

**Files:**
- Modify: `pyproject.toml` (via `uv add`)
- Create: `.gitignore`, `.env.example`, `.env`, `notebooks/01_agent_playwright.py`

**Interfaces:**
- Produces: notebook globals `MODEL: str`, `BASE: str`, `ALLOWED_HOSTS: set[str]`.

- [ ] **Step 1: Initialise git and add dependencies**

```bash
cd ~/Documents/interface-ai-cua-v2
git init
uv add deepagents langchain-anthropic playwright python-dotenv
uv add --dev jupytext ipykernel
uv run playwright install chromium
```

Expected: `pyproject.toml` `dependencies` lists the four packages; chromium download completes.

- [ ] **Step 2: Create `.gitignore`**

```gitignore
.env
.venv/
__pycache__/
.ipynb_checkpoints/
notebooks/scratch/
*.pyc
```

- [ ] **Step 3: Create `.env.example` (committed) and `.env` (not committed)**

`.env.example`:

```dotenv
ANTHROPIC_API_KEY=
MODEL=anthropic:claude-sonnet-5
PARABANK_USERNAME=
PARABANK_PASSWORD=
```

Copy it to `.env`, then paste your real `ANTHROPIC_API_KEY`. Leave the two ParaBank values empty until Task 2.

```bash
cp .env.example .env
```

- [ ] **Step 4: Create the notebook with the first cell**

`notebooks/01_agent_playwright.py`:

```python
# %% [markdown]
# # Phase 1: deep agent + Playwright on ParaBank
# Run cells top to bottom in ONE kernel. Restarting the kernel closes the browser.

# %% Section 1: config
import os
import asyncio
import base64
import json
import re
from dotenv import load_dotenv

load_dotenv(override=True)

MODEL = os.getenv("MODEL", "anthropic:claude-sonnet-5")
BASE = "https://parabank.parasoft.com/parabank"
ALLOWED_HOSTS = {"parabank.parasoft.com"}

assert os.getenv("ANTHROPIC_API_KEY"), "Set ANTHROPIC_API_KEY in .env"
print("model:", MODEL, "| anthropic key set: yes")
```

- [ ] **Step 5: Verify**

Open the notebook in VS Code, select the `.venv` kernel, run the cell. Alternatively: `uv run python notebooks/01_agent_playwright.py`.

Expected output: `model: anthropic:claude-sonnet-5 | anthropic key set: yes`

If it fails with the assertion, `.env` is missing the key.

- [ ] **Step 6: Commit**

```bash
git add pyproject.toml uv.lock .gitignore .env.example notebooks/01_agent_playwright.py DECISIONS.md docs
git commit -m "chore: uv project, deps, notebook skeleton"
```

Confirm `.env` is not staged: `git status --short` must not list it.

---

### Task 2: Browser, test user, and login helper

**Files:**
- Modify: `notebooks/01_agent_playwright.py` (append Section 2)
- Modify: `.env` (add test-user credentials)

**Interfaces:**
- Consumes: `BASE`.
- Produces: globals `pw`, `browser`, `context`, `page`; `async login(page) -> None`; `async first_account_id(page) -> str`; `async read_balance_ground_truth(page, account_id) -> str`.

ParaBank needs a registered user. This step is done **by you, by hand**, in the visible browser: it involves a form field for an SSN, and per D11/D17 the agent must never handle that.

- [ ] **Step 1: Launch a visible browser**

Append:

```python
# %% Section 2: browser
from playwright.async_api import async_playwright

pw = await async_playwright().start()
browser = await pw.chromium.launch(headless=False)
context = await browser.new_context(viewport={"width": 1280, "height": 900})
page = await context.new_page()
await page.goto(f"{BASE}/register.htm")
print("opened:", page.url)
```

Expected: a Chromium window opens on the ParaBank registration page; the cell prints the URL.

- [ ] **Step 2: Register a throwaway user by hand**

In the browser window, fill the form with **fake data only**:

| Field | Value |
|---|---|
| First / Last name | `Test` / `User` |
| Address / City / State / Zip | `1 Test St` / `Testville` / `TS` / `00000` |
| Phone | `0000000000` |
| SSN | `000-00-0000` |
| Username | `cua_demo_` + 4 random digits (usernames are shared site-wide) |
| Password | a throwaway, **not one you use anywhere else** |

Submit. ParaBank logs you in and shows a welcome page.

- [ ] **Step 3: Put the credentials in `.env`**

```dotenv
PARABANK_USERNAME=cua_demo_1234
PARABANK_PASSWORD=<the throwaway password>
```

- [ ] **Step 4: Append the login helper and ground-truth helpers**

```python
# %% Section 2b: login helper (credentials are typed here, never seen by the agent)
load_dotenv(override=True)


async def login(page) -> None:
    await page.goto(f"{BASE}/index.htm")
    await page.fill('input[name="username"]', os.environ["PARABANK_USERNAME"])
    await page.fill('input[name="password"]', os.environ["PARABANK_PASSWORD"])
    await page.click('input[value="Log In"]')
    await page.wait_for_url("**/overview.htm")


async def first_account_id(page) -> str:
    href = await page.locator('a[href*="activity.htm?id="]').first.get_attribute("href")
    return href.split("id=")[1]


async def read_balance_ground_truth(page, account_id: str) -> str:
    """Independent check of the balance, used only to grade the agent."""
    await page.goto(f"{BASE}/activity.htm?id={account_id}")
    text = await page.inner_text("body")
    match = re.search(r"Balance:\s*(\$[\d,]+\.\d{2})", text)
    assert match, f"could not find a balance in page text: {text[:300]!r}"
    return match.group(1)
```

- [ ] **Step 5: Verify**

Append and run:

```python
# %% verify: login
await login(page)
body = await page.inner_text("body")
assert "Accounts Overview" in body, "login did not reach the overview page"
ACCOUNT_ID = await first_account_id(page)
print("logged in; first account id:", ACCOUNT_ID)
```

Expected output: `logged in; first account id: <5 digits>`. The window shows the Accounts Overview.

If the assertion fails, the selectors `input[name="username"]` / `input[value="Log In"]` may differ; inspect the login form in DevTools and adjust the two selectors, then rerun.

- [ ] **Step 6: Commit**

```bash
git add notebooks/01_agent_playwright.py
git commit -m "feat(nb): visible browser, login helper, ground-truth balance reader"
```

---

### Task 3: Domain guard (pure functions, red → green)

**Files:**
- Modify: `notebooks/01_agent_playwright.py` (append Section 3)

**Interfaces:**
- Consumes: `ALLOWED_HOSTS`.
- Produces: `host_allowed(url: str) -> bool`.

This is the minimal slice of D15 needed so the agent cannot wander off-site. The real allowlist (`allowlist.yaml`, routes, action types) arrives in Phase 6.

- [ ] **Step 1: Write the failing check first**

Append:

```python
# %% Section 3: domain guard — checks first (should fail: function not defined yet)
assert host_allowed("https://parabank.parasoft.com/parabank/overview.htm") is True
assert host_allowed("https://evil.example.com/parabank") is False
assert host_allowed("https://parabank.parasoft.com.evil.com/x") is False
assert host_allowed("about:blank") is True
print("host_allowed checks passed")
```

- [ ] **Step 2: Run it to verify it fails**

Expected: `NameError: name 'host_allowed' is not defined`.

- [ ] **Step 3: Add the implementation above the checks**

Insert a cell *before* the checks cell:

```python
# %% Section 3: domain guard — implementation
from urllib.parse import urlparse


def host_allowed(url: str) -> bool:
    if url == "about:blank":
        return True
    return urlparse(url).hostname in ALLOWED_HOSTS
```

- [ ] **Step 4: Run both cells to verify they pass**

Expected output: `host_allowed checks passed`. (`parabank.parasoft.com.evil.com` must be rejected because we compare the full hostname, not a prefix.)

- [ ] **Step 5: Commit**

```bash
git add notebooks/01_agent_playwright.py
git commit -m "feat(nb): minimal domain guard"
```

---

### Task 4: `PlaywrightSurface.observe()` — screenshot plus numbered list

**Files:**
- Modify: `notebooks/01_agent_playwright.py` (append Section 4)

**Interfaces:**
- Consumes: `page`.
- Produces:
  - `format_elements(elements: list[dict]) -> str`
  - `@dataclass Observation(png: bytes, elements: list[dict], url: str, title: str)` with `.as_text() -> str`
  - `class PlaywrightSurface(page)` with `async observe() -> Observation`, `name_of(ref: int) -> str | None`

Element dicts have keys `ref:int, role:str, name:str, x,y,w,h:float, inViewport:bool`.

- [ ] **Step 1: Write the failing check for the text formatter**

```python
# %% Section 4a: format_elements — check first (should fail)
sample = [
    {"ref": 1, "role": "textbox", "name": "Username", "inViewport": True},
    {"ref": 2, "role": "button", "name": "Log In", "inViewport": True},
    {"ref": 3, "role": "link", "name": "Footer link", "inViewport": False},
]
expected = '[1] textbox "Username"\n[2] button "Log In"\n[3] link "Footer link" (below the fold)'
assert format_elements(sample) == expected, format_elements(sample)
print("format_elements check passed")
```

Run: expect `NameError`.

- [ ] **Step 2: Implement the formatter, the page scripts, and the surface**

Insert *before* the check cell:

```python
# %% Section 4b: page scripts + surface
from dataclasses import dataclass

OBSERVE_JS = """
() => {
  document.querySelectorAll('[data-cua-ref]').forEach(e => e.removeAttribute('data-cua-ref'));
  const sel = 'a[href], button, input:not([type=hidden]), select, textarea, [role=button], [role=link], [onclick]';
  const roleOf = (el) => {
    const r = el.getAttribute('role'); if (r) return r;
    const t = el.tagName.toLowerCase();
    if (t === 'a') return 'link';
    if (t === 'button') return 'button';
    if (t === 'select') return 'combobox';
    if (t === 'textarea') return 'textbox';
    if (t === 'input') {
      const ty = (el.getAttribute('type') || 'text').toLowerCase();
      if (['submit', 'button', 'reset', 'image'].includes(ty)) return 'button';
      if (ty === 'checkbox') return 'checkbox';
      if (ty === 'radio') return 'radio';
      return 'textbox';
    }
    return 'generic';
  };
  const nameOf = (el) => {
    const aria = el.getAttribute('aria-label'); if (aria) return aria.trim();
    if (el.labels && el.labels.length) return el.labels[0].innerText.trim();
    const t = el.tagName.toLowerCase();
    const ty = (el.getAttribute('type') || '').toLowerCase();
    if (t === 'input' && ['submit', 'button', 'reset'].includes(ty)) return (el.value || '').trim();
    const txt = (el.innerText || '').trim(); if (txt) return txt.slice(0, 80);
    return (el.getAttribute('placeholder') || el.getAttribute('title') ||
            el.getAttribute('alt') || el.getAttribute('name') || '').trim();
  };
  const items = [];
  document.querySelectorAll(sel).forEach((el) => {
    const r = el.getBoundingClientRect();
    const st = getComputedStyle(el);
    if (r.width < 2 || r.height < 2 || st.visibility === 'hidden' || st.display === 'none') return;
    const ref = items.length + 1;
    el.setAttribute('data-cua-ref', String(ref));
    items.push({
      ref, role: roleOf(el), name: nameOf(el),
      x: r.x, y: r.y, w: r.width, h: r.height,
      inViewport: r.bottom > 0 && r.top < innerHeight && r.right > 0 && r.left < innerWidth,
    });
  });
  return items;
}
"""

DRAW_JS = """
(items) => {
  const box = document.createElement('div');
  box.id = '__cua_overlay';
  box.style.cssText = 'position:fixed;inset:0;pointer-events:none;z-index:2147483647';
  items.filter(i => i.inViewport).forEach(i => {
    const b = document.createElement('div');
    b.style.cssText = `position:fixed;left:${i.x}px;top:${i.y}px;width:${i.w}px;height:${i.h}px;border:2px solid red;box-sizing:border-box`;
    const l = document.createElement('span');
    l.textContent = i.ref;
    l.style.cssText = 'position:absolute;left:0;top:-14px;background:red;color:#fff;font:bold 11px monospace;padding:0 3px';
    b.appendChild(l);
    box.appendChild(b);
  });
  document.body.appendChild(box);
}
"""

CLEAR_JS = "() => { const o = document.getElementById('__cua_overlay'); if (o) o.remove(); }"


def format_elements(elements: list[dict]) -> str:
    lines = []
    for e in elements:
        line = f'[{e["ref"]}] {e["role"]} "{e["name"]}"'
        if not e["inViewport"]:
            line += " (below the fold)"
        lines.append(line)
    return "\n".join(lines)


@dataclass
class Observation:
    png: bytes
    elements: list[dict]
    url: str
    title: str

    def as_text(self) -> str:
        return f"URL: {self.url}\nTitle: {self.title}\nElements:\n{format_elements(self.elements)}"


class PlaywrightSurface:
    """The only place that touches Playwright. Agent tools talk to this."""

    def __init__(self, page):
        self.page = page
        self.last_elements: list[dict] = []

    async def observe(self) -> Observation:
        elements = await self.page.evaluate(OBSERVE_JS)
        await self.page.evaluate(DRAW_JS, elements)
        png = await self.page.screenshot()
        await self.page.evaluate(CLEAR_JS)
        self.last_elements = elements
        return Observation(png, elements, self.page.url, await self.page.title())

    def name_of(self, ref: int) -> str | None:
        for e in self.last_elements:
            if e["ref"] == ref:
                return e["name"]
        return None
```

- [ ] **Step 3: Run the formatter check**

Expected output: `format_elements check passed`.

- [ ] **Step 4: Verify against the real page**

```python
# %% verify: observe on the overview page
surface = PlaywrightSurface(page)
await page.goto(f"{BASE}/overview.htm")
obs = await surface.observe()
os.makedirs("notebooks/scratch", exist_ok=True)
open("notebooks/scratch/observe.png", "wb").write(obs.png)
print(obs.as_text()[:1200])
```

Expected: printed list includes lines such as `[n] link "Open New Account"`, `[n] link "Transfer Funds"`, and a link whose name is your account id. Open `notebooks/scratch/observe.png`: red numbered boxes must sit on top of those links. The red boxes must **not** remain on the live page afterwards (look at the browser window).

- [ ] **Step 5: Commit**

```bash
git add notebooks/01_agent_playwright.py
git commit -m "feat(nb): PlaywrightSurface.observe with numbered screenshot"
```

---

### Task 5: Actions and the agent tools

**Files:**
- Modify: `notebooks/01_agent_playwright.py` (append Section 5)

**Interfaces:**
- Consumes: `PlaywrightSurface`, `Observation`, `host_allowed`, `page`.
- Produces: `PlaywrightSurface.click(ref)`, `.type_text(ref, text)`, `.page_text()`; module globals `surface`, `RESULT: dict`; LangChain tools `observe`, `click`, `type_text`, `page_text`, `finish`; `TOOLS: list`.

Each action tool returns the **new** screenshot and list, so the agent never acts on stale numbers.

- [ ] **Step 1: Add actions to the surface**

```python
# %% Section 5a: surface actions (extend the class)
async def _settle(self) -> None:
    try:
        await self.page.wait_for_load_state("domcontentloaded", timeout=5000)
    except Exception:
        pass


async def _click(self, ref: int) -> None:
    await self.page.locator(f'[data-cua-ref="{ref}"]').click(timeout=5000)
    await self._settle()


async def _type_text(self, ref: int, text: str) -> None:
    await self.page.locator(f'[data-cua-ref="{ref}"]').fill(text, timeout=5000)


async def _page_text(self) -> str:
    return (await self.page.inner_text("body"))[:4000]


PlaywrightSurface._settle = _settle
PlaywrightSurface.click = _click
PlaywrightSurface.type_text = _type_text
PlaywrightSurface.page_text = _page_text
```

(Kept as a notebook-friendly patch so earlier cells need not be re-run; when the code moves to `src/` in Phase 9 these become normal methods.)

- [ ] **Step 2: Define the tools**

```python
# %% Section 5b: agent tools
from langchain.tools import tool

surface = PlaywrightSurface(page)
RESULT: dict = {}


def _blocks(prefix: str, obs: Observation) -> list[dict]:
    return [
        {"type": "text", "text": f"{prefix}\n{obs.as_text()}"},
        {"type": "image", "base64": base64.b64encode(obs.png).decode(), "mime_type": "image/png"},
    ]


@tool
async def observe() -> list:
    """Look at the current page. Returns a screenshot with red numbered boxes and the list of numbered elements."""
    return _blocks("Current page.", await surface.observe())


@tool
async def click(ref: int) -> list:
    """Click the element with this number (from the latest screenshot/list). Returns the new page state."""
    try:
        await surface.click(ref)
    except Exception as exc:
        return _blocks(f"CLICK FAILED for [{ref}]: {type(exc).__name__}. Use a number from the list below.", await surface.observe())
    if not host_allowed(page.url):
        await page.go_back()
        return _blocks("BLOCKED: that led outside the allowed site. Went back.", await surface.observe())
    return _blocks(f"Clicked [{ref}].", await surface.observe())


@tool
async def type_text(ref: int, text: str) -> list:
    """Type text into the input with this number. Returns the new page state."""
    try:
        await surface.type_text(ref, text)
    except Exception as exc:
        return _blocks(f"TYPE FAILED for [{ref}]: {type(exc).__name__}.", await surface.observe())
    return _blocks(f"Typed into [{ref}].", await surface.observe())


@tool
async def page_text() -> str:
    """Read the visible text of the whole page. Use this to read values such as balances."""
    return await surface.page_text()


@tool
async def finish(summary: str, values: dict[str, str]) -> str:
    """Call once when the goal is done (or when stuck: start summary with 'STUCK:'). `values` holds the requested facts, e.g. {"balance": "$100.00"}."""
    RESULT.clear()
    RESULT.update({"summary": summary, "values": values})
    return "Recorded. Stop now."


TOOLS = [observe, click, type_text, page_text, finish]
print("tools:", [t.name for t in TOOLS])
```

Expected output: `tools: ['observe', 'click', 'type_text', 'page_text', 'finish']`.

- [ ] **Step 3: Verify the tools by calling them directly (no LLM yet)**

```python
# %% verify: tools work without the LLM
await page.goto(f"{BASE}/overview.htm")
r = await observe.ainvoke({})
print(type(r).__name__, "| content blocks:", [b["type"] for b in r] if isinstance(r, list) else r)
txt = await page_text.ainvoke({})
assert "Accounts Overview" in txt
print("page_text ok:", txt[:60].replace("\n", " "))
```

Expected: content blocks `['text', 'image']` (a `ToolMessage` may wrap it; either way both block types appear) and `page_text ok: …Accounts Overview…`. If `observe.ainvoke({})` returns a `ToolMessage`, print `r.content` block types instead; the content must be a list containing one text and one image block.

- [ ] **Step 4: Commit**

```bash
git add notebooks/01_agent_playwright.py
git commit -m "feat(nb): surface actions and agent tools"
```

---

### Task 6: Create the deep agent, stream its steps, run the happy path

**Files:**
- Modify: `notebooks/01_agent_playwright.py` (append Section 6)

**Interfaces:**
- Consumes: `TOOLS`, `MODEL`, `RESULT`, `surface`, `ACCOUNT_ID`, `read_balance_ground_truth`.
- Produces: `agent`; `async run(goal: str, thread_id: str, limit: int = 40) -> list[tuple[str, dict]]` returning the ordered `(tool_name, args)` trace.

- [ ] **Step 1: Create the agent and the streaming runner**

```python
# %% Section 6: the deep agent
from deepagents import create_deep_agent
from langgraph.checkpoint.memory import MemorySaver
from langgraph.errors import GraphRecursionError

SYSTEM_PROMPT = """You operate a real web browser to accomplish a goal on a banking demo website.
Every tool result shows a screenshot with red numbered boxes plus a list of the numbered elements.
Refer to elements only by their number. Numbers change after every action: use the latest list only.
You are already logged in. Never type or ask for passwords or other credentials.
Your tools: observe, click, type_text, page_text, finish. Use page_text to read values such as balances.
Do NOT use ls, read_file, write_file, edit_file, delete, glob, grep or task. They are irrelevant here.
When the goal is achieved, call finish with a one-line summary and the requested values, then stop.
If you cannot make progress, call finish with a summary starting 'STUCK:' and explain why."""

agent = create_deep_agent(
    model=MODEL,
    tools=TOOLS,
    system_prompt=SYSTEM_PROMPT,
    checkpointer=MemorySaver(),
)


async def run(goal: str, thread_id: str, limit: int = 40) -> list[tuple[str, dict]]:
    RESULT.clear()
    trace: list[tuple[str, dict]] = []
    cfg = {"configurable": {"thread_id": thread_id}, "recursion_limit": limit}
    try:
        async for chunk in agent.astream(
            {"messages": [{"role": "user", "content": goal}]}, config=cfg, stream_mode="updates"
        ):
            for _node, update in chunk.items():
                msgs = update.get("messages") if isinstance(update, dict) else None
                if not isinstance(msgs, list):
                    continue
                for m in msgs:
                    for call in getattr(m, "tool_calls", None) or []:
                        trace.append((call["name"], call["args"]))
                        print(f"  step {len(trace):>2}: {call['name']} {call['args']}")
    except GraphRecursionError:
        print(f"  STOPPED: recursion limit ({limit}) reached")
    return trace
```

- [ ] **Step 2: Run the happy path**

```python
# %% run: happy path
await page.goto(f"{BASE}/overview.htm")
goal = f"Open account {ACCOUNT_ID} from the Accounts Overview page and report its current balance."
trace = await run(goal, thread_id="happy-1")
print("RESULT:", RESULT)
```

Expected: the browser window visibly navigates; the log shows roughly 3–8 steps ending in `finish`; `RESULT` has `values` containing a balance like `{'balance': '$100.00'}`.

- [ ] **Step 3: Grade it against ground truth**

```python
# %% verify: happy path
agent_balance = RESULT["values"].get("balance", "")
truth = await read_balance_ground_truth(page, ACCOUNT_ID)
print("agent:", agent_balance, "| truth:", truth)
assert agent_balance.replace(" ", "") == truth, "agent balance does not match the page"
print("PASS. steps:", len(trace))
```

Expected output: `PASS. steps: <n>` with `n` ≤ 15.

If the agent loops or fails, do **not** tune blindly: read the printed steps, look at what the screenshot list showed at the failing step, and note it for Task 9. Common first fixes: prompt wording, or an element the list did not number (add its selector to `OBSERVE_JS`).

- [ ] **Step 4: Commit**

```bash
git add notebooks/01_agent_playwright.py
git commit -m "feat(nb): deep agent with streamed trace; happy path passes"
```

---

### Task 7: Stress the agent (stuck goal, tool misuse, step guard)

**Files:**
- Modify: `notebooks/01_agent_playwright.py` (append Section 7)

**Interfaces:**
- Consumes: `run`, `trace`, `RESULT`.

This answers the concerns you raised: infinite loops and unwanted deep-agent tools.

- [ ] **Step 1: Count misuse of the built-in tools**

```python
# %% Section 7a: built-in tool misuse in the happy-path trace
OURS = {"observe", "click", "type_text", "page_text", "finish"}
misuse = [name for name, _ in trace if name not in OURS]
print("non-browser tool calls in happy path:", misuse or "none")
```

Expected: `none`. Record any other value in Task 9.

- [ ] **Step 2: Run an impossible goal**

```python
# %% Section 7b: impossible goal — must stop, not loop
await page.goto(f"{BASE}/overview.htm")
trace_bad = await run(
    "Open account 99999999 from the Accounts Overview page and report its balance.",
    thread_id="stuck-1",
    limit=40,
)
print("steps:", len(trace_bad), "| RESULT:", RESULT)
```

Expected (either is a pass): the agent calls `finish` with a summary starting `STUCK:` **or** the run prints `STOPPED: recursion limit (40) reached`. Failing behaviour to look for: it "succeeds" with an invented balance, or wanders to another site.

- [ ] **Step 3: Repeat detection preview (observe only, no code change)**

Look at `trace_bad`. Count consecutive identical `(name, args)` pairs. If you see the same call 3+ times in a row, that confirms why D19 needs code-level repeat detection in Phase 7; note the count in Task 9.

- [ ] **Step 4: Commit**

```bash
git add notebooks/01_agent_playwright.py
git commit -m "feat(nb): stuck-goal and tool-misuse checks"
```

---

### Task 8: Pause / resume smoke test on the same live browser

**Files:**
- Modify: `notebooks/01_agent_playwright.py` (append Section 8)

**Interfaces:**
- Consumes: `surface.name_of`, `TOOLS`, `MODEL`, `SYSTEM_PROMPT`.
- Produces: `agent_hitl`; `is_risky_click(req) -> bool`.

This tests the biggest open risk (D4): can deep agents pause **before** a Playwright action, keep the browser alive, and continue? It also foreshadows D20/D28. The predicate here is a stand-in for the real risk policy (Phase 6).

- [ ] **Step 1: Build a second agent that pauses on risky clicks**

```python
# %% Section 8: pause / resume
import uuid
from langgraph.types import Command

RISKY_NAMES = {"Transfer Funds"}


def is_risky_click(req) -> bool:
    ref = req.tool_call["args"].get("ref")
    return surface.name_of(ref) in RISKY_NAMES


agent_hitl = create_deep_agent(
    model=MODEL,
    tools=TOOLS,
    system_prompt=SYSTEM_PROMPT,
    checkpointer=MemorySaver(),
    interrupt_on={"click": {"allowed_decisions": ["approve", "reject"], "when": is_risky_click}},
)


async def run_until_pause(goal: str, thread_id: str):
    cfg = {"configurable": {"thread_id": thread_id}, "recursion_limit": 40}
    out = await agent_hitl.ainvoke({"messages": [{"role": "user", "content": goal}]}, config=cfg, version="v2")
    return out, cfg
```

- [ ] **Step 2: Run until the agent tries the risky click**

```python
# %% run: hits the pause
await page.goto(f"{BASE}/overview.htm")
tid = f"hitl-{uuid.uuid4().hex[:6]}"
out, cfg = await run_until_pause("Open the Transfer Funds page and tell me which fields it has.", tid)
assert out.interrupts, "expected a pause before the Transfer Funds click"
req = out.interrupts[0].value["action_requests"][0]
print("PAUSED before:", req["name"], req["args"])
print("current url (should still be overview):", page.url)
```

Expected: `PAUSED before: click {'ref': <n>}`; the URL still ends in `overview.htm` (the click has **not** happened); the browser window is still open and responsive.

- [ ] **Step 3: Approve and resume**

```python
# %% resume: approve
out2 = await agent_hitl.ainvoke(
    Command(resume={"decisions": [{"type": "approve"}]}), config=cfg, version="v2"
)
final = (out2.value if hasattr(out2, "value") else out2)["messages"][-1]
print("url after approve:", page.url)
print("agent says:", str(final.content)[:300])
assert "transfer.htm" in page.url
```

Expected: `url after approve` ends in `transfer.htm`; the agent describes the transfer form fields.

- [ ] **Step 4: Run again and reject**

```python
# %% resume: reject
await page.goto(f"{BASE}/overview.htm")
tid2 = f"hitl-{uuid.uuid4().hex[:6]}"
out3, cfg3 = await run_until_pause("Open the Transfer Funds page and tell me which fields it has.", tid2)
assert out3.interrupts
out4 = await agent_hitl.ainvoke(
    Command(resume={"decisions": [{"type": "reject", "message": "A human declined this step."}]}),
    config=cfg3, version="v2",
)
final4 = (out4.value if hasattr(out4, "value") else out4)["messages"][-1]
print("url after reject (must NOT be transfer.htm):", page.url)
print("agent says:", str(final4.content)[:300])
assert "transfer.htm" not in page.url
```

Expected: URL stays on the overview page; the agent acknowledges the rejection instead of retrying blindly.

- [ ] **Step 5: Commit**

```bash
git add notebooks/01_agent_playwright.py
git commit -m "feat(nb): pause/resume smoke test with approve and reject"
```

---

### Task 9: Findings and go/no-go on deep agents

**Files:**
- Create: `notebooks/FINDINGS.md`
- Modify: `DECISIONS.md` only if a decision changes

- [ ] **Step 1: Write `notebooks/FINDINGS.md`** from what you actually observed. Use this structure and fill every line with a real number or sentence from the runs above:

```markdown
# Phase 1 findings

## Runs
| Run | Steps | Result | Cost/time notes |
|---|---|---|---|
| Happy path (Task 6) | <n> | <balance matched ground truth: yes/no> | <rough seconds, any obvious token cost> |
| Impossible goal (Task 7) | <n> | <finished STUCK: / hit recursion limit> | |
| Pause + approve (Task 8) | – | <url reached> | |
| Pause + reject (Task 8) | – | <agent behaviour> | |

## Go/no-go for deep agents (D4)
Criteria, each answered yes/no with one line of evidence:
1. Happy path completed in ≤ 15 tool calls?
2. Built-in tools (ls, write_file, task…) unused? (Task 7 step 1 output)
3. Impossible goal ended cleanly (STUCK or recursion stop), no invented answer?
4. Browser stayed alive and usable across a pause, and approve/reject both behaved?
5. Any friction between deep agents and the async Playwright tools?

**Decision:** GO (continue with deep agents) / NO-GO (switch to a custom LangGraph graph with the same tools).

## Things the agent got wrong or ignored
<bullet list of specific mistakes, with the step where each happened>

## Ideas for Phase 2/3
<e.g. elements the list did not number; extraction targets that are not clickable>
```

- [ ] **Step 2: Update `DECISIONS.md` if the decision changed**

If NO-GO, edit D4 to record the switch and why. If GO, add one line under D4: `Phase 1 confirmed: <one sentence of evidence>`.

- [ ] **Step 3: Commit**

```bash
git add notebooks/FINDINGS.md DECISIONS.md
git commit -m "docs: phase 1 findings and D4 go/no-go"
```

- [ ] **Step 4: Stop and hand back to the user**

Report the findings. Do not start Phase 2. The next plan (artifact schema) is written only after the user has read `FINDINGS.md`.

---

## Self-review

**Spec coverage (Phase 1 scope only).**
- D2 screenshot + numbered list → Task 4. ✓
- D4 deep agents + risk test, and fallback trigger → Tasks 6, 8, 9. ✓
- D5 plain Playwright, own tools → Tasks 4, 5. ✓
- D6b Sonnet 5 from config → Task 1, 6. ✓
- D11/D17 login helper, agent never sees credentials, human-only registration → Task 2 and the prompt in Task 6. ✓
- D15 minimal domain enforcement in tool code → Tasks 3, 5 (`click` guard). ✓
- D19 step guard (recursion limit) and a preview of repeat detection → Tasks 6, 7. ✓
- D14/D20/D28 pause-before-risky-click and same-live-session resume, as a smoke test → Task 8. ✓
- Not in Phase 1 by design: artifact (2), recorder (3), replay (4–5), full safety (6), full escalation (7), transfer flow (8), production port (9). All appear in the roadmap table. ✓

**Placeholder scan.** The only fill-in items are in `FINDINGS.md` (Task 9), which record observed results, and the throwaway username/password in Task 2, which the user chooses. No code step defers work.

**Type consistency.** `Observation`, `PlaywrightSurface`, `format_elements`, `host_allowed`, `surface`, `RESULT`, `TOOLS`, `run`, `agent_hitl`, `is_risky_click`, `ACCOUNT_ID`, and `read_balance_ground_truth` are each defined once and used with the same signatures in later tasks. `surface` is defined in Task 4 (verify cell) and redefined identically in Task 5; Task 5's definition is the one the tools close over, so run Task 5 before Task 6.

**API facts verified before writing.** Against `deepagents 0.7.15`, `langchain 1.4.2`, `langgraph 1.2.11`: `create_deep_agent(model, tools, system_prompt, checkpointer, interrupt_on)` exists; async tools work with `ainvoke`; tools can return `[{"type":"text",…},{"type":"image","base64":…,"mime_type":"image/png"}]` and they reach Anthropic as base64 image blocks; `interrupt_on` with a `when` predicate pauses, exposes `out.interrupts[0].value["action_requests"]`, and resumes with `Command(resume={"decisions":[…]})`; `recursion_limit` is accepted in config. Not yet verified against the live model: how Sonnet 5 behaves on the real page. That is what Phase 1 exists to learn.
