# Graph Report - BankerAgent  (2026-10-02)

## Corpus Check
- 234 files · ~240,976 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 2863 nodes · 8260 edges · 126 communities (112 shown, 14 thin omitted)
- Extraction: 93% EXTRACTED · 7% INFERRED · 0% AMBIGUOUS · INFERRED: 556 edges (avg confidence: 0.63)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `069000c4`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- cli.py
- FakeRoute
- Productionize Plan: notebooks → `src/cua/` package
- test_act.py
- Evidence README
- guard.py
- test_recorder_types.py
- test_replay_inputs.py
- test_input.py
- re
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
- test_recorder_runs.py
- ReplayConfig
- recorder/__init__.py
- steps.py
- masked_outputs
- integration/conftest.py
- redact.py
- test_replay_table.py
- test_session.py
- test_notebooks.py
- build_capability
- make_replay_ctx
- test_replay_evidence.py
- CLAUDE.md (project instructions)
- test_replay_steps.py
- RefCounter
- manifest.json
- langchain_tools
- Request
- test_human_tools.py
- look.py
- replay/evidence.py
- load
- AST
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
- routing.py
- FakeTab
- rescue.py
- vision/__init__.py
- langgraph_types
- test_screenshot.py
- Discovery decisions
- 2. Each box, with an example
- safety/__init__.py
- ControlWindow
- 2. Components
- canvas.py
- Pure-Visual Discovery Notebook: Build Plan
- pytest
- SiteLock
- .awrap_model_call
- test_eval.py
- fakes.py
- engine.py
- test_build.py
- test_routing.py
- FakeWin
- eval.py
- Ctx
- test_import_rules.py
- test_prompt.py
- copy
- prompt.py
- build_tools
- cua
- schema/events.py
- cua.schema
- ReplayResult
- handoff/__init__.py
- test_capability.py
- test_goal.py
- human_fills
- test_value_types.py
- locate
- llm.py
- Box
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
- one_at_a_time
- test_evidence.py
- make_ctx
- ._held
- Replay notebook plan
- BrowserConfig
- pathlib
- test_dropdowns.py
- load_capability
- test_recorder_reads.py
- cua/__init__.py
- discovery/evidence.py
- confidence_gate
- background.js
- discovery/wiring.py
- test_saved_artifacts.py
- mk_look
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
- `test_an_old_select_without_an_index_still_loads()` --calls--> `Select`  [INFERRED]
  tests/unit/discovery/recorder/test_recorder_reads.py → src/cua/schema/capability.py
- `test_meta_is_loose()` --calls--> `CapabilityMeta`  [INFERRED]
  tests/unit/schema/test_capability.py → src/cua/schema/capability.py

## Import Cycles
- 3-file cycle: `src/cua/discovery/tools/__init__.py -> src/cua/discovery/tools/act.py -> src/cua/discovery/tools/guard.py -> src/cua/discovery/tools/__init__.py`
- 3-file cycle: `src/cua/discovery/tools/__init__.py -> src/cua/discovery/tools/nav.py -> src/cua/discovery/tools/guard.py -> src/cua/discovery/tools/__init__.py`
- 3-file cycle: `src/cua/discovery/tools/__init__.py -> src/cua/discovery/tools/read.py -> src/cua/discovery/tools/guard.py -> src/cua/discovery/tools/__init__.py`
- 3-file cycle: `src/cua/discovery/tools/guard.py -> src/cua/discovery/tools/human.py -> src/cua/discovery/tools/observe.py -> src/cua/discovery/tools/guard.py`
- 3-file cycle: `src/cua/discovery/tools/__init__.py -> src/cua/discovery/tools/human.py -> src/cua/discovery/tools/observe.py -> src/cua/discovery/tools/__init__.py`
- 3-file cycle: `src/cua/discovery/tools/__init__.py -> src/cua/discovery/tools/act.py -> src/cua/discovery/tools/observe.py -> src/cua/discovery/tools/__init__.py`
- 3-file cycle: `src/cua/discovery/tools/__init__.py -> src/cua/discovery/tools/nav.py -> src/cua/discovery/tools/observe.py -> src/cua/discovery/tools/__init__.py`
- 4-file cycle: `src/cua/discovery/tools/__init__.py -> src/cua/discovery/tools/human.py -> src/cua/discovery/tools/observe.py -> src/cua/discovery/tools/guard.py -> src/cua/discovery/tools/__init__.py`
- 4-file cycle: `src/cua/discovery/tools/__init__.py -> src/cua/discovery/tools/act.py -> src/cua/discovery/tools/observe.py -> src/cua/discovery/tools/guard.py -> src/cua/discovery/tools/__init__.py`
- 4-file cycle: `src/cua/discovery/tools/__init__.py -> src/cua/discovery/tools/nav.py -> src/cua/discovery/tools/observe.py -> src/cua/discovery/tools/guard.py -> src/cua/discovery/tools/__init__.py`
- 4-file cycle: `src/cua/discovery/tools/__init__.py -> src/cua/discovery/tools/act.py -> src/cua/discovery/tools/human.py -> src/cua/discovery/tools/observe.py -> src/cua/discovery/tools/__init__.py`
- 5-file cycle: `src/cua/discovery/tools/__init__.py -> src/cua/discovery/tools/act.py -> src/cua/discovery/tools/human.py -> src/cua/discovery/tools/observe.py -> src/cua/discovery/tools/guard.py -> src/cua/discovery/tools/__init__.py`
- 5-file cycle: `src/cua/discovery/tools/__init__.py -> src/cua/discovery/tools/act.py -> src/cua/discovery/tools/guard.py -> src/cua/discovery/tools/human.py -> src/cua/discovery/tools/observe.py -> src/cua/discovery/tools/__init__.py`
- 5-file cycle: `src/cua/discovery/tools/__init__.py -> src/cua/discovery/tools/nav.py -> src/cua/discovery/tools/guard.py -> src/cua/discovery/tools/human.py -> src/cua/discovery/tools/observe.py -> src/cua/discovery/tools/__init__.py`
- 5-file cycle: `src/cua/discovery/tools/__init__.py -> src/cua/discovery/tools/read.py -> src/cua/discovery/tools/guard.py -> src/cua/discovery/tools/human.py -> src/cua/discovery/tools/observe.py -> src/cua/discovery/tools/__init__.py`

