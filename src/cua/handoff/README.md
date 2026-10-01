# cua.handoff

A human in the loop: our own "Agent control" tab, the hand-back toolbar button, and the shared
pieces of a take-over.

## Read order
1. `control_window.py` - `ControlWindow(win, site_page, *, side=)`: one class, every mode of both
   sides (approve, confirm, text, help, form, status, takeover, rescue). A `Side` holds what
   differs: default `who`, the "working" title, the take-over button label, the form note, and
   `guard_closed` (replay's closed-window guards and `_front`-before-`try`). Build one with
   `discovery_control(win, site_page)` or `replay_control(win, site_page)`.
2. `extension.py` - `ext_call` (one bounded call into the extension's service worker, None on any
   failure), `button_clicked` (poll the click count), `handback_button` (badge YOU, yield the
   click task, badge AI after), `watch_button` (discovery: a click answers the take-over).
3. `binding.py` - `bind_control(control_page, control)`: one `cuaReply` forwarder and one
   `close` listener per control tab, both dispatching to the window bound last (setup re-runs).
4. `takeover.py` - `takeover_text`, `hand_back(control, button, text)` (panel Done or toolbar
   click, whichever first), `wait_held_send(lock, timeout_s)` (after Done: wait for a send still
   held at the gates).

## How it fits
Discovery's `take_over` and replay's `rescue` stay with their side (`cua.discovery`,
`cua.replay`) and are built from these pieces plus `cua.browser.SiteLock.open()`.

## What may NOT go here
- Imports only `cua.config` (and may use `cua.schema`/`cua.vision`/`cua.browser`); never
  `cua.discovery`, `cua.replay` or `cua.safety` decisions.
- No call on the site page from the extension code: the button lives in the extension only.
- No site value: those live in `configs/<site>.yaml`.
