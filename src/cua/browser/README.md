# cua.browser

Playwright, no decisions: the open browser, the site lock, our own input, native dropdowns.

## Read order
1. `site_lock.py` - `SiteLock`: CDP `Input.setIgnoreInputEvents`. `open()` is the only unlock
   path and always re-locks, even on an exception.
2. `session.py` - `Session` (frozen: pw, context, site page, control page, hand-back extension
   worker or None, `BrowserConfig`, `SiteProfile`, `SiteLock`, `RefCounter`), `open_session()`
   (reuses a live `existing` session, so a notebook re-run never leaks a browser), and
   `check_viewport()` (Q10: refuse a screenshot of the wrong size; call it after `goto`).
3. `input.py` - `act()` (unlock, run steps, relock, settle, wait for a held send, look),
   `into_box()` (click, clear, type), `wait_for_change()`. Discovery passes `prepare`/`settled`
   hooks; replay passes neither.
4. `dropdown.py` - the one non-visual exception (D-B). Discovery uses `DROPDOWNS_WITH_BOX_JS`,
   `SELECT_AT_POINT_JS`, `list_options`, `choose_option_at_point`; replay uses `DROPDOWNS_JS`,
   `SELECT_AT_INDEX_JS`, `choose_option_at_index`. Both sides use `read_dropdowns(page, script)`.
   `select_under(page, point, timeout_s)` (`SELECT_UNDER_POINT_JS`): the index of the `<select>`
   right under a point, else None (bounded; None on any error) - discovery's click refuses it.

## How it fits
The screenshot path itself is `cua.vision.screenshot.take_look`; callers pass their own
`look_fn` (their take_look, which also stores the look) and `confirm` callbacks here.

## What may NOT go here
- Imports only `cua.vision` and `cua.config` (plus Playwright).
- No decisions: no send gating, routes, control window, `goto`, or run state (those belong to
  `cua.safety`, `cua.handoff`, `cua.discovery`, `cua.replay`).
- No site value: those live in `configs/<site>.yaml`.
