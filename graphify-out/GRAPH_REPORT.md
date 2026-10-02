# Graph Report - BankerAgent  (2026-10-02)

## Corpus Check
- 238 files · ~253,592 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 2958 nodes · 8598 edges · 128 communities (109 shown, 19 thin omitted)
- Extraction: 93% EXTRACTED · 7% INFERRED · 0% AMBIGUOUS · INFERRED: 602 edges (avg confidence: 0.64)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `120dab44`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- cli.py
- fakes.py
- Productionize Plan: notebooks → `src/cua/` package
- test_act.py
- Evidence README
- guard.py
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
- discovery/evidence.py
- test_cli.py
- test_replay_engine.py
- test_replay_rescue.py
- pytest
- test_replay_handback.py
- SiteProfile
- test_recorder_runs.py
- ReplayConfig
- recorder/__init__.py
- steps.py
- masked_outputs
- integration/conftest.py
- redactor
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
- SendState
- test_human_tools.py
- config.py
- cua/evidence.py
- load
- test_table.py
- DiscoveryConfig
- test_replay_wiring.py
- test_send_guard.py
- test_control_window.py
- cua.vision
- test_takeover_loop.py
- test_extension.py
- Session
- Look
- ask_inputs
- save.py
- FakeTab
- Frame
- table.py
- langgraph_types
- test_screenshot.py
- Discovery decisions
- 2. Each box, with an example
- safety/__init__.py
- ControlWindow
- 2. Components
- test_middleware.py
- Pure-Visual Discovery Notebook: Build Plan
- IdMask
- SiteLock
- crop
- test_eval.py
- FakeLock
- Capability
- HeldPage
- test_routing.py
- FakeWin
- eval.py
- Ctx
- types
- test_prompt.py
- copy
- Response
- build_tools
- cua
- test_crops.py
- cua.schema
- ReplayResult
- handoff/__init__.py
- yaml
- test_goal.py
- human.py
- Route
- locate
- HeldRoute
- BrowserConfig
- test_human.py
- interface-ai-cua
- cua.browser
- cua.handoff
- cua.safety
- cua.discovery
- cua.discovery.recorder
- cua.replay
- schema/__init__.py
- FakePage
- act.py
- observe.py
- make_ctx
- ._held
- one_at_a_time
- Replay notebook plan
- Box
- FakeBox
- FocusPage
- test_dropdowns.py
- load_capability
- ScriptedControl
- _no_crop_pixels
- _FakeModel
- Safety: mask account ids (last 3 visible), no screen text to TypeSafe, profile wiped
- GateControl
- background.js
- discovery/wiring.py
- helpers.py
- cua.discovery.agent

## God Nodes (most connected - your core abstractions)
1. `Look` - 126 edges
2. `make_ctx()` - 101 edges
3. `Ctx` - 89 edges
4. `BrowserConfig` - 86 edges
5. `build_capability()` - 78 edges
6. `ReplayConfig` - 72 edges
7. `_meta()` - 65 edges
8. `make_replay_ctx()` - 65 edges
9. `Box` - 64 edges
10. `Element` - 63 edges

## Surprising Connections (you probably didn't know these)
- `test_the_login_click_before_a_menu_link_is_kept()` --calls--> `step_events()`  [INFERRED]
  tests/unit/discovery/recorder/test_recorder_runs.py → src/cua/discovery/recorder/events.py
- `test_typed_ok_words_tolerant_digits_exact()` --calls--> `typed_ok()`  [INFERRED]
  tests/unit/replay/test_locate.py → src/cua/replay/locate.py
- `test_anchor_label_matches_ocr_merged_with_a_value()` --calls--> `same_label()`  [INFERRED]
  tests/unit/replay/test_locate.py → src/cua/replay/locate.py
- `test_a_target_needs_a_findable_rung()` --calls--> `Target`  [INFERRED]
  tests/unit/schema/test_capability.py → src/cua/schema/capability.py
- `test_meta_is_loose()` --calls--> `CapabilityMeta`  [INFERRED]
  tests/unit/schema/test_capability.py → src/cua/schema/capability.py

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

## Communities (128 total, 19 thin omitted)

### Community 0 - "cli.py"
Cohesion: 0.13
Nodes (28): argparse, Namespace, _cap_name(), check_eval(), _close(), default_site(), discover(), _load_cap() (+20 more)

### Community 1 - "fakes.py"
Cohesion: 0.10
Nodes (12): FakeControl, FakePage, FakeRoute, Shared offline fakes for the ported test suite (tests/unit, tests/integration).…, A fake discovery/replay ``CONTROL`` surface (what ``ControlWindow`` presents).…, A fake ``playwright.async_api.Route``: records every…, A fake ``playwright.async_api.Page``. Every awaited method is recorded in…, asyncio (+4 more)

