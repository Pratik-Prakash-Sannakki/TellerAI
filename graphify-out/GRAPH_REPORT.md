# Graph Report - BankerAgent  (2026-10-01)

## Corpus Check
- 194 files · ~185,605 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 2737 nodes · 7845 edges · 118 communities (102 shown, 16 thin omitted)
- Extraction: 93% EXTRACTED · 7% INFERRED · 0% AMBIGUOUS · INFERRED: 534 edges (avg confidence: 0.63)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `120e5ad0`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- cli.py
- FakePage
- Productionize Plan: notebooks → `src/cua/` package
- test_act.py
- Evidence README
- canvas.py
- test_recorder_types.py
- test_replay_inputs.py
- BrowserConfig
- middleware.py
- test_dropdown.py
- save_discovery_evidence / save_replay_evidence (D92)
- Replay decisions
- Five Error Demos (D30)
- langchain_typesafe
- langchain_typesafe_experimental_middleware
- DiscoveryRun
- test_cli.py
- test_replay_engine.py
- test_replay_rescue.py
- test_llm.py
- test_replay_handback.py
- config.py
- replay/evidence.py
- ReplayConfig
- recorder/__init__.py
- steps.py
- vision/__init__.py
- integration/conftest.py
- decode
- test_replay_table.py
- redact.py
- test_notebooks.py
- build_capability
- make_replay_ctx
- test_replay_evidence.py
- CLAUDE.md (project instructions)
- test_replay_steps.py
- RefCounter
- manifest.json
- langchain_tools
- safety/__init__.py
- test_human_tools.py
- replay/context.py
- cua/evidence.py
- mismatch.py
- discovery/wiring.py
- DiscoveryConfig
- ClearPage
- test_send_guard.py
- test_control_window.py
- cua.vision
- test_takeover_loop.py
- test_extension.py
- Session
- Look
- Capability
- _no_crop_pixels
- FakeTab
- test_screenshot.py
- test_recorder_runs.py
- langgraph_types
- _Request
- Discovery decisions
- 2. Each box, with an example
- request.py
- ControlWindow
- 2. Components
- HeldPage
- Pure-Visual Discovery Notebook: Build Plan
- ScriptedControl
- SiteLock
- ReplayResult
- engine.py
- GateControl
- test_routing.py
- FakeWin
- act.py
- Box
- test_import_rules.py
- fakes.py
- copy
- Route
- build_tools
- cua
- pytest
- cua.schema
- test_capability.py
- test_goal.py
- human.py
- AST
- host_allowed
- test_human.py
- interface-ai-cua
- cua.browser
- cua.handoff
- cua.safety
- cua.discovery
- cua.discovery.recorder
- cua.replay
- schema/__init__.py
- seen_outcome
- test_evidence.py
- make_ctx
- SendGuard
- test_session.py
- Replay notebook plan
- Ctx
- FakeRoute
- load_capability
- _FakeModel
- discovery/evidence.py
- FakePage
- ActTab
- background.js
- test_discovery_to_replay.py
- replay/wiring.py
- cua.discovery.agent

## God Nodes (most connected - your core abstractions)
1. `Look` - 121 edges
2. `make_ctx()` - 94 edges
3. `Ctx` - 87 edges
4. `BrowserConfig` - 85 edges
5. `ReplayConfig` - 70 edges
6. `build_capability()` - 69 edges
7. `Element` - 63 edges
8. `make_replay_ctx()` - 60 edges
9. `_meta()` - 57 edges
10. `Box` - 55 edges

## Surprising Connections (you probably didn't know these)
- `test_the_login_click_before_a_menu_link_is_kept()` --calls--> `step_events()`  [INFERRED]
  tests/unit/discovery/recorder/test_recorder_runs.py → src/cua/discovery/recorder/events.py
- `test_a_target_needs_a_findable_rung()` --calls--> `Target`  [INFERRED]
  tests/unit/schema/test_capability.py → src/cua/schema/capability.py
- `test_meta_is_loose()` --calls--> `CapabilityMeta`  [INFERRED]
  tests/unit/schema/test_capability.py → src/cua/schema/capability.py
- `test_stop_carries_its_fields()` --calls--> `Stop`  [INFERRED]
  tests/unit/schema/test_result.py → src/cua/schema/result.py
- `ActTab` --uses--> `Session`  [INFERRED]
  tests/fakes.py → src/cua/browser/session.py

