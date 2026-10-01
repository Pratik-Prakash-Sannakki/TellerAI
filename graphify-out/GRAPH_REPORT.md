# Graph Report - BankerAgent  (2026-10-01)

## Corpus Check
- 225 files · ~264,445 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 2605 nodes · 7390 edges · 115 communities (104 shown, 11 thin omitted)
- Extraction: 93% EXTRACTED · 7% INFERRED · 0% AMBIGUOUS · INFERRED: 504 edges (avg confidence: 0.62)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `918a609d`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- cli.py
- FakeRoute
- Productionize Plan: notebooks → `src/cua/` package
- test_act.py
- Evidence README
- agent/build.py
- vision/__init__.py
- test_replay_inputs.py
- test_input.py
- where
- test_dropdown.py
- save_discovery_evidence / save_replay_evidence (D92)
- Replay decisions
- Five Error Demos (D30)
- langchain_typesafe
- langchain_typesafe_experimental_middleware
- discovery/run.py
- ReplayResult
- test_replay_engine.py
- test_replay_rescue.py
- test_llm.py
- test_replay_handback.py
- test_recorder_reads.py
- request.py
- test_replay_wiring.py
- recorder/__init__.py
- steps.py
- test_table.py
- integration/conftest.py
- test_snapshots.py
- test_replay_table.py
- redact.py
- pytest
- build_capability
- make_replay_ctx
- safety/__init__.py
- CLAUDE.md (project instructions)
- test_replay_steps.py
- look.py
- manifest.json
- langchain_tools
- test_recorder_runs.py
- config.py
- test_read_helpers.py
- BrowserConfig
- human.py
- FakeTab
- discovery/wiring.py
- locate
- test_send_guard.py
- test_control_window.py
- cua.vision
- test_takeover_loop.py
- helpers.py
- Session
- RefCounter
- ocr.py
- Look
- test_extension.py
- choose_option_at_point
- SendGuard
- langgraph_types
- act.py
- Discovery decisions
- 2. Each box, with an example
- cua/__init__.py
- ControlWindow
- 2. Components
- Ctx
- Pure-Visual Discovery Notebook: Build Plan
- test_spot_changed.py
- SiteLock
- test_saved_artifacts.py
- SiteProfile
- engine.py
- loader.py
- .awrap_model_call
- Box
- test_session.py
- test_prompt.py
- copy
- build_tools
- cua
- replay/evidence.py
- cua.schema
- mismatch.py
- run_goal
- fakes.py
- test_routing.py
- test_human.py
- interface-ai-cua
- cua.browser
- cua.handoff
- cua.safety
- cua.discovery
- cua.discovery.recorder
- cua.replay
- schema/__init__.py
- test_evidence.py
- make_ctx
- test_screenshot.py
- Replay notebook plan
- nav.py
- test_dropdowns.py
- load_capability
- re
- ReplayConfig
- discovery/evidence.py
- routing.py
- background.js
- replay/wiring.py
- test_middleware.py
- typing
- cua.discovery.agent
- test_capability.py

## God Nodes (most connected - your core abstractions)
1. `Look` - 116 edges
2. `BrowserConfig` - 82 edges
3. `Ctx` - 81 edges
4. `make_ctx()` - 78 edges
5. `ReplayConfig` - 70 edges
6. `build_capability()` - 64 edges
7. `Element` - 63 edges
8. `make_replay_ctx()` - 60 edges
9. `Box` - 53 edges
10. `_meta()` - 53 edges

## Surprising Connections (you probably didn't know these)
- `test_the_login_click_before_a_menu_link_is_kept()` --calls--> `step_events()`  [INFERRED]
  tests/unit/discovery/recorder/test_recorder_runs.py → src/cua/discovery/recorder/events.py
- `test_typed_ok_words_tolerant_digits_exact()` --calls--> `typed_ok()`  [INFERRED]
  tests/unit/replay/test_locate.py → src/cua/replay/locate.py
- `test_anchor_label_matches_ocr_merged_with_a_value()` --calls--> `same_label()`  [INFERRED]
  tests/unit/replay/test_locate.py → src/cua/replay/locate.py
- `test_a_target_needs_a_findable_rung()` --calls--> `Target`  [INFERRED]
  tests/unit/schema/test_capability.py → src/cua/schema/capability.py
- `test_an_old_select_without_an_index_still_loads()` --calls--> `Select`  [INFERRED]
  tests/unit/discovery/recorder/test_recorder_reads.py → src/cua/schema/capability.py