### Community 2 - "Productionize Plan: notebooks → `src/cua/` package"
Cohesion: 0.12
Nodes (16): 10. Line-count offenders (today), 1. Package tree, 2. De-duplication (checked by AST diff of both notebooks), 3. State: globals → explicit objects, 4. Async and typing, 5. Notebooks after the move, 6. Tests, 7. ML-engineering practices (kept small) (+8 more)

### Community 3 - "test_act.py"
Cohesion: 0.06
Nodes (89): Items, (value, pattern) for an extract: the whole box when it is exactly the type,…, value_in_box(), blank_png(), make_look(), A plain PNG of this canvas size (canvas/crops decode the look's png)., A look whose elements are numbered 1.. in order (ref, text, box)., Driven (+81 more)

### Community 5 - "guard.py"
Cohesion: 0.13
Nodes (21): log_sent_dropdowns(), Ctx, A dropdown whose value a send carries becomes a step (discovery's send-guard…, A dropdown whose value this send carries is a step, even one left on its…, after_login_click(), _checked(), gate_click(), log() (+13 more)

### Community 6 - "test_recorder_types.py"
Cohesion: 0.23
Nodes (14): Typed inputs: the recorder infers each input's type from the shapes of the…, Older logs (and any tool that did not log shapes) never guess a type., test_a_plain_whole_number_is_a_number_so_decimals_pass_replay_later(), test_a_value_with_no_shape_is_string(), test_all_currency_values_make_a_currency_input(), test_an_event_without_shapes_is_string(), test_human_entry_is_typed_too(), test_mixed_shapes_fall_back_to_their_common_type() (+6 more)

### Community 7 - "test_replay_inputs.py"
Cohesion: 0.12
Nodes (34): select(), type_(), _cap(), ClearPage, env(), FakeForm, FakePage, asyncio (+26 more)

### Community 8 - "test_input.py"
Cohesion: 0.11
Nodes (26): act(), into_box(), Lock, Page, Session, Step, Unlock the site tab, run our own input steps, relock, settle, take a new look., Focus the site tab, click the box, clear what is in it, type. Retries replace… (+18 more)

### Community 9 - "middleware.py"
Cohesion: 0.11
Nodes (22): CompiledStateGraph, deepagents, Handler, langchain_agents_middleware, langgraph_checkpoint_memory, build_agent(), BaseChatModel, Ctx (+14 more)

### Community 10 - "test_dropdown.py"
Cohesion: 0.08
Nodes (36): BaseException, Confirm, LookFn, choose_option_at_index(), choose_option_at_point(), list_options(), Session, Every option of the dropdown at this page point ([] if it is not a dropdown).… (+28 more)

### Community 12 - "Replay decisions"
Cohesion: 0.08
Nodes (24): R10: where the compile step lives — DECIDED, R11: why compile, if `response_format` exists? — PROPOSED, R12: what each step type compiles to — PROPOSED, R13: target schema — PROPOSED, R14: what rung 2 needs that discovery doesn't record — DONE, R15: auto-approve at replay — PROPOSED, R16: dead ends and retries at compile — PROPOSED, R17: replay result statuses — PROPOSED (+16 more)

### Community 16 - "discovery/evidence.py"
Cohesion: 0.06
Nodes (65): Saved, The current run (the one the send guard serves)., artifact_mask(), _copy_capability(), _events(), _folder(), Ctx, OcrFn (+57 more)

### Community 17 - "test_cli.py"
Cohesion: 0.12
Nodes (35): For a name or a path (``[a-z0-9_]`` only): the last digits, no stars., _cap_file(), _fake_session(), _patch_session(), CaptureFixture, MonkeyPatch, parametrize, Path (+27 more)

### Community 18 - "test_replay_engine.py"
Cohesion: 0.20
Nodes (45): cap(), click(), extract(), _finish(), _login_cap(), _no_snap(), _only(), _pcap() (+37 more)

### Community 19 - "test_replay_rescue.py"
Cohesion: 0.20
Nodes (27): The guard keeps its own reference to the control window: swap both., set_control(), _env(), _fail_clicks(), HumanControl, HumanSimple, asyncio, MonkeyPatch (+19 more)

### Community 20 - "pytest"
Cohesion: 0.06
Nodes (42): pytest, _fake_llm_keys(), fixture, MonkeyPatch, Suite-wide: never let a real LLM key from `.env` reach a test (cua.config loads…, A fake Anthropic key so code that builds a chat model works offline., parametrize, Path (+34 more)

### Community 21 - "test_replay_handback.py"
Cohesion: 0.20
Nodes (18): _bctx(), Ext, Human, PanelDone, asyncio, Ctx, parametrize, The toolbar hand-back button during a rescue (its service worker, never the… (+10 more)

### Community 22 - "SiteProfile"
Cohesion: 0.07
Nodes (41): model_validator, _actions(), _find_root(), load_site(), OutcomeRule, _outcomes(), Path, The nearest folder at or above `start` that has a ``configs/`` folder. (+33 more)

### Community 23 - "test_recorder_runs.py"
Cohesion: 0.15
Nodes (22): _click(), _clicks(), _go(), _names(), _nav(), _noop_click(), _paths(), Recorder behaviour pinned by live runs: detours, 404s, login clicks kept, no-op… (+14 more)

### Community 24 - "ReplayConfig"
Cohesion: 0.13
Nodes (29): SameTextLike, Replay-only settings., ReplayConfig, Replay: runs a capability saved by discovery with plain code, no LLM (step 4:…, fill(), Put inputs into `{{name}}`. `{{secret:x}}` stays as it is: secrets go in only…, anchor_point(), find_template() (+21 more)

### Community 25 - "recorder/__init__.py"
Cohesion: 0.07
Nodes (57): check_savable(), Raise NotSaved before any model call when this run cannot become a capability., ``build_capability``'s refusals, unchanged: a leaked value, a blind dropdown,…, _refuse(), used_inputs(), checkpoint(), The capability's checkpoint: the text replay must see to call the run a…, C: after a send, the page's own response proves success (the agent's proof only… (+49 more)

### Community 26 - "steps.py"
Cohesion: 0.09
Nodes (51): Point, ask_option(), The one mid-run prompt: the given value is not a live option. Choose one, blank…, Bug B: the value is one of the OCR words. Digits exact ($10.00 is 10.00); words…, typed_ok(), changed(), choose_option(), do_click() (+43 more)

### Community 27 - "masked_outputs"
Cohesion: 0.33
Nodes (6): masked_outputs(), JsonValue, Names and shape only: a value is ***, a table keeps its rows and columns, every…, parametrize, test_masked_outputs_hide_every_option(), test_masked_outputs_keep_the_shape()

### Community 29 - "redactor"
Cohesion: 0.06
Nodes (54): Pattern, mask_png(), _num(), OcrFn, Secrets masked whole, then ids to their last digits, then the run's values. Ids…, Black out every OCR box whose text holds a run value or secret. With ``ids``, a…, text -> text with every value masked. Numbers match however they are written…, redactor() (+46 more)

### Community 30 - "test_replay_table.py"
Cohesion: 0.23
Nodes (17): _cap(), _defs(), Page, asyncio, Ctx, MonkeyPatch, Path, do_extract_table: find the header by its label, read the rows with discovery's… (+9 more)

### Community 31 - "test_session.py"
Cohesion: 0.23
Nodes (14): LivePage, _png(), asyncio, MonkeyPatch, Path, open_session reuses a live session (a notebook re-run must not leak a browser),…, The profile (cookies, cache, history of a bank session) was left in /tmp after…, _session() (+6 more)

### Community 32 - "test_notebooks.py"
Cohesion: 0.26
Nodes (16): Call, Module, _bind(), _code_cells(), _markdown(), _offline_namespace(), parametrize, Path (+8 more)

### Community 33 - "build_capability"
Cohesion: 0.07
Nodes (74): build_capability(), Steps, inputs and secrets come from the log only. The model's text cannot fail…, flag_leaks(), Mark (never store) an event whose label, anchor, own text, hint or input name…, _ev(), _id_cap(), _logout(), _meta() (+66 more)

### Community 34 - "make_replay_ctx"
Cohesion: 0.14
Nodes (29): make_replay_ctx(), A real Ctx (real SendGuard, real ReplayRun) over a fake page/control/lock.…, _extract(), _notebook_assign(), _options_cap(), OptionsPage, _pcap(), asyncio (+21 more)

### Community 35 - "test_replay_evidence.py"
Cohesion: 0.23
Nodes (23): Path, write_cap(), _all_text(), fake_ocr(), _png(), Ctx, fixture, Path (+15 more)

### Community 36 - "CLAUDE.md (project instructions)"
Cohesion: 0.12
Nodes (19): CLAUDE.md (project instructions), D101: labeled_value refuses a table-header resolution (general fix), D102: label_header/value_header flags ported into agent.py + cli.py capture path, D92: Evidence Capture Helpers (save_discovery_evidence/save_replay_evidence), D93: Pre-existing 02_artifact_schema.py IndexError bug, D95: Missing create_deep_agent import found live in BROWSER 12, D96: build_agent() goal_text vs given_text field-name bug, D97: cua replay --login flag + repeated Balance header trap (+11 more)

### Community 37 - "test_replay_steps.py"
Cohesion: 0.08
Nodes (39): mk_look(), navigate(), _click_env(), _form_png(), GotoPage, _judge(), Page, asyncio (+31 more)

### Community 38 - "RefCounter"
Cohesion: 0.09
Nodes (35): RapidOCR, draw_numbered(), number(), ocr(), ocr_engine(), NDArray, uint8, The shared RapidOCR engine, OCR itself, numbering and the numbered-box overlay.… (+27 more)

### Community 39 - "manifest.json"
Cohesion: 0.11
Nodes (18): action, default_icon, default_title, background, service_worker, 128, 16, 32 (+10 more)

### Community 41 - "SendState"
Cohesion: 0.25
Nodes (4): LookLike, Protocol, What the guard reads and writes on a run (DiscoveryRun / ReplayRun satisfy it)., SendState

### Community 42 - "test_human_tools.py"
Cohesion: 0.35
Nodes (13): _ctx(), asyncio, Ctx, MonkeyPatch, finish_business_outcome / request_missing_values / ask_human (the human-facing…, test_ask_human_asks_with_the_question(), test_finish_needs_the_proof_on_the_screen(), test_no_fields_given() (+5 more)

### Community 43 - "config.py"
Cohesion: 0.06
Nodes (41): dataclasses, dotenv, pathlib, re, Shared configuration: the site profile, browser/discovery/replay settings, and…, Ctx, note_takeover_send(), Page (+33 more)

### Community 44 - "cua/evidence.py"
Cohesion: 0.11
Nodes (21): pydantic, config_hash(), git_sha(), JsonValue, Path, Evidence helpers shared by discovery and replay: masking a JSON-able tree,…, `git rev-parse HEAD`, or "unknown" (no git, not a repo, any failure)., sha256 of the repr of the frozen configs plus the site name. (+13 more)

### Community 45 - "load"
Cohesion: 0.16
Nodes (17): functools, dropdown_options(), mismatches(), _norm_num(), Dropdown, Values a send carries that the human never gave, and the dropdown choices to…, Numbers being sent that the human never gave, e.g. account 1450 vs 1400. Only…, For each key: the options of the page dropdown whose CURRENT value is exactly… (+9 more)

### Community 46 - "test_table.py"
Cohesion: 0.18
Nodes (15): AST, _defs(), _is_header(), Path, The shared OCR table reader: parity between cua.vision.table and both…, ast.dump compare, ignoring docstrings -- the functions this step did not have…, tests/replay/test_table_replay.py's own SHARED set is the contract this module…, _read() (+7 more)

### Community 47 - "DiscoveryConfig"
Cohesion: 0.16
Nodes (31): DiscoveryConfig, Discovery-only settings., Discovery: an LLM agent learns a task once and the recorder saves it as a…, attach(), new_run(), A fresh run for this goal (run_goal's ``HANDOFF = HandoffState(goal=goal)``)., Route every request through a new send guard, open the control window. Re-run…, make_session() (+23 more)

### Community 48 - "test_replay_wiring.py"
Cohesion: 0.08
Nodes (24): Working values for one run. Replaced by a new one in ``replay``'s ``finally``…, What the mismatch check compares a send against (SendState)., ReplayRun, attach(), Session, Wire replay onto an open session and return its Ctx., _fake_session(), asyncio (+16 more)

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
Cohesion: 0.19
Nodes (14): Control, Ext, asyncio, parametrize, The hand-back extension's toolbar button: its service worker only, never the…, The extension's service worker: a click counter and a badge., test_a_click_count_rise_returns(), test_a_missing_or_broken_extension_gives_none() (+6 more)

### Community 54 - "Session"
Cohesion: 0.12
Nodes (25): BrowserContext, Playwright, Dropdown, Page, The page's dropdowns, read BEFORE an action (never while guard_send holds a…, The index (among the page's <select>s) of the native dropdown right under this…, read_dropdowns(), select_under() (+17 more)

### Community 55 - "Look"
Cohesion: 0.08
Nodes (63): Cols, _columns(), clean_label(), column_header(), headings(), is_header(), is_word(), label_near() (+55 more)

### Community 56 - "ask_inputs"
Cohesion: 0.11
Nodes (20): _ask(), ask_inputs(), _ask_rows(), given_inputs(), input_type(), mistyped(), Ctx, The caller's values, by the capability's own input names (any case). Any other… (+12 more)

### Community 57 - "save.py"
Cohesion: 0.11
Nodes (33): BaseChatModel, Save the run as a capability, or say plainly why not. Checked before the model…, _save(), NotSaved, A run that must not become a capability. The message says why, for a person to…, ArtifactMask, _crop(), crops_for() (+25 more)

### Community 58 - "FakeTab"
Cohesion: 0.10
Nodes (6): ActTab, FakeTab, SimpleNamespace, A fake site or control tab with the Playwright calls discovery's wiring and…, A site tab the act/nav tools drive: ``mouse``/``keyboard`` record into…, A page script: recorded, answered by ``answer`` (default: no dropdown anywhere).

### Community 60 - "table.py"
Cohesion: 0.16
Nodes (18): cell_shape(), col_of(), column_spans(), like_rows(), The shared OCR table reader: discovery and replay use it to find a table's…, A table's end: a line that no longer looks like its rows (a footer, a menu, a…, date', 'amount', or 'text': enough to tell a row cell from a footer line in its…, Each header's x-range: out to the midpoint with its neighbours on the header… (+10 more)

### Community 62 - "test_screenshot.py"
Cohesion: 0.27
Nodes (9): _png(), asyncio, MonkeyPatch, take_look: page calls on the loop, the CPU part (OCR, drawing, encoding) in one…, ShotPage, test_page_width_reads_the_window_width(), test_snap_look_gives_the_look_png_or_none_on_timeout(), test_snap_png_passes_the_timeout_and_gives_none_on_error() (+1 more)

### Community 63 - "Discovery decisions"
Cohesion: 0.08
Nodes (25): Base decisions, Cuts, Discovery decisions, Q10: window size and zoom — DECIDED, Q11: notebook format — DECIDED, Q12: dropdowns — DECIDED, Q13: scrolling — DECIDED, Q14: private data in saved pictures — DECIDED (+17 more)

### Community 64 - "2. Each box, with an example"
Cohesion: 0.12
Nodes (15): 1. Diagram, 2. Each box, with an example, 3. All tools, 4. Step by step: one discovery run, 5. Notes, Browser (Playwright), Control window and site lock (Q-A), Discovery architecture (+7 more)

### Community 65 - "safety/__init__.py"
Cohesion: 0.15
Nodes (19): JsonObj, Safety: what may leave the tab (hosts, the two send gates) and keeping values…, _flat(), _json(), Protocol, What a held request sends, and the same request rebuilt with edited values.…, The fields of a ``playwright.async_api.Request`` the guard reads., Every value a request sends, from its query, a form body, or a JSON body… (+11 more)

### Community 66 - "ControlWindow"
Cohesion: 0.09
Nodes (21): base64, json, Question, ControlWindow, discovery_control(), _img(), Protocol, ControlWindow: our own "Agent control" tab, the only place a human answers.… (+13 more)

### Community 67 - "2. Components"
Cohesion: 0.12
Nodes (15): 1. Diagram, 2. Components, 3. Step types, 4. Worked example: ParaBank login + read balance, 5. Notes, Actor, Artifact (made by discovery, not replay), Browser setup (+7 more)

### Community 68 - "test_middleware.py"
Cohesion: 0.16
Nodes (22): AIMessage, Ctx, 3.5: keep the text the model wrote before its tool calls as ``ctx.run.why``…, RecordWhy, _answer(), asyncio, parametrize, SimpleNamespace (+14 more)

### Community 69 - "Pure-Visual Discovery Notebook: Build Plan"
Cohesion: 0.09
Nodes (22): 10. Open risks, 1. Global constraints (every task must follow these), 2. Review focus (inputs no spec line covers, but likely to bite), 3. What already exists (reuse, or its visual version), 3a. How the agent is built today (`agent.ipynb` STEP 4, `src/cua/agent.py`), 3b. Existing handoff rules: when a human is called in, 3c. Existing tools → the new tools, 4. New dependencies (checked on PyPI, 2026-09-28) (+14 more)

### Community 70 - "IdMask"
Cohesion: 0.13
Nodes (20): _clean(), _png(), OcrFn, Redact, A masked PNG: run values and secrets blacked out; with ``ids``, account ids…, _drift_lines(), Ctx, OcrFn (+12 more)

### Community 71 - "SiteLock"
Cohesion: 0.16
Nodes (12): CdpSender, Protocol, SiteLock: the site tab ignores all real input (CDP…, The one method of a Playwright ``CDPSession`` the lock uses. ``params`` is a…, The site tab ignores all real input (CDP). Lifted only around our own action or…, SiteLock, FakeCdp, asyncio (+4 more)

### Community 72 - "crop"
Cohesion: 0.17
Nodes (16): canvas(), crop(), into_box(), Step, Crop around the target, every other text blanked (sized to the current canvas)., Focus the site tab, click the box, clear it, type (see…, The size of the image the model is looking at right now., _dropdown_refusal() (+8 more)

### Community 73 - "test_eval.py"
Cohesion: 0.18
Nodes (19): _cap(), _ok(), JsonValue, Path, cua.eval: summarize N replay results into a stability report. Pure, no browser., _row(), test_a_click_after_typing_an_input_sends_data(), test_a_step_that_left_its_first_choice_rung_is_a_fallback() (+11 more)

### Community 75 - "Capability"
Cohesion: 0.11
Nodes (47): Drift, Exception, R7: nothing kept. A fresh run, and the guard reads that one from now on., wipe(), action_allowed(), _cleanup_step(), error_page(), finish() (+39 more)

### Community 76 - "HeldPage"
Cohesion: 0.16
Nodes (7): FormRoute, HangPage, HeldPage, NeverAnsweredGate, Like Playwright: while a form POST (a navigation) is held, `page.screenshot()`…, `evaluate` also never returns while a request is held, as live., The human clicks Done while their own send's Gate 1 is still open and never…

### Community 77 - "test_routing.py"
Cohesion: 0.05
Nodes (64): ChatAnthropic, ModelKind, ModuleType, os, build_routing_middleware(), Classifier, confidence_gate(), job_tool_names() (+56 more)

### Community 79 - "eval.py"
Cohesion: 0.14
Nodes (20): Histogram, EvalReport, fallback_steps(), _hist_line(), _histograms(), _is_fallback(), _output_stability(), JsonValue (+12 more)

### Community 80 - "Ctx"
Cohesion: 0.13
Nodes (25): playwright_async_api, act(), choose_option(), _count_start(), Ctx, dropdown_under(), look(), Page (+17 more)

### Community 81 - "types"
Cohesion: 0.18
Nodes (9): pretty(), address.zipCode' -> 'Address zip code' (for the human; the key itself is kept)., parametrize, SimpleNamespace, sent_fields/rebuilt/pretty: what a request sends, and the same request with…, test_json_body_is_flattened_with_dotted_keys_and_lists_dropped(), test_parity_with_each_notebook(), test_pretty() (+1 more)

### Community 82 - "test_prompt.py"
Cohesion: 0.11
Nodes (9): The discovery agent: system prompt, middleware, optional TypeSafe routing, and…, The discovery agent's system prompt, verbatim from…, _capture(), MonkeyPatch, build_agent: the notebook's create_deep_agent call, with routing appended only…, test_build_agent_wires_the_notebooks_agent(), test_routing_is_appended_after_the_notebooks_middleware(), test_the_page_path_is_read_live() (+1 more)

### Community 84 - "Response"
Cohesion: 0.19
Nodes (8): _note_latest(), note_response(), Protocol, The Playwright ``Response`` fields note_response reads., The once-per-page listener: note on the ctx of the latest attach to this page., Keep the main document's HTTP status (not sub-resources, not iframes)., _Request, Response

### Community 85 - "build_tools"
Cohesion: 0.16
Nodes (16): AsyncFunctionDef, inspect, build_tools(), BaseTool, Ctx, observe, click, type_text, type_secret, select_option, scroll, open_path,…, test_the_prompt_lists_every_tool(), _notebook_tools() (+8 more)

### Community 86 - "cua"
Cohesion: 0.50
Nodes (3): cua, Read order, Rules

### Community 87 - "test_crops.py"
Cohesion: 0.22
Nodes (12): _form(), _look(), _png(), ndarray, crop_box/cut_crop/read_near/element_at/screens_same: the crop and comparison…, A 200x60 page: one bordered input box at (20,20)-(167,39), optionally with…, Live: a click changed the focus ring, so the old pixel check said 'typed', but…, test_crop_box_around_a_bare_point_uses_point_crop() (+4 more)

### Community 88 - "cua.schema"
Cohesion: 0.50
Nodes (3): cua.schema, Read order, What may NOT go here

### Community 89 - "ReplayResult"
Cohesion: 0.16
Nodes (11): ReplayResult, test_partial_label_when_not_success(), test_result_type_is_the_schema_one(), test_the_outputs_line_shows_rows(), ReplayResult summary/outputs_line, Stop, and the Status values., test_partial_outputs_line_when_not_success(), test_result_defaults(), test_stop_carries_its_fields() (+3 more)

### Community 90 - "handoff/__init__.py"
Cohesion: 0.20
Nodes (15): Answerable, button_clicked(), ext_call(), Extension, handback_button(), Future, Protocol, The hand-back extension (the Chrome toolbar button): its service worker, never… (+7 more)

### Community 91 - "yaml"
Cohesion: 0.12
Nodes (17): MonkeyPatch, parametrize, Path, Every capability saved in the top-level artifacts/ folder (Decision 6) loads in…, test_a_saved_artifact_loads_in_replay(), test_a_saved_artifact_round_trips(), test_the_old_artifacts_folder_is_gone(), _data() (+9 more)

### Community 92 - "test_goal.py"
Cohesion: 0.10
Nodes (31): An evidence screenshot: short timeout, None on failure (never hangs on a held…, snap(), Agent, Ctx, Protocol, run_goal: one goal through the discovery agent (moved from discovery.py…, What run_goal needs of the compiled deep agent., The deadline passed: end the run STUCK, keeping what the agent did so far. (+23 more)

### Community 93 - "human.py"
Cohesion: 0.15
Nodes (26): Field, Every shape the whole value matches, in precedence order. Safe to log: names,…, shapes_of(), _enter(), _from_goal(), human_fills(), _in_control(), _make_ask_human() (+18 more)

### Community 94 - "Route"
Cohesion: 0.20
Nodes (3): Frame, Req, Route

### Community 95 - "locate"
Cohesion: 0.21
Nodes (21): locate(), Path, Target, (point, rung) from the first rung that hits, or None., _dup_target(), _look(), Path, Target (+13 more)

### Community 96 - "HeldRoute"
Cohesion: 0.22
Nodes (4): DoneWhileSending, HeldRoute, Ctx, The human clicks Done just as their form POST is held: the gate must still show…

### Community 97 - "BrowserConfig"
Cohesion: 0.08
Nodes (40): Our own input into the locked site tab: ``act`` (unlock, run steps, relock,…, The response to a send lands after the human's approval, not after the click:…, wait_for_change(), BrowserConfig, Settings shared by discovery and replay (the same page size at both, Q10)., canvas_size(), NDArray, uint8 (+32 more)

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
Cohesion: 0.15
Nodes (36): BaseModel, _check_login_order(), _navigate(), output(), Step, Event log -> ``Capability``: steps, inputs, outputs and secrets come from the…, The {{input}} names the steps use, in order. {{secret:x}} is not an input., Every secret is typed before the first click (the login). Replay clicking Log… (+28 more)

### Community 107 - "FakePage"
Cohesion: 0.25
Nodes (4): FakePage, The site page: any call made on it for the button is a bug., SitePage, FakePage

### Community 108 - "act.py"
Cohesion: 0.19
Nodes (26): Every value typed, entered, given or sent this run, plus the secrets (in memory…, run_values(), landed(), _landing(), make_act_tools(), _make_click(), _make_select_option(), _make_type_secret() (+18 more)

### Community 109 - "observe.py"
Cohesion: 0.32
Nodes (7): blocks(), make_observe_tools(), BaseTool, Ctx, What the model sees: a look as content blocks (text listing + the numbered…, no_session(), The URL without its ``;jsessionid=...`` (a session token) and, unless…

### Community 110 - "make_ctx"
Cohesion: 0.11
Nodes (38): make_ctx(), Ctx, Session, A discovery ``Ctx`` over fakes, built like ``attach`` but with no page wiring., helped(), _only(), asyncio, fixture (+30 more)

### Community 111 - "._held"
Cohesion: 0.23
Nodes (3): Request, Gate 1: Approve, or Edit = back to the form with every value, then again.…, RouteLike

### Community 112 - "one_at_a_time"
Cohesion: 0.29
Nodes (7): P, list_options(), Every option of the dropdown at this point ([] if it is not a dropdown)., one_at_a_time(), Result, One tool call at a time (``ctx.run.act_lock``), counted against the step budget…, _make_extract_options()

### Community 113 - "Replay notebook plan"
Cohesion: 0.33
Nodes (5): Decisions made here (review), Open questions for the user, Replay notebook plan, Sections, Tasks

### Community 114 - "Box"
Cohesion: 0.09
Nodes (22): _black(), _glyphs(), _hidden_x(), NDArray, uint8, The box's ink column runs, left to right (x ranges): one per glyph when glyphs…, The x range of the id's hidden digits, found by counting glyphs from the box's…, The whole box, or (``cut``) the id's digits before its last visible ones. (+14 more)

### Community 117 - "test_dropdowns.py"
Cohesion: 0.22
Nodes (15): _approve(), HeldPage, _logged(), asyncio, Ctx, A dropdown the send carries becomes a Select step; the guard hooks never read a…, Page reads (a held send blocks them); bring_to_front is the control window's…, Human values (zip, phone, SSN) are not in the goal: no mismatch form, no… (+7 more)

### Community 118 - "load_capability"
Cohesion: 0.11
Nodes (32): load_capability(), load_outcomes(), _missing_crops(), Path, The capability and the folder its crop paths are relative to., The capability's own `outcomes:` [{text, status, meaning}], else the site's…, The first rule whose text (whole words, any case) appeared on screen with this…, seen_outcome() (+24 more)

### Community 120 - "_no_crop_pixels"
Cohesion: 0.50
Nodes (3): _no_crop_pixels(), fixture, MonkeyPatch

### Community 121 - "_FakeModel"
Cohesion: 0.17
Nodes (9): _FakeModel, asyncio, Stands in for a LangChain chat model: no network, records the prompt., asyncio, test_describe_names_the_options_outputs(), test_describe_names_the_table_outputs(), _Structured, test_describe_asks_the_given_model_with_labels_and_input_names_only() (+1 more)

### Community 129 - "discovery/wiring.py"
Cohesion: 0.14
Nodes (16): build_ctx(), _count_nav(), _hooks(), Ctx, Session, Attach discovery to an open browser session: the send guard on every request,…, Counts on the ctx of the latest attach to this page., Discovery's post-approve steps, in guard_send's order. ``holder`` gets the ctx… (+8 more)

### Community 133 - "helpers.py"
Cohesion: 0.16
Nodes (12): FakeLock, Ctx, Replay test helpers: ``make_replay_ctx`` (a real Ctx on fakes), ``mk_look``,…, SiteLock stand-in: open() unlocks for the block., ``take_look`` always returns this look., screen(), set_shoot(), AskStop (+4 more)

### Community 141 - "cua.discovery.agent"
Cohesion: 0.50
Nodes (3): cua.discovery.agent, Read order, What may NOT go here

## Knowledge Gaps
- **162 isolated node(s):** `MODES`, `manifest_version`, `name`, `version`, `description` (+157 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **19 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Look` connect `Look` to `discovery/wiring.py`, `fakes.py`, `test_act.py`, `guard.py`, `helpers.py`, `test_input.py`, `test_dropdown.py`, `discovery/evidence.py`, `test_replay_rescue.py`, `ReplayConfig`, `steps.py`, `make_replay_ctx`, `test_replay_steps.py`, `RefCounter`, `config.py`, `Session`, `FakeTab`, `table.py`, `test_screenshot.py`, `crop`, `FakeLock`, `Ctx`, `test_crops.py`, `human.py`, `locate`, `BrowserConfig`, `test_human.py`, `act.py`, `observe.py`, `make_ctx`, `Box`, `FakeBox`, `FocusPage`, `test_dropdowns.py`?**
  _High betweenness centrality (0.056) - this node is a cross-community bridge._
- **Why does `Ctx` connect `Ctx` to `discovery/wiring.py`, `fakes.py`, `test_act.py`, `guard.py`, `helpers.py`, `test_replay_inputs.py`, `middleware.py`, `discovery/evidence.py`, `test_replay_rescue.py`, `test_replay_handback.py`, `SiteProfile`, `test_replay_table.py`, `make_replay_ctx`, `test_replay_steps.py`, `DiscoveryConfig`, `test_replay_wiring.py`, `Session`, `Look`, `FakeTab`, `Frame`, `test_middleware.py`, `crop`, `FakeLock`, `HeldPage`, `Response`, `test_goal.py`, `human.py`, `Route`, `HeldRoute`, `test_human.py`, `FakePage`, `act.py`, `observe.py`, `one_at_a_time`, `Box`, `test_dropdowns.py`, `ScriptedControl`, `GateControl`?**
  _High betweenness centrality (0.049) - this node is a cross-community bridge._
- **Why does `BrowserConfig` connect `BrowserConfig` to `cli.py`, `fakes.py`, `helpers.py`, `test_input.py`, `test_dropdown.py`, `test_replay_handback.py`, `SiteProfile`, `test_session.py`, `make_replay_ctx`, `test_replay_steps.py`, `RefCounter`, `config.py`, `cua/evidence.py`, `DiscoveryConfig`, `test_takeover_loop.py`, `test_extension.py`, `Session`, `Look`, `FakeTab`, `test_screenshot.py`, `crop`, `FakeLock`, `test_crops.py`, `handoff/__init__.py`, `yaml`, `FakePage`, `Box`, `FakeBox`, `FocusPage`, `load_capability`?**
  _High betweenness centrality (0.034) - this node is a cross-community bridge._
- **Are the 27 inferred relationships involving `Look` (e.g. with `Ctx` and `DiscoveryRun`) actually correct?**
  _`Look` has 27 INFERRED edges - model-reasoned connections that need verification._
- **Are the 60 inferred relationships involving `Ctx` (e.g. with `LatestScreenshotOnly` and `NoopAnthropicPromptCachingMiddleware`) actually correct?**
  _`Ctx` has 60 INFERRED edges - model-reasoned connections that need verification._
- **Are the 36 inferred relationships involving `BrowserConfig` (e.g. with `Session` and `Answerable`) actually correct?**
  _`BrowserConfig` has 36 INFERRED edges - model-reasoned connections that need verification._
- **Are the 59 inferred relationships involving `build_capability()` (e.g. with `saved()` and `_id_cap()`) actually correct?**
  _`build_capability()` has 59 INFERRED edges - model-reasoned connections that need verification._