## Import Cycles
- 3-file cycle: `src/cua/discovery/tools/__init__.py -> src/cua/discovery/tools/act.py -> src/cua/discovery/tools/guard.py -> src/cua/discovery/tools/__init__.py`
- 3-file cycle: `src/cua/discovery/tools/__init__.py -> src/cua/discovery/tools/act.py -> src/cua/discovery/tools/observe.py -> src/cua/discovery/tools/__init__.py`
- 3-file cycle: `src/cua/discovery/tools/__init__.py -> src/cua/discovery/tools/read.py -> src/cua/discovery/tools/guard.py -> src/cua/discovery/tools/__init__.py`
- 3-file cycle: `src/cua/discovery/tools/__init__.py -> src/cua/discovery/tools/human.py -> src/cua/discovery/tools/observe.py -> src/cua/discovery/tools/__init__.py`
- 3-file cycle: `src/cua/discovery/tools/__init__.py -> src/cua/discovery/tools/nav.py -> src/cua/discovery/tools/guard.py -> src/cua/discovery/tools/__init__.py`
- 3-file cycle: `src/cua/discovery/tools/__init__.py -> src/cua/discovery/tools/nav.py -> src/cua/discovery/tools/observe.py -> src/cua/discovery/tools/__init__.py`
- 3-file cycle: `src/cua/discovery/tools/guard.py -> src/cua/discovery/tools/human.py -> src/cua/discovery/tools/observe.py -> src/cua/discovery/tools/guard.py`
- 4-file cycle: `src/cua/discovery/tools/__init__.py -> src/cua/discovery/tools/act.py -> src/cua/discovery/tools/human.py -> src/cua/discovery/tools/observe.py -> src/cua/discovery/tools/__init__.py`
- 4-file cycle: `src/cua/discovery/tools/__init__.py -> src/cua/discovery/tools/act.py -> src/cua/discovery/tools/observe.py -> src/cua/discovery/tools/guard.py -> src/cua/discovery/tools/__init__.py`
- 4-file cycle: `src/cua/discovery/tools/__init__.py -> src/cua/discovery/tools/human.py -> src/cua/discovery/tools/observe.py -> src/cua/discovery/tools/guard.py -> src/cua/discovery/tools/__init__.py`
- 4-file cycle: `src/cua/discovery/tools/__init__.py -> src/cua/discovery/tools/nav.py -> src/cua/discovery/tools/observe.py -> src/cua/discovery/tools/guard.py -> src/cua/discovery/tools/__init__.py`
- 5-file cycle: `src/cua/discovery/tools/__init__.py -> src/cua/discovery/tools/act.py -> src/cua/discovery/tools/guard.py -> src/cua/discovery/tools/human.py -> src/cua/discovery/tools/observe.py -> src/cua/discovery/tools/__init__.py`
- 5-file cycle: `src/cua/discovery/tools/__init__.py -> src/cua/discovery/tools/act.py -> src/cua/discovery/tools/human.py -> src/cua/discovery/tools/observe.py -> src/cua/discovery/tools/guard.py -> src/cua/discovery/tools/__init__.py`
- 5-file cycle: `src/cua/discovery/tools/__init__.py -> src/cua/discovery/tools/read.py -> src/cua/discovery/tools/guard.py -> src/cua/discovery/tools/human.py -> src/cua/discovery/tools/observe.py -> src/cua/discovery/tools/__init__.py`
- 5-file cycle: `src/cua/discovery/tools/__init__.py -> src/cua/discovery/tools/nav.py -> src/cua/discovery/tools/guard.py -> src/cua/discovery/tools/human.py -> src/cua/discovery/tools/observe.py -> src/cua/discovery/tools/__init__.py`

## Communities (118 total, 16 thin omitted)

### Community 0 - "cli.py"
Cohesion: 0.14
Nodes (23): argparse, Namespace, _close(), default_site(), discover(), main(), parse_args(), parse_inputs() (+15 more)

