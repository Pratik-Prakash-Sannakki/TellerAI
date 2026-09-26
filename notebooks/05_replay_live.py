# %% [markdown]
# # Phase 4 (live): replay against the REAL browser
#
# **This notebook is never run by an agent -- only the user runs it.** It imports Playwright and
# needs a real, visible browser plus `.env` (the ParaBank test user). It wires `run_capability_async`
# (`notebooks/04_replay_engine.py`, Sections 7-9) to `agent.ipynb`'s own real browser layer: the
# numbered-element scanner, the whole-page lock, and the Approve/Reject/Take-over decision bar.
# Nothing about `run_capability`/`run_capability_async`'s own logic changes here -- this notebook
# only supplies a real `AsyncReplaySurface` and a real `escalate`.
#
# ## How to test this (exact cells, in order)
#
# 1. Before you start: `.env` has `PARABANK_USERNAME`/`PARABANK_PASSWORD` (and `ANTHROPIC_API_KEY`
#    if you also use `agent.ipynb` in the same session -- not required here, replay has no LLM).
#    Kernel = this repo's `.venv`. ParaBank is reachable.
# 2. Run every **Setup** cell top to bottom. A visible Chromium window opens on ParaBank's login
#    page. You should see `model: ... | base: https://parabank.parasoft.com/parabank`, then
#    `opened: https://parabank.parasoft.com/parabank/index.htm`, then
#    `[lock] initial setup done | __cua_lock present on page: True | url=...`.
# 3. **Log in by hand once**, in the opened browser window: type your test username/password into
#    the two fields and click Log In. (`get_account_balance` has no login step of its own -- login
#    is its own separate, reusable capability, D45. This notebook does not drive the login form for
#    you; it replays a task that assumes an already-logged-in session, exactly like a scheduled job
#    resuming a session would.) Confirm you land on the Accounts Overview page.
# 4. Run the **`PlaywrightReplaySurface`**, **`make_escalate`**, and **run helper** cells.
# 5. Substitute a REAL account id you own, then run:
#    ```python
#    result = await replay_live(EX / "get_account_balance.yaml", {"account_id": "<YOUR REAL ACCOUNT ID>"})
#    ```
# 6. **Expected output:** a line `REPLAY RESULT: SUCCESS {'balance': '$<your real balance>'}` --
#    e.g. `REPLAY RESULT: SUCCESS {'balance': '$1,200.00'}`, the exact shape PHASE4.md already
#    showed for the file-level (non-live) proof, now produced by a real browser tab clicking
#    nothing (this capability is read-only) and reading a real value off a real page.
# 7. Optional: once you have captured a fresh artifact with `03_recorder.py`'s CAPTURE half, replay
#    that file the same way. For a RISKY capability (e.g. `transfer_funds.yaml`) with an amount at
#    or above `auto_approve_limit` (default $500), you will see the same dark Approve/Reject/Take
#    over bar `agent.ipynb`'s own `click()` tool shows. **Approve** makes the engine resolve the
#    button and click it for real (D85), then continue on to the capability's remaining steps --
#    expect `REPLAY RESULT: SUCCESS {'confirmation': '...'}` with the real confirmation text, not
#    `NEEDS_APPROVAL`. **Reject** or **Take over** still leave the result at `NEEDS_APPROVAL`,
#    with no click ever made on our say-so.
#
# **Send back:** the exact `REPLAY RESULT: ...` line, any `[escalate] ...` lines printed, and any
# red error, exactly as shown. Never paste `.env` or anything typed as a secret.

# %% Setup 1: Setup 1/4 -- config + secrets (copied verbatim from agent.ipynb)
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

# %% Setup 2: Setup 2/4 -- browser (copied verbatim from agent.ipynb)
from playwright.async_api import async_playwright

if "page" not in globals():
    pw = await async_playwright().start()
    browser = await pw.chromium.launch(headless=False)
    context = await browser.new_context(viewport={"width": 1280, "height": 900})
    page = await context.new_page()
await page.goto(f"{BASE}/index.htm")
print("opened:", page.url)

# %% Setup 3: Setup 3/4 -- domain guard (copied verbatim from agent.ipynb)
from urllib.parse import urlparse


def host_allowed(url: str) -> bool:
    if url == "about:blank":
        return True
    return urlparse(url).hostname in ALLOWED_HOSTS

