# Pure-Visual Discovery Notebook: Build Plan

> **For agentic workers:** REQUIRED SUB-SKILL: use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to build this task by task. Steps use checkboxes (`- [ ]`).
> **Status: all questions decided (Q-A to Q-F, 2026-09-28). Waiting for the user's final review of the whole plan before any build starts.**

**Goal:** one notebook, `notebooks/discovery/discovery.py` plus its paired `discovery.ipynb`. It runs a deep agent that sees the screen only through screenshot → RapidOCR → numbered boxes, and acts only through Playwright mouse and keyboard. It writes an event log plus the rung-3 picture crops.

**Architecture:** a pure-Python core (OCR parsing, numbering, geometry, the risk gate, crops, checks, the event log, and the agent class over a `Surface` Protocol) is tested offline with a `FakeSurface` and fixture images. A thin Playwright `Surface` plus a few BROWSER cells wire it to a real window. We reuse `cua.config`, `cua.agent.build_langchain_agent`, and `cua.agent.build_typesafe_middleware` by import. `src/cua/` is not edited.

**Tech stack:** Python 3.12, Playwright (async), RapidOCR on onnxruntime, OpenCV (`cv2`) + numpy for pixel work only, deepagents / langchain, optional langchain-typesafe.

**Spec:** `notebooks/discovery/decisions.md` (Base, Q7–Q14, Tools) and `notebooks/discovery/discovery_architecture.md`. Existing rules: `DECISIONS.md` D14, D15, D32–D34, D50, D52–D62, D69, D76, D82, D98.

---

## 1. Global constraints (every task must follow these)

- **Pure visual.** No DOM reads: no `page.evaluate` that reads, no `locator`, no `page.fill`, no `select_option`, no `get_by_*`, no accessibility tree. Playwright is used only for `goto`, `screenshot`, `mouse.click`, `mouse.wheel`, `keyboard.type`, `keyboard.press`, and `page.url`.
- **Allowed hosts:** only `parabank.parasoft.com` (Q-C: no localhost exception).
- **Secrets:** `type_secret` takes a NAME only. The value comes from `cua.config.resolve_secret` and goes straight to `keyboard.type`. It never appears in a return value, a log line, the event log, a crop, or the model's context.
- **No ParaBank code in tools.** Risky words, safe words, viewport, and thresholds live in one frozen `DiscoveryConfig`. ParaBank values live only in the ParaBank run cell.
- **Window locked (Q10):** 1280×800, `device_scale_factor=1`, zoom 100%. Screenshot pixels = CSS pixels = the model's coordinates.
- **The notebook is the production design (user, 2026-09-28).** Every mechanism in it must be what ships. No notebook-only stand-ins, such as `input()` prompts for approvals. Test-only pieces (offline fakes and fixtures) are clearly marked and never part of the run path.
- **Notebook-first.** jupytext `# %%` cells. Every cell header says `OFFLINE` or `BROWSER`. The builder never runs BROWSER cells. Only the user does.
- **No `uv run`** (it makes a stray `.venv`). **No commits** unless the user asks.
- **CLAUDE.md code limits:** each function ≤ 40 lines, nesting ≤ 3, no `typing.Any` in signatures, frozen dataclasses for data, a `Protocol` for the Surface.
- **Out of scope:** recorder compile, replay, the rung resolvers, and `DriftLog` (replay-only, deferred to the replay notebook). `src/cua/` is untouched. `notebooks/agent_2_legacy_surface.py` is not deleted yet (Q11 says only with a later go-ahead).

## 2. Review focus (inputs no spec line covers, but likely to bite)

1. **Retina screenshots.** On a Mac, a context without `device_scale_factor=1` gives a 2560×1600 PNG, so every point is off by 2×. → BROWSER 2 asserts the PNG size equals the viewport. OFFLINE 7 refuses any point outside the viewport.
2. **Stale numbers after renumbering.** If numbers restart at `[1]` on each look, an old `[7]` silently maps to a new element. → Refs increase for the whole run and are never reused (OFFLINE 4). A ref not in the latest look is refused (OFFLINE 7).
3. **A password field that shows plain text.** The post-type OCR re-read could capture the secret itself. → `secret_leaked()` compares only inside the tool. On a match, the tool stops and asks a human, and the OCR text of that box is never logged (OFFLINE 12, OFFLINE 17).
4. **OCR merges a table header into one box** ("Account Balance Available"), which breaks the column lookup. → OFFLINE 10 has a merged-header fixture. It must return `None` (refuse, so the human is asked), never a wrong cell.
5. **ParaBank's header strip and a left menu both show the same word** (for example two "Transfer Funds" texts, or "Accounts Overview" as both a link and a heading). → The ordinal plus anchor rules (OFFLINE 9), and OFFLINE 16 asserting that a duplicate-text click uses the exact ref, never a text lookup.

