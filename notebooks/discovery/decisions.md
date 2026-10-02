# Discovery decisions

Questions and decisions for the pure-visual discovery engine (redesign, in design). Nothing here
is built yet. Source of truth for the wider design: `ARCHITECTURE.md` §4. Diagram and tool list:
`discovery_architecture.md` in this folder.

Status key: **DECIDED** = user-confirmed. **OPEN** = not answered yet. All questions are now decided.

## Summary

| # | Question | Decision | Status |
|---|---|---|---|
| Base | How does discovery see the screen? | Pure visual: screenshot → OCR → mouse/keyboard. No DOM reads | DECIDED |
| Q7 | Things with no text (empty boxes, icons) | No shape detector. The agent points at them itself | DECIDED |
| Q7b | How does replay find those things? | Rung 2 (label + offset) and rung 3 (picture). No rung 1, no raw x,y | DECIDED |
| Q8 | Tables with look-alike rows | Row + column rule (`TableCellLocator`), no detector | DECIDED |
| Q9 | Image library | OpenCV, for pixel jobs only | DECIDED |
| Q10 | Window size and zoom | Locked, saved in the capability | DECIDED |
| Q11 | Notebook format | `notebooks/discovery/discovery.py` + paired `discovery.ipynb` | DECIDED |
| Q12 | Dropdowns | Keyboard: type the option + Enter, ↓ as fallback | DECIDED |
| Tools | How to type into boxes with no number | `type_text` / `type_secret` take a number or a point | DECIDED |
| Q13 | Scrolling | `scroll` tool + fresh look + renumber | DECIDED |
| Q14 | Private data in saved pictures | Tight crop + blank out any other text | DECIDED |
| Q15 | Sitemap before discovery | One cell: `ultimate-sitemap-parser`; found → page list to the agent, not found → carry on | DECIDED |
| Q16 | Handoff UI and site lock | Control window + site locked for the whole run; humans act only through the window; no Take over | DECIDED |
| Q17 | Which clicks need approval | Deny by default; only exact `safe_words` matches skip Approve | DECIDED |
| Q18 | Where to prove it live | ParaBank only, purely visual; no local hostile page for now | DECIDED |
| Q19 | What the builder may run | OFFLINE cells only, via `run_offline.py` | DECIDED |
| Q20 | Where the new libraries go | A separate `discovery` dependency group | DECIDED |
| Q22 | TypeSafe tool selection + model routing | Restored, off unless `TYPESAFE_API_KEY`; fails open | DECIDED |

---

## Base decisions

- **Pure visual everywhere, including ParaBank.** Screenshot, then OCR, then mouse/keyboard at
  coordinates. No DOM reads, no `page.evaluate`, no accessibility tree.
- **OCR engine:** RapidOCR only (it runs the PaddleOCR models).
- **Proof:** ~~two runs, both pure visual: a hostile local page (framesets, nested tables, no
  `id`s, no `<label>`s), and a ParaBank re-run.~~ Superseded by **Q18**: ParaBank only, for now.
- **Playwright's role:** navigation, screenshot, mouse and keyboard only.
- **Hard rules kept:**
  - `type_secret`: the model never sees the value; keys are sent via the keyboard.
  - `host_allowed`: gates every navigation.
  - Risky-click gate: ~~triggered by the element's OCR text matched against a risky-word
    list~~. Superseded by **Q17**: deny by default, only `safe_words` skip approval. Approve /
    Reject happens in the control window (**Q16**). There is no Take over.
- **Notebook-first.** Built in `notebooks/discovery/discovery` first. `src/cua/` is untouched until a later
  port.
- **Rule: the notebook is the production design (user, 2026-09-28).** Every mechanism in it is
  what ships. No notebook-only stand-ins (e.g. `input()` prompts). Test-only fakes and fixtures
  are clearly marked and never on the run path.

### The 3 rungs (how replay finds things)

