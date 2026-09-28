# Discovery architecture

How the DiscoveryAgent finds things on the screen. Discovery only; the recorder and replay are
not shown. All questions and decisions: `decisions.md` in this folder. Wider design: `ARCHITECTURE.md` §4.

## 1. Diagram

```
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
          │ risky click (e.g. 'Transfer') → human Approve / Reject
          ▼
   Browser (Playwright) ── new screenshot ──▶ back to the start
```

## 2. Each box, with an example

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
  empty box to its right, so it calls `type_text(at=(330,210), "john")`.
- **Never:** sees a password, reads the page's HTML, or calls Playwright directly.

### Tools
- **What they do:** turn the agent's choice into plain Playwright mouse/keyboard commands.
  Number → centre of its box → `mouse.click(x, y)`; text → `keyboard.type(...)`.
- **Example:** `click(3)` → centre of the "Log In" box is (235,290) → `mouse.click(235, 290)`.
- Full list in section 3.

### Safety checks (on the arrow down to the browser)
- **Risky-click gate:** if the clicked element's text is on a risky-word list (from config,
  e.g. "Transfer", "Pay"), the run pauses for a human: Approve / Reject / Take over.
- **Host check:** every navigation must go to an allowed host (`parabank.parasoft.com`).
- **Example:** `click(9)` on `[9] 'Transfer'` → paused → human clicks Approve → click happens.

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
| `click(ref)` | Click the centre of a numbered box. | `mouse.click(x, y)` | `click(3)` clicks "Log In" |
| `click_at(x, y)` | Click a spot with no number (icon, empty box). A new screenshot checks something changed. | `mouse.click(x, y)` | `click_at(612, 88)` clicks a 🔍 icon |
| `type_text(ref or at, value)` | Click a box (by number or point), then type. The box is re-read to check. | `mouse.click` + `keyboard.type` | `type_text(at=(330,210), "john")` |
| `type_secret(ref or at, name)` | Same, but types a saved secret. The model only sees the name, never the value. | `mouse.click` + `keyboard.type` | `type_secret(at=(330,250), "PARABANK_PASSWORD")` |
| `select_option(ref or at, text)` | Dropdown: click, type the option, Enter. Fallback: ↓ key until OCR shows it (Q12). | `mouse.click` + `keyboard.type` + `keyboard.press("Enter")` | `select_option(5, "13455")` |
| `scroll(dir, at=None)` | Scroll up/down, then fresh look + renumber. Same screenshot twice = bottom reached (Q13). | `mouse.wheel(0, 600)` | `scroll("down")` |
| `open_path(path)` | Go to a page on the allowed host only. | `page.goto(url)` | `open_path("/parabank/overview.htm")` |
| `extract_value(ref, name)` | Save a value the goal asked for. In a table, recorded as row + column (Q8). | none (uses OCR text already read) | `extract_value(12, "savings_balance")` → `$100.00` |
| `finish(...)` | Report the answer and stop. | none | `finish("savings balance is $100.00")` |

Human help (already in the current engine): `request_value` (ask a human to fill a known
field), `ask_human` (ask a question), and the Approve / Reject / Take over bar on risky clicks.

## 4. Step by step: one discovery run

**Goal:** "Log in and read the savings balance. Use extract_value to save it."

| Step | Agent sees | Agent calls | What happens |
|---|---|---|---|
| 1 | nothing yet | `observe()` | Screenshot + OCR: `[1] 'Username' [2] 'Password' [3] 'Log In'`. The two empty boxes have no number. |
| 2 | empty box right of `[1]` | `type_text(at=(330,210), "john")` | Click at (330,210), type "john". Re-read: box shows "john". ✔ |
| 3 | empty box right of `[2]` | `type_secret(at=(330,250), "PARABANK_PASSWORD")` | Value comes from `.env`, typed by keyboard. Re-read: box shows dots. ✔ The model never saw the password. |
| 4 | `[3] 'Log In'` | `click(3)` | "Log In" is not a risky word, so no pause. Click. |
| 5 | (old numbers now stale) | `observe()` | New page: `[4] 'Accounts Overview' [5] 'Account' [6] 'Balance' [7] '13344' [8] '$515.50' [9] '13455' [10] '$100.00' ...` |
| 6 | the savings row is `13455` | `extract_value(10, "savings_balance")` | Saves `$100.00`. Recorded as a table read: row `13455`, column `Balance`. |
| 7 | the value is saved | `finish("savings balance is $100.00")` | Run ends. |

**Other things that can happen in a run**
- **Target below the screen:** the agent calls `scroll("down")`, then uses the new numbers.
  If the screenshot didn't change, it is told "bottom of page reached".
- **A risky click** (e.g. `click(14)` on "Transfer"): paused for Approve / Reject / Take over.
- **A missed `click_at`:** the new screenshot shows no change, so the agent looks again and
  retries.

**What gets recorded (for replay later):** every tool call, its result, and the screenshot,
written to the event log. The recorder turns these into a capability file. That's out of scope
here.

## 5. Notes

- RapidOCR runs the PaddleOCR models, so the "Text Extraction" box is PaddleOCR in practice.
- No shape detector (Q7). Things with no text get no number; the agent points at them with
  `click_at`, or types into them with `type_text` / `type_secret` at a point.
- No DOM reads anywhere. The agent only works from what is on the screen.
- Saved rung-3 pictures are cut tight and have any other text blanked out, so no customer data is
  saved (Q14, see `decisions.md`).
- Example coordinates and values are illustrative, not from a real run.
