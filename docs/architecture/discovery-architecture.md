# Discovery architecture

> **Notebook-era design.** Written while the system was two notebooks (before 2026-10-01). The
> design still holds; names, file paths and some details (the sitemap step is design only, Q15)
> differ from the code. Current per-component docs: [docs/README.md](../README.md).

How the DiscoveryAgent finds things on the screen. Discovery only; the recorder and replay are
not shown. All questions and decisions: `docs/decisions/discovery-decisions.md`. Wider design: `ARCHITECTURE.md` §4.

## 1. Diagram

```
 Before discovery (once per run)
┌──────────────────────────────────────┐
│ Sitemap (ultimate-sitemap-parser)    │   found → page list added to the
│ sitemap_tree_for_homepage(SITE)      │──▶ agent's first message as context
│ allowed host only; not found = skip  │   not found → nothing added, carry on
└──────────────────────────────────────┘
                                   │
                                   ▼
                  ┌─────────────────────┐         ┌──────────────────────┐
┌──────────┐      │   Text Extraction   │         │  Numbered Elements   │
│   Page   ├────▶ │      RapidOCR       │────────▶│ • One number per box │
│screenshot│      │ • Text strings      │         │ • Red box + number   │
└──────────┘      │ • Bounding boxes    │         │   drawn on the image │
                  │ • Confidence score  │         └──────────────────────┘
                  └─────────────────────┘                    │
                                                             │
                                                             ▼
┌────────────────────────────────────────────────────────────────────────┐
│              DiscoveryAgent  (LLM, deep agents)                        │
│                                                                        │
│  Sees, every step:                                                     │
│   • Screenshot with numbered red boxes                                 │
│   • Text list, e.g.  [7] 'Transfer'                                    │
│   • The goal, e.g.  "log in and read the savings balance"              │
│   • Sitemap page list, if the site has one (from the first message)    │
│                                                                        │
│  Picks ONE tool per step:                                              │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐   │
│  │ observe      │ │ click(7)     │ │ type_text    │ │ scroll       │   │
│  │ take a new   │ │ or by point: │ │ type_secret  │ │ fresh look + │   │
│  │ screenshot   │ │ click_at(x,y)│ │ (7 or x,y);  │ │ renumber; old│   │
│  │ and number   │ │ for things   │ │ LLM never    │ │ numbers are  │   │
│  │ everything   │ │ w/o a number │ │ sees secret  │ │ refused      │   │
│  └──────────────┘ └──────────────┘ └──────────────┘ └──────────────┘   │
│    scroll: same screenshot twice = bottom of page reached.             │
│    More tools (dropdown, open_path, extract_value...): see table.      │
└────────────────────────────────────────────────────────────────────────┘
          │ tool: number → box centre → mouse click / key press
          │ every click: exact safe-list text → go; deny word → refused;
          │ anything else → control window: Approve / Reject
          ▼
   Browser (Playwright) ── new screenshot ──▶ back to the start
   site tab locked all run; unlocked only for the instant of our own action

┌──────────────────────────────────────┐
│ Control window (separate window)     │   the ONLY place a human acts:
│ Approve / Reject · value box · text  │──▶ our code then acts on the one
│ answer. No take over.                │   allowed target
└──────────────────────────────────────┘
```

## 2. Each box, with an example

### Sitemap (before discovery)
- **What it does:** one notebook cell, run once before the agent starts. It asks the site for its
  sitemap with `ultimate-sitemap-parser` (`sitemap_tree_for_homepage(SITE)`, then
  `tree.all_pages()`). `SITE` is the website being discovered, from config.
- **Found:** the page paths (allowed host only, deny words like "register" removed) are added to
  the agent's first message as context. The agent may `open_path` any of them.
- **Not found (or any error):** nothing is added. Discovery carries on as usual, from the screen.
- **Only allowed hosts** are ever fetched. This is the one step that reads something other than the
  screen, approved by the user (Q-F).
- **Legacy sites:** don't assume they have a sitemap. ParaBank has none (`/robots.txt` and
  `/sitemap.xml` both 404 on 2026-09-28), so "not found" is the normal case.
- **Example:** a site with a sitemap → first message = goal + "Pages listed in this site's
  sitemap: /accounts.htm, /transfer.htm, ...". ParaBank → first message = goal only.

Example screen used below (ParaBank login):

```
Username  [              ]
Password  [              ]
          [ Log In ]
```

### Page screenshot
- **What it is:** a picture of the browser window, taken with Playwright `page.screenshot()`.
- **Fixed size:** always the same window size and zoom (Q10), e.g. 1280×800 at 100%.
- **Example:** a 1280×800 PNG of the login page above.