Rungs are used **only in replay** (plain code, no LLM). Discovery only records them. Replay
tries them in order on a live screenshot and stops at the first that works.

| Rung | Locator | Finds it by | Example | Breaks when |
|---|---|---|---|---|
| 1 | `OcrTextLocator` | its own text (fuzzy) | "Log In" | the text changes ("Sign In") |
| 2 | `AnchorLocator` | a nearby label + offset | "Password", then 60px down | the layout moves |
| 3 | `VisualTemplateLocator` | a small saved picture | picture of the button | the look changes (colour, font) |

- If all 3 fail: replay stops and asks a human. It never guesses.
- Optional `ordinal` ("nth match") on rungs 1 and 2, e.g. the 2nd "Amount" on the page.
- **Drift log:** records which rung matched each step. A step that keeps falling to rung 2 or 3
  flags the capability for review.
- **Step check:** after each step, re-read the screen with OCR on a bounded poll (about every
  200ms, up to a time budget) until the expected text appears.
- Supersedes D63's 2-rung `Target`. The DOM locator types are retired in the new engine.

---

## Q7: things with no text — DECIDED

**Question.** OCR only finds text. Empty input boxes and icon-only buttons (e.g. a 🔍) have no
text, so they get no number. How does the agent act on them?

**Options considered**
1. OpenCV edges and outlines: find box-like shapes and number them.
2. OpenCV template matching: only finds pictures you already have, so no use for discovery.
3. UIED: research tool, awkward to install.
4. OmniParser (Microsoft): best at finding icons and inputs, but heavy and slow without a GPU.
5. PaddleOCR layout detection: finds big regions (tables), not small inputs.
6. **Let the LLM point at them itself.**

**Decision: option 6, no shape detector.**
- The agent points at text-less things using the screenshot it already sees (no extra LLM
  call): `click_at(x, y)`, or `type_text` / `type_secret` at a point.
- After each pointed action, a new screenshot checks that something changed; if not, the agent
  retries.
- Depends on Q10: positions only hold if window size and zoom are fixed.
- **Fallback, only if the hostile page shows repeated misses:** add OpenCV edge detection.
  (It was briefly chosen, then reverted: false finds on table cells and dividers, misses on
  borderless inputs, and per-site tuning.)

## Q7b: how replay finds text-less things — DECIDED

**Question.** Discovery clicked the empty box at (420, 210). How does replay know where to
click and type, with no LLM?

**Options considered**
- A. Save the raw screen coordinates and click them. Simplest, but breaks when anything shifts
  (a banner, an extra row, a different scroll).
- B. **Coordinates from the nearest label (rung 2).** "Username, 150px right". Survives shifts.
- C. Raw coordinates first, then rungs if the check fails.

**Decision: B.**
- A text-less thing has **no rung 1** (it has no text of its own). It gets rung 2 (label +
  offset) and rung 3 (picture). Replay never clicks raw screen coordinates.
- **Rung 3's picture is cut at discovery, before the action.** It shows the empty field, never
  a typed value or password dots. Replay only takes live screenshots and never saves new crops.
- **Replay checks every step** by OCR-ing the spot again (the typed value, or dots for a
  secret). If all rungs fail, replay stops and asks a human.

## Q8: tables with look-alike rows — DECIDED

**Question.** On the accounts table, OCR reads every number but doesn't know which numbers are
on the same row. How does replay read "the balance of account 13455"?

```
Account    Balance     Available
13344      $515.50     $515.50
13455      $100.00     $100.00
```

**Options considered**
- A. Rung 2: find "13455", take the number a fixed distance right. Breaks if columns move.
- B. **Row + column rule.** Find the row, find the column header, read where they cross.
- C. Build an OpenCV table-line detector now. Most work, may never be needed.

**Decision: B (`TableCellLocator`).**
- Replay: OCR the screen → find the row with text `13455` → find the column headed `Balance`
  → read where they cross (`$100.00`) → type-check it. On failure, stop and ask a human.