## Import Cycles
- 3-file cycle: `src/cua/discovery/tools/__init__.py -> src/cua/discovery/tools/human.py -> src/cua/discovery/tools/observe.py -> src/cua/discovery/tools/__init__.py`
- 3-file cycle: `src/cua/discovery/tools/guard.py -> src/cua/discovery/tools/human.py -> src/cua/discovery/tools/observe.py -> src/cua/discovery/tools/guard.py`
- 3-file cycle: `src/cua/discovery/tools/__init__.py -> src/cua/discovery/tools/nav.py -> src/cua/discovery/tools/guard.py -> src/cua/discovery/tools/__init__.py`
- 3-file cycle: `src/cua/discovery/tools/__init__.py -> src/cua/discovery/tools/nav.py -> src/cua/discovery/tools/observe.py -> src/cua/discovery/tools/__init__.py`
- 3-file cycle: `src/cua/discovery/tools/__init__.py -> src/cua/discovery/tools/read.py -> src/cua/discovery/tools/guard.py -> src/cua/discovery/tools/__init__.py`
- 3-file cycle: `src/cua/discovery/tools/__init__.py -> src/cua/discovery/tools/act.py -> src/cua/discovery/tools/guard.py -> src/cua/discovery/tools/__init__.py`
- 3-file cycle: `src/cua/discovery/tools/__init__.py -> src/cua/discovery/tools/act.py -> src/cua/discovery/tools/observe.py -> src/cua/discovery/tools/__init__.py`
- 4-file cycle: `src/cua/discovery/tools/__init__.py -> src/cua/discovery/tools/act.py -> src/cua/discovery/tools/human.py -> src/cua/discovery/tools/observe.py -> src/cua/discovery/tools/__init__.py`
- 4-file cycle: `src/cua/discovery/tools/__init__.py -> src/cua/discovery/tools/human.py -> src/cua/discovery/tools/observe.py -> src/cua/discovery/tools/guard.py -> src/cua/discovery/tools/__init__.py`
- 4-file cycle: `src/cua/discovery/tools/__init__.py -> src/cua/discovery/tools/nav.py -> src/cua/discovery/tools/observe.py -> src/cua/discovery/tools/guard.py -> src/cua/discovery/tools/__init__.py`
- 4-file cycle: `src/cua/discovery/tools/__init__.py -> src/cua/discovery/tools/act.py -> src/cua/discovery/tools/observe.py -> src/cua/discovery/tools/guard.py -> src/cua/discovery/tools/__init__.py`
- 5-file cycle: `src/cua/discovery/tools/__init__.py -> src/cua/discovery/tools/act.py -> src/cua/discovery/tools/guard.py -> src/cua/discovery/tools/human.py -> src/cua/discovery/tools/observe.py -> src/cua/discovery/tools/__init__.py`
- 5-file cycle: `src/cua/discovery/tools/__init__.py -> src/cua/discovery/tools/nav.py -> src/cua/discovery/tools/guard.py -> src/cua/discovery/tools/human.py -> src/cua/discovery/tools/observe.py -> src/cua/discovery/tools/__init__.py`
- 5-file cycle: `src/cua/discovery/tools/__init__.py -> src/cua/discovery/tools/read.py -> src/cua/discovery/tools/guard.py -> src/cua/discovery/tools/human.py -> src/cua/discovery/tools/observe.py -> src/cua/discovery/tools/__init__.py`
- 5-file cycle: `src/cua/discovery/tools/__init__.py -> src/cua/discovery/tools/act.py -> src/cua/discovery/tools/human.py -> src/cua/discovery/tools/observe.py -> src/cua/discovery/tools/guard.py -> src/cua/discovery/tools/__init__.py`

## Communities (115 total, 11 thin omitted)

### Community 0 - "cli.py"
Cohesion: 0.18
Nodes (18): argparse, Namespace, _close(), default_site(), discover(), main(), parse_args(), parse_inputs() (+10 more)

### Community 1 - "FakeRoute"
Cohesion: 0.09
Nodes (13): FakeControl, FakePage, FakeRoute, A fake discovery/replay ``CONTROL`` surface (what ``ControlWindow`` presents).…, The handful of ``playwright.async_api.Request`` fields the project's code reads., A fake ``playwright.async_api.Route``: records every…, A fake ``playwright.async_api.Page``. Every awaited method is recorded in…, _Request (+5 more)

### Community 2 - "Productionize Plan: notebooks → `src/cua/` package"
Cohesion: 0.12
Nodes (16): 10. Line-count offenders (today), 1. Package tree, 2. De-duplication (checked by AST diff of both notebooks), 3. State: globals → explicit objects, 4. Async and typing, 5. Notebooks after the move, 6. Tests, 7. ML-engineering practices (kept small) (+8 more)

### Community 3 - "test_act.py"
Cohesion: 0.07
Nodes (74): Items, (value, pattern) for an extract: the whole box when it is exactly the type,…, value_in_box(), make_look(), A look whose elements are numbered 1.. in order (ref, text, box)., Driven, _head(), _helped() (+66 more)

### Community 5 - "agent/build.py"
Cohesion: 0.12
Nodes (20): CompiledStateGraph, deepagents, Handler, langchain_agents_middleware, langgraph_checkpoint_memory, build_agent(), BaseChatModel, Ctx (+12 more)

