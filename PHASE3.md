# Phase 3 — The Recorder

*Read for this write-up: `git log` and `git status` as of now, plus `notebooks/03_recorder.py` on disk as of now. `notebooks/03_recorder.py` itself has no uncommitted changes (it matches commit `971a4d0` exactly), so it is not mid-edit right now. But see "Known gaps" below — it was written *before* the Phase 2 schema was simplified, and has not been updated since. Treat the schema-mismatch finding as current fact, not speculation; it is checked against the actual code on both sides, not assumed.*

> **2026-09-26 note: the paragraph above is now stale, kept for the historical record rather than
> rewritten.** It describes the recorder as it stood at commit `971a4d0`, before the schema-mismatch
> problem it warns about was actually fixed. Since that snapshot, two more rounds of work landed:
> **(1)** a full rebuild against the current schema and agent.ipynb (commits `c8b5afe` through
> `e4a4d57`, DECISIONS.md section P, D70–D76) — the `Target(locators=[...])`/`app`/`when_to_use`/
> `routes` mismatch this document calls "the most important gap" no longer exists; **(2)** a bugfix
> on top of that rebuild (this session, DECISIONS.md section Q, D82–D84) that is what the rest of
> this note explains. See "**The 2026-09-26 addition**" below for what changed, in what order, with
> examples — and the corrected "Known gaps" row further down for what is (and isn't) still true.

**What this phase is, in one line:** turning a real, already-happened agent run into a saved, checked recipe, in Phase 2's exact format.

**Built in:** `notebooks/03_recorder.py` (+ paired `.ipynb`)
**Decisions:** `DECISIONS.md` — foundations D2, D5, D8, D9, D10, D12, D20, D23, D29, D32–D34; Phase 3 section M, D41–D49; the honestly-stated gap in D68

---

## The idea, in plain terms

Phase 1's agent wanders: it looks, thinks, clicks, sometimes backtracks, sometimes gets it wrong on the first try. Phase 2 defined the recipe card format (ingredients, steps, proof it worked). Phase 3 is the person standing next to the agent with a notepad, writing down only the parts of the run that actually mattered, in the recipe format Phase 2 will accept — and refusing to write down a recipe it isn't sure is honest.

The notebook is split into two parts. In the file itself, the **pure Python half comes first** and the **browser half comes after**, even though the intro markdown at the top of the file calls them "Part A, CAPTURE" and "Part B, COMPILE" in that order. What actually happens, in the order the cells run:

| Half | Needs a browser? | Its job |
|---|---|---|
| **COMPILE** (cells `OFFLINE 1`–`OFFLINE 15`) | No | A pure function: `events + declared inputs -> Capability`. Tested with hand-built fixture events that imitate a real ParaBank run — no browser needed to prove this half works. |
| **CAPTURE** (cells `BROWSER 1`–`BROWSER 13`) | Yes, + an API key | Runs the real agent (copied from `agent.ipynb`, Phase 1) with every tool wired to also log an **event**: which tool, did it work, the page before and after, and a description of the element touched. Ends by calling COMPILE on the real events and saving the result. |

In recipe-card language: CAPTURE is watching someone cook once and writing down *everything* they touched, including mistakes. COMPILE is the editor who throws out the mis-steps, keeps the real ingredients and steps, checks the "proof it worked" step actually proves something, and only then lets the card go to print.

---

## What the recorder has to figure out, and why

Each row below is a real problem a raw agent run has that a clean recipe card cannot have. The examples are pulled directly from the notebook's own fixtures and docstrings (`notebooks/03_recorder.py`), not invented.

| What it figures out | Why it matters | Concrete example from the code |
|---|---|---|
| **Locator derivation** (D42) | The saved recipe must find the right element next month, without the model. A role+name locator is only trustworthy if the name came from something a screen reader would also use — not from a raw HTML attribute. | The login username box (`USER`) has `name="username"`, `name_source="attr"` — an attribute, not a real accessible name — so no role locator is built for it; it falls back to its `label`, `"Username:"`. The `FROM` account dropdown is the same case (`name="fromAccountId"`), so its target ends up `label` + a `structure` fallback ("nth `<select>` inside the form"), never `role`. |
| **Dropping dead ends** (D43) | An agent that clicks "Open New Account" by mistake, then clicks back to "Accounts Overview," did nothing useful. Baking that detour into the recipe would replay it every time. | Fixture test (`OFFLINE 10`): a click to `/openaccount.htm` followed by a click back to `/overview.htm`, with nothing typed or read in between, is dropped with the reason `"dead end: left /overview.htm and came back"` for *both* events. |
| **Splitting out login** (D45) | Login is its own reusable recipe (used on session expiry too), and the task recipe must never carry a password step. | `split_login()`: everything up to and including the first click after the last `type_secret` becomes `login_parabank`; the task capability starts fresh with a `navigate` to `/overview.htm` and has zero secret steps (`OFFLINE 9` asserts `task.secrets == []`). |
| **Turning literals into `{{inputs}}`** (D44) | The recipe must work for *any* account number, not just the one used during recording. A raw `"14232"` baked into a step would make the recipe replay-once-only. | Typing `"$20.00"` into the Amount field, with `amount` declared as `"20.00"`, becomes the step value `"{{amount}}"` (D44's `same_value` treats `$20.00` and `20` as equal). A `"Ref-77"` typed into the Note field matches no declared input, so it is kept as a literal and separately reported: `constants: [{"where": "event 5 (type_text) into 'Note:'", "value": "Ref-77"}]`. |
| **Business-outcome detection from a bad-input run** (D47) | A recipe needs to know what a *normal* bad answer looks like (e.g. "no such account"), found once on purpose rather than guessed. | `rule_from_probe()`: a probe run opens `/activity.htm?id=99999999` and calls `finish(outcome="ACCOUNT_NOT_FOUND", proof_text="Could not find account number 99999999")`. The recorder cuts the literal `99999999` out of the proof text and saves the rule as `text_present: "Could not find account number"` — so the rule matches for any bad account id, not just this one. |
| **Risk marking** (D33, D49) | The recipe must flag the point of no return so replay (Phase 4) knows to ask a human above a dollar limit. | A `Transfer` click that a human approved during discovery (`approved=True`) becomes `risk: risky`, `amount_input: "amount"`, and the whole capability's `risk_level` flips to `"risky"`. The exact same run with `approved=False` produces `risk: safe` and `amount_input: None` (`OFFLINE 12`'s control test). |

---

## Known gaps — honestly stated

**The most important one, found by reading the code, not assumed:** the recorder was written *before* the Phase 2 schema was simplified, and has not been rebuilt to match.

- `notebooks/03_recorder.py`'s `derive_target()` still builds `Target(locators=locs)` — a list under a field called `locators`.
- Its `_cap()` still constructs `Capability(..., app=App(**APP), when_to_use=when_to_use, routes=_routes(paths), ...)`.
- But the schema it dynamically loads at runtime (`notebooks/02_artifact_schema.py`, current on disk) has **no** `locators` field on `Target` (only `primary` / `fallback`, with `locators()` now a *method*), **no** `app` field, **no** `when_to_use` field, and **no** `routes` field (routes is `derived_routes(cap)`, computed on demand, not stored) — see D63–D66. `Capability` instead requires a top-level `base_url`, which the recorder never sets.
- This is not a guess: `notebooks/02_artifact_schema.py` line 113 defines `def locators(self) -> list:` as a method, and line 295 onward lists `Capability`'s actual fields, matching neither call the recorder makes. Confirmed by the git history too — the recorder's commits (`52e400e`, `971a4d0`) both land *before* the schema-simplification commits (`76c7c77` through `f4a4f12`).
- **Practical effect:** running the recorder's `OFFLINE 3` and later cells against the live schema, as the file stands right now, would raise a Pydantic validation error the first time `derive_target()` or `_cap()` runs. `PHASE2.md` already says this plainly in its own words: "the recorder, not yet rebuilt to this schema."

The rest of the gaps are ones the code and DECISIONS.md flag themselves:

| Gap | Where it's flagged |
|---|---|
| A `label` or `labeled_value` locator cannot be scoped to a container. Two identically-named things on a page (two "Edit" links) can be told apart with a `role`/`text` locator, but not with a `label` one, and the recorder does not yet check whether a name is duplicated before choosing a strategy. | DECISIONS.md D68, explicitly flagged as "a required test case, not an afterthought" for this rebuild. |
| Two identical clicks in a row are always treated as a repeat and dropped. A genuine intentional double "Next page" click would be lost. | D43, called out as a "known limit" in the decision itself. |
| Extraction only reads a *labeled* value. `transfer_funds` therefore has no declared output at all — its confirmation is a page heading, not a value next to a label. | D46, "known limit." |
| ~~Any run that used a human handoff (a value typed by a person, not the agent) is refused outright — it cannot be recorded, only avoided by declaring the value up front.~~ **Narrowed 2026-09-26 (D82), see the section below.** Only a genuinely *unstructured* handoff (`ask_human`, or a human taking over a risky click) still refuses the whole run. A `request_value`/`request_missing_values` handoff — one where the code already knows exactly which field(s) were opened for the human — is now recorded as a proper step instead. | D43 (original rule) / D82 (the narrowing) / `_refuse_bad_run()`'s own `CompileError` message. |
| ~~`drop_detours`'s dead-end-click removal only recognizes one shape (leave to a different URL, come straight back with nothing typed in between) and blanket-excludes risky clicks from ever being checked at all. A premature, failed risky click (e.g. a "Send Payment" submit fired before every required field was filled) survives compilation as a second, wrongly-positioned point of no return.~~ **Fixed 2026-09-26 (D86).** Risky clicks are no longer excluded from `drop_detours`, and a new `drop_dead_end_risky_clicks` drops a risky click proven — by a later click on the identical target with no state change in between — to be a dead end; two same-target risky clicks that both look real refuse the run outright rather than guess. | D23/D43 (original rule) / D86 (the fix) / `artifacts/pay_bill.yaml`, the real artifact this bug was found in. |
| ~~A human-entered value matching no declared input was kept as a hardcoded literal and only reported as a constant for a reviewer to notice — exactly the same treatment as an agent's own unmatched literal. In the real `pay_bill.yaml`, this baked in five throwaway discovery values (`'3'`, `'4'`, `'34'`, `'4'`, `'4'` for Address/City/State/Zip Code/Phone #) as permanent literals, silently resubmitted on every future replay.~~ **Fixed 2026-09-26 (D90).** A human-entered unmatched value is now auto-declared as a new input, named from the field's own label; an agent's own unmatched literal is unaffected. | D29/D44 (original rule) / D84 (the rule this fix corrects) / D90 (the fix) / `artifacts/pay_bill.yaml`, the real artifact this bug was found in. |
| An auto-declared human-entered input (D90) always gets a generic `type: string`, pattern `^.{1,80}$` — the recorder only ever saw one throwaway discovery value for it, so it has no basis to infer a stricter real-world shape (e.g. a 5-digit zip). A reviewer who wants tighter validation must hand-edit the pattern before promoting the capability to `verified`. | D90, "cost, honestly stated." |
| Capture has touched a real browser at least once — `notebooks/scratch/events_balance.json` holds 23 real logged events — but that saved run shows the agent stuck retyping the login form and clicking Log In repeatedly, ending in `finish` while still on `/login.htm`, never reaching the account overview page. It never got far enough to prove a real capture-to-compile round trip end to end. | Read directly from the saved event file; not a claim made anywhere in the docs. |

---

## The 2026-09-26 addition: a human-entered value is now recordable, not just a refusal

**The bug this fixes, from a real run:** a bill-pay discovery run filled 4 fields itself
(`type_text`), then called `request_missing_values` because fields were still empty. A human
filled in the rest by hand during the takeover — a text field (payee name, "Nagarjuana") and a
dropdown (account number, "12345"). The payment actually went through in the browser (a real $20
payment). But `compile_run` looked at that run afterward and refused to save anything at all:
*"a human entered a value by hand during this run. That step cannot be recorded."* The run worked;
the recorder just couldn't see that it had enough information to write it down.

**Why the old rule was too blunt:** the recorder decides a run is unrecordable by checking, for
every tool call, whether its result message starts with `"A human"` (`classify_status`, → status
`"handoff"`). But `"A human"` covers two very different situations:

| Tool | What it knows in advance | Can we reconstruct what happened? |
|---|---|---|
| `ask_human(question)` | Nothing — it's a free-form "figure out what's needed" | No. The human could have clicked, typed, navigated — anything. |
| A risky click's "take over" choice | Nothing specific either — the human is handed the whole button/page | No, same reason. |
| `request_value(ref, hint)` | The EXACT field (`ref`) it opened for the human | **Yes** — read that one field's live value after hand-back. |
| `request_missing_values(hints)` | The EXACT list of empty fields it opened | **Yes** — read each of those fields' live values after hand-back. |

The old rule treated all four rows the same. The fix only changes how the bottom two are handled.

**What was added, in the order it runs during a real capture, with examples:**

1. **`request_value`/`request_missing_values` get their own wrapper** (`BROWSER 10b` in
   `notebooks/03_recorder.py`), instead of sharing the generic one every other tool uses. Right
   after the human hands the browser back, the wrapper calls `current_value(ref)` — a function
   agent.ipynb already had, that reads whatever is *currently* sitting in a field (a textbox's
   `.value`, or a `<select>`'s selected option text). Example: for the bill-pay run above, this
   reads `"Nagarjuana"` out of the payee-name field, and `"12345"` out of the from-account dropdown.

2. **`synthesize_human_entries(...)` turns that into a proper event** — the same shape the recorder
   already gives a real `type_text`/`select_option` call. It looks at the field's `role` to decide
   the shape: a dropdown (`role: combobox`/`select`) becomes a `select_option`-shaped event; anything
   else becomes `type_text`-shaped. Example, in the shape the code actually produces:
   ```
   {"tool": "type_text", "args": {"ref": 8, "text": "Nagarjuana"}, "status": "ok",
    "human_entered": True, "why": "Value entered by a human during discovery; the agent did not have this value.", ...}
   {"tool": "select_option", "args": {"ref": 9, "option": "12345"}, "status": "ok",
    "human_entered": True, "why": "Value entered by a human during discovery; the agent did not have this value.", ...}
   ```
   If a field is still empty after hand-back (the human chose not to fill it), no event is made for
   it at all — that's treated the same as the agent never having filled it in.

3. **`compile_run`'s refusal narrows** to exactly the top two rows of the table above
   (`UNSTRUCTURED_HANDOFF_TOOLS = {"ask_human", "click"}`). The bottom two rows' own "a human took
   over" event is still logged (for audit visibility that a human was involved) but no longer, by
   itself, blocks the whole capability — the two synthesized events from step 2 are what actually
   become steps.

4. **The compiled capability shows its work.** Continuing the example: `pay_bill.yaml` now gets a
   `type` step for the payee name and a `select` step for the account, each carrying
   `why: "Value entered by a human during discovery; the agent did not have this value."` — so a
   reviewer opening the file later can immediately see which two values came from a human's hands
   during discovery, not the agent's own judgment, without digging through raw logs.

5. **Nothing about the existing safety checks was loosened to make this work.** A human-entered
   value still has to become `{{an_input}}` or get flagged, exactly like an agent-typed one: if it
   matches a declared input, it's parameterized; if it leaks into the capability somewhere that
   never got parameterized (say, the capability's own description text repeats "Nagarjuana"
   verbatim), the save is still refused, naming the input and the location; if it matches no
   declared input at all, it's kept and reported as a constant for a reviewer to see, never silently
   accepted.

`ask_human` and a risky click's "take over" are **unchanged** — those still refuse the whole run,
because there is genuinely no way to know what a human did with an open-ended handoff. See
DECISIONS.md D82–D84 and `docs/superpowers/plans/2026-09-26-recorder-human-entry-fix.md` for the
full reasoning and the offline fixtures that prove all of this (`notebooks/03_recorder.py`,
`OFFLINE 4c`/`4d`/`12b`–`12e`).

---

## How the three phases fit together

Phase 2 is the paper the recipe is written on, and the strict inspector that refuses a bad one. Phase 3 is meant to be the hand that fills that paper in, straight from a real, messy agent run — but as things stand today, that hand is still holding the *old* pen: it writes in a shape the Phase 2 inspector no longer accepts, and needs to be rebuilt against the current schema before it can produce a file Phase 4 could ever load. Once that's fixed, the pipeline is simple: Phase 3 produces the YAML, Phase 2's `Capability.model_validate` checks it the moment it's saved, and Phase 4's replay engine loads that exact same validated shape and walks it with no LLM in the loop — one artifact, checked once, written once, run any number of times after.
