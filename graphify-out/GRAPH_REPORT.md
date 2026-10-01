# Graph Report - BankerAgent  (2026-10-01)

## Corpus Check
- 226 files · ~267,758 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 2698 nodes · 7739 edges · 116 communities (105 shown, 11 thin omitted)
- Extraction: 93% EXTRACTED · 7% INFERRED · 0% AMBIGUOUS · INFERRED: 522 edges (avg confidence: 0.63)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `f73705ac`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- cli.py
- FakeRoute
- Productionize Plan: notebooks → `src/cua/` package
- test_act.py
- Evidence README
- test_middleware.py
- test_recorder_types.py
- test_replay_inputs.py
- test_input.py
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
- ReplayConfig
- test_llm.py
- test_replay_handback.py
- SiteProfile
- test_notebooks.py
- test_replay_wiring.py
- recorder/__init__.py
- steps.py
- test_table.py
- integration/conftest.py
- test_replay_evidence.py
- test_replay_table.py
- redactor
- Request
- build_capability
- test_replay_extract.py
- request.py
- CLAUDE.md (project instructions)
- make_replay_ctx
- vision/__init__.py
- manifest.json
- langchain_tools
- test_recorder_runs.py
- pathlib
- test_import_rules.py
- ReplayResult
- human.py
- FakeTab
- DiscoveryConfig
- locate.py
- test_send_guard.py
- test_control_window.py
- cua.vision
- test_takeover_loop.py
- where
- Session
- BrowserConfig
- Capability
- read_helpers.py
- handoff/__init__.py
- fakes.py
- SendGuard
- langgraph_types
- act.py
- Discovery decisions
- 2. Each box, with an example
- test_capability.py
- ControlWindow
- 2. Components
- yaml
- Pure-Visual Discovery Notebook: Build Plan
- spot_changed
- SiteLock
- AST
- test_discovery_to_replay.py
- config.py
- engine.py
- choose_option_at_point
- test_routing.py
- routing.py
- .awrap_model_call
- Look
- test_session.py
- test_prompt.py
- copy
- discovery/wiring.py
- build_tools
- cua
- cua/__init__.py
- cua.schema
- seen_outcome
- safety/__init__.py
- test_goal.py
- test_human_tools.py
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
- Replay notebook plan
- Ctx
- test_dropdowns.py
- load_capability
- replay/evidence.py
- discovery/evidence.py
- llm.py
- background.js
- replay/wiring.py
- bind_control
- cua.discovery.agent
- pytest

## God Nodes (most connected - your core abstractions)
1. `Look` - 116 edges
2. `make_ctx()` - 93 edges
3. `Ctx` - 87 edges
4. `BrowserConfig` - 82 edges
5. `ReplayConfig` - 70 edges
6. `build_capability()` - 69 edges
7. `Element` - 63 edges
8. `make_replay_ctx()` - 60 edges
9. `_meta()` - 57 edges
10. `Box` - 53 edges

## Surprising Connections (you probably didn't know these)
- `test_input_name_slugs_a_label_and_never_starts_with_a_digit()` --calls--> `input_name()`  [INFERRED]
  tests/unit/discovery/recorder/test_recorder.py → src/cua/discovery/recorder/events.py
- `test_the_login_click_before_a_menu_link_is_kept()` --calls--> `step_events()`  [INFERRED]
  tests/unit/discovery/recorder/test_recorder_runs.py → src/cua/discovery/recorder/events.py
- `test_typed_ok_words_tolerant_digits_exact()` --calls--> `typed_ok()`  [INFERRED]
  tests/unit/replay/test_locate.py → src/cua/replay/locate.py
- `test_a_target_needs_a_findable_rung()` --calls--> `Target`  [INFERRED]
  tests/unit/schema/test_capability.py → src/cua/schema/capability.py
- `test_an_old_select_without_an_index_still_loads()` --calls--> `Select`  [INFERRED]
  tests/unit/discovery/recorder/test_recorder_reads.py → src/cua/schema/capability.py