- The code is generic. Only the values are site-specific, and discovery fills them in:
  `row_key` (usually an input, e.g. `{{account_id}}`) and `column`.
- Survives moved columns and added rows. Only for row/column layouts; a single labelled value
  uses the normal rungs.
- Fallback, only if the hostile page shows this is not enough: an OpenCV grid-line detector.

## Q8b: reading a whole table — DECIDED (2026-09-30)

**Why.** Live goal "Log in, get all transactions per account": the agent read 6 accounts and ~15
rows by eye, wrote them in its final message, and saved nothing (`extract_value` = one value per
box), so the save refused ("nothing was read or sent").

**Decision.**
- New tool `extract_table(header_ref, save_as, columns, description, row_limit=50)`. The agent
  points at one header cell and names the columns by their header texts. **Code** reads the rows
  from the look's OCR: the header line = the texts on the header's line; each header's x-range
  runs to the midpoint with its neighbours; rows below it end at a vertical gap >= `TABLE_GAP`, a
  line with no text in any asked column, or `row_limit`; each text goes to the column it overlaps
  most. `HANDOFF.saved[save_as] = [{column: text}, ...]`.
- Past the screen's bottom the tool says "may continue below"; a second call with the same
  `save_as` after a scroll appends, dropping only the rows the two reads share. At compile, the
  second read and the scrolls before it fold into the first: one step (replay scrolls itself).
- The event holds labels only: the columns, their x-ranges, the header's ordinal, `row_limit`.
  Never a cell. A column name holding a run value is refused. Page texts/headings for the
  checkpoint skip the table's cells.
- Schema (additive): step `ExtractTable {action: extract_table, header: {label, ordinal},
  columns, save_as, row_limit}`; `Output.type = "table"` with optional `columns`. A table read
  counts as a read for "nothing was read or sent". `describe()` is told the table outputs.
- One table per step. One table per item (per account) = one call per item page, `save_as`
  `name_1`, `name_2`, ... (a fixed name + an index, never a value).
- The reading functions (`same_line` ... `append_rows`) are copied verbatim into replay; a test
  checks they stay identical.

## Cuts

- **For-each over a list output** (next step): a step that runs a sub-sequence once per row of a
  table output (e.g. click each account, then `extract_table`). Today a variable number of
  accounts is not supported: a capability replays exactly the items discovery visited.

## Q9: image library — DECIDED

**Options considered:** A. OpenCV. B. Pillow only (can't find a picture inside a picture, so
rung 3 would need our own code). C. scikit-image (extra install, slower).

**Decision: A, OpenCV, for pixel jobs only. It never finds elements in discovery.**
- Discovery: draws the numbered red boxes, and cuts the rung 3 picture (before the action).
- Replay: rung 3, finding the saved picture in a live screenshot (`matchTemplate`). The match
  threshold lives in **config**. Two near-equal best matches = not found, ask a human.
- Already installed as a RapidOCR dependency, so nothing new is added.

## Q10: window size and zoom — DECIDED

**Question.** Positions and pictures only line up if the screen is the same size at discovery
and at replay.

**Options considered:** A. Lock and save. B. Scale numbers to a new size (pictures and OCR get
less reliable). C. Do nothing.

**Decision: A.** Discovery runs at a fixed window size and zoom (e.g. 1280×800 at 100%; values
in **config**). Both are saved in the capability. Replay sets the same values via Playwright
before step 1, and refuses to run if it cannot. No scaling.

## Q11: notebook format — DECIDED

**Options considered:** A. `discovery.py` + paired `discovery.ipynb` (jupytext), in
`notebooks/discovery/` (first named `agent2`, renamed by the user). B. `.py` only with
`# %%` cells. C. `.ipynb` only.

