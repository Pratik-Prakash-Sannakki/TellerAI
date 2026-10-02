# Graph Report - BankerAgent  (2026-10-01)

## Corpus Check
- 234 files · ~240,781 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 2855 nodes · 8234 edges · 125 communities (110 shown, 15 thin omitted)
- Extraction: 93% EXTRACTED · 7% INFERRED · 0% AMBIGUOUS · INFERRED: 553 edges (avg confidence: 0.63)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `564db51b`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- cli.py
- FakeRoute
- Productionize Plan: notebooks → `src/cua/` package
- test_act.py
- Evidence README
- test_read.py
- test_recorder_types.py
- test_replay_inputs.py
- test_input.py
- test_middleware.py
- test_dropdown.py
- save_discovery_evidence / save_replay_evidence (D92)
- Replay decisions
- Five Error Demos (D30)
- langchain_typesafe
- langchain_typesafe_experimental_middleware
- discovery/context.py
- test_cli.py
- test_replay_engine.py
- test_replay_rescue.py
- test_llm.py
- test_replay_handback.py
- SiteProfile
- test_recorder_runs.py
- locate.py
- recorder/__init__.py
- steps.py
- replay/evidence.py
- integration/conftest.py
- redact.py
- test_replay_table.py
- BrowserConfig
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
- ActTab
- replay/context.py
- test_shared_evidence.py
- mismatch.py
- test_table.py
- DiscoveryConfig
- ReplayConfig
- test_send_guard.py
- test_control_window.py
- cua.vision
- test_takeover_loop.py
- test_extension.py
- Session
- Look
- loader.py
- middleware.py
- FakeTab
- Trace
- ._record
- langgraph_types
- test_screenshot.py
- Discovery decisions
- 2. Each box, with an example
- request.py
- ControlWindow
- 2. Components
- HeldPage
- Pure-Visual Discovery Notebook: Build Plan
- ScriptedControl
- SiteLock
- .awrap_model_call
- ReplayResult
- _where
- Capability
- GateControl
- test_routing.py
- FakeWin
- _check_login_order
- value_in_box
- test_import_rules.py
- test_build.py
- copy
- Route
- test_prompt.py
- cua
- pytest
- cua.schema
- rescue
- Driven
- test_capability.py
- test_goal.py
- human.py
- test_value_types.py
- locate
- routing.py
- Element
- test_human.py
- interface-ai-cua
- cua.browser
- cua.handoff
- cua.safety
- cua.discovery
- cua.discovery.recorder
- cua.replay
- schema/__init__.py
- FakeInput
- Ctx
- test_evidence.py
- make_ctx
- is_sensitive
- _logged_arg_keys
- Replay notebook plan
- config.py
- test_dropdowns.py
- load_capability
- _FakeModel
- discovery/evidence.py
- fakes.py
- background.js
- replay/wiring.py
- test_saved_artifacts.py
- helpers.py
- cua.discovery.agent

## God Nodes (most connected - your core abstractions)
1. `Look` - 125 edges
2. `make_ctx()` - 96 edges
3. `Ctx` - 89 edges
4. `BrowserConfig` - 86 edges
5. `build_capability()` - 74 edges
6. `ReplayConfig` - 72 edges
7. `Element` - 63 edges
8. `make_replay_ctx()` - 63 edges
9. `_meta()` - 61 edges
10. `Capability` - 57 edges

## Surprising Connections (you probably didn't know these)
- `test_the_login_click_before_a_menu_link_is_kept()` --calls--> `step_events()`  [INFERRED]
  tests/unit/discovery/recorder/test_recorder_runs.py → src/cua/discovery/recorder/events.py
- `test_typed_ok_words_tolerant_digits_exact()` --calls--> `typed_ok()`  [INFERRED]
  tests/unit/replay/test_locate.py → src/cua/replay/locate.py
- `test_a_target_needs_a_findable_rung()` --calls--> `Target`  [INFERRED]
  tests/unit/schema/test_capability.py → src/cua/schema/capability.py
- `test_meta_is_loose()` --calls--> `CapabilityMeta`  [INFERRED]
  tests/unit/schema/test_capability.py → src/cua/schema/capability.py
- `test_stop_carries_its_fields()` --calls--> `Stop`  [INFERRED]
  tests/unit/schema/test_result.py → src/cua/schema/result.py