## Communities (126 total, 14 thin omitted)

### Community 0 - "cli.py"
Cohesion: 0.13
Nodes (27): argparse, Namespace, _cap_name(), check_eval(), _close(), default_site(), discover(), _load_cap() (+19 more)

### Community 1 - "FakeRoute"
Cohesion: 0.10
Nodes (11): FakeControl, FakePage, FakeRoute, A fake discovery/replay ``CONTROL`` surface (what ``ControlWindow`` presents).…, A fake ``playwright.async_api.Route``: records every…, A fake ``playwright.async_api.Page``. Every awaited method is recorded in…, asyncio, Tests for the shared offline fakes in tests/fakes.py (TDD: written before the… (+3 more)

### Community 2 - "Productionize Plan: notebooks → `src/cua/` package"
Cohesion: 0.12
Nodes (16): 10. Line-count offenders (today), 1. Package tree, 2. De-duplication (checked by AST diff of both notebooks), 3. State: globals → explicit objects, 4. Async and typing, 5. Notebooks after the move, 6. Tests, 7. ML-engineering practices (kept small) (+8 more)

### Community 3 - "test_act.py"
Cohesion: 0.06
Nodes (87): Items, (value, pattern) for an extract: the whole box when it is exactly the type,…, value_in_box(), blank_png(), make_look(), A plain PNG of this canvas size (canvas/crops decode the look's png)., A look whose elements are numbered 1.. in order (ref, text, box)., Driven (+79 more)

### Community 5 - "guard.py"
Cohesion: 0.08
Nodes (36): An evidence screenshot: short timeout, None on failure (never hangs on a held…, snap(), Ctx, run_goal: one goal through the discovery agent (moved from discovery.py…, The deadline passed: end the run STUCK, keeping what the agent did so far., _start(), _timed_out(), select_option's body once the option is the agent's to pick: choose it, log its… (+28 more)

### Community 6 - "test_recorder_types.py"
Cohesion: 0.23
Nodes (14): Typed inputs: the recorder infers each input's type from the shapes of the…, Older logs (and any tool that did not log shapes) never guess a type., test_a_plain_whole_number_is_a_number_so_decimals_pass_replay_later(), test_a_value_with_no_shape_is_string(), test_all_currency_values_make_a_currency_input(), test_an_event_without_shapes_is_string(), test_human_entry_is_typed_too(), test_mixed_shapes_fall_back_to_their_common_type() (+6 more)

### Community 7 - "test_replay_inputs.py"
Cohesion: 0.12
Nodes (33): type_(), _cap(), ClearPage, env(), FakeForm, FakePage, asyncio, Ctx (+25 more)

### Community 8 - "test_input.py"
Cohesion: 0.09
Nodes (25): act(), into_box(), Lock, Session, Step, Unlock the site tab, run our own input steps, relock, settle, take a new look., Focus the site tab, click the box, clear what is in it, type. Retries replace…, FakeBox (+17 more)

### Community 9 - "re"
Cohesion: 0.07
Nodes (45): AIMessage, CompiledStateGraph, deepagents, Handler, langgraph_checkpoint_memory, re, build_agent(), BaseChatModel (+37 more)

### Community 10 - "test_dropdown.py"
Cohesion: 0.07
Nodes (40): BaseException, Confirm, LookFn, choose_option_at_index(), choose_option_at_point(), list_options(), Dropdown, Page (+32 more)

### Community 12 - "Replay decisions"
Cohesion: 0.08
Nodes (23): R10: where the compile step lives — DECIDED, R11: why compile, if `response_format` exists? — PROPOSED, R12: what each step type compiles to — PROPOSED, R13: target schema — PROPOSED, R14: what rung 2 needs that discovery doesn't record — DONE, R15: auto-approve at replay — PROPOSED, R16: dead ends and retries at compile — PROPOSED, R17: replay result statuses — PROPOSED (+15 more)

### Community 16 - "DiscoveryRun"
Cohesion: 0.12
Nodes (18): Saved, The current run (the one the send guard serves)., DiscoveryRun, What the human gave: the goal and every answer (the send guard's mismatch text)., Every saved text, table cells and dropdown options included (evidence masking…, Banking: values live only for the run. Keep the log (labels only), drop the…, saved_texts(), wipe() (+10 more)

### Community 17 - "test_cli.py"
Cohesion: 0.13
Nodes (31): _cap_file(), _fake_session(), _patch_session(), CaptureFixture, MonkeyPatch, parametrize, Path, SimpleNamespace (+23 more)

### Community 18 - "test_replay_engine.py"
Cohesion: 0.21
Nodes (44): cap(), click(), extract(), _finish(), _login_cap(), _no_snap(), _only(), _pcap() (+36 more)

### Community 19 - "test_replay_rescue.py"
Cohesion: 0.06
Nodes (44): The guard keeps its own reference to the control window: swap both., set_control(), DoneWhileSending, _env(), _fail_clicks(), FormRoute, Frame, GateControl (+36 more)

### Community 20 - "test_llm.py"
Cohesion: 0.19
Nodes (12): _clean_env(), fixture, MonkeyPatch, Offline tests for `cua.llm.make_chat_model`. No network, no real key. Direct…, test_a_base_url_in_the_env_never_redirects(), test_ca_bundle_passthrough(), test_direct_anthropic(), test_existing_ssl_cert_file_wins() (+4 more)

### Community 21 - "test_replay_handback.py"
Cohesion: 0.14
Nodes (22): FakePage, _bctx(), Ext, Human, PanelDone, asyncio, Ctx, parametrize (+14 more)

### Community 22 - "config.py"
Cohesion: 0.07
Nodes (43): dotenv, _actions(), _find_root(), load_site(), OutcomeRule, _outcomes(), Path, Shared configuration: the site profile, browser/discovery/replay settings, and… (+35 more)

### Community 23 - "test_recorder_runs.py"
Cohesion: 0.14
Nodes (23): _click(), _clicks(), _go(), _names(), _nav(), _noop_click(), _paths(), Recorder behaviour pinned by live runs: detours, 404s, login clicks kept, no-op… (+15 more)

### Community 24 - "ReplayConfig"
Cohesion: 0.13
Nodes (30): SameTextLike, Replay-only settings., ReplayConfig, Replay: runs a capability saved by discovery with plain code, no LLM (step 4:…, fill(), Put inputs into `{{name}}`. `{{secret:x}}` stays as it is: secrets go in only…, anchor_point(), find_template() (+22 more)

### Community 25 - "recorder/__init__.py"
Cohesion: 0.07
Nodes (55): check_savable(), Raise NotSaved before any model call when this run cannot become a capability., ``build_capability``'s refusals, unchanged: a leaked value, a blind dropdown,…, _refuse(), checkpoint(), The capability's checkpoint: the text replay must see to call the run a…, C: after a send, the page's own response proves success (the agent's proof only…, field_area() (+47 more)

### Community 26 - "steps.py"
Cohesion: 0.09
Nodes (51): Point, changed(), choose_option(), do_click(), do_extract(), do_extract_options(), do_extract_table(), do_navigate() (+43 more)

### Community 27 - "masked_outputs"
Cohesion: 0.33
Nodes (6): masked_outputs(), JsonValue, Names and shape only: a value is ***, a table keeps its rows and columns, every…, parametrize, test_masked_outputs_hide_every_option(), test_masked_outputs_keep_the_shape()

### Community 29 - "redact.py"
Cohesion: 0.10
Nodes (30): Pattern, mask_png(), _num(), OcrFn, Value masking: ``norm``, ``is_sensitive``, ``hide_secrets``, ``redactor``,…, text -> text with every value masked. Numbers match however they are written…, Black out every OCR box whose text holds a run value. A clean image is written…, redactor() (+22 more)

### Community 30 - "test_replay_table.py"
Cohesion: 0.23
Nodes (17): _cap(), _defs(), Page, asyncio, Ctx, MonkeyPatch, Path, do_extract_table: find the header by its label, read the rows with discovery's… (+9 more)

### Community 31 - "test_session.py"
Cohesion: 0.24
Nodes (11): LivePage, _png(), asyncio, MonkeyPatch, Path, open_session reuses a live session (a notebook re-run must not leak a browser),…, _session(), test_a_live_existing_session_is_returned_unchanged() (+3 more)

### Community 32 - "test_notebooks.py"
Cohesion: 0.26
Nodes (16): Call, Module, _bind(), _code_cells(), _markdown(), _offline_namespace(), parametrize, Path (+8 more)

### Community 33 - "build_capability"
Cohesion: 0.08
Nodes (64): build_capability(), Steps, inputs and secrets come from the log only. The model's text cannot fail…, crops_for(), Path, save_artifact(), fixture, MonkeyPatch, saved() (+56 more)

### Community 34 - "make_replay_ctx"
Cohesion: 0.14
Nodes (29): make_replay_ctx(), A real Ctx (real SendGuard, real ReplayRun) over a fake page/control/lock.…, _extract(), _notebook_assign(), _options_cap(), OptionsPage, _pcap(), asyncio (+21 more)

### Community 35 - "test_replay_evidence.py"
Cohesion: 0.26
Nodes (19): Path, write_cap(), _all_text(), fake_ocr(), _png(), Ctx, fixture, Path (+11 more)

### Community 36 - "CLAUDE.md (project instructions)"
Cohesion: 0.12
Nodes (19): CLAUDE.md (project instructions), D101: labeled_value refuses a table-header resolution (general fix), D102: label_header/value_header flags ported into agent.py + cli.py capture path, D92: Evidence Capture Helpers (save_discovery_evidence/save_replay_evidence), D93: Pre-existing 02_artifact_schema.py IndexError bug, D95: Missing create_deep_agent import found live in BROWSER 12, D96: build_agent() goal_text vs given_text field-name bug, D97: cua replay --login flag + repeated Balance header trap (+11 more)

### Community 37 - "test_replay_steps.py"
Cohesion: 0.07
Nodes (42): encode(), NDArray, uint8, navigate(), select(), _click_env(), _form_png(), GotoPage (+34 more)

### Community 38 - "RefCounter"
Cohesion: 0.10
Nodes (29): RapidOCR, draw_numbered(), ocr(), ocr_engine(), NDArray, uint8, The shared RapidOCR engine, OCR itself, numbering and the numbered-box overlay.…, The RapidOCR engine, built once per process. rapidocr is imported here only, so… (+21 more)

### Community 39 - "manifest.json"
Cohesion: 0.11
Nodes (18): action, default_icon, default_title, background, service_worker, 128, 16, 32 (+10 more)

### Community 41 - "Request"
Cohesion: 0.11
Nodes (11): Protocol, The fields of a ``playwright.async_api.Request`` the guard reads., Request, ControlLike, GuardOptions, LookLike, Protocol, The two notebooks' differences, by name. human_in_lock: discovery reads… (+3 more)

### Community 42 - "test_human_tools.py"
Cohesion: 0.35
Nodes (13): _ctx(), asyncio, Ctx, MonkeyPatch, finish_business_outcome / request_missing_values / ask_human (the human-facing…, test_ask_human_asks_with_the_question(), test_finish_needs_the_proof_on_the_screen(), test_no_fields_given() (+5 more)

### Community 43 - "look.py"
Cohesion: 0.08
Nodes (26): dataclasses, Ctx, note_takeover_send(), Page, Request, Ctx: what every replay function takes first (session, run, settings, send…, LastRun, One replay run's working state: :class:`ReplayRun` (was the notebook's… (+18 more)

### Community 44 - "replay/evidence.py"
Cohesion: 0.10
Nodes (33): pydantic, _clean(), config_hash(), git_sha(), _png(), JsonValue, OcrFn, Path (+25 more)

### Community 45 - "load"
Cohesion: 0.16
Nodes (17): functools, dropdown_options(), mismatches(), _norm_num(), Dropdown, Values a send carries that the human never gave, and the dropdown choices to…, Numbers being sent that the human never gave, e.g. account 1450 vs 1400. Only…, For each key: the options of the page dropdown whose CURRENT value is exactly… (+9 more)

### Community 46 - "AST"
Cohesion: 0.50
Nodes (5): AST, _defs(), Path, ast.dump compare, ignoring docstrings -- the functions this step did not have…, test_the_no_global_table_functions_are_byte_identical_to_discoverys_source()

### Community 47 - "DiscoveryConfig"
Cohesion: 0.12
Nodes (38): DiscoveryConfig, Discovery-only settings., Discovery: an LLM agent learns a task once and the recorder saves it as a…, attach(), build_ctx(), _hooks(), new_run(), Ctx (+30 more)

### Community 48 - "test_replay_wiring.py"
Cohesion: 0.09
Nodes (21): Working values for one run. Replaced by a new one in ``replay``'s ``finally``…, What the mismatch check compares a send against (SendState)., ReplayRun, _fake_session(), asyncio, MonkeyPatch, Path, attach (the replay setup cell), the guard's replay hooks, and R7: after… (+13 more)

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
Cohesion: 0.14
Nodes (21): BrowserContext, Playwright, playwright_async_api, Playwright, no decisions: the open session, the site lock, our own input,…, Our own input into the locked site tab: ``act`` (unlock, run steps, relock,…, _alive(), check_viewport(), close_session() (+13 more)

### Community 55 - "Look"
Cohesion: 0.08
Nodes (56): Cols, _columns(), clean_label(), column_header(), headings(), is_header(), is_word(), label_near() (+48 more)

### Community 56 - "Capability"
Cohesion: 0.12
Nodes (30): Exception, _ask(), ask_inputs(), ask_option(), _ask_rows(), given_inputs(), input_type(), _missing_crops() (+22 more)

### Community 57 - "routing.py"
Cohesion: 0.17
Nodes (15): langchain_agents_middleware, ModuleType, build_routing_middleware(), Classifier, ModelRouter, _models(), AgentMiddleware, BaseChatModel (+7 more)

### Community 58 - "FakeTab"
Cohesion: 0.10
Nodes (6): ActTab, FakeTab, SimpleNamespace, A fake site or control tab with the Playwright calls discovery's wiring and…, A site tab the act/nav tools drive: ``mouse``/``keyboard`` record into…, A page script: recorded, answered by ``answer`` (default: no dropdown anywhere).

### Community 59 - "rescue.py"
Cohesion: 0.12
Nodes (19): Asker, hand_back(), Future, Lock, Protocol, The shared take-over loop pieces. Each side's own take-over stays with that…, Done on the toolbar button or in the take-over panel hands back. No reminders…, A send the human started is still held: its gate is on screen next; wait for… (+11 more)

### Community 60 - "vision/__init__.py"
Cohesion: 0.10
Nodes (32): Pixels -> text: screenshots, OCR, canvas math, crops, and the shared table…, append_rows(), cell_shape(), col_of(), column_spans(), like_rows(), The shared OCR table reader: discovery and replay use it to find a table's…, A table's end: a line that no longer looks like its rows (a footer, a menu, a… (+24 more)

### Community 62 - "test_screenshot.py"
Cohesion: 0.27
Nodes (9): _png(), asyncio, MonkeyPatch, take_look: page calls on the loop, the CPU part (OCR, drawing, encoding) in one…, ShotPage, test_page_width_reads_the_window_width(), test_snap_look_gives_the_look_png_or_none_on_timeout(), test_snap_png_passes_the_timeout_and_gives_none_on_error() (+1 more)

### Community 63 - "Discovery decisions"
Cohesion: 0.08
Nodes (24): Base decisions, Cuts, Discovery decisions, Q10: window size and zoom — DECIDED, Q11: notebook format — DECIDED, Q12: dropdowns — DECIDED, Q13: scrolling — DECIDED, Q14: private data in saved pictures — DECIDED (+16 more)

### Community 64 - "2. Each box, with an example"
Cohesion: 0.12
Nodes (15): 1. Diagram, 2. Each box, with an example, 3. All tools, 4. Step by step: one discovery run, 5. Notes, Browser (Playwright), Control window and site lock (Q-A), Discovery architecture (+7 more)

### Community 65 - "safety/__init__.py"
Cohesion: 0.13
Nodes (23): JsonObj, Which hosts the browser may reach (D15). The allowlist itself lives in the site…, Safety: what may leave the tab (hosts, the two send gates) and keeping values…, _flat(), _json(), pretty(), What a held request sends, and the same request rebuilt with edited values.…, Every value a request sends, from its query, a form body, or a JSON body… (+15 more)

### Community 66 - "ControlWindow"
Cohesion: 0.11
Nodes (19): base64, Question, ControlWindow, discovery_control(), _img(), Protocol, ControlWindow: our own "Agent control" tab, the only place a human answers.…, Answers the question on top. Closing the window (None) answers every one: fail… (+11 more)

### Community 67 - "2. Components"
Cohesion: 0.12
Nodes (15): 1. Diagram, 2. Components, 3. Step types, 4. Worked example: ParaBank login + read balance, 5. Notes, Actor, Artifact (made by discovery, not replay), Browser setup (+7 more)

### Community 68 - "canvas.py"
Cohesion: 0.17
Nodes (13): canvas_size(), NDArray, uint8, Canvas-pixel <-> page-point mapping: any window size or pixel density maps to…, Fit the screenshot inside the canvas. Returns it and canvas-pixel -> page-point…, The size of the image the model is looking at right now., to_canvas(), to_page() (+5 more)

### Community 69 - "Pure-Visual Discovery Notebook: Build Plan"
Cohesion: 0.09
Nodes (22): 10. Open risks, 1. Global constraints (every task must follow these), 2. Review focus (inputs no spec line covers, but likely to bite), 3. What already exists (reuse, or its visual version), 3a. How the agent is built today (`agent.ipynb` STEP 4, `src/cua/agent.py`), 3b. Existing handoff rules: when a human is called in, 3c. Existing tools → the new tools, 4. New dependencies (checked on PyPI, 2026-09-28) (+14 more)

### Community 70 - "pytest"
Cohesion: 0.17
Nodes (10): pytest, _fake_llm_keys(), fixture, MonkeyPatch, Suite-wide: never let a real LLM key from `.env` reach a test (cua.config loads…, A fake Anthropic key so code that builds a chat model works offline., parametrize, Path (+2 more)

### Community 71 - "SiteLock"
Cohesion: 0.16
Nodes (12): CdpSender, Protocol, SiteLock: the site tab ignores all real input (CDP…, The one method of a Playwright ``CDPSession`` the lock uses. ``params`` is a…, The site tab ignores all real input (CDP). Lifted only around our own action or…, SiteLock, FakeCdp, asyncio (+4 more)

### Community 72 - ".awrap_model_call"
Cohesion: 0.27
Nodes (8): page_name(), AsyncHandler, ModelRequest, ModelResponse, The URL's last path segment: no query, no ``;jsessionid=``, no trailing slash,…, What the classifier sees for a step: the page path + the last result's first…, step_state(), test_page_name_is_the_last_path_segment()

### Community 73 - "test_eval.py"
Cohesion: 0.18
Nodes (19): _cap(), _ok(), JsonValue, Path, cua.eval: summarize N replay results into a stability report. Pure, no browser., _row(), test_a_click_after_typing_an_input_sends_data(), test_a_step_that_left_its_first_choice_rung_is_a_fallback() (+11 more)

### Community 74 - "fakes.py"
Cohesion: 0.20
Nodes (5): FakeLock, Shared offline fakes for the ported test suite (tests/unit, tests/integration).…, A fake ``cua.browser.SiteLock``: ``open()`` records unlock/lock, nothing else., The handful of ``playwright.async_api.Request`` fields the project's code reads., _Request

### Community 75 - "engine.py"
Cohesion: 0.11
Nodes (44): Drift, R7: nothing kept. A fresh run, and the guard reads that one from now on., wipe(), action_allowed(), _cleanup_step(), error_page(), finish(), is_cleanup() (+36 more)

### Community 76 - "test_build.py"
Cohesion: 0.57
Nodes (6): _capture(), MonkeyPatch, build_agent: the notebook's create_deep_agent call, with routing appended only…, test_build_agent_wires_the_notebooks_agent(), test_routing_is_appended_after_the_notebooks_middleware(), test_the_page_path_is_read_live()

### Community 77 - "test_routing.py"
Cohesion: 0.20
Nodes (19): _choice(), FakeClassifier, FakeRequest, _model(), _names(), asyncio, CaptureFixture, MonkeyPatch (+11 more)

### Community 79 - "eval.py"
Cohesion: 0.14
Nodes (20): Histogram, EvalReport, fallback_steps(), _hist_line(), _histograms(), _is_fallback(), _output_stability(), JsonValue (+12 more)

### Community 80 - "Ctx"
Cohesion: 0.07
Nodes (72): The index (among the page's <select>s) of the native dropdown right under this…, select_under(), act(), canvas(), choose_option(), _count_start(), crop(), Ctx (+64 more)

### Community 81 - "test_import_rules.py"
Cohesion: 0.29
Nodes (13): _cua_imports(), _layer_files(), _module(), parametrize, Path, The package's import rule (docs/PRODUCTIONIZE_PLAN.md section 1), read from…, The top-level cua subpackage of every ``cua.*`` import (``import`` or ``from``)., Guard the guard: a planted forbidden import is caught in both spellings. (+5 more)

### Community 85 - "build_tools"
Cohesion: 0.16
Nodes (16): AsyncFunctionDef, inspect, build_tools(), BaseTool, Ctx, observe, click, type_text, type_secret, select_option, scroll, open_path,…, test_the_prompt_lists_every_tool(), _notebook_tools() (+8 more)

### Community 86 - "cua"
Cohesion: 0.50
Nodes (3): cua, Read order, Rules

### Community 87 - "schema/events.py"
Cohesion: 0.50
Nodes (3): _EventBase, The discovery event log entry: one tool call, as discovery's ``log()`` writes…, TypedDict

### Community 88 - "cua.schema"
Cohesion: 0.50
Nodes (3): cua.schema, Read order, What may NOT go here

### Community 89 - "ReplayResult"
Cohesion: 0.12
Nodes (15): What a replay run returns: its Status, the Stop that ends a run early, and…, R17 run statuses. A member is a plain str, so ``Status.SUCCESS == "SUCCESS"``., ReplayResult, Status, StrEnum, test_partial_label_when_not_success(), test_result_type_is_the_schema_one(), test_the_outputs_line_shows_rows() (+7 more)

### Community 90 - "handoff/__init__.py"
Cohesion: 0.20
Nodes (15): Answerable, button_clicked(), ext_call(), Extension, handback_button(), Future, Protocol, The hand-back extension (the Chrome toolbar button): its service worker, never… (+7 more)

### Community 91 - "test_capability.py"
Cohesion: 0.23
Nodes (9): _data(), parametrize, Path, cua.schema.Capability loads every saved artifact and refuses an unknown schema…, test_a_target_needs_a_findable_rung(), test_a_wrong_schema_version_is_refused(), test_an_unknown_key_is_refused(), test_every_saved_artifact_loads() (+1 more)

### Community 92 - "test_goal.py"
Cohesion: 0.14
Nodes (21): Agent, Protocol, What run_goal needs of the compiled deep agent., New run on a fresh thread; pass an earlier thread_id to resume it with a next…, run_goal(), FakeAgent, HangingAgent, asyncio (+13 more)

### Community 93 - "human_fills"
Cohesion: 0.23
Nodes (15): Field, _from_goal(), human_fills(), _make_ask_human(), _make_finish(), make_human_tools(), _make_request_missing_values(), _options() (+7 more)

### Community 94 - "test_value_types.py"
Cohesion: 0.36
Nodes (7): parametrize, Path, cua.schema.value_types matches both notebooks' SHAPES/TYPES exactly., SHAPES and TYPES as each notebook defines them (TYPES spreads SHAPES, so exec…, _tables(), test_tables_equal_the_notebooks(), test_value_matches_type()

### Community 95 - "locate"
Cohesion: 0.23
Nodes (22): locate(), Path, Target, (point, rung) from the first rung that hits, or None., Anchor, OcrText, _dup_target(), _look() (+14 more)

### Community 96 - "llm.py"
Cohesion: 0.19
Nodes (13): ChatAnthropic, ModelKind, os, _build(), make_chat_model(), model_name_for(), _pass_through_ca_bundle(), BaseChatModel (+5 more)

### Community 97 - "Box"
Cohesion: 0.06
Nodes (47): crop_box(), cut_crop(), _ink(), input_box(), Crops around one point: find the element there, crop around it, read text near…, New ink appeared INSIDE the input box (text, or a password's dots). A click…, Crop around the target, with every other piece of text blanked out., Pixels around the point changed. Catches password dots that OCR cannot read. (+39 more)

### Community 98 - "test_human.py"
Cohesion: 0.13
Nodes (43): goal_value(), The value the goal already gives for this field, or None. Code backstop for the…, _answer(), _badge(), _ctx(), _dirty(), entry(), Ext (+35 more)

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
Nodes (32): BaseModel, model_validator, _check_login_order(), _navigate(), output(), Step, Event log -> ``Capability``: steps, inputs, outputs and secrets come from the…, The {{input}} names the steps use, in order. {{secret:x}} is not an input. (+24 more)

### Community 107 - "seen_outcome"
Cohesion: 0.67
Nodes (3): The first rule whose text (whole words, any case) appeared on screen with this…, seen_outcome(), test_text_already_on_screen_before_the_step_is_not_an_outcome()

### Community 108 - "one_at_a_time"
Cohesion: 0.24
Nodes (20): P, make_act_tools(), _make_click(), _make_select_option(), _make_type_secret(), _make_type_text(), BaseTool, Ctx (+12 more)

### Community 109 - "test_evidence.py"
Cohesion: 0.23
Nodes (18): _artifact(), masked(), fixture, MonkeyPatch, Path, save_evidence: one masked folder per run. No run value or secret is ever…, Live: a form value of '1' made 'version: 1' and 's1.png' look like a leak, so a…, The OCR mask is tested in tests/unit/safety; here: that every PNG goes through… (+10 more)

### Community 110 - "make_ctx"
Cohesion: 0.13
Nodes (35): make_ctx(), Ctx, A discovery ``Ctx`` over fakes, built like ``attach`` but with no page wiring., helped(), _only(), asyncio, fixture, MonkeyPatch (+27 more)

### Community 111 - "._held"
Cohesion: 0.20
Nodes (3): Request, Gate 1: Approve, or Edit = back to the form with every value, then again.…, RouteLike

### Community 113 - "Replay notebook plan"
Cohesion: 0.33
Nodes (5): Decisions made here (review), Open questions for the user, Replay notebook plan, Sections, Tasks

### Community 114 - "BrowserConfig"
Cohesion: 0.11
Nodes (15): Page, The response to a send lands after the human's approval, not after the click:…, wait_for_change(), BrowserConfig, Settings shared by discovery and replay (the same page size at both, Q10)., FakeInput, A fake ``page.mouse`` / ``page.keyboard``: every call is recorded as ``(name,…, _png() (+7 more)

### Community 115 - "pathlib"
Cohesion: 0.18
Nodes (5): json, pathlib, The hand-back extension never touches any site: no content scripts, no host…, Frozen notebook sources for the parity tests (step 10 replaced the notebooks…, Guard: no site value lives in src/. Site values belong in configs/<site>.yaml…

### Community 117 - "test_dropdowns.py"
Cohesion: 0.17
Nodes (18): _approve(), HeldPage, _logged(), _no_crop_pixels(), asyncio, Ctx, fixture, MonkeyPatch (+10 more)

### Community 118 - "load_capability"
Cohesion: 0.14
Nodes (27): load_capability(), load_outcomes(), Path, The capability and the folder its crop paths are relative to., The capability's own `outcomes:` [{text, status, meaning}], else the site's…, Path, Discovery's saved artifact runs in replay unchanged: build -> save -> load ->…, test_crop_paths_resolve_to_saved_files() (+19 more)

### Community 121 - "test_recorder_reads.py"
Cohesion: 0.07
Nodes (39): BaseChatModel, Save the run as a capability, or say plainly why not. Checked before the model…, _save(), flag_leaks(), Mark (never store) an event whose label, anchor, own text, hint or input name…, describe(), BaseChatModel, R11: name, description, input descriptions, success text. Labels only, no… (+31 more)

### Community 122 - "cua/__init__.py"
Cohesion: 0.33
Nodes (3): cua: shared config and the LLM model factory (direct Anthropic) for the pure-…, host_allowed: only the site's own hosts (D15); about:blank always., test_only_allowed_hosts_and_blank()

### Community 123 - "discovery/evidence.py"
Cohesion: 0.20
Nodes (17): artifact_texts(), _copy_capability(), _events(), _folder(), Ctx, OcrFn, Path, Redact (+9 more)

### Community 125 - "confidence_gate"
Cohesion: 0.50
Nodes (5): confidence_gate(), job_tool_names(), Tools this job needs, plus the always-allowed set. Pure: no network, no LLM., Narrow base_tools to this job's tools, but only if the classifier is confident.…, test_job_tool_names_and_gate()

### Community 129 - "discovery/wiring.py"
Cohesion: 0.21
Nodes (10): _count_nav(), Attach discovery to an open browser session: the send guard on every request,…, Counts on the ctx of the latest attach to this page., bind_control(), ControlTab, Protocol, Bind the control tab to the current :class:`ControlWindow`, once per tab. A…, The Playwright calls binding makes on the control tab. (+2 more)

### Community 130 - "test_saved_artifacts.py"
Cohesion: 0.31
Nodes (7): MonkeyPatch, parametrize, Path, Every capability saved in the top-level artifacts/ folder (Decision 6) loads in…, test_a_saved_artifact_loads_in_replay(), test_a_saved_artifact_round_trips(), test_the_old_artifacts_folder_is_gone()

### Community 133 - "mk_look"
Cohesion: 0.21
Nodes (12): mk_look(), Ctx, Replay test helpers: ``make_replay_ctx`` (a real Ctx on fakes), ``mk_look``,…, ``take_look`` always returns this look., screen(), set_shoot(), AskStop, clean() (+4 more)

### Community 141 - "cua.discovery.agent"
Cohesion: 0.50
Nodes (3): cua.discovery.agent, Read order, What may NOT go here

## Knowledge Gaps
- **159 isolated node(s):** `MODES`, `manifest_version`, `name`, `version`, `description` (+154 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **14 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Ctx` connect `Ctx` to `discovery/wiring.py`, `FakeRoute`, `test_act.py`, `guard.py`, `mk_look`, `test_replay_inputs.py`, `re`, `DiscoveryRun`, `test_replay_rescue.py`, `test_replay_handback.py`, `config.py`, `test_replay_table.py`, `make_replay_ctx`, `test_replay_steps.py`, `look.py`, `DiscoveryConfig`, `test_replay_wiring.py`, `Session`, `Look`, `FakeTab`, `rescue.py`, `fakes.py`, `test_goal.py`, `test_human.py`, `BrowserConfig`, `test_dropdowns.py`, `discovery/evidence.py`?**
  _High betweenness centrality (0.066) - this node is a cross-community bridge._
- **Why does `Look` connect `Look` to `discovery/wiring.py`, `FakeRoute`, `test_act.py`, `guard.py`, `mk_look`, `test_input.py`, `test_dropdown.py`, `DiscoveryRun`, `test_replay_rescue.py`, `ReplayConfig`, `recorder/__init__.py`, `steps.py`, `make_replay_ctx`, `test_replay_steps.py`, `RefCounter`, `look.py`, `Session`, `FakeTab`, `vision/__init__.py`, `test_screenshot.py`, `canvas.py`, `fakes.py`, `Ctx`, `human_fills`, `locate`, `Box`, `test_human.py`, `BrowserConfig`, `test_dropdowns.py`?**
  _High betweenness centrality (0.056) - this node is a cross-community bridge._
- **Why does `BrowserConfig` connect `BrowserConfig` to `cli.py`, `FakeRoute`, `test_saved_artifacts.py`, `test_input.py`, `test_dropdown.py`, `test_replay_handback.py`, `config.py`, `test_session.py`, `make_replay_ctx`, `test_replay_steps.py`, `RefCounter`, `look.py`, `replay/evidence.py`, `DiscoveryConfig`, `test_takeover_loop.py`, `test_extension.py`, `Session`, `Look`, `Capability`, `FakeTab`, `test_screenshot.py`, `fakes.py`, `Ctx`, `handoff/__init__.py`, `Box`, `load_capability`?**
  _High betweenness centrality (0.045) - this node is a cross-community bridge._
- **Are the 27 inferred relationships involving `Look` (e.g. with `Ctx` and `DiscoveryRun`) actually correct?**
  _`Look` has 27 INFERRED edges - model-reasoned connections that need verification._
- **Are the 60 inferred relationships involving `Ctx` (e.g. with `LatestScreenshotOnly` and `NoopAnthropicPromptCachingMiddleware`) actually correct?**
  _`Ctx` has 60 INFERRED edges - model-reasoned connections that need verification._
- **Are the 36 inferred relationships involving `BrowserConfig` (e.g. with `Session` and `Answerable`) actually correct?**
  _`BrowserConfig` has 36 INFERRED edges - model-reasoned connections that need verification._
- **Are the 55 inferred relationships involving `build_capability()` (e.g. with `saved()` and `test_a_continued_table_is_one_step()`) actually correct?**
  _`build_capability()` has 55 INFERRED edges - model-reasoned connections that need verification._