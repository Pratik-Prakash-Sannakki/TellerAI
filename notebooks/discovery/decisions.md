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
