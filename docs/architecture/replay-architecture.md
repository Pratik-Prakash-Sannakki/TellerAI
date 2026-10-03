# Replay architecture

> **Notebook-era design.** Written while the system was two notebooks (before 2026-10-01). The
> design still holds; names and file paths differ from the code. Current per-component docs: [docs/README.md](../README.md).

How replay runs a saved capability with plain code, no LLM. All questions and decisions:
`docs/decisions/replay-decisions.md` (R1-R18). Discovery side: `discovery-architecture.md`.

## 1. Diagram

```
 Once, at the end of a discovery run (discovery's `## Save artifact`, pure Python)
┌───────────────────────────┐   ┌─────────────────────────────┐
│ Discovery event log       │   │ Agent metadata              │
│ (tool, args, result,      │   │ (response_format, Pydantic) │
│  point, url, crop, label, │   │ name, description, inputs,  │
│  text, table, human_entry,│   │ input vs constant, outputs, │
│  recordable) + crops      │   │ success text                │
└─────────────┬─────────────┘   └──────────────┬──────────────┘
              │ drop failures, keep last        │
              │ success per target, refuse      │
              │ take-overs (R16)                │
              ▼                                 ▼
        ┌──────────────────────────────────────────────┐
        │ Merge + validate (Capability, schema v2)     │──▶ capability.yaml + crops/
        └──────────────────────────────────────────────┘

 Every replay (no LLM)
┌───────────────┐  ┌───────────────┐  ┌──────────────────────┐
│ Load YAML     │─▶│ Pre-flight    │─▶│ Open browser          │
│ Pydantic check│  │ inputs form   │  │ 1280x800, dsf=1       │
└───────────────┘  │ (control tab) │  │ refuse if not exact   │
                   └───────────────┘  │ SiteLock on, guard on │
                                      └──────────┬───────────┘
                                                 ▼
┌────────────────────────────────────────────────────────────────────┐
│ Step loop (one step at a time)                                     │
│  screenshot → RapidOCR → find target:                              │
│    rung 1 OCR text (+ordinal) → rung 2 label + offset →            │
│    rung 3 matchTemplate(crop) → table cell (extracts)              │
│    all miss → scroll + retry (limit) → help panel                  │
│  unlock → mouse/keyboard (clear-then-type, SELECT_AT_JS) → relock  │
│  check with OCR (value / dots / option / expect text), bounded poll│
│  drift log: rung used                                              │
└──────────┬────────────────────────────────────────┬────────────────┘
           │ any non-GET request                    │ stuck / failed check
           ▼                                        ▼
