# %% [markdown]
# # Notebook 1: browser, secrets config, and numbered screenshot
# Run cells top to bottom in ONE kernel. Restarting the kernel closes the browser.
# No LLM in this notebook. It only proves we can drive ParaBank and "see" the page.

# %% [markdown]
# ## Section 1: config
# Loads `.env`, sets the base URL, the one allowed host, and the secret names. `resolve_secret` maps a secret name to its `.env` value.
# Expected output: `model: anthropic:claude-sonnet-5 | base: https://parabank.parasoft.com/parabank`

# %%
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
SECRETS = {"username": "PARABANK_USERNAME", "password": "PARABANK_PASSWORD"}


def resolve_secret(name: str) -> str:
    """Look up a secret by name. Raises on unknown name or empty value."""
    if name not in SECRETS:
        raise KeyError(f"unknown secret name: {name!r}")
    value = os.environ.get(SECRETS[name], "")
    if not value:
        raise RuntimeError(f"env var {SECRETS[name]} is empty or not set")
    return value


print("model:", MODEL, "| base:", BASE)

# %% [markdown]
# ## Section 1b: check `resolve_secret`
# Pure check, no browser. Uses a fake value and restores `os.environ` afterwards. Never prints a value.
# Expected output: `resolve_secret checks passed`.
# (Written test-first: without the config cell above these fail with `NameError`.)

# %%
_var = SECRETS["password"]
_saved = os.environ.get(_var)
try:
    try:
        resolve_secret("nope")
        raise AssertionError("unknown name should raise KeyError")
    except KeyError:
        pass

    os.environ[_var] = "fake-value-for-check"
    assert resolve_secret("password") == "fake-value-for-check"

    os.environ[_var] = ""
    try:
        resolve_secret("password")
        raise AssertionError("empty env var should raise RuntimeError")
    except RuntimeError:
        pass
finally:
    if _saved is None:
        os.environ.pop(_var, None)
    else:
        os.environ[_var] = _saved
print("resolve_secret checks passed")

# %% [markdown]
# ## Section 2: open the browser
# Starts a visible Chromium window and opens the ParaBank register page.
# Expected output: a Chromium window appears, and the cell prints `opened: https://parabank.parasoft.com/parabank/register.htm`.

# %%
from playwright.async_api import async_playwright

pw = await async_playwright().start()
browser = await pw.chromium.launch(headless=False)
context = await browser.new_context(viewport={"width": 1280, "height": 900})
page = await context.new_page()
await page.goto(f"{BASE}/register.htm")
print("opened:", page.url)

# %% [markdown]
# ## Section 2a: YOU register a throwaway user (by hand)
# Do this step yourself in the browser window. The agent must never handle an SSN field.
# Use **fake data only**:
#
# | Field | Value |
# |---|---|
# | First / Last name | `Test` / `User` |
# | Address / City / State / Zip | `1 Test St` / `Testville` / `TS` / `00000` |
# | Phone | `0000000000` |
# | SSN | `000-00-0000` |
# | Username | `cua_demo_` + 4 random digits (usernames are shared site-wide) |
# | Password | a throwaway, **not one you use anywhere else** |
#
# Submit the form. ParaBank leaves the browser logged in afterwards.
# Then open `.env` and fill in:
#
# ```
# PARABANK_USERNAME=cua_demo_1234
# PARABANK_PASSWORD=<the throwaway password>
# ```
#
# The agent will use these later through `type_secret`. It only sees the names `username` and `password`, never the values.
# Save `.env`, then run the next cell. It reloads `.env` with `load_dotenv(override=True)`, so the new values are picked up without restarting the kernel.

# %% [markdown]
# ## Section 2b: ground-truth helpers
# ParaBank-only grader used to check the agent. Not product code.
# Defines `first_account_id` and `read_balance_ground_truth`, and reloads `.env`.
# Expected output: nothing (just defines functions).

# %%
load_dotenv(override=True)


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


# %% [markdown]
# ## Section 3: domain guard
# `host_allowed(url)` says whether a URL is on the one allowed host. It compares the full hostname, so look-alikes like `parabank.parasoft.com.evil.com` are rejected.
# Run the implementation cell first, then the checks cell.
# Expected output of the checks: `host_allowed checks passed`.
# (Written test-first: the checks were written before the function. Without the implementation cell they fail with `NameError`.)

# %%
from urllib.parse import urlparse


def host_allowed(url: str) -> bool:
    if url == "about:blank":
        return True
    return urlparse(url).hostname in ALLOWED_HOSTS


# %%
assert host_allowed("https://parabank.parasoft.com/parabank/overview.htm") is True
assert host_allowed("https://evil.example.com/parabank") is False
assert host_allowed("https://parabank.parasoft.com.evil.com/x") is False
assert host_allowed("about:blank") is True
print("host_allowed checks passed")

# %% [markdown]
# ## Section 4a: page scripts and the surface
# Defines the JavaScript that finds clickable elements, draws red numbered boxes, and removes them again.
# Also defines `format_elements`, the `Observation` result, and `PlaywrightSurface` with `observe()` and `name_of()`.
# Expected output: nothing (just defines things).

# %%
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


# %% [markdown]
# ## Section 4b: check the text formatter
# A small pure check that `format_elements` prints the numbered list the way we expect.
# Expected output: `format_elements check passed`.

# %%
sample = [
    {"ref": 1, "role": "textbox", "name": "Username", "inViewport": True},
    {"ref": 2, "role": "button", "name": "Log In", "inViewport": True},
    {"ref": 3, "role": "link", "name": "Footer link", "inViewport": False},
]
expected = '[1] textbox "Username"\n[2] button "Log In"\n[3] link "Footer link" (below the fold)'
assert format_elements(sample) == expected, format_elements(sample)
print("format_elements check passed")

# %% [markdown]
# ## Verify: observe on the overview page
# Takes a numbered screenshot of the Accounts Overview page (the browser is still logged in from registration), saves it to `notebooks/scratch/observe.png`, and prints the element list.
# Expected output: lines like `[n] link "Open New Account"`, `[n] link "Transfer Funds"`, and a link named with your account id.
# Open `notebooks/scratch/observe.png`: red numbered boxes should sit on those links. The red boxes must NOT stay on the live browser page.

# %%
surface = PlaywrightSurface(page)
await page.goto(f"{BASE}/overview.htm")
obs = await surface.observe()
os.makedirs("notebooks/scratch", exist_ok=True)
open("notebooks/scratch/observe.png", "wb").write(obs.png)
print(obs.as_text()[:1200])

# %% [markdown]
# ## Verify: observe the login page (logged out)
# Clears cookies, opens the login page, observes it, saves `notebooks/scratch/observe_login.png`, and prints the list.
# Expected output: a `textbox` for username, a `textbox` for password, and a `button "Log In"` in the list.
# The browser is now logged out on purpose. Notebook 2's agent will log in itself.

# %%
await context.clear_cookies()
await page.goto(f"{BASE}/index.htm")
obs = await surface.observe()
open("notebooks/scratch/observe_login.png", "wb").write(obs.png)
print(obs.as_text()[:1200])