## Import Cycles
- 3-file cycle: `src/cua/discovery/tools/__init__.py -> src/cua/discovery/tools/nav.py -> src/cua/discovery/tools/guard.py -> src/cua/discovery/tools/__init__.py`
- 3-file cycle: `src/cua/discovery/tools/__init__.py -> src/cua/discovery/tools/nav.py -> src/cua/discovery/tools/observe.py -> src/cua/discovery/tools/__init__.py`
- 3-file cycle: `src/cua/discovery/tools/__init__.py -> src/cua/discovery/tools/human.py -> src/cua/discovery/tools/observe.py -> src/cua/discovery/tools/__init__.py`
- 3-file cycle: `src/cua/discovery/tools/__init__.py -> src/cua/discovery/tools/act.py -> src/cua/discovery/tools/observe.py -> src/cua/discovery/tools/__init__.py`
- 3-file cycle: `src/cua/discovery/tools/guard.py -> src/cua/discovery/tools/human.py -> src/cua/discovery/tools/observe.py -> src/cua/discovery/tools/guard.py`
- 3-file cycle: `src/cua/discovery/tools/__init__.py -> src/cua/discovery/tools/read.py -> src/cua/discovery/tools/guard.py -> src/cua/discovery/tools/__init__.py`
- 3-file cycle: `src/cua/discovery/tools/__init__.py -> src/cua/discovery/tools/act.py -> src/cua/discovery/tools/guard.py -> src/cua/discovery/tools/__init__.py`
- 4-file cycle: `src/cua/discovery/tools/__init__.py -> src/cua/discovery/tools/nav.py -> src/cua/discovery/tools/observe.py -> src/cua/discovery/tools/guard.py -> src/cua/discovery/tools/__init__.py`
- 4-file cycle: `src/cua/discovery/tools/__init__.py -> src/cua/discovery/tools/act.py -> src/cua/discovery/tools/human.py -> src/cua/discovery/tools/observe.py -> src/cua/discovery/tools/__init__.py`
- 4-file cycle: `src/cua/discovery/tools/__init__.py -> src/cua/discovery/tools/human.py -> src/cua/discovery/tools/observe.py -> src/cua/discovery/tools/guard.py -> src/cua/discovery/tools/__init__.py`
- 4-file cycle: `src/cua/discovery/tools/__init__.py -> src/cua/discovery/tools/act.py -> src/cua/discovery/tools/observe.py -> src/cua/discovery/tools/guard.py -> src/cua/discovery/tools/__init__.py`
- 5-file cycle: `src/cua/discovery/tools/__init__.py -> src/cua/discovery/tools/nav.py -> src/cua/discovery/tools/guard.py -> src/cua/discovery/tools/human.py -> src/cua/discovery/tools/observe.py -> src/cua/discovery/tools/__init__.py`
- 5-file cycle: `src/cua/discovery/tools/__init__.py -> src/cua/discovery/tools/act.py -> src/cua/discovery/tools/guard.py -> src/cua/discovery/tools/human.py -> src/cua/discovery/tools/observe.py -> src/cua/discovery/tools/__init__.py`
- 5-file cycle: `src/cua/discovery/tools/__init__.py -> src/cua/discovery/tools/read.py -> src/cua/discovery/tools/guard.py -> src/cua/discovery/tools/human.py -> src/cua/discovery/tools/observe.py -> src/cua/discovery/tools/__init__.py`
- 5-file cycle: `src/cua/discovery/tools/__init__.py -> src/cua/discovery/tools/act.py -> src/cua/discovery/tools/human.py -> src/cua/discovery/tools/observe.py -> src/cua/discovery/tools/guard.py -> src/cua/discovery/tools/__init__.py`

## Communities (116 total, 11 thin omitted)

### Community 0 - "cli.py"
Cohesion: 0.18
Nodes (18): argparse, Namespace, _close(), default_site(), discover(), main(), parse_args(), parse_inputs() (+10 more)

