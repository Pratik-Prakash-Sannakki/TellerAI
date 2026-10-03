# Graph Report - interface-ai-cua-v2  (2026-10-03)

## Corpus Check
- 330 files · ~518,392 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 126 file(s) not represented in the graph (top: .jsonl 116, (none) 3, .ipynb 2)

## Summary
- 3510 nodes · 10120 edges · 135 communities (121 shown, 14 thin omitted)
- Extraction: 85% EXTRACTED · 15% INFERRED · 0% AMBIGUOUS · INFERRED: 1548 edges (avg confidence: 0.92)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `16a177a6`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- extension.py
- Ctx
- make_replay_ctx
- test_act.py
- Evidence README
- look.py
- test_recorder_types.py
- test_replay_inputs.py
- test_input.py
- load_classifier
- test_dropdown.py
- save_discovery_evidence / save_replay_evidence (D92)
- one_at_a_time
- Five Error Demos (D30)
- langchain_typesafe
- langchain_typesafe_experimental_middleware
- test_build_tools.py
- test_replay_evidence.py
- Ctx
- cli.py
- test_replay_table.py
- test_replay_handback.py
- test_config.py
- test_recorder_runs.py
- checkpoint
- recorder/__init__.py
- discovery/evidence.py
- 2. Each box, with an example
- integration/conftest.py
- test_send_guard.py
- test_session.py
- test_read.py
- Brag Plan: Teller (v2), AI banking agent (repo: cua)
- test_act_without_a_send_does_not_wait
- Replay decisions
- redactor
- CLAUDE.md (project instructions)
- test_replay_steps.py
- test_table.py
- manifest.json
- langchain_tools
- test_evidence.py
- control_window.py
- test_replay_wiring.py
- 2. Components
- types
- test_notebooks.py
- make_session
- check_output
- test_control_window.py
- Productionize Plan: notebooks → `src/cua/` package
- test_middleware.py
- test_takeover_loop.py
- _FakeModel
- FakePage
- agent/build.py
- _where
- build_capability
- steps.py
- test_replay_rescue.py
- ReplayConfig
- save_artifact
- config.py
- replay/wiring.py
- routing.py
- ReplayResult
- Hyperframes Composition Brief: cua
- LatestScreenshotOnly
- Look
- build_routing_middleware
- ControlWindow
- test_cli.py
- step_state
- test_eval.py
- loader.py
- Capability
- ocr.py
- test_routing.py
- test_build.py
- SiteProfile
- Teller guardrails: how they decide
- discovery/wiring.py
- test_prompt.py
- copy
- vision/__init__.py
- SendGuard
- test_saved_artifacts.py
- rails.py
- pytest
- deepagents_middleware_patch_tool_calls
- BrowserConfig
- Read order
- test_goal.py
- _patch_session
- test_dropdowns.py
- Read order
- confidence_gate
- test_capability.py
- test_human.py
- interface-ai-cua
- test_rails_input.py
- test_import_rules.py
- MonkeyPatch
- test_discover_wires_like_the_notebook
- test_human_tools.py
- Request
- schema/__init__.py
- test_eval_replays_n_times_in_one_session
- Box
- NeMo Guardrails for Teller (discovery) — design
- make_ctx
- cua.browser
- FakeWin
- langchain_agents
- OnlyOurTools
- Agent architecture (discovery)
- .classify
- Path
- load_capability
- GotoPage
- _rails_site
- test_llm.py
- test_rails_nemo.py
- background.js
- test_evidence_clean.py
- eval.py
- _fake_session
- build_tools
- test_site_lock.py
- load
- middleware.py
- Pure-Visual Discovery Notebook: Build Plan
- FakeLock
- cua/__init__.py
- Agent

## God Nodes (most connected - your core abstractions)
1. `Ctx` - 161 edges
2. `Ctx` - 127 edges
3. `Look` - 125 edges
4. `make_ctx()` - 105 edges
5. `build_capability()` - 83 edges
6. `make_replay_ctx()` - 69 edges
7. `Capability` - 68 edges
8. `_meta()` - 68 edges
9. `BrowserConfig` - 56 edges
10. `Box` - 55 edges

## Surprising Connections (you probably didn't know these)
- `R4: reuse discovery's code — DECIDED` --references--> `SiteLock`  [INFERRED]
  notebooks/replay/DECISIONS.md → src/cua/browser/site_lock.py
- `Browser setup` --references--> `SiteLock`  [INFERRED]
  notebooks/replay/replay_architecture.md → src/cua/browser/site_lock.py
- `Decisions (user, 2026-10-01)` --references--> `SiteProfile`  [INFERRED]
  docs/PRODUCTIONIZE_PLAN.md → src/cua/config.py
- `Open questions (user's call)` --references--> `SiteProfile`  [INFERRED]
  docs/PRODUCTIONIZE_PLAN.md → src/cua/config.py
- `1. What the guardrails are` --references--> `OnlyOurTools`  [INFERRED]
  docs/GUARDRAILS.md → src/cua/discovery/agent/middleware.py

