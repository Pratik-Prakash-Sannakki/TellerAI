"""The discovery agent: deep agents + Playwright tools, safety/lock/takeover mechanism.

Ported from ``notebooks/agent.ipynb`` (all 12 real cells). The notebook builds everything as
module-level globals set up across cells that must run in order (`page`, `surface`, `TYPED`,
`DECLINED`, `LOGIN_ATTEMPTS`, `HANDBACK`, ...) -- exactly the kind of Jupyter cell-order
dependency this port needs to remove. Here the same state lives on one `DiscoveryAgent` instance,
built by the async factory function `build_agent()` at the bottom of this module (no top-level
`await`, no Jupyter-specific assumptions), matching the same async-def-wrapping pattern already
used for the other notebooks in this session.

**What is a genuine port vs. what changed shape:**
- Every JS string, every safety rule, every tool's own logic is unchanged from agent.ipynb.
- The mutable globals become instance attributes of `DiscoveryAgent`; the free functions that
  closed over them (`click`, `type_text`, `human_takeover`, `needs_human`, ...) become bound
  methods. This is a structural change only -- no rule, guard, or order of operations differs.
- `PlaywrightSurface.click`/`type_text`/`page_text` were monkeypatched onto the class after the
  fact in the notebook (STEP 3), because STEP 1 and STEP 3 are different cells. Here they are
  just defined directly on the class, since there is no cell-order reason not to.

See DECISIONS.md D2-D6 (the loop), D14/D19/D20/D32-D34 (safety, escalation), D50-D69 (every real
bug found and fixed through live testing), and PHASE1.md for the design write-up this class
implements.
"""

from __future__ import annotations

import asyncio
import base64
import functools
import os
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from langchain.agents.middleware.types import AgentMiddleware

from cua.config import ALLOWED_HOSTS, BASE, SECRETS, host_allowed, resolve_secret
from cua.models import make_chat_model, model_name_for

if TYPE_CHECKING:
    from langchain_core.language_models import BaseChatModel

__all__ = [
    "Observation",
    "PlaywrightSurface",
    "DiscoveryAgent",
    "login_check",
    "missing_field_labels",
    "format_elements",
    "build_agent",
    "build_langchain_agent",
    "build_typesafe_middleware",
    "job_tool_names",
    "confidence_gate",
    "NEVER_HIDE",
    "JOB_EXTRA_TOOLS",
    "JOB_CRITERIA",
    "JOB_CONFIDENCE_THRESHOLD",
    "SYSTEM_PROMPT",
    "OBSERVE_JS",
    "DRAW_JS",
    "CLEAR_JS",
    "DECISION_JS",
    "LOCK_JS",
    "UNLOCK_JS",
    "BLOCK_JS",
    "UNBLOCK_JS",
    "RESTRICT_JS",
    "UNRESTRICT_JS",
    "BANNER_ONLY_JS",
    "SYNC_UI_JS",
    "HEADING_JS",
    "READ_LABELED_JS",
    "DESCRIBE_JS",
]

# ---------------------------------------------------------------------------
# Setup 4/4: numbered-element scanner JS (D2). STEP 1's options/submit patch is folded in
# directly (the notebook applies it as a post-hoc string patch in a later cell; here it is just
# part of the one definition, since nothing forces two separate cells any more).
# ---------------------------------------------------------------------------
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
        if e.get("value"):
            line += f' = {e["value"]!r}'      # already-typed content, so the model does not have to guess from pixels
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
    """The only place that touches Playwright directly. Agent tools talk to this."""

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

    async def click(self, ref: int) -> None:
        """The single unlocked click path every automated click (agent tool or replay) uses (D61)."""
        await _unlocked(self.page, self.page.locator(f'[data-cua-ref="{ref}"]').click(timeout=5000, force=True))
        await self.page.wait_for_timeout(600)
        try:
            await self.page.wait_for_load_state("load", timeout=5000)
        except Exception:
            pass

    async def type_text(self, ref: int, text: str) -> None:
        await _unlocked(self.page, self.page.locator(f'[data-cua-ref="{ref}"]').fill(text, timeout=5000, force=True))

    async def page_text(self) -> str:
        return (await self.page.inner_text("body"))[:4000]


# ---------------------------------------------------------------------------
# STEP 2: banner, takeover, Approve/Reject/Take-over decision bar (D14, D56-D62).
# ---------------------------------------------------------------------------
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

# Whole-page lock: while it is the agent's turn, a real human can neither click nor type anywhere
# on the page. Our own injected UI always sits on a higher z-index, so it stays usable regardless
# of lock state. Our OWN automated actions bypass this via `_unlocked` (D61), not `force=True`
# alone (D61 found `force=True` does not bypass a covering overlay for a coordinate-based click).
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

# Risky-element block (D56/D57/D60): separate from the general lock above. During a GENERAL
# takeover (filling in a field) the rest of the page opens up but the risky button must still
# stay non-interactive.
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

# Restrict to specific fields (D62): keep the general lock fully ACTIVE, and poke a hole for ONLY
# the given refs, used by request_value/request_missing_values, which know exactly which field(s)
# are needed.
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

# "You are in control" bar with a Done button. Runs on every page load (add_init_script); also
# applied immediately to the current page. Locked/unlocked state is driven by the SAME
# 'cua_takeover' sessionStorage flag, so both stay in sync across navigations for free (D59).
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