**Decision: A.** The user runs the `.ipynb`; the `.py` gives readable git diffs.
`notebooks/agent_2_legacy_surface.py` is deleted once its ideas (e.g. `VisualTemplateLocator`)
are folded into `discovery`, and only with the user's go-ahead at that time.

## Q12: dropdowns — DECIDED

**Question.** A native dropdown's list is drawn by the browser and may not show in the
screenshot at all.

**Options considered:** A. Click, type the option text, Enter. B. Arrow keys, checking with
OCR after each press. C. Screenshot a different way (browser-dependent).

**Decision: A, with B as fallback.**
- First: click the dropdown, type the option text, press Enter.
- Fallback: if OCR of the closed box shows the wrong option, press ↓ one at a time, re-reading
  after each press, up to a limit, then ask a human.
- Replay step: find the dropdown by its rungs, type `{{input}}`, Enter, check the box shows it.

## Tools: typing into boxes with no number — DECIDED

**Question.** `type_text(ref, value)` and `type_secret(ref, name)` need a number, but empty
input boxes (Q7) have none.

**Options considered:** A. New tools `type_at` / `type_secret_at`. B. `click_at`, then type
into whatever is selected (risky: a missed click sends text, even a password, elsewhere).
C. **Let the existing tools take a number or a point.**

**Decision: C. No new typing tools, no custom input code.**
- `type_text(7, "john")` or `type_text(at=(420, 210), "john")`; same for `type_secret`.
  `click_at(x, y)` stays for clicking text-less things.
- Every tool is a thin wrapper over Playwright's mouse/keyboard only: `mouse.click`,
  `keyboard.type`, `keyboard.press`, `mouse.wheel`. Playwright's DOM commands (`page.fill`,
  `select_option`, `get_by_label`) are not used.
- The wrapper adds only our rules: number → screen point, secret hidden from the model,
  risky-click gate, host check.
- After typing, the box is re-read (text, or dots for a secret). A failed `type_secret` check
  stops and asks a human; it never retries blindly.

## Q13: scrolling — DECIDED

**Question.** Things below the window can't be seen or numbered, and every scroll moves all
positions.

**Options considered**
- A. **`scroll` tool + fresh look.**
- B. Auto-scroll inside `click` (can't help discovery: the agent can't name what it can't see).
- C. Tall window / full-page screenshot (clashes with Q10; text shrinks; lazy-loaded content
  never loads).
- D. A plus Page Down / Home / End keys (keys misbehave when an input is focused).

**Decision: A.**
- Discovery: `scroll("down" | "up")` runs `mouse.wheel` (distance in **config**, about ¾ of the
  screen so some overlap stays), then takes a new screenshot and renumbers. Numbers from before
  the scroll are refused ("look again").
- Same screenshot before and after = "bottom of page reached". Optional `at=(x, y)` scrolls
  inside a small scrolling panel.
- Replay: each scroll is its own step. If rungs 1-3 all miss a target, replay scrolls down and
  retries, up to a limit in **config** (e.g. 5), then asks a human.
- D can be added later if needed.

## Q14: private data in saved pictures — DECIDED

**Question.** A rung-3 crop can catch nearby customer data (an account number, or a value typed
in an earlier step) and save it into the capability file.

**Decision: crop tight and blank out other text.**
- The rung-3 picture is cut (at discovery, before the action) tight to the element's own box.
- Any OCR text inside the crop that isn't the element's own label is blanked out before saving.
- Customer data never goes into saved files, the same rule as secrets.

## Q15: sitemap before discovery — DECIDED

**Question.** Can the agent be told a site's pages up front, so it can go straight to the right one?

**Decision (user, 2026-09-28):**
- One cell, run once before discovery, using `ultimate-sitemap-parser`:
  `sitemap_tree_for_homepage(SITE)`, then `tree.all_pages()`. `SITE` comes from config.
- Found: the allowed-host page paths (deny words removed, capped) are added to the agent's first
  message as context. `open_path` accepts them.
- Not found, or any error: nothing is added, and discovery carries on as usual.
- Only allowed hosts are fetched. This is the one approved exception to "screen only", since it
  fetches over HTTP, not the browser.
- Legacy sites can't be assumed to have a sitemap. ParaBank has none (`/robots.txt` and
  `/sitemap.xml` both 404 on 2026-09-28).