## Import Cycles
- 3-file cycle: `src/cua/discovery/tools/__init__.py -> src/cua/discovery/tools/read.py -> src/cua/discovery/tools/guard.py -> src/cua/discovery/tools/__init__.py`
- 3-file cycle: `src/cua/discovery/tools/__init__.py -> src/cua/discovery/tools/act.py -> src/cua/discovery/tools/guard.py -> src/cua/discovery/tools/__init__.py`
- 3-file cycle: `src/cua/discovery/tools/__init__.py -> src/cua/discovery/tools/act.py -> src/cua/discovery/tools/observe.py -> src/cua/discovery/tools/__init__.py`
- 3-file cycle: `src/cua/discovery/tools/__init__.py -> src/cua/discovery/tools/human.py -> src/cua/discovery/tools/observe.py -> src/cua/discovery/tools/__init__.py`
- 3-file cycle: `src/cua/discovery/tools/guard.py -> src/cua/discovery/tools/human.py -> src/cua/discovery/tools/observe.py -> src/cua/discovery/tools/guard.py`
- 3-file cycle: `src/cua/discovery/tools/__init__.py -> src/cua/discovery/tools/nav.py -> src/cua/discovery/tools/guard.py -> src/cua/discovery/tools/__init__.py`
- 3-file cycle: `src/cua/discovery/tools/__init__.py -> src/cua/discovery/tools/nav.py -> src/cua/discovery/tools/observe.py -> src/cua/discovery/tools/__init__.py`
- 4-file cycle: `src/cua/discovery/tools/__init__.py -> src/cua/discovery/tools/act.py -> src/cua/discovery/tools/human.py -> src/cua/discovery/tools/observe.py -> src/cua/discovery/tools/__init__.py`
- 4-file cycle: `src/cua/discovery/tools/__init__.py -> src/cua/discovery/tools/act.py -> src/cua/discovery/tools/observe.py -> src/cua/discovery/tools/guard.py -> src/cua/discovery/tools/__init__.py`
- 4-file cycle: `src/cua/discovery/tools/__init__.py -> src/cua/discovery/tools/human.py -> src/cua/discovery/tools/observe.py -> src/cua/discovery/tools/guard.py -> src/cua/discovery/tools/__init__.py`
- 4-file cycle: `src/cua/discovery/tools/__init__.py -> src/cua/discovery/tools/nav.py -> src/cua/discovery/tools/observe.py -> src/cua/discovery/tools/guard.py -> src/cua/discovery/tools/__init__.py`
- 5-file cycle: `src/cua/discovery/tools/__init__.py -> src/cua/discovery/tools/read.py -> src/cua/discovery/tools/guard.py -> src/cua/discovery/tools/human.py -> src/cua/discovery/tools/observe.py -> src/cua/discovery/tools/__init__.py`
- 5-file cycle: `src/cua/discovery/tools/__init__.py -> src/cua/discovery/tools/act.py -> src/cua/discovery/tools/guard.py -> src/cua/discovery/tools/human.py -> src/cua/discovery/tools/observe.py -> src/cua/discovery/tools/__init__.py`
- 5-file cycle: `src/cua/discovery/tools/__init__.py -> src/cua/discovery/tools/act.py -> src/cua/discovery/tools/human.py -> src/cua/discovery/tools/observe.py -> src/cua/discovery/tools/guard.py -> src/cua/discovery/tools/__init__.py`
- 5-file cycle: `src/cua/discovery/tools/__init__.py -> src/cua/discovery/tools/nav.py -> src/cua/discovery/tools/guard.py -> src/cua/discovery/tools/human.py -> src/cua/discovery/tools/observe.py -> src/cua/discovery/tools/__init__.py`

## Communities (135 total, 14 thin omitted)