# ---------------------------------------------------------------------------
# BROWSER 8 (03_recorder.py) / Setup 7 (05_replay_live.py): descriptor, heading, and
# labeled-value JS. Ported here too (not duplicated a third time) since agent.py is now the one
# shared place both the recorder's CAPTURE glue and cua.live import these from.
# ---------------------------------------------------------------------------
HEADING_JS = """
() => {
  const vis = (e) => { const r = e.getBoundingClientRect(), s = getComputedStyle(e); return r.width > 1 && r.height > 1 && s.visibility !== 'hidden' && s.display !== 'none'; };
  const pick = (q) => Array.from(document.querySelectorAll(q)).find(vis);
  const el = pick('h1') || pick('.title') || pick('h2');
  return ((el && el.innerText) || document.title || '').replace(/\\s+/g, ' ').trim().slice(0, 80);
}
"""

# D87: bare() strips ONE trailing non-alphanumeric "decoration" character (not just a colon), so
# a declared label like "Balance" matches a real page's "Balance*" (a footnote asterisk).
# D101: `label_header`/`value_header` are a purely STRUCTURAL signal (DOM tag/role/ancestor only --
# never any cell's own text) added so `cua.recorder.compile_run` can later refuse a `labeled_value`
# extract step whose captured resolution is itself a header cell, not real row data -- the general
# shape of D89/D97/D100's recurring "Balance"/"Balance*" -> "Available Amount" bug. `valueOf`'s own
# reading logic (the text a REPLAY-equivalent read actually returns) is completely unchanged below;
# `valueElementOf` is a second, additive function that walks the exact same fallback order to name
# the ELEMENT `valueOf` read from, purely so `headerLike()` can be asked about it. This string must
# stay byte-identical to `notebooks/03_recorder.py`'s own copy (D78-style duplication discipline;
# see `tests/test_agent.py`'s parity test).
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
  const valueElementOf = (el) => {
    const cell = el.closest('td, th, dt');
    if (cell && cell.nextElementSibling) return cell.nextElementSibling;
    if (el.tagName === 'LABEL' && el.htmlFor) { return null; }
    if (el.nextElementSibling) return el.nextElementSibling;
    let n = el.nextSibling;
    while (n) { if (norm(n.textContent)) return (n.nodeType === 1 ? n : null); n = n.nextSibling; }
    return null;
  };
  const headerLike = (node) => {
    if (!node || node.nodeType !== 1) return false;
    if (node.tagName === 'TH') return true;
    if ((node.getAttribute('role') || '').toLowerCase() === 'columnheader') return true;
    if (node.closest && node.closest('thead')) return true;
    return false;
  };
  for (const h of hits) {
    const v = valueOf(h);
    if (v) {
      return {
        value: v, matches: hits.length,
        label_header: headerLike(h.closest('td, th, dt')) || headerLike(h),
        value_header: headerLike(valueElementOf(h)),
      };
    }
  }
  return { value: '', matches: hits.length, label_header: false, value_header: false };
}
"""

# One element's RICH descriptor (role, name, name_source, label, container, nth, duplicate
# counts). Never shown to the model -- only used by the recorder's CAPTURE glue and by replay's
# live locator resolution (D78). Deliberately mirrors OBSERVE_JS's own roleOf/nameOf.
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


async def _unlocked(page, coro):
    """Run one Playwright action with the general lock removed for just that instant (D61):
    `force=True` alone does NOT bypass the lock, since Playwright still dispatches the click/fill
    by coordinate and the lock overlay -- being on top -- would receive it instead of our
    intended target. Genuinely removing the lock, only for this one action, is what works."""
    await page.evaluate(UNLOCK_JS)
    try:
        return await coro
    finally:
        await page.evaluate(LOCK_JS)


# ---------------------------------------------------------------------------
# Pure functions with no page access -- kept standalone (not methods) so they can be unit-tested
# with plain dicts, no browser, exactly like the notebook's own offline reasoning about them.
# ---------------------------------------------------------------------------
LOGIN_FAILURE_TEXTS = ("could not be verified", "user does not exist", "invalid username or password")
LOGIN_ATTEMPT_LIMIT = 3


def login_check(attempts_so_far: int, page_text_after: str, limit: int = LOGIN_ATTEMPT_LIMIT):
    """Pure decision (D69): after a login click, should further attempts be blocked, and why."""
    attempts = attempts_so_far + 1
    failed_text = next((t for t in LOGIN_FAILURE_TEXTS if t in page_text_after.lower()), None)
    if failed_text:
        return attempts, True, f"the login page reported: '{failed_text}'"
    if attempts >= limit:
        return attempts, True, f"login was attempted {attempts} times with no success"
    return attempts, False, None


def missing_field_labels(elements: list[dict], hints: dict[str, str] | None = None) -> list[tuple[int, str]]:
    """Empty, visible, fillable fields, in page order. Pure: no browser, no network call."""
    hints = hints or {}
    out = []
    for e in elements:
        if not e["inViewport"] or e["role"] not in ("textbox", "combobox") or e.get("value"):
            continue
        ref = e["ref"]
        name = (e.get("name") or "").strip()
        hint = hints.get(str(ref), "").strip()
        label = f"{name} ({hint})" if name and hint else (name or hint or f"field {ref}")
        out.append((ref, label))
    return out


START_PAGES = {"overview.htm", "index.htm"}   # start pages: asking a human here is too early.
SAFE_SUBMITS = {"log in", "find transactions"}   # buttons that do not change data
DENY_LINKS = ("register", "lookup", "admin")
SENSITIVE_WORDS = ("ssn", "password", "social")


def page_name_from_url(url: str) -> str:
    """Page name from the URL: no query, no ;jsessionid=, no trailing slash, lower case."""
    return url.split("?")[0].split(";")[0].rstrip("/").rsplit("/", 1)[-1].lower()


# ---------------------------------------------------------------------------
# The discovery agent itself.
# ---------------------------------------------------------------------------
@dataclass
class DiscoveryAgent:
    """One discovery run's worth of browser control state (D33-D62). All state that used to be a
    module-level global in agent.ipynb (`TYPED`, `GIVEN`, `RESULT`, `DECLINED`,
    `LOGIN_ATTEMPTS`/`LOGIN_BLOCKED`, `HANDBACK`) now lives here instead, one instance per run."""

    page: object
    given_text: str = ""
    auto_limit: float | None = None   # None = always ask a human for a risky "transfer" click

    surface: PlaywrightSurface = field(init=False)
    typed: dict[str, str] = field(default_factory=dict)
    declined: set = field(default_factory=set)
    login_attempts: int = 0
    login_blocked: bool = False
    result: dict = field(default_factory=dict)
    _handback_event: asyncio.Event | None = field(default=None, init=False, repr=False)
    _act_lock: asyncio.Lock = field(default_factory=asyncio.Lock, init=False, repr=False)
    _ready: bool = field(default=False, init=False, repr=False)

    def __post_init__(self):
        self.surface = PlaywrightSurface(self.page)

    # ---- one-time setup: expose the handback bridge, install the lock, clear stale flags ----
    async def setup(self) -> None:
        if self._ready:
            return

        async def _handback():
            if self._handback_event:
                self._handback_event.set()

        await self.page.expose_function("__cua_handback", _handback)
        await self.page.add_init_script(SYNC_UI_JS)
        # sessionStorage lives in the BROWSER TAB. Force-clear any flag left over from an earlier,
        # possibly-interrupted run, so a fresh agent always starts from a known "not in takeover"
        # state regardless of the tab's history (D60).
        await self.page.evaluate("() => { sessionStorage.removeItem('cua_takeover'); sessionStorage.removeItem('cua_question'); }")
        await self.page.evaluate(SYNC_UI_JS)
        self._ready = True

    # ---- small pure-ish helpers ----
    def current_page(self) -> str:
        return page_name_from_url(self.page.url)

    def _amount(self) -> float:
        raw = self.typed.get("amount", "").replace("$", "").replace(",", "")
        try:
            return float(raw)
        except ValueError:
            return float("inf")   # unknown amount counts as risky

    def needs_human(self, ref: int) -> bool:
        """Every button except a short safe list needs a human. Links (navigation) run freely (D33)."""
        el = next((e for e in self.surface.last_elements if e["ref"] == ref), None)
        role = (el or {}).get("role")
        name = ((el or {}).get("name") or "").strip().lower()
        risky = bool(el) and (bool(el.get("submit")) or role == "button") and name not in SAFE_SUBMITS
        if risky and "transfer" in name and self.auto_limit is not None and self._amount() <= self.auto_limit:
            risky = False
        return risky

    def _describe(self, ref: int, hint: str = "") -> str:
        """Best available description of an element (D53): the code's own name, the model's
        visual hint, both together, or a last-resort 'field N'."""
        name = (self.surface.name_of(ref) or "").strip()
        hint = (hint or "").strip()
        if name and hint:
            return f"{name} ({hint})"
        return name or hint or f"field {ref}"

    async def current_value(self, ref: int) -> str:
        """Read whatever is currently in this field, live from the page (D54)."""
        try:
            loc = self.page.locator(f'[data-cua-ref="{ref}"]')
            tag = await loc.evaluate("el => el.tagName.toLowerCase()")
            if tag == "select":
                return (await loc.evaluate("el => el.selectedOptions[0] ? el.selectedOptions[0].text : ''")).strip()
            return (await loc.input_value(timeout=1000)).strip()
        except Exception:
            return ""

    def approval_info(self, args: dict) -> dict:
        name = self.surface.name_of(args["ref"])
        fields = "; ".join(f"{k}: {v}" for k, v in self.typed.items()) or "(nothing typed)"
        return {"title": f"Agent wants to click '{name}' on {self.page.url.split('/')[-1]}", "details": f"Values it entered: {fields}"}

    def _blocks(self, prefix: str, obs: Observation) -> list[dict]:
        """Package text and a screenshot as one tool result the model can read."""
        return [
            {"type": "text", "text": f"{prefix}\n{obs.as_text()}"},
            {"type": "image", "base64": base64.b64encode(obs.png).decode(), "mime_type": "image/png"},
        ]

    # ---- the human handoff mechanism (D14, D56-D62) ----
    async def human_takeover(self, question: str = "", auto_on_navigate: bool = False,
                              block_risky: bool = True, allow_refs: list[int] | None = None) -> str:
        """Give the live browser to a human. Returns when they click 'Done', OR, if
        auto_on_navigate is set, as soon as the page reloads at all.

        allow_refs, when given, is the STRICTEST mode (D62): the general lock stays fully ACTIVE,
        and only these specific elements are poked open. Without allow_refs, the whole page
        unlocks instead; block_risky=True (the default) then additionally blurs and disables every
        risky button (D56/D57), so a general takeover cannot bypass the approval step. The one
        call site that should pass block_risky=False is the take-over-to-submit case inside
        `click()`, since acting on that specific button is the entire point of that takeover.
        """
        page = self.page
        self._handback_event = asyncio.Event()
        visited: list[str] = []

        def on_nav(frame):
            if frame != page.main_frame:
                return
            visited.append(frame.url)
            if auto_on_navigate and not self._handback_event.is_set():
                self._handback_event.set()

        page.on("framenavigated", on_nav)
        await page.evaluate("([q]) => { sessionStorage.setItem('cua_takeover', '1'); sessionStorage.setItem('cua_question', q); }", [question])
        if allow_refs is not None:
            await page.evaluate(BANNER_ONLY_JS)
            await page.evaluate(RESTRICT_JS, allow_refs)
        else:
            await page.evaluate(SYNC_UI_JS)
            risky = [e["ref"] for e in self.surface.last_elements if e["inViewport"] and self.needs_human(e["ref"])] if block_risky else []
            if block_risky:
                await page.evaluate(BLOCK_JS, risky)
        await self._handback_event.wait()
        page.remove_listener("framenavigated", on_nav)
        if allow_refs is not None:
            await page.evaluate(UNRESTRICT_JS)
        elif block_risky:
            await page.evaluate(UNBLOCK_JS)
        try:
            await page.evaluate("sessionStorage.removeItem('cua_takeover'); sessionStorage.removeItem('cua_question');")
            await page.evaluate(SYNC_UI_JS)
        except Exception:
            pass   # the page likely moved on
        text = (await page.inner_text("body"))[:300].replace("\n", " ")
        return f"Pages the human visited: {visited or 'none'}. Page now: {page.url}. Page text: {text}"

    async def _ask_for_value(self, ref: int, field_name: str, kind: str) -> list:
        """The agent tried to enter a value the user never gave. Hand the browser to a human --
        unless the field already has a value, in which case refuse and say so (D54)."""
        val = await self.current_value(ref)
        if val:
            return self._blocks(
                f"SKIP: '{field_name}' already has a value ({val!r}). Do not ask about it again; move to a different field.",
                await self.surface.observe(),
            )
        report = await self.human_takeover(
            f"I need a value for '{field_name}' and you did not give me one. Please {kind} it yourself in the page, then click Done.",
            allow_refs=[ref],
        )
        return self._blocks(
            f"A human entered the value for '{field_name}' themselves. Do NOT type it again. {report}",
            await self.surface.observe(),
        )

    # ---- the browser tools (STEP 3, D33-D69) ----
    async def observe(self) -> list:
        return self._blocks("Current page.", await self.surface.observe())

    async def click(self, ref: int) -> list:
        name = (self.surface.name_of(ref) or "").strip().lower()
        if any(w in name for w in DENY_LINKS):
            return self._blocks(f"DENIED: '{name}' is not allowed.", await self.surface.observe())
        if name in self.declined:
            return self._blocks("DECLINED earlier by a human. Do not retry. Call finish with 'DECLINED:' and stop.", await self.surface.observe())
        if name == "log in" and self.login_blocked:
            return self._blocks("BLOCKED: login already failed or hit its attempt limit. Do not try again. Call finish with a summary starting 'STUCK:' and stop.", await self.surface.observe())
        if self.needs_human(ref):
            choice = await self.page.evaluate(DECISION_JS, self.approval_info({"ref": ref}))
            if choice == "r":
                self.declined.add(name)
                return self._blocks("DECLINED by a human. Do not retry or work around it. Call finish with 'DECLINED:' and stop.", await self.surface.observe())
            if choice == "t":
                report = await self.human_takeover(question="", auto_on_navigate=True, block_risky=False)
                return self._blocks(f"A human completed this step manually in the browser. {report} Do NOT click again. Check the result from the page text, then call finish.", await self.surface.observe())
            # choice == "a": approved, fall through.
        try:
            await self.surface.click(ref)
        except Exception as exc:
            return self._blocks(f"CLICK FAILED for [{ref}]: {type(exc).__name__}", await self.surface.observe())
        if not host_allowed(self.page.url):
            await self.page.go_back()
            return self._blocks("BLOCKED: left the allowed site. Went back.", await self.surface.observe())
        if name == "log in":
            page_text_after = await self.surface.page_text()
            self.login_attempts, blocked, reason = login_check(self.login_attempts, page_text_after)
            if blocked:
                self.login_blocked = True
                return self._blocks(
                    f"STOP: login failed ({reason}). Do not try again. Call finish with a summary starting 'STUCK:' explaining this.",
                    await self.surface.observe(),
                )
        return self._blocks(f"Clicked [{ref}].", await self.surface.observe())

    async def type_text(self, ref: int, text: str) -> list:
        field_name = self._describe(ref)
        if any(w in field_name.lower() for w in SENSITIVE_WORDS) or text.strip().lower() not in self.given_text.lower():
            return await self._ask_for_value(ref, field_name, "type")
        try:
            await self.surface.type_text(ref, text)
        except Exception as exc:
            return self._blocks(f"TYPE FAILED for [{ref}]: {type(exc).__name__}", await self.surface.observe())
        self.typed[field_name.lower()] = text
        return self._blocks(f"Typed into [{ref}].", await self.surface.observe())

    async def type_secret(self, ref: int, name: str) -> list:
        if name not in SECRETS:
            return self._blocks(f"UNKNOWN SECRET '{name}'. Use one of: {list(SECRETS)}", await self.surface.observe())
        if not host_allowed(self.page.url):
            return self._blocks("REFUSED: this site is not on the allowlist.", await self.surface.observe())
        try:
            await _unlocked(self.page, self.page.locator(f'[data-cua-ref="{ref}"]').fill(resolve_secret(name), timeout=5000, force=True))
        except Exception as exc:
            return self._blocks(f"FAILED for [{ref}]: {type(exc).__name__}", await self.surface.observe())
        return self._blocks(f"Typed secret '{name}' into [{ref}].", await self.surface.observe())

    async def select_option(self, ref: int, option: str) -> list:
        field_name = self._describe(ref)
        if option.strip().lower() not in self.given_text.lower():
            return await self._ask_for_value(ref, field_name, "choose")
        try:
            await _unlocked(self.page, self.page.locator(f'[data-cua-ref="{ref}"]').select_option(label=option, timeout=5000, force=True))
        except Exception as exc:
            return self._blocks(f"SELECT FAILED for [{ref}]: {type(exc).__name__}", await self.surface.observe())
        self.typed[field_name.lower()] = option
        return self._blocks(f"Selected '{option}' in [{ref}].", await self.surface.observe())

    async def page_text(self) -> str:
        return await self.surface.page_text()

    async def ask_human(self, question: str) -> list:
        if self.current_page() in START_PAGES:
            return self._blocks(
                "NOT YET: you are still on the start page. Open the page where this task is done first "
                "(use the menu). Then, with the form on screen, use request_value on each field you cannot fill.",
                await self.surface.observe(),
            )
        report = await self.human_takeover(question)
        return self._blocks(f"A human took over and handed back. {report}", await self.surface.observe())

    async def request_value(self, ref: int, hint: str) -> list:
        if self.current_page() in START_PAGES:
            return self._blocks(
                "NOT YET: you are still on the start page. Open the page that has this form first.",
                await self.surface.observe(),
            )
        field_name = self._describe(ref, hint)
        try:
            loc = self.page.locator(f'[data-cua-ref="{ref}"]')
            await loc.scroll_into_view_if_needed(timeout=3000)
            await loc.focus(timeout=3000)
        except Exception:
            pass
        return await self._ask_for_value(ref, field_name, "enter")

    async def request_missing_values(self, hints: dict[str, str] | None = None) -> list:
        hints = hints or {}
        if self.current_page() in START_PAGES:
            return self._blocks("NOT YET: open the page that has this form first.", await self.surface.observe())
        missing = missing_field_labels(self.surface.last_elements, hints)
        if not missing:
            return self._blocks("Nothing is missing right now.", await self.surface.observe())
        labels = [label for _, label in missing]
        question = "Please fill in these fields, then click Done: " + "; ".join(labels)
        report = await self.human_takeover(question, allow_refs=[ref for ref, _ in missing])
        return self._blocks(f"A human filled in what they chose to. {report}", await self.surface.observe())

    async def finish(self, summary: str, values: dict[str, str]) -> str:
        self.result.clear()
        self.result.update({"summary": summary, "values": values})
        return "Recorded. Stop now."

    def build_tools(self) -> list:
        """Wrap this instance's bound methods as langchain `@tool` functions -- the same tool
        names, docstrings, and signatures agent.ipynb's STEP 3 defines, closing over `self`
        instead of module globals."""
        from langchain.tools import tool

        agent = self

        def one_at_a_time(fn):
            @functools.wraps(fn)
            async def wrapper(*a, **k):
                async with agent._act_lock:
                    return await fn(*a, **k)
            return wrapper

        @tool(parse_docstring=True)
        @one_at_a_time
        async def observe() -> list:
            """Look at the current page.

            Returns:
                A screenshot with red numbered boxes, plus a text list of the numbered elements.
            """
            return await agent.observe()

        @tool(parse_docstring=True)
        @one_at_a_time
        async def click(ref: int) -> list:
            """Click an element on the page.

            Buttons that change data ask a human for approval first. You do not need to do anything for that.

            Args:
                ref: Number of the element in the latest screenshot and list.

            Returns:
                The new page state. If a human declined, the result says DECLINED and you must stop.
            """
            return await agent.click(ref)

        @tool(parse_docstring=True)
        @one_at_a_time
        async def type_text(ref: int, text: str) -> list:
            """Type normal text into an input box.

            Only type values the user gave you in the goal. Never invent a value.

            Args:
                ref: Number of the input box in the latest screenshot and list.
                text: The text to type. It must come from the user's goal.

            Returns:
                The new page state.
            """
            return await agent.type_text(ref, text)

        @tool(parse_docstring=True)
        @one_at_a_time
        async def type_secret(ref: int, name: str) -> list:
            """Type a stored secret into an input box, without ever seeing its value.

            Use this to log in. You give only the secret's name.

            Args:
                ref: Number of the input box in the latest screenshot and list.
                name: Secret name. Either 'username' or 'password'.

            Returns:
                The new page state. The value is never included.
            """
            return await agent.type_secret(ref, name)

        @tool(parse_docstring=True)
        @one_at_a_time
        async def select_option(ref: int, option: str) -> list:
            """Choose an option in a dropdown.

            Only choose options the user named in the goal. Never guess.

            Args:
                ref: Number of the dropdown in the latest screenshot and list.
                option: Visible text of the option, exactly as shown in its options list.

            Returns:
                The new page state.
            """
            return await agent.select_option(ref, option)

        @tool(parse_docstring=True)
        @one_at_a_time
        async def page_text() -> str:
            """Read the visible text of the whole page (balances, tables, messages).

            Returns:
                The page text, up to 4000 characters.
            """
            return await agent.page_text()

        @tool(parse_docstring=True)
        @one_at_a_time
        async def ask_human(question: str) -> list:
            """Ask a human for help by handing over the browser.

            Use this when you are unsure which element to pick, the page looks unexpected,
            a step failed twice, or you would have to guess. Never guess account choices or amounts.

            Args:
                question: What you are unsure about and what you need the human to do.

            Returns:
                What the human did, and the new page state.
            """
            return await agent.ask_human(question)

        @tool(parse_docstring=True)
        @one_at_a_time
        async def request_value(ref: int, hint: str) -> list:
            """Ask the human to fill one field that you cannot fill, because the user did not give the value.

            Open the page that has the field first. Then point at the field, and say what you see: read
            the label from the screenshot even if the element has no name in the code. This happens on
            older pages where a label sits in a nearby table cell or heading, not attached to the input.
            Your visual reading is what the human sees in the request, so give your best reading even if
            you are not fully sure. The page scrolls to the field, the human types the value there and
            hands control back. Do not type into that field yourself afterwards.

            Args:
                ref: Number of the field (input box or dropdown) in the latest screenshot and list.
                hint: What you see as this field's label or purpose, read from the screenshot.

            Returns:
                The new page state, after the human is done.
            """
            return await agent.request_value(ref, hint)

        @tool(parse_docstring=True)
        @one_at_a_time
        async def request_missing_values(hints: dict[str, str] = {}) -> list:
            """Ask a human to fill every empty field on the current page in one go.

            Use this once you have typed or chosen every value the user actually gave you, and the
            form still has empty fields left. Call this ONCE for all of them, rather than calling
            request_value field by field. If some fields are still empty after the human clicks Done,
            call this again: only the fields still empty will be shown, not the ones already filled.

            Args:
                hints: Optional. Maps a field's ref number (as text, e.g. "17") to your own reading of
                    its label, for fields with no clear name in the code.

            Returns:
                The new page state, after the human is done.
            """
            return await agent.request_missing_values(hints)

        @tool(parse_docstring=True)
        async def finish(summary: str, values: dict[str, str]) -> str:
            """Report the final result and stop.

            If you cannot make progress, start the summary with 'STUCK:'. If a human declined, start it with 'DECLINED:'.

            Args:
                summary: One-line summary of what you did or why you stopped.
                values: The requested facts, for example {"account_id": "13344", "balance": "$100.00"}.

            Returns:
                A confirmation. Stop after this.
            """
            return await agent.finish(summary, values)

        return [observe, click, type_text, type_secret, select_option, page_text,
                request_value, request_missing_values, ask_human, finish]


SYSTEM_PROMPT = """You are an expert browser operator. You drive a real browser on a banking demo site, and you can search the web for outside facts.

