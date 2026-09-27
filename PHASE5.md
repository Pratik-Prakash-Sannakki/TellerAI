# Phase 5 — Replay Against the Real Browser

**What this phase is, in one line:** takes Phase 4's replay engine (which only ever ran against a fake, hand-built browser) and points it at the real ParaBank site — a real Chromium tab, a real login, real clicks, a real human approval bar.

**Built in:** `notebooks/05_replay_live.py`
**Decisions:** `DECISIONS.md` — D77–D81 (async engine + first live wiring), D85 (approve actually completes the run), D87–D89 (three real bugs found live), D91 (pre-flight input gate)

---

## The idea, in plain terms

Phase 4 proved the replay engine's *logic* was correct — locator fallback, template substitution, the risk gate, retries, checkpoints — but only against `FakeSurface`, a dict-based stand-in that never touched a real page. Phase 5 is the last mile: swap that fake for a real one, `PlaywrightReplaySurface`, that actually drives a browser, and wire the engine's `escalate` hook to a real Approve/Reject/Take-over bar a human can click on the live page.

Nothing about `run_capability_async`'s own logic changes here. This file only supplies two things Phase 4 always needed but never had: a real `AsyncReplaySurface`, and a real `escalate`.

This notebook is explicitly never run by an agent — only a human, watching a real browser. Every fix described below was found and verified by actually running it live, not by reasoning about what should happen.

---

## What's in it

| Piece | What it does |
|---|---|
| `PlaywrightReplaySurface` | Implements Phase 4's `AsyncReplaySurface` for real. Reuses `agent.ipynb`'s own numbered scanner, lock, and force-click mechanism — this is not a second implementation of clicking or typing, it's the same one Phase 1's agent already uses. |
| `make_escalate(cap)` | Shows the same dark Approve/Reject/Take-over bar `agent.ipynb`'s own `click()` tool shows. On Approve, it reports the decision back to the engine — it does **not** click anything itself (D85, below). |
| `gather_missing_inputs` / `missing_required_inputs` | A pre-flight gate, checked before anything else runs (D91, below). |
| `replay_live(cap_path, inputs)` | The one function a person actually calls: loads a capability, runs the pre-flight gate, replays it for real, prints the result. |

---

## Three real bugs found live, and fixed (D87–D89)

The first real test of this file was reading a real account balance. It failed. Here's exactly what was found, in order, by actually logging in and dumping the real page:

| # | What was wrong | The real evidence | The fix |
|---|---|---|---|
| D87 | The recorded label was `"Balance"`; the real page's header is `"Balance*"` (a footnote asterisk). Exact-match locator never matched. | `<th>Balance*</th>` | The label-matching JS now strips one trailing non-alphanumeric character, not just a colon. |
| D88 | The account table's `<tbody>` is empty when the page's `load` event fires — it's filled in seconds later by a jQuery AJAX call. A single resolve attempt could race an empty table. | The page's own script: `$.ajax({ url: "services_proxy/bank/customers/.../accounts", ... success: function(response) { ...append rows... } })` | `resolve()` now polls every 0.4s for up to 5s before giving up, instead of trying once. |
| D89 | Even with the label fixed, the column header's "next sibling" is the *next column header* ("Available Amount"), not any account's value. Wrong regardless of how many accounts exist. | The table's own `<thead>` structure, read directly | Repointed the extract at the table's own footer "Total" row, which uses the same label-value mechanism correctly. |

All three were confirmed with a real, printed DOM dump before being fixed — not guessed. After the fix, a real run returned:

```
REPLAY RESULT: SUCCESS {'balance': '$355.50'}
```

— read live off the real ParaBank site, matching the real test account's real balance (confirmed separately: the account has exactly one entry, `13788`, `$355.50`).

---

## Approving a risky click actually finishes the job now (D85)

Before this fix: approving a real payment made a real click happen, but the function still returned `NEEDS_APPROVAL` — the confirmation was never read, the checkpoint never checked. Worse, **Reject produced the exact same status**, so a caller reading the result couldn't tell "paid" from "nothing happened."

The fix: `escalate` only reports the human's decision now (`"approve"`, or nothing). The **engine** is what resolves the button and clicks it, then continues to the capability's remaining steps — the same way every other step already works.

```
Before:
  Approve -> real click -> NEEDS_APPROVAL  (confirmation never read)
  Reject  -> nothing     -> NEEDS_APPROVAL  (identical status — can't tell them apart)

After:
  Approve -> real click -> remaining steps run -> SUCCESS with the real confirmation
  Reject  -> nothing     -> NEEDS_APPROVAL  (unchanged)
```

This was confirmed live during a real run: approving a real `pay_bill` submission correctly continued past the click and returned `SUCCESS`, not `NEEDS_APPROVAL`.

---

## The pre-flight input gate (D91)

Once the recorder started correctly declaring human-entered values as real inputs (Phase 3's D90 fix) instead of baking them in as literals, calling `replay_live` with only *some* of a capability's inputs supplied started failing with a raw `InputValidationError` traceback — technically correct (the engine should refuse to run with required inputs missing), but not useful to a person sitting at the keyboard.

The fix, exactly as specified: before anything starts — before login, before any browser action — `replay_live` checks the capability's own declared inputs against what was passed in, and for anything missing:

```
You have not entered these fields. Please enter these fields.
  - address
  - city
  - state
  - zip_code
  - phone
```

...then prompts for each one, in order, showing that field's own description as the prompt text. Confirmed live: this printed exactly the message above, gathered all 5 fields, then proceeded into a real browser run — real login, real navigation, real typing into all 8 fields.

If a call already supplies everything, this is a silent no-op — no prints, no prompts, identical to before this fix. `run_capability_async`'s own strict validation is untouched: a real unattended/production run (no human at the keyboard) still fails fast and loudly on a missing input, exactly as it always has.

---

## Known gaps — honestly stated

- **The Reject path has not been successfully confirmed live.** An attempt to verify it (using a scripted auto-click to simulate a human clicking Reject) had a bug in the *test script itself* and ended up clicking Approve instead, completing a real (test-bank, no real money) bill payment. The Approve path is now well-confirmed live; Reject and Take-over are confirmed only by the offline `FakeSurface` test suite, not by a real click in a real browser.
- **Only one risky capability has been run live end-to-end** (`pay_bill`, twice). `transfer_funds.yaml` — the other risky example — has not yet been replayed live.
- This file is still a notebook, run by a human in Jupyter. Phase 9 is where this logic gets ported into a real installable package (`src/cua/`) with a `cua replay` CLI command.
- `artifacts/pay_bill.yaml` currently has an uncommitted local diff (from a re-capture, not from any of the fixes above) that hasn't been reviewed or resolved.

---

## How it fits with the rest

Phase 4 proved the engine's logic was correct in isolation. Phase 5 is where that logic met a real, imperfect legacy-style page for the first time — and found three real bugs a clean `FakeSurface` test could never have caught (a footnote character, an async-loading race, a table structure that doesn't fit a simple label-value read). That's the whole point of this phase: Phase 4 answers "is the engine correct?"; Phase 5 answers "does it actually work against the real thing?" — and, this time, the honest answer required three real fixes before it did.
