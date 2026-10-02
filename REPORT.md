# REPORT

A computer-use system for a banking web app (ParaBank), in three parts:

- A **discovery agent** learns a task from screenshots.
- A **capability artifact** (YAML) records what it learned.
- A **replay engine** runs the artifact again with plain code and no LLM.

One installable package, `src/cua/` (map in `src/cua/README.md`), with a `cua` CLI and two demo
notebooks. Decision IDs: `Q*` in `notebooks/discovery/decisions.md`; `R*`/`P*` in
`notebooks/replay/`.

Status words: **built** (in the code and tested), **designed** (decided, not in the code),
**cut**.

## Architecture

**Pure visual seeing and acting (built).** Each step:

1. Screenshot a fixed 1280x800 page (Q10). RapidOCR reads it in `asyncio.to_thread`.
2. Every text box gets a red number; the agent sees the image plus `[7] 'Transfer'`.
3. The agent picks one tool, which acts with `page.mouse` / `page.keyboard` at a point.
4. A second screenshot checks it worked.

No DOM reads, no accessibility tree. Things with no text are pointed at by x,y (Q7).

**One exception: native `<select>` (built).** macOS draws its list outside the page, so
`SELECT_AT_JS` sets the option under the point; OCR confirms it. Clicking one only ever reads
NO CHANGE, so the `click` tool refuses a point on a `<select>` unclicked (`REFUSED: that is a
dropdown`); `select_option` chooses, and `extract_options` saves its option list as an
`options` output (a list, masked in evidence) that replay reads live by the recorded index.

**The agent (built).** A LangChain deep agent with 13 tools (`observe`, `click`, `type_text`,
`type_secret`, `select_option`, `scroll`, `open_path`, `extract_value`, `extract_table`,
`extract_options`, `finish_business_outcome`, `request_missing_values`, `ask_human`).

- Model: Sonnet via direct Anthropic (`ANTHROPIC_API_KEY`, `cua.llm.make_chat_model`).
- Middleware: prompt caching off; latest screenshot only; `RecordWhy` (see evidence). TypeSafe
  routing is opt-in (`TYPESAFE_API_KEY`).
- Run deadline (built): `DiscoveryConfig.run_timeout_s` (900). Past it the run ends `STUCK`
  ("discovery timed out after N s"); cleanup and evidence still run.
- Key rule: the agent picks the tool; our code decides if the action may happen.

**Replay (built)** shares vision, browser, safety and handoff code with discovery, and has no model
import (R1).

## Artifact schema

**Discovery writes the artifact directly (built, R10/R11).** `save_artifact` writes
`artifacts/<name>.yaml` + `artifacts/crops/<name>/`. Replay only loads it. Two sources:

- **Steps come from the event log**, the ground truth. `build_capability` drops failed or refused
  calls, keeps the last success per field, and trims the trailing logout.
- **Meaning comes from the model.** `describe()` writes only the name, descriptions and success
  text. It cannot add a step or an input.
- **Typed inputs (built).** Each typed value's *shape* is logged, never the value. The recorder
  infers the input type from it: `email`, `phone`, `date`, `currency`, `number`, `integer`, `id`,
  else `string`.
- The saved file is re-validated with replay's own model (integration-tested).

**Shape** (`Capability`, strict): `name`, `version`, `description`, `base_url`, `viewport`,
`device_scale_factor`, `inputs`, `outputs`, `secrets` (names only), `steps`, `checkpoint`.
Step types: `navigate | click | type | select | scroll | extract | extract_table |
extract_options` (`extract_options` runs under the site's `extract` permission). A `type` value
is always `{{input}}` or `{{secret:name}}`, never a literal.

**Targeting: three rungs, never raw x,y (built, R2/R13).**

| Rung | Field | Finds it by | Breaks when |
|---|---|---|---|
| 1 | `ocr_text` (+ `ordinal`) | its own OCR text | the text changes |
| 2 | `anchor` | a nearby label + a saved offset | the layout moves |
| 3 | `template` | `cv2.matchTemplate` of a tight crop; two near-equal peaks = a miss | the look changes |
| - | `table_cell` | row key + column, for look-alike rows (Q8) | the columns are renamed |

Crops are tight and other text in them is blanked, so no customer data is saved (Q14).

## Determinism & error handling

**Replay is deterministic code (built).**

1. Load and validate (viewport, host, inputs, secrets, crops).
2. Log out first if the capability types a secret before its first click (P8).
3. Ask every missing input in one form. Check given inputs: an unknown key or a value not of its
   declared type stops the run before the site opens (name and type only, never the value).
4. Walk the steps: rung 1, 2, 3; one scroll and retry; act; check by OCR on a bounded poll.
   A failed check is retried once, **never** for a send or a secret (R15).
5. A step whose action is not in `allowed_actions` fails before acting.
6. Check the `checkpoint` and the outputs.

**Statuses (built, R17).** `ReplayResult(status, outputs, drift, reason, human, failure)`:

| Status | When |
|---|---|
| `SUCCESS` | all steps done, checkpoint seen, outputs read |
| `DECLINED` | a human said no at Gate 2; nothing sent |
| `STUCK` | a human stopped it, rejected Gate 1, or an input was blank or wrong |
| `FAILED` | bad YAML, wrong screen size, host blocked, action not allowed, checkpoint or output missing |
| `BUSINESS_OUTCOME` | a known answer, e.g. "not found", "insufficient funds" |

Every non-success carries a masked `failure = {step, action, expected, observed}`.

**Error taxonomy (built).** Newly appeared OCR text is matched against `outcomes:` or config
defaults.

- **Business outcome:** stop as `BUSINESS_OUTCOME`. A legitimate answer.
- **Recoverable:** "session expired" or the login form returns. Re-run the login steps once, never
  after a send.
- **Hard failure:** "error", "access denied", a second expiry. Stop as `FAILED`.

**Multi-run stability (built).** `cua eval cap.yaml --runs N` replays a capability N times in one
session (`src/cua/eval.py`) and reports status counts, success rate, `flaky` (not every run had
the same status), human-assisted runs, a per-step rung histogram (cleanup rows kept apart), and
whether each output matched across the successful runs (a bool per name, never the value). The
drift signal is `fallback_steps`: a step whose first-choice rung (`rung1` or `table`) was not used
in every run. A capability can still pass while a step silently slides to an anchor or template;
that step is the one to re-discover before it breaks.

**Rescue (built).** A step that still misses opens the help panel: take over or stop (P2).

**Drift log and evidence (built, R18/P11).** Per step: rung, point, attempt, check result, no
values. Each run's masked evidence
folder (layout in `evidence/README.md`) includes `run.json`: prompt version, model, config hash,
git sha. Discovery events also carry a `why`: the model's text before the call, masked (run values
and value shapes blanked), max 200 chars.

