# REPORT

A computer-use system for a real banking web app (ParaBank). It has three parts. A discovery
agent learns a task from screenshots. The capability artifact records what it learned. A replay
engine runs the artifact again with plain code and no LLM. Both engines are notebooks, written as
the production design: `notebooks/discovery/discovery.py` and `notebooks/replay/replay.py`
(jupytext pairs of the `.ipynb` files). Decision IDs: `Q*` are in
`notebooks/discovery/decisions.md`, `R*` and `P*` are in `notebooks/replay/DECISIONS.md` /
`PLAN.md`. An earlier DOM-based stack was removed (2026-10-01). Only its model factory and config
remain, in `src/cua/models.py` and `src/cua/config.py`.

Status words used below: **built** (in the code and tested), **designed** (decided, not in the
code), **in progress** (being added now), **cut**.

## Architecture

**Seeing and acting are pure visual (built).** Each step works like this:

1. A Playwright screenshot of a fixed 1280x800 page at `device_scale_factor=1` (Q10). The Browser
   cell refuses to start if the screenshot is any other size.
2. RapidOCR reads it. It returns text, boxes, and scores.
3. Every text box gets a number, drawn as a red box on the image (OpenCV).
4. The agent sees the numbered image plus a text list like `[7] 'Transfer'`. It picks one tool.
5. The tool acts with `page.mouse` / `page.keyboard` at a point.

There are no DOM reads, no `page.fill`, and no accessibility tree. Things with no text (empty
boxes, icons) get no number. The agent points at them by x,y (Q7). A second screenshot checks
that the action worked: the typed text is read back, a secret shows as dots, a click changed the
screen.

**The one non-visual exception: native `<select>` dropdowns (built).** On macOS the OS draws the
open option list outside the page. No screenshot shows it, and no key sent to the page moves it.
For the `<select>` under the point only, `SELECT_AT_JS` reads its options and sets one. OCR of the
closed box still confirms the choice. We rejected whole-screen OCR plus a real OS mouse (it needs
OS permissions and a big build).

**The agent (built).** A LangChain deep agent (`create_deep_agent`) with 11 tools: `observe`,
`click`, `type_text`, `type_secret`, `select_option`, `scroll`, `open_path`, `extract_value`,
`finish_business_outcome`, `request_missing_values`, `ask_human`. It runs with a `MemorySaver`
checkpointer. The model is Sonnet through the Iliad gateway (`cua.models.make_chat_model`). Two
small middlewares: one turns off prompt caching (the gateway rejects it), one sends the model
only the latest screenshot (old numbers are stale). The rule that matters most: the agent picks
the tool, but the tool's own code decides whether the action may happen. The host check, the
lock, and the send gates all run inside our code, whatever the model asked for.

**Replay (built)** reuses discovery's own vision, lock, control tab, and send guard, copied
verbatim for now (R4). It has no model import at all (R1).

## Artifact schema

**Discovery writes the artifact directly (built, R10/R11).** The artifact is `schema_version: 2`
YAML plus `crops/<name>/s<i>.png`, written by discovery's `## Save artifact` section. Replay only
loads it. It never edits or recompiles it. The artifact is a hybrid of two sources:

- **Steps come from the event log**, the ground truth of what actually ran:
  - `build_capability` drops failed or refused tool calls.
  - It keeps only the last success per field.
  - It trims the trailing logout.
  - It maps each event to a step.
- **Meaning comes from the model.** `describe()` uses structured output (`CapabilityMeta`) for
  the name, the description, the input descriptions, and the success text. The model cannot add
  a step or an input. Input names it makes up are ignored, and a bad name is slugged, so the
  model's text can never fail the build.
- `save_artifact` writes the file, then re-validates it with the same Pydantic model replay uses.
  `tests/replay/test_round_trip.py` proves it: build, save, then replay's `load_capability`, with
  no changes.

