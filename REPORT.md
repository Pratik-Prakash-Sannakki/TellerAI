# REPORT

A computer-use system for ParaBank: a **discovery agent** learns a task from screenshots, writes a
**capability artifact** (YAML), and a **replay engine** runs it again with plain code, no LLM.
One package, `src/cua/`, with a `cua` CLI. Setup and commands: `README.md`. Decisions: `Q*` in
`notebooks/discovery/decisions.md`, `R*`/`P*` in `notebooks/replay/`. **Built** = in code and
tested; **designed** = decided, not built.

## Architecture

**Pure visual (built).** Each step: screenshot a fixed 1280x800 page (Q10); RapidOCR numbers every
text box (`[7] 'Transfer'`); the agent picks one tool, which acts with `page.mouse` /
`page.keyboard` at a point; a second screenshot checks it worked. No DOM, no accessibility tree.
Trade-off: slower and OCR-noisy, but it works where there is no clean DOM.

- **One exception: native `<select>`.** macOS draws it outside the page, so a script sets the
  option under the point and OCR confirms. `click` refuses dropdowns.
- **Agent:** a LangChain deep agent, 13 tools. Every call goes through `cua.llm.make_chat_model`.
  Latest screenshot only; a 900 s deadline ends the run `STUCK`, evidence intact.
- **Key rule:** the agent picks the tool; our code decides if the action may happen.
- **Observability:** discovery is traced in LangSmith (env vars only): the full agent trace, latency per model/tool call, and token usage and cost per run by model. Replay makes no model calls.
- **Replay** shares vision, browser, safety and handoff code, and imports no model (R1).

**Routing (built, opt-in).** TypeSafe classifies each step's job and picks the model. Its models
are RLCD-trained (calibrated confidence), so a fixed 0.8 gate is meaningful. From the
live transfer discovery: confidence was 0.35–0.53 on most steps, 0.86 once (form fill), so tool
narrowing rarely engaged (it fails open by design). Model routing sent most steps to Haiku and
switched to Sonnet near the end.

## Artifact schema

Discovery writes `artifacts/<name>.yaml` + `artifacts/crops/<name>/` directly (R10/R11). Two
sources, kept apart:

- **Steps come from the event log**, the ground truth. Failed or refused calls are dropped.
- **Meaning comes from the model.** `describe()` writes only name, descriptions and success text.
  It cannot add a step or an input.
- **Typed inputs.** Only each value's *shape* is logged; the type is inferred from it (`email`,
  `date`, `currency`, `id`, ... else `string`).
- **Checkpoint:** stable final-screen text, never a value or a lone label (cdb3b7e).

**Shape** (`Capability`, strict): `name`, `version`, `description`, `base_url`, `viewport`,
`inputs`, `outputs`, `secrets` (names only), `steps`, `checkpoint`. A `type` step's value is
always `{{input}}` or `{{secret:name}}`, never a literal.

**Targeting: rungs, never raw x,y (R2/R13).**

| Rung | Finds it by | Breaks when |
|---|---|---|
| 1 `ocr_text` | its own OCR text (+ ordinal) | the text changes |
| 2 `anchor` | a nearby label + saved offset | the layout moves |
| 3 `template` | `cv2.matchTemplate` of a tight crop; two near-equal peaks = miss | the look changes |
| `table_cell` | row key + column (Q8) | columns are renamed |

Crops are tight with other text blanked, so no customer data is saved (Q14).

## Determinism & error handling

**Replay (built):** validate the artifact; ask missing inputs in one form and reject wrong types
before the site opens; per step try rung 1, 2, 3, scroll once, act, check by OCR on a bounded poll.
A failed check is retried once, **never** for a send or a secret (R15). Then check the checkpoint
and read outputs.

| Status (R17) | When |
|---|---|
| `SUCCESS` | steps done, checkpoint seen, outputs read |
| `BUSINESS_OUTCOME` | a known answer, e.g. "not found", "insufficient funds" |
| `DECLINED` | a human said no at Gate 2; nothing sent |
| `STUCK` | a human stopped it or rejected Gate 1, or an input was blank or wrong |
| `FAILED` | bad YAML, host blocked, action not allowed, checkpoint or output missing |

Every non-success carries a masked `failure = {step, action, expected, observed}`. New OCR text is
matched against `outcomes:` in config: a business outcome stops cleanly; "session expired" re-runs
login once (never after a send); "error" or a second expiry is `FAILED`.

**Drift (built).** Each step logs its rung. `cua eval --runs N` reports status counts, flakiness,
and whether outputs matched (a bool, never a value). A step that slid off its first rung is the
one to re-discover; anchor-only steps are not flagged (c007853).

