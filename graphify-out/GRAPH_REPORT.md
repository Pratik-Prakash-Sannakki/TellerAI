# Graph Report - BankerAgent  (2026-10-01)

## Corpus Check
- 188 files · ~161,291 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 2725 nodes · 7808 edges · 135 communities (120 shown, 15 thin omitted)
- Extraction: 93% EXTRACTED · 7% INFERRED · 0% AMBIGUOUS · INFERRED: 534 edges (avg confidence: 0.63)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `91f0a16e`
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
- test_middleware.py
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
- SiteProfile
- test_table.py
- test_replay_wiring.py
- recorder/__init__.py
- steps.py
- vision/__init__.py
- integration/conftest.py
- test_redact_more.py
- test_replay_table.py
- redactor
- test_notebooks.py
- build_capability
- make_replay_ctx
- test_replay_evidence.py
- CLAUDE.md (project instructions)
- test_replay_steps.py
- RefCounter
- manifest.json
- langchain_tools
- redact.py
- test_human_tools.py
- replay/context.py
- replay/evidence.py
- crop
- Ctx
- DiscoveryConfig
- locate
- test_send_guard.py
- test_control_window.py
- cua.vision
- test_takeover_loop.py
- handoff/__init__.py
- Session
- Look
- Capability
- yaml
- FakeTab
- test_screenshot.py
- test_recorder_runs.py
- langgraph_types
- guard.py
- Discovery decisions
- 2. Each box, with an example
- request.py
- ControlWindow
- 2. Components
- HeldPage
- Pure-Visual Discovery Notebook: Build Plan
- ScriptedControl
- SiteLock
- test_recorder_reads.py
- ReplayResult
- pathlib
- engine.py
- GateControl
- routing.py
- FakeWin
- act.py
- Element
- test_import_rules.py
- fakes.py
- copy
- Route
- build_tools
- cua
- pytest
- cua.schema
- ReplayConfig
- middleware.py
- test_capability.py
- test_goal.py
- human.py
- test_value_types.py
- rescue.py
- cua/__init__.py
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
- seen_outcome
- into_box
- test_evidence.py
- make_ctx
- ._held
- BrowserConfig
- Replay notebook plan
- nav.py
- where
- config.py
- test_dropdowns.py
- load_capability
- ToolRouter
- Stop
- _FakeModel
- agent/build.py
- discovery/evidence.py
- FakePage
- ActTab
- background.js
- test_discovery_to_replay.py
- HumanControl
- choose_option_at_point
- AST
- replay/wiring.py
- test_spot_changed.py
- IndexPage
- cua.discovery.agent

## God Nodes (most connected - your core abstractions)
1. `Look` - 117 edges
2. `make_ctx()` - 93 edges
3. `Ctx` - 87 edges
4. `BrowserConfig` - 83 edges
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
- `test_anchor_label_matches_ocr_merged_with_a_value()` --calls--> `same_label()`  [INFERRED]
  tests/unit/replay/test_locate.py → src/cua/replay/locate.py
- `test_a_target_needs_a_findable_rung()` --calls--> `Target`  [INFERRED]
  tests/unit/schema/test_capability.py → src/cua/schema/capability.py

## Import Cycles
- 3-file cycle: `src/cua/discovery/tools/__init__.py -> src/cua/discovery/tools/act.py -> src/cua/discovery/tools/guard.py -> src/cua/discovery/tools/__init__.py`
- 3-file cycle: `src/cua/discovery/tools/__init__.py -> src/cua/discovery/tools/act.py -> src/cua/discovery/tools/observe.py -> src/cua/discovery/tools/__init__.py`
- 3-file cycle: `src/cua/discovery/tools/__init__.py -> src/cua/discovery/tools/nav.py -> src/cua/discovery/tools/guard.py -> src/cua/discovery/tools/__init__.py`
- 3-file cycle: `src/cua/discovery/tools/__init__.py -> src/cua/discovery/tools/nav.py -> src/cua/discovery/tools/observe.py -> src/cua/discovery/tools/__init__.py`
- 3-file cycle: `src/cua/discovery/tools/__init__.py -> src/cua/discovery/tools/human.py -> src/cua/discovery/tools/observe.py -> src/cua/discovery/tools/__init__.py`
- 3-file cycle: `src/cua/discovery/tools/guard.py -> src/cua/discovery/tools/human.py -> src/cua/discovery/tools/observe.py -> src/cua/discovery/tools/guard.py`
- 3-file cycle: `src/cua/discovery/tools/__init__.py -> src/cua/discovery/tools/read.py -> src/cua/discovery/tools/guard.py -> src/cua/discovery/tools/__init__.py`
- 4-file cycle: `src/cua/discovery/tools/__init__.py -> src/cua/discovery/tools/act.py -> src/cua/discovery/tools/human.py -> src/cua/discovery/tools/observe.py -> src/cua/discovery/tools/__init__.py`
- 4-file cycle: `src/cua/discovery/tools/__init__.py -> src/cua/discovery/tools/act.py -> src/cua/discovery/tools/observe.py -> src/cua/discovery/tools/guard.py -> src/cua/discovery/tools/__init__.py`
- 4-file cycle: `src/cua/discovery/tools/__init__.py -> src/cua/discovery/tools/nav.py -> src/cua/discovery/tools/observe.py -> src/cua/discovery/tools/guard.py -> src/cua/discovery/tools/__init__.py`
- 4-file cycle: `src/cua/discovery/tools/__init__.py -> src/cua/discovery/tools/human.py -> src/cua/discovery/tools/observe.py -> src/cua/discovery/tools/guard.py -> src/cua/discovery/tools/__init__.py`
- 5-file cycle: `src/cua/discovery/tools/__init__.py -> src/cua/discovery/tools/act.py -> src/cua/discovery/tools/guard.py -> src/cua/discovery/tools/human.py -> src/cua/discovery/tools/observe.py -> src/cua/discovery/tools/__init__.py`
- 5-file cycle: `src/cua/discovery/tools/__init__.py -> src/cua/discovery/tools/act.py -> src/cua/discovery/tools/human.py -> src/cua/discovery/tools/observe.py -> src/cua/discovery/tools/guard.py -> src/cua/discovery/tools/__init__.py`
- 5-file cycle: `src/cua/discovery/tools/__init__.py -> src/cua/discovery/tools/nav.py -> src/cua/discovery/tools/guard.py -> src/cua/discovery/tools/human.py -> src/cua/discovery/tools/observe.py -> src/cua/discovery/tools/__init__.py`
- 5-file cycle: `src/cua/discovery/tools/__init__.py -> src/cua/discovery/tools/read.py -> src/cua/discovery/tools/guard.py -> src/cua/discovery/tools/human.py -> src/cua/discovery/tools/observe.py -> src/cua/discovery/tools/__init__.py`