### Text Extraction (RapidOCR)
- **What it does:** reads every piece of text in the screenshot.
- **Gives, per piece of text:** the text, a box around it, and how sure it is (0 to 1).
- **Example output:**
  ```
  "Username"  box (100,200)-(180,220)  0.98
  "Password"  box (100,240)-(180,260)  0.97
  "Log In"    box (210,280)-(260,300)  0.99
  ```
- **Cannot see:** things with no text, like the two empty input boxes.

### Numbered Elements
- **What it does:** gives every OCR box a number and draws a red box + the number on the
  screenshot (drawing is done with OpenCV, Q9).
- **Example output:**
  ```
  [1] 'Username'   [2] 'Password'   [3] 'Log In'
  ```
  plus the same screenshot with three red numbered boxes on it.

### DiscoveryAgent (LLM)
- **What it sees each step:** the numbered screenshot, the text list, and the goal.
- **What it does:** picks exactly ONE tool call per step (LOOK, THINK, ACT).
- **Example:** goal "log in and read the savings balance". It sees `[1] 'Username'` and an
  empty box to its right, so it calls `type_text("john", x=330, y=210)`.
- **Never:** sees a password, reads the page's HTML, or calls Playwright directly.

### Tools
- **What they do:** turn the agent's choice into plain Playwright mouse/keyboard commands.
  Number → centre of its box → `mouse.click(x, y)`; text → `keyboard.type(...)`.
- **Example:** `click(3)` → centre of the "Log In" box is (235,290) → `mouse.click(235, 290)`.
- Full list in section 3.

### Safety checks (on the arrow down to the browser)
- **Click gate: deny by default (Q-B).** Every `click` or `click_at` needs Approve in the
  control window, unless its OCR text exactly matches the config safe list (`cfg.safe_words`).
  - Deny words (`cfg.deny_words`) are refused first, before any approval.
  - A `click_at` on a spot with no OCR text is never safe, so it always asks.
  - A rejected target is remembered for the run.
  - Example: the ParaBank safe list has `log in`, `find transactions` and its menu links.
- **Host check:** every navigation must go to `parabank.parasoft.com`. Nothing else, and no
  localhost exception (Q-C).
- **Example:** `click(9)` on `[9] 'Transfer'` → not on the safe list → control window asks →
  human clicks Approve → our code clicks that exact target.

### Control window and site lock (Q-A)
- **Site lock:** the site tab ignores all real input for the whole run, handoffs included
  (Chrome DevTools `Input.setIgnoreInputEvents`).
  - It is lifted only for the instant of our own mouse/keyboard action: unlock → act → relock.
- **Control window:** our own small page in a second window. The only place a human acts.
  - **Approve / Reject** for a click.
  - **A value box** for a missing value, masked for sensitive fields. The value never reaches
    the model or the log.
  - **A text answer** for `ask_human`.
- **Our code performs the action** on the one allowed target. The human never touches the site.
- **No take over.** If the window can't express something, the run ends as `STUCK:`.
- **Browser:** opens in app mode (no address bar), with a fresh profile per run.
- **Hard gate:** BROWSER 0 must prove the lock blocks real input before anything else runs.
- **Example:** the agent calls `request_value("zip code", x=330, y=410)` → the window shows the
  field's crop + a value box → human types `90210` → our code clicks (330,410), types it, re-reads.

### Browser (Playwright)
- **What it does:** navigate, screenshot, mouse, keyboard. Nothing else.
- **Never:** reads the DOM (no `page.fill`, no `get_by_label`, no `page.evaluate`).
- After each action a new screenshot is taken, and the loop starts again at the top.

## 3. All tools

Every tool uses only Playwright mouse/keyboard (or `goto` / `screenshot`). Nothing reads the
page's HTML.

