# Graph Report - BankerAgent  (2026-10-01)

## Corpus Check
- 200 files · ~187,699 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 2749 nodes · 7879 edges · 142 communities (125 shown, 17 thin omitted)
- Extraction: 93% EXTRACTED · 7% INFERRED · 0% AMBIGUOUS · INFERRED: 535 edges (avg confidence: 0.63)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `e9a447b6`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- cli.py
- FakeRoute
- Productionize Plan: notebooks → `src/cua/` package
- test_act.py
- Evidence README
- look.py
- test_recorder_types.py
- test_replay_inputs.py
- test_input.py
- agent/build.py
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
- test_config.py
- replay/evidence.py
- ReplayConfig
- recorder/__init__.py
- steps.py
- vision/__init__.py
- integration/conftest.py
- test_redact_more.py
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
- test_replay_wiring.py
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
- test_middleware.py
- Discovery decisions
- 2. Each box, with an example
- request.py
- ControlWindow
- 2. Components
- HeldPage
- Pure-Visual Discovery Notebook: Build Plan
- ScriptedControl
- SiteLock
- discovery/context.py
- ReplayResult
- SiteProfile
- engine.py
- GateControl
- test_routing.py
- FakeWin
- guard.py
- Box
- test_import_rules.py
- test_prompt.py
- copy
- HumanControl
- build_tools
- cua
- pytest
- cua.schema
- rescue.py
- handoff/__init__.py
- test_capability.py
- test_goal.py
- human.py
- test_value_types.py
- locate
- hosts.py
- decode
- test_human.py
- interface-ai-cua
- cua.browser
- cua.handoff
- cua.safety
- cua.discovery
- cua.discovery.recorder
- cua.replay
- schema/__init__.py
- types.py
- act.py
- test_evidence.py
- make_ctx
- ._held
- test_session.py
- Replay notebook plan
- Ctx
- config.py
- crop
- test_dropdowns.py
- load_capability
- one_at_a_time
- hide_secrets
- _FakeModel
- test_table.py
- discovery/evidence.py
- FakePage
- fakes.py
- background.js
- BrowserConfig
- pathlib
- bind_control
- test_saved_artifacts.py
- Response
- Tab
- screen
- Route
- choose_option_at_point
- FakeBox
- test_read_helpers.py
- AST
- masked
- Ctx
- cua.discovery.agent

## God Nodes (most connected - your core abstractions)
1. `Look` - 123 edges
2. `make_ctx()` - 95 edges
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
- 3-file cycle: `src/cua/discovery/tools/__init__.py -> src/cua/discovery/tools/act.py -> src/cua/discovery/tools/guard.py -> src/cua/discovery/tools/__init__.py`
- 3-file cycle: `src/cua/discovery/tools/__init__.py -> src/cua/discovery/tools/read.py -> src/cua/discovery/tools/guard.py -> src/cua/discovery/tools/__init__.py`
- 3-file cycle: `src/cua/discovery/tools/__init__.py -> src/cua/discovery/tools/act.py -> src/cua/discovery/tools/observe.py -> src/cua/discovery/tools/__init__.py`
- 4-file cycle: `src/cua/discovery/tools/__init__.py -> src/cua/discovery/tools/act.py -> src/cua/discovery/tools/human.py -> src/cua/discovery/tools/observe.py -> src/cua/discovery/tools/__init__.py`
- 4-file cycle: `src/cua/discovery/tools/__init__.py -> src/cua/discovery/tools/human.py -> src/cua/discovery/tools/observe.py -> src/cua/discovery/tools/guard.py -> src/cua/discovery/tools/__init__.py`
- 4-file cycle: `src/cua/discovery/tools/__init__.py -> src/cua/discovery/tools/nav.py -> src/cua/discovery/tools/observe.py -> src/cua/discovery/tools/guard.py -> src/cua/discovery/tools/__init__.py`
- 4-file cycle: `src/cua/discovery/tools/__init__.py -> src/cua/discovery/tools/act.py -> src/cua/discovery/tools/observe.py -> src/cua/discovery/tools/guard.py -> src/cua/discovery/tools/__init__.py`
- 5-file cycle: `src/cua/discovery/tools/__init__.py -> src/cua/discovery/tools/act.py -> src/cua/discovery/tools/guard.py -> src/cua/discovery/tools/human.py -> src/cua/discovery/tools/observe.py -> src/cua/discovery/tools/__init__.py`
- 5-file cycle: `src/cua/discovery/tools/__init__.py -> src/cua/discovery/tools/nav.py -> src/cua/discovery/tools/guard.py -> src/cua/discovery/tools/human.py -> src/cua/discovery/tools/observe.py -> src/cua/discovery/tools/__init__.py`
- 5-file cycle: `src/cua/discovery/tools/__init__.py -> src/cua/discovery/tools/read.py -> src/cua/discovery/tools/guard.py -> src/cua/discovery/tools/human.py -> src/cua/discovery/tools/observe.py -> src/cua/discovery/tools/__init__.py`
- 5-file cycle: `src/cua/discovery/tools/__init__.py -> src/cua/discovery/tools/act.py -> src/cua/discovery/tools/human.py -> src/cua/discovery/tools/observe.py -> src/cua/discovery/tools/guard.py -> src/cua/discovery/tools/__init__.py`

## Communities (142 total, 17 thin omitted)

### Community 0 - "cli.py"
Cohesion: 0.12
Nodes (26): argparse, Namespace, _close(), default_site(), discover(), main(), parse_args(), parse_inputs() (+18 more)