---

## 3. What already exists (reuse, or its visual version)

### 3a. How the agent is built today (`agent.ipynb` STEP 4, `src/cua/agent.py`)
- `create_deep_agent(model=MODEL, tools=[...], system_prompt=..., checkpointer=MemorySaver(), middleware=middleware)`. `cua.agent.build_langchain_agent` wraps exactly this, so we import it.
- Each run is `agent.ainvoke({"messages":[{"role":"user","content":GOAL}]}, config={"configurable":{"thread_id":...},"recursion_limit":100})`.
- Tools are `@tool(parse_docstring=True)` closures over one agent instance, each wrapped in `one_at_a_time` (an `asyncio.Lock`, D98). This stops parallel tool calls from corrupting state.
- **TypeSafe (D50, D52, D76). Off unless `TYPESAFE_API_KEY` is set.**
  - `TypeSafeToolRouterMiddleware` classifies the step's job (`login` / `fill_form` / `read_value` / `need_human`) and narrows the tool list. Below 0.8 confidence it fails open, and any error fails open.
  - `ModelRouterMiddleware` picks Haiku for simple steps and Sonnet for everything else.
  - `cua.agent.build_typesafe_middleware(agent, extra_never_hide=...)` builds both. It needs `agent.current_page()`.
  - Caveat: it sends the page path plus the last result text to api.typesafe.ai. Never turn it on when real data could show.
  - For us, `extra_never_hide = {"click_at","type_text","select_option","scroll","extract_value","open_path","finish_business_outcome","request_missing_values"}`. The `read_value` job's `page_text` tool doesn't exist here, so `extract_value` must never be hidden.

### 3b. Existing handoff rules: when a human is called in
| Rule | When | Source | Visual version |
|---|---|---|---|
| Risky click → Approve / Reject (Take over removed, Q-A) | Agent clicks any button except `SAFE_SUBMITS` (`log in`, `find transactions`). Deny by default. `auto_limit` can skip small transfers. | D33 | **Q-B:** deny by default on every click, links included, since OCR can't tell a button from a link. Safe only on an exact match to the config safe list. `auto_limit` is dropped for v1. |
| Reject is remembered | The same target is refused for the rest of the run. The agent must `finish("DECLINED: ...")`. | D33 | Same, keyed by normalised OCR text |
| Take over to submit | The human does the click. Control comes back on Done or on the next page load. The risky block is off for this case only. | D57, D58 | **Removed (Q-A).** A human never acts on the site directly. |
| Value not in the goal | `type_text` / `select_option` with a value that isn't in the goal text → the human types it. | D34 | Same check, then a human handoff for that point |
| Sensitive field | Field name contains `ssn` / `password` / `social` → always the human (unless `type_secret`) | D34 | Checked against the nearest anchor label's OCR text |
| Already filled | Refuse to ask about a field that already has a value | D54 | Re-OCR the field's box. Non-empty → `SKIP` |
| Not on a start page | `ask_human` / `request_value` / `request_missing_values` refused on `overview.htm`, `index.htm` | D34 | Same, from `page.url`. The start-page set moves to config. |
| Ask once for everything | `request_missing_values` batches every empty field into one handoff | D55 | The agent passes `fields=[{x,y,hint}, ...]` (no DOM scan is possible) |
| During any handoff | Risky buttons blocked; whole page locked outside a handoff; only the needed fields opened | D56, D59–D62 | **Replaced (Q-A):** the site tab is locked by the browser for the whole run. Humans act only through the control window, and our code performs the one allowed action. |
| Login limit | Max 3 tries. Stop on a failure text (`could not be verified`, ...) → `STUCK:` | D69 | Same, using OCR text |
| Deny links | `register`, `lookup`, `admin` are refused | D33 | Same, on OCR text and on `open_path` |
| Values from a human are recordable | `request_value` / `request_missing_values` yes; `ask_human` and take-over no | D82 | Event log marks `human_entry: true` plus the point |
| Prompt rules | Repeating 3× → `STUCK:`; always log out at the end; one tool call at a time | STEP 4 prompt | Kept, reworded for numbers and points |