| Tool | What it does | Playwright underneath | Example |
|---|---|---|---|
| `observe()` | New screenshot → OCR → new numbers. Old numbers stop working. | `page.screenshot()` | `observe()` → `[1] 'Username' [2] 'Password' [3] 'Log In'` |
| `click(ref)` | Click the centre of a numbered box. Goes through the click gate. | `mouse.click(x, y)` | `click(3)` clicks "Log In" |
| `click_at(x, y)` | Click a spot with no number (icon, empty box). Always asks if no OCR text. A new screenshot checks something changed. | `mouse.click(x, y)` | `click_at(612, 88)` clicks a 🔍 icon |
| `type_text(text, ref or x,y)` | Click a box (by number or point), then type. The box is re-read to check. | `mouse.click` + `keyboard.type` | `type_text("john", x=330, y=210)` |
| `type_secret(name, ref or x,y)` | Same, but types a saved secret. The model only sees the name, never the value. The re-read expects dots. | `mouse.click` + `keyboard.type` | `type_secret("PARABANK_PASSWORD", x=330, y=250)` |
| `select_option(option, ref or x,y)` | Dropdown: click, type the option, Enter. Fallback: ↓ key until OCR shows it (Q12). | `mouse.click` + `keyboard.type` + `keyboard.press("Enter")` | `select_option("13455", ref=5)` |
| `scroll(direction, x,y optional)` | Scroll up/down, then fresh look + renumber. Same screenshot twice = bottom reached (Q13). | `mouse.wheel(0, 600)` | `scroll("down")` |
| `open_path(path)` | Go to a page on the allowed host only. Also accepts sitemap paths. | `page.goto(url)` | `open_path("/parabank/overview.htm")` |
| `extract_value(ref, save_as, value_type, description)` | Save a value the goal asked for, from an OCR box. Recorded as a table read: row + column (Q8). | none (uses OCR text already read) | `extract_value(10, "savings_balance", "money", "savings balance")` → `$100.00` |
| `finish_business_outcome(...)` | Report the business result (for the recorder). | none | `finish_business_outcome("savings balance read")` |
| `finish(summary, values)` | Report the answer and stop. | none | `finish("savings balance is $100.00", {...})` |

**Human help** (all through the control window; never through the site):

| Tool | What the human does in the window | Example |
|---|---|---|
| `request_value(hint, ref or x,y)` | Types a value for one known field (masked if sensitive). Our code types it in. | `request_value("zip code", x=330, y=410)` |
| `request_missing_values(fields)` | Fills the empty fields the agent lists, one value box each. | `request_missing_values([...])` |
| `ask_human(question)` | Types a text answer. No access to the page. | `ask_human("Which account is savings?")` |

## 4. Step by step: one discovery run

**Goal:** "Log in and read the savings balance. Use extract_value to save it."

| Step | Agent sees | Agent calls | What happens |
|---|---|---|---|
| 0 | (before the agent) | (none: the sitemap cell) | Sitemap checked. ParaBank has none, so the first message is the goal only. |
| 1 | nothing yet | `observe()` | Screenshot + OCR: `[1] 'Username' [2] 'Password' [3] 'Log In'`. The two empty boxes have no number. |
| 2 | empty box right of `[1]` | `type_text("john", x=330, y=210)` | Unlock, click at (330,210), type "john", relock. Re-read: box shows "john". ✔ |
| 3 | empty box right of `[2]` | `type_secret("PARABANK_PASSWORD", x=330, y=250)` | Value comes from `.env`, typed by keyboard. Re-read: box shows dots. ✔ The model never saw the password. |
| 4 | `[3] 'Log In'` | `click(3)` | "log in" is on the ParaBank safe list, so no pause. Click. |
| 5 | (old numbers now stale) | `observe()` | New page: `[4] 'Accounts Overview' [5] 'Account' [6] 'Balance' [7] '13344' [8] '$515.50' [9] '13455' [10] '$100.00' ...` |
| 6 | the savings row is `13455` | `extract_value(10, "savings_balance", "money", "savings balance")` | Saves `$100.00`. Recorded as a table read: row `13455`, column `Balance`. |
| 7 | the value is saved | `finish("savings balance is $100.00")` | Run ends. |

**Other things that can happen in a run**
- **Target below the screen:** the agent calls `scroll("down")`, then uses the new numbers.
  If the screenshot didn't change, it is told "bottom of page reached".
- **A click not on the safe list** (e.g. `click(14)` on "Transfer"): the control window asks
  Approve / Reject. Reject → that target is refused for the rest of the run.
- **Something the control window can't express:** the run ends as `STUCK:`.
- **A missed `click_at`:** the new screenshot shows no change, so the agent looks again and
  retries.

**What gets recorded (for replay later):** every tool call, its result, and the screenshot,
written to the event log. The recorder turns these into a capability file. That's out of scope
here.

## 5. Notes

- The sitemap is a hint, not a map: often missing (ParaBank), out of date, or listing pages that
  need a login. A listed page that doesn't open falls back to normal on-screen navigation.
- RapidOCR runs the PaddleOCR models, so the "Text Extraction" box is PaddleOCR in practice.
- No shape detector (Q7). Things with no text get no number; the agent points at them with
  `click_at`, or types into them with `type_text` / `type_secret` at a point.
- No DOM reads anywhere. The agent only works from what is on the screen.
- Saved rung-3 pictures are cut tight and have any other text blanked out, so no customer data is
  saved (Q14, see `decisions.md`).
- Example coordinates and values are illustrative, not from a real run.