**Shape** (`Capability`, strict, `extra="forbid"`): `name`, `version`, `description`, `base_url`,
`viewport`, `device_scale_factor`, `inputs`, `outputs`, `secrets` (names only), `steps`, and
`checkpoint` (text that proves success on the final screen). Each step is one of six types:
`navigate | click | type | select | scroll | extract`. A `type` value is always `{{input}}` or
`{{secret:name}}`, never a literal.

**Targeting: three rungs, never raw x,y (built, R2/R13).** A `Target` holds any of these:

| Rung | Field | Finds it by | Breaks when |
|---|---|---|---|
| 1 | `ocr_text` (+ `ordinal`) | its own OCR text; exact for anything with a digit (P3) | the text changes |
| 2 | `anchor` (label, `ordinal`, `offset`) | a nearby label + a saved pixel offset | the layout moves |
| 3 | `template` | `cv2.matchTemplate` of a tight crop; two near-equal peaks = a miss | the look changes |
| - | `table_cell` (row key, column) | extracts in look-alike table rows (Q8) | the columns are renamed |

A target must have at least an anchor, a template, or a table cell. Crops are cut tight, and any
other text inside them is blanked, so no customer data is saved (Q14).

## Determinism & error handling

**Replay is deterministic code (built).** The run goes in this order:

1. Load and validate the YAML. The run refuses when:
   - the viewport or scale is wrong;
   - the host is not allowed;
   - an `{{input}}` is undeclared;
   - a secret is missing from `.env`;
   - a crop file is missing.
2. Log out first if the capability types a secret before its first click (P8).
3. Open `base_url` and check the screenshot size.
4. Show one control-tab form asking every input.
5. Walk the steps. For each step:
   - Try rung 1, then 2, then 3 (or the table cell).
   - If all miss, scroll once and retry (`CFG.scroll_retries`).
   - Act through discovery's `act` / `into_box` / `choose_option`.
   - Check by OCR on a bounded poll.
   - A failed check is retried once. It is **never** retried for a send or a secret (R15). A slow page can never fire a payment twice.
6. Check the `checkpoint` text and the declared outputs.

**Statuses (R17).** `ReplayResult(status, outputs, drift, reason, human, failure)`:

| Status | When | In code |
|---|---|---|
| `SUCCESS` | all steps done, checkpoint seen, outputs read | built |
| `DECLINED` | a human said no at Gate 2; nothing sent | built |
| `STUCK` | a human stopped it, rejected Gate 1, or left an input blank | built |
| `FAILED` | bad YAML, wrong screen size, host blocked, checkpoint or output missing | built |
| `BUSINESS_OUTCOME` | a known answer appears, e.g. "not found", "insufficient funds" | built |

- Every non-success result carries `failure = {step, action, expected, observed}`. `observed` is
  masked.
- `NEEDS_APPROVAL` from the old engine is retired. Approval now happens live in the control tab,
  and a closed tab fails closed.

**Error taxonomy (built, R17).** After every step, replay compares the new OCR text on the screen
with what was there before. Only newly appeared text counts, matched as whole words, so help text
already on the page never triggers. The rules come from the capability's optional `outcomes:`
list, else generic defaults in config. There are no site words in code. Each match falls into one
of three classes:

- **Business outcome:** e.g. "not found", "insufficient funds". The run stops as
  `BUSINESS_OUTCOME` with the rule's meaning. It is a legitimate answer, not a crash.
- **Recoverable:** "session expired", or the login form reappearing mid-run. Replay re-runs the
  capability's own login steps once, then retries the step. It never does this after a send, and
  only once per run. `result.recoveries` counts it. Slow pages are handled by bounded waits.
- **Hard failure:** "error", "access denied", or a second expiry. The run stops as `FAILED`, with
  the step, what was expected, and the first 200 characters of what was on screen.

**Caller inputs (built).** `replay(path, inputs={...})`:
- Keys match declared inputs by exact name, ignoring case.
- An unknown key stops the run before the site opens: "not a permissible input".
- Anything not given goes to one upfront form. So an AI agent can run it unattended, and a human
  can still fill the gaps.

**Rescue (built).** A step that still misses opens the help panel, with two choices: take over or
stop. Replay has no LLM to read a free-text answer (P2).

