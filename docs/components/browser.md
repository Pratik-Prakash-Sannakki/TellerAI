# Browser

Playwright with no decisions: the open browser, the site lock, our own mouse and keyboard input,
and native dropdowns. Gating, routes and run state belong to other components.

## Where it lives

- [`src/cua/browser/`](../../src/cua/browser/) (read order:
  [`browser/README.md`](../../src/cua/browser/README.md))
  - `session.py`: `Session`, `open_session`, `close_session`, `check_viewport`.
  - `site_lock.py`: `SiteLock`.
  - `input.py`: `act`, `into_box`, `wait_for_change`.
  - `dropdown.py`: the native `<select>` scripts and helpers.

## How it works

- **`open_session(site, cfg, existing=None, profile_prefix=...)`** launches one visible Chromium
  (persistent context in a temp profile) at the configured viewport, scale 1. It loads the
  hand-back extension from `extensions/handback/` ([handoff](handoff.md)), opens the site tab and
  the "Agent control" tab, and locks the site tab. A live `existing` session is returned
  unchanged, so a re-run never leaks a browser.
- **`check_viewport(session)`** refuses a screenshot of the wrong size (Q10). Call it after `goto`.
- **`close_session`** closes the browser, stops Playwright and deletes the temp profile (the bank
  session's cookies and cache).
- **`SiteLock`** sends CDP `Input.setIgnoreInputEvents`: the site tab ignores all real mouse and
  keyboard input. `async with lock.open():` is the only unlock path, and it always re-locks, even
  on an exception. Our own input runs inside it; so does a human take-over.
- **`act(session, steps, ...)`**: unlock, run the input steps, relock, settle (`settle_ms`), wait
  on the send gate if a send is held, then take a new look. Discovery adds two hooks
  (`prepare` reads dropdowns before acting; `settled` waits for a send's response); replay passes
  neither.
- **`into_box`**: bring the site tab to the front (else keys reach the control tab), click the
  box, select all, delete, type. A retry replaces instead of doubling up.
- **Native dropdowns** (the one non-visual exception, "D-B"): macOS draws a `<select>` list outside
  the page, so no screenshot shows it. A small script reads or sets only the `<select>` under (or
  nearest) a point, or the Nth `<select>` by recorded index. OCR then confirms the box shows the
  option.
  - Discovery: `DROPDOWNS_WITH_BOX_JS`, `SELECT_AT_POINT_JS`, `list_options`,
    `choose_option_at_point`.
  - Replay: `DROPDOWNS_JS`, `SELECT_AT_INDEX_JS`, `choose_option_at_index`.
  - Both: `select_under` (`SELECT_UNDER_POINT_JS`): discovery's `click` refuses a dropdown with it.

## Public API / key types

`Session`, `open_session`, `close_session`, `check_viewport`, `SiteLock`, `act`, `into_box`,
`wait_for_change`, `read_dropdowns`, `select_under`, `list_options`, `choose_option_at_point`,
`choose_option_at_index`.

## Config knobs

`BrowserConfig`: `viewport`, `settle_ms`, `scroll_px`, `ext_s`, `ext_poll_s` ([config](config.md)).

## Safety and guarantees

- The site tab is locked for the whole run except inside `SiteLock.open()` (Q16, Q21).
- Imports only `cua.vision` and `cua.config` (`tests/unit/test_import_rules.py`).
- The temp browser profile is deleted at close (Q23).
- No send gating here: `act` only waits on the lock the [send guard](safety.md) holds.

## Tests

`tests/unit/browser/` (`test_session.py`, `test_site_lock.py`, `test_input.py`,
`test_dropdown.py`).

## Limits and cuts

- Needs a desktop with a display (`headless=False`); built and tested on macOS.
- Native dropdowns are read by script, not pixels.
- Desktop apps would replace this layer with a screenshot source and a point-input sink (REPORT §4).

## Decisions

Q10, Q12 (keyboard dropdowns, later replaced by the D-B script), Q16, Q21 in
[discovery-decisions.md](../decisions/discovery-decisions.md); R3, R4 in
[replay-decisions.md](../decisions/replay-decisions.md).