## Q16: handoff UI and site lock — DECIDED

**Question.** When a human must approve a click or give a missing value, where do they do it,
and what stops anyone (agent or human) from touching anything else on the site?

**Options considered**
- A. The in-page bar (injected into the site). Rejected: fails on framesets, and injects into
  the customer's site.
- B. A notebook `input()` prompt. Rejected: not production.
- C. A control window, but the site is not locked. A human could still click anything.
- D. The control window + site lock, keeping Take over. Rejected: breaks zero trust.
- E. **The control window + site lock, no Take over.**

**Decision (user, 2026-09-28): E. Zero trust.**
- The rule, in the user's words: "this is a banking application; I should not be allowed to
  click or enter anything other than what I'm supposed to." No trust exception.
- **Control window:** our own small page in a second browser window (`set_content`, no host).
  Nothing is injected into the site, so it works on any site, framesets included.
- **Site lock:** `SiteLock` sends DevTools `Input.setIgnoreInputEvents(ignore=true)` on the site
  tab's own CDP session. On for the whole run, handoffs included. Lifted only for the instant of
  our own mouse/keyboard call on the allowed target (unlock → act → relock, in `try/finally`).
- **Humans act only through the control window.** Our code then does the action:
  - Risky click: Approve / Reject only. Approve = our code clicks that exact target.
  - Missing value: the field's crop + a value box (masked if sensitive). Our code clicks,
    types, and re-reads it with OCR. The value never reaches the model or the log (the log gets
    only `human_entry: true` + the field).
  - Dropdown: the human types the option text; our code runs `choose_option`.
  - `ask_human`: a typed text answer only, never access to the page.