## Import Cycles
- 3-file cycle: `src/cua/discovery/tools/__init__.py -> src/cua/discovery/tools/human.py -> src/cua/discovery/tools/observe.py -> src/cua/discovery/tools/__init__.py`
- 3-file cycle: `src/cua/discovery/tools/__init__.py -> src/cua/discovery/tools/act.py -> src/cua/discovery/tools/observe.py -> src/cua/discovery/tools/__init__.py`
- 3-file cycle: `src/cua/discovery/tools/__init__.py -> src/cua/discovery/tools/nav.py -> src/cua/discovery/tools/observe.py -> src/cua/discovery/tools/__init__.py`
- 3-file cycle: `src/cua/discovery/tools/guard.py -> src/cua/discovery/tools/human.py -> src/cua/discovery/tools/observe.py -> src/cua/discovery/tools/guard.py`
- 3-file cycle: `src/cua/discovery/tools/__init__.py -> src/cua/discovery/tools/act.py -> src/cua/discovery/tools/guard.py -> src/cua/discovery/tools/__init__.py`
- 3-file cycle: `src/cua/discovery/tools/__init__.py -> src/cua/discovery/tools/nav.py -> src/cua/discovery/tools/guard.py -> src/cua/discovery/tools/__init__.py`
- 3-file cycle: `src/cua/discovery/tools/__init__.py -> src/cua/discovery/tools/read.py -> src/cua/discovery/tools/guard.py -> src/cua/discovery/tools/__init__.py`
- 4-file cycle: `src/cua/discovery/tools/__init__.py -> src/cua/discovery/tools/act.py -> src/cua/discovery/tools/human.py -> src/cua/discovery/tools/observe.py -> src/cua/discovery/tools/__init__.py`
- 4-file cycle: `src/cua/discovery/tools/__init__.py -> src/cua/discovery/tools/human.py -> src/cua/discovery/tools/observe.py -> src/cua/discovery/tools/guard.py -> src/cua/discovery/tools/__init__.py`
- 4-file cycle: `src/cua/discovery/tools/__init__.py -> src/cua/discovery/tools/act.py -> src/cua/discovery/tools/observe.py -> src/cua/discovery/tools/guard.py -> src/cua/discovery/tools/__init__.py`
- 4-file cycle: `src/cua/discovery/tools/__init__.py -> src/cua/discovery/tools/nav.py -> src/cua/discovery/tools/observe.py -> src/cua/discovery/tools/guard.py -> src/cua/discovery/tools/__init__.py`
- 5-file cycle: `src/cua/discovery/tools/__init__.py -> src/cua/discovery/tools/act.py -> src/cua/discovery/tools/guard.py -> src/cua/discovery/tools/human.py -> src/cua/discovery/tools/observe.py -> src/cua/discovery/tools/__init__.py`
- 5-file cycle: `src/cua/discovery/tools/__init__.py -> src/cua/discovery/tools/nav.py -> src/cua/discovery/tools/guard.py -> src/cua/discovery/tools/human.py -> src/cua/discovery/tools/observe.py -> src/cua/discovery/tools/__init__.py`
- 5-file cycle: `src/cua/discovery/tools/__init__.py -> src/cua/discovery/tools/read.py -> src/cua/discovery/tools/guard.py -> src/cua/discovery/tools/human.py -> src/cua/discovery/tools/observe.py -> src/cua/discovery/tools/__init__.py`
- 5-file cycle: `src/cua/discovery/tools/__init__.py -> src/cua/discovery/tools/act.py -> src/cua/discovery/tools/human.py -> src/cua/discovery/tools/observe.py -> src/cua/discovery/tools/guard.py -> src/cua/discovery/tools/__init__.py`

## Communities (125 total, 15 thin omitted)

### Community 0 - "cli.py"
Cohesion: 0.07
Nodes (53): argparse, Histogram, Namespace, _cap_name(), check_eval(), _close(), default_site(), discover() (+45 more)