### 3c. Existing tools → the new tools
| Today (DOM) | New (visual) | Change |
|---|---|---|
| `observe()` | `observe()` | Screenshot → OCR → boxes drawn with OpenCV. No JS overlay. |
| `click(ref)` | `click(ref)` + new `click_at(x,y)` | `mouse.click` at the box centre. `click_at` checks the screen changed. |
| `type_text(ref,text)` | `type_text(text, ref=None, x=None, y=None)` | `mouse.click` + `keyboard.type`, then an OCR re-read |
| `type_secret(ref,name)` | `type_secret(name, ref=None, x=None, y=None)` | Same. The re-read expects dots. |
| `select_option(ref,opt)` | `select_option(option, ref=None, x=None, y=None)` | Click, type, Enter; ↓ fallback (Q12) |
| `page_text()` | removed | `observe()`'s text list replaces it |
| — | `scroll(direction, x=None, y=None)` | `mouse.wheel`, then a new look (Q13) |
| `open_path`, `extract_value`, `finish_business_outcome` (cli.py) | same names | `extract_value(ref, save_as, value_type, description)` works from an OCR box and records a table read (Q8) |
| `request_value(ref,hint)` | `request_value(hint, ref=None, x=None, y=None)` | Point-based |
| `request_missing_values(hints)` | `request_missing_values(fields)` | The agent lists the empty boxes it sees |
| `ask_human(question)`, `finish(summary, values)` | same | — |

---

## 4. New dependencies (checked on PyPI, 2026-09-28)
- `rapidocr>=3.9.2`. The OCR engine. The default PP-OCRv6 models ship inside the wheel, so no download is needed. It pulls in `opencv-python`, `numpy`, `Pillow`, `shapely`, `pyclipper`, `omegaconf`, and `requests`.
- `onnxruntime>=1.30.0`. The inference backend. **rapidocr 3.x does not install it for you.** On Mac, wheels are arm64 only and need macOS 14+.
- `numpy>=2`. Declared explicitly because we use it directly. It already comes in through rapidocr.
- `ultimate-sitemap-parser>=1.8.1` (imports as `usp`). Needs Python ≥3.10. Pulls in `requests` and `python-dateutil`. It is used for the sitemap cell (Task 1b).
- **Not `opencv-python-headless`.** rapidocr hard-requires `opencv-python`. Both packages install the same `cv2` module and overwrite each other. Q9 already says "OpenCV comes with RapidOCR, nothing new added."
- **Where:** a new `[dependency-groups] discovery = [...]` in `pyproject.toml`, so the `cua` package stays lean. The user installs it (`uv sync --group discovery`). The builder does not.

## 5. Files
- Create `notebooks/discovery/discovery.py`: the notebook (jupytext percent), paired with `discovery.ipynb` via `jupytext --set-formats ipynb,py:percent`
- Create `notebooks/discovery/fixtures/ocr/`: fake RapidOCR outputs as JSON (section 7)
- Create `notebooks/discovery/fixtures/png/`: synthetic PNGs made by OFFLINE 0, plus real screenshots the user saves in BROWSER 3
- Create `notebooks/discovery/run_offline.py`: the OFFLINE-only runner (Q-D)
- Modify `pyproject.toml`: add the `discovery` dependency group only
- Run output (git-ignored): `notebooks/discovery/runs/<run_id>/events.jsonl`, `shots/NNN.png`, `crops/NNN.png`. Add `notebooks/discovery/runs/` to `.gitignore`.

---

## 6. Test target: ParaBank only (Q-C, DECIDED)
- **User decision, 2026-09-28:** no local test page for now. The live proof is ParaBank, driven purely visually.
- `cua.config.host_allowed` is used as is. There is no localhost exception anywhere.
- "Purely visual" is checked, not assumed:
  - `PlaywrightSurface` exposes only screenshot / mouse / keyboard / goto / url, plus the CDP lock call.
  - OFFLINE 21 greps this notebook's own source and fails if it finds any DOM-reading call: `evaluate`, `locator`, `fill`, `select_option`, `get_by_`, `query_selector`, `inner_text`, `content(`, `accessibility`, `add_init_script`, `expose_function`.
  - `page.url` is the only non-pixel fact the agent gets (used for the host gate and the start-page rule).
- The hostile legacy page (framesets, nested tables) is deferred. It goes in the open-risks list as "unproven on legacy markup".