# %% Setup 4: Setup 4/4 -- numbered scanner + PlaywrightSurface (copied verbatim from agent.ipynb,
# STEP 1's options/submit patch already folded in, exactly as agent.ipynb applies it)
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
    const valueOf = (el) => {
      const t = el.tagName.toLowerCase();
      if (t === 'select') return el.selectedOptions[0] ? el.selectedOptions[0].text.trim() : '';
      if (t === 'input' || t === 'textarea') {
        const ty = (el.getAttribute('type') || 'text').toLowerCase();
        if (['submit', 'button', 'reset', 'image', 'password'].includes(ty)) return '';
        return (el.value || '').trim();
      }
      return '';
    };
    items.push({
      ref, role: roleOf(el), name: nameOf(el), value: valueOf(el),
      x: r.x, y: r.y, w: r.width, h: r.height,
      options: el.tagName === 'SELECT' ? Array.from(el.options).map(o => o.text.trim()).slice(0, 15) : null,
      submit: (el.tagName === 'BUTTON' && el.type !== 'button') || (el.tagName === 'INPUT' && ['submit', 'image'].includes(el.type)),
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
        if e.get("options"):
            line += f' options={e["options"]}'
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

# %% Setup 5: STEP 2 -- lock, takeover, Approve/Reject/Take-over decision bar (copied verbatim
# from agent.ipynb)
from langgraph.types import Command

HANDBACK = {"event": None}

# ---- Approve / Reject / Take over buttons (their own floating bar, always clickable) ----
DECISION_JS = """(info) => new Promise(resolve => {
  const bar = document.createElement('div');
  bar.style.cssText = 'position:fixed;top:0;left:0;right:0;z-index:2147483647;background:#111;color:#fff;font:14px sans-serif;padding:10px;display:flex;flex-direction:column;gap:8px;align-items:center';
  const t = document.createElement('b'); t.textContent = info.title;
  const d = document.createElement('div'); d.textContent = info.details;
  const row = document.createElement('div'); row.style.cssText = 'display:flex;gap:12px';
  [['Approve', 'a'], ['Reject', 'r'], ['Take over', 't']].forEach(([label, val]) => {
    const b = document.createElement('button'); b.textContent = label;
    b.style.cssText = 'padding:6px 14px;font-size:14px;cursor:pointer';
    b.onclick = () => { bar.remove(); resolve(val); };
    row.appendChild(b);
  });
  bar.append(t, d, row);
  document.body.appendChild(bar);
})"""

# ---- Whole-page lock: while it is the agent's turn, a real human can neither click nor type
# anywhere on the page. Our own injected UI (this banner, the decision bar above) always sits
# on a higher z-index, so it stays usable regardless of lock state. Our OWN automated actions
# use force=True (STEP 3), which bypasses this overlay entirely -- it only stops a real human's
# mouse and keyboard, never Playwright's own dispatched actions. ----
LOCK_JS = """
() => {
  if (!document.getElementById('__cua_lock')) {
    const d = document.createElement('div');
    d.id = '__cua_lock';
    d.style.cssText = 'position:fixed;inset:0;z-index:2147483000;background:transparent;';
    document.documentElement.appendChild(d);
  }
  if (document.activeElement && document.activeElement.blur) document.activeElement.blur();
  if (!window.__cuaBlockKeys) {
    // Let typing through for an element explicitly poked open by RESTRICT_JS (allow_refs mode).
    // Without this check, the click-blocking overlay and the keyboard block were two separate
    // mechanisms: raising an element's z-index let a click focus it, but every keystroke was
    // still swallowed here, at the document level, regardless of what had focus.
    window.__cuaBlockKeys = (e) => {
      if (e.target && e.target.classList && e.target.classList.contains('__cua_allowed')) return;
      e.preventDefault(); e.stopPropagation();
    };
    document.addEventListener('keydown', window.__cuaBlockKeys, true);
    document.addEventListener('keypress', window.__cuaBlockKeys, true);
  }
}
"""
UNLOCK_JS = """
() => {
  document.getElementById('__cua_lock')?.remove();
  if (window.__cuaBlockKeys) {
    document.removeEventListener('keydown', window.__cuaBlockKeys, true);
    document.removeEventListener('keypress', window.__cuaBlockKeys, true);
    window.__cuaBlockKeys = null;
  }
}
"""

# ---- Risky-element block: separate from the general lock above. During a GENERAL takeover
# (filling in a field), the rest of the page opens up but the risky button must still stay
# non-interactive. Only the take-over-to-submit case turns this off too. ----
BLOCK_JS = """(refs) => {
  document.querySelectorAll('.__cua_blocked').forEach(el => {
    el.classList.remove('__cua_blocked');
    el.style.filter = ''; el.style.pointerEvents = ''; el.style.opacity = '';
  });
  refs.forEach(ref => {
    const el = document.querySelector(`[data-cua-ref="${ref}"]`);
    if (el) { el.classList.add('__cua_blocked'); el.style.filter = 'blur(3px)'; el.style.pointerEvents = 'none'; el.style.opacity = '0.5'; }
  });
}"""
UNBLOCK_JS = "() => document.querySelectorAll('.__cua_blocked').forEach(el => { el.classList.remove('__cua_blocked'); el.style.filter = ''; el.style.pointerEvents = ''; el.style.opacity = ''; })"

# ---- Restrict to specific fields: keep the general lock fully ACTIVE, and poke a hole (raise
# z-index above the lock, but below our own UI) for ONLY the given refs. A visible green outline
# shows the human exactly what is expected. Used by request_value/request_missing_values, where
# we know precisely which field(s) are needed -- unlike ask_human or the approval take-over,
# which genuinely need broader access. ----
RESTRICT_JS = """(refs) => {
  document.querySelectorAll('.__cua_allowed').forEach(el => {
    el.classList.remove('__cua_allowed');
    el.style.position = ''; el.style.zIndex = ''; el.style.outline = '';
  });
  refs.forEach(ref => {
    const el = document.querySelector(`[data-cua-ref="${ref}"]`);
    if (el) {
      el.classList.add('__cua_allowed');
      if (getComputedStyle(el).position === 'static') el.style.position = 'relative';
      el.style.zIndex = '2147483001';
      el.style.outline = '3px solid #2a7';
    }
  });
}"""
UNRESTRICT_JS = "() => document.querySelectorAll('.__cua_allowed').forEach(el => { el.classList.remove('__cua_allowed'); el.style.position = ''; el.style.zIndex = ''; el.style.outline = ''; })"

BANNER_ONLY_JS = """
() => {
  if (document.getElementById('__cua_banner')) return;
  const q = sessionStorage.getItem('cua_question') || '';
  const b = document.createElement('div');
  b.id = '__cua_banner';
  b.style.cssText = 'position:fixed;top:0;left:0;right:0;z-index:2147483647;background:#c00;color:#fff;font:14px sans-serif;padding:8px;display:flex;gap:12px;align-items:center;justify-content:center';
  const label = document.createElement('b'); label.textContent = 'YOU are in control.';
  const msg = document.createElement('span'); msg.textContent = q ? 'Agent asks: ' + q : 'Do the step in this page.';
  const btn = document.createElement('button'); btn.textContent = 'Done, hand back to agent';
  btn.style.cssText = 'padding:6px 14px;font-size:14px;cursor:pointer';
  btn.onclick = () => window.__cua_handback();
  b.append(label, msg, btn);
  document.documentElement.appendChild(b);
}
"""

# ---- "You are in control" bar with a Done button. Runs on every page load (add_init_script);
# also applied immediately to the current page. Locked/unlocked state is driven by the SAME
# 'cua_takeover' sessionStorage flag, so both stay in sync across navigations for free. ----
SYNC_UI_JS = """
(() => {
  const active = sessionStorage.getItem('cua_takeover') === '1';
  if (!active) {
    if (!document.getElementById('__cua_lock')) {
      const d = document.createElement('div');
      d.id = '__cua_lock';
      d.style.cssText = 'position:fixed;inset:0;z-index:2147483000;background:transparent;';
      document.documentElement.appendChild(d);
    }
    if (!window.__cuaBlockKeys) {
      window.__cuaBlockKeys = (e) => {
        if (e.target && e.target.classList && e.target.classList.contains('__cua_allowed')) return;
        e.preventDefault(); e.stopPropagation();
      };
      document.addEventListener('keydown', window.__cuaBlockKeys, true);
      document.addEventListener('keypress', window.__cuaBlockKeys, true);
    }
    document.getElementById('__cua_banner')?.remove();
    return;
  }
  document.getElementById('__cua_lock')?.remove();
  if (window.__cuaBlockKeys) {
    document.removeEventListener('keydown', window.__cuaBlockKeys, true);
    document.removeEventListener('keypress', window.__cuaBlockKeys, true);
    window.__cuaBlockKeys = null;
  }
  if (document.getElementById('__cua_banner')) return;
  const q = sessionStorage.getItem('cua_question') || '';
  const b = document.createElement('div');
  b.id = '__cua_banner';
  b.style.cssText = 'position:fixed;top:0;left:0;right:0;z-index:2147483647;background:#c00;color:#fff;font:14px sans-serif;padding:8px;display:flex;gap:12px;align-items:center;justify-content:center';
  const label = document.createElement('b');
  label.textContent = 'YOU are in control.';
  const msg = document.createElement('span');
  msg.textContent = q ? 'Agent asks: ' + q : 'Do the step in this page.';
  const btn = document.createElement('button');
  btn.textContent = 'Done, hand back to agent';
  btn.style.cssText = 'padding:6px 14px;font-size:14px;cursor:pointer';
  btn.onclick = () => window.__cua_handback();
  b.append(label, msg, btn);
  document.documentElement.appendChild(b);
})();
"""

if "_takeover_ready" not in globals():
    async def _handback():
        if HANDBACK["event"]:
            HANDBACK["event"].set()
    await page.expose_function("__cua_handback", _handback)   # page -> notebook signal
    await page.add_init_script(SYNC_UI_JS)                    # keeps lock/banner correct after every navigation
    # sessionStorage lives in the BROWSER TAB, not the Python kernel: restarting the kernel does
    # NOT clear it, since Playwright's browser process is separate and keeps running. Force-clear
    # any flag left over from an earlier, possibly-interrupted run, so a fresh kernel always starts
    # from a known "not in takeover" state regardless of the tab's history.
    await page.evaluate("() => { sessionStorage.removeItem('cua_takeover'); sessionStorage.removeItem('cua_question'); }")
    await page.evaluate(SYNC_UI_JS)                            # apply to the current page right now (locked by default)
    _lock_present = await page.evaluate("() => !!document.getElementById('__cua_lock')")
    print(f"[lock] initial setup done | __cua_lock present on page: {_lock_present} | url={page.url}")
    _takeover_ready = True


async def human_takeover(question: str = "", auto_on_navigate: bool = False, block_risky: bool = True, allow_refs: list[int] | None = None) -> str:
    """Give the live browser to a human. Returns when they click 'Done', OR, if auto_on_navigate
    is set, as soon as the page reloads at all (same url or not -- a form POST-back that
    re-renders the same url still counts).

    allow_refs, when given, is the STRICTEST mode: the general lock stays fully ACTIVE, and only
    these specific elements are poked open (a visible green outline marks them). Everything else
    on the page, including navigation links, stays locked. Used by request_value and
    request_missing_values, which know exactly which field(s) are needed.

    Without allow_refs, the whole page unlocks instead. block_risky=True (the default) then
    ADDITIONALLY blurs and disables every button needs_human (STEP 3) would flag, so a general
    takeover (ask_human) can still not be used to bypass the approval step. The one call site
    that should pass block_risky=False is the take-over-to-submit case in click(), since acting
    on that specific button is the entire point of that one takeover.

    auto_on_navigate=True is for that same approval-step takeover: the human took over
    specifically to click a submit button, so ANY resulting page reload IS the "done" signal.
    """
    HANDBACK["event"] = asyncio.Event()
    visited = []
    print(f"[takeover] started | auto_on_navigate={auto_on_navigate} | block_risky={block_risky} | allow_refs={allow_refs} | url={page.url}")

    def on_nav(frame):
        if frame != page.main_frame:
            return
        visited.append(frame.url)
        print(f"[takeover] framenavigated fired -> {frame.url}")
        if auto_on_navigate and not HANDBACK["event"].is_set():
            HANDBACK["event"].set()
            print("[takeover] auto hand-back triggered")

    page.on("framenavigated", on_nav)
    await page.evaluate("([q]) => { sessionStorage.setItem('cua_takeover', '1'); sessionStorage.setItem('cua_question', q); }", [question])
    if allow_refs is not None:
        await page.evaluate(BANNER_ONLY_JS)     # lock stays active; only these refs are poked open
        await page.evaluate(RESTRICT_JS, allow_refs)
        risky = []
    else:
        await page.evaluate(SYNC_UI_JS)
        risky = [e["ref"] for e in surface.last_elements if e["inViewport"] and needs_human(e["ref"])] if block_risky else []
        if block_risky:
            await page.evaluate(BLOCK_JS, risky)
    _lock_present = await page.evaluate("() => !!document.getElementById('__cua_lock')")
    print(f"[lock] takeover open | __cua_lock present={_lock_present} (True only expected in allow_refs mode) | risky refs blocked: {risky}")
    await HANDBACK["event"].wait()
    print(f"[takeover] hand-back received | visited={visited} | url now={page.url}")
    page.remove_listener("framenavigated", on_nav)
    if allow_refs is not None:
        await page.evaluate(UNRESTRICT_JS)
    elif block_risky:
        await page.evaluate(UNBLOCK_JS)
    try:
        await page.evaluate("sessionStorage.removeItem('cua_takeover'); sessionStorage.removeItem('cua_question');")
        await page.evaluate(SYNC_UI_JS)   # re-lock and remove the banner right away (safe in both modes)
        _lock_present = await page.evaluate("() => !!document.getElementById('__cua_lock')")
        print(f"[lock] takeover ended, re-locked | __cua_lock present (should be True): {_lock_present}")
    except Exception as exc:
        print(f"[lock] could not confirm re-lock after hand-back (page likely moved on): {type(exc).__name__}")
    text = (await page.inner_text("body"))[:300].replace("\n", " ")
    return f"Pages the human visited: {visited or 'none'}. Page now: {page.url}. Page text: {text}"


def approval_info(args: dict) -> dict:
    name = surface.name_of(args["ref"])
    fields = "; ".join(f"{k}: {v}" for k, v in TYPED.items()) or "(nothing typed)"
    return {"title": f"Agent wants to click '{name}' on {page.url.split('/')[-1]}", "details": f"Values it entered: {fields}"}

# %% Setup 6: STEP 3 -- the tool-INDEPENDENT mechanics only (copied verbatim, selected lines,
# from agent.ipynb STEP 3). Replay has no LLM in the loop, so the @tool-decorated wrappers
# themselves (observe, click, type_text, type_secret, select_option, page_text, ask_human,
# request_value, request_missing_values, finish) are NOT copied -- only the underlying mechanism
# every one of them (and, below, PlaywrightReplaySurface) actually depends on: the lock-bypass
# helper, the PlaywrightSurface method patches, the one shared surface instance, the live-value
# reader, and the risk classifier `human_takeover`'s own block_risky path calls.
TYPED: dict[str, str] = {}      # what was typed, by field name (shown in the approval bar's details)


async def _unlocked(coro):
    """Run one Playwright action with the general lock (Setup 5) removed for just that instant.
    force=True alone does NOT bypass the lock: Playwright still dispatches the click/fill by
    coordinate ('use page.mouse over the center of the element', per its own docs), so the real
    browser hit-tests normally and the lock overlay -- being on top -- would receive it instead
    of our intended target. Genuinely removing the lock, only for this one action, is what
    actually works."""
    await page.evaluate(UNLOCK_JS)
    try:
        return await coro
    finally:
        await page.evaluate(LOCK_JS)


async def _click(self, ref: int):
    await _unlocked(self.page.locator(f'[data-cua-ref="{ref}"]').click(timeout=5000, force=True))
    await self.page.wait_for_timeout(600)
    try:
        await self.page.wait_for_load_state("load", timeout=5000)
    except Exception:
        pass

async def _type_text(self, ref: int, text: str):
    await _unlocked(self.page.locator(f'[data-cua-ref="{ref}"]').fill(text, timeout=5000, force=True))

async def _page_text(self) -> str:
    return (await self.page.inner_text("body"))[:4000]

PlaywrightSurface.click = _click
PlaywrightSurface.type_text = _type_text
PlaywrightSurface.page_text = _page_text
surface = PlaywrightSurface(page)


async def current_value(ref: int) -> str:
    """Read whatever is currently in this field, live from the page. Empty string if none or unreadable."""
    try:
        loc = page.locator(f'[data-cua-ref="{ref}"]')
        tag = await loc.evaluate("el => el.tagName.toLowerCase()")
        if tag == "select":
            return (await loc.evaluate("el => el.selectedOptions[0] ? el.selectedOptions[0].text : ''")).strip()
        return (await loc.input_value(timeout=1000)).strip()
    except Exception:
        return ""


SAFE_SUBMITS = {"log in", "find transactions"}   # buttons that do not change data
AUTO_LIMIT = None                                # None = always ask a human. Later: 500.0 for small transfers


def _amount() -> float:
    raw = TYPED.get("amount", "").replace("$", "").replace(",", "")
    try:
        return float(raw)
    except ValueError:
        return float("inf")                      # unknown amount counts as risky


def needs_human(ref: int) -> bool:
    """Every button except a short safe list needs a human. Links (navigation) run freely."""
    el = next((e for e in surface.last_elements if e["ref"] == ref), None)
    role = (el or {}).get("role")
    name = ((el or {}).get("name") or "").strip().lower()
    risky = bool(el) and (bool(el.get("submit")) or role == "button") and name not in SAFE_SUBMITS
    if risky and "transfer" in name and AUTO_LIMIT is not None and _amount() <= AUTO_LIMIT:
        risky = False
    return risky

# %% Setup 7: the descriptor + labeled-value JS (copied verbatim from 03_recorder.py BROWSER 8 --
# NOT from agent.ipynb, which has no reason to carry these; the recorder already built and tested
# this exact mechanism for finding a live element's label/container/nth/duplicate counts and for
# reading "the value next to this label". Reused here rather than inventing a second
# implementation, per D78.)
HEADING_JS = """
() => {
  const vis = (e) => { const r = e.getBoundingClientRect(), s = getComputedStyle(e); return r.width > 1 && r.height > 1 && s.visibility !== 'hidden' && s.display !== 'none'; };
  const pick = (q) => Array.from(document.querySelectorAll(q)).find(vis);
  const el = pick('h1') || pick('.title') || pick('h2');
  return ((el && el.innerText) || document.title || '').replace(/\\s+/g, ' ').trim().slice(0, 80);
}
"""

# The value shown next to a label: the cell after it, the input a <label> points at, or the next
# sibling. `matches` (how many elements on the page carry this exact label text) is D68's
# duplicate-label signal for extract steps.
# D87 (Problem 1 fix): mirrors 03_recorder.py BROWSER 8's READ_LABELED_JS exactly -- `bare()` now
# strips ONE trailing non-alphanumeric "decoration" character (a strict superset of the old
# colon-only rule), so a declared label like "Balance" matches the real page's "Balance*". This
# copy must stay byte-identical to the recorder's (per this file's own comment above); keep both
# in sync if either changes again.
READ_LABELED_JS = """
(label) => {
  const norm = (s) => (s || '').replace(/\\s+/g, ' ').trim();
  const bare = (s) => norm(s).replace(/[^a-zA-Z0-9]$/, '').toLowerCase();
  const want = bare(label);
  const vis = (e) => { const r = e.getBoundingClientRect(); return r.width > 1 && r.height > 1; };
  const all = Array.from(document.body.querySelectorAll('td, th, dt, label, b, strong, span, div, p, li')).filter(vis);
  const hits = all.filter(e => bare(e.innerText || e.textContent) === want &&
                               !Array.from(e.children).some(c => bare(c.innerText || c.textContent) === want));
  const valueOf = (el) => {
    const cell = el.closest('td, th, dt');
    if (cell && cell.nextElementSibling) return norm(cell.nextElementSibling.innerText);
    if (el.tagName === 'LABEL' && el.htmlFor) { const t = document.getElementById(el.htmlFor); if (t) return norm(t.value || t.innerText); }
    if (el.nextElementSibling) return norm(el.nextElementSibling.innerText);
    let n = el.nextSibling;
    while (n) { const t = norm(n.textContent); if (t) return t; n = n.nextSibling; }
    return '';
  };
  for (const h of hits) { const v = valueOf(h); if (v) return { value: v, matches: hits.length }; }
  return { value: '', matches: hits.length };
}
"""

# One element's RICH descriptor (role, name, name_source, label, container, nth, and duplicate
# counts). Deliberately mirrors agent.ipynb's OWN roleOf/nameOf (Setup 4) so 'name' means the same
# thing here as it does to the model and to the recorder; labelOf/containerOf are the recorder's
# own additions (agent.ipynb never needed them).
DESCRIBE_JS = """
(ref) => {
  const norm = (s) => (s || '').replace(/\\s+/g, ' ').trim();
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
  const nameInfo = (el) => {
    const aria = norm(el.getAttribute('aria-label')); if (aria) return [aria, 'aria'];
    if (el.labels && el.labels.length) { const t = norm(el.labels[0].innerText); if (t) return [t, 'label']; }
    const t = el.tagName.toLowerCase(), ty = (el.getAttribute('type') || '').toLowerCase();
    if (t === 'input' && ['submit', 'button', 'reset'].includes(ty)) { const v = norm(el.value); if (v) return [v, 'value']; }
    const txt = norm(el.innerText).slice(0, 80); if (txt) return [txt, 'text'];
    for (const a of ['placeholder', 'title', 'alt']) { const v = norm(el.getAttribute(a)); if (v) return [v, 'attr_acc']; }
    const nm = el.getAttribute('name') || el.id; if (nm) return [nm, 'attr'];
    return ['', 'none'];
  };
  const formCtl = (el) => ['INPUT', 'SELECT', 'TEXTAREA'].includes(el.tagName);
  const labelOf = (el, role) => {
    if (!formCtl(el) || role === 'button') return '';
    if (el.labels && el.labels.length) return norm(el.labels[0].innerText).slice(0, 60);
    const cell = el.closest('td, th, dd');
    const prev = cell && cell.previousElementSibling;
    return prev ? norm(prev.innerText).slice(0, 60) : '';
  };
  const containerOf = (el) => {
    const form = el.closest('form, [role=form]');
    const tbl = el.closest('table, [role=table], [role=grid]');
    const c = formCtl(el) || el.tagName === 'BUTTON' ? (form || tbl) : (tbl || form);
    if (!c) return [null, null];
    const isForm = c === form;
    let name = norm(c.getAttribute('aria-label'));
    if (!name && !isForm) { const cap = c.querySelector('caption'); if (cap) name = norm(cap.innerText); }
    if (!name && isForm) { const lg = c.querySelector('legend'); if (lg) name = norm(lg.innerText); }
    const tag = el.tagName.toLowerCase();
    const nth = Array.from(c.querySelectorAll(tag)).indexOf(el) + 1;
    return [{ role: isForm ? 'form' : 'table', name: name || null }, nth || null];
  };
  const all = Array.from(document.querySelectorAll('[data-cua-ref]'));
  const target = all.find(el => el.getAttribute('data-cua-ref') === String(ref));
  if (!target) return null;
  const role = roleOf(target), ni = nameInfo(target), label = labelOf(target, role);
  const name = ni[0], name_source = ni[1];
  const nameCount = name ? all.filter(el => roleOf(el) === role && nameInfo(el)[0] === name).length : 1;
  const labelCount = label ? all.filter(el => labelOf(el, roleOf(el)) === label).length : 1;
  const cn = containerOf(target);
  return {
    role, name, name_source, label: label || null,
    text: (!formCtl(target) ? (norm(target.innerText).slice(0, 80) || null) : null),
    tag: target.tagName.toLowerCase(), type: (target.getAttribute('type') || '').toLowerCase() || null,
    submit: (target.tagName === 'BUTTON' && target.type !== 'button') ||
            (target.tagName === 'INPUT' && ['submit', 'image'].includes((target.getAttribute('type') || '').toLowerCase())),
    options: target.tagName === 'SELECT' ? Array.from(target.options).map(o => o.text.trim()).slice(0, 15) : null,
    container: cn[0], nth: cn[1], name_count: nameCount || 1, label_count: labelCount || 1,
  };
}
"""


async def current_heading() -> str:
    try:
        return await page.evaluate(HEADING_JS)
    except Exception:
        return ""


async def describe_ref(ref: int) -> dict | None:
    try:
        return await page.evaluate(DESCRIBE_JS, ref)
    except Exception:
        return None


async def read_labeled_value(page, label: str) -> str:
    """The value shown next to `label` on the current page. Raises LookupError if there is none.
    Same mechanism the recorder itself uses (D46), so record and replay read values the same way."""
    res = await page.evaluate(READ_LABELED_JS, label)
    if not res["value"]:
        raise LookupError(f"no value found next to the label {label!r}")
    return res["value"]


print("descriptor/heading/labeled-value helpers ready (from 03_recorder.py BROWSER 8)")

# %% Load the replay engine: Sections 1-4, 7-9 of 04_replay_engine.py
import pathlib


def _find_repo_for_engine() -> pathlib.Path:
    here = pathlib.Path.cwd()
    for p in [here, *here.parents]:
        if (p / "notebooks" / "04_replay_engine.py").exists():
            return p
    raise FileNotFoundError("cannot find notebooks/04_replay_engine.py. Start the kernel in the repo.")


def load_replay_engine(wanted=("Section 1:", "Section 2:", "Section 3:", "Section 4:",
                                "Section 7:", "Section 8:", "Section 9:")) -> None:
    """Exec the non-check cells of 04_replay_engine.py into this namespace -- the same
    exec-cells-into-namespace technique 04_replay_engine.py's own Section 1 already uses to load
    02_artifact_schema.py, and 03_recorder.py's load_schema() also uses. "Section 1:" of
    04_replay_engine.py itself defines REPO/EX/load_schema and loads the Phase 2 v2 schema, so
    running it here gives this notebook Capability/Target/ReplayResult/from_yaml/etc for free.
    Loads, in order: the schema (Section 1), ReplaySurface/exceptions (Section 2), resolve_target
    + the shared pure `_target_locators` (Section 3), run_capability + the shared pure
    `_find_outcome_rule` (Section 4, unused directly here but harmless to load), AsyncReplaySurface
    (Section 7), resolve_target_async + `_call_escalate` (Section 8), run_capability_async
    (Section 9). Skips every `*b`-suffixed checks cell and Sections 5/6/9b/10 (FakeSurface-only
    tests and the async mirror's own markdown/offline integration check) -- this notebook never
    touches FakeSurface."""
    repo = _find_repo_for_engine()
    text = (repo / "notebooks" / "04_replay_engine.py").read_text()
    for cell in re.split(r"(?m)^# %%", text)[1:]:
        header, _, body = cell.partition("\n")
        if header.strip().startswith(wanted):
            exec(compile(body, f"04_replay_engine.py [{header.strip()}]", "exec"), globals())


load_replay_engine()
print("replay engine loaded:", run_capability_async.__name__, "| schema:", Capability.__name__, "| repo:", REPO.name)

# %% [markdown]
# ## `PlaywrightReplaySurface` -- `AsyncReplaySurface`, for real
#
# **Assumes ONE global `page`** (Setup 2 above), exactly like `agent.ipynb` and `03_recorder.py`
# both do: `_unlocked`, `human_takeover`, `describe_ref`, and the global `surface` all close over
# that same module-level `page`, not a constructor parameter. Do not construct this class with a
# different `Page` object -- the lock would then apply to the wrong tab. This is not a new
# limitation; it is the same single-page assumption the rest of this codebase already makes.

# %% PlaywrightReplaySurface
@dataclass(frozen=True)
class LabeledValueRef:
    """A `resolve()` result for a `labeled_value` locator: not a numbered element ref -- a
    labeled-value read never depends on page position (D46) -- just the label text, re-read live
    by `read_value` every time it is needed."""
    label: str


class PlaywrightReplaySurface:
    """Implements AsyncReplaySurface (04_replay_engine.py Section 7) against the real browser.
    Wraps agent.ipynb's own PlaywrightSurface/lock mechanism -- nothing here is a second
    implementation of clicking, typing, selecting, or locking (D78)."""

    def __init__(self, page):
        self.page = page

    async def navigate(self, path: str) -> None:
        url = BASE + path
        if not host_allowed(url):
            # D80: run_capability_async's step loop only catches ResolutionError/TransientFailure
            # today (D77, unchanged from run_capability) -- there is no "policy blocked" bucket to
            # return a FAILED ReplayResult through. Raising here propagates uncaught, an honestly
            # documented gap rather than a silent off-host navigation (D15 forbids the latter
            # outright).
            raise PermissionError(f"host not allowed by ALLOWED_HOSTS: {url}")
        await self.page.goto(url)

    # D88 (Problem 2 fix): a bounded poll budget for `resolve()`'s own real-page timing, separate
    # from and unrelated to 04_replay_engine.py's step-level TransientFailure retry (D26) -- that
    # one retries a whole step after a raised exception; this one is `resolve()` re-checking the
    # live DOM a few times before it ever reports a miss at all. ParaBank's own Accounts Overview
    # page (confirmed from its real <script>) renders its table body via a jQuery AJAX call that
    # runs AFTER the page's `load` event -- `page.goto`/`wait_for_load_state("load")` (this file's
    # `navigate`, above) can return well before that data exists, so a single immediate `resolve()`
    # attempt can race it.
    _RESOLVE_POLL_INTERVAL_S = 0.4
    _RESOLVE_POLL_BUDGET_S = 5.0

    async def _resolve_once(self, locator):
        """One resolution attempt, no retry -- the exact logic `resolve()` used before D88."""
        if locator.strategy == "labeled_value":
            res = await self.page.evaluate(READ_LABELED_JS, locator.label)
            return LabeledValueRef(label=locator.label) if res["value"] else None

        obs = await surface.observe()
        for el in obs.elements:
            desc = await describe_ref(el["ref"])
            if desc is not None and self._matches(locator, desc):
                return el["ref"]
        return None

    async def resolve(self, locator):
        """D78: for `labeled_value`, go straight to READ_LABELED_JS (no numbered scan at all --
        matches how the recorder itself reads a labeled value). For every other strategy, run the
        SAME numbered scan `PlaywrightSurface.observe()` does (this also keeps `surface.last_elements`
        in sync for `approval_info`/`needs_human`), then match each candidate's DESCRIBE_JS
        descriptor against the locator. Returns the first match, or None -- a miss is never
        swallowed here; resolve_target_async's own primary-then-fallback logic does the rest.

        D88: applied to BOTH branches above via `_resolve_once` -- not just `labeled_value`. The
        general numbered-scan branch is judged equally exposed: any page's interactive controls
        (not only a `labeled_value` target) can just as easily be inserted by a late-running script,
        and this poll is cheap (bounded, self-contained, no new dependency) relative to the cost of
        a wrongly-early FAILED on a page that was still loading. On a miss, wait
        `_RESOLVE_POLL_INTERVAL_S` and re-check, up to `_RESOLVE_POLL_BUDGET_S` total (wall-clock,
        so slow individual attempts count against the same budget rather than being retried
        unboundedly); once the budget is exhausted, return None -- today's behavior, unchanged."""
        loop = asyncio.get_event_loop()
        deadline = loop.time() + self._RESOLVE_POLL_BUDGET_S
        while True:
            found = await self._resolve_once(locator)
            if found is not None:
                return found
            if loop.time() >= deadline:
                return None
            await asyncio.sleep(self._RESOLVE_POLL_INTERVAL_S)

    @staticmethod
    def _container_matches(within, container: dict | None) -> bool:
        if within is None:
            return True
        if container is None:
            return False
        if container.get("role") != within.role:
            return False
        return within.name is None or container.get("name") == within.name

    def _matches(self, locator, desc: dict) -> bool:
        strategy = locator.strategy
        if strategy == "role":
            return (desc["role"] == locator.role and desc["name"] == locator.name
                    and self._container_matches(locator.within, desc.get("container")))
        if strategy == "label":
            # D68's own stated gap: no `within` slot exists on this strategy. The first matching
            # descriptor wins -- same ambiguity the recorder already documents and refuses to
            # silently paper over at record time; not newly introduced, not closed, here either.
            return desc.get("label") == locator.label
        if strategy == "text":
            return (desc.get("text") == locator.text
                    and self._container_matches(locator.within, desc.get("container")))
        if strategy == "structure":
            return (self._container_matches(locator.within, desc.get("container"))
                    and desc.get("tag") == locator.tag and desc.get("nth") == locator.nth)
        return False   # labeled_value never reaches here -- handled directly in resolve() above

    async def click(self, ref) -> None:
        await surface.click(ref)   # PlaywrightSurface.click (Setup 6): _unlocked + force=True

    async def type_text(self, ref, value: str) -> None:
        await surface.type_text(ref, value)   # PlaywrightSurface.type_text (Setup 6), same mechanism

    async def select_option(self, ref, value: str) -> None:
        # agent.ipynb never factors this onto PlaywrightSurface either -- its own select_option
        # TOOL (STEP 3) calls this exact line inline. Wrapped here unchanged, not reinvented.
        await _unlocked(self.page.locator(f'[data-cua-ref="{ref}"]').select_option(label=value, timeout=5000, force=True))

    async def read_value(self, ref) -> str:
        if isinstance(ref, LabeledValueRef):
            return await read_labeled_value(self.page, ref.label)
        value = await current_value(ref)   # form value first (agent.ipynb's own current_value, Setup 6)
        if value:
            return value
        # Not a form control -- e.g. a `text`-strategy extract target such as transfer_funds'
        # "Transfer Complete!" confirmation heading. current_value only reads input_value /
        # selectedOptions, so fall back to the element's own live visible text (D81).
        try:
            return (await self.page.locator(f'[data-cua-ref="{ref}"]').inner_text(timeout=1000)).strip()
        except Exception:
            return ""

    async def current_url(self) -> str:
        return self.page.url

    async def page_text(self) -> str:
        return (await self.page.inner_text("body"))[:4000]   # same truncation agent.ipynb's page_text tool uses


live_surface = PlaywrightReplaySurface(page)
print("PlaywrightReplaySurface ready, backed by the single global page/surface")

# %% [markdown]
# ## Wiring `escalate` to the real decision bar (D79, corrected by D85)
#
# `run_capability_async`'s risky-click branch calls `escalate(reason, ctx)` and now consults its
# return value (D85): exactly the string `"approve"` means "proceed" -- the ENGINE resolves the
# target itself (via `resolve_target_async`, the exact same code path a normal click step already
# uses) and clicks it, then continues on to the capability's remaining steps. Anything else
# (including `None`, the default) leaves the engine's behavior exactly as before: it stops and
# returns `NEEDS_APPROVAL` without ever touching the page.
#
# `make_escalate` below therefore only shows the decision bar and REPORTS the human's choice --
# it must never click anything itself; that would be a second, competing click path now that the
# engine performs the click on approval (D28's "hold the session open" design is still satisfied:
# the session stays open, and the engine's own click happens in it once `escalate` says
# `"approve"`).
#
# - **Approve** -> return the string `"approve"`. No click here; the engine performs it.
# - **Reject** -> return `None`, print the same rejection message as before.
# - **Take over** -> the same `human_takeover(auto_on_navigate=True, block_risky=False)` call
#   `agent.ipynb`'s own `click()` tool uses for its take-over-to-submit case, then return `None`
#   (not `"approve"`) -- the engine cannot safely assume the click happened just because a human
#   took over, so this stays the same honest, conservative `NEEDS_APPROVAL` outcome as before.
#
# **Corrected (D85):** approving a real payment now results in `SUCCESS` with the real
# confirmation text and a verified checkpoint -- not `NEEDS_APPROVAL` -- because the engine
# itself continues past the click instead of returning immediately. Rejecting still returns
# `NEEDS_APPROVAL`, and a caller reading only `result.status` still cannot distinguish "rejected"
# from "took over" (both leave `status` at `NEEDS_APPROVAL`); distinguishing those two still needs
# the `[escalate] ...` line this prints, or the live page -- D79's honestly-stated limitation for
# that specific pair, not for Approve any more.

# %% make_escalate
async def _show_decision(title: str, details: str) -> str:
    """Runs the SAME DECISION_JS bar agent.ipynb's click() tool shows. The general lock (Setup 5)
    is already active by default, so a human cannot act on the real page while this bar is up --
    only the bar itself (its own higher z-index) is interactive, exactly as D57 established."""
    return await page.evaluate(DECISION_JS, {"title": title, "details": details})


def make_escalate(cap: "Capability"):
    """Returns an escalate(reason, ctx) closure for this one capability. Passed as
    run_capability_async's `escalate=` argument.

    D85: for the risky-click case, this closure only shows the decision bar and REPORTS the
    human's choice -- it must never click anything itself any more. The engine (D85) is what
    resolves the target and clicks it, and only when this returns exactly the string "approve"."""

    async def escalate(reason: str, ctx: dict) -> str | None:
        step_index = ctx.get("step_index")
        step = cap.steps[step_index] if step_index is not None else None

        if step is not None and getattr(step, "action", None) == "click" and step.risk == "risky":
            ref = await resolve_target_async(live_surface, step.target)
            info = approval_info({"ref": ref})          # reuses agent.ipynb's own title-building
            info["details"] = f"Reason: {reason}"        # TYPED is empty during replay; show the real reason instead
            choice = await _show_decision(info["title"], info["details"])
            if choice == "a":
                print(f"[escalate] APPROVED -- ref={ref} ({surface.name_of(ref)!r}); the engine will click it")
                return "approve"
            elif choice == "r":
                print(f"[escalate] REJECTED -- no action taken. reason: {reason}")
                return None
            else:
                report = await human_takeover(question="", auto_on_navigate=True, block_risky=False)
                print(f"[escalate] TAKE OVER -- a human acted directly. {report}")
                return None   # a human took over; the engine must not also click on our say-so

        # A hard failure (checkpoint / outcome-rule / resolution / retries-exhausted). Nothing to
        # click here -- run_capability_async already returns FAILED regardless of what a human
        # does with this bar; it exists only to make the failure visible in the live browser.
        await _show_decision("REPLAY needs your attention", reason)
        print(f"[escalate] acknowledged: {reason} | context: {ctx}")
        return None

    return escalate


print("make_escalate ready")

# %% Run helper: replay a saved capability against the real browser
async def replay_live(cap_path, inputs: dict[str, str], *, auto_approve_limit: float = 500.0) -> "ReplayResult":
    """Load a capability YAML and replay it for real, printing the result. `secrets` is always
    `resolve_secret` (D32): a secret VALUE is never printed, logged, or placed in anything this
    function returns or prints -- only its NAME ever appears, if at all."""
    cap = from_yaml(pathlib.Path(cap_path).read_text())
    result = await run_capability_async(
        cap, live_surface, inputs, resolve_secret,
        auto_approve_limit=auto_approve_limit, escalate=make_escalate(cap), logger=print,
    )
    print("REPLAY RESULT:", result.status, result.outputs or result.outcome or result.reason or result.failure)
    return result


print("replay_live ready. Example: await replay_live(EX / 'get_account_balance.yaml', {'account_id': '<YOUR ACCOUNT ID>'})")

# %% Run pay_bill.yaml (example)
login_result = await replay_live(REPO / "artifacts" / "examples" / "login_parabank.yaml", {})
print("login status:", login_result.status)

result = await replay_live(
    REPO / "artifacts" / "pay_bill.yaml",
    {
        "payee_name": "Nagarjuana",
        "payee_account": "12345",
        "amount": "20.00",
    },
)
result