## Heterogeneity & multi-tenant

**Designed, not built.** Pure visual needs no clean DOM, `id`s or `<label>`s. Rungs store what a
control looks like and where it sits, never an app ID or raw pixel.

- **One base capability per vendor product, plus small per-tenant overrides** (e.g. "Sign In"
  instead of "Log In"). A vendor update fixes the base once.
- **Per-tenant config (built).** Every site value lives in `configs/<site>.yaml`, loaded into a
  frozen `SiteProfile`: base URL, secret env-var names, allowed hosts, words, and
  `allowed_actions`. A second tenant is one more file, not a code change.
- **Drift detection** from the per-step rung in the drift log.

## Escalation & handoff

**Control tab and site lock (built, Q16/Q21).** Our own "Agent control" tab shows who is in
control. CDP `Input.setIgnoreInputEvents` blocks human input on the site except during a take-over.

**When the human is asked (built):**

- Missing values: `request_missing_values`, one form per page. Our code types and reads back.
- Unsure: `ask_human`, or automatically after 3 failed results in a row, the same call 3 times,
  40 steps, or a login failure. Choices: answer, take over, stop.
- Sends: the two gates (see Safety).

**Take over (built).**

- The human works in the live session, then hands back (toolbar button or Done).
- We record pages, send paths and screenshots, never keystrokes. Sends still hit both gates.
- `build_capability` refuses to save a run with a take-over.
- In replay it shows on `result.human`, e.g. `SUCCESS (human intervened at step 5)`.

## Safety

- **Every send is held at the network layer (built).** `SendGuard` (`page.route`) holds every
  non-GET request, however triggered; login is exempt. Then:
  1. **Mismatch check.** Any number the human never gave opens a prefilled form for those fields.
  2. **Gate 1:** approve or edit the details.
  3. **Gate 2:** send it? No means `DECLINED`, nothing sent.

  The agent never approves a send. Replay never auto-approves one (R15).
- **Confirmation saved (built).** The prompt tells the agent to `extract_value` the confirmation or
  reference number (`id`), else the message (`string`), before `finish_business_outcome`. Never
  invented.
- **Allowed actions (built).** `allowed_actions` in the site config (ParaBank: `navigate`, `click`,
  `type`, `select`, `scroll`, `extract`, `extract_table`). Discovery refuses any other (`REFUSED`,
  logged). Replay fails that step before acting.
- **Nothing is stored (built, R7).** Values never enter logs or YAML and are wiped at run end.
- **Secrets (built).** `type_secret(name)`: the model sees only the name.
- **Host lock (built).** Only `parabank.parasoft.com`.
- **Deny words (built).** Clicks on `register`, `lookup`, `admin` are refused.

## Cuts

1. **Per-keystroke take-over capture (cut).** A take-over stays unreplayable; the save refuses it.
2. **Desktop surfaces (cut).** Browser only.
3. **Whole-screen OCR for OS-drawn menus (cut).** Needs OS permissions.
4. **Multi-tenant plumbing (designed).** See above.
5. **Discovery-written outcome rules (cut).** Discovery does not write `outcomes:` yet.
6. **Per-step `expect` text (cut, R14).**
7. **Sitemap hint (designed, Q15).** Not built; ParaBank has no sitemap.
8. **A hostile legacy test page (cut, Q18).** Proven live on ParaBank only.
9. **One shared module (built).** `src/cua/` is the single port, one `SendGuard` for both sides.
10. **Assisted-LLM replay fallback, cross-process approvals, live CI tests (cut).** Offline suites
    use fake pages.