- **No Take over.** Anything the window can't express ends the run as `STUCK:`.
- **2026-09-28 build notes (user-confirmed):**
  - The control window is a second tab in the same browser ("Agent control"). It comes to the
    front when a human is needed (approve, form, stuck choice) and the site tab comes back when
    they answer (`finally`). During a take-over the site tab is in front and the control tab's
    title reads "▶ Agent control: your turn" so Done is easy to find. (User choice; a
    side-by-side window was built and dropped.)
  - Missing values are one form per page: one row per field (its crop + an input, masked if
    sensitive; dropdowns take the option text). Our code enters every value; the site never
    unlocks for value entry. A "fill it in the site yourself" variant was tried and dropped: it
    let the human click links / other fields and hung the agent.
  - Take over survives only after a tool said STUCK (Q21), and is the one time the lock lifts.
  - **Transactions (user rule, 2026-09-28): the agent never commits one.** Every request that
    sends data (any method but GET/HEAD/OPTIONS) is held at the network layer (`page.route`) for
    two human gates: (1) "are these details right?" with what was entered and what is being sent,
    (2) "send it?". Reject at gate 1 = STUCK + human control; reject at gate 2 = DECLINED; a
    closed control tab = blocked. Generic: no button names. Only the login click is exempt.
    A click-level gate keyed on "was something typed on this page" was tried and failed live: a
    form whose values were all dropdown defaults went through with no gate.
  - **Who the human is asked, and when (user rule, 2026-09-29):** only for transactions (the two
    send gates), take-over, and when the agent is unsure. Navigating and entering values needs
    no approval: the per-click Approve (Q17, `safe_words`) is removed. The two gates also apply
    to the human's OWN sends during a take-over, and they supersede whatever is on the control
    tab; when answered, the take-over comes back as it was (a question stack, not a queue).
  - **Gates are confirmations, not checks (user rule, 2026-09-29).** Before any gate, the code
    compares every number the page is about to send against every number the human gave (the
    goal, ask_human answers, form values). Any number the human never gave (e.g. sending account
    1450 when they said 1400) holds the send and opens the fill-in form for just those fields,
    prefilled with the page's value; the human's corrected values are what gets sent. (First
    version aborted the request instead, and the site answered with an "internal error" page.)
    Skipping the form blocks the send. Only a fully matching send reaches Gate 1 (confirm details) and Gate 2 (confirm
    sending). Generic: compares digit groups, no field names.
  - **Gate 1 = Approve / Edit (user rule, 2026-09-29).** Edit reopens a form built from the
    held request's own fields (only a page dropdown whose current value exactly equals a field
    becomes a dropdown); the edits are what is sent. **Nothing is stored** (banking): a saved
    copy of the human's form was built and removed the same day. Typed and selected values
    never enter the event log (labels and positions only); the run's working values (what was
    entered, what the human gave, the last screenshot) are wiped when `run_goal` ends.
  - **Unsure = human.** The agent never guesses or picks a value; it calls `ask_human` (answer /
    take over / stop). The same panel opens by itself after 3 failed tool results in a row.
  - **Hand-back button (user decision, 2026-09-29).** Humans forgot to go back to the control
    tab and click Done. The hand-back is a browser-extension toolbar button
    (`extensions/handback/`, Manifest V3): no content scripts, no host permissions, so it never
    touches any site. The browser launches with it (`launch_persistent_context` +
    `--load-extension`); the notebook talks only to the extension's service worker (`EXT`):
    `setMode('YOU')` at take-over start (badge "YOU"), `setMode('AI')` in `finally`, and a
    0.5 s poll of its click count; a rise answers the take-over. Every call is bounded and
    swallows errors. It **replaced a separate small "Hand back" window** (own context, placed
    over CDP), built and dropped the same day; an on-site bar injected into the page was dropped
    before that because it touches the target's DOM. **Limit:** browser-only. For desktop
    targets the fallback is a small always-on-top window of our own. If the extension does not
    load, the take-over carries on. Fallback: the control tab's Done. An idle "Done? Hand back"
    reminder was built and removed the same day at the user's request: no prompts interrupt a
    take-over.
- **Dropdowns: the one non-visual exception (user choice B, 2026-09-29).** On macOS a native
  `<select>`'s list is drawn by the OS outside the page: no screenshot shows it and no key sent
  to the page moves it (keyboard stepping, Q12, read only the first option). So for the
  `<select>` under a point, and only that, `SELECT_AT_JS` reads its options and sets it by value
  (then fires input/change); OCR of the closed box still confirms the result. Everything else
  stays visual. Rejected: whole-screen OCR + real mouse (needs OS permissions, large), Linux-only
  runs. Known limit: a streamed/remote-desktop target has no `<select>` to read; that case
  would need whole-screen capture.
- **Screen size (2026-09-29): Q10 holds, at 1280x800** (1440x900 was tried and reverted by the
  user: more text on screen, but the agent handled it worse). Page fixed at `CFG.viewport`,
  `device_scale_factor=1`, the same numbers at discovery and replay; the Browser cell refuses to
  start if the screenshot is not exactly that size. A maximised, any-size window was tried and
  dropped: on Retina the screenshot was 2x the mouse's points (login broke), and a layout that
  changes with the screen breaks replay's label+offset and picture rungs. `take_look`'s
  rescale + `to_page` stay only as a safety net for an unexpected pixel density.
- **Depends on the BROWSER 0 lock check:** it must prove the lock blocks real human input
  before anything is built on it. If it fails, Q16 is reopened.

## Q17: which clicks need approval — DECIDED

**Question.** A risky-word list misses any risky button whose words aren't on it. How do we
decide which clicks need a human's Approve?

**Options considered**
- A. A risky-word list (the old gate): only listed words need approval. Fails open.
- B. **Deny by default, with a safe list.** Every click needs approval unless its text is on the
  safe list.