┌──────────────────────────────┐        ┌──────────────────────────────┐
│ guard_send (page.route)      │        │ Control tab (discovery's)    │
│ mismatch check → form        │        │ answer / take over / stop    │
│ Gate 1 Approve/Edit          │        │ inputs form, masked secrets  │
│ Gate 2 send it?              │        └──────────────────────────────┘
└──────────────────────────────┘
           │
           ▼
   ReplayResult: SUCCESS | BUSINESS_OUTCOME | DECLINED | STUCK | FAILED
   (outputs to the caller only; working values wiped in finally)
```

## 2. Components

### Artifact (made by discovery, not replay)
- Discovery's `## Save artifact` section builds and saves the capability (R10): cleans the log
  (R16), maps each event to a step (R12), attaches rungs (R13), adds the model's name and
  descriptions (R11), validates, writes YAML + `crops/`. Replay loads it as is, no edits.
- Refuses, with a reason, rather than guessing: a take-over, an input name the model made up.

### Loader + pre-flight
- Pydantic-validates the YAML. Checks `base_url` host, viewport, secret names exist in `.env`.
- Missing or bad inputs (`pattern`) → one form in the control tab, before step 1 (D91 idea,
  no `input()`).

### Browser setup
- Discovery's own setup: context at `viewport` from the capability, `device_scale_factor=1`.
- First screenshot must be exactly that size, or `FAILED`.
- `SiteLock` on for the whole run. `guard_send` routed for the whole run.

### Target finder
- Generic, no site code. Tries rung 1 → 2 → 3 on the live look; table extracts use
  `TableCellLocator` (Q8).
- Rung 1: fuzzy OCR match of the saved text, nth match if `ordinal` set.
- Rung 2: find the label by OCR (with its ordinal), add the saved offset to its box centre.
- Rung 3: `cv2.matchTemplate(screenshot, crop)`, threshold in config; two near-equal peaks = miss.
- All miss → `scroll("down")`, new look, retry, up to the config limit → help panel.

### Actor
- Discovery's `act` / `into_box`: unlock → `mouse.click` / `keyboard.type` → relock, in `finally`.
- Dropdowns: `SELECT_AT_JS` on the `<select>` under the point only.
- `{{input}}` and `{{secret:name}}` are rendered at the moment of typing, never earlier.

### Checker
- OCR on a bounded poll (~200ms, budget in config) after every action (R5).
- Secret: the spot changed (dots). The secret in plain text on screen = stop at once.

### Send guard
- Discovery's `guard_send`, unchanged: mismatch check against the caller's inputs, Gate 1
  (Approve / Edit), Gate 2. Login click exempt via `CFG.login_words`. Never auto-approved (R15).

### Control tab
- Discovery's "Agent control" tab: inputs form, help panel, the two gates. Fails closed.

### Result + drift log
- `ReplayResult` (D27 shape), statuses per R17. Drift log: step index, action, rung, polls.
  Neither holds a typed, selected, or extracted value.

## 3. Step types

| Step (`action`) | Find | Act | Check |
|---|---|---|---|
| `navigate` | none (`path` on `base_url`, `host_allowed`) | `page.goto` | `expect` text on screen |
| `click` | rung 1 → 2 → 3 | `mouse.click` (via lock) | `expect` text, or screen changed |
| `type` | rung 2 → 3 | click, clear, `keyboard.type` | box shows the value |
| `type` (secret) | rung 2 → 3 | same, value from `.env` | spot changed (dots); plain text = stop |
| `select` | rung 1 → 2 → 3 | `SELECT_AT_JS` at the point | closed box shows the option |
| `scroll` | none (optional point) | `mouse.wheel` (config distance) | new look |
| `extract` | table cell, or rung 1 → 2 | none (OCR text) | value matches its type |
| (checkpoint) | — | — | proof text on the final screen |

- A click that fires a non-GET request is held by the send guard; the step waits on the gates.
- Every step: all finds miss → scroll + retry → help panel. A secret check is never retried blind.

## 4. Worked example: ParaBank login + read balance

**Capability (excerpt, `get_savings_balance.yaml`):**

```yaml
schema_version: 2
name: get_savings_balance
version: 1
description: Log in and read one account's balance from Accounts Overview.
base_url: https://parabank.parasoft.com/parabank
viewport: [1280, 800]
device_scale_factor: 1
inputs:
  - {name: account_id, type: string, description: "Account number, e.g. 13455"}
outputs:
  - {name: balance, type: money, description: "Balance of that account"}
secrets: [username, password]
steps:
  - action: type
    value: "{{secret:username}}"
    target: {anchor: {label: Username, offset: [150, 0]}, template: crops/s0.png}
  - action: type
    value: "{{secret:password}}"
    target: {anchor: {label: Password, offset: [150, 0]}, template: crops/s1.png}
  - action: click
    target: {ocr_text: {text: Log In}, template: crops/s2.png}
    expect: {text_present: Accounts Overview}
  - action: extract
    target: {table_cell: {row_key: "{{account_id}}", column: Balance}}
    save_as: balance
checkpoint: {text_present: Accounts Overview}
```

**Replay:** `replay("get_savings_balance.yaml", {"account_id": "13455"})`

| # | Step | What the code does | Drift log |
|---|---|---|---|
| 0 | pre-flight | YAML valid; `account_id` given; `username`/`password` in `.env`. Browser at 1280x800, screenshot size matches. Lock + guard on. | — |
| 1 | type username | OCR finds "Username" at (60,210) → +150px → (210,210). Unlock, click, clear, type the `.env` value, relock. OCR re-read shows it. | rung 2 |
| 2 | type password | "Password" at (60,250) → (210,250). Type from `.env`. Spot changed (dots); secret not visible. | rung 2 |
| 3 | click Log In | OCR finds "Log In" (rung 1). Click. The login POST is exempt (`login_words`). Poll until "Accounts Overview" shows. | rung 1 |
| 4 | extract balance | OCR the table: row "13455", column "Balance" → `$100.00`. Type check `money`: ok. | table |
| 5 | checkpoint | "Accounts Overview" on screen. | — |
| end | result | `SUCCESS`, `outputs={"balance": "$100.00"}` to the caller only. Log holds steps + rungs, no values. Working values wiped. | — |

**What changes on a bad day**
- Layout moved and "Username" text reads "User name": rung 1 isn't used for boxes; rung 2 fuzzy
  match still finds it, or rung 3 finds the empty box picture. Drift log records the rung.
- Account `99999` not in the table → `outcome_rule` → `BUSINESS_OUTCOME` (e.g. ACCOUNT_NOT_FOUND),
  or the help panel if no rule matches.
- A transfer capability instead: the Transfer click's POST is held; mismatch check, Gate 1,
  Gate 2. Reject at Gate 2 → `DECLINED`, nothing sent.

## 5. Notes
- Coordinates and values are illustrative, not from a real run.
- The anchor's offset, label box and ordinal are recorded by discovery (`DECISIONS.md` R14).
- Schema v2 lives in discovery's `## Save artifact` section (the single source); replay imports it (R13).