## 7. Offline fixtures and what each proves
| Fixture | Made by | Proves |
|---|---|---|
| `png/login_synth.png`: "Username" / "Password" labels, two empty rectangles, "Log In" button, drawn with `cv2.putText` | OFFLINE 0 (built from code, so it's reproducible) | Real RapidOCR finds the 3 texts (OFFLINE 6). Crops, anchors, blanking. |
| `png/crop_neighbour_synth.png`: an empty box with an account number `20002` printed just inside the crop area | OFFLINE 0 | After blanking, re-OCR of the crop finds no digits (Q14) |
| `png/same_a.png`, `png/same_b.png` (1-pixel caret difference), `png/diff.png` | OFFLINE 0 | `screens_same` tolerates noise but catches a real change |
| `ocr/login.json`: RapidOCR-shaped `{boxes: N×4×2, txts, scores}` | hand-written | Parsing, numbering order, anchors |
| `ocr/accounts.json`: header row + 3 look-alike rows | hand-written | `TableRead(row_key="20002", column="Balance")` |
| `ocr/accounts_moved.json`: columns reordered | hand-written | The table read still finds the right cell |
| `ocr/accounts_merged_header.json`: one merged header box | hand-written | Refuses (returns `None`) |
| `ocr/two_amounts.json`: two "Amount" labels | hand-written | Anchor `ordinal=1` |
| `ocr/empty.json`: RapidOCR returns `None` | hand-written | A blank page gives an empty list, no crash |
| `FakeSurface`: records mouse/keyboard calls and returns queued PNG + OCR fixtures | OFFLINE 16 | Every tool's routing, gates, and log, with no browser |
| `FakeHuman`: scripted approve / reject / typed value / typed answer | OFFLINE 20 | Handoff paths |
| Real screenshots `png/parabank_*.png` (login, overview, transfer) | saved by the user in BROWSER 3 | Later regression checks for real OCR (optional re-run of OFFLINE 6 on them) |

---

## 8. Cell-by-cell plan (`discovery.py`)
Every OFFLINE cell ends in `assert`s and prints `OK <cell name>`. The builder writes one cell, then its asserts, in TDD order: write the asserts, see them fail with `run_offline.py`, implement, then see them pass (Q-D).

### Task 1: Setup, config, host gate (cells 0–2)
- [x] **MD**: title, how to run (order of cells, `.env` keys, `uv sync --group discovery`), OFFLINE/BROWSER key
- [x] **OFFLINE 0 — fixtures.** Draw the synthetic PNGs into `fixtures/png/` with cv2. Assert the files exist and are 1280×800.
- [x] **OFFLINE 1 — config.** `@dataclass(frozen=True) DiscoveryConfig` with viewport (1280, 800), scale 1, safe_words (per app; default empty = every click asks), deny_words, sensitive_words, start_pages, scroll_px 600, same_screen_mad 1.0, crop_pad 6, point_crop (160, 34), poll_ms 200, poll_budget_ms 3000, dropdown_down_limit 15, ocr_min_score 0.5, anchor_radius 220. Assert that it's frozen and that no ParaBank URL is in it.
- [x] **OFFLINE 2 — host gate.** Re-export `cua.config.host_allowed`. Asserts: a ParaBank URL passes; `http://127.0.0.1:8000/x`, `http://localhost/`, `file:///etc/passwd`, `https://evil.com`, and `https://parabank.parasoft.com.evil.com` are all refused.

### Task 1b: Sitemap step. One cell, run before any discovery (user, 2026-09-28)
**Why:** if the site publishes a sitemap, the agent gets the list of its pages as context, so it can go straight to the right page. If there is none, nothing changes and discovery runs as usual.
**Can we assume legacy sites have one? No.** ParaBank has none (`/robots.txt` and `/sitemap.xml` returned 404 on 2026-09-28). Old intranet apps rarely do. So "not found → carry on" is the normal case.

- [ ] **BROWSER 2b — SITEMAP (one cell).** Built around the user's own code. SITE is the website being discovered, taken from config (`BASE`), never hardcoded in the cell.
```python
# %% BROWSER 2b: SITEMAP. Runs once, before discovery. Not found → carry on as usual.
from usp.tree import sitemap_tree_for_homepage

SITE = BASE                       # the website we are discovering (from config)
SITEMAP_PAGES: list[str] = []
if host_allowed(SITE):            # only ever fetch the site we are allowed to touch
    try:
        # 1. Fetch and parse the website's sitemap structure
        tree = sitemap_tree_for_homepage(SITE)
        # 2. Iterate through all discovered pages; keep allowed ones only
        for page in tree.all_pages():
            if host_allowed(page.url) and page.url not in SITEMAP_PAGES:
                SITEMAP_PAGES.append(page.url)
    except Exception as exc:      # any failure = "no sitemap", never a crash
        print(f"sitemap: skipped ({type(exc).__name__})")
SITEMAP_CONTEXT = sitemap_context(SITEMAP_PAGES)   # OFFLINE 2b
print(f"sitemap: {len(SITEMAP_PAGES)} pages found" if SITEMAP_PAGES else "sitemap: none found, continuing as usual")
```
  - Expected on ParaBank today: `sitemap: none found, continuing as usual`.

- [x] **OFFLINE 2b — `sitemap_context(urls: list[str], cap: int = 150) -> str`.** Pure function; turns the page list into the text the agent is given.
  - Empty list → `""` (nothing added; the agent works from the screen as before).
  - Otherwise: `Pages listed in this site's sitemap (you may open_path any of them):`, then one path per line. Paths only (host and query string removed). Deny-word paths (`register`, `admin`, ...) are removed. De-duplicated, and capped with `... and N more`.
  - Asserts: an empty list → `""`; 3 URLs → header + 3 paths; `/register.htm` is dropped; the cap gives `... and N more`; no `https://` in the output.

- [x] **How it reaches the agent.**
  - BROWSER 6 and 7 send `GOAL + ("\n\n" + SITEMAP_CONTEXT if SITEMAP_CONTEXT else "")` as the first user message.
  - `open_path` also accepts a path from the sitemap list, still behind the host gate and deny words. Query values must still come from the goal. (Assert in OFFLINE 18.)
  - The event log records `{"sitemap_pages": <count>}` once per run.

### Task 2: OCR → numbered elements (cells 3–6)
- [x] **OFFLINE 3 — types + parser.** `Box(x1,y1,x2,y2)` with `.center`; `Element(ref:int, text:str, box:Box, score:float)`; `Look(gen:int, png:bytes, elements:tuple[Element,...])`; `parse_rapidocr(boxes, txts, scores, min_score) -> list[tuple[str,Box,float]]` (quad → axis box). Asserts: `login.json` gives 3 items; `empty.json` gives `[]`; a low-score item is dropped.
- [x] **OFFLINE 4 — numbering.** `RefCounter`, then `number(items, counter) -> tuple[Element,...]` in reading order (rows grouped by y-overlap, then left to right). Asserts: the order is Username, Password, Log In; a second call starts at 4; refs are never reused.
- [x] **OFFLINE 5 — draw + text list.** `draw_numbered(png, elements) -> bytes` (cv2 red rectangles + labels) and `format_elements(elements) -> str` (`[7] 'Transfer'`). Asserts: the output size equals the input; red pixels sit on each box edge; the text format is exact.
- [x] **OFFLINE 6 — real OCR smoke.** `ocr_png(png, engine) -> list[...]` using `RapidOCR()` once, shared across cells. Assert that fuzzy matching on `login_synth.png` finds the 3 labels. This proves the engine and bundled models work with no network. Print the time taken.

### Task 3: Targets, risk, geometry (cells 7–10)
- [x] **OFFLINE 7 — resolve target.** `resolve_target(look, ref, x, y, cfg) -> Point | str`. Asserts: a ref gives its box centre; a point is passed through; both given → error; neither → error; a stale ref → `"STALE: look again"`; a point outside the viewport → error.
- [x] **OFFLINE 8 — risk gate (Q-B: deny by default).** `classify_click(text: str | None, cfg) -> "deny" | "ask" | "safe"`. Text is normalised (case-folded, whitespace collapsed, trailing punctuation stripped). `safe` only on an exact match to `cfg.safe_words`. Asserts: `Log In` → safe; `log in ` → safe; `Log In Now` → ask (no partial matches); `Transfer` → ask; `Confirm` (a word never listed) → ask; `None` / empty (`click_at`) → ask; `Register` → deny; a deny word beats a safe word; an OCR misread `Log ln` → ask (fails closed).
- [x] **OFFLINE 9 — anchor (rung-2 hint).** `nearest_anchor(elements, point, cfg) -> Anchor(label, ordinal, dx, dy) | None`, preferring a label to the left, then above, within the radius. Asserts: the Username box gives `("Username", 0, +150, 0)`; `two_amounts.json` gives ordinal 1; a far-away point gives `None`.
- [x] **OFFLINE 10 — table read (Q8).** `infer_table_cell(elements, ref) -> TableRead(row_key, column) | None`. Asserts: `accounts.json` gives `("20002","Balance")`; the moved-columns fixture still works; the merged header gives `None`; the ref being the header itself gives `None` (the visual form of D101); a lone labelled value gives `None`.

### Task 4: Crops, checks, dropdown, log (cells 11–15)
- [x] **OFFLINE 11 — rung-3 crop (Q14).** `crop_box_for(target, cfg) -> Box` (the element box + pad, or a fixed box around a point). `cut_crop(png, box, elements, keep: str | None) -> bytes` fills every other OCR box inside the crop with the crop's median colour. Asserts: the crop size is right; the blanked areas are flat; the own label is kept; re-OCR of `crop_neighbour_synth` has no digits.
- [x] **OFFLINE 12 — step checks.** `typed_ok(read, expected, secret: bool)` (a secret needs ≥1 of `•●*·`); `secret_leaked(read, value) -> bool`; `screens_same(a, b, cfg)` using the mean absolute difference; `async poll_until(check, budget_ms, interval_ms, sleep)` driven by a fake sleep. Asserts: all branches, the budget runs out → False, the caret noise counts as the same screen.
- [x] **OFFLINE 13 — dropdown.** `async choose_option(surface, target, option, read_box, cfg)`: click, type, Enter, then re-read; otherwise ↓ with a re-read after each press, up to the limit. Asserts, against a fake: a direct hit; a hit after 3 ↓ presses; the limit reached → `"ASK_HUMAN"`.
- [x] **OFFLINE 14 — event log.** `EventLog(run_dir)`, with `.record(tool, args, result_prefix, look_before, crop_png, anchor, table, human_entry)` writing one JSON line plus `shots/NNN.png`, and `.path`. Secrets are logged as `{"secret_name": ...}` only. Asserts: a fake secret value written anywhere in the test is absent from every file under `run_dir`; the line count equals the number of calls.
- [x] **OFFLINE 15 — rung-hint record.** `@dataclass(frozen=True) RungHints(text: str|None, anchor: Anchor|None, crop_path: str|None, table: TableRead|None)`. This replaces the legacy `VisualTemplateLocator` signature string with a real crop path. A text-less target must have `text=None`. Assert that it serialises to a JSON round trip.

### Task 5: The agent over a Surface Protocol (cells 16–21)
- [x] **OFFLINE 16 — Surface + core.** `class Surface(Protocol)` with `screenshot()`, `click(x,y)`, `type(text)`, `press(key)`, `wheel(dx,dy,x,y)`, `goto(url)`, `url`. Plus `FakeSurface`. `VisualDiscoveryAgent(surface, ocr, cfg, log, given_text, secrets_for_origin, escalate, human)` with `observe`, `click`, `click_at`, `current_page`. Asserts: `click(3)` clicks (235,290); a stale ref is refused with no mouse call; `click_at` with an unchanged screen → `"NO CHANGE"`; a deny word is refused; each call writes one log line with a crop cut from the look before the action.
- [x] **OFFLINE 17 — typing.** `type_text`, `type_secret`. Asserts: a value not in the goal → the human path; a sensitive anchor label → the human path; `type_secret` with an unknown name → refused; a name not allowed for the origin → refused; the fake keyboard receives the value but the return blocks and log don't contain it; the re-read shows plain secret text → `STOP` + human, and nothing is logged; the crop is cut before typing (the fixture box is empty).
- [x] **OFFLINE 18 — scroll, select, open_path.** Asserts: `scroll` renumbers with new refs and old refs become stale; the same screen twice → `"BOTTOM OF PAGE"`; `select_option` uses OFFLINE 13; `open_path` checks deny words, goal values (the cli.py rule), and the host gate.
- [x] **OFFLINE 19 — extract + finish.** `extract_value(ref, save_as, value_type, description)` checks `recorder.value_matches_type` (imported from `cua.recorder`) and records a `TableRead` when there is one. `finish`, `finish_business_outcome` (proof is checked against the joined OCR text, whitespace-normalised). Asserts: `$100.00` counts as currency; a header ref is refused; a bad proof is refused.
- [x] **OFFLINE 20 — human help + gate.** `ask_human`, `request_value`, `request_missing_values(fields)`, the risky-click `escalate` path, and the login limit. Uses `FakeHuman`. Asserts: refused on start pages; `r` is remembered → DECLINED on a retry; no takeover path exists (the tool set and `escalate` return only approve / reject); `request_value` → our code types the human's control-window value at the target → an event with `human_entry: true`, the value itself not logged, the OCR read-back checked; the site lock is on before, during and after every handoff (the fake records every lock/unlock, and unlocks happen only around our own actions); an already-filled box → SKIP; the 3rd login failure → STUCK.
- [x] **OFFLINE 21 — tool wrappers.** `build_tools(agent) -> list` of `@tool(parse_docstring=True)` + `one_at_a_time` on `agent._act_lock`. Asserts: the exact tool-name set; two concurrent calls run one after the other (the fake records no overlap); no tool's schema has a parameter holding a secret value. **Pure-visual guard (Q-C):** read this notebook's own `.py` source (the cells above this one, excluding this check's own string list). Assert that none of these appear: `.evaluate(`, `.locator(`, `.fill(`, `.select_option(`, `get_by_`, `query_selector`, `inner_text`, `.content(`, `accessibility`, `add_init_script`, `expose_function`.

### Task 6: Prompt + agent build (cell 22)
- [x] **OFFLINE 22 — prompt + middleware.** `VISUAL_SYSTEM_PROMPT` (the STEP 4 rules, reworded: numbers or points, `click_at` for text-less things, `scroll` for things you can't see, `extract_value` for saved values, always log out). `middleware = build_typesafe_middleware(agent, extra_never_hide=...)`. Asserts: with no key → `[]`; the prompt names every tool; the prompt mentions no DOM tool (`page_text`).

### Task 7: BROWSER cells (the user runs them; the builder only checks syntax with `ast.parse`)
> Status 2026-09-28: every BROWSER cell is written and passes the syntax check. The boxes stay unticked until the user runs them live.
- [ ] **BROWSER 2 — browser.** Chromium, headed, `new_context(viewport=1280×800, device_scale_factor=1)`. Assert the screenshot PNG is exactly 1280×800 (Review focus 1).
- [ ] **BROWSER 3 — PlaywrightSurface + first look.** Mouse/keyboard/goto/screenshot only. `observe()` on the ParaBank login page. Show the numbered image. Check that `Username`, `Password`, and `Log In` are numbered, and that the two empty boxes are not. Save `fixtures/png/parabank_login.png`.
- [ ] **BROWSER 0 — lock check (run first; the whole Q-A design depends on it).** Send `Input.setIgnoreInputEvents(true)` on the site tab's CDP session. (a) You try to click and type in the site: nothing happens. (b) Playwright `mouse.click` while locked: record whether it is blocked. (c) Unlock → click → relock works. (d) The control window stays usable. If (a) fails, stop and re-decide Q-A.
- [ ] **BROWSER 4 — control window.** A second window with our own `set_content` page (no host). It shows the step, the values entered, the target crop, and Approve / Reject, or a value box (masked for sensitive fields) with Submit, or an answer box. `SiteLock` is on for the whole run. `escalate` and `human` are wired to it.
- [ ] **BROWSER 5 — build the agent.** `build_langchain_agent(build_tools(agent), system_prompt=VISUAL_SYSTEM_PROMPT, middleware=middleware)`.
- [ ] **BROWSER 6 — run 1, ParaBank read.** Navigate to `BASE/index.htm`. The user message is the goal plus `SITEMAP_CONTEXT` when a sitemap was found. Goal: "Log in with type_secret, read the balance of account <your account id>, and use extract_value to save it." Expected: login done with `type_secret` at points (the boxes have no text); `balance` is currency; the event log has a table read (row = account id, column = Balance); crops exist, and the password-box crop shows an empty box.
- [ ] **BROWSER 7 — run 2, ParaBank risky step.** Goal: a small transfer between your own two accounts. Expected: Transfer needs Approve in the control window; the site lock stays on; Reject → `DECLINED:`. Run it twice: once approve, once reject.
- [ ] **BROWSER 8 — audit + close.** Assert that no secret value appears in any file under `runs/`. Show every crop (the user checks by eye that no customer data is visible). Close the browser.

**Cell count: 1 markdown + 24 OFFLINE (0–22, plus 2b) + 9 BROWSER (0, 2–8, plus 2b) = 34 cells.**

---

## 9. Decisions (all answered by the user, 2026-09-28)
- **Q-A: DECIDED (user, 2026-09-28). A control window, the site locked for the whole run, zero trust.**
  - **Rule:** in a banking app, no one (agent or human) can click or type anything except the one target the current step allows. There is no trust exception.
  - **Control window:** our own small page in a second browser window (`set_content`, no host). Nothing is injected into the site, so it works on any site, framesets included.
  - **Site lock:** `SiteLock` sends Chrome DevTools `Input.setIgnoreInputEvents(ignore=true)` on the site tab's own CDP session (`context.new_cdp_session(page)`).
    - It is on from the first step to the end of the run, handoffs included.
    - It is lifted only for the instant of our own mouse or keyboard call on the allowed target (unlock → act → relock, in a `try/finally`; the D61 pattern).
  - **Humans act only through the control window.** Our code then performs the action on the allowed target.
    - Risky click: **Approve / Reject** only. Approve means our code clicks that exact target.
    - Missing value: the field's crop plus a value box (masked for sensitive fields). Our code clicks that point, types it, then re-reads it with OCR. The value is never sent to the model or written to the log; the log gets only `human_entry: true` plus the field.
    - Dropdown: the human types the option text, and our code runs `choose_option`.
    - `ask_human`: a typed text answer only, never access to the page.
  - **Take over is removed.** Anything the window can't express ends the run as `STUCK:`.
  - **Hard gate:** BROWSER 0 must prove the lock blocks real human input before anything else is built on it. If it fails, Q-A is reopened.
  - **Rejected options:**
    - The in-page bar: fails on framesets, and injects into the customer's site.
    - A notebook `input()` prompt: not production.
    - Keeping take over: breaks zero trust.
- **Q-B: DECIDED (user, 2026-09-28). Option B: deny by default, with a safe list.**
  - Every click (`click` or `click_at`) needs Approve in the control window unless its normalised OCR text exactly matches an entry in `cfg.safe_words`.
  - `click_at` on a spot with no OCR text is never safe, so it always needs approval.
  - `cfg.deny_words` are refused outright, before any approval.
  - `cfg.safe_words` lives in config per app. The ParaBank list is set in the ParaBank run cell: `log in`, `find transactions`, and its menu links. Tools hold no site values.
  - A rejected target is remembered for the run (D33).
  - The old risky-word list is dropped: fail-closed covers every button.
- **Q-C: DECIDED (user, 2026-09-28). C: ParaBank only, purely visual.** No local test page and no localhost exception. See section 6.
- **Q-D: DECIDED (user, 2026-09-28). A: the builder may run the OFFLINE cells only.**
  - **Runner:** `notebooks/discovery/run_offline.py`. A tiny script that reads `discovery.py` and runs, in order, only the cells whose header starts with `# %% OFFLINE`, in one shared namespace. It stops at the first failing assert.
  - **Python:** run it with the project's existing kernel interpreter, invoked directly by path. Never `uv run`.
  - **Never:** a BROWSER cell, a browser, the AI model, the network, or `.env` values. The runner sets `os.environ` to a scrubbed copy with no `ANTHROPIC_API_KEY`, `TYPESAFE_API_KEY` or `PARABANK_*` before running any cell.
  - **Import guard:** the runner fails if an OFFLINE cell imports `playwright`.
  - **Exception:** OFFLINE 6 runs the real RapidOCR engine on a synthetic PNG. It is local and needs no network.
  - **Workflow:** each task writes its cells, runs the runner, and must print every `OK <cell>` line before the task counts as done.
- **Q-E: DECIDED (user, 2026-09-28). A: a separate `discovery` dependency group.** `[dependency-groups] discovery = ["rapidocr>=3.9.2", "onnxruntime>=1.30.0", "numpy>=2", "ultimate-sitemap-parser>=1.8.1"]`. The user installs it with `uv sync --group discovery`. It moves to the main dependencies at the later `src/cua/` port.
- **Q-F: DECIDED (user, 2026-09-28). A: fetch the sitemap directly, tightly limited.** Allowed hosts only, never followed off-host, page paths only, deny words dropped. The log records the page count only. This is the one documented exception to the screen-only rule, and it runs before the agent starts.

## 10. Open risks
- **Model pointing accuracy.** `click_at` and typing at a point depend on the model's coordinate guesses. The fallback (Q7) is OpenCV edge detection, and only if the ParaBank runs keep missing.
- **Unproven on legacy markup** (Q-C). With no hostile page, framesets, nested tables and pages with no labels are not tested live. ParaBank is a modern-ish JSP site. Revisit before calling this legacy-ready.
- **Image resizing.** The API downscales large images. 1280×800 (about 1.0 MP) is under the limit today. If the viewport ever grows, points drift.
- **OCR speed.** RapidOCR on CPU takes roughly 0.3–1.5 s per look. With many steps, runs get slower. OFFLINE 6 prints the real time.
- **OCR misreads** ("Log ln", "$1O0.00"). Word lists and the value-type checks need fuzzy matching. A misread value fails the type check and goes to a human. It is never silently saved.
- **Plain-text password fields** (Review focus 3) and full-page screenshots. After `type_secret`, the step screenshot could show the secret if the field isn't masked. We stop and don't save that screenshot.
- **Frames and keyboard focus** (Review focus 5). Typing lands in whatever frame the click focused. The OCR re-read catches a miss.
- **The Q-A lock depends on a Chrome DevTools command** (`Input.setIgnoreInputEvents`), described as "useful while auditing page". BROWSER 0 must prove it blocks real human input. Chromium only.
- **Take over (Q21, added later).** A `take_over` tool now exists, for when the agent is truly stuck (an odd popup, a CAPTCHA). It replaces the old "no take over" rule; see OFFLINE 20.
- **Browser-level holes the lock may not cover:** the address bar, browser menus, DevTools, and closing the tab. Launch in kiosk / app mode with no address bar (`--app` or `--kiosk`), and check this in BROWSER 0.
- **Merged OCR header boxes** (Review focus 4). Refused today. If this is common, we may need `return_word_box=True` or the OpenCV grid fallback.
- **`opencv-python` versus `-headless`.** Never install both in the same env.
- **onnxruntime 1.30 needs macOS 14+ on arm64.** Pin lower if the user's Mac is older.
- **Sitemaps are often missing** (ParaBank has none), out of date, or list pages that need a login. They are a hint only. A listed page that doesn't open falls back to normal navigation.
- **TypeSafe** sends step text off the machine. It stays off unless the key is set, as today.
- **`same_screen_mad=1.0` is too loose.** Tune it on real screenshots in BROWSER 3.
- **ControlWindow in p0 lacks `take_over`.** The Protocol has no `take_over`; `AuditedControl` forwards it via `__getattr__`. Add it to the Protocol.
- **The "already filled" check can mistake grey placeholder text for a filled box** (request_value / request_missing_values would SKIP a truly empty field).
- **The take-over pane is untested in a real browser.** Only the fake (`FakeControlTO`, `FakeControlPage`) is tested.
- **Success events store outcome/proof under `extra`.** The future replay compiler must read `extra`, not top-level fields.