- C. B, plus every navigation link counted as safe automatically.

**Decision (user, 2026-09-28): B.**
- Every `click` / `click_at` needs Approve in the control window (Q16) unless its normalised OCR
  text exactly matches an entry in `cfg.safe_words`.
- `click_at` on a spot with no OCR text is never safe: it always needs approval.
- `cfg.deny_words` are refused outright, before any approval.
- `safe_words` lives in config per app. ParaBank's list (`log in`, `find transactions`, its menu
  links) is set in the ParaBank run cell. Tools hold no site values.
- A rejected target is remembered for the run (D33). The old risky-word list is dropped.

## Q18: where to prove it live — DECIDED

**Question.** The base plan had two proof runs: a hostile local page and ParaBank. Do we need
both now?

**Options considered:** A. Both runs. B. A local hostile page only. C. **ParaBank only, purely
visual.**

**Decision (user, 2026-09-28): C.**
- Live proof is ParaBank only, purely visual. No local test page, no localhost exception.
- The hostile local page is deferred, not dropped.
- **Risk:** the engine is unproven on legacy markup (framesets, nested tables, no `<label>`s)
  until that page is built.

## Q19: what the builder may run — DECIDED

**Question.** The builder sub-agent writes the notebook. May it run any of it?

**Options considered:** A. **OFFLINE cells only, via a runner.** B. Nothing (the user runs
everything). C. Everything, BROWSER cells included.

**Decision (user, 2026-09-28): A.**
- Runner: `notebooks/discovery/run_offline.py`. Runs only `# %% OFFLINE` cells, in order, in one
  shared namespace, and stops at the first failing assert.
- Keys scrubbed: no `ANTHROPIC_API_KEY`, `TYPESAFE_API_KEY` or `PARABANK_*` in `os.environ`.
- Import guard: fails if an OFFLINE cell imports `playwright`.
- Never a BROWSER cell, a browser, the model, the network, or `.env` values. One exception:
  OFFLINE 6 runs real RapidOCR on a synthetic PNG (local, no network).
- Run with the project's kernel interpreter by path, never `uv run`. A task is done only when
  every `OK <cell>` line prints.

## Q20: where the new libraries go — DECIDED

**Question.** Discovery needs new libraries. Main dependencies, or kept apart?

**Options considered:** A. **A separate `discovery` dependency group.** B. Main dependencies
now.

**Decision (user, 2026-09-28): A.**
- `[dependency-groups] discovery = ["rapidocr>=3.9.2", "onnxruntime>=1.30.0", "numpy>=2",
  "ultimate-sitemap-parser>=1.8.1"]`. Installed with `uv sync --group discovery`.
- Moves to the main dependencies at the later `src/cua/` port.

## Q21: live-session take over (reopens Q16) — DECIDED

**Why reopened.** The spec (3.6) requires that a human can "take control of the live session",
do the manual steps, "then hand control back", and that we "record what the human did". Q16-E
(no take over) fails that requirement.