**Drift log and evidence (built, R18/P11).**
- The drift log records, per step: the rung used, the point, the attempt, and whether the check
  passed. It holds no values. A step that keeps falling to rung 2 or 3 is the signal to
  re-discover.
- `save_evidence` writes `evidence/replay/<UTC>-<name>/`: `summary.json`, `drift.jsonl`,
  `failure.json`, `final.png`, take-over before/after shots, and a copy of the capability. All of
  it is masked.

## Heterogeneity & multi-tenant

This is **designed, not built**, as the brief allows. Pure visual already covers the hardest part
of heterogeneity. The engine never assumes a clean DOM, `id`s, `<label>`s, or even HTML. Anything
that draws text on a screen can be targeted. The rungs describe *what a control looks like and
where it sits relative to its label*. They never store an app-specific ID or a raw pixel.

The design, carried over from the earlier DOM stack's reasoning:

- **One base capability per vendor product, plus small per-tenant overrides.** Not one artifact
  per tenant. An override patches only what differs, e.g. rung 1 text "Sign In" instead of
  "Log In", or a new crop for a rebranded button. A vendor UI update then fixes the base once.
- **Per-tenant deployment config**, kept outside the artifact: the `base_url`, the secret env-var
  names, the allowed hosts, and `safe`/`login`/`deny` words. The engine already keeps site values
  in `Config` and the capability, not in tool code (R9). Moving them into a per-tenant file is
  config work, not a redesign.
- **Drift detection from data we already log.** The per-step rung is in the drift log. A tenant
  whose runs keep falling from rung 1 to rung 3 has drifted from the base.
- **Theme and scale.** The fixed viewport and scale factor are saved per capability. A tenant with
  a different theme would need its own crops (rung 3) but could share rungs 1 and 2.

This was not built because the brief says tenant plumbing is not rewarded. Nothing in `Target`,
`Step`, or the step loop would change to add it.

## Escalation & handoff

**The control tab (built, Q16/Q21).** A second tab in the same browser, "Agent control", is our
own page (`set_content`, nothing injected into the site). It comes to the front when a human is
needed. It always shows who is in control.

**The site lock (built).** `SiteLock` sends CDP `Input.setIgnoreInputEvents` to the site tab for
the whole run. It lifts only for the instant of our own mouse or keyboard call (unlock, act,
relock, in `finally`), or during a take-over. A human cannot click or type on the site outside a
take-over.

**When the human is asked (built):**
- Missing values: `request_missing_values` opens one form per page. Each row shows the field's
  crop and a box, masked if sensitive. Our code types the values in and reads them back.
- Unsure: `ask_human`, or the tool results trigger it. The panel opens by itself after:
  - 3 failed tool results in a row (`unsure_limit`);
  - the same call repeated 3 times;
  - 40 steps (`step_budget`);
  - login hitting its limit or a failure text.
  The panel has three choices: **answer** (text back to the agent), **take over**, **stop**.
- Sends: the two gates (see Safety).

**Take over (built).**
- The site unlocks and the human works in the same live session, then clicks Done. The lock comes
  back *first*, then a new look.
- What we record is evidence, not steps: the page paths visited (a `framenavigated` listener,
  attached only while the human holds control), the send paths (from `guard_send`; no query, no
  body), and screenshots at start and hand-back. We record pages, sends and screenshots rather
  than each keystroke, because keystrokes would mean storing typed values.
- **Hand-back (built).** The human hands back with a browser-extension toolbar button (badge
  YOU / AI; no content scripts, no host permissions, so it never touches any site), or Done in
  the control tab. Nothing prompts them while they work: an idle "are you done?" reminder was
  tried and removed as an interruption.
- The human's own sends during a take-over still go through both gates.
- `build_capability` **refuses to save a run that had a take-over**, because a human did steps we
  cannot see.
- In replay, the take-over is recorded on `result.human` (`{step, reason, actions}`), and
  `result.summary` reads e.g. `SUCCESS (human intervened at step 5)`. A calling agent must check
  `human`, not just `status`.

