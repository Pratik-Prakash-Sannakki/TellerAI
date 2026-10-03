# Handoff: control tab, take-over, hand-back

A human in the loop. Our own "Agent control" tab is the only place a human answers. A take-over
unlocks the site for the human, in the same live session, until they hand back.

## Where it lives

- [`src/cua/handoff/`](../../src/cua/handoff/) (read order:
  [`handoff/README.md`](../../src/cua/handoff/README.md))
  - `control_window.py`: `ControlWindow`, `Side`, `discovery_control`, `replay_control`.
  - `binding.py`: `bind_control` (the `cuaReply` bridge and the close listener).
  - `extension.py`: `ext_call`, `button_clicked`, `handback_button`, `watch_button`.
  - `takeover.py`: `takeover_text`, `hand_back`, `wait_held_send`.
- [`extensions/handback/`](../../extensions/handback/): the Chrome toolbar extension
  (`manifest.json`, `background.js`, icons).
- Each side's own take-over: `take_over` / `human_help` in `discovery/tools/human.py`, `rescue` in
  `replay/rescue.py`.

## How it works

- **Control tab.** `ControlWindow` renders one question at a time into its own tab and brings it
  to the front. The page's buttons call `cuaReply(value)`, a Playwright-exposed function bound once
  per tab (`bind_control`). It always shows who is in control (agent, replay or human).
- **Modes:**

| Mode | Buttons | Used for |
|---|---|---|
| `confirm` | Approve / Edit | Gate 1 |
| `approve` | Approve / Reject | Gate 2 |
| `form` | Submit / Skip | missing values, mismatch fixes, Gate 1 edits, replay inputs |
| `text` | Send | a free-text answer |
| `help` | Send answer / Take over / Stop | discovery: the agent is stuck or asks |
| `rescue` | Take over / Stop | replay: a step failed |
| `takeover` | Done, hand back | while the human is in control |
| `status` | none | "Agent is working" / "Replay is working" |

- **When discovery calls a human:** `ask_human`, `request_missing_values`, or automatically
  (`human_help`) after `unsure_limit` failures in a row, the same call `repeat_limit` times, the
  step budget, or a login failure. The human can answer in words, take over, or stop.
- **When replay calls a human:** missing inputs (one form), a dropdown value that is not a live
  option, and `rescue` after a step's retry fails.
- **Take-over:**
  1. `SiteLock.open()` unlocks the site tab ([browser](browser.md)).
  2. `handback_button` sets the extension badge to `YOU`.
  3. `hand_back` waits for whichever comes first: Done in the control tab, or a click on the
     toolbar icon (polled from the extension's click counter).
  4. The site re-locks; the badge goes back to `AI`.
  5. `wait_held_send` waits (`handback_s` / `gate_s`) for any send the human started that is still
     at the gates; still held = `STUCK`.
  6. Off the allowed hosts: discovery goes back to `base_url`; replay stops `FAILED`.
- **What is recorded:** page paths visited, send paths, screenshots before and after, and the
  reason (discovery also logs the duration). Never keystrokes or typed values.
  - Discovery: one `take_over` event marked not recordable; the run cannot be saved as a
    capability ([recorder](recorder.md)).
  - Replay: an entry in `result.human`; the status reads e.g. `SUCCESS (human intervened at step 4)`.
- **The extension** has no content scripts and no host access. It only counts toolbar clicks
  (`self.handbackClicked`) and shows a badge (`setMode('YOU' | 'AI')`). Every call into it is
  bounded (`ext_s`); if it fails to load, the take-over still hands back from the control tab.

## Public API / key types

`ControlWindow.ask(title, details, mode, image=None, who=None, rows="")`,
`ControlWindow.form(title, fields, values=None, options=None)`, `ControlWindow.show`,
`discovery_control`, `replay_control`, `bind_control`, `handback_button`, `watch_button`,
`hand_back`, `wait_held_send`, `takeover_text`.

## Config knobs

`BrowserConfig.ext_s`, `ext_poll_s`; `DiscoveryConfig.handback_s`; `ReplayConfig.gate_s`
([config](config.md)).

## Safety and guarantees

- The site is locked for the whole run except during a take-over (Q16, Q21).
- Sends a human makes during a take-over still meet both gates ([safety](safety.md)).
- The extension never touches the site page; the control tab never shows a secret value
  (sensitive form rows are masked).
- A closed control tab fails closed: a held send is aborted.
- Imports only `cua.config` (plus schema, vision, browser); never discovery, replay or safety.

## Tests

`tests/unit/handoff/` (`test_control_window.py`, `test_extension.py`, `test_manifest.py`,
`test_takeover_loop.py`); `tests/unit/discovery/test_human.py`;
`tests/unit/replay/test_replay_rescue.py`, `test_replay_handback.py`.

## Limits and cuts

- Keystrokes during a take-over are not captured (by design), so a discovery take-over run is not
  replayable (REPORT §7).
- The toolbar icon must be pinned once from the puzzle-piece menu to be visible.

## Decisions

Q16 (control window + site lock), Q21 (live-session take-over) in
[discovery-decisions.md](../decisions/discovery-decisions.md); R8 (human handoffs), R19
(hand-back button) in [replay-decisions.md](../decisions/replay-decisions.md).