## Browser tools
Every tool result shows a screenshot with red numbered boxes plus a list of numbered elements. A field already filled shows its current value, e.g. [7] textbox "City" = '2'. Never ask about a field that already shows a value; move to one that does not. Dropdowns list their options. Refer to elements only by number. Numbers change after every action, so use the latest list.
- observe: look at the page.
- click(ref), type_text(ref, text), select_option(ref, option): act on elements.
- type_secret(ref, name): type a stored secret ('username' or 'password'). You never see the value.
- page_text: read the visible page text (balances, messages).
- request_value(ref, hint): ONE field you cannot fill. Prefer request_missing_values instead when several fields are empty.
- request_missing_values(hints): every empty field on the current page, asked in ONE go, not one at a time. hints maps a ref number to your own label reading, for fields with no name in the code.
- ask_human(question): only when you are unsure what to click. Not for missing values.
- finish(summary, values): report the result, logout and then stop.

## How to work
1. Call observe first. If you see a login form, log in with type_secret, then confirm the account overview appears.
2. Do the task by the shortest path. Read values with page_text and copy them exactly. Never invent a value.
3. Use ONLY values the user gave you in the goal. Never make one up. If values you need (payee, amount, account, address) are missing: FIRST open the page where the task is done (use the menu links), THEN call request_missing_values ONCE to ask for everything still empty at the same time. Never ask a human while you are still on the start page.
4. If a tool says a human entered a value, do not type it again. Continue with the next step.
5. Buttons that change data (Send Payment, Transfer, Open New Account, and so on) need a human. Click the button when the form is ready; the system asks the human for approval by itself. If the result says DECLINED, never retry or work around it: call finish with 'DECLINED:'.
6. Make ONE tool call at a time. Do not click into a field before typing.
7. Stay on the banking site. If you are lost or repeat the same action 3 times, call finish with 'STUCK:' and say why.
8. Attempt login at most 3 times. If the page says the login could not be verified, stop immediately -- do not retry. Call finish with a summary starting 'STUCK:' explaining what happened.
9. Do not use ls, read_file, write_file, edit_file, delete, glob, grep or task.
9. all steps must end with logout. STUCK or happy path or DECLINED, always logout after you finish. Do not leave the session open.
"""


async def build_agent(page=None, goal_text: str = "", *, auto_limit: float | None = None) -> DiscoveryAgent:
    """Build a ready-to-use `DiscoveryAgent`. If `page` is None, launches a real, visible
    Chromium browser on ParaBank's login page (agent.ipynb Setup 2) -- this is the one call in
    this module that actually needs Playwright installed and a network path to ParaBank.

    No top-level `await`: call this from an `async def` (a CLI command, a test, or a notebook
    cell wrapped the same way the other notebooks in this session already are)."""
    if page is None:
        from playwright.async_api import async_playwright

        pw = await async_playwright().start()
        browser = await pw.chromium.launch(headless=False)
        context = await browser.new_context(viewport={"width": 1280, "height": 900})
        page = await context.new_page()
        await page.goto(f"{BASE}/index.htm")

    agent = DiscoveryAgent(page, given_text=goal_text, auto_limit=auto_limit)
    await agent.setup()
    return agent


class NoopAnthropicPromptCachingMiddleware(AgentMiddleware):
    """Disable Anthropic prompt-caching on the Iliad gateway.

    The gateway rejects the Anthropic prompt-caching breakpoint metadata with a 500,
    even though plain ChatAnthropic calls succeed. We keep the middleware name stable
    so deepagents can replace the default middleware in-place without changing the rest
    of the stack.
    """

    name = "AnthropicPromptCachingMiddleware"

    def wrap_model_call(self, request, handler):
        return handler(request)

    async def awrap_model_call(self, request, handler):
        return await handler(request)


def build_langchain_agent(tools: list, *, model: "str | BaseChatModel | None" = None,
                          system_prompt: str = SYSTEM_PROMPT, middleware: list | None = None):
    """Wrap a tool list in a deep agent (D4) with the standard checkpointer. Kept as a thin,
    separate function (not part of `build_agent`) so `cua discover`'s CAPTURE-mode tool list
    (the base tools plus the recorder's own additive tools) can share this exact call, matching
    agent.ipynb's STEP 4 / 03_recorder.py's BROWSER 12.

    `model` defaults to `make_chat_model("sonnet")` (the Iliad gateway). A chat-model instance
    or a `provider:model` string is passed straight through: `create_deep_agent`'s own signature
    is `model: str | BaseChatModel | None`.

    The Iliad gateway rejects Anthropic prompt-caching metadata despite accepting straight
    ChatAnthropic calls, so this wrapper installs a no-op replacement for the default
    `AnthropicPromptCachingMiddleware` before `create_deep_agent` assembles the final stack.
    """
    from deepagents import create_deep_agent
    from langgraph.checkpoint.memory import MemorySaver

    middleware_list = [NoopAnthropicPromptCachingMiddleware()]
    if middleware:
        middleware_list.extend(middleware)

    return create_deep_agent(
        model=model if model is not None else make_chat_model("sonnet"),
        tools=tools,
        system_prompt=system_prompt,
        checkpointer=MemorySaver(),
        middleware=middleware_list,
    )


# ---------------------------------------------------------------------------
# Optional TypeSafe tool-selection + model-routing middleware (D50, D52, D76).
#
# D99: `build_langchain_agent`'s own `middleware` parameter (above) has existed since this was
# ported, but nothing in `src/cua/` ever actually BUILT a middleware list from it -- `cua.cli`'s
# `_run_discover` called `build_langchain_agent(tools, system_prompt=RECORDER_SYSTEM_PROMPT)` with
# no `middleware` argument at all, so it silently defaulted to `[]` on every single `cua discover`
# run, REGARDLESS of whether `TYPESAFE_API_KEY` was set in `.env`. `03_recorder.py`'s own BROWSER
# 11/12 (the reference implementation) builds `recorder_middleware` from
# `TypeSafeToolRouterMiddleware`/`ModelRouterMiddleware` and passes it into its own
# `create_deep_agent(..., middleware=recorder_middleware)` call. `src/cua/config.py` already had
# `TYPESAFE_API_KEY` (and, then, `HAIKU_MODEL`/`SONNET_MODEL` strings, now replaced by
# `cua.models.make_chat_model`, the Iliad gateway) defined (D93's shared config module) -- only the
# middleware CLASSES and the job-mapping/confidence-gate logic that decide what to build from them
# were never ported. This is that port: `job_tool_names`/`confidence_gate`/`NEVER_HIDE`/
# `JOB_EXTRA_TOOLS`/`JOB_CRITERIA` are copied verbatim from `03_recorder.py`'s OFFLINE 13b (itself
# copied from agent.ipynb's STEP 3d/3e), and `build_typesafe_middleware()` reproduces BROWSER 12's
# own `if TYPESAFE_API_KEY: ... else: ...` construction exactly, as a single, reusable, offline-
# testable function instead of inline notebook-cell code. Still off by default: with no
# `TYPESAFE_API_KEY` in `.env`, this returns `[]` and the agent behaves exactly as before.
NEVER_HIDE = {"observe", "click", "type_secret", "finish"}   # always allowed, whatever the job

JOB_EXTRA_TOOLS = {
    "login": {"type_secret"},
    "fill_form": {"type_text", "select_option"},
    "read_value": {"page_text"},
    "need_human": {"request_value", "ask_human"},
}
JOB_CRITERIA = {
    "login": "The page shows a username or password field, or we have not logged in yet.",
    "fill_form": "A form is on screen and a field still needs a value typed or a dropdown chosen.",
    "read_value": "We need to read a value already on the page, such as a balance or a confirmation message.",
    "need_human": "We are unsure which element to use, or a value we need was not given by the user.",
}
JOB_CONFIDENCE_THRESHOLD = 0.8


def job_tool_names(job: str, never_hide: frozenset[str] | set[str] = NEVER_HIDE) -> set[str]:
    """Tools this job needs, plus the always-allowed set. Pure: no network, no LLM."""
    return set(never_hide) | JOB_EXTRA_TOOLS.get(job, set())


def confidence_gate(base_tools: set[str], job: str, confidence: float,
                     never_hide: frozenset[str] | set[str] = NEVER_HIDE,
                     threshold: float = JOB_CONFIDENCE_THRESHOLD) -> set[str]:
    """Narrow base_tools to this job's tools, but only if the classifier is confident.
    Below the threshold, fail OPEN: return base_tools unchanged rather than guess wrong."""
    if confidence < threshold:
        return base_tools
    return base_tools & job_tool_names(job, never_hide)


def build_typesafe_middleware(agent: "DiscoveryAgent", *, extra_never_hide: set[str] | None = None) -> list:
    """Build the D50/D52 TypeSafe middleware list (tool router + model router), matching
    `03_recorder.py`'s BROWSER 11/12 wiring exactly. Returns `[]` if `TYPESAFE_API_KEY` is not set
    in `.env` -- the caller's agent then behaves exactly as before this function existed (one
    model, full tool list, D50's own "off by default" contract).

    `extra_never_hide` folds in caller-specific tool names that must never be stripped by the job
    router (D76: `03_recorder.py`'s own `extract_value`/`open_path`/`finish_business_outcome`/
    `request_missing_values`, which predate agent.ipynb's `JOB_EXTRA_TOOLS` mapping) -- `cua.cli`
    passes these for `cua discover`'s CAPTURE-mode tool list; a caller building a plain (non-
    capture) agent can omit it and get agent.ipynb's original 4-tool `NEVER_HIDE` unchanged."""
    key = os.getenv("TYPESAFE_API_KEY", "")
    if not key:
        print("model router OFF: no TYPESAFE_API_KEY in .env. Using Sonnet only:", model_name_for("sonnet"))
        return []

    from langchain.agents.middleware import AgentMiddleware
    from langchain_typesafe import Choice, TypeSafeClassifier
    from langchain_typesafe.experimental.middleware import ModelChoice, ModelRouterMiddleware

    never_hide = NEVER_HIDE | (extra_never_hide or set())

    class TypeSafeToolRouterMiddleware(AgentMiddleware):
        """Classifies the step's job with TypeSafe's Choice primitive and narrows the tool
        list to it. Sends the current page path and the last tool result's text to
        api.typesafe.ai (D50/D52 caveat: never enable on a run that may show real account
        data). Any error here (network, auth, timeout) fails OPEN: the request goes through
        unmodified."""

        def __init__(self, classifier, never_hide: set[str] = never_hide):
            self.classifier = classifier
            self.never_hide = never_hide   # instance attribute, not just a closure -- testable directly

        async def awrap_model_call(self, request, handler):
            try:
                state = f"page={page_name_from_url(agent.page.url)!r}. last result: {str(request.messages[-1].content)[:400]!r}"
                response = await self.classifier.ainvoke(
                    {"state": state, "questions": {"job": Choice(instructions="What kind of step is this?", criteria=JOB_CRITERIA)}}
                )
                answer = response.choices["job"]
                named = {t.name for t in request.tools if hasattr(t, "name")}
                keep = confidence_gate(named, answer.choice, answer.confidence, self.never_hide)
                request = request.override(tools=[t for t in request.tools if not hasattr(t, "name") or t.name in keep])
                print(f"typesafe job -> {answer.choice!r} confidence={answer.confidence:.2f} kept={sorted(keep)}")
            except Exception as exc:
                print(f"typesafe job router FAILED, continuing with no change: {type(exc).__name__}: {exc}")
            return await handler(request)

    recorder_router = ModelRouterMiddleware(
        choices={
            "fast": ModelChoice(
                model=make_chat_model("haiku"),
                criteria="A single simple step: reading the page, or one obvious click, type, or select with no ambiguity.",
            ),
            "powerful": ModelChoice(
                model=make_chat_model("sonnet"),
                criteria="Anything else: planning, choosing between several similar elements, forms, or any step before a risky click.",
            ),
        },
        instructions="Pick the cheapest model that can do the step correctly. If unsure, pick 'powerful'.",
    )
    print(f"model router ON (TypeSafe): fast={model_name_for('haiku')} | powerful={model_name_for('sonnet')}")
    return [TypeSafeToolRouterMiddleware(TypeSafeClassifier()), recorder_router]
