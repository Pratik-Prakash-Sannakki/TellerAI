# Phase 2 — The Artifact Schema

**What this phase is, in one line:** the format of the recipe card every automated task gets written on, plus a strict inspector that refuses a bad recipe before it ever reaches a real run.

**Built in:** `notebooks/02_artifact_schema.py` (+ paired `.ipynb`)
**Examples:** `artifacts/examples/get_account_balance.yaml`, `artifacts/examples/transfer_funds.yaml`
**Decisions:** `DECISIONS.md` — original design D7–D12, D37–D40; simplification D63–D68

---

## The idea, in plain terms

Before an AI can safely repeat a task without a human watching, someone has to write down exactly what it does — like a recipe card:

- **Ingredients** — what you need to give it (an account number, an amount).
- **Steps** — what to do, in order.
- **How you know it's done** — a real proof, not a guess.
- **What a weird result means** — a normal answer, something fixable, or a genuine break.

Phase 2 is that recipe card's **template**, plus a strict inspector that rejects any card that's missing something or contradicts itself. It doesn't watch an AI work (that's Phase 3), and it doesn't run anything in a browser (that's Phase 4, already built). It only defines the paper the recipe is written on, and refuses a bad one.

---

## The building blocks

| Piece | Plain-English meaning |
|---|---|
| **5 ways to find something on screen** | By role+name ("the button named Log In"), by label, by visible text, by position inside a container, or "the value next to this label" (reading only, never clicking). |
| **Target** | One main way to find a thing (`primary`), plus one optional backup (`fallback`), tried only if the primary breaks. No third slot exists — it's structurally impossible, not just discouraged. |
| **A trust reason, required** | Every locator must say *why* it's trusted. No reason, no locator. |
| **Checkpoint** | The final "did this actually work?" proof. Must check both the page's address **and** its text — either alone isn't enough. |
| **5 actions** | navigate, click, type, select, extract. Every step in a recipe is one of these. |
| **3 kinds of surprises** | `business` (a normal answer, e.g. "no such account"), `recoverable` (fixable, e.g. "log in again"), `hard` (a genuine break). |

---

## Cell by cell

| Cell | What's built | Example |
|---|---|---|
| 1 | A note explaining this is the simplified rebuild. No code. | — |
| 2 | The building blocks above — locators, `Target`, `Checkpoint`, the 5 actions, the 3-way outcome taxonomy. | `transfer_funds.yaml`'s amount field: **primary** — `strategy: label, label: 'Amount:'`. **fallback** — `strategy: structure, tag: input, within: {role: form}, nth: 1`, only tried if the primary breaks. |
| 3 | Tests for Cell 2 — deliberately broken recipes, checked to be rejected. | Fallback claimed *more* reliable than the primary → rejected. A "3rd item on the page" locator with no named container → rejected. A locator missing its trust reason → rejected. |
| 4 | The full recipe: bundles everything into one task, cross-checks it end to end, and figures out which pages it visits by itself. | `transfer_funds.yaml` declares `risk_level: risky` **and** marks its Transfer click `risk: risky` with `amount_input: amount` — the cross-check confirms these agree. The visited-pages list isn't hand-written; it's read straight off the one `navigate` step, `/transfer.htm`. |
| 5 | Save/load as YAML — the exact file format the two example files use. Re-checked every time it's read back. | The raw file text (`strategy: labeled_value`, `label: 'Balance:'`) *is* the saved form of the checked object — no hidden translation step. |
| 6 | Tests for Cells 4–5: loads both real files and confirms they pass, then breaks things on purpose. | `description` misspelled as `descripton` → rejected. `{{acount_id}}` (typo) → "unknown input." Transfer's click marked `risk: safe` → rejected, since `risk_level: risky` no longer matches any step. |
| 7 | A short card describing the task to a calling AI: what it needs, what it returns, whether a human might need to approve it. | `transfer_funds`: needs `from_account`, `to_account`, `amount`; returns `confirmation`; `may_need_approval: true`. `get_account_balance`: `may_need_approval: false`, lists `ACCOUNT_NOT_FOUND` as a possible answer. |
| 8 | Tests for Cell 7 — confirms that card is actually correct, not just present. | The transfer card's required-inputs list must be *exactly* `[from_account, to_account, amount]`. |
| 9 | What comes back after really running a task: worked, a known real-world answer, paused for a human, or broke. | Balance read successfully → `SUCCESS, outputs: {balance: "$1,200.00"}`. Bad account number → `BUSINESS_OUTCOME, outcome: ACCOUNT_NOT_FOUND` — a real answer, not a crash. |
| 10 | Tests for Cell 9 — a result can't lie about itself. | Claiming `SUCCESS` but missing the promised `balance` → rejected. Naming an outcome the recipe never declared → rejected. |

**The thread through the whole table:** every "mistake" caught above would otherwise only surface while a real customer is mid-transaction. Catching it the moment the file loads is the entire point of this phase.

---

## What changed in the simplification (D63–D68)

| Cut | Why |
|---|---|
| Up to 3 ranked locators per step | Down to one primary + one optional fallback. The brief asks for identification *with reasoning*, not a fallback chain. |
| `app.id`, `vendor`, `base`, `overrides` (multi-tenant fields) | Cut from the schema entirely — moved to the write-up as a design discussion (the brief itself says "design, not necessarily build," 3.7). Only `base_url` remains. |
| `routes` as a separately maintained field | Now derived automatically from the `navigate` steps, so it can't go stale. |
| `when_to_use` as its own field | Folded into `description` — one field, not two. |

Everything the brief actually grades — typed inputs/outputs, the checkpoint, the 3-way outcome taxonomy, risk marking, secrets referenced by name only — is unchanged.

## Two known, honestly-stated gaps (D67, D68)

- **An element with no name at all** (no label, no aria-label, no visible text) still gets found, numbered, and shown on screen — only its *name* comes back empty. Downstream, this falls back to a generic `"field N"` unless the model supplies its own visual reading (Phase 1, D53).
- **Two elements with the identical name** (e.g. two "Edit" links) are told apart fine during discovery (different numbers, different positions, visible in the picture) — but at replay time, only `role` and `text` locators can be scoped to a specific container to disambiguate them. `label` and `labeled_value` locators cannot be scoped at all yet. Flagged as a required test case for the Phase 3 recorder rebuild.

## What Phase 2 is not

- It does not watch an AI work — that's **Phase 3** (the recorder, not yet rebuilt to this schema).
- It does not run anything in a browser — that's **Phase 4** (`notebooks/04_replay_engine.py`), already built and tested against these two example files.