### Community 1 - "FakeRoute"
Cohesion: 0.11
Nodes (11): FakeControl, FakePage, FakeRoute, A fake discovery/replay ``CONTROL`` surface (what ``ControlWindow`` presents).…, A fake ``playwright.async_api.Route``: records every…, A fake ``playwright.async_api.Page``. Every awaited method is recorded in…, asyncio, Tests for the shared offline fakes in tests/fakes.py (TDD: written before the… (+3 more)

### Community 2 - "Productionize Plan: notebooks → `src/cua/` package"
Cohesion: 0.12
Nodes (16): 10. Line-count offenders (today), 1. Package tree, 2. De-duplication (checked by AST diff of both notebooks), 3. State: globals → explicit objects, 4. Async and typing, 5. Notebooks after the move, 6. Tests, 7. ML-engineering practices (kept small) (+8 more)

### Community 3 - "test_act.py"
Cohesion: 0.07
Nodes (75): Items, (value, pattern) for an extract: the whole box when it is exactly the type,…, value_in_box(), make_look(), A look whose elements are numbered 1.. in order (ref, text, box)., Driven, _head(), _helped() (+67 more)

### Community 5 - "look.py"
Cohesion: 0.16
Nodes (15): Our own input into the locked site tab: ``act`` (unlock, run steps, relock,…, Page wiring for replay: :func:`attach` (the notebook's setup cell, replay.py…, canvas_size(), Canvas-pixel <-> page-point mapping: any window size or pixel density maps to…, The size of the image the model is looking at right now., to_page(), Box, Element, Look: the shapes every vision/discovery/replay function reads and…, Evidence screenshot. A held form POST blocks ``page.screenshot()``: give up,… (+7 more)

### Community 6 - "test_recorder_types.py"
Cohesion: 0.25
Nodes (13): Typed inputs: the recorder infers each input's type from the shapes of the…, Older logs (and any tool that did not log shapes) never guess a type., test_a_plain_whole_number_is_a_number_so_decimals_pass_replay_later(), test_a_value_with_no_shape_is_string(), test_all_currency_values_make_a_currency_input(), test_an_event_without_shapes_is_string(), test_human_entry_is_typed_too(), test_no_typed_value_reaches_the_capability_or_its_yaml() (+5 more)

### Community 7 - "test_replay_inputs.py"
Cohesion: 0.12
Nodes (34): select(), type_(), _cap(), ClearPage, env(), FakeForm, FakePage, asyncio (+26 more)

### Community 8 - "test_input.py"
Cohesion: 0.08
Nodes (30): act(), into_box(), Lock, Page, Session, Step, The response to a send lands after the human's approval, not after the click:…, Unlock the site tab, run our own input steps, relock, settle, take a new look. (+22 more)

### Community 9 - "agent/build.py"
Cohesion: 0.12
Nodes (20): CompiledStateGraph, deepagents, Handler, langgraph_checkpoint_memory, build_agent(), BaseChatModel, Ctx, build_agent: the notebook's ``AGENT = create_deep_agent(...)`` (discovery.py… (+12 more)

### Community 10 - "test_dropdown.py"
Cohesion: 0.08
Nodes (33): BaseException, list_options(), Dropdown, Page, Every option of the dropdown at this page point ([] if it is not a dropdown).…, The page's dropdowns, read BEFORE an action (never while guard_send holds a…, read_dropdowns(), IndexPage (+25 more)

### Community 12 - "Replay decisions"
Cohesion: 0.08
Nodes (23): R10: where the compile step lives — DECIDED, R11: why compile, if `response_format` exists? — PROPOSED, R12: what each step type compiles to — PROPOSED, R13: target schema — PROPOSED, R14: what rung 2 needs that discovery doesn't record — DONE, R15: auto-approve at replay — PROPOSED, R16: dead ends and retries at compile — PROPOSED, R17: replay result statuses — PROPOSED (+15 more)

### Community 16 - "DiscoveryRun"
Cohesion: 0.12
Nodes (17): Saved, The current run (the one the send guard serves)., DiscoveryRun, What the human gave: the goal and every answer (the send guard's mismatch text)., Every saved text, table cells included (evidence masking only)., Banking: values live only for the run. Keep the log (labels only), drop the…, saved_texts(), wipe() (+9 more)

### Community 17 - "test_cli.py"
Cohesion: 0.12
Nodes (24): _fake_session(), _patch_session(), CaptureFixture, MonkeyPatch, parametrize, Path, SimpleNamespace, cua.cli: argument parsing, --input parsing, and main() as the only asyncio.run… (+16 more)

### Community 18 - "test_replay_engine.py"
Cohesion: 0.19
Nodes (47): cap(), click(), extract(), clean(), _finish(), _login_cap(), _no_snap(), _only() (+39 more)

### Community 19 - "test_replay_rescue.py"
Cohesion: 0.21
Nodes (25): The guard keeps its own reference to the control window: swap both., set_control(), _env(), _fail_clicks(), HangPage, HumanSimple, asyncio, MonkeyPatch (+17 more)

### Community 20 - "test_llm.py"
Cohesion: 0.20
Nodes (14): _clean_env(), _gateway(), fixture, MonkeyPatch, Offline tests for `cua.llm.make_chat_model`. No network, no real key. Default:…, test_ca_bundle_passthrough(), test_existing_ssl_cert_file_wins(), test_gateway_env_means_gateway() (+6 more)

### Community 21 - "test_replay_handback.py"
Cohesion: 0.19
Nodes (19): _bctx(), Ext, Human, PanelDone, asyncio, Ctx, parametrize, The toolbar hand-back button during a rescue (its service worker, never the… (+11 more)

### Community 22 - "test_config.py"
Cohesion: 0.13
Nodes (19): load_site(), Read and validate ``configs/<name>.yaml`` (root defaults to the repo root)., fixture, parametrize, Path, cua.config: the site profile from configs/parabank.yaml, and the notebooks'…, site(), test_allowed_actions_default_to_all() (+11 more)

### Community 23 - "replay/evidence.py"
Cohesion: 0.17
Nodes (14): _drift_lines(), masked_outputs(), Ctx, JsonValue, OcrFn, Path, Redact, One folder per replay run (spec 3.5, 6.3): summary, drift, failure, the final… (+6 more)

### Community 24 - "ReplayConfig"
Cohesion: 0.13
Nodes (29): SameTextLike, Replay-only settings., ReplayConfig, Replay: runs a capability saved by discovery with plain code, no LLM (step 4:…, fill(), Put inputs into `{{name}}`. `{{secret:x}}` stays as it is: secrets go in only…, anchor_point(), find_template() (+21 more)

### Community 25 - "recorder/__init__.py"
Cohesion: 0.08
Nodes (49): check_savable(), output(), Raise NotSaved before any model call when this run cannot become a capability., ``build_capability``'s refusals, unchanged: a leaked value, a blind dropdown,…, _refuse(), used_inputs(), checkpoint(), The capability's checkpoint: the text replay must see to call the run a… (+41 more)

### Community 26 - "steps.py"
Cohesion: 0.10
Nodes (45): Point, choose_option(), do_click(), do_extract(), do_extract_table(), do_navigate(), do_scroll(), do_select() (+37 more)

### Community 27 - "vision/__init__.py"
Cohesion: 0.15
Nodes (22): Pixels -> text: screenshots, OCR, canvas math, crops, and the shared table…, append_rows(), cell_shape(), col_of(), column_spans(), like_rows(), The shared OCR table reader: discovery and replay use it to find a table's…, A table's end: a line that no longer looks like its rows (a footer, a menu, a… (+14 more)

### Community 29 - "test_redact_more.py"
Cohesion: 0.17
Nodes (20): mask_png(), OcrFn, Black out every OCR box whose text holds a run value. A clean image is written…, encode(), NDArray, uint8, load(), Path (+12 more)

### Community 30 - "test_replay_table.py"
Cohesion: 0.21
Nodes (18): _cap(), _defs(), Page, asyncio, Ctx, MonkeyPatch, Path, do_extract_table: find the header by its label, read the rows with discovery's… (+10 more)

### Community 31 - "redact.py"
Cohesion: 0.14
Nodes (18): Pattern, re, The notebook's two agent middlewares, moved unchanged from discovery.py…, _num(), Value masking: ``norm``, ``is_sensitive``, ``hide_secrets``, ``redactor``,…, text -> text with every value masked. Numbers match however they are written…, redactor(), Value types an extract may declare. Shared by discovery and replay (one table,… (+10 more)

### Community 32 - "test_notebooks.py"
Cohesion: 0.26
Nodes (16): Call, Module, _bind(), _code_cells(), _markdown(), _offline_namespace(), parametrize, Path (+8 more)

### Community 33 - "build_capability"
Cohesion: 0.08
Nodes (69): build_capability(), Steps, inputs and secrets come from the log only. The model's text cannot fail…, flag_leaks(), Mark (never store) an event whose label, anchor, own text, hint or input name…, crops_for(), _ev(), _meta(), Path (+61 more)

### Community 34 - "make_replay_ctx"
Cohesion: 0.18
Nodes (24): make_replay_ctx(), A real Ctx (real SendGuard, real ReplayRun) over a fake page/control/lock.…, _extract(), _notebook_assign(), _pcap(), asyncio, Ctx, parametrize (+16 more)

### Community 35 - "test_replay_evidence.py"
Cohesion: 0.26
Nodes (19): Path, write_cap(), _all_text(), fake_ocr(), _png(), Ctx, fixture, Path (+11 more)

### Community 36 - "CLAUDE.md (project instructions)"
Cohesion: 0.12
Nodes (19): CLAUDE.md (project instructions), D101: labeled_value refuses a table-header resolution (general fix), D102: label_header/value_header flags ported into agent.py + cli.py capture path, D92: Evidence Capture Helpers (save_discovery_evidence/save_replay_evidence), D93: Pre-existing 02_artifact_schema.py IndexError bug, D95: Missing create_deep_agent import found live in BROWSER 12, D96: build_agent() goal_text vs given_text field-name bug, D97: cua replay --login flag + repeated Balance header trap (+11 more)

### Community 37 - "test_replay_steps.py"
Cohesion: 0.08
Nodes (40): mk_look(), navigate(), Replay test helpers: ``make_replay_ctx`` (a real Ctx on fakes), ``mk_look``,…, _click_env(), _form_png(), GotoPage, _judge(), Page (+32 more)

### Community 38 - "RefCounter"
Cohesion: 0.08
Nodes (39): RapidOCR, NDArray, uint8, Fit the screenshot inside the canvas. Returns it and canvas-pixel -> page-point…, to_canvas(), draw_numbered(), number(), ocr() (+31 more)

### Community 39 - "manifest.json"
Cohesion: 0.11
Nodes (18): action, default_icon, default_title, background, service_worker, 128, 16, 32 (+10 more)

### Community 41 - "safety/__init__.py"
Cohesion: 0.12
Nodes (13): Safety: what may leave the tab (hosts, the two send gates) and keeping values…, Protocol, The fields of a ``playwright.async_api.Request`` the guard reads., Request, ControlLike, GuardOptions, LookLike, Protocol (+5 more)

### Community 42 - "test_human_tools.py"
Cohesion: 0.35
Nodes (13): _ctx(), asyncio, Ctx, MonkeyPatch, finish_business_outcome / request_missing_values / ask_human (the human-facing…, test_ask_human_asks_with_the_question(), test_finish_needs_the_proof_on_the_screen(), test_no_fields_given() (+5 more)

### Community 43 - "replay/context.py"
Cohesion: 0.14
Nodes (14): pydantic, note_takeover_send(), Request, Ctx: what every replay function takes first (session, run, settings, send…, R7: nothing kept. A fresh run, and the guard reads that one from now on., wipe(), LastRun, One replay run's working state: :class:`ReplayRun` (was the notebook's… (+6 more)

### Community 44 - "cua/evidence.py"
Cohesion: 0.14
Nodes (19): config_hash(), git_sha(), JsonValue, Path, Evidence helpers shared by discovery and replay: masking a JSON-able tree,…, `git rev-parse HEAD`, or "unknown" (no git, not a repo, any failure)., sha256 of the repr of the frozen configs plus the site name., What ``run.json`` holds: prompt version, model, config hash, git sha. Never a… (+11 more)

### Community 45 - "mismatch.py"
Cohesion: 0.22
Nodes (13): dropdown_options(), mismatches(), _norm_num(), Dropdown, Values a send carries that the human never gave, and the dropdown choices to…, Numbers being sent that the human never gave, e.g. account 1450 vs 1400. Only…, For each key: the options of the page dropdown whose CURRENT value is exactly…, _hide() (+5 more)

### Community 46 - "discovery/wiring.py"
Cohesion: 0.21
Nodes (11): build_ctx(), _count_nav(), _hooks(), new_run(), Ctx, Session, Attach discovery to an open browser session: the send guard on every request,…, Counts on the ctx of the latest attach to this page. (+3 more)

### Community 47 - "DiscoveryConfig"
Cohesion: 0.16
Nodes (31): DiscoveryConfig, Discovery-only settings., Discovery: an LLM agent learns a task once and the recorder saves it as a…, attach(), Route every request through a new send guard, open the control window. Re-run…, changed(), The pixels moved, or new text is on screen: a small answer ('Transfer…, make_session() (+23 more)

### Community 48 - "test_replay_wiring.py"
Cohesion: 0.14
Nodes (20): attach(), Session, Wire replay onto an open session and return its Ctx., _fake_session(), asyncio, MonkeyPatch, Path, attach (the replay setup cell), the guard's replay hooks, and R7: after… (+12 more)

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
Cohesion: 0.19
Nodes (18): replay_control(), takeover_text(), Ext, _modes(), asyncio, Take-over pieces and their timing (review focus 1): Done in the panel vs the…, The human pressed Pay (send held, its gate on top of the take-over), then Done…, Done in the panel (answer by mode) reaches the take-over even with a gate on… (+10 more)

### Community 53 - "test_extension.py"
Cohesion: 0.19
Nodes (14): Control, Ext, asyncio, parametrize, The hand-back extension's toolbar button: its service worker only, never the…, The extension's service worker: a click counter and a badge., test_a_click_count_rise_returns(), test_a_missing_or_broken_extension_gives_none() (+6 more)

### Community 54 - "Session"
Cohesion: 0.15
Nodes (20): BrowserContext, Playwright, playwright_async_api, Playwright, no decisions: the open session, the site lock, our own input,…, _alive(), check_viewport(), close_session(), _extension() (+12 more)

### Community 55 - "Look"
Cohesion: 0.10
Nodes (45): Cols, _columns(), clean_label(), column_header(), headings(), is_header(), is_word(), merged_label() (+37 more)

### Community 56 - "Capability"
Cohesion: 0.14
Nodes (26): _ask(), ask_inputs(), ask_option(), _ask_rows(), given_inputs(), input_type(), _missing_crops(), mistyped() (+18 more)

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
Cohesion: 0.14
Nodes (23): _click(), _clicks(), _go(), _names(), _nav(), _noop_click(), _paths(), Recorder behaviour pinned by live runs: detours, 404s, login clicks kept, no-op… (+15 more)

### Community 62 - "test_middleware.py"
Cohesion: 0.16
Nodes (22): AIMessage, Ctx, 3.5: keep the text the model wrote before its tool calls as ``ctx.run.why``…, RecordWhy, _answer(), asyncio, parametrize, SimpleNamespace (+14 more)

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
Nodes (19): base64, Question, ControlWindow, discovery_control(), _img(), Protocol, ControlWindow: our own "Agent control" tab, the only place a human answers.…, Answers the question on top. Closing the window (None) answers every one: fail… (+11 more)

### Community 67 - "2. Components"
Cohesion: 0.12
Nodes (15): 1. Diagram, 2. Components, 3. Step types, 4. Worked example: ParaBank login + read balance, 5. Notes, Actor, Artifact (made by discovery, not replay), Browser setup (+7 more)

### Community 68 - "HeldPage"
Cohesion: 0.13
Nodes (8): DoneWhileSending, FormRoute, HeldPage, HeldRoute, NeverAnsweredGate, Like Playwright: while a form POST (a navigation) is held, `page.screenshot()`…, The human clicks Done just as their form POST is held: the gate must still show…, The human clicks Done while their own send's Gate 1 is still open and never…

### Community 69 - "Pure-Visual Discovery Notebook: Build Plan"
Cohesion: 0.09
Nodes (22): 10. Open risks, 1. Global constraints (every task must follow these), 2. Review focus (inputs no spec line covers, but likely to bite), 3. What already exists (reuse, or its visual version), 3a. How the agent is built today (`agent.ipynb` STEP 4, `src/cua/agent.py`), 3b. Existing handoff rules: when a human is called in, 3c. Existing tools → the new tools, 4. New dependencies (checked on PyPI, 2026-09-28) (+14 more)

### Community 71 - "SiteLock"
Cohesion: 0.16
Nodes (12): CdpSender, Protocol, SiteLock: the site tab ignores all real input (CDP…, The one method of a Playwright ``CDPSession`` the lock uses. ``params`` is a…, The site tab ignores all real input (CDP). Lifted only around our own action or…, SiteLock, FakeCdp, asyncio (+4 more)

### Community 72 - "discovery/context.py"
Cohesion: 0.13
Nodes (20): dataclasses, _count_start(), Ctx: what every discovery tool is given, plus the page wrappers the tools…, An evidence screenshot: short timeout, None on failure (never hangs on a held…, The start event's look bookkeeping: the page a run begins on, and how often…, snap(), DiscoveryRun: one discovery run's working state (was the notebook's…, Every value typed, entered, given or sent this run, plus the secrets (in memory… (+12 more)

### Community 73 - "ReplayResult"
Cohesion: 0.16
Nodes (10): What a replay run returns: its Status, the Stop that ends a run early, and…, R17 run statuses. A member is a plain str, so ``Status.SUCCESS == "SUCCESS"``., ReplayResult, Status, StrEnum, ReplayResult summary/outputs_line, Stop, and the Status values., test_partial_outputs_line_when_not_success(), test_result_defaults() (+2 more)

### Community 74 - "SiteProfile"
Cohesion: 0.11
Nodes (16): Look up a secret by NAME. Raises on an unknown name or an empty/missing value.…, Secret name -> value from `.env` ("" when unset), as the notebook's SECRETS., Everything site-specific, loaded from ``configs/<name>.yaml``. Secrets: env…, Secret name -> env var name., resolve_secret(), secret_values(), SiteProfile, Ctx (+8 more)

### Community 75 - "engine.py"
Cohesion: 0.10
Nodes (46): Drift, Exception, action_allowed(), _cleanup_step(), error_page(), finish(), is_cleanup(), judge() (+38 more)

### Community 77 - "test_routing.py"
Cohesion: 0.06
Nodes (52): ChatAnthropic, langchain_agents_middleware, ModelKind, ModuleType, os, build_routing_middleware(), Classifier, confidence_gate() (+44 more)

### Community 79 - "guard.py"
Cohesion: 0.13
Nodes (22): run_goal: one goal through the discovery agent (moved from discovery.py…, after_login_click(), _checked(), gate_click(), log(), mark_stuck(), note_call(), Ctx (+14 more)

### Community 80 - "Box"
Cohesion: 0.11
Nodes (23): Box, Live: row_key 'Transfer Funds' (menu), column 'Accounts Overview' (title);…, test_the_first_accounts_balance_never_uses_the_menu_or_the_title(), _form(), _look(), _png(), ndarray, crop_box/cut_crop/read_near/element_at/screens_same: the crop and comparison… (+15 more)

### Community 81 - "test_import_rules.py"
Cohesion: 0.29
Nodes (13): _cua_imports(), _layer_files(), _module(), parametrize, Path, The package's import rule (docs/PRODUCTIONIZE_PLAN.md section 1), read from…, The top-level cua subpackage of every ``cua.*`` import (``import`` or ``from``)., Guard the guard: a planted forbidden import is caught in both spellings. (+5 more)

### Community 82 - "test_prompt.py"
Cohesion: 0.12
Nodes (9): The discovery agent: system prompt, middleware, optional TypeSafe routing, and…, The discovery agent's system prompt, verbatim from…, _capture(), MonkeyPatch, build_agent: the notebook's create_deep_agent call, with routing appended only…, test_build_agent_wires_the_notebooks_agent(), test_routing_is_appended_after_the_notebooks_middleware(), test_the_page_path_is_read_live() (+1 more)

### Community 84 - "HumanControl"
Cohesion: 0.22
Nodes (4): Frame, HumanControl, Ctx, Takes over; while 'in control', the human opens a page and sends a form.

### Community 85 - "build_tools"
Cohesion: 0.15
Nodes (17): AsyncFunctionDef, inspect, build_tools(), BaseTool, Ctx, observe, click, type_text, type_secret, select_option, scroll, open_path,…, test_the_prompt_lists_every_tool(), test_every_built_tool_has_an_action_type() (+9 more)

### Community 86 - "cua"
Cohesion: 0.50
Nodes (3): cua, Read order, Rules

### Community 87 - "pytest"
Cohesion: 0.17
Nodes (10): pytest, _fake_llm_keys(), fixture, MonkeyPatch, Suite-wide: never let a real LLM key from `.env` reach a test (cua.config loads…, A fake direct-Anthropic key so code that builds a chat model works offline; no…, parametrize, Path (+2 more)

### Community 88 - "cua.schema"
Cohesion: 0.50
Nodes (3): cua.schema, Read order, What may NOT go here

### Community 89 - "rescue.py"
Cohesion: 0.12
Nodes (19): Asker, hand_back(), Future, Lock, Protocol, The shared take-over loop pieces. Each side's own take-over stays with that…, Done on the toolbar button or in the take-over panel hands back. No reminders…, A send the human started is still held: its gate is on screen next; wait for… (+11 more)

### Community 90 - "handoff/__init__.py"
Cohesion: 0.17
Nodes (18): _in_control(), The take-over itself: badge YOU, unlock the site, wait for Done (panel or…, _takeover_note(), Answerable, button_clicked(), ext_call(), Extension, handback_button() (+10 more)

### Community 91 - "test_capability.py"
Cohesion: 0.21
Nodes (10): _data(), parametrize, Path, cua.schema.Capability loads every saved artifact and refuses an unknown schema…, test_a_target_needs_a_findable_rung(), test_a_wrong_schema_version_is_refused(), test_an_unknown_key_is_refused(), test_every_saved_artifact_loads() (+2 more)

### Community 92 - "test_goal.py"
Cohesion: 0.12
Nodes (25): Agent, Ctx, Protocol, What run_goal needs of the compiled deep agent., The deadline passed: end the run STUCK, keeping what the agent did so far., New run on a fresh thread; pass an earlier thread_id to resume it with a next…, run_goal(), _start() (+17 more)

### Community 93 - "human.py"
Cohesion: 0.15
Nodes (23): Field, choose_option(), list_options(), Every option of the dropdown at this point ([] if it is not a dropdown)., Select the first option containing this text in the dropdown at (or next to)…, Every shape the whole value matches, in precedence order. Safe to log: names,…, shapes_of(), select_option's body once the option is the agent's to pick: choose it, log its… (+15 more)

### Community 94 - "test_value_types.py"
Cohesion: 0.36
Nodes (7): parametrize, Path, cua.schema.value_types matches both notebooks' SHAPES/TYPES exactly., SHAPES and TYPES as each notebook defines them (TYPES spreads SHAPES, so exec…, _tables(), test_tables_equal_the_notebooks(), test_value_matches_type()

### Community 95 - "locate"
Cohesion: 0.21
Nodes (21): locate(), Path, Target, (point, rung) from the first rung that hits, or None., _dup_target(), _look(), Path, Target (+13 more)

### Community 96 - "hosts.py"
Cohesion: 0.25
Nodes (4): cua: shared config and the LLM model factory (direct Anthropic or an optional…, Which hosts the browser may reach (D15). The allowlist itself lives in the site…, host_allowed: only the site's own hosts (D15); about:blank always., test_only_allowed_hosts_and_blank()

### Community 97 - "decode"
Cohesion: 0.17
Nodes (18): crop_box(), cut_crop(), _ink(), input_box(), Crops around one point: find the element there, crop around it, read text near…, New ink appeared INSIDE the input box (text, or a password's dots). A click…, Crop around the target, with every other piece of text blanked out., Pixels around the point changed. Catches password dots that OCR cannot read. (+10 more)

### Community 98 - "test_human.py"
Cohesion: 0.12
Nodes (45): goal_value(), The value the goal already gives for this field, or None. Code backstop for the…, Q21: the one time the site unlocks for a human. What they did is kept as…, take_over(), _answer(), _badge(), _ctx(), _dirty() (+37 more)

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
Cohesion: 0.21
Nodes (28): BaseModel, _navigate(), Step, Event log -> ``Capability``: steps, inputs, outputs and secrets come from the…, The {{input}} names the steps use, in order. {{secret:x}} is not an input., ``to_step``'s open_path branch, unchanged., step_inputs(), target() (+20 more)

### Community 107 - "types.py"
Cohesion: 0.13
Nodes (17): input_name(), event_shapes(), input_types(), pick_type(), Typed inputs: an input's type is inferred from the SHAPES of the values typed…, One input's type from each of its values' shapes. Unknown shapes (None) ->…, input name -> the shapes of the value it took in this event (None: not logged)., input name -> its inferred type, from the events that became steps. (+9 more)

### Community 108 - "act.py"
Cohesion: 0.33
Nodes (15): make_act_tools(), _make_click(), _make_select_option(), _make_type_secret(), _make_type_text(), BaseTool, Ctx, The tools that act on the page: click, type_text, type_secret, select_option.… (+7 more)

### Community 109 - "test_evidence.py"
Cohesion: 0.34
Nodes (14): _artifact(), Path, save_evidence: one masked folder per run. No run value or secret is ever…, Live: a form value of '1' made 'version: 1' and 's1.png' look like a leak, so a…, _save(), test_a_failed_run_still_writes_evidence(), test_a_short_number_typed_this_run_does_not_flag_the_artifacts_own_numbers(), test_an_artifact_holding_a_run_value_is_refused() (+6 more)

### Community 110 - "make_ctx"
Cohesion: 0.12
Nodes (35): make_ctx(), Ctx, Session, A discovery ``Ctx`` over fakes, built like ``attach`` but with no page wiring., helped(), _only(), asyncio, fixture (+27 more)

### Community 111 - "._held"
Cohesion: 0.29
Nodes (3): Request, Gate 1: Approve, or Edit = back to the form with every value, then again.…, RouteLike

### Community 112 - "test_session.py"
Cohesion: 0.24
Nodes (11): LivePage, _png(), asyncio, MonkeyPatch, Path, open_session reuses a live session (a notebook re-run must not leak a browser),…, _session(), test_a_live_existing_session_is_returned_unchanged() (+3 more)

### Community 113 - "Replay notebook plan"
Cohesion: 0.33
Nodes (5): Decisions made here (review), Open questions for the user, Replay notebook plan, Sections, Tasks

### Community 114 - "Ctx"
Cohesion: 0.13
Nodes (28): act(), Ctx, look(), Page, Unlock the site tab, run our own input steps, relock, settle, take a new look., The only screenshot path; stores the look on the run., to_page(), _press() (+20 more)

### Community 115 - "config.py"
Cohesion: 0.19
Nodes (13): dotenv, model_validator, _actions(), _find_root(), OutcomeRule, _outcomes(), Path, Shared configuration: the site profile, browser/discovery/replay settings, and… (+5 more)

### Community 116 - "crop"
Cohesion: 0.21
Nodes (13): canvas(), crop(), into_box(), Step, Crop around the target, every other text blanked (sized to the current canvas)., Focus the site tab, click the box, clear it, type (see…, The size of the image the model is looking at right now., Result (+5 more)

### Community 117 - "test_dropdowns.py"
Cohesion: 0.22
Nodes (15): _approve(), HeldPage, _logged(), asyncio, Ctx, A dropdown the send carries becomes a Select step; the guard hooks never read a…, Page reads (a held send blocks them); bring_to_front is the control window's…, Human values (zip, phone, SSN) are not in the goal: no mismatch form, no… (+7 more)

### Community 118 - "load_capability"
Cohesion: 0.16
Nodes (25): load_capability(), load_outcomes(), Path, The capability and the folder its crop paths are relative to., The capability's own `outcomes:` [{text, status, meaning}], else the site's…, The first rule whose text (whole words, any case) appeared on screen with this…, seen_outcome(), fixture (+17 more)

### Community 119 - "one_at_a_time"
Cohesion: 0.29
Nodes (12): P, one_at_a_time(), One tool call at a time (``ctx.run.act_lock``), counted against the step budget…, _make_ask_human(), _make_finish(), make_human_tools(), _make_request_missing_values(), BaseTool (+4 more)

### Community 120 - "hide_secrets"
Cohesion: 0.20
Nodes (6): hide_secrets(), Each secret value -> ``<name>``. ``secrets`` maps a secret NAME to its value., pretty(), address.zipCode' -> 'Address zip code' (for the human; the key itself is kept)., test_hide_secrets_replaces_each_value_by_its_name(), test_pretty()

### Community 121 - "_FakeModel"
Cohesion: 0.18
Nodes (7): _FakeModel, asyncio, Stands in for a LangChain chat model: no network, records the prompt., asyncio, test_describe_names_the_table_outputs(), _Structured, test_describe_asks_the_given_model_with_labels_and_input_names_only()

### Community 122 - "test_table.py"
Cohesion: 0.26
Nodes (10): _is_header(), _look(), The shared OCR table reader: parity between cua.vision.table and both…, tests/replay/test_table_replay.py's own SHARED set is the contract this module…, _read(), test_a_table_that_runs_to_the_bottom_of_the_screen_may_continue(), test_a_three_column_table_is_read_into_rows_even_when_cells_are_a_few_px_off(), test_only_the_asked_columns_are_kept_and_the_row_limit_holds() (+2 more)

### Community 123 - "discovery/evidence.py"
Cohesion: 0.17
Nodes (21): artifact_texts(), _copy_capability(), _events(), _folder(), Ctx, OcrFn, Path, Redact (+13 more)

### Community 124 - "FakePage"
Cohesion: 0.25
Nodes (4): FakePage, The site page: any call made on it for the button is a bug., SitePage, FakePage

### Community 125 - "fakes.py"
Cohesion: 0.10
Nodes (11): ActTab, blank_png(), FakeInput, FakeLock, Shared offline fakes for the ported test suite (tests/unit, tests/integration).…, A fake ``cua.browser.SiteLock``: ``open()`` records unlock/lock, nothing else., A fake ``page.mouse`` / ``page.keyboard``: every call is recorded as ``(name,…, A site tab the act/nav tools drive: ``mouse``/``keyboard`` record into… (+3 more)

### Community 127 - "BrowserConfig"
Cohesion: 0.23
Nodes (10): BrowserConfig, Settings shared by discovery and replay (the same page size at both, Q10)., Path, Discovery's saved artifact runs in replay unchanged: build -> save -> load ->…, test_crop_paths_resolve_to_saved_files(), test_rung2_offset_hits_the_point_discovery_acted_on(), test_saved_artifact_loads_as_is(), test_steps_dispatch_to_replay_handlers() (+2 more)

### Community 128 - "pathlib"
Cohesion: 0.18
Nodes (5): json, pathlib, The hand-back extension never touches any site: no content scripts, no host…, Frozen notebook sources for the parity tests (step 10 replaced the notebooks…, Guard: no site value lives in src/. Site values belong in configs/<site>.yaml…

### Community 129 - "bind_control"
Cohesion: 0.31
Nodes (6): bind_control(), ControlTab, Protocol, Bind the control tab to the current :class:`ControlWindow`, once per tab. A…, The Playwright calls binding makes on the control tab., Point the control tab's buttons and its close at ``control``. Re-run safe: the…

### Community 130 - "test_saved_artifacts.py"
Cohesion: 0.31
Nodes (7): MonkeyPatch, parametrize, Path, Every capability saved in the top-level artifacts/ folder (Decision 6) loads in…, test_a_saved_artifact_loads_in_replay(), test_a_saved_artifact_round_trips(), test_the_old_artifacts_folder_is_gone()

### Community 131 - "Response"
Cohesion: 0.19
Nodes (8): _note_latest(), note_response(), Protocol, The Playwright ``Response`` fields note_response reads., The once-per-page listener: note on the ctx of the latest attach to this page., Keep the main document's HTTP status (not sub-resources, not iframes)., _Request, Response

### Community 133 - "screen"
Cohesion: 0.32
Nodes (6): ``take_look`` always returns this look., screen(), AskStop, ectx(), pctx(), fixture

### Community 134 - "Route"
Cohesion: 0.25
Nodes (4): Req, Route, test_sends_are_noted_only_during_a_take_over(), test_the_gate_marks_a_human_approved_send()

### Community 135 - "choose_option_at_point"
Cohesion: 0.38
Nodes (7): Confirm, LookFn, choose_option_at_index(), choose_option_at_point(), Session, Select the first option containing this text in the dropdown at (or next to)…, Select this exact live option in the Nth <select> (``index``), else the one at…

### Community 137 - "test_read_helpers.py"
Cohesion: 0.47
Nodes (5): _look(), where / label_near / spot / page_texts: a point's label in words, never a…, Live bug: 'From account #' dropdown showing '74838' was saved as input…, test_a_dropdowns_own_number_is_never_its_label(), test_where_records_label_box_ordinal_offset_but_not_the_box_contents()

### Community 138 - "AST"
Cohesion: 0.50
Nodes (5): AST, _defs(), Path, ast.dump compare, ignoring docstrings -- the functions this step did not have…, test_the_no_global_table_functions_are_byte_identical_to_discoverys_source()

### Community 139 - "masked"
Cohesion: 0.50
Nodes (4): masked(), fixture, MonkeyPatch, The OCR mask is tested in tests/unit/safety; here: that every PNG goes through…

### Community 141 - "cua.discovery.agent"
Cohesion: 0.50
Nodes (3): cua.discovery.agent, Read order, What may NOT go here

## Knowledge Gaps
- **159 isolated node(s):** `MODES`, `manifest_version`, `name`, `version`, `description` (+154 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **17 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Look` connect `Look` to `FakeRoute`, `test_act.py`, `look.py`, `screen`, `test_input.py`, `FakeBox`, `test_dropdown.py`, `test_read_helpers.py`, `Ctx`, `DiscoveryRun`, `test_replay_rescue.py`, `ReplayConfig`, `steps.py`, `vision/__init__.py`, `make_replay_ctx`, `test_replay_steps.py`, `RefCounter`, `discovery/wiring.py`, `DiscoveryConfig`, `Session`, `FakeTab`, `test_screenshot.py`, `discovery/context.py`, `Box`, `human.py`, `locate`, `decode`, `test_human.py`, `act.py`, `Ctx`, `crop`, `test_dropdowns.py`, `test_table.py`, `fakes.py`, `BrowserConfig`?**
  _High betweenness centrality (0.060) - this node is a cross-community bridge._
- **Why does `BrowserConfig` connect `BrowserConfig` to `cli.py`, `FakeRoute`, `test_saved_artifacts.py`, `look.py`, `test_input.py`, `FakeBox`, `test_dropdown.py`, `test_replay_handback.py`, `test_config.py`, `make_replay_ctx`, `test_replay_steps.py`, `RefCounter`, `replay/context.py`, `cua/evidence.py`, `DiscoveryConfig`, `test_takeover_loop.py`, `test_extension.py`, `Session`, `Capability`, `FakeTab`, `test_screenshot.py`, `SiteProfile`, `Box`, `handoff/__init__.py`, `decode`, `test_session.py`, `config.py`, `load_capability`, `FakePage`, `fakes.py`?**
  _High betweenness centrality (0.049) - this node is a cross-community bridge._
- **Why does `Ctx` connect `Ctx` to `FakeRoute`, `Response`, `test_act.py`, `screen`, `Route`, `test_replay_inputs.py`, `Tab`, `agent/build.py`, `DiscoveryRun`, `test_replay_rescue.py`, `test_replay_handback.py`, `test_replay_table.py`, `redact.py`, `test_replay_steps.py`, `discovery/wiring.py`, `DiscoveryConfig`, `test_replay_wiring.py`, `Session`, `Look`, `FakeTab`, `test_middleware.py`, `HeldPage`, `ScriptedControl`, `discovery/context.py`, `SiteProfile`, `GateControl`, `guard.py`, `HumanControl`, `rescue.py`, `test_goal.py`, `human.py`, `test_human.py`, `act.py`, `crop`, `test_dropdowns.py`, `discovery/evidence.py`, `FakePage`, `fakes.py`, `BrowserConfig`?**
  _High betweenness centrality (0.044) - this node is a cross-community bridge._
- **Are the 27 inferred relationships involving `Look` (e.g. with `Ctx` and `DiscoveryRun`) actually correct?**
  _`Look` has 27 INFERRED edges - model-reasoned connections that need verification._
- **Are the 59 inferred relationships involving `Ctx` (e.g. with `LatestScreenshotOnly` and `NoopAnthropicPromptCachingMiddleware`) actually correct?**
  _`Ctx` has 59 INFERRED edges - model-reasoned connections that need verification._
- **Are the 36 inferred relationships involving `BrowserConfig` (e.g. with `Session` and `Answerable`) actually correct?**
  _`BrowserConfig` has 36 INFERRED edges - model-reasoned connections that need verification._
- **Are the 30 inferred relationships involving `ReplayConfig` (e.g. with `Ctx` and `_Request`) actually correct?**
  _`ReplayConfig` has 30 INFERRED edges - model-reasoned connections that need verification._