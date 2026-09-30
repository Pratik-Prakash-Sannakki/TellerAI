# Coordination: discovery <-> replay

Owner: coordinator agent (writes only this file). Discovery is the source of truth for anything it
produces; replay adapts.

**Last updated:** 2026-09-28 05:01 EDT (check #3)

## Status

### Discovery (`notebooks/discovery/`, orchestrator ac2ad3f302f5be3b5; p1 builder a9cc1291cca0102fb done, p4 builder a4b8ff70020b5454d done)
Assembled by `assemble.py` from `parts/p0, p1, p2, p3, p3b, p4, p5` -> `discovery.py`. Not committed yet. Runner: ALL OFFLINE CELLS PASSED (21 cells, p0+p1+p2+p4+p5), per the orchestrator.

| Plan item | State | Where |
|---|---|---|
| MD intro, OFFLINE 1 config + shared types, 1b test helpers | done | parts/p0_contract.py |
| OFFLINE 2 host gate, 2b sitemap, BROWSER 2b | done | parts/p2_gates.py |
| OFFLINE 3-7, 9-12 (OCR parse, numbering, draw, RapidOCR, targets, anchor, table read, crop, checks) | done | parts/p1_vision.py |
| OFFLINE 8 click gate, 13 dropdown, 14 event log | done | parts/p2_gates.py |
| OFFLINE 4a-4c (site lock, control window, PlaywrightSurface) | done | parts/p4_browser.py (472 lines) |
| OFFLINE 4d-4e (open_run_browser(pw, user_dir, start_url, cfg), lock-check helpers), BROWSER 0, 2, 3 | done | parts/p5_browser_cells.py (252 lines) |
| OFFLINE 14 `write_run_json` (M3) | done | parts/p2_gates.py:282 |
| OFFLINE 15 RungHints | done (folded into OFFLINE 1) | parts/p0_contract.py:120 |
| OFFLINE 16-22 (agent core, typing, scroll/select/open_path, extract/finish, human help, tool wrappers, prompt) | in progress (p3 builder) | parts/p3_agent.py, p3b_agent.py (missing) |
| BROWSER 5, 6, 7, 8 | not started | |
| `discovery.py` assembled + `.ipynb` pair | not started | |
| `pyproject.toml` `discovery` group, `.gitignore` runs/ | done (uncommitted) | |

### Replay (`notebooks/replay/`, orchestrator a0245948081e7b9c1)
| Plan item | State |
|---|---|
| replay.md, replay_architecture.md, PLAN.md | not started (folder does not exist yet) |
| replay.py / .ipynb, parts/ | not started |

## Shared contract

Discovery side is quoted from the part files. Replay side: nothing on disk yet, so every row is
MISSING on the replay side until it lands.

| Item | Discovery defines it | Replay uses it | State |
|---|---|---|---|
| Event line fields: `step, ts, tool, args, result, shot, crop, hints, human_entry, extra` (sorted-key JSON, one per line). Writer API is now `record(tool, args, result, extras: EventExtras|None)` | parts/p2_gates.py:234-280 | - | MISSING (replay) |
| Event log file: `<run_dir>/events.jsonl` | parts/p2_gates.py:227 | - | MISSING |
| Screenshots: `<run_dir>/shots/NNN.png` (NNN = step, 3 digits), relative path stored in `shot` | parts/p2_gates.py:232-237 | - | MISSING |
| Crops: `<run_dir>/crops/NNN.png`, relative path in `crop`; cut BEFORE the action, other OCR boxes blanked to the crop's median colour | parts/p2_gates.py:232, parts/p1_vision.py:336-358 | - | MISSING |
| Crop box: element box + `crop_pad` 6, or a `point_crop` (160x34) box centred on a point, clamped to viewport | parts/p1_vision.py:336-343 | - | MISSING |
| Element model: `Element(ref:int, text:str, box:Box(x1,y1,x2,y2), score:float)`, `Look(gen, png, elements)`; refs run-wide, never reused | parts/p0_contract.py:71-101 | - | MISSING |
| Reading order: `group_rows` (y-overlap >= 50% of the smaller height, then x1) | parts/p1_vision.py:61-77 | - | MISSING (replay must use the same function, or ordinals differ) |
| Target / 3 rungs: `RungHints(text: str|None, anchor: Anchor|None, crop_path: str|None, table: TableRead|None)` | parts/p0_contract.py:120-139 | - | MISSING |
| Rung 1: `text` = the element's own OCR text; `None` for a text-less point | parts/p0_contract.py:123 | - | MISSING |
| Rung 2: `Anchor(label, ordinal, dx, dy)`; dx/dy from the LABEL BOX CENTRE to the target point; ordinal = index among casefold-equal texts in reading order; label to the left on the row (+-15 px band) else directly above, within 220 px | parts/p1_vision.py:235-247 | - | MISSING |
| Rung 3: crop PNG (see crops row); match threshold lives in replay config (Q9) | decisions.md:139 | - | MISSING |
| Table read: `TableRead(row_key, column)`, literal OCR text of the row key and header; `None` when unsure | parts/p0_contract.py:113-117, parts/p1_vision.py:293-306 | - | MISSING |
| Viewport record: `runs/<run_id>/run.json` v1 = `{version:1, run_id, start_url, viewport:{width,height}, device_scale_factor, zoom:1.0, sitemap_pages, created}`; off-host start_url -> PermissionError | parts/p2_gates.py:282-300 | - | MISSING (replay must read this for the Q10 check) |
| Click gate: `classify_click(text, cfg) -> "deny"|"ask"|"safe"`, `normalise()` | parts/p2_gates.py:104-121 | - | MISSING |
| Control window API: `ControlWindow.approve/ask_value/ask_values/ask_text/status`; `Decision = "approve"|"reject"` | parts/p0_contract.py:171-177, parts/p4_browser.py:158-230 | - | MISSING |
| Site lock: `SiteLock.lock/unlock/during()`; `CdpSiteLock` over `Input.setIgnoreInputEvents` | parts/p0_contract.py:163-168, parts/p4_browser.py:5-28 | - | MISSING |
| Surface: `url, screenshot, click, type, press, wheel, goto` | parts/p0_contract.py:151-160, parts/p4_browser.py:331-370 | - | MISSING |
| host_allowed: `cua.config.host_allowed`, used as is | parts/p0_contract.py:30, parts/p2_gates.py:1-6 | - | MISSING |
| Secrets: args log `{"secret_name": ...}` only; `EventLog.record` refuses a `value_secret` key; `assert_no_secret(run_dir, value)` | parts/p2_gates.py:243-259 | - | MISSING |
| Run folder: `notebooks/discovery/runs/<run_id>/` (events.jsonl, run.json, shots/, crops/); git-ignored | parts/p0_contract.py:34, p2_gates.py:282, .gitignore | - | MISSING. `run_id` is any str; format still not fixed (who picks it: run_goal in BROWSER 5) |
| Run header | now `run.json` (row above) | - | see above |

## Mismatches

| # | Where | Problem | Owner | State |
|---|---|---|---|---|
| M1 | PLAN.md:201 (planned OFFLINE 21 guard) vs parts/p4_browser.py OFFLINE 4b | The planned whole-notebook grep for `.evaluate(`, `expose_function` will fail on the control window, which legitimately uses them on OUR page. Fix: scan cell by cell, exclude only the "OFFLINE 4b" cell by name, plus a negative test. | discovery (p3 builder) | assigned, open until p3 lands |
| M2 | parts/p2_gates.py:269 | `hints.crop_path` could disagree with the saved `crop`. | discovery | RESOLVED 05:00: record() sets it via dataclasses.replace; asserted at p2:325-326 |
| M3 | decisions.md:151-153 (Q10) | Viewport/scale never written to the run folder. | discovery | RESOLVED 05:00: `write_run_json` (p2:282). Follow-up: replay's reader must match v1 exactly; run_id format still free-form |

## Duplication (watch list)

Replay will need these. It should reuse discovery's, not write its own:
`make_ocr_engine`/`parse_rapidocr` (p1:23-152), `group_rows` (p1:68), `fuzzy_find` (p1:155),
`normalise`/`classify_click` (p2:104-121), `screens_same`/`poll_until`/`typed_ok` (p1:398-428),
`choose_option` (p2:144), `CdpSiteLock` (p4:5), `BrowserControlWindow` (p4:158),
`PlaywrightSurface` (p4:331), `open_run_browser` (p4:486).
Open question: notebooks can't import each other. Either replay copies cells verbatim (the D70
"temporary duplication" pattern, and must say so) or these move to a shared module. Nothing
duplicated yet.