**Decision (user, 2026-09-28): add ONE bounded take-over path; everything else in Q16 stays.**
- Only when the agent is stuck (the tool `ask_human(question, take_over=True)` or a `STUCK:`
  condition the control window can't express). Never for a risky click: those stay Approve / Reject.
- The control window shows **who is in control** (`agent` / `human`) at all times.
- Take over: our code unlocks the site for the human (the ONE exception to the whole-run lock),
  shows "You are in control. Click Done to hand back." The human works on the SAME live session.
- Done: our code re-locks the site FIRST, then takes a new look. The agent resumes on that session.
- Recorded: an event `human_takeover` with the reason, the page URL + screenshot before and after,
  and the duration. No typed values are captured (we can't see keystrokes, by design), so steps a
  human did during a take over are marked `human_entry: true, recordable: false` (D82 rule).
- Cost: zero trust is broken only while the human holds control, and the log shows it.
- **2026-09-29 build (spec 3.6 "record what the human did"):** `take_over()` stores ONE event
  `{"tool": "take_over", "recordable": false, "actions": [{"kind": "page", "path": ...},
  {"kind": "send", "path": ...}], "shot_before": png, "shot_after": png}`. Pages come from a
  main-frame `framenavigated` listener attached only while the human holds control (removed in
  `finally`); sends come from `guard_send` (path only, no body, no query). It is **evidence, not
  steps**: `build_capability` still refuses a run with a take-over.
- **Q16 note: take-over screenshots are evidence and may show values on screen** (the human's own
  entries). They live in memory on the event, like crops. They must be redacted, or kept out of
  the artifact, before anything persists them (the `evidence/` saving path decides). They are
  never written into a capability YAML.

## Q22: TypeSafe tool selection + model routing — DECIDED

**Why.** Planned in `PLAN.md` (D50/D52/D76) for the DOM agent, never wired into this notebook, then
deleted with `src/cua/agent.py` in 4f692a8.

**Decision (user, 2026-10-01): restore it in the package, off by default.**
- `src/cua/discovery/agent/routing.py`: a tool router (TypeSafe `Choice` picks the step's job and
  narrows the tools to it) and a model router (Haiku "fast" / Sonnet "powerful", both via
  `cua.llm.make_chat_model`). Appended after the notebook's own middleware by `build_agent`.
- Jobs map to the visual tools. Always kept: `observe`, `click`, `type_secret`, `ask_human`.
  `login` + `type_secret`; `fill_form` + `type_text`, `select_option`, `scroll`; `read_value` +
  `extract_value`, `extract_table`, `scroll`; `navigate` + `open_path`, `scroll`; `need_human` +
  `request_missing_values`, `ask_human`; `finish` + `finish_business_outcome`.
- Off unless `TYPESAFE_API_KEY` is set (then `[]`, the notebook's agent unchanged).
  `langchain-typesafe` is the optional `typesafe` extra, imported only when on.
- **What leaves (2026-10-02, Q23):** only the page name, the last tool's name and its status word.
  (It used to send the last result's first 400 chars: the OCR listing, ids, the session token.)
- **Fail open:** classifier confidence below 0.8, or any error (network, auth, timeout), keeps
  every tool. A wrong guess must never hide the tool the agent needs.
- **Model choice is per step (2026-10-02).** TypeSafe's own `ModelRouterMiddleware` classifies
  once per run, from the goal text, so a multi-step goal always got Sonnet and Haiku was never
  used. Our `ModelRouter` asks for every model call, from the same step state as the tool router.
  Haiku only when the classifier says "fast" with confidence 0.8 or more; anything else, or any
  error, uses Sonnet.

## Q23: account ids in what is stored or shown — DECIDED (user, 2026-10-02)

- An account id keeps only its last 3 digits everywhere it is stored or shown: `***010` (text,
  names, evidence folder names, artifacts, crops, the model's `extract_value` echo, `describe()`,
  the terminal). Mask in place, never swap in a fake id. Amounts are shown. Secrets stay `***`.
- An id is 5+ digits on its own, not an amount (`$`, `-$`, decimals, thousands) and not inside a
  word (timestamps, hashes, tokens). Both numbers are site config (`id_min_digits`,
  `id_visible_digits`).
- PNGs: a box holding only an id is blacked out but its last 3 digits, by width share; a box with
  a run value or secret is blacked out whole, as before.
- An artifact is masked, then leak-checked, before any file is written ("not saved: ..."). A
  masked `ocr_text` (`***010`) no longer matches the screen at rung 1; replay falls to the anchor
  or the template for that step.
- Also: TypeSafe gets no screen text (Q22), logged URLs drop `;jsessionid=` and the query, the
  browser profile is deleted at close, and a discovery run's chat, reads, crops and final screen
  are dropped once its evidence is written.