## Communities (135 total, 15 thin omitted)

### Community 0 - "cli.py"
Cohesion: 0.15
Nodes (21): argparse, Namespace, _close(), default_site(), discover(), main(), parse_args(), parse_inputs() (+13 more)

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
Cohesion: 0.12
Nodes (22): Our own input into the locked site tab: ``act`` (unlock, run steps, relock,…, canvas_size(), NDArray, uint8, Canvas-pixel <-> page-point mapping: any window size or pixel density maps to…, Fit the screenshot inside the canvas. Returns it and canvas-pixel -> page-point…, The size of the image the model is looking at right now., to_canvas() (+14 more)

### Community 6 - "test_recorder_types.py"
Cohesion: 0.25
Nodes (13): Typed inputs: the recorder infers each input's type from the shapes of the…, Older logs (and any tool that did not log shapes) never guess a type., test_a_plain_whole_number_is_a_number_so_decimals_pass_replay_later(), test_a_value_with_no_shape_is_string(), test_all_currency_values_make_a_currency_input(), test_an_event_without_shapes_is_string(), test_human_entry_is_typed_too(), test_no_typed_value_reaches_the_capability_or_its_yaml() (+5 more)

### Community 7 - "test_replay_inputs.py"
Cohesion: 0.12
Nodes (34): select(), type_(), _cap(), ClearPage, env(), FakeForm, FakePage, asyncio (+26 more)

### Community 8 - "test_input.py"
Cohesion: 0.12
Nodes (22): act(), Lock, Page, Session, Step, The response to a send lands after the human's approval, not after the click:…, Unlock the site tab, run our own input steps, relock, settle, take a new look., wait_for_change() (+14 more)

### Community 9 - "test_middleware.py"
Cohesion: 0.16
Nodes (22): AIMessage, Ctx, 3.5: keep the text the model wrote before its tool calls as ``ctx.run.why``…, RecordWhy, _answer(), asyncio, parametrize, SimpleNamespace (+14 more)

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
Cohesion: 0.12
Nodes (24): _fake_session(), _patch_session(), CaptureFixture, MonkeyPatch, parametrize, Path, SimpleNamespace, cua.cli: argument parsing, --input parsing, and main() as the only asyncio.run… (+16 more)

### Community 18 - "test_replay_engine.py"
Cohesion: 0.21
Nodes (44): cap(), click(), extract(), _finish(), _login_cap(), _no_snap(), _only(), _pcap() (+36 more)

### Community 19 - "test_replay_rescue.py"
Cohesion: 0.20
Nodes (27): The guard keeps its own reference to the control window: swap both., set_control(), _env(), _fail_clicks(), HangPage, HumanSimple, asyncio, MonkeyPatch (+19 more)

### Community 20 - "test_llm.py"
Cohesion: 0.20
Nodes (14): _clean_env(), _gateway(), fixture, MonkeyPatch, Offline tests for `cua.llm.make_chat_model`. No network, no real key. Default:…, test_ca_bundle_passthrough(), test_existing_ssl_cert_file_wins(), test_gateway_env_means_gateway() (+6 more)

### Community 21 - "test_replay_handback.py"
Cohesion: 0.20
Nodes (18): _bctx(), Ext, Human, PanelDone, asyncio, Ctx, parametrize, The toolbar hand-back button during a rescue (its service worker, never the… (+10 more)

### Community 22 - "SiteProfile"
Cohesion: 0.08
Nodes (33): load_site(), Read and validate ``configs/<name>.yaml`` (root defaults to the repo root)., Look up a secret by NAME. Raises on an unknown name or an empty/missing value.…, Secret name -> value from `.env` ("" when unset), as the notebook's SECRETS., Everything site-specific, loaded from ``configs/<name>.yaml``. Secrets: env…, Secret name -> env var name., resolve_secret(), secret_values() (+25 more)

### Community 23 - "test_table.py"
Cohesion: 0.26
Nodes (10): _is_header(), _look(), The shared OCR table reader: parity between cua.vision.table and both…, tests/replay/test_table_replay.py's own SHARED set is the contract this module…, _read(), test_a_table_that_runs_to_the_bottom_of_the_screen_may_continue(), test_a_three_column_table_is_read_into_rows_even_when_cells_are_a_few_px_off(), test_only_the_asked_columns_are_kept_and_the_row_limit_holds() (+2 more)

### Community 24 - "test_replay_wiring.py"
Cohesion: 0.10
Nodes (21): attach(), Session, Wire replay onto an open session and return its Ctx., _fake_session(), asyncio, MonkeyPatch, Path, attach (the replay setup cell), the guard's replay hooks, and R7: after… (+13 more)

### Community 25 - "recorder/__init__.py"
Cohesion: 0.07
Nodes (56): check_savable(), Raise NotSaved before any model call when this run cannot become a capability., ``build_capability``'s refusals, unchanged: a leaked value, a blind dropdown,…, _refuse(), used_inputs(), checkpoint(), The capability's checkpoint: the text replay must see to call the run a…, C: after a send, the page's own response proves success (the agent's proof only… (+48 more)

### Community 26 - "steps.py"
Cohesion: 0.09
Nodes (47): Point, ask_option(), The one mid-run prompt: the given value is not a live option. Choose one, blank…, changed(), choose_option(), do_click(), do_extract(), do_navigate() (+39 more)

### Community 27 - "vision/__init__.py"
Cohesion: 0.15
Nodes (22): Pixels -> text: screenshots, OCR, canvas math, crops, and the shared table…, append_rows(), cell_shape(), col_of(), column_spans(), like_rows(), The shared OCR table reader: discovery and replay use it to find a table's…, A table's end: a line that no longer looks like its rows (a footer, a menu, a… (+14 more)

### Community 29 - "test_redact_more.py"
Cohesion: 0.13
Nodes (25): dropdown_options(), Dropdown, For each key: the options of the page dropdown whose CURRENT value is exactly…, mask_png(), OcrFn, Black out every OCR box whose text holds a run value. A clean image is written…, load(), Path (+17 more)

### Community 30 - "test_replay_table.py"
Cohesion: 0.21
Nodes (18): _cap(), _defs(), Page, asyncio, Ctx, MonkeyPatch, Path, do_extract_table: find the header by its label, read the rows with discovery's… (+10 more)

### Community 31 - "redactor"
Cohesion: 0.20
Nodes (13): Pattern, _num(), text -> text with every value masked. Numbers match however they are written…, redactor(), test_a_short_number_is_masked_only_as_a_whole_number(), _notebook(), redactor/norm: the value masker discovery uses (numbers however written, whole…, test_a_number_matches_however_it_is_written() (+5 more)

### Community 32 - "test_notebooks.py"
Cohesion: 0.26
Nodes (16): Call, Module, _bind(), _code_cells(), _markdown(), _offline_namespace(), parametrize, Path (+8 more)

### Community 33 - "build_capability"
Cohesion: 0.09
Nodes (55): build_capability(), Steps, inputs and secrets come from the log only. The model's text cannot fail…, crops_for(), Path, save_artifact(), fixture, MonkeyPatch, saved() (+47 more)

### Community 34 - "make_replay_ctx"
Cohesion: 0.10
Nodes (40): FakeLock, make_replay_ctx(), mk_look(), Ctx, Replay test helpers: ``make_replay_ctx`` (a real Ctx on fakes), ``mk_look``,…, SiteLock stand-in: open() unlocks for the block., A real Ctx (real SendGuard, real ReplayRun) over a fake page/control/lock.…, ``take_look`` always returns this look. (+32 more)

### Community 35 - "test_replay_evidence.py"
Cohesion: 0.23
Nodes (21): Path, write_cap(), _all_text(), fake_ocr(), _png(), Ctx, fixture, parametrize (+13 more)

### Community 36 - "CLAUDE.md (project instructions)"
Cohesion: 0.12
Nodes (19): CLAUDE.md (project instructions), D101: labeled_value refuses a table-header resolution (general fix), D102: label_header/value_header flags ported into agent.py + cli.py capture path, D92: Evidence Capture Helpers (save_discovery_evidence/save_replay_evidence), D93: Pre-existing 02_artifact_schema.py IndexError bug, D95: Missing create_deep_agent import found live in BROWSER 12, D96: build_agent() goal_text vs given_text field-name bug, D97: cua replay --login flag + repeated Balance header trap (+11 more)

### Community 37 - "test_replay_steps.py"
Cohesion: 0.08
Nodes (36): navigate(), _click_env(), GotoPage, _judge(), Page, asyncio, Ctx, MonkeyPatch (+28 more)

### Community 38 - "RefCounter"
Cohesion: 0.08
Nodes (37): RapidOCR, draw_numbered(), number(), ocr(), ocr_engine(), NDArray, uint8, The shared RapidOCR engine, OCR itself, numbering and the numbered-box overlay.… (+29 more)

### Community 39 - "manifest.json"
Cohesion: 0.11
Nodes (18): action, default_icon, default_title, background, service_worker, 128, 16, 32 (+10 more)

### Community 41 - "redact.py"
Cohesion: 0.09
Nodes (23): Safety: what may leave the tab (hosts, the two send gates) and keeping values…, mismatches(), _norm_num(), Values a send carries that the human never gave, and the dropdown choices to…, Numbers being sent that the human never gave, e.g. account 1450 vs 1400. Only…, hide_secrets(), is_sensitive(), Value masking: ``norm``, ``is_sensitive``, ``hide_secrets``, ``redactor``,… (+15 more)

### Community 42 - "test_human_tools.py"
Cohesion: 0.35
Nodes (13): _ctx(), asyncio, Ctx, MonkeyPatch, finish_business_outcome / request_missing_values / ask_human (the human-facing…, test_ask_human_asks_with_the_question(), test_finish_needs_the_proof_on_the_screen(), test_no_fields_given() (+5 more)

### Community 43 - "replay/context.py"
Cohesion: 0.13
Nodes (16): dataclasses, Ctx, note_takeover_send(), Page, Request, Ctx: what every replay function takes first (session, run, settings, send…, R7: nothing kept. A fresh run, and the guard reads that one from now on., wipe() (+8 more)

### Community 44 - "replay/evidence.py"
Cohesion: 0.09
Nodes (35): _clean(), config_hash(), git_sha(), _png(), JsonValue, OcrFn, Path, Redact (+27 more)

### Community 45 - "crop"
Cohesion: 0.16
Nodes (17): canvas(), crop(), into_box(), Step, Crop around the target, every other text blanked (sized to the current canvas)., Focus the site tab, click the box, clear it, type (see…, The size of the image the model is looking at right now., Every shape the whole value matches, in precedence order. Safe to log: names,… (+9 more)

### Community 46 - "Ctx"
Cohesion: 0.12
Nodes (21): choose_option(), Ctx, list_options(), Page, Ctx: what every discovery tool is given, plus the page wrappers the tools…, An evidence screenshot: short timeout, None on failure (never hangs on a held…, Every option of the dropdown at this point ([] if it is not a dropdown)., Select the first option containing this text in the dropdown at (or next to)… (+13 more)

### Community 47 - "DiscoveryConfig"
Cohesion: 0.12
Nodes (39): DiscoveryConfig, Discovery-only settings., Discovery: an LLM agent learns a task once and the recorder saves it as a…, attach(), build_ctx(), _count_nav(), _hooks(), new_run() (+31 more)

### Community 48 - "locate"
Cohesion: 0.21
Nodes (21): locate(), Path, Target, (point, rung) from the first rung that hits, or None., _dup_target(), _look(), Path, Target (+13 more)

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

### Community 53 - "handoff/__init__.py"
Cohesion: 0.11
Nodes (29): Answerable, button_clicked(), ext_call(), Extension, handback_button(), Future, Protocol, The hand-back extension (the Chrome toolbar button): its service worker, never… (+21 more)

### Community 54 - "Session"
Cohesion: 0.15
Nodes (20): BrowserContext, Playwright, playwright_async_api, Playwright, no decisions: the open session, the site lock, our own input,…, _alive(), check_viewport(), close_session(), _extension() (+12 more)

### Community 55 - "Look"
Cohesion: 0.11
Nodes (38): Cols, _columns(), column_header(), headings(), is_header(), is_word(), off_table(), page_texts() (+30 more)

### Community 56 - "Capability"
Cohesion: 0.13
Nodes (27): re, _ask(), ask_inputs(), _ask_rows(), given_inputs(), input_type(), _missing_crops(), mistyped() (+19 more)

### Community 57 - "yaml"
Cohesion: 0.27
Nodes (8): MonkeyPatch, parametrize, Path, Every capability saved in the top-level artifacts/ folder (Decision 6) loads in…, test_a_saved_artifact_loads_in_replay(), test_a_saved_artifact_round_trips(), test_the_old_artifacts_folder_is_gone(), yaml

### Community 58 - "FakeTab"
Cohesion: 0.12
Nodes (3): FakeTab, SimpleNamespace, A fake site or control tab with the Playwright calls discovery's wiring and…

### Community 59 - "test_screenshot.py"
Cohesion: 0.27
Nodes (9): _png(), asyncio, MonkeyPatch, take_look: page calls on the loop, the CPU part (OCR, drawing, encoding) in one…, ShotPage, test_page_width_reads_the_window_width(), test_snap_look_gives_the_look_png_or_none_on_timeout(), test_snap_png_passes_the_timeout_and_gives_none_on_error() (+1 more)

### Community 60 - "test_recorder_runs.py"
Cohesion: 0.13
Nodes (26): _click(), _clicks(), _go(), _names(), _nav(), _noop_click(), _paths(), Recorder behaviour pinned by live runs: detours, 404s, login clicks kept, no-op… (+18 more)

### Community 62 - "guard.py"
Cohesion: 0.18
Nodes (16): after_login_click(), _checked(), gate_click(), log(), mark_stuck(), note_call(), Ctx, Result (+8 more)

### Community 63 - "Discovery decisions"
Cohesion: 0.08
Nodes (24): Base decisions, Cuts, Discovery decisions, Q10: window size and zoom — DECIDED, Q11: notebook format — DECIDED, Q12: dropdowns — DECIDED, Q13: scrolling — DECIDED, Q14: private data in saved pictures — DECIDED (+16 more)

### Community 64 - "2. Each box, with an example"
Cohesion: 0.12
Nodes (15): 1. Diagram, 2. Each box, with an example, 3. All tools, 4. Step by step: one discovery run, 5. Notes, Browser (Playwright), Control window and site lock (Q-A), Discovery architecture (+7 more)

### Community 65 - "request.py"
Cohesion: 0.13
Nodes (21): functools, json, JsonObj, Which hosts the browser may reach (D15). The allowlist itself lives in the site…, _flat(), _json(), What a held request sends, and the same request rebuilt with edited values.…, Every value a request sends, from its query, a form body, or a JSON body… (+13 more)

### Community 66 - "ControlWindow"
Cohesion: 0.11
Nodes (19): base64, Question, ControlWindow, discovery_control(), _img(), Protocol, ControlWindow: our own "Agent control" tab, the only place a human answers.…, Answers the question on top. Closing the window (None) answers every one: fail… (+11 more)

### Community 67 - "2. Components"
Cohesion: 0.12
Nodes (15): 1. Diagram, 2. Components, 3. Step types, 4. Worked example: ParaBank login + read balance, 5. Notes, Actor, Artifact (made by discovery, not replay), Browser setup (+7 more)

### Community 68 - "HeldPage"
Cohesion: 0.16
Nodes (6): FormRoute, HeldPage, HeldRoute, NeverAnsweredGate, Like Playwright: while a form POST (a navigation) is held, `page.screenshot()`…, The human clicks Done while their own send's Gate 1 is still open and never…

### Community 69 - "Pure-Visual Discovery Notebook: Build Plan"
Cohesion: 0.09
Nodes (22): 10. Open risks, 1. Global constraints (every task must follow these), 2. Review focus (inputs no spec line covers, but likely to bite), 3. What already exists (reuse, or its visual version), 3a. How the agent is built today (`agent.ipynb` STEP 4, `src/cua/agent.py`), 3b. Existing handoff rules: when a human is called in, 3c. Existing tools → the new tools, 4. New dependencies (checked on PyPI, 2026-09-28) (+14 more)

### Community 71 - "SiteLock"
Cohesion: 0.16
Nodes (12): CdpSender, Protocol, SiteLock: the site tab ignores all real input (CDP…, The one method of a Playwright ``CDPSession`` the lock uses. ``params`` is a…, The site tab ignores all real input (CDP). Lifted only around our own action or…, SiteLock, FakeCdp, asyncio (+4 more)

### Community 72 - "test_recorder_reads.py"
Cohesion: 0.12
Nodes (25): flag_leaks(), Mark (never store) an event whose label, anchor, own text, hint or input name…, asyncio, parametrize, What the tools log, compiled: read-only runs, tables, labels joined to values,…, An event with no page_texts (an older log) proves nothing: the proof is kept., A box's own text with nothing cut from it (a value, a button) stays off the…, _read_log() (+17 more)

### Community 73 - "ReplayResult"
Cohesion: 0.19
Nodes (9): ReplayResult, test_partial_label_when_not_success(), test_result_type_is_the_schema_one(), ReplayResult summary/outputs_line, Stop, and the Status values., test_partial_outputs_line_when_not_success(), test_result_defaults(), test_stop_carries_its_fields(), test_success_outputs_line() (+1 more)

### Community 74 - "pathlib"
Cohesion: 0.20
Nodes (4): pathlib, The hand-back extension never touches any site: no content scripts, no host…, Frozen notebook sources for the parity tests (step 10 replaced the notebooks…, Guard: no site value lives in src/. Site values belong in configs/<site>.yaml…

### Community 75 - "engine.py"
Cohesion: 0.13
Nodes (39): Drift, action_allowed(), _cleanup_step(), error_page(), finish(), is_cleanup(), judge(), login_came_back() (+31 more)

### Community 77 - "routing.py"
Cohesion: 0.10
Nodes (26): ChatAnthropic, ModelKind, ModuleType, os, build_routing_middleware(), confidence_gate(), job_tool_names(), _model_router() (+18 more)

### Community 79 - "act.py"
Cohesion: 0.20
Nodes (25): P, _count_start(), The start event's look bookkeeping: the page a run begins on, and how often…, Every value typed, entered, given or sent this run, plus the secrets (in memory…, run_values(), landed(), _landing(), make_act_tools() (+17 more)

### Community 80 - "Element"
Cohesion: 0.08
Nodes (32): crop_box(), cut_crop(), element_at(), Crops around one point: find the element there, crop around it, read text near…, Crop around the target, with every other piece of text blanked out., Pixels around the point changed. Catches password dots that OCR cannot read., read_near(), spot_changed() (+24 more)

### Community 81 - "test_import_rules.py"
Cohesion: 0.29
Nodes (13): _cua_imports(), _layer_files(), _module(), parametrize, Path, The package's import rule (docs/PRODUCTIONIZE_PLAN.md section 1), read from…, The top-level cua subpackage of every ``cua.*`` import (``import`` or ``from``)., Guard the guard: a planted forbidden import is caught in both spellings. (+5 more)

### Community 82 - "fakes.py"
Cohesion: 0.10
Nodes (13): langgraph_checkpoint_memory, The discovery agent: system prompt, middleware, optional TypeSafe routing, and…, The discovery agent's system prompt, verbatim from…, blank_png(), Shared offline fakes for the ported test suite (tests/unit, tests/integration).…, A plain PNG of this canvas size (canvas/crops decode the look's png)., _capture(), MonkeyPatch (+5 more)

### Community 84 - "Route"
Cohesion: 0.20
Nodes (3): Frame, Req, Route

### Community 85 - "build_tools"
Cohesion: 0.16
Nodes (16): AsyncFunctionDef, inspect, build_tools(), BaseTool, Ctx, observe, click, type_text, type_secret, select_option, scroll, open_path,…, test_the_prompt_lists_every_tool(), _notebook_tools() (+8 more)

### Community 86 - "cua"
Cohesion: 0.50
Nodes (3): cua, Read order, Rules

### Community 87 - "pytest"
Cohesion: 0.17
Nodes (10): pytest, _fake_llm_keys(), fixture, MonkeyPatch, Suite-wide: never let a real LLM key from `.env` reach a test (cua.config loads…, A fake direct-Anthropic key so code that builds a chat model works offline; no…, parametrize, Path (+2 more)

### Community 88 - "cua.schema"
Cohesion: 0.50
Nodes (3): cua.schema, Read order, What may NOT go here

### Community 89 - "ReplayConfig"
Cohesion: 0.13
Nodes (31): SameTextLike, Replay-only settings., ReplayConfig, Replay: runs a capability saved by discovery with plain code, no LLM (step 4:…, fill(), Put inputs into `{{name}}`. `{{secret:x}}` stays as it is: secrets go in only…, anchor_point(), find_template() (+23 more)

### Community 90 - "middleware.py"
Cohesion: 0.17
Nodes (14): Handler, langchain_agents_middleware, _arg_values(), _has_image(), LatestScreenshotOnly, NoopAnthropicPromptCachingMiddleware, AgentMiddleware, AsyncHandler (+6 more)

### Community 91 - "test_capability.py"
Cohesion: 0.21
Nodes (10): pydantic, _data(), parametrize, Path, cua.schema.Capability loads every saved artifact and refuses an unknown schema…, test_a_target_needs_a_findable_rung(), test_a_wrong_schema_version_is_refused(), test_an_unknown_key_is_refused() (+2 more)

### Community 92 - "test_goal.py"
Cohesion: 0.12
Nodes (25): Agent, Ctx, Protocol, What run_goal needs of the compiled deep agent., The deadline passed: end the run STUCK, keeping what the agent did so far., New run on a fresh thread; pass an earlier thread_id to resume it with a next…, run_goal(), _start() (+17 more)

### Community 93 - "human.py"
Cohesion: 0.18
Nodes (21): Field, _enter(), human_fills(), _in_control(), _make_ask_human(), _make_finish(), make_human_tools(), _make_request_missing_values() (+13 more)

### Community 94 - "test_value_types.py"
Cohesion: 0.36
Nodes (7): parametrize, Path, cua.schema.value_types matches both notebooks' SHAPES/TYPES exactly., SHAPES and TYPES as each notebook defines them (TYPES spreads SHAPES, so exec…, _tables(), test_tables_equal_the_notebooks(), test_value_matches_type()

### Community 95 - "rescue.py"
Cohesion: 0.12
Nodes (19): Asker, hand_back(), Future, Lock, Protocol, The shared take-over loop pieces. Each side's own take-over stays with that…, Done on the toolbar button or in the take-over panel hands back. No reminders…, A send the human started is still held: its gate is on screen next; wait for… (+11 more)

### Community 96 - "cua/__init__.py"
Cohesion: 0.33
Nodes (3): cua: shared config and the LLM model factory (direct Anthropic or an optional…, host_allowed: only the site's own hosts (D15); about:blank always., test_only_allowed_hosts_and_blank()

### Community 97 - "test_routing.py"
Cohesion: 0.21
Nodes (15): _choice(), FakeClassifier, FakeRequest, _names(), asyncio, CaptureFixture, MonkeyPatch, SimpleNamespace (+7 more)

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
Cohesion: 0.20
Nodes (28): BaseModel, _navigate(), output(), Step, Event log -> ``Capability``: steps, inputs, outputs and secrets come from the…, The {{input}} names the steps use, in order. {{secret:x}} is not an input., ``to_step``'s open_path branch, unchanged., step_inputs() (+20 more)

### Community 107 - "seen_outcome"
Cohesion: 0.67
Nodes (3): The first rule whose text (whole words, any case) appeared on screen with this…, seen_outcome(), test_text_already_on_screen_before_the_step_is_not_an_outcome()

### Community 108 - "into_box"
Cohesion: 0.11
Nodes (10): into_box(), Focus the site tab, click the box, clear what is in it, type. Retries replace…, FakeBox, FocusPage, Records the order of calls: keystrokes must come after the site tab is brought…, Live: login typed into nothing ('please enter a username and password') until a…, A text box: Ctrl/Cmd+A then Backspace clears it; type appends., test_into_box_clicks_at_the_page_point_of_the_look() (+2 more)

### Community 109 - "test_evidence.py"
Cohesion: 0.26
Nodes (16): _artifact(), masked(), fixture, MonkeyPatch, Path, save_evidence: one masked folder per run. No run value or secret is ever…, The OCR mask is tested in tests/unit/safety; here: that every PNG goes through…, _save() (+8 more)

### Community 110 - "make_ctx"
Cohesion: 0.13
Nodes (34): make_ctx(), Ctx, Session, A discovery ``Ctx`` over fakes, built like ``attach`` but with no page wiring., helped(), _only(), asyncio, fixture (+26 more)

### Community 111 - "._held"
Cohesion: 0.16
Nodes (6): pretty(), address.zipCode' -> 'Address zip code' (for the human; the key itself is kept)., Request, Gate 1: Approve, or Edit = back to the form with every value, then again.…, RouteLike, test_pretty()

### Community 112 - "BrowserConfig"
Cohesion: 0.20
Nodes (13): BrowserConfig, Settings shared by discovery and replay (the same page size at both, Q10)., LivePage, _png(), asyncio, MonkeyPatch, Path, open_session reuses a live session (a notebook re-run must not leak a browser),… (+5 more)

### Community 113 - "Replay notebook plan"
Cohesion: 0.33
Nodes (5): Decisions made here (review), Open questions for the user, Replay notebook plan, Sections, Tasks

### Community 114 - "nav.py"
Cohesion: 0.13
Nodes (25): act(), look(), Unlock the site tab, run our own input steps, relock, settle, take a new look., The only screenshot path; stores the look on the run., _press(), What a click aims at, worked out before it happens., The click itself (login clicks may send), then what it did, logged., _Target (+17 more)

### Community 115 - "where"
Cohesion: 0.19
Nodes (15): clean_label(), label_near(), merged_label(), OCR joins a label to the box beside it ('to account #16785') and reads a box…, The text above/left of the point that labels it, cleaned (clean_label): never a…, The box under the point, when OCR merged a label with this run's value in it…, R14: anchor label + offset (rung 2) and the clicked element (rung 1). The text…, where() (+7 more)

### Community 116 - "config.py"
Cohesion: 0.19
Nodes (13): dotenv, model_validator, _actions(), _find_root(), OutcomeRule, _outcomes(), Path, Shared configuration: the site profile, browser/discovery/replay settings, and… (+5 more)

### Community 117 - "test_dropdowns.py"
Cohesion: 0.16
Nodes (18): _approve(), HeldPage, _logged(), _no_crop_pixels(), asyncio, Ctx, fixture, MonkeyPatch (+10 more)

### Community 118 - "load_capability"
Cohesion: 0.18
Nodes (23): load_capability(), load_outcomes(), Path, The capability and the folder its crop paths are relative to., The capability's own `outcomes:` [{text, status, meaning}], else the site's…, fixture, MonkeyPatch, parametrize (+15 more)

### Community 119 - "ToolRouter"
Cohesion: 0.17
Nodes (10): Classifier, page_name(), AsyncHandler, ModelRequest, ModelResponse, Protocol, The URL's last path segment: no query, no ``;jsessionid=``, no trailing slash,…, Classifies the step's job with TypeSafe's Choice primitive and narrows the tool… (+2 more)

### Community 120 - "Stop"
Cohesion: 0.22
Nodes (7): Exception, What a replay run returns: its Status, the Stop that ends a run early, and…, R17 run statuses. A member is a plain str, so ``Status.SUCCESS == "SUCCESS"``., Ends the run with a status (R17). The reason never holds a value; `observed` is…, Status, Stop, StrEnum

### Community 121 - "_FakeModel"
Cohesion: 0.22
Nodes (5): _FakeModel, asyncio, Stands in for a LangChain chat model: no network, records the prompt., _Structured, test_describe_asks_the_given_model_with_labels_and_input_names_only()

### Community 122 - "agent/build.py"
Cohesion: 0.25
Nodes (7): CompiledStateGraph, deepagents, build_agent(), BaseChatModel, Ctx, build_agent: the notebook's ``AGENT = create_deep_agent(...)`` (discovery.py…, The discovery deep agent, with a checkpointer so a run can be resumed…

### Community 123 - "discovery/evidence.py"
Cohesion: 0.23
Nodes (15): _copy_capability(), _events(), _folder(), Ctx, OcrFn, Path, Redact, One masked folder per discovery run: goal, answer, events, transcript, crops,… (+7 more)

### Community 124 - "FakePage"
Cohesion: 0.25
Nodes (4): FakePage, The site page: any call made on it for the button is a bug., SitePage, FakePage

### Community 125 - "ActTab"
Cohesion: 0.25
Nodes (4): ActTab, FakeInput, A fake ``page.mouse`` / ``page.keyboard``: every call is recorded as ``(name,…, A site tab the act/nav tools drive: ``mouse``/``keyboard`` record into…

### Community 127 - "test_discovery_to_replay.py"
Cohesion: 0.36
Nodes (6): Path, Discovery's saved artifact runs in replay unchanged: build -> save -> load ->…, test_crop_paths_resolve_to_saved_files(), test_rung2_offset_hits_the_point_discovery_acted_on(), test_saved_artifact_loads_as_is(), test_steps_dispatch_to_replay_handlers()

### Community 128 - "HumanControl"
Cohesion: 0.25
Nodes (5): DoneWhileSending, HumanControl, Ctx, The human clicks Done just as their form POST is held: the gate must still show…, Takes over; while 'in control', the human opens a page and sends a form.

### Community 129 - "choose_option_at_point"
Cohesion: 0.38
Nodes (7): Confirm, LookFn, choose_option_at_index(), choose_option_at_point(), Session, Select the first option containing this text in the dropdown at (or next to)…, Select this exact live option in the Nth <select> (``index``), else the one at…

### Community 130 - "AST"
Cohesion: 0.50
Nodes (5): AST, _defs(), Path, ast.dump compare, ignoring docstrings -- the functions this step did not have…, test_the_no_global_table_functions_are_byte_identical_to_discoverys_source()

### Community 131 - "replay/wiring.py"
Cohesion: 0.11
Nodes (18): bind_control(), ControlTab, Protocol, The Playwright calls binding makes on the control tab., Point the control tab's buttons and its close at ``control``. Re-run safe: the…, _note_latest(), note_response(), Protocol (+10 more)

### Community 132 - "test_spot_changed.py"
Cohesion: 0.50
Nodes (4): _look(), ndarray, spot_changed: password dots are pixels, not OCR text. Ported from…, test_dots_count_as_change_and_blank_does_not()

### Community 141 - "cua.discovery.agent"
Cohesion: 0.50
Nodes (3): cua.discovery.agent, Read order, What may NOT go here

## Knowledge Gaps
- **159 isolated node(s):** `MODES`, `manifest_version`, `name`, `version`, `description` (+154 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **15 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Look` connect `Look` to `FakeRoute`, `replay/wiring.py`, `test_act.py`, `look.py`, `IndexPage`, `test_spot_changed.py`, `test_input.py`, `test_dropdown.py`, `DiscoveryRun`, `test_replay_rescue.py`, `test_table.py`, `steps.py`, `vision/__init__.py`, `make_replay_ctx`, `test_replay_steps.py`, `RefCounter`, `crop`, `Ctx`, `locate`, `Session`, `FakeTab`, `test_screenshot.py`, `act.py`, `Element`, `ReplayConfig`, `human.py`, `test_human.py`, `into_box`, `nav.py`, `where`, `test_dropdowns.py`, `ActTab`, `test_discovery_to_replay.py`?**
  _High betweenness centrality (0.057) - this node is a cross-community bridge._
- **Why does `Ctx` connect `Ctx` to `HumanControl`, `FakeRoute`, `replay/wiring.py`, `test_act.py`, `test_replay_inputs.py`, `test_middleware.py`, `DiscoveryRun`, `test_replay_rescue.py`, `test_replay_handback.py`, `SiteProfile`, `test_replay_wiring.py`, `test_replay_table.py`, `make_replay_ctx`, `test_replay_steps.py`, `crop`, `DiscoveryConfig`, `Session`, `Look`, `FakeTab`, `guard.py`, `HeldPage`, `ScriptedControl`, `GateControl`, `act.py`, `Element`, `Route`, `middleware.py`, `test_goal.py`, `human.py`, `rescue.py`, `test_human.py`, `nav.py`, `test_dropdowns.py`, `agent/build.py`, `discovery/evidence.py`, `FakePage`, `ActTab`?**
  _High betweenness centrality (0.053) - this node is a cross-community bridge._
- **Why does `BrowserConfig` connect `BrowserConfig` to `cli.py`, `FakeRoute`, `look.py`, `IndexPage`, `test_input.py`, `test_dropdown.py`, `test_replay_handback.py`, `SiteProfile`, `make_replay_ctx`, `test_replay_steps.py`, `RefCounter`, `replay/context.py`, `replay/evidence.py`, `DiscoveryConfig`, `test_takeover_loop.py`, `handoff/__init__.py`, `Session`, `Capability`, `yaml`, `FakeTab`, `test_screenshot.py`, `Element`, `into_box`, `config.py`, `load_capability`, `FakePage`, `ActTab`, `test_discovery_to_replay.py`?**
  _High betweenness centrality (0.047) - this node is a cross-community bridge._
- **Are the 27 inferred relationships involving `Look` (e.g. with `Ctx` and `DiscoveryRun`) actually correct?**
  _`Look` has 27 INFERRED edges - model-reasoned connections that need verification._
- **Are the 59 inferred relationships involving `Ctx` (e.g. with `LatestScreenshotOnly` and `NoopAnthropicPromptCachingMiddleware`) actually correct?**
  _`Ctx` has 59 INFERRED edges - model-reasoned connections that need verification._
- **Are the 36 inferred relationships involving `BrowserConfig` (e.g. with `Session` and `Answerable`) actually correct?**
  _`BrowserConfig` has 36 INFERRED edges - model-reasoned connections that need verification._
- **Are the 30 inferred relationships involving `ReplayConfig` (e.g. with `Ctx` and `_Request`) actually correct?**
  _`ReplayConfig` has 30 INFERRED edges - model-reasoned connections that need verification._