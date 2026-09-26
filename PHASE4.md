# Phase 4 — The Replay Engine

**What this phase is, in one line:** actually following a saved recipe for real, with zero AI involved, the way a bank's production system would call it.

**Built in:** `notebooks/04_replay_engine.py`
**Decisions:** `DECISIONS.md` — D9 (checkpoint), D10 (error taxonomy), D26 (waiting/retries), D27 (replay result contract), D38–D39 (risk in the artifact, result contract), D77–D81 (async mirror, live wiring), D82 (escalate's return value gates the risky click, not a side effect inside it)

---

## The idea, in plain terms

Phase 2 wrote the recipe format. Phase 3 is meant to fill a recipe in from a real agent run. Phase 4 is the part that actually **cooks** from that recipe — no model, no judgment calls, just code that reads the steps in order and does exactly what they say. If a step can't be found, it fails loudly instead of guessing. If a step is about moving money and the amount is too big, it stops and asks a human *before* clicking, not after.

This notebook has no `import playwright` anywhere in it. Every test runs against a hand-built fake stand-in for a browser, called `FakeSurface`. The real browser wiring is Phase 9's job (see "Known gaps" below).

---

## What `run_capability` actually does

It takes a `Capability` (Phase 2's schema), a surface to act on, the caller's inputs, and a way to resolve secrets. It walks the steps one at a time and returns one `ReplayResult`.

| Step | What happens | Why |
|---|---|---|
| 1. Validate inputs | Every caller-supplied value is checked against its declared type and pattern (e.g. `account_id` must match `^[0-9]{4,10}$`) before anything touches the page. | A bad input should fail fast and clearly, not halfway through a run (D29). |
| 2. Walk each step | For `navigate`, `click`, `type`, `select`, `extract` — resolve the target element first (see next row), fill in templates, then act. | Same five actions as Phase 2's schema. |
| 3. Resolve the target | Try the `primary` locator. If it doesn't find anything and there's a `fallback`, try that. If neither works, stop with a `FAILED` result naming both. | Matches Phase 2's "one primary, one optional fallback" design (no guessing a third way). |
| 4. Fill in templates | `{{input_name}}` comes from the caller's validated inputs. `{{secret:name}}` comes from the secret resolver, never from the model. | The recipe must work for any account number, not just the one it was recorded with. |
| 5. Gate a risky click, BEFORE acting | If a click is marked `risk: risky`, its dollar amount is read from the named input and compared to `auto_approve_limit` *before* the click happens. At or above the limit: stop, call `escalate`, and read its return value. Exactly `"approve"`: resolve the target and click it (same code path an ordinary click uses), then continue to the remaining steps. Anything else (including the default `None`): return `NEEDS_APPROVAL` without touching the page. Below the limit: click goes ahead automatically. | The point of no return must be checked before the button is pressed, not after (D38); `escalate`'s own decision, not a side effect inside it, is what the engine acts on (D82). |
| 6. Check outcome rules after each step | After every step, the current page's URL and text are checked against the capability's own `outcome_rules`, in the order they're declared. First match wins: `business` → return `BUSINESS_OUTCOME` right away; `hard` → return `FAILED` right away; `recoverable` → log it and keep going. | A "no such account" page is a normal answer, not a crash (D10). |
| 7. Retry on a transient failure | A surface can raise `TransientFailure` to mean "not ready yet." The engine retries up to `max_retries` times — except a risky click is **never** retried, even if it's under the limit, so a slow page can never cause the same transfer to fire twice. | D26: only safe steps retry. |
| 8. Verify the checkpoint | After all steps finish, the final page must match the capability's `checkpoint` — both `url_contains` and `text_present`, not just one. If not, `FAILED`. | Same two-signal rule Phase 2 requires (D9). |
| 9. Extract outputs, check types | An extracted value that doesn't match its declared type (e.g. text where a `currency` was expected) is a `FAILED`, never a silently wrong `SUCCESS`. Once all steps pass, the collected outputs must exactly match what the capability declares, or it's `FAILED`. | Never return a result that lies about what it produced. |
| 10. Return one of four statuses | `SUCCESS` (outputs attached), `BUSINESS_OUTCOME` (a known real answer), `NEEDS_APPROVAL` (waiting on a human), or `FAILED` (step, expected, observed). | D27's exact four-status contract — `NEEDS_APPROVAL` is deliberately its own status, not folded into `FAILED`, because a caller should wait, not retry or give up. |

A small honest detail: the `escalate` hook (called for `NEEDS_APPROVAL` and for hard failures) is just a plain callable here, faked in tests. In real use it's meant to hand control to a person the same way `agent.ipynb`'s `human_takeover`/decision-bar mechanism does — that wiring doesn't exist yet either (Phase 9).

---

## The 8 required test scenarios, plus 3 bonus

All of these run against `FakeSurface`, a dict-based stand-in for a browser that the test code controls directly (registers which locator maps to which fake element, sets fake page text, etc).

| # | Scenario | What it proves | Result in the notebook |
|---|---|---|---|
| 1 | Happy path | A clean run returns `SUCCESS` with the right outputs. | `SUCCESS`, `{"value": "99"}` |
| 2 | Business-outcome page | A declared bad-input page state returns `BUSINESS_OUTCOME`, not a crash. | `BUSINESS_OUTCOME`, `ITEM_NOT_FOUND` |
| 3 | Primary locator fails, fallback works | Falling back is real, not just declared — and it's logged so you can see it happened. | `SUCCESS`, log line contains "fallback" |
| 4 | Both locators fail | A clean `FAILED` naming both the primary and fallback that were tried. | `FAILED`, step 1, action `click`, expected string names both |
| 5 | Risky step, amount under the limit | A risky click proceeds on its own when the amount is safely below the auto-approve limit. | `SUCCESS`, click actually happened |
| 6 | Risky step, amount at/above the limit | The click is gated *before* it happens — `escalate` is called once, the button is never clicked. | `NEEDS_APPROVAL`, pending step recorded, click count stays 0 |
| 7 | Checkpoint fails after all steps ran | Even if every step "worked," a bad final page state is still caught. | `FAILED`, step action `checkpoint` |
| 8 | Extracted value fails its declared type | A non-numeric value read where an `integer` was expected is a hard failure, not a wrong success. | `FAILED`, step action `extract` |
| Bonus 1 | Transient failure, then it recovers | A step that fails twice then succeeds is retried automatically and still finishes as `SUCCESS`. | `SUCCESS` |
| Bonus 2 | Transient failure past the retry limit | Retries are bounded — it doesn't retry forever. | `FAILED`, observed text mentions "transient failure" |
| Bonus 3 | Risky click never retried | Even a risky click that's under the limit and fails transiently is not retried, to avoid double-clicking a money-moving button. | `FAILED` |

There's also a Section 5 in the notebook that runs both real example artifacts (`get_account_balance.yaml`, `transfer_funds.yaml`) end to end through a `FakeSurface` built from each YAML's own declared locators — including the transfer's under-the-limit (`SUCCESS`) and over-the-limit (`NEEDS_APPROVAL`) cases. All of it passes.

---

## Does it actually work with what Phase 3 produces?

This is separate from the notebook's own Section 5 test above, and it's the more important one: it tests Phase 3 and Phase 4 as two *independent* programs, not two notebooks that happen to import the same schema classes.

Here's what was actually run, live, in this conversation: a `Capability` was compiled using Phase 3's own recorder logic (`get_account_balance`), and saved out to a real YAML file on disk. Then, in a **separate Phase 4 process** — no shared Python objects, nothing held in memory between the two — that YAML file was loaded independently and run through `run_capability`. This is exactly the shape a real deployment would take: the recorder writes a file once, and the replay engine reads that file back later, possibly on a different machine, days apart.

The result:

```
loaded into Phase 4, independently, as: Capability | get_account_balance
REPLAY RESULT: SUCCESS {'balance': '$1,200.00'}
```

This is a real, verified result — not a guess and not just both halves importing the same Pydantic models. It's the first proof that Phase 3's saved output is actually usable by Phase 4 as a file, the way it would be in production.

---

## Known gaps — honestly stated

**The one real gap:** everything above has only ever been tested against `FakeSurface`, a hand-written fake that lives entirely in the test cells of this notebook. It is not a browser. It has never been pointed at a real page, and it has never been wired to the actual Playwright browser built in `agent.ipynb` (Phase 1).

The notebook is explicit about this itself: no `import playwright` appears anywhere in the file, on purpose, so that the engine logic (locator resolution, template substitution, the risk gate, outcome rules, the checkpoint) could be proven correct entirely on its own, independent of a real browser. The plan (not yet built) is for Phase 9's real `ReplaySurface` to wrap `agent.ipynb`'s own `PlaywrightSurface` and its `human_takeover`/decision-bar mechanism — the same `escalate` seam this notebook already has, just pointed at the real thing instead of a test fake.

So: the engine's logic is solid and tested, including against a real Phase-3-produced file. What's still missing is the last mile — a real browser tab actually clicking a real button on parabank.parasoft.com.

---

## How the three phases fit together

Phase 2 defines the paper the recipe is written on, and a strict inspector that refuses a bad one. Phase 3 fills that paper in from a real, messy agent run — its compile logic has already been rebuilt against Phase 2's simplified schema and confirmed working (see PHASE3.md). Phase 4 is the part that reads a filled-in recipe and actually runs it, with no AI anywhere in the loop.

The pipeline is now verified end to end **at the file level**: a capability written to YAML by Phase 3's recorder logic loads independently in a separate Phase 4 process and runs to a correct `SUCCESS`. What's still pending on both ends is the real browser, not the schema: Phase 3's *capture* half (the part that would watch a live discovery run) has never been pointed at a real browser, and Phase 4's replay side needs its `FakeSurface` swapped for a real one wrapping Playwright. The logic in the middle — the part that matters most for correctness — is done and tested.