## Rule checks (discovery parts, check #3)

- DOM reads on the site: none. `evaluate`/`expose_function`/`set_content` only on the control page (allowed). PASS.
- `typing.Any` in signatures: none. Bare `except:`: none. PASS.
- Functions <= 40 lines: all pass (AST check).
- Files <= 500 lines: all parts pass now (p4 split into p4 472 + p5 252, approved by main). The assembled `discovery.py` will be ~2000+ lines; the notebook needs a stated exception.
- ParaBank strings in tool/engine code:
  - `DiscoveryConfig` defaults `start_pages={"overview.htm","index.htm"}` and `login_failure_texts` are ParaBank text (p0:46, 57-58). Config is allowed, but PLAN.md section 1 says ParaBank values live only in the run cell. Minor.
  - `open_run_browser` hardcoded `BASE + "/index.htm"`: FIXED, now a `start_url` parameter set in the BROWSER cells.
- Secrets in fixtures/logs: none. The only secret-like strings are fake test values. PASS.
- Untyped parameters (`cdp`, `page`, `pw`, `answer`, `during()` return) would fail `mypy --strict`. Minor.

## Blockers for the user

1. `uv sync --group discovery` (the new dependency group; builders may not install it).
2. Run discovery BROWSER 0 (the lock check) before anything else. The whole Q-A design depends on it.