### Community 1 - "FakeRoute"
Cohesion: 0.11
Nodes (11): FakeControl, FakePage, FakeRoute, A fake discovery/replay ``CONTROL`` surface (what ``ControlWindow`` presents).…, A fake ``playwright.async_api.Route``: records every…, A fake ``playwright.async_api.Page``. Every awaited method is recorded in…, asyncio, Tests for the shared offline fakes in tests/fakes.py (TDD: written before the… (+3 more)

### Community 2 - "Productionize Plan: notebooks → `src/cua/` package"
Cohesion: 0.12
Nodes (16): 10. Line-count offenders (today), 1. Package tree, 2. De-duplication (checked by AST diff of both notebooks), 3. State: globals → explicit objects, 4. Async and typing, 5. Notebooks after the move, 6. Tests, 7. ML-engineering practices (kept small) (+8 more)

### Community 3 - "test_act.py"
Cohesion: 0.21
Nodes (37): make_look(), A look whose elements are numbered 1.. in order (ref, text, box)., _head(), _helped(), asyncio, MonkeyPatch, parametrize, click / type_text / type_secret / select_option / scroll / open_path / observe:… (+29 more)

### Community 5 - "test_read.py"
Cohesion: 0.10
Nodes (37): Items, blank_png(), A plain PNG of this canvas size (canvas/crops decode the look's png)., _cell(), _extract_options(), _no_crop_pixels(), _options_ctx(), asyncio (+29 more)

### Community 6 - "test_recorder_types.py"
Cohesion: 0.12
Nodes (26): input_name(), event_shapes(), input_types(), pick_type(), Typed inputs: an input's type is inferred from the SHAPES of the values typed…, Every shape the whole value matches, in precedence order. Safe to log: names,…, One input's type from each of its values' shapes. Unknown shapes (None) ->…, input name -> the shapes of the value it took in this event (None: not logged). (+18 more)

### Community 7 - "test_replay_inputs.py"
Cohesion: 0.12
Nodes (34): select(), type_(), _cap(), ClearPage, env(), FakeForm, FakePage, asyncio (+26 more)

### Community 8 - "test_input.py"
Cohesion: 0.09
Nodes (21): into_box(), Page, Our own input into the locked site tab: ``act`` (unlock, run steps, relock,…, The response to a send lands after the human's approval, not after the click:…, Focus the site tab, click the box, clear what is in it, type. Retries replace…, wait_for_change(), to_page(), FakeBox (+13 more)

### Community 9 - "test_middleware.py"
Cohesion: 0.16
Nodes (22): AIMessage, Ctx, 3.5: keep the text the model wrote before its tool calls as ``ctx.run.why``…, RecordWhy, _answer(), asyncio, parametrize, SimpleNamespace (+14 more)

### Community 10 - "test_dropdown.py"
Cohesion: 0.07
Nodes (41): BaseException, Confirm, LookFn, playwright_async_api, choose_option_at_index(), choose_option_at_point(), list_options(), Dropdown (+33 more)

### Community 12 - "Replay decisions"
Cohesion: 0.08
Nodes (23): R10: where the compile step lives — DECIDED, R11: why compile, if `response_format` exists? — PROPOSED, R12: what each step type compiles to — PROPOSED, R13: target schema — PROPOSED, R14: what rung 2 needs that discovery doesn't record — DONE, R15: auto-approve at replay — PROPOSED, R16: dead ends and retries at compile — PROPOSED, R17: replay result statuses — PROPOSED (+15 more)

### Community 16 - "discovery/context.py"
Cohesion: 0.06
Nodes (46): dataclasses, Saved, The index (among the page's <select>s) of the native dropdown right under this…, select_under(), Ctx: what every discovery tool is given, plus the page wrappers the tools…, An evidence screenshot: short timeout, None on failure (never hangs on a held…, The current run (the one the send guard serves)., snap() (+38 more)

### Community 17 - "test_cli.py"
Cohesion: 0.13
Nodes (31): _cap_file(), _fake_session(), _patch_session(), CaptureFixture, MonkeyPatch, parametrize, Path, SimpleNamespace (+23 more)

### Community 18 - "test_replay_engine.py"
Cohesion: 0.18
Nodes (47): cap(), click(), extract(), AskStop, _finish(), _login_cap(), _no_snap(), _only() (+39 more)

### Community 19 - "test_replay_rescue.py"
Cohesion: 0.20
Nodes (27): The guard keeps its own reference to the control window: swap both., set_control(), _env(), _fail_clicks(), HangPage, HumanSimple, asyncio, MonkeyPatch (+19 more)

### Community 20 - "test_llm.py"
Cohesion: 0.20
Nodes (14): _clean_env(), _gateway(), fixture, MonkeyPatch, Offline tests for `cua.llm.make_chat_model`. No network, no real key. Default:…, test_ca_bundle_passthrough(), test_existing_ssl_cert_file_wins(), test_gateway_env_means_gateway() (+6 more)

### Community 21 - "test_replay_handback.py"
Cohesion: 0.13
Nodes (23): FakePage, _bctx(), Ext, Human, PanelDone, asyncio, Ctx, parametrize (+15 more)

### Community 22 - "SiteProfile"
Cohesion: 0.08
Nodes (35): load_site(), OutcomeRule, Read and validate ``configs/<name>.yaml`` (root defaults to the repo root)., Look up a secret by NAME. Raises on an unknown name or an empty/missing value.…, Secret name -> value from `.env` ("" when unset), as the notebook's SECRETS., R17: text seen after a step -> status. First match wins., Everything site-specific, loaded from ``configs/<name>.yaml``. Secrets: env…, Secret name -> env var name. (+27 more)

### Community 23 - "test_recorder_runs.py"
Cohesion: 0.14
Nodes (23): _click(), _clicks(), _go(), _names(), _nav(), _noop_click(), _paths(), Recorder behaviour pinned by live runs: detours, 404s, login clicks kept, no-op… (+15 more)

### Community 24 - "locate.py"
Cohesion: 0.11
Nodes (27): SameTextLike, Replay: runs a capability saved by discovery with plain code, no LLM (step 4:…, fill(), Put inputs into `{{name}}`. `{{secret:x}}` stays as it is: secrets go in only…, The first rule whose text (whole words, any case) appeared on screen with this…, secret_name(), seen_outcome(), anchor_point() (+19 more)

### Community 25 - "recorder/__init__.py"
Cohesion: 0.08
Nodes (51): check_savable(), Raise NotSaved before any model call when this run cannot become a capability., ``build_capability``'s refusals, unchanged: a leaked value, a blind dropdown,…, _refuse(), used_inputs(), checkpoint(), The capability's checkpoint: the text replay must see to call the run a…, C: after a send, the page's own response proves success (the agent's proof only… (+43 more)

### Community 26 - "steps.py"
Cohesion: 0.09
Nodes (49): Point, changed(), choose_option(), do_click(), do_extract(), do_extract_options(), do_extract_table(), do_navigate() (+41 more)

### Community 27 - "replay/evidence.py"
Cohesion: 0.13
Nodes (21): _clean(), _png(), OcrFn, Redact, _drift_lines(), masked_outputs(), Ctx, JsonValue (+13 more)

### Community 29 - "redact.py"
Cohesion: 0.10
Nodes (34): Pattern, re, hide_secrets(), mask_png(), _num(), OcrFn, Value masking: ``norm``, ``is_sensitive``, ``hide_secrets``, ``redactor``,…, text -> text with every value masked. Numbers match however they are written… (+26 more)

### Community 30 - "test_replay_table.py"
Cohesion: 0.21
Nodes (18): _cap(), _defs(), Page, asyncio, Ctx, MonkeyPatch, Path, do_extract_table: find the header by its label, read the rows with discovery's… (+10 more)

### Community 31 - "BrowserConfig"
Cohesion: 0.17
Nodes (15): BrowserConfig, Settings shared by discovery and replay (the same page size at both, Q10)., LivePage, _png(), asyncio, MonkeyPatch, Path, open_session reuses a live session (a notebook re-run must not leak a browser),… (+7 more)

### Community 32 - "test_notebooks.py"
Cohesion: 0.26
Nodes (16): Call, Module, _bind(), _code_cells(), _markdown(), _offline_namespace(), parametrize, Path (+8 more)

### Community 33 - "build_capability"
Cohesion: 0.07
Nodes (78): build_capability(), Steps, inputs and secrets come from the log only. The model's text cannot fail…, flag_leaks(), Mark (never store) an event whose label, anchor, own text, hint or input name…, crops_for(), Path, save_artifact(), fixture (+70 more)

### Community 34 - "make_replay_ctx"
Cohesion: 0.14
Nodes (29): make_replay_ctx(), A real Ctx (real SendGuard, real ReplayRun) over a fake page/control/lock.…, _extract(), _notebook_assign(), _options_cap(), OptionsPage, _pcap(), asyncio (+21 more)

### Community 35 - "test_replay_evidence.py"
Cohesion: 0.24
Nodes (20): Path, write_cap(), _all_text(), fake_ocr(), _png(), Ctx, fixture, Path (+12 more)

### Community 36 - "CLAUDE.md (project instructions)"
Cohesion: 0.12
Nodes (19): CLAUDE.md (project instructions), D101: labeled_value refuses a table-header resolution (general fix), D102: label_header/value_header flags ported into agent.py + cli.py capture path, D92: Evidence Capture Helpers (save_discovery_evidence/save_replay_evidence), D93: Pre-existing 02_artifact_schema.py IndexError bug, D95: Missing create_deep_agent import found live in BROWSER 12, D96: build_agent() goal_text vs given_text field-name bug, D97: cua replay --login flag + repeated Balance header trap (+11 more)

### Community 37 - "test_replay_steps.py"
Cohesion: 0.07
Nodes (45): Rung 2 anchors only. Discovery saves labels cleaned ('to account #'); live OCR…, same_label(), mk_look(), navigate(), test_anchor_label_matches_ocr_merged_with_a_value(), _click_env(), _form_png(), GotoPage (+37 more)

### Community 38 - "RefCounter"
Cohesion: 0.07
Nodes (41): RapidOCR, NDArray, uint8, Fit the screenshot inside the canvas. Returns it and canvas-pixel -> page-point…, to_canvas(), draw_numbered(), number(), ocr() (+33 more)

### Community 39 - "manifest.json"
Cohesion: 0.11
Nodes (18): action, default_icon, default_title, background, service_worker, 128, 16, 32 (+10 more)

### Community 41 - "safety/__init__.py"
Cohesion: 0.12
Nodes (13): Safety: what may leave the tab (hosts, the two send gates) and keeping values…, Protocol, The fields of a ``playwright.async_api.Request`` the guard reads., Request, ControlLike, GuardOptions, LookLike, Protocol (+5 more)

### Community 42 - "ActTab"
Cohesion: 0.22
Nodes (16): ActTab, A site tab the act/nav tools drive: ``mouse``/``keyboard`` record into…, A page script: recorded, answered by ``answer`` (default: no dropdown anywhere)., _ctx(), asyncio, Ctx, MonkeyPatch, finish_business_outcome / request_missing_values / ask_human (the human-facing… (+8 more)

### Community 43 - "replay/context.py"
Cohesion: 0.10
Nodes (17): pydantic, Ctx, note_takeover_send(), Page, Request, Ctx: what every replay function takes first (session, run, settings, send…, Frame, Protocol (+9 more)

### Community 44 - "test_shared_evidence.py"
Cohesion: 0.13
Nodes (18): config_hash(), git_sha(), JsonValue, Path, `git rev-parse HEAD`, or "unknown" (no git, not a repo, any failure)., sha256 of the repr of the frozen configs plus the site name., What ``run.json`` holds: prompt version, model, config hash, git sha. Never a…, run_info() (+10 more)

### Community 45 - "mismatch.py"
Cohesion: 0.22
Nodes (13): dropdown_options(), mismatches(), _norm_num(), Dropdown, Values a send carries that the human never gave, and the dropdown choices to…, Numbers being sent that the human never gave, e.g. account 1450 vs 1400. Only…, For each key: the options of the page dropdown whose CURRENT value is exactly…, _hide() (+5 more)

### Community 46 - "test_table.py"
Cohesion: 0.17
Nodes (16): AST, _defs(), _is_header(), _look(), Path, The shared OCR table reader: parity between cua.vision.table and both…, ast.dump compare, ignoring docstrings -- the functions this step did not have…, tests/replay/test_table_replay.py's own SHARED set is the contract this module… (+8 more)

### Community 47 - "DiscoveryConfig"
Cohesion: 0.11
Nodes (41): DiscoveryConfig, Discovery-only settings., Discovery: an LLM agent learns a task once and the recorder saves it as a…, attach(), build_ctx(), _count_nav(), _hooks(), new_run() (+33 more)

### Community 48 - "ReplayConfig"
Cohesion: 0.11
Nodes (18): Replay-only settings., ReplayConfig, _fake_session(), asyncio, Path, attach (the replay setup cell), the guard's replay hooks, and R7: after…, C1: one cuaReply forwarder and one close listener per control page, both…, I1: the once-per-page response listener reads the current ctx. (+10 more)

### Community 49 - "test_send_guard.py"
Cohesion: 0.15
Nodes (25): ``await guard(route)`` is the route handler. ``guard.lock`` is the send gate:…, Side-specific steps, each at the exact point its notebook ran it. on_request:…, SendGuard, SendHooks, Control, _new(), _no_dropdowns(), _old() (+17 more)

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
Cohesion: 0.10
Nodes (31): _in_control(), The take-over itself: badge YOU, unlock the site, wait for Done (panel or…, _takeover_note(), Answerable, button_clicked(), ext_call(), Extension, handback_button() (+23 more)

### Community 54 - "Session"
Cohesion: 0.16
Nodes (19): BrowserContext, Playwright, Playwright, no decisions: the open session, the site lock, our own input,…, _alive(), check_viewport(), close_session(), _extension(), handback_dir() (+11 more)

### Community 55 - "Look"
Cohesion: 0.08
Nodes (58): Cols, dropdown_under(), The index of the native <select> right under this point, or None (bounded; None…, _columns(), clean_label(), column_header(), headings(), is_header() (+50 more)

### Community 56 - "loader.py"
Cohesion: 0.11
Nodes (27): Exception, _ask(), ask_inputs(), ask_option(), _ask_rows(), given_inputs(), input_type(), mistyped() (+19 more)

### Community 57 - "middleware.py"
Cohesion: 0.14
Nodes (16): CompiledStateGraph, deepagents, langchain_agents_middleware, langgraph_checkpoint_memory, build_agent(), BaseChatModel, Ctx, build_agent: the notebook's ``AGENT = create_deep_agent(...)`` (discovery.py… (+8 more)

### Community 58 - "FakeTab"
Cohesion: 0.12
Nodes (3): FakeTab, SimpleNamespace, A fake site or control tab with the Playwright calls discovery's wiring and…

### Community 59 - "Trace"
Cohesion: 0.18
Nodes (13): act(), Lock, Session, Step, Unlock the site tab, run our own input steps, relock, settle, take a new look., _hooks(), _session(), test_act_waits_for_a_held_send_before_looking() (+5 more)

### Community 60 - "._record"
Cohesion: 0.29
Nodes (6): Handler, _arg_values(), AsyncHandler, ModelRequest, ModelResponse, Every text the model is about to pass a tool (refs and x/y are ints, not…

### Community 62 - "test_screenshot.py"
Cohesion: 0.27
Nodes (9): _png(), asyncio, MonkeyPatch, take_look: page calls on the loop, the CPU part (OCR, drawing, encoding) in one…, ShotPage, test_page_width_reads_the_window_width(), test_snap_look_gives_the_look_png_or_none_on_timeout(), test_snap_png_passes_the_timeout_and_gives_none_on_error() (+1 more)

### Community 63 - "Discovery decisions"
Cohesion: 0.08
Nodes (24): Base decisions, Cuts, Discovery decisions, Q10: window size and zoom — DECIDED, Q11: notebook format — DECIDED, Q12: dropdowns — DECIDED, Q13: scrolling — DECIDED, Q14: private data in saved pictures — DECIDED (+16 more)

### Community 64 - "2. Each box, with an example"
Cohesion: 0.12
Nodes (15): 1. Diagram, 2. Each box, with an example, 3. All tools, 4. Step by step: one discovery run, 5. Notes, Browser (Playwright), Control window and site lock (Q-A), Discovery architecture (+7 more)

### Community 65 - "request.py"
Cohesion: 0.16
Nodes (18): functools, JsonObj, _flat(), _json(), What a held request sends, and the same request rebuilt with edited values.…, Every value a request sends, from its query, a form body, or a JSON body…, The request's url and body with these values put back in, in the same format., rebuilt() (+10 more)

### Community 66 - "ControlWindow"
Cohesion: 0.11
Nodes (20): base64, Question, ControlWindow, discovery_control(), _img(), Protocol, ControlWindow: our own "Agent control" tab, the only place a human answers.…, Answers the question on top. Closing the window (None) answers every one: fail… (+12 more)

### Community 67 - "2. Components"
Cohesion: 0.12
Nodes (15): 1. Diagram, 2. Components, 3. Step types, 4. Worked example: ParaBank login + read balance, 5. Notes, Actor, Artifact (made by discovery, not replay), Browser setup (+7 more)

### Community 68 - "HeldPage"
Cohesion: 0.11
Nodes (9): DoneWhileSending, FormRoute, HeldPage, HeldRoute, NeverAnsweredGate, Ctx, Like Playwright: while a form POST (a navigation) is held, `page.screenshot()`…, The human clicks Done just as their form POST is held: the gate must still show… (+1 more)

### Community 69 - "Pure-Visual Discovery Notebook: Build Plan"
Cohesion: 0.09
Nodes (22): 10. Open risks, 1. Global constraints (every task must follow these), 2. Review focus (inputs no spec line covers, but likely to bite), 3. What already exists (reuse, or its visual version), 3a. How the agent is built today (`agent.ipynb` STEP 4, `src/cua/agent.py`), 3b. Existing handoff rules: when a human is called in, 3c. Existing tools → the new tools, 4. New dependencies (checked on PyPI, 2026-09-28) (+14 more)

### Community 71 - "SiteLock"
Cohesion: 0.16
Nodes (12): CdpSender, Protocol, SiteLock: the site tab ignores all real input (CDP…, The one method of a Playwright ``CDPSession`` the lock uses. ``params`` is a…, The site tab ignores all real input (CDP). Lifted only around our own action or…, SiteLock, FakeCdp, asyncio (+4 more)

### Community 72 - ".awrap_model_call"
Cohesion: 0.18
Nodes (8): Classifier, page_name(), AsyncHandler, ModelRequest, ModelResponse, Protocol, The URL's last path segment: no query, no ``;jsessionid=``, no trailing slash,…, test_page_name_is_the_last_path_segment()

### Community 73 - "ReplayResult"
Cohesion: 0.09
Nodes (31): What a replay run returns: its Status, the Stop that ends a run early, and…, R17 run statuses. A member is a plain str, so ``Status.SUCCESS == "SUCCESS"``., ReplayResult, Status, StrEnum, test_partial_label_when_not_success(), ReplayResult summary/outputs_line, Stop, and the Status values., test_partial_outputs_line_when_not_success() (+23 more)

### Community 74 - "_where"
Cohesion: 0.25
Nodes (8): parametrize, A box's own text with nothing cut from it (a value, a button) stays off the…, test_a_box_border_read_as_a_bracket_is_not_part_of_the_label(), test_a_label_that_is_only_a_value_falls_back_to_the_next_nearest(), test_a_plain_word_under_the_point_is_still_never_the_anchor(), test_a_point_inside_a_merged_label_and_value_box_anchors_on_the_cleaned_label(), test_a_sent_value_joined_to_a_label_is_cut_from_it_and_from_the_input_name(), _where()

### Community 75 - "Capability"
Cohesion: 0.12
Nodes (43): Drift, R7: nothing kept. A fresh run, and the guard reads that one from now on., wipe(), action_allowed(), _cleanup_step(), error_page(), finish(), is_cleanup() (+35 more)

### Community 77 - "test_routing.py"
Cohesion: 0.19
Nodes (17): Classifies the step's job with TypeSafe's Choice primitive and narrows the tool…, ToolRouter, _choice(), FakeClassifier, FakeRequest, _names(), asyncio, CaptureFixture (+9 more)

### Community 79 - "_check_login_order"
Cohesion: 0.29
Nodes (7): _check_login_order(), Step, The {{input}} names the steps use, in order. {{secret:x}} is not an input., Every secret is typed before the first click (the login). Replay clicking Log…, step_inputs(), A guard on the result: replay must never click Log In before the boxes are…, test_secrets_typed_after_the_login_click_are_refused()

### Community 80 - "value_in_box"
Cohesion: 0.33
Nodes (6): (value, pattern) for an extract: the whole box when it is exactly the type,…, value_in_box(), parametrize, test_a_box_without_the_shape_is_refused(), test_a_whole_box_type_takes_the_whole_box(), test_the_value_is_the_first_match_of_its_shape_inside_the_box()

### Community 81 - "test_import_rules.py"
Cohesion: 0.29
Nodes (13): _cua_imports(), _layer_files(), _module(), parametrize, Path, The package's import rule (docs/PRODUCTIONIZE_PLAN.md section 1), read from…, The top-level cua subpackage of every ``cua.*`` import (``import`` or ``from``)., Guard the guard: a planted forbidden import is caught in both spellings. (+5 more)

### Community 82 - "test_build.py"
Cohesion: 0.57
Nodes (6): _capture(), MonkeyPatch, build_agent: the notebook's create_deep_agent call, with routing appended only…, test_build_agent_wires_the_notebooks_agent(), test_routing_is_appended_after_the_notebooks_middleware(), test_the_page_path_is_read_live()

### Community 84 - "Route"
Cohesion: 0.17
Nodes (5): Frame, HumanControl, Takes over; while 'in control', the human opens a page and sends a form., Req, Route

### Community 85 - "test_prompt.py"
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

### Community 89 - "rescue"
Cohesion: 0.33
Nodes (7): Ctx, JsonValue, Step, Returns the evidence (3.6): screenshots at start and hand-back, page and send…, The human is in control until Done or the toolbar button; pages they visit are…, rescue(), _taken_over()

### Community 90 - "Driven"
Cohesion: 0.47
Nodes (3): Driven, Ctx, The stubbed page work: every ``act`` call and the looks it returns.

### Community 91 - "test_capability.py"
Cohesion: 0.23
Nodes (9): _data(), parametrize, Path, cua.schema.Capability loads every saved artifact and refuses an unknown schema…, test_a_target_needs_a_findable_rung(), test_a_wrong_schema_version_is_refused(), test_an_unknown_key_is_refused(), test_every_saved_artifact_loads() (+1 more)

### Community 92 - "test_goal.py"
Cohesion: 0.14
Nodes (21): Agent, Protocol, What run_goal needs of the compiled deep agent., New run on a fresh thread; pass an earlier thread_id to resume it with a next…, run_goal(), FakeAgent, HangingAgent, asyncio (+13 more)

### Community 93 - "human.py"
Cohesion: 0.16
Nodes (25): Field, into_box(), list_options(), Focus the site tab, click the box, clear it, type (see…, Every option of the dropdown at this point ([] if it is not a dropdown)., _enter(), _from_goal(), human_fills() (+17 more)

### Community 94 - "test_value_types.py"
Cohesion: 0.36
Nodes (7): parametrize, Path, cua.schema.value_types matches both notebooks' SHAPES/TYPES exactly., SHAPES and TYPES as each notebook defines them (TYPES spreads SHAPES, so exec…, _tables(), test_tables_equal_the_notebooks(), test_value_matches_type()

### Community 95 - "locate"
Cohesion: 0.23
Nodes (20): locate(), Path, Target, (point, rung) from the first rung that hits, or None., _dup_target(), _look(), Path, Target (+12 more)

### Community 96 - "routing.py"
Cohesion: 0.11
Nodes (26): ChatAnthropic, ModelKind, ModuleType, os, build_routing_middleware(), confidence_gate(), job_tool_names(), _model_router() (+18 more)

### Community 97 - "Element"
Cohesion: 0.05
Nodes (69): crop_box(), cut_crop(), _ink(), input_box(), Crops around one point: find the element there, crop around it, read text near…, New ink appeared INSIDE the input box (text, or a password's dots). A click…, Crop around the target, with every other piece of text blanked out., Pixels around the point changed. Catches password dots that OCR cannot read. (+61 more)

### Community 98 - "test_human.py"
Cohesion: 0.12
Nodes (47): goal_value(), human_help(), The value the goal already gives for this field, or None. Code backstop for the…, Q21, open-ended: the human answers in words, takes over the site, or stops the…, Q21: the one time the site unlocks for a human. What they did is kept as…, take_over(), _answer(), _badge() (+39 more)

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
Cohesion: 0.22
Nodes (28): BaseModel, _navigate(), output(), Event log -> ``Capability``: steps, inputs, outputs and secrets come from the…, ``to_step``'s open_path branch, unchanged., target(), to_step(), Anchor (+20 more)

### Community 108 - "Ctx"
Cohesion: 0.07
Nodes (82): P, act(), canvas(), choose_option(), _count_start(), crop(), Ctx, look() (+74 more)

### Community 109 - "test_evidence.py"
Cohesion: 0.17
Nodes (20): The discovery agent: system prompt, middleware, optional TypeSafe routing, and…, The discovery agent's system prompt, verbatim from…, _artifact(), masked(), fixture, MonkeyPatch, Path, save_evidence: one masked folder per run. No run value or secret is ever… (+12 more)

### Community 110 - "make_ctx"
Cohesion: 0.12
Nodes (36): after_login_click(), D69: at most N login tries; a failure text on screen stops login for the run., make_ctx(), Ctx, A discovery ``Ctx`` over fakes, built like ``attach`` but with no page wiring., helped(), _only(), asyncio (+28 more)

### Community 111 - "is_sensitive"
Cohesion: 0.14
Nodes (8): is_sensitive(), pretty(), address.zipCode' -> 'Address zip code' (for the human; the key itself is kept)., Request, Gate 1: Approve, or Edit = back to the form with every value, then again.…, RouteLike, test_is_sensitive_is_a_casefolded_substring(), test_pretty()

### Community 112 - "_logged_arg_keys"
Cohesion: 0.50
Nodes (4): _logged_arg_keys(), The arg-dict keys of every ``log(ctx, "<tool>", {...}, ...)`` call in the tool…, Banking rule (ported from test_no_values_stored.py, now on the package's own…, test_typed_and_selected_values_never_reach_the_log()

### Community 113 - "Replay notebook plan"
Cohesion: 0.33
Nodes (5): Decisions made here (review), Open questions for the user, Replay notebook plan, Sections, Tasks

### Community 115 - "config.py"
Cohesion: 0.09
Nodes (20): dotenv, model_validator, pathlib, _actions(), _find_root(), _outcomes(), Path, Shared configuration: the site profile, browser/discovery/replay settings, and… (+12 more)

### Community 117 - "test_dropdowns.py"
Cohesion: 0.16
Nodes (18): _approve(), HeldPage, _logged(), _no_crop_pixels(), asyncio, Ctx, fixture, MonkeyPatch (+10 more)

### Community 118 - "load_capability"
Cohesion: 0.13
Nodes (29): load_capability(), load_outcomes(), _missing_crops(), Path, The capability and the folder its crop paths are relative to., The capability's own `outcomes:` [{text, status, meaning}], else the site's…, Path, Discovery's saved artifact runs in replay unchanged: build -> save -> load ->… (+21 more)

### Community 121 - "_FakeModel"
Cohesion: 0.18
Nodes (8): _FakeModel, asyncio, Stands in for a LangChain chat model: no network, records the prompt., asyncio, test_describe_names_the_options_outputs(), test_describe_names_the_table_outputs(), _Structured, test_describe_asks_the_given_model_with_labels_and_input_names_only()

### Community 123 - "discovery/evidence.py"
Cohesion: 0.15
Nodes (19): json, artifact_texts(), _copy_capability(), _events(), _folder(), Ctx, OcrFn, Path (+11 more)

### Community 125 - "fakes.py"
Cohesion: 0.18
Nodes (5): FakeLock, Shared offline fakes for the ported test suite (tests/unit, tests/integration).…, A fake ``cua.browser.SiteLock``: ``open()`` records unlock/lock, nothing else., The handful of ``playwright.async_api.Request`` fields the project's code reads., _Request

### Community 129 - "replay/wiring.py"
Cohesion: 0.11
Nodes (19): bind_control(), ControlTab, Protocol, Bind the control tab to the current :class:`ControlWindow`, once per tab. A…, The Playwright calls binding makes on the control tab., Point the control tab's buttons and its close at ``control``. Re-run safe: the…, _note_latest(), note_response() (+11 more)

### Community 130 - "test_saved_artifacts.py"
Cohesion: 0.31
Nodes (7): MonkeyPatch, parametrize, Path, Every capability saved in the top-level artifacts/ folder (Decision 6) loads in…, test_a_saved_artifact_loads_in_replay(), test_a_saved_artifact_round_trips(), test_the_old_artifacts_folder_is_gone()

### Community 133 - "helpers.py"
Cohesion: 0.28
Nodes (8): Ctx, Replay test helpers: ``make_replay_ctx`` (a real Ctx on fakes), ``mk_look``,…, ``take_look`` always returns this look., screen(), set_shoot(), clean(), ectx(), fixture

### Community 141 - "cua.discovery.agent"
Cohesion: 0.50
Nodes (3): cua.discovery.agent, Read order, What may NOT go here

## Knowledge Gaps
- **159 isolated node(s):** `MODES`, `manifest_version`, `name`, `version`, `description` (+154 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **15 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Ctx` connect `Ctx` to `replay/wiring.py`, `FakeRoute`, `test_replay_inputs.py`, `test_middleware.py`, `discovery/context.py`, `test_replay_engine.py`, `test_replay_rescue.py`, `test_replay_handback.py`, `SiteProfile`, `test_replay_table.py`, `BrowserConfig`, `make_replay_ctx`, `test_replay_steps.py`, `ActTab`, `replay/context.py`, `DiscoveryConfig`, `ReplayConfig`, `Session`, `Look`, `middleware.py`, `FakeTab`, `HeldPage`, `ScriptedControl`, `GateControl`, `Route`, `Driven`, `test_goal.py`, `human.py`, `Element`, `test_human.py`, `FakeInput`, `test_dropdowns.py`, `discovery/evidence.py`, `fakes.py`?**
  _High betweenness centrality (0.057) - this node is a cross-community bridge._
- **Why does `Look` connect `Look` to `replay/wiring.py`, `FakeRoute`, `test_act.py`, `helpers.py`, `test_input.py`, `test_dropdown.py`, `discovery/context.py`, `test_replay_rescue.py`, `locate.py`, `steps.py`, `make_replay_ctx`, `test_replay_steps.py`, `RefCounter`, `ActTab`, `test_table.py`, `FakeTab`, `Trace`, `test_screenshot.py`, `Driven`, `human.py`, `locate`, `Element`, `test_human.py`, `FakeInput`, `Ctx`, `test_dropdowns.py`, `load_capability`, `fakes.py`?**
  _High betweenness centrality (0.051) - this node is a cross-community bridge._
- **Why does `BrowserConfig` connect `BrowserConfig` to `cli.py`, `FakeRoute`, `test_saved_artifacts.py`, `test_input.py`, `test_dropdown.py`, `test_replay_handback.py`, `SiteProfile`, `make_replay_ctx`, `test_replay_steps.py`, `RefCounter`, `ActTab`, `replay/context.py`, `test_shared_evidence.py`, `DiscoveryConfig`, `test_takeover_loop.py`, `test_extension.py`, `Session`, `loader.py`, `FakeTab`, `Trace`, `test_screenshot.py`, `Element`, `FakeInput`, `Ctx`, `config.py`, `load_capability`, `fakes.py`?**
  _High betweenness centrality (0.050) - this node is a cross-community bridge._
- **Are the 27 inferred relationships involving `Look` (e.g. with `Ctx` and `DiscoveryRun`) actually correct?**
  _`Look` has 27 INFERRED edges - model-reasoned connections that need verification._
- **Are the 60 inferred relationships involving `Ctx` (e.g. with `LatestScreenshotOnly` and `NoopAnthropicPromptCachingMiddleware`) actually correct?**
  _`Ctx` has 60 INFERRED edges - model-reasoned connections that need verification._
- **Are the 36 inferred relationships involving `BrowserConfig` (e.g. with `Session` and `Answerable`) actually correct?**
  _`BrowserConfig` has 36 INFERRED edges - model-reasoned connections that need verification._
- **Are the 55 inferred relationships involving `build_capability()` (e.g. with `saved()` and `test_a_continued_table_is_one_step()`) actually correct?**
  _`build_capability()` has 55 INFERRED edges - model-reasoned connections that need verification._