### Community 6 - "vision/__init__.py"
Cohesion: 0.16
Nodes (21): Pixels -> text: screenshots, OCR, canvas math, crops, and the shared table…, append_rows(), cell_shape(), col_of(), column_spans(), like_rows(), The shared OCR table reader: discovery and replay use it to find a table's…, A table's end: a line that no longer looks like its rows (a footer, a menu, a… (+13 more)

### Community 7 - "test_replay_inputs.py"
Cohesion: 0.14
Nodes (29): select(), type_(), _cap(), ClearPage, env(), FakeForm, FakePage, asyncio (+21 more)

### Community 8 - "test_input.py"
Cohesion: 0.12
Nodes (22): act(), into_box(), Lock, Page, Session, Step, Unlock the site tab, run our own input steps, relock, settle, take a new look., Click the box, clear what is in it, type. Retries replace instead of doubling… (+14 more)

### Community 9 - "where"
Cohesion: 0.16
Nodes (14): choose_option(), crop(), Crop around the target, every other text blanked (sized to the current canvas)., Select the first option containing this text in the dropdown at (or next to)…, select_option's body once the option is the agent's to pick: choose it, log its…, _selected(), log_sent_dropdowns(), Ctx (+6 more)

### Community 10 - "test_dropdown.py"
Cohesion: 0.08
Nodes (33): BaseException, list_options(), Dropdown, Page, Every option of the dropdown at this page point ([] if it is not a dropdown).…, The page's dropdowns, read BEFORE an action (never while guard_send holds a…, read_dropdowns(), IndexPage (+25 more)

### Community 12 - "Replay decisions"
Cohesion: 0.08
Nodes (23): R10: where the compile step lives — DECIDED, R11: why compile, if `response_format` exists? — PROPOSED, R12: what each step type compiles to — PROPOSED, R13: target schema — PROPOSED, R14: what rung 2 needs that discovery doesn't record — DONE, R15: auto-approve at replay — PROPOSED, R16: dead ends and retries at compile — PROPOSED, R17: replay result statuses — PROPOSED (+15 more)

### Community 16 - "discovery/run.py"
Cohesion: 0.13
Nodes (19): Saved, DiscoveryRun, DiscoveryRun: one discovery run's working state (was the notebook's…, What the human gave: the goal and every answer (the send guard's mismatch text)., Every value typed, entered, given or sent this run, plus the secrets (in memory…, Every saved text, table cells included (evidence masking only)., Banking: values live only for the run. Keep the log (labels only), drop the…, run_values() (+11 more)

### Community 17 - "ReplayResult"
Cohesion: 0.06
Nodes (52): ReplayResult, Path, write_cap(), test_partial_label_when_not_success(), _all_text(), fake_ocr(), _png(), Ctx (+44 more)

### Community 18 - "test_replay_engine.py"
Cohesion: 0.21
Nodes (41): cap(), click(), extract(), _finish(), _login_cap(), _no_snap(), _pcap(), asyncio (+33 more)

### Community 19 - "test_replay_rescue.py"
Cohesion: 0.06
Nodes (44): The guard keeps its own reference to the control window: swap both., set_control(), DoneWhileSending, _env(), _fail_clicks(), FormRoute, Frame, GateControl (+36 more)

### Community 20 - "test_llm.py"
Cohesion: 0.18
Nodes (13): _clean_env(), CaptureFixture, fixture, MonkeyPatch, Offline tests for `cua.llm.make_chat_model` (Iliad gateway). No network, no…, test_ca_bundle_passthrough(), test_existing_ssl_cert_file_wins(), test_fallback_to_anthropic_key() (+5 more)

### Community 21 - "test_replay_handback.py"
Cohesion: 0.14
Nodes (22): FakePage, _bctx(), Ext, Human, PanelDone, asyncio, Ctx, parametrize (+14 more)

### Community 22 - "test_recorder_reads.py"
Cohesion: 0.09
Nodes (27): flag_leaks(), input_name(), Mark (never store) an event whose label, anchor, own text, hint or input name…, _FakeModel, asyncio, Stands in for a LangChain chat model: no network, records the prompt., asyncio, parametrize (+19 more)

### Community 23 - "request.py"
Cohesion: 0.13
Nodes (22): functools, json, JsonObj, Which hosts the browser may reach (D15). The allowlist itself lives in the site…, _flat(), _json(), What a held request sends, and the same request rebuilt with edited values.…, Every value a request sends, from its query, a form body, or a JSON body… (+14 more)

### Community 24 - "test_replay_wiring.py"
Cohesion: 0.08
Nodes (24): Working values for one run. Replaced by a new one in ``replay``'s ``finally``…, What the mismatch check compares a send against (SendState)., ReplayRun, attach(), Session, Wire replay onto an open session and return its Ctx., _fake_session(), asyncio (+16 more)

### Community 25 - "recorder/__init__.py"
Cohesion: 0.10
Nodes (40): output(), ``build_capability``'s refusals, unchanged: a leaked value, a blind dropdown,…, _refuse(), used_inputs(), checkpoint(), The capability's checkpoint: the text replay must see to call the run a…, C: after a send, the page's own response proves success (the agent's proof only…, field_area() (+32 more)

### Community 26 - "steps.py"
Cohesion: 0.08
Nodes (53): Point, JsonValue, Step, Returns the evidence (3.6): screenshots at start and hand-back, page and send…, rescue(), changed(), choose_option(), do_click() (+45 more)

### Community 27 - "test_table.py"
Cohesion: 0.06
Nodes (51): AST, Call, Module, _bind(), _code_cells(), _markdown(), _offline_namespace(), parametrize (+43 more)

### Community 29 - "test_snapshots.py"
Cohesion: 0.40
Nodes (4): parametrize, Path, The frozen notebook snapshots the parity tests read must never drift (see…, test_snapshot_is_unchanged()

### Community 30 - "test_replay_table.py"
Cohesion: 0.23
Nodes (17): _cap(), _defs(), Page, asyncio, Ctx, MonkeyPatch, Path, do_extract_table: find the header by its label, read the rows with discovery's… (+9 more)

### Community 31 - "redact.py"
Cohesion: 0.10
Nodes (32): Pattern, mask_png(), _num(), OcrFn, Value masking: ``norm``, ``is_sensitive``, ``hide_secrets``, ``redactor``,…, text -> text with every value masked. Numbers match however they are written…, Black out every OCR box whose text holds a run value. A clean image is written…, redactor() (+24 more)

### Community 32 - "pytest"
Cohesion: 0.29
Nodes (6): pytest, _fake_llm_keys(), fixture, MonkeyPatch, Suite-wide: never let a real LLM key from `.env` reach a test (cua.config loads…, A fake Iliad key so code that builds a chat model works offline; no real key is…

### Community 33 - "build_capability"
Cohesion: 0.08
Nodes (63): build_capability(), Steps, inputs and secrets come from the log only. The model's text cannot fail…, crops_for(), Path, save_artifact(), fixture, MonkeyPatch, saved() (+55 more)

### Community 34 - "make_replay_ctx"
Cohesion: 0.18
Nodes (24): make_replay_ctx(), A real Ctx (real SendGuard, real ReplayRun) over a fake page/control/lock.…, _extract(), _notebook_assign(), _pcap(), asyncio, Ctx, parametrize (+16 more)

### Community 35 - "safety/__init__.py"
Cohesion: 0.12
Nodes (13): Safety: what may leave the tab (hosts, the two send gates) and keeping values…, Protocol, The fields of a ``playwright.async_api.Request`` the guard reads., Request, ControlLike, GuardOptions, LookLike, Protocol (+5 more)

### Community 36 - "CLAUDE.md (project instructions)"
Cohesion: 0.12
Nodes (19): CLAUDE.md (project instructions), D101: labeled_value refuses a table-header resolution (general fix), D102: label_header/value_header flags ported into agent.py + cli.py capture path, D92: Evidence Capture Helpers (save_discovery_evidence/save_replay_evidence), D93: Pre-existing 02_artifact_schema.py IndexError bug, D95: Missing create_deep_agent import found live in BROWSER 12, D96: build_agent() goal_text vs given_text field-name bug, D97: cua replay --login flag + repeated Balance header trap (+11 more)

### Community 37 - "test_replay_steps.py"
Cohesion: 0.08
Nodes (39): mk_look(), navigate(), _click_env(), _form_png(), GotoPage, _judge(), Page, asyncio (+31 more)

### Community 38 - "look.py"
Cohesion: 0.09
Nodes (32): Our own input into the locked site tab: ``act`` (unlock, run steps, relock,…, canvas_size(), NDArray, uint8, Canvas-pixel <-> page-point mapping: any window size or pixel density maps to…, Fit the screenshot inside the canvas. Returns it and canvas-pixel -> page-point…, The size of the image the model is looking at right now., to_canvas() (+24 more)

### Community 39 - "manifest.json"
Cohesion: 0.11
Nodes (18): action, default_icon, default_title, background, service_worker, 128, 16, 32 (+10 more)

### Community 41 - "test_recorder_runs.py"
Cohesion: 0.15
Nodes (21): _click(), _clicks(), _go(), _names(), _nav(), _noop_click(), _paths(), Recorder behaviour pinned by live runs: detours, 404s, login clicks kept, no-op… (+13 more)

### Community 42 - "config.py"
Cohesion: 0.13
Nodes (14): dotenv, pathlib, _find_root(), OutcomeRule, _outcomes(), Path, Shared configuration: the site profile, browser/discovery/replay settings, and…, The nearest folder at or above `start` that has a ``configs/`` folder. (+6 more)

### Community 43 - "test_read_helpers.py"
Cohesion: 0.43
Nodes (6): _look(), where / label_near / spot / page_texts: a point's label in words, never a…, Live bug: 'From account #' dropdown showing '74838' was saved as input…, test_a_dropdowns_own_number_is_never_its_label(), test_page_texts_and_headings_are_words_without_run_values(), test_where_records_label_box_ordinal_offset_but_not_the_box_contents()

### Community 44 - "BrowserConfig"
Cohesion: 0.16
Nodes (14): The response to a send lands after the human's approval, not after the click:…, wait_for_change(), BrowserConfig, Settings shared by discovery and replay (the same page size at both, Q10)., Path, Discovery's saved artifact runs in replay unchanged: build -> save -> load ->…, test_crop_paths_resolve_to_saved_files(), test_rung2_offset_hits_the_point_discovery_acted_on() (+6 more)

### Community 45 - "human.py"
Cohesion: 0.16
Nodes (23): Field, _enter(), human_fills(), human_help(), _make_ask_human(), _make_finish(), make_human_tools(), _make_request_missing_values() (+15 more)

### Community 46 - "FakeTab"
Cohesion: 0.12
Nodes (3): FakeTab, SimpleNamespace, A fake site or control tab with the Playwright calls discovery's wiring and…

### Community 47 - "discovery/wiring.py"
Cohesion: 0.12
Nodes (41): DiscoveryConfig, Discovery-only settings., Discovery: an LLM agent learns a task once and the recorder saves it as a…, attach(), build_ctx(), _count_nav(), _hooks(), new_run() (+33 more)

### Community 48 - "locate"
Cohesion: 0.21
Nodes (21): locate(), Path, Target, (point, rung) from the first rung that hits, or None., _dup_target(), _look(), Path, Target (+13 more)

### Community 49 - "test_send_guard.py"
Cohesion: 0.16
Nodes (23): Side-specific steps, each at the exact point its notebook ran it. on_request:…, SendHooks, Control, _new(), _no_dropdowns(), _old(), _play(), parametrize (+15 more)

### Community 50 - "test_control_window.py"
Cohesion: 0.21
Nodes (23): Factory, SIDES, FakeWin, asyncio, parametrize, ControlWindow: one class, both sides' behaviour. Ported from…, Discovery calls _front inside try (the question is removed on failure); replay…, Regression: a gate during a take-over must win, then hand the take-over back… (+15 more)

### Community 51 - "cua.vision"
Cohesion: 0.50
Nodes (3): cua.vision, Read order, What may NOT go here

### Community 52 - "test_takeover_loop.py"
Cohesion: 0.12
Nodes (27): replay_control(), Asker, hand_back(), Future, Lock, Protocol, The shared take-over loop pieces. Each side's own take-over stays with that…, Done on the toolbar button or in the take-over panel hands back. No reminders… (+19 more)

### Community 53 - "helpers.py"
Cohesion: 0.16
Nodes (12): FakeLock, Ctx, Replay test helpers: ``make_replay_ctx`` (a real Ctx on fakes), ``mk_look``,…, SiteLock stand-in: open() unlocks for the block., ``take_look`` always returns this look., screen(), set_shoot(), AskStop (+4 more)

### Community 54 - "Session"
Cohesion: 0.17
Nodes (17): BrowserContext, Playwright, Playwright, no decisions: the open session, the site lock, our own input,…, _alive(), check_viewport(), _extension(), handback_dir(), _launch() (+9 more)

### Community 55 - "RefCounter"
Cohesion: 0.14
Nodes (19): number(), Fresh element refs for one run. Refs grow for the whole run and are never…, Reading order (rows top to bottom, then left to right), fresh refs., RefCounter, sys, The page heading 'Accounts Overview' sits above the menu link with the same…, test_the_menu_links_ordinal_is_counted_on_its_own_look_in_reading_order(), number()'s reading order and ref continuity; ocr_engine() built lazily, never… (+11 more)

### Community 56 - "ocr.py"
Cohesion: 0.33
Nodes (8): RapidOCR, draw_numbered(), ocr(), ocr_engine(), NDArray, uint8, The shared RapidOCR engine, OCR itself, numbering and the numbered-box overlay.…, The RapidOCR engine, built once per process. rapidocr is imported here only, so…

### Community 57 - "Look"
Cohesion: 0.10
Nodes (44): Cols, _columns(), clean_label(), column_header(), headings(), is_header(), is_word(), merged_label() (+36 more)

### Community 58 - "test_extension.py"
Cohesion: 0.10
Nodes (32): playwright_async_api, _in_control(), The take-over itself: badge YOU, unlock the site, wait for Done (panel or…, _takeover_note(), Answerable, button_clicked(), ext_call(), Extension (+24 more)

### Community 59 - "choose_option_at_point"
Cohesion: 0.38
Nodes (7): Confirm, LookFn, choose_option_at_index(), choose_option_at_point(), Session, Select the first option containing this text in the dropdown at (or next to)…, Select this exact live option in the Nth <select> (``index``), else the one at…

### Community 60 - "SendGuard"
Cohesion: 0.17
Nodes (7): pretty(), address.zipCode' -> 'Address zip code' (for the human; the key itself is kept)., Request, ``await guard(route)`` is the route handler. ``guard.lock`` is the send gate:…, Gate 1: Approve, or Edit = back to the form with every value, then again.…, RouteLike, SendGuard

### Community 62 - "act.py"
Cohesion: 0.13
Nodes (34): P, landed(), _landing(), make_act_tools(), _make_click(), _make_select_option(), _make_type_secret(), _make_type_text() (+26 more)

### Community 63 - "Discovery decisions"
Cohesion: 0.08
Nodes (24): Base decisions, Cuts, Discovery decisions, Q10: window size and zoom — DECIDED, Q11: notebook format — DECIDED, Q12: dropdowns — DECIDED, Q13: scrolling — DECIDED, Q14: private data in saved pictures — DECIDED (+16 more)

### Community 64 - "2. Each box, with an example"
Cohesion: 0.12
Nodes (15): 1. Diagram, 2. Each box, with an example, 3. All tools, 4. Step by step: one discovery run, 5. Notes, Browser (Playwright), Control window and site lock (Q-A), Discovery architecture (+7 more)

### Community 65 - "cua/__init__.py"
Cohesion: 0.33
Nodes (3): cua: shared config and the LLM model factory (Iliad gateway) for the pure-…, host_allowed: only the site's own hosts (D15); about:blank always., test_only_allowed_hosts_and_blank()

### Community 66 - "ControlWindow"
Cohesion: 0.11
Nodes (19): Question, ControlWindow, discovery_control(), _img(), Protocol, ControlWindow: our own "Agent control" tab, the only place a human answers.…, Answers the question on top. Closing the window (None) answers every one: fail…, Answers the newest open question of this mode, wherever it sits on the stack. (+11 more)

### Community 67 - "2. Components"
Cohesion: 0.12
Nodes (15): 1. Diagram, 2. Components, 3. Step types, 4. Worked example: ParaBank login + read balance, 5. Notes, Actor, Artifact (made by discovery, not replay), Browser setup (+7 more)

### Community 68 - "Ctx"
Cohesion: 0.11
Nodes (21): canvas(), _count_start(), Ctx, into_box(), list_options(), Page, Step, Ctx: what every discovery tool is given, plus the page wrappers the tools… (+13 more)

### Community 69 - "Pure-Visual Discovery Notebook: Build Plan"
Cohesion: 0.09
Nodes (22): 10. Open risks, 1. Global constraints (every task must follow these), 2. Review focus (inputs no spec line covers, but likely to bite), 3. What already exists (reuse, or its visual version), 3a. How the agent is built today (`agent.ipynb` STEP 4, `src/cua/agent.py`), 3b. Existing handoff rules: when a human is called in, 3c. Existing tools → the new tools, 4. New dependencies (checked on PyPI, 2026-09-28) (+14 more)

### Community 70 - "test_spot_changed.py"
Cohesion: 0.50
Nodes (4): _look(), ndarray, spot_changed: password dots are pixels, not OCR text. Ported from…, test_dots_count_as_change_and_blank_does_not()

### Community 71 - "SiteLock"
Cohesion: 0.16
Nodes (12): CdpSender, Protocol, SiteLock: the site tab ignores all real input (CDP…, The one method of a Playwright ``CDPSession`` the lock uses., The site tab ignores all real input (CDP). Lifted only around our own action or…, SiteLock, FakeCdp, asyncio (+4 more)

### Community 73 - "test_saved_artifacts.py"
Cohesion: 0.31
Nodes (7): MonkeyPatch, parametrize, Path, Every capability saved in the top-level artifacts/ folder (Decision 6) loads in…, test_a_saved_artifact_loads_in_replay(), test_a_saved_artifact_round_trips(), test_the_old_artifacts_folder_is_gone()

### Community 74 - "SiteProfile"
Cohesion: 0.09
Nodes (28): load_site(), Read and validate ``configs/<name>.yaml`` (root defaults to the repo root)., Look up a secret by NAME. Raises on an unknown name or an empty/missing value.…, Secret name -> value from `.env` ("" when unset), as the notebook's SECRETS., Everything site-specific, loaded from ``configs/<name>.yaml``. Secrets: env…, Secret name -> env var name., resolve_secret(), secret_values() (+20 more)

### Community 75 - "engine.py"
Cohesion: 0.14
Nodes (39): Drift, _cleanup_step(), error_page(), finish(), is_cleanup(), judge(), login_came_back(), login_steps() (+31 more)

### Community 76 - "loader.py"
Cohesion: 0.11
Nodes (21): Exception, ask_inputs(), ask_option(), _ask_rows(), given_inputs(), Ctx, Loading a saved capability (schema v2) and the inputs it needs. Moved unchanged…, Every `{{input}}` the steps use, in step order, once each. (+13 more)

### Community 77 - ".awrap_model_call"
Cohesion: 0.13
Nodes (13): Classifier, confidence_gate(), job_tool_names(), page_name(), AsyncHandler, ModelRequest, ModelResponse, Protocol (+5 more)

### Community 80 - "Box"
Cohesion: 0.10
Nodes (27): crop_box(), cut_crop(), Crops around one point: find the element there, crop around it, read text near…, Crop around the target, with every other piece of text blanked out., Pixels around the point changed. Catches password dots that OCR cannot read., read_near(), screens_same(), spot_changed() (+19 more)

### Community 81 - "test_session.py"
Cohesion: 0.24
Nodes (11): LivePage, _png(), asyncio, MonkeyPatch, Path, open_session reuses a live session (a notebook re-run must not leak a browser),…, _session(), test_a_live_existing_session_is_returned_unchanged() (+3 more)

### Community 82 - "test_prompt.py"
Cohesion: 0.13
Nodes (9): The discovery agent: system prompt, middleware, optional TypeSafe routing, and…, The discovery agent's system prompt, verbatim from…, _capture(), MonkeyPatch, build_agent: the notebook's create_deep_agent call, with routing appended only…, test_build_agent_wires_the_notebooks_agent(), test_routing_is_appended_after_the_notebooks_middleware(), test_the_page_path_is_read_live() (+1 more)

### Community 85 - "build_tools"
Cohesion: 0.16
Nodes (16): AsyncFunctionDef, inspect, build_tools(), BaseTool, Ctx, observe, click, type_text, type_secret, select_option, scroll, open_path,…, test_the_prompt_lists_every_tool(), _notebook_tools() (+8 more)

### Community 86 - "cua"
Cohesion: 0.50
Nodes (3): cua, Read order, Rules

### Community 87 - "replay/evidence.py"
Cohesion: 0.22
Nodes (12): _drift_lines(), masked_outputs(), Ctx, JsonValue, OcrFn, Path, Redact, One folder per replay run (spec 3.5, 6.3): summary, drift, failure, the final… (+4 more)

### Community 88 - "cua.schema"
Cohesion: 0.50
Nodes (3): cua.schema, Read order, What may NOT go here

### Community 90 - "mismatch.py"
Cohesion: 0.22
Nodes (13): dropdown_options(), mismatches(), _norm_num(), Dropdown, Values a send carries that the human never gave, and the dropdown choices to…, Numbers being sent that the human never gave, e.g. account 1450 vs 1400. Only…, For each key: the options of the page dropdown whose CURRENT value is exactly…, _hide() (+5 more)

### Community 92 - "run_goal"
Cohesion: 0.17
Nodes (15): Agent, Ctx, Protocol, What run_goal needs of the compiled deep agent., New run on a fresh thread; pass an earlier thread_id to resume it with a next…, run_goal(), _start(), FakeAgent (+7 more)

### Community 93 - "fakes.py"
Cohesion: 0.11
Nodes (22): ActTab, blank_png(), FakeInput, FakeLock, Shared offline fakes for the ported test suite (tests/unit, tests/integration).…, A fake ``cua.browser.SiteLock``: ``open()`` records unlock/lock, nothing else., A fake ``page.mouse`` / ``page.keyboard``: every call is recorded as ``(name,…, A site tab the act/nav tools drive: ``mouse``/``keyboard`` record into… (+14 more)

### Community 96 - "test_routing.py"
Cohesion: 0.21
Nodes (15): _choice(), FakeClassifier, FakeRequest, _names(), asyncio, CaptureFixture, MonkeyPatch, SimpleNamespace (+7 more)

### Community 98 - "test_human.py"
Cohesion: 0.15
Nodes (39): Q21: the one time the site unlocks for a human. What they did is kept as…, take_over(), _answer(), _badge(), _ctx(), _dirty(), entry(), Ext (+31 more)

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
Cohesion: 0.15
Nodes (32): BaseModel, model_validator, _navigate(), Step, Event log -> ``Capability``: steps, inputs, outputs and secrets come from the…, ``to_step``'s open_path branch, unchanged., The {{input}} names the steps use, in order. {{secret:x}} is not an input., step_inputs() (+24 more)

### Community 109 - "test_evidence.py"
Cohesion: 0.26
Nodes (16): _artifact(), masked(), fixture, MonkeyPatch, Path, save_evidence: one masked folder per run. No run value or secret is ever…, The OCR mask is tested in tests/unit/safety; here: that every PNG goes through…, _save() (+8 more)

### Community 110 - "make_ctx"
Cohesion: 0.15
Nodes (29): make_ctx(), Ctx, Session, A discovery ``Ctx`` over fakes, built like ``attach`` but with no page wiring., helped(), asyncio, fixture, MonkeyPatch (+21 more)

### Community 112 - "test_screenshot.py"
Cohesion: 0.27
Nodes (9): _png(), asyncio, MonkeyPatch, take_look: page calls on the loop, the CPU part (OCR, drawing, encoding) in one…, ShotPage, test_page_width_reads_the_window_width(), test_snap_look_gives_the_look_png_or_none_on_timeout(), test_snap_png_passes_the_timeout_and_gives_none_on_error() (+1 more)

### Community 113 - "Replay notebook plan"
Cohesion: 0.33
Nodes (5): Decisions made here (review), Open questions for the user, Replay notebook plan, Sections, Tasks

### Community 114 - "nav.py"
Cohesion: 0.14
Nodes (29): base64, act(), look(), Unlock the site tab, run our own input steps, relock, settle, take a new look., The only screenshot path; stores the look on the run., _press(), Result, type_text's body once the value is the agent's to type: type it, read the box… (+21 more)

### Community 117 - "test_dropdowns.py"
Cohesion: 0.15
Nodes (17): _approve(), HeldPage, _logged(), _no_crop_pixels(), asyncio, Ctx, fixture, MonkeyPatch (+9 more)

### Community 118 - "load_capability"
Cohesion: 0.19
Nodes (21): load_capability(), load_outcomes(), _missing_crops(), Path, The capability and the folder its crop paths are relative to., The capability's own `outcomes:` [{text, status, meaning}], else the site's…, fixture, MonkeyPatch (+13 more)

### Community 120 - "re"
Cohesion: 0.12
Nodes (20): re, config_hash(), git_sha(), JsonValue, Path, Evidence helpers shared by discovery and replay: masking a JSON-able tree,…, `git rev-parse HEAD`, or "unknown" (no git, not a repo, any failure)., sha256 of the repr of the frozen configs plus the site name. (+12 more)

### Community 121 - "ReplayConfig"
Cohesion: 0.12
Nodes (33): SameTextLike, Replay-only settings., ReplayConfig, Replay: runs a capability saved by discovery with plain code, no LLM (step 4:…, fill(), Put inputs into `{{name}}`. `{{secret:x}}` stays as it is: secrets go in only…, secret_name(), anchor_point() (+25 more)

### Community 123 - "discovery/evidence.py"
Cohesion: 0.18
Nodes (20): _copy_capability(), _events(), _folder(), Ctx, OcrFn, Path, Redact, One masked folder per discovery run: goal, answer, events, transcript, crops,… (+12 more)

### Community 125 - "routing.py"
Cohesion: 0.13
Nodes (22): ModelKind, ModuleType, os, build_routing_middleware(), _model_router(), AgentMiddleware, TypeSafe tool selection + model routing, restored (user, 2026-10-01;…, Haiku for a simple step, Sonnet otherwise (both through cua.llm). (+14 more)

### Community 131 - "replay/wiring.py"
Cohesion: 0.08
Nodes (28): dataclasses, Ctx, note_takeover_send(), Page, Request, Ctx: what every replay function takes first (session, run, settings, send…, R7: nothing kept. A fresh run, and the guard reads that one from now on., wipe() (+20 more)

### Community 132 - "test_middleware.py"
Cohesion: 0.29
Nodes (9): asyncio, SimpleNamespace, LatestScreenshotOnly keeps only the newest image in the model's context; the…, _req(), _shot(), test_async_call_trims_too(), test_noop_caching_passes_the_request_through(), test_only_last_image_survives() (+1 more)

### Community 134 - "typing"
Cohesion: 0.27
Nodes (7): bind_control(), ControlTab, Protocol, Bind the control tab to the current :class:`ControlWindow`, once per tab. A…, The Playwright calls binding makes on the control tab., Point the control tab's buttons and its close at ``control``. Re-run safe: the…, typing

### Community 141 - "cua.discovery.agent"
Cohesion: 0.50
Nodes (3): cua.discovery.agent, Read order, What may NOT go here

### Community 149 - "test_capability.py"
Cohesion: 0.11
Nodes (17): pydantic, _EventBase, The discovery event log entry: one tool call, as discovery's ``log()`` writes…, What a replay run returns: its Status, the Stop that ends a run early, and…, R17 run statuses. A member is a plain str, so ``Status.SUCCESS == "SUCCESS"``., Status, StrEnum, _data() (+9 more)

## Knowledge Gaps
- **159 isolated node(s):** `MODES`, `manifest_version`, `name`, `version`, `description` (+154 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **11 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Look` connect `Look` to `FakeRoute`, `test_act.py`, `vision/__init__.py`, `test_input.py`, `where`, `test_dropdown.py`, `discovery/run.py`, `test_replay_rescue.py`, `steps.py`, `make_replay_ctx`, `test_replay_steps.py`, `look.py`, `test_read_helpers.py`, `BrowserConfig`, `human.py`, `FakeTab`, `discovery/wiring.py`, `locate`, `helpers.py`, `Session`, `RefCounter`, `act.py`, `Ctx`, `test_spot_changed.py`, `Box`, `fakes.py`, `test_human.py`, `test_screenshot.py`, `nav.py`, `test_dropdowns.py`, `ReplayConfig`?**
  _High betweenness centrality (0.067) - this node is a cross-community bridge._
- **Why does `Ctx` connect `Ctx` to `FakeRoute`, `replay/wiring.py`, `test_act.py`, `agent/build.py`, `test_replay_inputs.py`, `where`, `discovery/run.py`, `test_replay_rescue.py`, `test_replay_handback.py`, `test_replay_wiring.py`, `test_replay_table.py`, `test_replay_steps.py`, `human.py`, `FakeTab`, `discovery/wiring.py`, `helpers.py`, `Session`, `Look`, `act.py`, `SiteProfile`, `run_goal`, `fakes.py`, `test_human.py`, `nav.py`, `test_dropdowns.py`, `discovery/evidence.py`?**
  _High betweenness centrality (0.055) - this node is a cross-community bridge._
- **Why does `BrowserConfig` connect `BrowserConfig` to `cli.py`, `FakeRoute`, `replay/wiring.py`, `test_input.py`, `test_dropdown.py`, `test_replay_handback.py`, `make_replay_ctx`, `test_replay_steps.py`, `look.py`, `config.py`, `FakeTab`, `discovery/wiring.py`, `test_takeover_loop.py`, `helpers.py`, `Session`, `test_extension.py`, `test_saved_artifacts.py`, `SiteProfile`, `loader.py`, `Box`, `test_session.py`, `fakes.py`, `test_screenshot.py`, `load_capability`, `re`?**
  _High betweenness centrality (0.048) - this node is a cross-community bridge._
- **Are the 26 inferred relationships involving `Look` (e.g. with `Ctx` and `DiscoveryRun`) actually correct?**
  _`Look` has 26 INFERRED edges - model-reasoned connections that need verification._
- **Are the 35 inferred relationships involving `BrowserConfig` (e.g. with `Session` and `Answerable`) actually correct?**
  _`BrowserConfig` has 35 INFERRED edges - model-reasoned connections that need verification._
- **Are the 54 inferred relationships involving `Ctx` (e.g. with `Session` and `DiscoveryConfig`) actually correct?**
  _`Ctx` has 54 INFERRED edges - model-reasoned connections that need verification._
- **Are the 30 inferred relationships involving `ReplayConfig` (e.g. with `Ctx` and `_Request`) actually correct?**
  _`ReplayConfig` has 30 INFERRED edges - model-reasoned connections that need verification._