### Community 0 - "extension.py"
Cohesion: 0.10
Nodes (32): _in_control(), The take-over itself: badge YOU, unlock the site, wait for Done (panel or…, _takeover_note(), Answerable, button_clicked(), ext_call(), Extension, handback_button() (+24 more)

### Community 1 - "Ctx"
Cohesion: 0.06
Nodes (78): langchain_core_tools, act(), prepare(), canvas(), choose_option(), shown(), _count_start(), Ctx (+70 more)

### Community 2 - "make_replay_ctx"
Cohesion: 0.10
Nodes (35): FakeLock, make_replay_ctx(), shoot(), Replay test helpers: ``make_replay_ctx`` (a real Ctx on fakes), ``mk_look``,…, SiteLock stand-in: open() unlocks for the block., A real Ctx (real SendGuard, real ReplayRun) over a fake page/control/lock.…, ``take_look`` always returns this look., screen() (+27 more)

### Community 3 - "test_act.py"
Cohesion: 0.12
Nodes (45): make_look(), A look whose elements are numbered 1.. in order (ref, text, box)., observe(), Driven, _head(), _helped(), _logged_arg_keys(), asyncio (+37 more)

### Community 5 - "look.py"
Cohesion: 0.10
Nodes (24): cv2, numpy, numpy_typing, Canvas-pixel <-> page-point mapping: any window size or pixel density maps to…, to_page(), Box, Element, Look: the shapes every vision/discovery/replay function reads and…, parametrize, take_look's canvas: any window size or pixel density maps to one grid, and… (+16 more)

### Community 6 - "test_recorder_types.py"
Cohesion: 0.19
Nodes (18): _entry(), Typed inputs: the recorder infers each input's type from the shapes of the…, Older logs (and any tool that did not log shapes) never guess a type., Bug: a human typed fake digits ("1") into City during discovery and City became…, test_a_digit_only_human_entry_does_not_make_a_number_input(), test_a_goal_value_the_agent_types_still_makes_a_number_input(), test_a_human_entry_still_types_by_a_structural_shape(), test_a_plain_whole_number_is_a_number_so_decimals_pass_replay_later() (+10 more)

### Community 7 - "test_replay_inputs.py"
Cohesion: 0.10
Nodes (35): select(), type_(), _cap(), ClearPage, env(), FakeForm, FakePage, asyncio (+27 more)

### Community 8 - "test_input.py"
Cohesion: 0.07
Nodes (31): act(), into_box(), Lock, Page, Step, Unlock the site tab, run our own input steps, relock, settle, take a new look., Focus the site tab, click the box, clear what is in it, type. Retries replace…, FakeBox (+23 more)

### Community 9 - "load_classifier"
Cohesion: 0.22
Nodes (8): load_classifier(), BaseChatModel, Path, None when the ``rails`` extra is not installed., clf(), fixture, MonkeyPatch, test_load_classifier_returns_none_without_the_extra()

### Community 10 - "test_dropdown.py"
Cohesion: 0.07
Nodes (34): BaseException, shutil, list_options(), Page, The index (among the page's <select>s) of the native dropdown right under this…, Every option of the dropdown at this page point ([] if it is not a dropdown).…, select_under(), IndexPage (+26 more)

### Community 12 - "one_at_a_time"
Cohesion: 0.06
Nodes (66): Field, Cuts, Discovery decisions, Q10: window size and zoom — DECIDED, Q11: notebook format — DECIDED, Q12: dropdowns — DECIDED, Q13: scrolling — DECIDED, Q14: private data in saved pictures — DECIDED (+58 more)

### Community 16 - "test_build_tools.py"
Cohesion: 0.25
Nodes (9): AsyncFunctionDef, inspect, _notebook_tools(), _params(), build_tools(ctx): the notebook's 12 tools, in its TOOLS order, with its names,…, test_build_tools_returns_the_notebooks_tools_plus_extract_options_in_order(), test_each_docstring_is_the_notebooks(), test_each_signature_is_the_notebooks() (+1 more)

### Community 17 - "test_replay_evidence.py"
Cohesion: 0.14
Nodes (29): masked_outputs(), JsonValue, Names and shape only: a value is ***, a table keeps its rows and columns, every…, Path, write_cap(), _all_text(), fake_ocr(), _png() (+21 more)

### Community 18 - "Ctx"
Cohesion: 0.10
Nodes (53): Ctx, Page, cap(), click(), extract(), AskStop, clean(), ectx() (+45 more)

### Community 19 - "cli.py"
Cohesion: 0.06
Nodes (49): argparse, importlib_util, Namespace, NoReturn, _Broken, _cap_name(), check_eval(), _close() (+41 more)

### Community 20 - "test_replay_table.py"
Cohesion: 0.21
Nodes (21): _cap(), _defs(), Page, asyncio, MonkeyPatch, Path, do_extract_table: find the header by its label, read the rows with discovery's…, Each scroll shows the next look. (+13 more)

### Community 21 - "test_replay_handback.py"
Cohesion: 0.17
Nodes (20): _bctx(), Ext, Human, PanelDone, asyncio, parametrize, The toolbar hand-back button during a rescue (its service worker, never the…, The site page: any call made on it for the button is a bug. (+12 more)

### Community 22 - "test_config.py"
Cohesion: 0.07
Nodes (39): Task 2: Input rail orchestrator — `check_goal` (fail closed, modes, timeout), _actions(), _find_root(), load_site(), OutcomeRule, _outcomes(), Path, _rails() (+31 more)

### Community 23 - "test_recorder_runs.py"
Cohesion: 0.14
Nodes (23): _click(), _clicks(), _go(), _names(), _nav(), _noop_click(), _paths(), Recorder behaviour pinned by live runs: detours, 404s, login clicks kept, no-op… (+15 more)

### Community 24 - "checkpoint"
Cohesion: 0.10
Nodes (45): collections, checkpoint(), new(), rank(), _key(), _link_bar(), _on_page(), _pick() (+37 more)

### Community 25 - "recorder/__init__.py"
Cohesion: 0.06
Nodes (66): _check_login_order(), check_savable(), output(), Step, The {{input}} names the steps use, in order. {{secret:x}} is not an input., Every secret is typed before the first click (the login). Replay clicking Log…, Raise NotSaved before any model call when this run cannot become a capability., ``build_capability``'s refusals, unchanged: a leaked value, a blind dropdown,… (+58 more)

### Community 26 - "discovery/evidence.py"
Cohesion: 0.09
Nodes (40): Pattern, artifact_mask(), _copy_capability(), _events(), _folder(), OcrFn, Path, Redact (+32 more)

### Community 27 - "2. Each box, with an example"
Cohesion: 0.13
Nodes (14): 1. Diagram, 2. Each box, with an example, 3. All tools, 4. Step by step: one discovery run, Browser (Playwright), Control window and site lock (Q-A), Discovery architecture, DiscoveryAgent (LLM) (+6 more)

### Community 29 - "test_send_guard.py"
Cohesion: 0.11
Nodes (24): Side-specific steps, each at the exact point its notebook ran it. on_request:…, SendHooks, Control, _new(), on_request(), _play(), parametrize, SendGuard: nothing that sends data leaves the tab without two human approvals.… (+16 more)

### Community 30 - "test_session.py"
Cohesion: 0.16
Nodes (14): LivePage, _png(), asyncio, MonkeyPatch, Path, open_session reuses a live session (a notebook re-run must not leak a browser),…, The profile (cookies, cache, history of a bank session) was left in /tmp after…, _session() (+6 more)

### Community 31 - "test_read.py"
Cohesion: 0.10
Nodes (38): Items, _cell(), _extract_options(), _no_crop_pixels(), _options_ctx(), asyncio, fixture, MonkeyPatch (+30 more)

### Community 32 - "Brag Plan: Teller (v2), AI banking agent (repo: cua)"
Cohesion: 0.09
Nodes (21): Audio direction, Brag Plan: Teller (v2), AI banking agent (repo: cua), Duration: 22s, Format: landscape — 1920x1080, Hook (first 2-3 seconds), Key moments (the middle), Outro / punchline, Privacy / masking (+13 more)

### Community 33 - "test_act_without_a_send_does_not_wait"
Cohesion: 0.14
Nodes (14): _no_crop_pixels(), fixture, MonkeyPatch, MonkeyPatch, test_act_reads_dropdowns_first_and_waits_for_a_response_after_a_send(), changed(), dropdowns(), fake_look() (+6 more)

### Community 34 - "Replay decisions"
Cohesion: 0.11
Nodes (17): R10: where the compile step lives — DECIDED, R15: auto-approve at replay — PROPOSED, R16: dead ends and retries at compile — PROPOSED, R18: drift log — DECIDED, R19: hand-back button during a take-over — DECIDED (user), R1: no LLM at replay — DECIDED, R20: replay ends logged out — DECIDED (user), R22: account ids in replay evidence and the terminal — DECIDED (user, 2026-10-02) (+9 more)

### Community 35 - "redactor"
Cohesion: 0.06
Nodes (49): _black(), _glyphs(), _hidden_x(), mask_png(), NDArray, OcrFn, uint8, The box's ink column runs, left to right (x ranges): one per glyph when glyphs… (+41 more)

### Community 36 - "CLAUDE.md (project instructions)"
Cohesion: 0.13
Nodes (18): CLAUDE.md (project instructions), D101: labeled_value refuses a table-header resolution (general fix), D102: label_header/value_header flags ported into agent.py + cli.py capture path, D92: Evidence Capture Helpers (save_discovery_evidence/save_replay_evidence), D93: Pre-existing 02_artifact_schema.py IndexError bug, D95: Missing create_deep_agent import found live in BROWSER 12, D96: build_agent() goal_text vs given_text field-name bug, D97: cua replay --login flag + repeated Balance header trap (+10 more)

### Community 37 - "test_replay_steps.py"
Cohesion: 0.08
Nodes (41): mk_look(), navigate(), _click_env(), click(), gates_then_answer(), _form_png(), _judge(), Page (+33 more)

### Community 38 - "test_table.py"
Cohesion: 0.16
Nodes (16): AST, _defs(), _is_header(), Path, The shared OCR table reader: parity between cua.vision.table and both…, ast.dump compare, ignoring docstrings -- the functions this step did not have…, tests/replay/test_table_replay.py's own SHARED set is the contract this module…, _read() (+8 more)

### Community 39 - "manifest.json"
Cohesion: 0.11
Nodes (18): action, default_icon, default_title, background, service_worker, 128, 16, 32 (+10 more)

### Community 41 - "test_evidence.py"
Cohesion: 0.14
Nodes (31): _ai(), _artifact(), masked(), mask(), fixture, MonkeyPatch, parametrize, Path (+23 more)

### Community 42 - "control_window.py"
Cohesion: 0.17
Nodes (10): base64, html, discovery_control(), Protocol, ControlWindow: our own "Agent control" tab, the only place a human answers.…, The two Playwright pages this class touches: the control tab and the site tab., What differs between the discovery and replay control windows., Side (+2 more)

### Community 43 - "test_replay_wiring.py"
Cohesion: 0.08
Nodes (19): _fake_session(), asyncio, MonkeyPatch, Path, attach (the replay setup cell), the guard's replay hooks, and R7: after…, C1: one cuaReply forwarder and one close listener per control page, both…, I1: the once-per-page response listener reads the current ctx., _Resp (+11 more)

### Community 44 - "2. Components"
Cohesion: 0.14
Nodes (13): 1. Diagram, 2. Components, 4. Worked example: ParaBank login + read balance, 5. Notes, Actor, Artifact (made by discovery, not replay), Browser setup, Checker (+5 more)

### Community 45 - "types"
Cohesion: 0.18
Nodes (16): JsonObj, _flat(), _json(), Every value a request sends, from its query, a form body, or a JSON body…, The request's url and body with these values put back in, in the same format., rebuilt(), sent_fields(), parametrize (+8 more)

### Community 46 - "test_notebooks.py"
Cohesion: 0.22
Nodes (18): builtins, Call, jupytext, Module, _bind(), _code_cells(), _markdown(), _offline_namespace() (+10 more)

### Community 47 - "make_session"
Cohesion: 0.10
Nodes (27): DiscoveryConfig, Discovery-only settings., Discovery: an LLM agent learns a task once and the recorder saves it as a…, attach(), Route every request through a new send guard, open the control window. Re-run…, FakeTab, make_session(), A fake site or control tab with the Playwright calls discovery's wiring and… (+19 more)

### Community 48 - "check_output"
Cohesion: 0.11
Nodes (26): 6. Output rail, Global Constraints, NeMo Guardrails for Teller (discovery) Implementation Plan, Review Focus, Spec adjustment (flagged for review), Task 1: Output rail — `check_output` (pure Python), Task 3: NeMo adapter + Colang rails + the labelled goal set, Task 6: Docs and the live check (+18 more)

### Community 49 - "test_control_window.py"
Cohesion: 0.28
Nodes (22): Factory, SIDES, asyncio, parametrize, ControlWindow: one class, both sides' behaviour. Ported from…, Discovery calls _front inside try (the question is removed on failure); replay…, Regression: a gate during a take-over must win, then hand the take-over back…, _settle() (+14 more)

### Community 50 - "Productionize Plan: notebooks → `src/cua/` package"
Cohesion: 0.09
Nodes (16): 1. Package tree, 3. State: globals → explicit objects, 4. Async and typing, 5. Notebooks after the move, 7. ML-engineering practices (kept small), 8. Migration order (strictly sequential; one sub-agent per step; notebooks untouched until step 10), 9. Risks, Decisions (user, 2026-10-01) (+8 more)

### Community 51 - "test_middleware.py"
Cohesion: 0.12
Nodes (27): 3.5: keep the text the model wrote before its tool calls as ``ctx.run.why``…, RecordWhy, _answer(), _call(), asyncio, parametrize, SimpleNamespace, ToolMessage (+19 more)

### Community 52 - "test_takeover_loop.py"
Cohesion: 0.12
Nodes (27): replay_control(), Asker, hand_back(), Future, Lock, Protocol, The shared take-over loop pieces. Each side's own take-over stays with that…, Done on the toolbar button or in the take-over panel hands back. No reminders… (+19 more)

### Community 53 - "_FakeModel"
Cohesion: 0.14
Nodes (10): _FakeModel, asyncio, Stands in for a LangChain chat model: no network, records the prompt., asyncio, test_describe_names_the_options_outputs(), test_describe_names_the_table_outputs(), _Structured, test_describe_asks_the_given_model_with_labels_and_input_names_only() (+2 more)

### Community 54 - "FakePage"
Cohesion: 0.13
Nodes (8): FakeControl, FakePage, A fake discovery/replay ``CONTROL`` surface (what ``ControlWindow`` presents).…, A fake ``playwright.async_api.Page``. Every awaited method is recorded in…, asyncio, Tests for the shared offline fakes in tests/fakes.py (TDD: written before the…, TestFakeControl, TestFakePage

### Community 55 - "agent/build.py"
Cohesion: 0.13
Nodes (14): CompiledStateGraph, deepagents, langgraph_checkpoint_memory, langgraph_graph_state, build_agent(), BaseChatModel, build_agent: the notebook's ``AGENT = create_deep_agent(...)`` (discovery.py…, The discovery deep agent, with a checkpointer so a run can be resumed… (+6 more)

### Community 56 - "_where"
Cohesion: 0.25
Nodes (8): parametrize, A box's own text with nothing cut from it (a value, a button) stays off the…, test_a_box_border_read_as_a_bracket_is_not_part_of_the_label(), test_a_label_that_is_only_a_value_falls_back_to_the_next_nearest(), test_a_plain_word_under_the_point_is_still_never_the_anchor(), test_a_point_inside_a_merged_label_and_value_box_anchors_on_the_cleaned_label(), test_a_sent_value_joined_to_a_label_is_cut_from_it_and_from_the_input_name(), _where()

### Community 57 - "build_capability"
Cohesion: 0.07
Nodes (72): build_capability(), Collection, Steps, inputs and secrets come from the log only. The model's text cannot fail…, _ev(), _id_cap(), _logout(), _meta(), The recorder: the event log becomes a replay-ready capability (R12, R13, R16).… (+64 more)

### Community 58 - "steps.py"
Cohesion: 0.06
Nodes (67): Decisions made here (review), Open questions for the user, Replay notebook plan, Sections, Tasks, 3. Step types, Loader + pre-flight, Point (+59 more)

### Community 59 - "test_replay_rescue.py"
Cohesion: 0.04
Nodes (54): The guard keeps its own reference to the control window: swap both., set_control(), DoneWhileSending, _env(), _fail_clicks(), clicked(), FakePage, FormRoute (+46 more)

### Community 60 - "ReplayConfig"
Cohesion: 0.08
Nodes (53): difflib, math, SameTextLike, Replay-only settings., ReplayConfig, Replay: runs a capability saved by discovery with plain code, no LLM (step 4:…, anchor_point(), find_template() (+45 more)

### Community 61 - "save_artifact"
Cohesion: 0.11
Nodes (29): BaseChatModel, Collection, Save the run as a capability, or say plainly why not. Checked before the model…, _save(), cua.discovery.recorder, What may NOT go here, artifact_texts(), walk() (+21 more)

### Community 62 - "config.py"
Cohesion: 0.10
Nodes (22): collections_abc, dotenv, pathlib, Shared configuration: the site profile, browser/discovery/replay settings, and…, config_hash(), git_sha(), Path, Evidence helpers shared by discovery and replay: masking a JSON-able tree,… (+14 more)

### Community 63 - "replay/wiring.py"
Cohesion: 0.04
Nodes (52): dataclasses, enum, pydantic, Dropdown, The page's dropdowns, read BEFORE an action (never while guard_send holds a…, read_dropdowns(), bind_control(), ControlTab (+44 more)

### Community 64 - "routing.py"
Cohesion: 0.15
Nodes (17): ChatAnthropic, Data flow, langchain_anthropic, langchain_core_language_models, ModelKind, os, TypeSafe tool selection + model routing, restored (user, 2026-10-01;…, _build() (+9 more)

### Community 65 - "ReplayResult"
Cohesion: 0.19
Nodes (10): R17: replay result statuses — PROPOSED, `SUCCESS`, or e.g. `SUCCESS (human input at step 2; human intervened at step…, ReplayResult, test_summary_names_take_overs_and_option_choices_apart(), ReplayResult summary/outputs_line, Stop, and the Status values., test_partial_outputs_line_when_not_success(), test_result_defaults(), test_stop_carries_its_fields() (+2 more)

### Community 66 - "Hyperframes Composition Brief: cua"
Cohesion: 0.22
Nodes (8): Audio, Creative Direction, Hyperframes Composition Brief: cua, Hyperframes Instructions, Objective, Output, Storyboard, Visual Identity

### Community 67 - "LatestScreenshotOnly"
Cohesion: 0.27
Nodes (6): Handler, LatestScreenshotOnly, AsyncHandler, ModelRequest, ModelResponse, Old screenshots are stale (their numbers no longer work); send the model only…

### Community 68 - "Look"
Cohesion: 0.08
Nodes (57): crop(), Crop around the target, every other text blanked (sized to the current canvas)., Read order, Every shape the whole value matches, in precedence order. Safe to log: names,…, shapes_of(), select_option's body once the option is the agent's to pick: choose it, log its…, _selected(), _enter() (+49 more)

### Community 69 - "build_routing_middleware"
Cohesion: 0.15
Nodes (16): ModuleType, build_routing_middleware(), Classifier, ModelRouter, _models(), AgentMiddleware, BaseChatModel, Protocol (+8 more)

### Community 70 - "ControlWindow"
Cohesion: 0.16
Nodes (11): Question, ControlWindow, _img(), Answers the question on top. Closing the window (None) answers every one: fail…, Answers the newest open question of this mode, wherever it sits on the stack., A new question supersedes the one on screen (e.g. a gate during a take-over);…, One labelled input per field (label, masked), optionally prefilled. A dropdown…, After a question closes: the one below comes back, else the working page + site… (+3 more)

### Community 71 - "test_cli.py"
Cohesion: 0.14
Nodes (5): parametrize, cua.cli: argument parsing, --input parsing, and main() as the only asyncio.run…, test_a_bad_input_is_refused(), test_entry_exits_with_mains_code_after_flushing(), test_eval_refuses_a_run_count_below_one()

### Community 72 - "step_state"
Cohesion: 0.15
Nodes (14): page_name(), AsyncHandler, ModelRequest, ModelResponse, What the classifier sees for a step: the page name, the last tool's name and…, The URL's last path segment: no query, no ``;jsessionid=``, no trailing slash,…, The first word of the last tool result ('OK', 'REFUSED', 'Saved'), never its…, _status_word() (+6 more)

### Community 73 - "test_eval.py"
Cohesion: 0.14
Nodes (27): _cap(), _no_values(), _ok(), JsonValue, Path, cua.eval: summarize N replay results into a stability report. Pure, no browser., _row(), _table() (+19 more)

### Community 74 - "loader.py"
Cohesion: 0.13
Nodes (23): _ask(), ask_inputs(), _ask_rows(), row(), given_inputs(), input_type(), mistyped(), Loading a saved capability (schema v2) and the inputs it needs. Moved unchanged… (+15 more)

### Community 75 - "Capability"
Cohesion: 0.11
Nodes (43): Drift, action_allowed(), _cleanup_step(), error_page(), finish(), is_cleanup(), judge(), login_came_back() (+35 more)

### Community 76 - "ocr.py"
Cohesion: 0.07
Nodes (43): Source Material, 2. De-duplication (checked by AST diff of both notebooks), Q16: handoff UI and site lock — DECIDED, RapidOCR, rapidocr_utils_output, shoot(), NDArray, uint8 (+35 more)

### Community 77 - "test_routing.py"
Cohesion: 0.19
Nodes (18): _choice(), FakeClassifier, FakeRequest, _model(), _names(), handler(), asyncio, CaptureFixture (+10 more)

### Community 78 - "test_build.py"
Cohesion: 0.13
Nodes (18): GenericFakeChatModel, langchain_core_language_models_fake_chat_models, The discovery agent: system prompt, middleware, optional TypeSafe routing, and…, The discovery agent's system prompt, verbatim from…, _capture(), _fake_model(), asyncio, MonkeyPatch (+10 more)

### Community 79 - "SiteProfile"
Cohesion: 0.08
Nodes (28): Task 4: REFUSED evidence, Components, json, fix(), main(), Path, Re-mask stored evidence/artifact text in place (session tokens, raw account…, remask() (+20 more)

### Community 80 - "Teller guardrails: how they decide"
Cohesion: 0.13
Nodes (15): 10. How to try it, 1. What the guardrails are, 3.1 `off_topic`, 3.2 `jailbreak`, 3.3 `steering`, 3.4 `sensitive`, 3.5 `empty_goal`, 3.6 `guardrails_unavailable` (+7 more)

### Community 81 - "discovery/wiring.py"
Cohesion: 0.07
Nodes (42): Saved, The current run (the one the send guard serves)., run_goal: one goal through the discovery agent (moved from discovery.py…, The deadline passed: end the run STUCK, keeping what the agent did so far., _start(), _timed_out(), DiscoveryRun, DiscoveryRun: one discovery run's working state (was the notebook's… (+34 more)

### Community 82 - "test_prompt.py"
Cohesion: 0.10
Nodes (8): hashlib, The prompts are the first filter (user, 2026-09-30); the models and code checks…, test_the_prompt_lists_every_tool(), Frozen notebook sources for the parity tests (step 10 replaced the notebooks…, parametrize, Path, The frozen notebook snapshots the parity tests read must never drift (see…, test_snapshot_is_unchanged()

### Community 84 - "vision/__init__.py"
Cohesion: 0.08
Nodes (48): Cols, Q8b: reading a whole table — DECIDED (2026-09-30), R21: table reads — DECIDED (2026-09-30), _columns(), is_header(), is_word(), off_table(), (value, pattern) for an extract: the whole box when it is exactly the type,… (+40 more)

### Community 85 - "SendGuard"
Cohesion: 0.27
Nodes (6): 10. Line-count offenders (today), pretty(), address.zipCode' -> 'Address zip code' (for the human; the key itself is kept)., ``await guard(route)`` is the route handler. ``guard.lock`` is the send gate:…, Gate 1: Approve, or Edit = back to the form with every value, then again.…, SendGuard

### Community 86 - "test_saved_artifacts.py"
Cohesion: 0.21
Nodes (12): MonkeyPatch, parametrize, Path, Every capability saved in the top-level artifacts/ folder (Decision 6) loads in…, The latest discovery run that saved this capability with exactly these steps., Regression: inputs typed "number" from a human's placeholder digits ("1" in…, A plain-text value passes replay's type check for every input the site would…, _source_run() (+4 more)

### Community 87 - "rails.py"
Cohesion: 0.19
Nodes (15): logging, _cards(), mask(), check_goal(), Classifier, _classify_all(), _luhn(), Protocol (+7 more)

### Community 88 - "pytest"
Cohesion: 0.16
Nodes (13): pytest, _fake_llm_keys(), fixture, MonkeyPatch, Suite-wide: never let a real LLM key from `.env` reach a test (cua.config loads…, A fake Anthropic key so code that builds a chat model works offline., parametrize, Path (+5 more)

### Community 90 - "BrowserConfig"
Cohesion: 0.07
Nodes (45): asyncio, BrowserContext, Confirm, contextlib, LookFn, Playwright, playwright_async_api, choose_option_at_index() (+37 more)

### Community 91 - "Read order"
Cohesion: 0.15
Nodes (13): EvalReport, _hist_line(), JsonValue, Path, A short plain-text table for the terminal. Step numbers are 1-based, like the…, Per run: status and reason, the reason masked with that run's own values +…, ``<out_dir>/<UTC stamp>-<name>/report.json`` + ``run.json``. Never an output…, render() (+5 more)

### Community 92 - "test_goal.py"
Cohesion: 0.16
Nodes (18): New run on a fresh thread; pass an earlier thread_id to resume it with a next…, run_goal(), FakeAgent, HangingAgent, asyncio, Path, run_goal: a fresh run per goal (or a resumed thread), the start event, the…, _state_with() (+10 more)

### Community 93 - "_patch_session"
Cohesion: 0.18
Nodes (9): Task 5: Wire the rails into `cua discover`, _Clf, _Exited, _patch_session(), Exception, Stands in for ``os._exit`` so the test process survives., test_a_broken_rails_config_refuses(), test_a_refused_goal_never_opens_the_browser_and_exits_1() (+1 more)

### Community 94 - "test_dropdowns.py"
Cohesion: 0.11
Nodes (20): 6. Tests, FakeRoute, The handful of ``playwright.async_api.Request`` fields the project's code reads., A fake ``playwright.async_api.Route``: records every…, _Request, _approve(), HeldPage, _logged() (+12 more)

### Community 95 - "Read order"
Cohesion: 0.20
Nodes (8): cua.safety, Read order, Rules, What may NOT go here, ControlLike, GuardOptions, The two notebooks' differences, by name. human_in_lock: discovery reads…, The two ControlWindow calls the gates use.

### Community 96 - "confidence_gate"
Cohesion: 0.47
Nodes (6): Restore: TypeSafe tool selection + model routing (user, 2026-10-01), confidence_gate(), job_tool_names(), Tools this job needs, plus the always-allowed set. Pure: no network, no LLM., Narrow base_tools to this job's tools, but only if the classifier is confident.…, test_job_tool_names_and_gate()

### Community 97 - "test_capability.py"
Cohesion: 0.23
Nodes (9): _data(), parametrize, Path, cua.schema.Capability loads every saved artifact and refuses an unknown schema…, test_a_target_needs_a_findable_rung(), test_a_wrong_schema_version_is_refused(), test_an_unknown_key_is_refused(), test_every_saved_artifact_loads() (+1 more)

### Community 98 - "test_human.py"
Cohesion: 0.08
Nodes (53): goal_value(), The value the goal already gives for this field, or None. Code backstop for the…, Q21: the one time the site unlocks for a human. What they did is kept as…, take_over(), cua.handoff, How it fits, What may NOT go here, _answer() (+45 more)

### Community 100 - "test_rails_input.py"
Cohesion: 0.22
Nodes (14): Fake, Exception, parametrize, Input rail orchestrator: per-sentence + whole-goal check, fail closed,…, run(), test_a_classifier_error_fails_closed(), test_a_hanging_classifier_times_out_closed(), test_a_refused_intent_refuses_with_its_message() (+6 more)

### Community 101 - "test_import_rules.py"
Cohesion: 0.29
Nodes (13): _cua_imports(), _layer_files(), _module(), parametrize, Path, The package's import rule (docs/PRODUCTIONIZE_PLAN.md section 1), read from…, The top-level cua subpackage of every ``cua.*`` import (``import`` or ``from``)., Guard the guard: a planted forbidden import is caught in both spellings. (+5 more)

### Community 102 - "MonkeyPatch"
Cohesion: 0.25
Nodes (8): MonkeyPatch, _record_run(), test_a_bad_input_exits_before_any_browser(), test_entry_lets_an_exception_in_main_propagate(), test_main_runs_discover_through_asyncio_run(), test_main_runs_replay_through_asyncio_run(), test_safe_output_withholds_when_the_rail_errors(), boom()

### Community 103 - "test_discover_wires_like_the_notebook"
Cohesion: 0.22
Nodes (8): CaptureFixture, Live: a take-over run crashed with a traceback after a wasted describe() call., test_a_leak_found_while_masking_is_not_saved_and_says_so(), refuse(), test_a_run_that_cannot_be_saved_prints_why_and_never_asks_the_model(), test_discover_wires_like_the_notebook(), describe(), test_the_terminal_shows_ids_by_their_last_digits_and_amounts_as_is()

### Community 104 - "test_human_tools.py"
Cohesion: 0.18
Nodes (16): ActTab, SimpleNamespace, A site tab the act/nav tools drive: ``mouse``/``keyboard`` record into…, A page script: recorded, answered by ``answer`` (default: no dropdown anywhere)., _ctx(), asyncio, MonkeyPatch, finish_business_outcome / request_missing_values / ask_human (the human-facing… (+8 more)

### Community 105 - "Request"
Cohesion: 0.20
Nodes (4): Protocol, The fields of a ``playwright.async_api.Request`` the guard reads., Request, RouteLike

### Community 106 - "schema/__init__.py"
Cohesion: 0.12
Nodes (38): BaseModel, model_validator, Base decisions, The 3 rungs (how replay finds things), R13: target schema — PROPOSED, re, _navigate(), Event log -> ``Capability``: steps, inputs, outputs and secrets come from the… (+30 more)

### Community 107 - "test_eval_replays_n_times_in_one_session"
Cohesion: 0.18
Nodes (9): _result(), attach(), test_eval_replays_n_times_in_one_session(), run_eval(), run_replay(), test_replay_wires_like_the_notebook(), replay(), test_replay_without_evidence_saves_none() (+1 more)

### Community 108 - "Box"
Cohesion: 0.07
Nodes (50): canvas_size(), The size of the image the model is looking at right now., crop_box(), cut_crop(), _ink(), input_box(), Crops around one point: find the element there, crop around it, read text near…, New ink appeared INSIDE the input box (text, or a password's dots). A click… (+42 more)

### Community 109 - "NeMo Guardrails for Teller (discovery) — design"
Cohesion: 0.25
Nodes (7): Docs, Failure handling, Goal, NeMo Guardrails for Teller (discovery) — design, Open questions, Scope, Testing (offline, test-first)

### Community 110 - "make_ctx"
Cohesion: 0.10
Nodes (35): make_ctx(), A discovery ``Ctx`` over fakes, built like ``attach`` but with no page wiring., helped(), _only(), asyncio, fixture, MonkeyPatch, Tool guards: the event log, the step budget, repeats, login tries, click gates,… (+27 more)

### Community 111 - "cua.browser"
Cohesion: 0.40
Nodes (4): cua.browser, How it fits, What may NOT go here, confirm()

### Community 114 - "OnlyOurTools"
Cohesion: 0.24
Nodes (7): AsyncToolHandler, OnlyOurTools, ToolMessage, ``create_deep_agent`` always adds deepagents' file tools (``ls``,…, ToolCallRequest, ToolHandler, ToolResult

### Community 115 - "Agent architecture (discovery)"
Cohesion: 0.25
Nodes (6): 1. The whole run, in order, 2. What is used where, 3. The guardrail layers, 4. Replay (no LLM), Agent architecture (discovery), README.md (setup + demo path)

### Community 116 - ".classify"
Cohesion: 0.29
Nodes (3): 2. How the input rail decides, Build the embedding index now (a first run downloads the model), so…, Best similarity per intent for ``text`` (NeMo's own formula).

### Community 117 - "Path"
Cohesion: 0.29
Nodes (8): _cap_file(), Path, test_eval_stops_on_a_missing_input_before_any_run(), test_eval_warns_when_the_capability_sends_data(), test_main_runs_eval_through_asyncio_run(), run_eval(), test_several_profiles_need_an_explicit_site(), test_the_classifier_is_warmed_up_before_the_goal_check()

### Community 118 - "load_capability"
Cohesion: 0.13
Nodes (29): load_capability(), load_outcomes(), _missing_crops(), Path, The capability and the folder its crop paths are relative to., The capability's own `outcomes:` [{text, status, meaning}], else the site's…, Path, Discovery's saved artifact runs in replay unchanged: build -> save -> load ->… (+21 more)

### Community 119 - "GotoPage"
Cohesion: 0.33
Nodes (3): GotoPage, Resp, test_only_the_main_documents_status_is_kept()

### Community 120 - "_rails_site"
Cohesion: 0.18
Nodes (9): R11: why compile, if `response_format` exists? — PROPOSED, For a name or a path (``[a-z0-9_]`` only): the last digits, no stars., _never(), _rails_site(), test_a_failed_warmup_fails_closed(), test_only_main_calls_asyncio_run(), test_rails_off_never_builds_the_classifier_or_haiku(), test_rails_on_without_the_extra_prints_off_and_never_builds_haiku() (+1 more)

### Community 124 - "test_llm.py"
Cohesion: 0.19
Nodes (12): _clean_env(), fixture, MonkeyPatch, Offline tests for `cua.llm.make_chat_model`. No network, no real key. Direct…, test_a_base_url_in_the_env_never_redirects(), test_ca_bundle_passthrough(), test_direct_anthropic(), test_existing_ssl_cert_file_wins() (+4 more)

### Community 125 - "test_rails_nemo.py"
Cohesion: 0.16
Nodes (26): NemoClassifier, One NeMo ``LLMRails`` over ``configs/rails/``, used for its user-message index., Labelled goals for the NeMo input rails: (goal, expected rail or None for…, label_for(), parametrize, Path, SimpleNamespace, The real NeMo config (local embeddings) on the labelled goals. Needs the… (+18 more)

### Community 127 - "test_evidence_clean.py"
Cohesion: 0.32
Nodes (10): parametrize, Path, Brief 3.4: no session token and no raw account id is ever stored. Scans every…, Every string in a JSON value, keys included (numbers are counts and pixels,…, _rel(), _strings(), test_stored_text_never_holds_a_raw_account_id(), test_stored_text_never_holds_a_session_token() (+2 more)

### Community 128 - "eval.py"
Cohesion: 0.17
Nodes (19): Histogram, _cells(), _describe(), fallback_steps(), _histograms(), _is_fallback(), _no_ocr_steps(), _output_diffs() (+11 more)

### Community 129 - "_fake_session"
Cohesion: 0.33
Nodes (5): _fake_session(), stop(), SimpleNamespace, _Session, SITE_NS()

### Community 130 - "build_tools"
Cohesion: 0.11
Nodes (20): Contracts for the tools / agent (steps 8b, 8c), cua.discovery, What may NOT go here, _checked(), mark_stuck(), note_call(), decorate(), wrapper() (+12 more)

### Community 132 - "test_site_lock.py"
Cohesion: 0.31
Nodes (7): FakeCdp, asyncio, SiteLock: the site tab ignores real input except inside ``open()``, which…, test_an_exception_inside_open_still_relocks(), test_open_unlocks_then_relocks(), test_set_sends_the_cdp_ignore_input_command(), fake()

### Community 133 - "load"
Cohesion: 0.15
Nodes (20): functools, dropdown_options(), mismatches(), _norm_num(), Dropdown, Values a send carries that the human never gave, and the dropdown choices to…, Numbers being sent that the human never gave, e.g. account 1450 vs 1400. Only…, For each key: the options of the page dropdown whose CURRENT value is exactly… (+12 more)

### Community 135 - "middleware.py"
Cohesion: 0.20
Nodes (9): AIMessage, langchain_agents_middleware, langchain_core_messages, langgraph_prebuilt_tool_node, langgraph_types, _arg_values(), _has_image(), The notebook's two agent middlewares, moved unchanged from discovery.py… (+1 more)

### Community 139 - "Pure-Visual Discovery Notebook: Build Plan"
Cohesion: 0.09
Nodes (18): 10. Open risks, 2. Review focus (inputs no spec line covers, but likely to bite), 4. New dependencies (checked on PyPI, 2026-09-28), 5. Files, 6. Test target: ParaBank only (Q-C, DECIDED), 7. Offline fixtures and what each proves, 8. Cell-by-cell plan (`discovery.py`), 9. Decisions (all answered by the user, 2026-09-28) (+10 more)

### Community 144 - "cua/__init__.py"
Cohesion: 0.33
Nodes (3): cua: shared config and the LLM model factory (direct Anthropic) for the pure-…, host_allowed: only the site's own hosts (D15); about:blank always., test_only_allowed_hosts_and_blank()

### Community 145 - "Agent"
Cohesion: 0.40
Nodes (3): Agent, Protocol, What run_goal needs of the compiled deep agent.

## Knowledge Gaps
- **123 isolated node(s):** `MODES`, `manifest_version`, `name`, `version`, `description` (+118 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 1273 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **14 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Ctx` connect `Ctx` to `make_replay_ctx`, `test_replay_inputs.py`, `test_replay_evidence.py`, `cli.py`, `test_replay_table.py`, `test_replay_handback.py`, `discovery/evidence.py`, `test_send_guard.py`, `test_replay_steps.py`, `test_replay_wiring.py`, `steps.py`, `test_replay_rescue.py`, `ReplayConfig`, `replay/wiring.py`, `ControlWindow`, `loader.py`, `Capability`, `SiteProfile`, `SendGuard`, `BrowserConfig`, `Request`?**
  _High betweenness centrality (0.063) - this node is a cross-community bridge._
- **Why does `Look` connect `Look` to `Ctx`, `make_replay_ctx`, `test_act.py`, `look.py`, `test_input.py`, `test_dropdown.py`, `one_at_a_time`, `test_act_without_a_send_does_not_wait`, `test_replay_steps.py`, `steps.py`, `test_replay_rescue.py`, `ReplayConfig`, `ocr.py`, `discovery/wiring.py`, `vision/__init__.py`, `BrowserConfig`, `test_human.py`, `Box`, `make_ctx`?**
  _High betweenness centrality (0.040) - this node is a cross-community bridge._
- **Why does `Ctx` connect `Ctx` to `extension.py`, `build_tools`, `test_act.py`, `middleware.py`, `one_at_a_time`, `discovery/evidence.py`, `test_read.py`, `make_session`, `test_middleware.py`, `agent/build.py`, `Look`, `SiteProfile`, `discovery/wiring.py`, `vision/__init__.py`, `BrowserConfig`, `test_goal.py`, `test_dropdowns.py`, `test_human.py`, `test_human_tools.py`, `make_ctx`, `OnlyOurTools`?**
  _High betweenness centrality (0.035) - this node is a cross-community bridge._
- **Are the 142 inferred relationships involving `Ctx` (e.g. with `Session` and `BrowserConfig`) actually correct?**
  _`Ctx` has 142 INFERRED edges - model-reasoned connections that need verification._
- **Are the 93 inferred relationships involving `Ctx` (e.g. with `build_agent()` and `RecordWhy`) actually correct?**
  _`Ctx` has 93 INFERRED edges - model-reasoned connections that need verification._
- **Are the 84 inferred relationships involving `Look` (e.g. with `act()` and `into_box()`) actually correct?**
  _`Look` has 84 INFERRED edges - model-reasoned connections that need verification._
- **Are the 4 inferred relationships involving `make_ctx()` (e.g. with `6. Tests` and `Session`) actually correct?**
  _`make_ctx()` has 4 INFERRED edges - model-reasoned connections that need verification._