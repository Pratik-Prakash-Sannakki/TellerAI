# ruff: noqa: E501  (the page scripts are verbatim copies of the notebooks' JS)
"""Native dropdowns (D-B, the ONE non-visual exception): a native <select>'s list is drawn by the
OS outside the page, so no screenshot shows it and no key moves it. For the <select> under (or
next to) a point only, we read its options and set it by value. Everything else stays visual.

Each side keeps its own scripts (user decision 2):

- discovery: ``DROPDOWNS_WITH_BOX_JS`` (discovery.py 641-647, also returns each select's centre
  ``at`` and ``box``), ``SELECT_AT_POINT_JS`` (997-1017: the select at a point, option matched by
  "contains"), ``list_options``/``choose_option_at_point`` (1020-1035).
- replay: ``DROPDOWNS_JS`` (replay.py 354-356, values only), ``SELECT_AT_INDEX_JS`` (650-671: the
  Nth select when an index is recorded, option matched exactly), ``choose_option_at_index``
  (697-705).

The on-screen confirm differs per side (discovery: ``norm(option) in norm(read_near(...))``;
replay: ``shows_option(read_field(...), option)``), so it is a ``confirm(look, point, option)``
callback; ``look_fn`` is the side's own take_look (which also stores the look). Replay's
``stash_dropdowns`` (it writes STATE) stays replay-side and calls :func:`read_dropdowns`.
"""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable

from playwright.async_api import Error as PlaywrightError
from playwright.async_api import Page

from cua.browser.session import Session
from cua.vision.look import Look

LookFn = Callable[[], Awaitable[Look]]
Confirm = Callable[[Look, tuple[int, int], str], bool]
Dropdown = dict[str, object]

DROPDOWNS_WITH_BOX_JS = """() => [...document.querySelectorAll('select')].map(s => {
  const r = s.getBoundingClientRect();
  return {value: s.value, text: s.options[s.selectedIndex]?.text.trim() ?? '',
          options: [...s.options].map(o => o.text.trim()),
          at: r.width && r.height ? [r.left + r.width / 2, r.top + r.height / 2] : null,
          box: [r.left, r.top, r.right, r.bottom]};
})"""

DROPDOWNS_JS = """() => [...document.querySelectorAll('select')].map(s => ({
  value: s.value, text: s.options[s.selectedIndex]?.text.trim() ?? '',
  options: [...s.options].map(o => o.text.trim())}))"""

SELECT_AT_POINT_JS = """([x, y, want]) => {
  let el = document.elementFromPoint(x, y)?.closest('select');
  if (!el) {            // pointed at its label: take the nearest dropdown within 250px
    let best = 250;
    for (const s of document.querySelectorAll('select')) {
      const r = s.getBoundingClientRect();
      const d = Math.hypot(Math.max(r.left - x, 0, x - r.right), Math.max(r.top - y, 0, y - r.bottom));
      if (d < best) { best = d; el = s; }
    }
  }
  if (!el) return null;
  const opts = [...el.options].map(o => o.text.trim());
  if (want === null) return opts;
  const i = opts.findIndex(t => t.toLowerCase().includes(want.toLowerCase()));
  if (i < 0) return false;
  el.selectedIndex = i;
  el.dispatchEvent(new Event('input', {bubbles: true}));
  el.dispatchEvent(new Event('change', {bubbles: true}));
  const r = el.getBoundingClientRect();
  return [r.left + r.width / 2, r.top + r.height / 2, [...document.querySelectorAll('select')].indexOf(el)];
}"""

SELECT_AT_INDEX_JS = """([x, y, want, index]) => {
  let el = index === null ? document.elementFromPoint(x, y)?.closest('select')
                          : document.querySelectorAll('select')[index];
  if (!el && index === null) {
    let best = 250;
    for (const s of document.querySelectorAll('select')) {
      const r = s.getBoundingClientRect();
      const d = Math.hypot(Math.max(r.left - x, 0, x - r.right), Math.max(r.top - y, 0, y - r.bottom));
      if (d < best) { best = d; el = s; }
    }
  }
  if (!el) return null;
  const opts = [...el.options].map(o => o.text.trim());
  if (want === null) return opts;
  const i = opts.indexOf(want);
  if (i < 0) return false;
  el.selectedIndex = i;
  el.dispatchEvent(new Event('input', {bubbles: true}));
  el.dispatchEvent(new Event('change', {bubbles: true}));
  const r = el.getBoundingClientRect();
  return [r.left + r.width / 2, r.top + r.height / 2, el.options[el.selectedIndex].text.trim()];
}"""


async def read_dropdowns(page: Page, script: str, timeout_s: float) -> list[Dropdown]:
    """The page's dropdowns, read BEFORE an action (never while guard_send holds a request: then a
    page read never returns). Bounded: empty on a timeout or error."""
    try:
        found: list[Dropdown] = await asyncio.wait_for(page.evaluate(script), timeout_s)
        return found
    except (TimeoutError, PlaywrightError):
        return []


async def list_options(
    page: Page, point: tuple[float, float], hide: Callable[[str], str]
) -> list[str]:
    """Every option of the dropdown at this page point ([] if it is not a dropdown).
    (Discovery's ``list_options``; ``point`` is already in page points, ``hide`` its hide_secrets.)
    """
    return [hide(o) for o in (await page.evaluate(SELECT_AT_POINT_JS, [*point, None]) or [])]


async def choose_option_at_point(
    session: Session,
    point: tuple[float, float],
    option: str,
    *,
    look_fn: LookFn,
    confirm: Confirm,
) -> int | None:
    """Select the first option containing this text in the dropdown at (or next to) this page
    point; OCR of the dropdown's own box confirms it. The dropdown's index among the page's
    <select>s (replay picks it by that), or None."""
    page = session.page
    at = await page.evaluate(SELECT_AT_POINT_JS, [*point, option])
    if not isinstance(at, list):
        return None
    await page.wait_for_timeout(session.cfg.settle_ms)
    look = await look_fn()
    shown = confirm(look, (round(at[0] / look.scale), round(at[1] / look.scale)), option)
    return int(at[2]) if shown else None


async def choose_option_at_index(  # noqa: PLR0913 (constraints allow 6)
    session: Session,
    point: tuple[float, float],
    option: str,
    index: int | None,
    *,
    look_fn: LookFn,
    confirm: Confirm,
) -> bool:
    """Select this exact live option in the Nth <select> (``index``), else the one at the page
    point; the dropdown's selected text and its OCR'd box confirm it. (Replay's ``choose_option``.)
    """
    page = session.page
    at = await page.evaluate(SELECT_AT_INDEX_JS, [*point, option, index])
    if not isinstance(at, list) or at[2] != option:
        return False
    await page.wait_for_timeout(session.cfg.settle_ms)
    look = await look_fn()
    return confirm(look, (round(at[0] / look.scale), round(at[1] / look.scale)), at[2])


__all__ = [
    "DROPDOWNS_JS",
    "DROPDOWNS_WITH_BOX_JS",
    "SELECT_AT_INDEX_JS",
    "SELECT_AT_POINT_JS",
    "choose_option_at_index",
    "choose_option_at_point",
    "list_options",
    "read_dropdowns",
]