### Community 1 - "FakeRoute"
Cohesion: 0.11
Nodes (11): FakeControl, FakePage, FakeRoute, A fake discovery/replay ``CONTROL`` surface (what ``ControlWindow`` presents).…, A fake ``playwright.async_api.Route``: records every…, A fake ``playwright.async_api.Page``. Every awaited method is recorded in…, asyncio, Tests for the shared offline fakes in tests/fakes.py (TDD: written before the… (+3 more)

### Community 2 - "Productionize Plan: notebooks → `src/cua/` package"
Cohesion: 0.12
Nodes (16): 10. Line-count offenders (today), 1. Package tree, 2. De-duplication (checked by AST diff of both notebooks), 3. State: globals → explicit objects, 4. Async and typing, 5. Notebooks after the move, 6. Tests, 7. ML-engineering practices (kept small) (+8 more)

### Community 3 - "test_act.py"
Cohesion: 0.07
Nodes (75): Items, (value, pattern) for an extract: the whole box when it is exactly the type,…, value_in_box(), make_look(), A look whose elements are numbered 1.. in order (ref, text, box)., Driven, _head(), _helped() (+67 more)

### Community 5 - "test_middleware.py"
Cohesion: 0.16
Nodes (22): AIMessage, Ctx, 3.5: keep the text the model wrote before its tool calls as ``ctx.run.why``…, RecordWhy, _answer(), asyncio, parametrize, SimpleNamespace (+14 more)

### Community 6 - "test_recorder_types.py"
Cohesion: 0.24
Nodes (13): Typed inputs: the recorder infers each input's type from the shapes of the…, Older logs (and any tool that did not log shapes) never guess a type., test_a_plain_whole_number_is_a_number_so_decimals_pass_replay_later(), test_a_value_with_no_shape_is_string(), test_all_currency_values_make_a_currency_input(), test_an_event_without_shapes_is_string(), test_human_entry_is_typed_too(), test_mixed_shapes_fall_back_to_their_common_type() (+5 more)

### Community 7 - "test_replay_inputs.py"
Cohesion: 0.12
Nodes (34): select(), type_(), _cap(), ClearPage, env(), FakeForm, FakePage, asyncio (+26 more)

### Community 8 - "test_input.py"
Cohesion: 0.12
Nodes (22): act(), into_box(), Lock, Page, Session, Step, Unlock the site tab, run our own input steps, relock, settle, take a new look., Click the box, clear what is in it, type. Retries replace instead of doubling… (+14 more)

### Community 9 - "middleware.py"
Cohesion: 0.11
Nodes (22): CompiledStateGraph, deepagents, Handler, langchain_agents_middleware, langgraph_checkpoint_memory, build_agent(), BaseChatModel, Ctx (+14 more)

### Community 10 - "test_dropdown.py"
Cohesion: 0.09
Nodes (32): BaseException, list_options(), Dropdown, Page, Every option of the dropdown at this page point ([] if it is not a dropdown).…, The page's dropdowns, read BEFORE an action (never while guard_send holds a…, read_dropdowns(), _js() (+24 more)

### Community 12 - "Replay decisions"
Cohesion: 0.08
Nodes (23): R10: where the compile step lives — DECIDED, R11: why compile, if `response_format` exists? — PROPOSED, R12: what each step type compiles to — PROPOSED, R13: target schema — PROPOSED, R14: what rung 2 needs that discovery doesn't record — DONE, R15: auto-approve at replay — PROPOSED, R16: dead ends and retries at compile — PROPOSED, R17: replay result statuses — PROPOSED (+15 more)

### Community 16 - "DiscoveryRun"
Cohesion: 0.12
Nodes (17): Saved, The current run (the one the send guard serves)., DiscoveryRun, What the human gave: the goal and every answer (the send guard's mismatch text)., Every saved text, table cells included (evidence masking only)., Banking: values live only for the run. Keep the log (labels only), drop the…, saved_texts(), wipe() (+9 more)

### Community 17 - "test_cli.py"
Cohesion: 0.14
Nodes (21): _fake_session(), _patch_session(), MonkeyPatch, parametrize, Path, SimpleNamespace, cua.cli: argument parsing, --input parsing, and main() as the only asyncio.run…, _record_run() (+13 more)

### Community 18 - "test_replay_engine.py"
Cohesion: 0.18
Nodes (47): cap(), click(), extract(), AskStop, _finish(), _login_cap(), _no_snap(), _only() (+39 more)

### Community 19 - "ReplayConfig"
Cohesion: 0.06
Nodes (49): Replay-only settings., ReplayConfig, The guard keeps its own reference to the control window: swap both., set_control(), DoneWhileSending, _env(), _fail_clicks(), FormRoute (+41 more)

### Community 20 - "test_llm.py"
Cohesion: 0.20
Nodes (14): _clean_env(), _gateway(), fixture, MonkeyPatch, Offline tests for `cua.llm.make_chat_model`. No network, no real key. Default:…, test_ca_bundle_passthrough(), test_existing_ssl_cert_file_wins(), test_gateway_env_means_gateway() (+6 more)

### Community 21 - "test_replay_handback.py"
Cohesion: 0.13
Nodes (23): FakePage, _bctx(), Ext, Human, PanelDone, asyncio, Ctx, parametrize (+15 more)

### Community 22 - "SiteProfile"
Cohesion: 0.09
Nodes (26): Look up a secret by NAME. Raises on an unknown name or an empty/missing value.…, Secret name -> value from `.env` ("" when unset), as the notebook's SECRETS., Everything site-specific, loaded from ``configs/<name>.yaml``. Secrets: env…, Secret name -> env var name., resolve_secret(), secret_values(), SiteProfile, True if `name` is a known secret with a non-empty value in `.env` (D32: never… (+18 more)

### Community 23 - "test_notebooks.py"
Cohesion: 0.26
Nodes (16): Call, Module, _bind(), _code_cells(), _markdown(), _offline_namespace(), parametrize, Path (+8 more)

### Community 24 - "test_replay_wiring.py"
Cohesion: 0.08
Nodes (24): Working values for one run. Replaced by a new one in ``replay``'s ``finally``…, What the mismatch check compares a send against (SendState)., ReplayRun, attach(), Session, Wire replay onto an open session and return its Ctx., _fake_session(), asyncio (+16 more)

### Community 25 - "recorder/__init__.py"
Cohesion: 0.08
Nodes (51): ``build_capability``'s refusals, unchanged: a leaked value, a blind dropdown,…, _refuse(), used_inputs(), checkpoint(), The capability's checkpoint: the text replay must see to call the run a…, C: after a send, the page's own response proves success (the agent's proof only…, field_area(), flag_leaks() (+43 more)

### Community 26 - "steps.py"
Cohesion: 0.08
Nodes (57): Point, fill(), Put inputs into `{{name}}`. `{{secret:x}}` stays as it is: secrets go in only…, secret_name(), Bug B: the value is one of the OCR words. Digits exact ($10.00 is 10.00); words…, typed_ok(), changed(), choose_option() (+49 more)

### Community 27 - "test_table.py"
Cohesion: 0.18
Nodes (15): _defs(), _is_header(), _look(), Path, The shared OCR table reader: parity between cua.vision.table and both…, ast.dump compare, ignoring docstrings -- the functions this step did not have…, tests/replay/test_table_replay.py's own SHARED set is the contract this module…, _read() (+7 more)

### Community 29 - "test_replay_evidence.py"
Cohesion: 0.12
Nodes (30): Path, write_cap(), _all_text(), fake_ocr(), _png(), Ctx, fixture, parametrize (+22 more)

### Community 30 - "test_replay_table.py"
Cohesion: 0.21
Nodes (18): _cap(), _defs(), Page, asyncio, Ctx, MonkeyPatch, Path, do_extract_table: find the header by its label, read the rows with discovery's… (+10 more)

### Community 31 - "redactor"
Cohesion: 0.10
Nodes (32): functools, Pattern, mask_png(), _num(), OcrFn, text -> text with every value masked. Numbers match however they are written…, Black out every OCR box whose text holds a run value. A clean image is written…, redactor() (+24 more)

### Community 32 - "Request"
Cohesion: 0.13
Nodes (9): Protocol, The fields of a ``playwright.async_api.Request`` the guard reads., Request, ControlLike, LookLike, Protocol, What the guard reads and writes on a run (DiscoveryRun / ReplayRun satisfy it)., The two ControlWindow calls the gates use. (+1 more)

### Community 33 - "build_capability"
Cohesion: 0.06
Nodes (85): build_capability(), Steps, inputs and secrets come from the log only. The model's text cannot fail…, crops_for(), Path, save_artifact(), _ev(), _FakeModel, _meta() (+77 more)

### Community 34 - "test_replay_extract.py"
Cohesion: 0.19
Nodes (21): _extract(), _notebook_assign(), _pcap(), asyncio, Ctx, parametrize, Path, Extract steps on fakes: strict value types and an optional `pattern`. Ported… (+13 more)

### Community 35 - "request.py"
Cohesion: 0.19
Nodes (16): JsonObj, _flat(), _json(), What a held request sends, and the same request rebuilt with edited values.…, Every value a request sends, from its query, a form body, or a JSON body…, The request's url and body with these values put back in, in the same format., rebuilt(), sent_fields() (+8 more)

### Community 36 - "CLAUDE.md (project instructions)"
Cohesion: 0.12
Nodes (19): CLAUDE.md (project instructions), D101: labeled_value refuses a table-header resolution (general fix), D102: label_header/value_header flags ported into agent.py + cli.py capture path, D92: Evidence Capture Helpers (save_discovery_evidence/save_replay_evidence), D93: Pre-existing 02_artifact_schema.py IndexError bug, D95: Missing create_deep_agent import found live in BROWSER 12, D96: build_agent() goal_text vs given_text field-name bug, D97: cua replay --login flag + repeated Balance header trap (+11 more)

### Community 37 - "make_replay_ctx"
Cohesion: 0.08
Nodes (51): make_replay_ctx(), mk_look(), navigate(), Ctx, Replay test helpers: ``make_replay_ctx`` (a real Ctx on fakes), ``mk_look``,…, A real Ctx (real SendGuard, real ReplayRun) over a fake page/control/lock.…, ``take_look`` always returns this look., screen() (+43 more)

### Community 38 - "vision/__init__.py"
Cohesion: 0.06
Nodes (57): RapidOCR, canvas_size(), NDArray, uint8, Canvas-pixel <-> page-point mapping: any window size or pixel density maps to…, Fit the screenshot inside the canvas. Returns it and canvas-pixel -> page-point…, The size of the image the model is looking at right now., to_canvas() (+49 more)

### Community 39 - "manifest.json"
Cohesion: 0.11
Nodes (18): action, default_icon, default_title, background, service_worker, 128, 16, 32 (+10 more)

### Community 41 - "test_recorder_runs.py"
Cohesion: 0.14
Nodes (23): _click(), _clicks(), _go(), _names(), _nav(), _noop_click(), _paths(), Recorder behaviour pinned by live runs: detours, 404s, login clicks kept, no-op… (+15 more)

### Community 42 - "pathlib"
Cohesion: 0.18
Nodes (5): json, pathlib, The hand-back extension never touches any site: no content scripts, no host…, Frozen notebook sources for the parity tests (step 10 replaced the notebooks…, Guard: no site value lives in src/. Site values belong in configs/<site>.yaml…

### Community 43 - "test_import_rules.py"
Cohesion: 0.29
Nodes (13): _cua_imports(), _layer_files(), _module(), parametrize, Path, The package's import rule (docs/PRODUCTIONIZE_PLAN.md section 1), read from…, The top-level cua subpackage of every ``cua.*`` import (``import`` or ``from``)., Guard the guard: a planted forbidden import is caught in both spellings. (+5 more)

### Community 44 - "ReplayResult"
Cohesion: 0.15
Nodes (11): What a replay run returns: its Status, the Stop that ends a run early, and…, R17 run statuses. A member is a plain str, so ``Status.SUCCESS == "SUCCESS"``., ReplayResult, Status, StrEnum, ReplayResult summary/outputs_line, Stop, and the Status values., test_partial_outputs_line_when_not_success(), test_result_defaults() (+3 more)

### Community 45 - "human.py"
Cohesion: 0.20
Nodes (19): Field, An evidence screenshot: short timeout, None on failure (never hangs on a held…, snap(), _enter(), human_fills(), _make_ask_human(), _make_finish(), make_human_tools() (+11 more)

### Community 46 - "FakeTab"
Cohesion: 0.12
Nodes (3): FakeTab, SimpleNamespace, A fake site or control tab with the Playwright calls discovery's wiring and…

### Community 47 - "DiscoveryConfig"
Cohesion: 0.16
Nodes (31): DiscoveryConfig, Discovery-only settings., Discovery: an LLM agent learns a task once and the recorder saves it as a…, attach(), new_run(), A fresh run for this goal (run_goal's ``HANDOFF = HandoffState(goal=goal)``)., Route every request through a new send guard, open the control window. Re-run…, make_session() (+23 more)

### Community 48 - "locate.py"
Cohesion: 0.10
Nodes (43): SameTextLike, Replay: runs a capability saved by discovery with plain code, no LLM (step 4:…, anchor_point(), find_template(), find_text(), locate(), _ocr_hit(), NDArray (+35 more)

### Community 49 - "test_send_guard.py"
Cohesion: 0.16
Nodes (23): Side-specific steps, each at the exact point its notebook ran it. on_request:…, SendHooks, Control, _new(), _no_dropdowns(), _old(), _play(), parametrize (+15 more)

### Community 50 - "test_control_window.py"
Cohesion: 0.20
Nodes (24): Factory, SIDES, discovery_control(), FakeWin, asyncio, parametrize, ControlWindow: one class, both sides' behaviour. Ported from…, Discovery calls _front inside try (the question is removed on failure); replay… (+16 more)

### Community 51 - "cua.vision"
Cohesion: 0.50
Nodes (3): cua.vision, Read order, What may NOT go here

### Community 52 - "test_takeover_loop.py"
Cohesion: 0.12
Nodes (27): replay_control(), Asker, hand_back(), Future, Lock, Protocol, The shared take-over loop pieces. Each side's own take-over stays with that…, Done on the toolbar button or in the take-over panel hands back. No reminders… (+19 more)

### Community 53 - "where"
Cohesion: 0.14
Nodes (19): log_sent_dropdowns(), Ctx, A dropdown whose value a send carries becomes a step (discovery's send-guard…, A dropdown whose value this send carries is a step, even one left on its…, clean_label(), label_near(), merged_label(), OCR joins a label to the box beside it ('to account #16785') and reads a box… (+11 more)

### Community 54 - "Session"
Cohesion: 0.16
Nodes (19): BrowserContext, Playwright, playwright_async_api, Playwright, no decisions: the open session, the site lock, our own input,…, Our own input into the locked site tab: ``act`` (unlock, run steps, relock,…, _alive(), check_viewport(), _extension() (+11 more)

### Community 55 - "BrowserConfig"
Cohesion: 0.13
Nodes (11): The response to a send lands after the human's approval, not after the click:…, wait_for_change(), BrowserConfig, Settings shared by discovery and replay (the same page size at both, Q10)., IndexPage, _png(), ShotsPage, test_wait_for_change_gives_up_after_the_budget() (+3 more)

### Community 56 - "Capability"
Cohesion: 0.13
Nodes (28): Exception, _ask(), ask_inputs(), ask_option(), _ask_rows(), given_inputs(), input_type(), _missing_crops() (+20 more)

### Community 57 - "read_helpers.py"
Cohesion: 0.13
Nodes (29): Cols, _columns(), headings(), is_header(), is_word(), off_table(), page_texts(), Where a point is on a look, in words: labels, anchors, page texts. Pure (no… (+21 more)

### Community 58 - "handoff/__init__.py"
Cohesion: 0.10
Nodes (32): _in_control(), The take-over itself: badge YOU, unlock the site, wait for Done (panel or…, _takeover_note(), Answerable, button_clicked(), ext_call(), Extension, handback_button() (+24 more)

### Community 59 - "fakes.py"
Cohesion: 0.10
Nodes (11): ActTab, blank_png(), FakeInput, FakeLock, Shared offline fakes for the ported test suite (tests/unit, tests/integration).…, A fake ``cua.browser.SiteLock``: ``open()`` records unlock/lock, nothing else., A fake ``page.mouse`` / ``page.keyboard``: every call is recorded as ``(name,…, A site tab the act/nav tools drive: ``mouse``/``keyboard`` record into… (+3 more)

### Community 60 - "SendGuard"
Cohesion: 0.15
Nodes (8): pretty(), address.zipCode' -> 'Address zip code' (for the human; the key itself is kept)., Request, ``await guard(route)`` is the route handler. ``guard.lock`` is the send gate:…, Gate 1: Approve, or Edit = back to the form with every value, then again.…, RouteLike, SendGuard, test_pretty()

### Community 62 - "act.py"
Cohesion: 0.08
Nodes (55): P, _count_start(), The start event's look bookkeeping: the page a run begins on, and how often…, run_goal: one goal through the discovery agent (moved from discovery.py…, _start(), Every shape the whole value matches, in precedence order. Safe to log: names,…, shapes_of(), DiscoveryRun: one discovery run's working state (was the notebook's… (+47 more)

### Community 63 - "Discovery decisions"
Cohesion: 0.08
Nodes (24): Base decisions, Cuts, Discovery decisions, Q10: window size and zoom — DECIDED, Q11: notebook format — DECIDED, Q12: dropdowns — DECIDED, Q13: scrolling — DECIDED, Q14: private data in saved pictures — DECIDED (+16 more)

### Community 64 - "2. Each box, with an example"
Cohesion: 0.12
Nodes (15): 1. Diagram, 2. Each box, with an example, 3. All tools, 4. Step by step: one discovery run, 5. Notes, Browser (Playwright), Control window and site lock (Q-A), Discovery architecture (+7 more)

### Community 65 - "test_capability.py"
Cohesion: 0.23
Nodes (9): _data(), parametrize, Path, cua.schema.Capability loads every saved artifact and refuses an unknown schema…, test_a_target_needs_a_findable_rung(), test_a_wrong_schema_version_is_refused(), test_an_unknown_key_is_refused(), test_every_saved_artifact_loads() (+1 more)

### Community 66 - "ControlWindow"
Cohesion: 0.11
Nodes (18): base64, Question, ControlWindow, _img(), Protocol, ControlWindow: our own "Agent control" tab, the only place a human answers.…, Answers the question on top. Closing the window (None) answers every one: fail…, Answers the newest open question of this mode, wherever it sits on the stack. (+10 more)

### Community 67 - "2. Components"
Cohesion: 0.12
Nodes (15): 1. Diagram, 2. Components, 3. Step types, 4. Worked example: ParaBank login + read balance, 5. Notes, Actor, Artifact (made by discovery, not replay), Browser setup (+7 more)

### Community 68 - "yaml"
Cohesion: 0.27
Nodes (8): MonkeyPatch, parametrize, Path, Every capability saved in the top-level artifacts/ folder (Decision 6) loads in…, test_a_saved_artifact_loads_in_replay(), test_a_saved_artifact_round_trips(), test_the_old_artifacts_folder_is_gone(), yaml

### Community 69 - "Pure-Visual Discovery Notebook: Build Plan"
Cohesion: 0.09
Nodes (22): 10. Open risks, 1. Global constraints (every task must follow these), 2. Review focus (inputs no spec line covers, but likely to bite), 3. What already exists (reuse, or its visual version), 3a. How the agent is built today (`agent.ipynb` STEP 4, `src/cua/agent.py`), 3b. Existing handoff rules: when a human is called in, 3c. Existing tools → the new tools, 4. New dependencies (checked on PyPI, 2026-09-28) (+14 more)

### Community 70 - "spot_changed"
Cohesion: 0.33
Nodes (6): Pixels around the point changed. Catches password dots that OCR cannot read., spot_changed(), _look(), ndarray, spot_changed: password dots are pixels, not OCR text. Ported from…, test_dots_count_as_change_and_blank_does_not()

### Community 71 - "SiteLock"
Cohesion: 0.16
Nodes (12): CdpSender, Protocol, SiteLock: the site tab ignores all real input (CDP…, The one method of a Playwright ``CDPSession`` the lock uses., The site tab ignores all real input (CDP). Lifted only around our own action or…, SiteLock, FakeCdp, asyncio (+4 more)

### Community 72 - "AST"
Cohesion: 0.31
Nodes (8): AST, parametrize, Path, cua.schema.value_types matches both notebooks' SHAPES/TYPES exactly., SHAPES and TYPES as each notebook defines them (TYPES spreads SHAPES, so exec…, _tables(), test_tables_equal_the_notebooks(), test_value_matches_type()

### Community 73 - "test_discovery_to_replay.py"
Cohesion: 0.27
Nodes (8): fixture, MonkeyPatch, Path, Discovery's saved artifact runs in replay unchanged: build -> save -> load ->…, saved(), test_crop_paths_resolve_to_saved_files(), test_saved_artifact_loads_as_is(), test_steps_dispatch_to_replay_handlers()

### Community 74 - "config.py"
Cohesion: 0.18
Nodes (18): dotenv, _actions(), _find_root(), load_site(), OutcomeRule, _outcomes(), Path, Shared configuration: the site profile, browser/discovery/replay settings, and… (+10 more)

### Community 75 - "engine.py"
Cohesion: 0.12
Nodes (40): Drift, action_allowed(), _cleanup_step(), error_page(), finish(), is_cleanup(), judge(), login_came_back() (+32 more)

### Community 76 - "choose_option_at_point"
Cohesion: 0.38
Nodes (7): Confirm, LookFn, choose_option_at_index(), choose_option_at_point(), Session, Select the first option containing this text in the dropdown at (or next to)…, Select this exact live option in the Nth <select> (``index``), else the one at…

### Community 77 - "test_routing.py"
Cohesion: 0.21
Nodes (15): CaptureFixture, _choice(), FakeClassifier, FakeRequest, _names(), asyncio, MonkeyPatch, SimpleNamespace (+7 more)

### Community 78 - "routing.py"
Cohesion: 0.19
Nodes (12): ModuleType, build_routing_middleware(), Classifier, _model_router(), AgentMiddleware, Protocol, TypeSafe tool selection + model routing, restored (user, 2026-10-01;…, Haiku for a simple step, Sonnet otherwise (both through cua.llm). (+4 more)

### Community 79 - ".awrap_model_call"
Cohesion: 0.18
Nodes (11): confidence_gate(), job_tool_names(), page_name(), AsyncHandler, ModelRequest, ModelResponse, Tools this job needs, plus the always-allowed set. Pure: no network, no LLM., Narrow base_tools to this job's tools, but only if the classifier is confident.… (+3 more)

### Community 80 - "Look"
Cohesion: 0.06
Nodes (56): column_header(), The value's column, walked upwards while each text is within TABLE_GAP of the…, The texts on el's row, left of it, up to its table's left edge: the first CLEAR…, Row key + column header, only for a value in a real table, else None (replay…, Where an extracted value is, for replay, never the value itself: its table cell…, Text, box, and ordinal (the Nth element on screen whose `text(...)` is the…, read_target(), row_block() (+48 more)

### Community 81 - "test_session.py"
Cohesion: 0.24
Nodes (11): LivePage, _png(), asyncio, MonkeyPatch, Path, open_session reuses a live session (a notebook re-run must not leak a browser),…, _session(), test_a_live_existing_session_is_returned_unchanged() (+3 more)

### Community 82 - "test_prompt.py"
Cohesion: 0.13
Nodes (9): The discovery agent: system prompt, middleware, optional TypeSafe routing, and…, The discovery agent's system prompt, verbatim from…, _capture(), MonkeyPatch, build_agent: the notebook's create_deep_agent call, with routing appended only…, test_build_agent_wires_the_notebooks_agent(), test_routing_is_appended_after_the_notebooks_middleware(), test_the_page_path_is_read_live() (+1 more)

### Community 84 - "discovery/wiring.py"
Cohesion: 0.24
Nodes (9): build_ctx(), _count_nav(), _hooks(), Ctx, Session, Attach discovery to an open browser session: the send guard on every request,…, Counts on the ctx of the latest attach to this page., Discovery's post-approve steps, in guard_send's order. ``holder`` gets the ctx… (+1 more)

### Community 85 - "build_tools"
Cohesion: 0.15
Nodes (17): AsyncFunctionDef, inspect, build_tools(), BaseTool, Ctx, observe, click, type_text, type_secret, select_option, scroll, open_path,…, test_the_prompt_lists_every_tool(), test_every_built_tool_has_an_action_type() (+9 more)

### Community 86 - "cua"
Cohesion: 0.50
Nodes (3): cua, Read order, Rules

### Community 87 - "cua/__init__.py"
Cohesion: 0.33
Nodes (3): cua: shared config and the LLM model factory (Iliad gateway) for the pure-…, host_allowed: only the site's own hosts (D15); about:blank always., test_only_allowed_hosts_and_blank()

### Community 88 - "cua.schema"
Cohesion: 0.50
Nodes (3): cua.schema, Read order, What may NOT go here

### Community 89 - "seen_outcome"
Cohesion: 0.67
Nodes (3): The first rule whose text (whole words, any case) appeared on screen with this…, seen_outcome(), test_text_already_on_screen_before_the_step_is_not_an_outcome()

### Community 90 - "safety/__init__.py"
Cohesion: 0.16
Nodes (19): Safety: what may leave the tab (hosts, the two send gates) and keeping values…, dropdown_options(), mismatches(), _norm_num(), Dropdown, Values a send carries that the human never gave, and the dropdown choices to…, Numbers being sent that the human never gave, e.g. account 1450 vs 1400. Only…, For each key: the options of the page dropdown whose CURRENT value is exactly… (+11 more)

### Community 92 - "test_goal.py"
Cohesion: 0.13
Nodes (24): Agent, Ctx, Protocol, What run_goal needs of the compiled deep agent., The deadline passed: end the run STUCK, keeping what the agent did so far., New run on a fresh thread; pass an earlier thread_id to resume it with a next…, run_goal(), _timed_out() (+16 more)

### Community 93 - "test_human_tools.py"
Cohesion: 0.35
Nodes (13): _ctx(), asyncio, Ctx, MonkeyPatch, finish_business_outcome / request_missing_values / ask_human (the human-facing…, test_ask_human_asks_with_the_question(), test_finish_needs_the_proof_on_the_screen(), test_no_fields_given() (+5 more)

### Community 98 - "test_human.py"
Cohesion: 0.13
Nodes (43): human_help(), offer_control(), Q21, open-ended: the human answers in words, takes over the site, or stops the…, Only the reason: the first line of the tool result, without its prefix or…, Q21: the one time the site unlocks for a human. What they did is kept as…, take_over(), _answer(), _badge() (+35 more)

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
Nodes (31): BaseModel, model_validator, re, _navigate(), output(), Step, Event log -> ``Capability``: steps, inputs, outputs and secrets come from the…, The {{input}} names the steps use, in order. {{secret:x}} is not an input. (+23 more)

### Community 109 - "test_evidence.py"
Cohesion: 0.26
Nodes (16): _artifact(), masked(), fixture, MonkeyPatch, Path, save_evidence: one masked folder per run. No run value or secret is ever…, The OCR mask is tested in tests/unit/safety; here: that every PNG goes through…, _save() (+8 more)

### Community 110 - "make_ctx"
Cohesion: 0.13
Nodes (33): make_ctx(), Ctx, Session, A discovery ``Ctx`` over fakes, built like ``attach`` but with no page wiring., helped(), _only(), asyncio, fixture (+25 more)

### Community 113 - "Replay notebook plan"
Cohesion: 0.33
Nodes (5): Decisions made here (review), Open questions for the user, Replay notebook plan, Sections, Tasks

### Community 114 - "Ctx"
Cohesion: 0.10
Nodes (40): dataclasses, act(), canvas(), choose_option(), crop(), Ctx, into_box(), list_options() (+32 more)

### Community 117 - "test_dropdowns.py"
Cohesion: 0.16
Nodes (18): _approve(), HeldPage, _logged(), _no_crop_pixels(), asyncio, Ctx, fixture, MonkeyPatch (+10 more)

### Community 118 - "load_capability"
Cohesion: 0.20
Nodes (22): load_capability(), load_outcomes(), Path, The capability and the folder its crop paths are relative to., The capability's own `outcomes:` [{text, status, meaning}], else the site's…, fixture, MonkeyPatch, parametrize (+14 more)

### Community 120 - "replay/evidence.py"
Cohesion: 0.09
Nodes (35): _clean(), config_hash(), git_sha(), _png(), JsonValue, OcrFn, Path, Redact (+27 more)

### Community 123 - "discovery/evidence.py"
Cohesion: 0.23
Nodes (15): _copy_capability(), _events(), _folder(), Ctx, OcrFn, Path, Redact, One masked folder per discovery run: goal, answer, events, transcript, crops,… (+7 more)

### Community 125 - "llm.py"
Cohesion: 0.24
Nodes (10): ModelKind, os, make_chat_model(), model_name_for(), _pass_through_ca_bundle(), BaseChatModel, The one place that builds a chat model. Every LLM call in the project goes…, The configured model name for `kind` (``ILIAD_SONNET_MODEL`` /… (+2 more)

### Community 131 - "replay/wiring.py"
Cohesion: 0.06
Nodes (41): pydantic, Bind the control tab to the current :class:`ControlWindow`, once per tab. A…, Ctx, note_takeover_send(), Page, Request, Ctx: what every replay function takes first (session, run, settings, send…, R7: nothing kept. A fresh run, and the guard reads that one from now on. (+33 more)

### Community 134 - "bind_control"
Cohesion: 0.38
Nodes (5): bind_control(), ControlTab, Protocol, The Playwright calls binding makes on the control tab., Point the control tab's buttons and its close at ``control``. Re-run safe: the…

### Community 141 - "cua.discovery.agent"
Cohesion: 0.50
Nodes (3): cua.discovery.agent, Read order, What may NOT go here

### Community 149 - "pytest"
Cohesion: 0.17
Nodes (10): pytest, _fake_llm_keys(), fixture, MonkeyPatch, Suite-wide: never let a real LLM key from `.env` reach a test (cua.config loads…, A fake direct-Anthropic key so code that builds a chat model works offline; no…, parametrize, Path (+2 more)

## Knowledge Gaps
- **159 isolated node(s):** `MODES`, `manifest_version`, `name`, `version`, `description` (+154 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **11 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `BrowserConfig` connect `BrowserConfig` to `cli.py`, `FakeRoute`, `replay/wiring.py`, `test_input.py`, `test_dropdown.py`, `ReplayConfig`, `test_replay_handback.py`, `SiteProfile`, `test_replay_evidence.py`, `make_replay_ctx`, `vision/__init__.py`, `FakeTab`, `DiscoveryConfig`, `test_takeover_loop.py`, `Session`, `Capability`, `handoff/__init__.py`, `fakes.py`, `yaml`, `spot_changed`, `test_discovery_to_replay.py`, `config.py`, `Look`, `test_session.py`, `Ctx`, `load_capability`, `replay/evidence.py`?**
  _High betweenness centrality (0.052) - this node is a cross-community bridge._
- **Why does `Look` connect `Look` to `FakeRoute`, `replay/wiring.py`, `test_act.py`, `test_input.py`, `test_dropdown.py`, `DiscoveryRun`, `ReplayConfig`, `steps.py`, `test_table.py`, `test_replay_evidence.py`, `make_replay_ctx`, `vision/__init__.py`, `human.py`, `FakeTab`, `locate.py`, `where`, `Session`, `BrowserConfig`, `read_helpers.py`, `fakes.py`, `act.py`, `spot_changed`, `discovery/wiring.py`, `test_human.py`, `Ctx`, `test_dropdowns.py`?**
  _High betweenness centrality (0.052) - this node is a cross-community bridge._
- **Why does `Ctx` connect `Ctx` to `FakeRoute`, `replay/wiring.py`, `test_act.py`, `test_middleware.py`, `test_replay_inputs.py`, `middleware.py`, `DiscoveryRun`, `test_replay_engine.py`, `ReplayConfig`, `test_replay_handback.py`, `SiteProfile`, `test_replay_wiring.py`, `test_replay_table.py`, `make_replay_ctx`, `human.py`, `FakeTab`, `DiscoveryConfig`, `where`, `Session`, `BrowserConfig`, `read_helpers.py`, `fakes.py`, `act.py`, `Look`, `discovery/wiring.py`, `test_goal.py`, `test_human.py`, `test_dropdowns.py`, `discovery/evidence.py`?**
  _High betweenness centrality (0.049) - this node is a cross-community bridge._
- **Are the 26 inferred relationships involving `Look` (e.g. with `Ctx` and `DiscoveryRun`) actually correct?**
  _`Look` has 26 INFERRED edges - model-reasoned connections that need verification._
- **Are the 59 inferred relationships involving `Ctx` (e.g. with `LatestScreenshotOnly` and `NoopAnthropicPromptCachingMiddleware`) actually correct?**
  _`Ctx` has 59 INFERRED edges - model-reasoned connections that need verification._
- **Are the 35 inferred relationships involving `BrowserConfig` (e.g. with `Session` and `Answerable`) actually correct?**
  _`BrowserConfig` has 35 INFERRED edges - model-reasoned connections that need verification._
- **Are the 30 inferred relationships involving `ReplayConfig` (e.g. with `Ctx` and `_Request`) actually correct?**
  _`ReplayConfig` has 30 INFERRED edges - model-reasoned connections that need verification._