## Safety

- **Every send is held at the network layer (built).** `guard_send` is a `page.route` handler.
  Every request except GET/HEAD/OPTIONS is held, however it was triggered: a click, Enter, or the
  page's own script. No button names are involved. The login click is the only exemption
  (`login_words`). Then, in order:
  1. **Mismatch check.** Every number the request carries is compared with every number the human
     gave (the goal, the answers, the form values; the caller's inputs at replay). Any number the
     human never gave, e.g. account 1450 when they said 1400, opens a form for just those fields,
     prefilled. The corrected value is what gets sent. Skipping the form blocks the send.
  2. **Gate 1: Approve / Edit** the details being sent.
  3. **Gate 2: send it?** A no at Gate 2 means `DECLINED`, and nothing is sent.

  The agent never approves a send. Replay never auto-approves one (R15). An earlier click-level
  gate was tried and failed live: a form left on its dropdown defaults went through ungated.
- **Nothing is stored (built, R7).**
  - Typed, selected, and human-given values never enter the event log (labels and positions
    only), the YAML, or the drift log.
  - Working values are wiped in `finally` when a run ends.
  - `flag_leaks` marks any label that equals a run value, and the save then refuses.
  - `save_evidence` refuses to copy an artifact that holds a run value.
  - Evidence is masked: `***` in text, and black boxes over any OCR text in a PNG that matches a
    run value or a secret.
- **Secrets (built).** `type_secret(name)` types the value from `.env` by keyboard. The model
  sees only the name, and `hide_secrets` strips values from any OCR text shown to it. At replay,
  a secret visible as plain text on screen stops the run.
- **Host lock (built).** `host_allowed` allows only `parabank.parasoft.com`, on every
  `open_path`, on `base_url` at load, and after a take-over (replay fails, discovery navigates
  back).
- **Deny words (built).** Clicks on `register`, `lookup`, and `admin` are refused outright.
  Per-click Approve was removed on 2026-09-29: the human is asked only about sends, take-overs,
  and doubt.

## Cuts

0. **`cua eval --runs N` (planned next, deferred 2026-10-01).** Replay a capability N times and
   report a stability score: status counts + which rung found each step. The assignment's
   "multi-run stability" stretch goal. Design in `docs/PRODUCTIONIZE_PLAN.md` step 12.

1. **Per-keystroke take-over capture.** We record pages, sends, and screenshots, not what the
   human typed. The design is a report-only listener that logs *which labelled field* got input,
   never the value. So a take-over is still not replayable, and the save refuses it.
2. **Desktop surfaces.** Browser only. The vision and act layers use only screenshots and
   mouse/keyboard, so a desktop backend would reuse them. The `<select>` exception and the CDP
   lock are browser-specific.
3. **Whole-screen OCR for OS-drawn menus.** This would replace `SELECT_AT_JS` and cover
   streamed or remote-desktop targets. It needs OS screen and input permissions.
4. **Multi-tenant plumbing.** Designed above, not built.
5. **Input `pattern`s and discovery-written outcome rules.** Replay classifies outcomes from an
   optional `outcomes:` list or config defaults. Discovery does not yet write that list from what
   it saw, and a malformed input is only caught by the page (open question P1b).
6. **Per-step `expect` text.** Replay checks each step by OCR itself, plus the final checkpoint.
   It does not check for the specific next page (R14 leftover).
7. **Sitemap hint (Q15).** Decided, not in the current notebook (ParaBank has no sitemap anyway).
8. **A hostile legacy test page (Q18).** Deferred. Proven live on ParaBank only, so framesets and
   nested tables are unproven.
9. **One shared module.** Replay copies discovery's vision, lock, and gate cells verbatim. The
   `src/cua/` port that merges them is not done.
10. **Assisted-LLM replay fallback, parked/resumable approvals across processes, live end-to-end
    tests in CI.** Not built. The offline suites (`tests/discovery`, `tests/replay`) drive the
    notebook cells against fake pages instead.