**Live verification (2026-10-02, current package):**

- Discover → replay `get_all_account_balances`: `SUCCESS`, one row read.
- `pay_bill_to_payee` replay: `SUCCESS`, confirmation read. `get_transfer_account_options`:
  `SUCCESS`.
- `request_loan`, down payment above balance: `BUSINESS_OUTCOME` "not enough funds for the down
  payment (loan denied)".
- `cua eval get_all_account_balances --runs 3`: 3/3 `SUCCESS`, outputs stable, no drift.
- Fresh discover + replay `transfer_funds_between_accounts`: `SUCCESS`, confirmation read. The demo
  DB had reset, so the requested account was gone; replay asked the human to pick a live one
  instead of guessing.

**Bugs those runs found (each fixed test-first):**

- Table header matched a menu item that only starts with the label (85595bf).
- Menu text on the header line made tables read empty (aa8cbe5, 27ef5ef; shared with discovery).
- OCR dropped a space ("1 Main" → "1Main"): typed check failed, value slipped past masking (07664f2).
- Loan-denial wording now maps to `BUSINESS_OUTCOME` (5915a22, config only).
- Read steps were skipped after a take-over reached the checkpoint (0c4c75a).
- CLI could abort at exit on macOS in onnxruntime teardown (b8f5c4a).

## Heterogeneity & multi-tenant

**Designed.** Pure visual needs no `id`s or `<label>`s, so legacy web is the same path. The seam:
perception/action (screenshot, OCR, point input) versus the recorded flow (rungs). Desktop swaps
only the screenshot and input layer.

- **One base capability per vendor product, plus small per-tenant overrides** (e.g. "Sign In" vs
  "Log In"). A vendor update fixes the base once.
- **Per-tenant config (built).** All site values live in `configs/<site>.yaml`. A second tenant is
  one file, not a code change.
- **Drift per tenant** from rung logs and `cua eval`.

## Escalation & handoff

- **Who is in control (built, Q16/Q21).** Our "Agent control" tab shows it. CDP
  `Input.setIgnoreInputEvents` blocks human input on the site except during a take-over.
- **Stuck detection (built).** `ask_human`, or automatically after 3 failures in a row, the same
  call 3 times, 40 steps, or a login failure. Choices: answer, take over, stop.
- **Take over (built).** The human works in the same live session, then hands back (toolbar button
  or Done). We record pages, send paths and screenshots, never keystrokes. Sends still hit both
  gates. Discovery won't save a take-over run; replay reports it on `result.human`.
- **Live demo.** `takeover_demo` has step 3's target broken on purpose. Result: `SUCCESS (human
  intervened at step 4)`, outputs still read after hand-back.

## Safety

- **Guardrails (NeMo):** the goal is checked before any work (off-topic, jailbreak, steering,
  sensitive), embeddings first with a Haiku fallback; refused goals exit 1 with REFUSED
  evidence. The answer is masked on the way out. Both fail closed.
- **Every send held at the network layer (built).** `SendGuard` (`page.route`) holds any non-GET
  (login exempt). A number the human never gave opens a prefilled form; then Gate 1 (approve/edit)
  and Gate 2 (send?). No means `DECLINED`. Neither agent nor replay ever approves a send.
- **Allowlists.** Host lock (`parabank.parasoft.com`), per-site `allowed_actions`, deny words.
  Discovery refuses outside them; replay fails before acting.
- **Secrets.** `type_secret(name)`: the model sees only the name.
- **Nothing stored (R7).** Values never enter logs or YAML. Account ids show only their last 3
  digits, in text and PNGs. URLs drop `;jsessionid=`. Artifacts are leak-checked before writing.
  TypeSafe sees no screen text. The browser profile is deleted at close.

**Data-handling note.** Older discovery runs logged a ParaBank session id (jsessionid) and two raw
account ids before masking covered them. Those files are re-masked (2ca336a);
`tests/integration/test_evidence_clean.py` now fails CI on any leak; `scripts/remask_evidence.py`
re-masks. The old values stay in earlier git history (expired demo session ids, public demo-bank
fake accounts); history was deliberately not rewritten.

**Limits.** Masking is only as good as OCR (see 07664f2). The gates trust the human reading them.

## Cuts

- **Cut:** per-keystroke take-over capture (a take-over run stays unreplayable); desktop and
  whole-screen OCR; discovery-written `outcomes:`; per-step `expect` text (R14); a hostile legacy
  test page (Q18); assisted-LLM replay fallback; live CI tests (offline suites use fake pages).
- **Designed only:** multi-tenant plumbing; sitemap hint (Q15).

**Next:**

- Copy each run's LangSmith token and cost totals into `run.json`, so evidence carries cost without the dashboard.