### Community 1 - "FakePage"
Cohesion: 0.12
Nodes (9): FakeControl, FakePage, A fake discovery/replay ``CONTROL`` surface (what ``ControlWindow`` presents).…, A fake ``playwright.async_api.Page``. Every awaited method is recorded in…, asyncio, Tests for the shared offline fakes in tests/fakes.py (TDD: written before the…, TestFakeControl, TestFakePage (+1 more)

### Community 2 - "Productionize Plan: notebooks → `src/cua/` package"
Cohesion: 0.12
Nodes (16): 10. Line-count offenders (today), 1. Package tree, 2. De-duplication (checked by AST diff of both notebooks), 3. State: globals → explicit objects, 4. Async and typing, 5. Notebooks after the move, 6. Tests, 7. ML-engineering practices (kept small) (+8 more)

### Community 3 - "test_act.py"
Cohesion: 0.07
Nodes (77): Items, (value, pattern) for an extract: the whole box when it is exactly the type,…, value_in_box(), make_look(), A look whose elements are numbered 1.. in order (ref, text, box)., Driven, _head(), _helped() (+69 more)

### Community 5 - "canvas.py"
Cohesion: 0.18
Nodes (12): canvas_size(), NDArray, uint8, Canvas-pixel <-> page-point mapping: any window size or pixel density maps to…, Fit the screenshot inside the canvas. Returns it and canvas-pixel -> page-point…, The size of the image the model is looking at right now., to_canvas(), parametrize (+4 more)

### Community 6 - "test_recorder_types.py"
Cohesion: 0.11
Nodes (28): input_name(), event_shapes(), input_types(), pick_type(), Typed inputs: an input's type is inferred from the SHAPES of the values typed…, Every shape the whole value matches, in precedence order. Safe to log: names,…, One input's type from each of its values' shapes. Unknown shapes (None) ->…, input name -> the shapes of the value it took in this event (None: not logged). (+20 more)

### Community 7 - "test_replay_inputs.py"
Cohesion: 0.14
Nodes (35): Path, select(), type_(), write_cap(), _cap(), env(), FakeForm, FakePage (+27 more)

### Community 8 - "BrowserConfig"
Cohesion: 0.06
Nodes (39): act(), into_box(), Lock, Page, Session, Step, Our own input into the locked site tab: ``act`` (unlock, run steps, relock,…, The response to a send lands after the human's approval, not after the click:… (+31 more)

### Community 9 - "middleware.py"
Cohesion: 0.07
Nodes (43): AIMessage, CompiledStateGraph, deepagents, Handler, langchain_agents_middleware, build_agent(), BaseChatModel, Ctx (+35 more)

### Community 10 - "test_dropdown.py"
Cohesion: 0.07
Nodes (40): BaseException, Confirm, LookFn, choose_option_at_index(), choose_option_at_point(), list_options(), Dropdown, Page (+32 more)

### Community 12 - "Replay decisions"
Cohesion: 0.08
Nodes (23): R10: where the compile step lives — DECIDED, R11: why compile, if `response_format` exists? — PROPOSED, R12: what each step type compiles to — PROPOSED, R13: target schema — PROPOSED, R14: what rung 2 needs that discovery doesn't record — DONE, R15: auto-approve at replay — PROPOSED, R16: dead ends and retries at compile — PROPOSED, R17: replay result statuses — PROPOSED (+15 more)

### Community 16 - "DiscoveryRun"
Cohesion: 0.12
Nodes (17): Saved, The current run (the one the send guard serves)., DiscoveryRun, What the human gave: the goal and every answer (the send guard's mismatch text)., Every saved text, table cells included (evidence masking only)., Banking: values live only for the run. Keep the log (labels only), drop the…, saved_texts(), wipe() (+9 more)

### Community 17 - "test_cli.py"
Cohesion: 0.13
Nodes (23): _fake_session(), _patch_session(), CaptureFixture, MonkeyPatch, parametrize, Path, SimpleNamespace, cua.cli: argument parsing, --input parsing, and main() as the only asyncio.run… (+15 more)

### Community 18 - "test_replay_engine.py"
Cohesion: 0.22
Nodes (42): cap(), click(), extract(), _finish(), _login_cap(), _no_snap(), _only(), _pcap() (+34 more)

### Community 19 - "test_replay_rescue.py"
Cohesion: 0.20
Nodes (27): The guard keeps its own reference to the control window: swap both., set_control(), _env(), _fail_clicks(), HangPage, HumanSimple, asyncio, MonkeyPatch (+19 more)

### Community 20 - "test_llm.py"
Cohesion: 0.20
Nodes (14): _clean_env(), _gateway(), fixture, MonkeyPatch, Offline tests for `cua.llm.make_chat_model`. No network, no real key. Default:…, test_ca_bundle_passthrough(), test_existing_ssl_cert_file_wins(), test_gateway_env_means_gateway() (+6 more)

### Community 21 - "test_replay_handback.py"
Cohesion: 0.20
Nodes (18): _bctx(), Ext, Human, PanelDone, asyncio, Ctx, parametrize, The toolbar hand-back button during a rescue (its service worker, never the… (+10 more)

### Community 22 - "config.py"
Cohesion: 0.07
Nodes (45): dotenv, os, pathlib, _actions(), _find_root(), load_site(), OutcomeRule, _outcomes() (+37 more)

### Community 23 - "replay/evidence.py"
Cohesion: 0.15
Nodes (19): _clean(), _png(), OcrFn, Redact, _drift_lines(), masked_outputs(), Ctx, JsonValue (+11 more)

### Community 24 - "ReplayConfig"
Cohesion: 0.05
Nodes (64): SameTextLike, Replay-only settings., ReplayConfig, Replay: runs a capability saved by discovery with plain code, no LLM (step 4:…, anchor_point(), find_template(), find_text(), locate() (+56 more)

### Community 25 - "recorder/__init__.py"
Cohesion: 0.08
Nodes (49): check_savable(), Raise NotSaved before any model call when this run cannot become a capability., ``build_capability``'s refusals, unchanged: a leaked value, a blind dropdown,…, _refuse(), used_inputs(), checkpoint(), The capability's checkpoint: the text replay must see to call the run a…, C: after a send, the page's own response proves success (the agent's proof only… (+41 more)

### Community 26 - "steps.py"
Cohesion: 0.09
Nodes (51): Point, fill(), Put inputs into `{{name}}`. `{{secret:x}}` stays as it is: secrets go in only…, changed(), choose_option(), do_click(), do_extract(), do_extract_table() (+43 more)

### Community 27 - "vision/__init__.py"
Cohesion: 0.10
Nodes (32): Pixels -> text: screenshots, OCR, canvas math, crops, and the shared table…, append_rows(), cell_shape(), col_of(), column_spans(), like_rows(), The shared OCR table reader: discovery and replay use it to find a table's…, A table's end: a line that no longer looks like its rows (a footer, a menu, a… (+24 more)

### Community 29 - "decode"
Cohesion: 0.17
Nodes (22): mask_png(), OcrFn, Black out every OCR box whose text holds a run value. A clean image is written…, decode(), encode(), NDArray, uint8, load() (+14 more)

### Community 30 - "test_replay_table.py"
Cohesion: 0.23
Nodes (17): _cap(), _defs(), Page, asyncio, Ctx, MonkeyPatch, Path, do_extract_table: find the header by its label, read the rows with discovery's… (+9 more)

### Community 31 - "redact.py"
Cohesion: 0.12
Nodes (18): Pattern, re, _num(), Value masking: ``norm``, ``is_sensitive``, ``hide_secrets``, ``redactor``,…, text -> text with every value masked. Numbers match however they are written…, redactor(), Value types an extract may declare. Shared by discovery and replay (one table,…, test_a_short_number_is_masked_only_as_a_whole_number() (+10 more)

### Community 32 - "test_notebooks.py"
Cohesion: 0.26
Nodes (16): Call, Module, _bind(), _code_cells(), _markdown(), _offline_namespace(), parametrize, Path (+8 more)

### Community 33 - "build_capability"
Cohesion: 0.08
Nodes (69): build_capability(), Steps, inputs and secrets come from the log only. The model's text cannot fail…, flag_leaks(), Mark (never store) an event whose label, anchor, own text, hint or input name…, _ev(), _meta(), Path, The recorder: the event log becomes a replay-ready capability (R12, R13, R16).… (+61 more)

### Community 34 - "make_replay_ctx"
Cohesion: 0.09
Nodes (42): FakeLock, make_replay_ctx(), mk_look(), Ctx, Replay test helpers: ``make_replay_ctx`` (a real Ctx on fakes), ``mk_look``,…, SiteLock stand-in: open() unlocks for the block., A real Ctx (real SendGuard, real ReplayRun) over a fake page/control/lock.…, ``take_look`` always returns this look. (+34 more)

### Community 35 - "test_replay_evidence.py"
Cohesion: 0.30
Nodes (17): _all_text(), fake_ocr(), _png(), Ctx, fixture, Path, save_evidence writes one masked folder per run: summary, drift, failure (only…, A capability on disk, a fake OCR that reads the value, and the last run's mask… (+9 more)

### Community 36 - "CLAUDE.md (project instructions)"
Cohesion: 0.12
Nodes (19): CLAUDE.md (project instructions), D101: labeled_value refuses a table-header resolution (general fix), D102: label_header/value_header flags ported into agent.py + cli.py capture path, D92: Evidence Capture Helpers (save_discovery_evidence/save_replay_evidence), D93: Pre-existing 02_artifact_schema.py IndexError bug, D95: Missing create_deep_agent import found live in BROWSER 12, D96: build_agent() goal_text vs given_text field-name bug, D97: cua replay --login flag + repeated Balance header trap (+11 more)

### Community 37 - "test_replay_steps.py"
Cohesion: 0.08
Nodes (36): navigate(), _click_env(), GotoPage, _judge(), Page, asyncio, Ctx, MonkeyPatch (+28 more)

### Community 38 - "RefCounter"
Cohesion: 0.09
Nodes (35): RapidOCR, draw_numbered(), number(), ocr(), ocr_engine(), NDArray, uint8, The shared RapidOCR engine, OCR itself, numbering and the numbered-box overlay.… (+27 more)

### Community 39 - "manifest.json"
Cohesion: 0.11
Nodes (18): action, default_icon, default_title, background, service_worker, 128, 16, 32 (+10 more)

### Community 41 - "safety/__init__.py"
Cohesion: 0.12
Nodes (13): Safety: what may leave the tab (hosts, the two send gates) and keeping values…, Protocol, The fields of a ``playwright.async_api.Request`` the guard reads., Request, ControlLike, GuardOptions, LookLike, Protocol (+5 more)

### Community 42 - "test_human_tools.py"
Cohesion: 0.28
Nodes (15): blank_png(), A plain PNG of this canvas size (canvas/crops decode the look's png)., _ctx(), asyncio, Ctx, MonkeyPatch, finish_business_outcome / request_missing_values / ask_human (the human-facing…, test_ask_human_asks_with_the_question() (+7 more)

### Community 43 - "replay/context.py"
Cohesion: 0.08
Nodes (28): pydantic, Ctx, note_takeover_send(), Page, Request, Ctx: what every replay function takes first (session, run, settings, send…, R7: nothing kept. A fresh run, and the guard reads that one from now on., wipe() (+20 more)

### Community 44 - "cua/evidence.py"
Cohesion: 0.13
Nodes (19): config_hash(), git_sha(), JsonValue, Path, Evidence helpers shared by discovery and replay: masking a JSON-able tree,…, `git rev-parse HEAD`, or "unknown" (no git, not a repo, any failure)., sha256 of the repr of the frozen configs plus the site name., What ``run.json`` holds: prompt version, model, config hash, git sha. Never a… (+11 more)

### Community 45 - "mismatch.py"
Cohesion: 0.22
Nodes (13): dropdown_options(), mismatches(), _norm_num(), Dropdown, Values a send carries that the human never gave, and the dropdown choices to…, Numbers being sent that the human never gave, e.g. account 1450 vs 1400. Only…, For each key: the options of the page dropdown whose CURRENT value is exactly…, _hide() (+5 more)

### Community 46 - "discovery/wiring.py"
Cohesion: 0.15
Nodes (15): build_ctx(), _count_nav(), _hooks(), Ctx, Session, Attach discovery to an open browser session: the send guard on every request,…, Counts on the ctx of the latest attach to this page., Discovery's post-approve steps, in guard_send's order. ``holder`` gets the ctx… (+7 more)

### Community 47 - "DiscoveryConfig"
Cohesion: 0.16
Nodes (31): DiscoveryConfig, Discovery-only settings., Discovery: an LLM agent learns a task once and the recorder saves it as a…, attach(), new_run(), A fresh run for this goal (run_goal's ``HANDOFF = HandoffState(goal=goal)``)., Route every request through a new send guard, open the control window. Re-run…, make_session() (+23 more)

### Community 49 - "test_send_guard.py"
Cohesion: 0.16
Nodes (23): Side-specific steps, each at the exact point its notebook ran it. on_request:…, SendHooks, Control, _new(), _no_dropdowns(), _old(), _play(), parametrize (+15 more)

### Community 50 - "test_control_window.py"
Cohesion: 0.28
Nodes (22): Factory, SIDES, asyncio, parametrize, ControlWindow: one class, both sides' behaviour. Ported from…, Discovery calls _front inside try (the question is removed on failure); replay…, Regression: a gate during a take-over must win, then hand the take-over back…, _settle() (+14 more)

### Community 51 - "cua.vision"
Cohesion: 0.50
Nodes (3): cua.vision, Read order, What may NOT go here

### Community 52 - "test_takeover_loop.py"
Cohesion: 0.12
Nodes (27): replay_control(), Asker, hand_back(), Future, Lock, Protocol, The shared take-over loop pieces. Each side's own take-over stays with that…, Done on the toolbar button or in the take-over panel hands back. No reminders… (+19 more)

### Community 53 - "test_extension.py"
Cohesion: 0.11
Nodes (28): Answerable, button_clicked(), ext_call(), Extension, handback_button(), Future, Protocol, The hand-back extension (the Chrome toolbar button): its service worker, never… (+20 more)

### Community 54 - "Session"
Cohesion: 0.15
Nodes (20): BrowserContext, Playwright, playwright_async_api, Playwright, no decisions: the open session, the site lock, our own input,…, _alive(), check_viewport(), close_session(), _extension() (+12 more)

### Community 55 - "Look"
Cohesion: 0.09
Nodes (55): Cols, _columns(), clean_label(), column_header(), headings(), is_header(), is_word(), label_near() (+47 more)

### Community 56 - "Capability"
Cohesion: 0.15
Nodes (24): Exception, _ask(), ask_inputs(), ask_option(), _ask_rows(), given_inputs(), input_type(), mistyped() (+16 more)

### Community 57 - "_no_crop_pixels"
Cohesion: 0.50
Nodes (3): _no_crop_pixels(), fixture, MonkeyPatch

### Community 58 - "FakeTab"
Cohesion: 0.12
Nodes (3): FakeTab, SimpleNamespace, A fake site or control tab with the Playwright calls discovery's wiring and…

### Community 59 - "test_screenshot.py"
Cohesion: 0.27
Nodes (9): _png(), asyncio, MonkeyPatch, take_look: page calls on the loop, the CPU part (OCR, drawing, encoding) in one…, ShotPage, test_page_width_reads_the_window_width(), test_snap_look_gives_the_look_png_or_none_on_timeout(), test_snap_png_passes_the_timeout_and_gives_none_on_error() (+1 more)

### Community 60 - "test_recorder_runs.py"
Cohesion: 0.13
Nodes (25): _click(), _clicks(), _go(), _names(), _nav(), _noop_click(), _paths(), Recorder behaviour pinned by live runs: detours, 404s, login clicks kept, no-op… (+17 more)

### Community 63 - "Discovery decisions"
Cohesion: 0.08
Nodes (24): Base decisions, Cuts, Discovery decisions, Q10: window size and zoom — DECIDED, Q11: notebook format — DECIDED, Q12: dropdowns — DECIDED, Q13: scrolling — DECIDED, Q14: private data in saved pictures — DECIDED (+16 more)

### Community 64 - "2. Each box, with an example"
Cohesion: 0.12
Nodes (15): 1. Diagram, 2. Each box, with an example, 3. All tools, 4. Step by step: one discovery run, 5. Notes, Browser (Playwright), Control window and site lock (Q-A), Discovery architecture (+7 more)

### Community 65 - "request.py"
Cohesion: 0.14
Nodes (21): functools, JsonObj, _flat(), _json(), pretty(), What a held request sends, and the same request rebuilt with edited values.…, Every value a request sends, from its query, a form body, or a JSON body…, The request's url and body with these values put back in, in the same format. (+13 more)

### Community 66 - "ControlWindow"
Cohesion: 0.09
Nodes (22): base64, json, Question, ControlWindow, discovery_control(), _img(), Protocol, ControlWindow: our own "Agent control" tab, the only place a human answers.… (+14 more)

### Community 67 - "2. Components"
Cohesion: 0.12
Nodes (15): 1. Diagram, 2. Components, 3. Step types, 4. Worked example: ParaBank login + read balance, 5. Notes, Actor, Artifact (made by discovery, not replay), Browser setup (+7 more)

### Community 68 - "HeldPage"
Cohesion: 0.12
Nodes (9): DoneWhileSending, FormRoute, HeldPage, HeldRoute, NeverAnsweredGate, Ctx, Like Playwright: while a form POST (a navigation) is held, `page.screenshot()`…, The human clicks Done just as their form POST is held: the gate must still show… (+1 more)

### Community 69 - "Pure-Visual Discovery Notebook: Build Plan"
Cohesion: 0.09
Nodes (22): 10. Open risks, 1. Global constraints (every task must follow these), 2. Review focus (inputs no spec line covers, but likely to bite), 3. What already exists (reuse, or its visual version), 3a. How the agent is built today (`agent.ipynb` STEP 4, `src/cua/agent.py`), 3b. Existing handoff rules: when a human is called in, 3c. Existing tools → the new tools, 4. New dependencies (checked on PyPI, 2026-09-28) (+14 more)

### Community 71 - "SiteLock"
Cohesion: 0.16
Nodes (12): CdpSender, Protocol, SiteLock: the site tab ignores all real input (CDP…, The one method of a Playwright ``CDPSession`` the lock uses. ``params`` is a…, The site tab ignores all real input (CDP). Lifted only around our own action or…, SiteLock, FakeCdp, asyncio (+4 more)

### Community 73 - "ReplayResult"
Cohesion: 0.16
Nodes (11): ReplayResult, test_partial_label_when_not_success(), test_result_type_is_the_schema_one(), test_the_outputs_line_shows_rows(), ReplayResult summary/outputs_line, Stop, and the Status values., test_partial_outputs_line_when_not_success(), test_result_defaults(), test_stop_carries_its_fields() (+3 more)

### Community 75 - "engine.py"
Cohesion: 0.12
Nodes (41): Drift, action_allowed(), _cleanup_step(), error_page(), finish(), is_cleanup(), judge(), login_came_back() (+33 more)

### Community 77 - "test_routing.py"
Cohesion: 0.06
Nodes (50): ChatAnthropic, ModelKind, ModuleType, build_routing_middleware(), Classifier, confidence_gate(), job_tool_names(), _model_router() (+42 more)

### Community 79 - "act.py"
Cohesion: 0.09
Nodes (58): P, crop(), Crop around the target, every other text blanked (sized to the current canvas)., Every value typed, entered, given or sent this run, plus the secrets (in memory…, run_values(), landed(), _landing(), make_act_tools() (+50 more)

### Community 80 - "Box"
Cohesion: 0.07
Nodes (42): dataclasses, DiscoveryRun: one discovery run's working state (was the notebook's…, crop_box(), cut_crop(), _ink(), input_box(), Crops around one point: find the element there, crop around it, read text near…, New ink appeared INSIDE the input box (text, or a password's dots). A click… (+34 more)

### Community 81 - "test_import_rules.py"
Cohesion: 0.29
Nodes (13): _cua_imports(), _layer_files(), _module(), parametrize, Path, The package's import rule (docs/PRODUCTIONIZE_PLAN.md section 1), read from…, The top-level cua subpackage of every ``cua.*`` import (``import`` or ``from``)., Guard the guard: a planted forbidden import is caught in both spellings. (+5 more)

### Community 82 - "fakes.py"
Cohesion: 0.19
Nodes (10): langgraph_checkpoint_memory, FakeLock, Shared offline fakes for the ported test suite (tests/unit, tests/integration).…, A fake ``cua.browser.SiteLock``: ``open()`` records unlock/lock, nothing else., _capture(), MonkeyPatch, build_agent: the notebook's create_deep_agent call, with routing appended only…, test_build_agent_wires_the_notebooks_agent() (+2 more)

### Community 84 - "Route"
Cohesion: 0.15
Nodes (5): Frame, HumanControl, Takes over; while 'in control', the human opens a page and sends a form., Req, Route

### Community 85 - "build_tools"
Cohesion: 0.09
Nodes (17): AsyncFunctionDef, inspect, build_tools(), BaseTool, Ctx, observe, click, type_text, type_secret, select_option, scroll, open_path,…, The prompts are the first filter (user, 2026-09-30); the models and code checks…, test_the_prompt_lists_every_tool() (+9 more)

### Community 86 - "cua"
Cohesion: 0.50
Nodes (3): cua, Read order, Rules

### Community 87 - "pytest"
Cohesion: 0.17
Nodes (10): pytest, _fake_llm_keys(), fixture, MonkeyPatch, Suite-wide: never let a real LLM key from `.env` reach a test (cua.config loads…, A fake direct-Anthropic key so code that builds a chat model works offline; no…, parametrize, Path (+2 more)

### Community 88 - "cua.schema"
Cohesion: 0.50
Nodes (3): cua.schema, Read order, What may NOT go here

### Community 91 - "test_capability.py"
Cohesion: 0.12
Nodes (17): MonkeyPatch, parametrize, Path, Every capability saved in the top-level artifacts/ folder (Decision 6) loads in…, test_a_saved_artifact_loads_in_replay(), test_a_saved_artifact_round_trips(), test_the_old_artifacts_folder_is_gone(), _data() (+9 more)

### Community 92 - "test_goal.py"
Cohesion: 0.10
Nodes (31): An evidence screenshot: short timeout, None on failure (never hangs on a held…, snap(), Agent, Ctx, Protocol, run_goal: one goal through the discovery agent (moved from discovery.py…, What run_goal needs of the compiled deep agent., The deadline passed: end the run STUCK, keeping what the agent did so far. (+23 more)

### Community 93 - "human.py"
Cohesion: 0.15
Nodes (25): Field, into_box(), Step, Focus the site tab, click the box, clear it, type (see…, _enter(), human_fills(), _in_control(), _make_ask_human() (+17 more)

### Community 94 - "AST"
Cohesion: 0.21
Nodes (12): AST, parametrize, Path, cua.schema.value_types matches both notebooks' SHAPES/TYPES exactly., SHAPES and TYPES as each notebook defines them (TYPES spreads SHAPES, so exec…, _tables(), test_tables_equal_the_notebooks(), test_value_matches_type() (+4 more)

### Community 96 - "host_allowed"
Cohesion: 0.29
Nodes (5): host_allowed(), Which hosts the browser may reach (D15). The allowlist itself lives in the site…, True if `url`'s host is on the site's allowlist (D15). ``about:blank`` is…, host_allowed: only the site's own hosts (D15); about:blank always., test_only_allowed_hosts_and_blank()

### Community 98 - "test_human.py"
Cohesion: 0.14
Nodes (41): human_help(), Q21, open-ended: the human answers in words, takes over the site, or stops the…, Q21: the one time the site unlocks for a human. What they did is kept as…, take_over(), _answer(), _badge(), _ctx(), _dirty() (+33 more)

### Community 100 - "cua.browser"
Cohesion: 0.40
Nodes (4): cua.browser, How it fits, Read order, What may NOT go here

### Community 101 - "cua.handoff"
Cohesion: 0.40
Nodes (4): cua.handoff, How it fits, Read order, What may NOT go here

### Community 102 - "cua.safety"
Cohesion: 0.40
Nodes (4): cua.safety, Read order, Rules, What may NOT go here

### Community 103 - "cua.discovery"
Cohesion: 0.40
Nodes (4): Contracts for the tools / agent (steps 8b, 8c), cua.discovery, Read order, What may NOT go here

### Community 104 - "cua.discovery.recorder"
Cohesion: 0.50
Nodes (3): cua.discovery.recorder, Read order, What may NOT go here

### Community 105 - "cua.replay"
Cohesion: 0.40
Nodes (4): cua.replay, How it fits, Read order, What may NOT go here

### Community 106 - "schema/__init__.py"
Cohesion: 0.14
Nodes (35): BaseModel, model_validator, _navigate(), output(), Step, Event log -> ``Capability``: steps, inputs, outputs and secrets come from the…, The {{input}} names the steps use, in order. {{secret:x}} is not an input., ``to_step``'s open_path branch, unchanged. (+27 more)

### Community 107 - "seen_outcome"
Cohesion: 0.67
Nodes (3): The first rule whose text (whole words, any case) appeared on screen with this…, seen_outcome(), test_text_already_on_screen_before_the_step_is_not_an_outcome()

### Community 109 - "test_evidence.py"
Cohesion: 0.26
Nodes (16): _artifact(), masked(), fixture, MonkeyPatch, Path, save_evidence: one masked folder per run. No run value or secret is ever…, The OCR mask is tested in tests/unit/safety; here: that every PNG goes through…, _save() (+8 more)

### Community 110 - "make_ctx"
Cohesion: 0.12
Nodes (36): make_ctx(), Ctx, Session, A discovery ``Ctx`` over fakes, built like ``attach`` but with no page wiring., helped(), _only(), asyncio, fixture (+28 more)

### Community 111 - "SendGuard"
Cohesion: 0.18
Nodes (5): Request, ``await guard(route)`` is the route handler. ``guard.lock`` is the send gate:…, Gate 1: Approve, or Edit = back to the form with every value, then again.…, RouteLike, SendGuard

### Community 112 - "test_session.py"
Cohesion: 0.24
Nodes (11): LivePage, _png(), asyncio, MonkeyPatch, Path, open_session reuses a live session (a notebook re-run must not leak a browser),…, _session(), test_a_live_existing_session_is_returned_unchanged() (+3 more)

### Community 113 - "Replay notebook plan"
Cohesion: 0.33
Nodes (5): Decisions made here (review), Open questions for the user, Replay notebook plan, Sections, Tasks

### Community 114 - "Ctx"
Cohesion: 0.11
Nodes (32): act(), canvas(), choose_option(), _count_start(), Ctx, list_options(), look(), Page (+24 more)

### Community 117 - "FakeRoute"
Cohesion: 0.15
Nodes (19): FakeRoute, A fake ``playwright.async_api.Route``: records every…, _approve(), HeldPage, _logged(), asyncio, Ctx, Path (+11 more)

### Community 118 - "load_capability"
Cohesion: 0.16
Nodes (26): load_capability(), load_outcomes(), _missing_crops(), Path, The capability and the folder its crop paths are relative to., The capability's own `outcomes:` [{text, status, meaning}], else the site's…, fixture, MonkeyPatch (+18 more)

### Community 121 - "_FakeModel"
Cohesion: 0.18
Nodes (7): _FakeModel, asyncio, Stands in for a LangChain chat model: no network, records the prompt., asyncio, test_describe_names_the_table_outputs(), _Structured, test_describe_asks_the_given_model_with_labels_and_input_names_only()

### Community 123 - "discovery/evidence.py"
Cohesion: 0.17
Nodes (17): The discovery agent: system prompt, middleware, optional TypeSafe routing, and…, The discovery agent's system prompt, verbatim from…, _copy_capability(), _events(), _folder(), Ctx, OcrFn, Path (+9 more)

### Community 124 - "FakePage"
Cohesion: 0.25
Nodes (4): FakePage, The site page: any call made on it for the button is a bug., SitePage, FakePage

### Community 125 - "ActTab"
Cohesion: 0.25
Nodes (4): ActTab, FakeInput, A fake ``page.mouse`` / ``page.keyboard``: every call is recorded as ``(name,…, A site tab the act/nav tools drive: ``mouse``/``keyboard`` record into…

### Community 127 - "test_discovery_to_replay.py"
Cohesion: 0.25
Nodes (9): fixture, MonkeyPatch, Path, Discovery's saved artifact runs in replay unchanged: build -> save -> load ->…, saved(), test_crop_paths_resolve_to_saved_files(), test_rung2_offset_hits_the_point_discovery_acted_on(), test_saved_artifact_loads_as_is() (+1 more)

### Community 131 - "replay/wiring.py"
Cohesion: 0.14
Nodes (14): attach(), _note_latest(), note_response(), Protocol, Session, Page wiring for replay: :func:`attach` (the notebook's setup cell, replay.py…, The Playwright ``Response`` fields note_response reads., Wire replay onto an open session and return its Ctx. (+6 more)

### Community 141 - "cua.discovery.agent"
Cohesion: 0.50
Nodes (3): cua.discovery.agent, Read order, What may NOT go here

## Knowledge Gaps
- **159 isolated node(s):** `MODES`, `manifest_version`, `name`, `version`, `description` (+154 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **16 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Look` connect `Look` to `FakePage`, `replay/wiring.py`, `test_act.py`, `canvas.py`, `BrowserConfig`, `test_dropdown.py`, `DiscoveryRun`, `test_replay_rescue.py`, `ReplayConfig`, `steps.py`, `vision/__init__.py`, `make_replay_ctx`, `test_replay_steps.py`, `RefCounter`, `discovery/wiring.py`, `Session`, `FakeTab`, `test_screenshot.py`, `_Request`, `act.py`, `Box`, `fakes.py`, `human.py`, `test_human.py`, `Ctx`, `FakeRoute`, `ActTab`, `test_discovery_to_replay.py`?**
  _High betweenness centrality (0.052) - this node is a cross-community bridge._
- **Why does `Ctx` connect `Ctx` to `FakePage`, `replay/wiring.py`, `test_act.py`, `test_replay_inputs.py`, `middleware.py`, `DiscoveryRun`, `test_replay_rescue.py`, `test_replay_handback.py`, `config.py`, `ReplayConfig`, `test_replay_table.py`, `make_replay_ctx`, `test_replay_steps.py`, `replay/context.py`, `discovery/wiring.py`, `DiscoveryConfig`, `ClearPage`, `Session`, `Look`, `FakeTab`, `_Request`, `HeldPage`, `ScriptedControl`, `GateControl`, `act.py`, `fakes.py`, `Route`, `test_goal.py`, `human.py`, `test_human.py`, `FakeRoute`, `discovery/evidence.py`, `FakePage`, `ActTab`?**
  _High betweenness centrality (0.047) - this node is a cross-community bridge._
- **Why does `BrowserConfig` connect `BrowserConfig` to `cli.py`, `FakePage`, `test_dropdown.py`, `test_replay_handback.py`, `config.py`, `make_replay_ctx`, `test_replay_steps.py`, `RefCounter`, `replay/context.py`, `cua/evidence.py`, `DiscoveryConfig`, `test_takeover_loop.py`, `test_extension.py`, `Session`, `Capability`, `FakeTab`, `test_screenshot.py`, `_Request`, `Box`, `fakes.py`, `test_capability.py`, `test_session.py`, `Ctx`, `FakeRoute`, `load_capability`, `FakePage`, `ActTab`, `test_discovery_to_replay.py`?**
  _High betweenness centrality (0.039) - this node is a cross-community bridge._
- **Are the 27 inferred relationships involving `Look` (e.g. with `Ctx` and `DiscoveryRun`) actually correct?**
  _`Look` has 27 INFERRED edges - model-reasoned connections that need verification._
- **Are the 59 inferred relationships involving `Ctx` (e.g. with `LatestScreenshotOnly` and `NoopAnthropicPromptCachingMiddleware`) actually correct?**
  _`Ctx` has 59 INFERRED edges - model-reasoned connections that need verification._
- **Are the 36 inferred relationships involving `BrowserConfig` (e.g. with `Session` and `Answerable`) actually correct?**
  _`BrowserConfig` has 36 INFERRED edges - model-reasoned connections that need verification._
- **Are the 30 inferred relationships involving `ReplayConfig` (e.g. with `Ctx` and `_Request`) actually correct?**
  _`ReplayConfig` has 30 INFERRED edges - model-reasoned connections that need verification._