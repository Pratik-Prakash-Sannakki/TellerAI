# Graph Report - BankerAgent  (2026-10-01)

## Corpus Check
- 176 files · ~133,855 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 2699 nodes · 7740 edges · 111 communities (99 shown, 12 thin omitted)
- Extraction: 93% EXTRACTED · 7% INFERRED · 0% AMBIGUOUS · INFERRED: 522 edges (avg confidence: 0.63)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `88e038c1`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- cli.py
- fakes.py
- Productionize Plan: notebooks → `src/cua/` package
- test_act.py
- Evidence README
- rescue.py
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
- pytest
- test_replay_wiring.py
- recorder/__init__.py
- steps.py
- crops_for
- integration/conftest.py
- test_replay_evidence.py
- test_replay_table.py
- redact.py
- ._held
- build_capability
- test_replay_extract.py
- safety/__init__.py
- CLAUDE.md (project instructions)
- make_replay_ctx
- RefCounter
- manifest.json
- langchain_tools
- choose_option_at_point
- redactor
- replay/context.py
- ReplayResult
- human.py
- FakeTab
- locate
- test_send_guard.py
- test_control_window.py
- cua.vision
- test_takeover_loop.py
- test_extension.py
- Session
- read_helpers.py
- Capability
- read.py
- BrowserConfig
- langgraph_types
- guard.py
- Discovery decisions
- 2. Each box, with an example
- test_capability.py
- ControlWindow
- 2. Components
- replay/evidence.py
- Pure-Visual Discovery Notebook: Build Plan
- ReplayConfig
- SiteLock
- test_recorder_reads.py
- ocr.py
- config.py
- engine.py
- json
- test_routing.py
- FakeWin
- masked
- Look
- test_session.py
- test_prompt.py
- copy
- seen_outcome
- build_tools
- cua
- cua/__init__.py
- cua.schema
- locate.py
- types
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
- cua/evidence.py
- discovery/evidence.py
- background.js
- replay/wiring.py
- bind_control
- cua.discovery.agent

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
- `test_typed_ok_words_tolerant_digits_exact()` --calls--> `typed_ok()`  [INFERRED]
  tests/unit/replay/test_locate.py → src/cua/replay/locate.py
- `test_a_target_needs_a_findable_rung()` --calls--> `Target`  [INFERRED]
  tests/unit/schema/test_capability.py → src/cua/schema/capability.py
- `test_an_old_select_without_an_index_still_loads()` --calls--> `Select`  [INFERRED]
  tests/unit/discovery/recorder/test_recorder_reads.py → src/cua/schema/capability.py
- `test_meta_is_loose()` --calls--> `CapabilityMeta`  [INFERRED]
  tests/unit/schema/test_capability.py → src/cua/schema/capability.py
- `test_stop_carries_its_fields()` --calls--> `Stop`  [INFERRED]
  tests/unit/schema/test_result.py → src/cua/schema/result.py

## Import Cycles
- 3-file cycle: `src/cua/discovery/tools/__init__.py -> src/cua/discovery/tools/act.py -> src/cua/discovery/tools/guard.py -> src/cua/discovery/tools/__init__.py`
- 3-file cycle: `src/cua/discovery/tools/__init__.py -> src/cua/discovery/tools/nav.py -> src/cua/discovery/tools/guard.py -> src/cua/discovery/tools/__init__.py`
- 3-file cycle: `src/cua/discovery/tools/__init__.py -> src/cua/discovery/tools/read.py -> src/cua/discovery/tools/guard.py -> src/cua/discovery/tools/__init__.py`
- 3-file cycle: `src/cua/discovery/tools/guard.py -> src/cua/discovery/tools/human.py -> src/cua/discovery/tools/observe.py -> src/cua/discovery/tools/guard.py`
- 3-file cycle: `src/cua/discovery/tools/__init__.py -> src/cua/discovery/tools/act.py -> src/cua/discovery/tools/observe.py -> src/cua/discovery/tools/__init__.py`
- 3-file cycle: `src/cua/discovery/tools/__init__.py -> src/cua/discovery/tools/human.py -> src/cua/discovery/tools/observe.py -> src/cua/discovery/tools/__init__.py`
- 3-file cycle: `src/cua/discovery/tools/__init__.py -> src/cua/discovery/tools/nav.py -> src/cua/discovery/tools/observe.py -> src/cua/discovery/tools/__init__.py`
- 4-file cycle: `src/cua/discovery/tools/__init__.py -> src/cua/discovery/tools/human.py -> src/cua/discovery/tools/observe.py -> src/cua/discovery/tools/guard.py -> src/cua/discovery/tools/__init__.py`
- 4-file cycle: `src/cua/discovery/tools/__init__.py -> src/cua/discovery/tools/act.py -> src/cua/discovery/tools/observe.py -> src/cua/discovery/tools/guard.py -> src/cua/discovery/tools/__init__.py`
- 4-file cycle: `src/cua/discovery/tools/__init__.py -> src/cua/discovery/tools/nav.py -> src/cua/discovery/tools/observe.py -> src/cua/discovery/tools/guard.py -> src/cua/discovery/tools/__init__.py`
- 4-file cycle: `src/cua/discovery/tools/__init__.py -> src/cua/discovery/tools/act.py -> src/cua/discovery/tools/human.py -> src/cua/discovery/tools/observe.py -> src/cua/discovery/tools/__init__.py`
- 5-file cycle: `src/cua/discovery/tools/__init__.py -> src/cua/discovery/tools/act.py -> src/cua/discovery/tools/human.py -> src/cua/discovery/tools/observe.py -> src/cua/discovery/tools/guard.py -> src/cua/discovery/tools/__init__.py`
- 5-file cycle: `src/cua/discovery/tools/__init__.py -> src/cua/discovery/tools/act.py -> src/cua/discovery/tools/guard.py -> src/cua/discovery/tools/human.py -> src/cua/discovery/tools/observe.py -> src/cua/discovery/tools/__init__.py`
- 5-file cycle: `src/cua/discovery/tools/__init__.py -> src/cua/discovery/tools/nav.py -> src/cua/discovery/tools/guard.py -> src/cua/discovery/tools/human.py -> src/cua/discovery/tools/observe.py -> src/cua/discovery/tools/__init__.py`
- 5-file cycle: `src/cua/discovery/tools/__init__.py -> src/cua/discovery/tools/read.py -> src/cua/discovery/tools/guard.py -> src/cua/discovery/tools/human.py -> src/cua/discovery/tools/observe.py -> src/cua/discovery/tools/__init__.py`

## Communities (111 total, 12 thin omitted)

### Community 0 - "cli.py"
Cohesion: 0.18
Nodes (18): argparse, Namespace, _close(), default_site(), discover(), main(), parse_args(), parse_inputs() (+10 more)

### Community 1 - "fakes.py"
Cohesion: 0.07
Nodes (18): blank_png(), FakeControl, FakeInput, FakeLock, FakePage, FakeRoute, Shared offline fakes for the ported test suite (tests/unit, tests/integration).…, A fake discovery/replay ``CONTROL`` surface (what ``ControlWindow`` presents).… (+10 more)

### Community 2 - "Productionize Plan: notebooks → `src/cua/` package"
Cohesion: 0.12
Nodes (16): 10. Line-count offenders (today), 1. Package tree, 2. De-duplication (checked by AST diff of both notebooks), 3. State: globals → explicit objects, 4. Async and typing, 5. Notebooks after the move, 6. Tests, 7. ML-engineering practices (kept small) (+8 more)

### Community 3 - "test_act.py"
Cohesion: 0.07
Nodes (77): Items, (value, pattern) for an extract: the whole box when it is exactly the type,…, value_in_box(), make_look(), A look whose elements are numbered 1.. in order (ref, text, box)., Driven, _head(), _helped() (+69 more)

### Community 5 - "rescue.py"
Cohesion: 0.13
Nodes (16): _in_control(), The take-over itself: badge YOU, unlock the site, wait for Done (panel or…, _takeover_note(), Lock, A send the human started is still held: its gate is on screen next; wait for…, wait_held_send(), Frame, Ctx (+8 more)

### Community 6 - "test_recorder_types.py"
Cohesion: 0.12
Nodes (23): event_shapes(), input_types(), pick_type(), Typed inputs: an input's type is inferred from the SHAPES of the values typed…, One input's type from each of its values' shapes. Unknown shapes (None) ->…, input name -> the shapes of the value it took in this event (None: not logged)., input name -> its inferred type, from the events that became steps., Which hosts the browser may reach (D15). The allowlist itself lives in the site… (+15 more)

### Community 7 - "test_replay_inputs.py"
Cohesion: 0.12
Nodes (33): select(), _cap(), ClearPage, env(), FakeForm, FakePage, asyncio, Ctx (+25 more)

### Community 8 - "test_input.py"
Cohesion: 0.12
Nodes (22): act(), into_box(), Lock, Page, Session, Step, Unlock the site tab, run our own input steps, relock, settle, take a new look., Click the box, clear what is in it, type. Retries replace instead of doubling… (+14 more)

### Community 9 - "test_middleware.py"
Cohesion: 0.08
Nodes (41): AIMessage, CompiledStateGraph, deepagents, Handler, build_agent(), BaseChatModel, Ctx, build_agent: the notebook's ``AGENT = create_deep_agent(...)`` (discovery.py… (+33 more)

### Community 10 - "test_dropdown.py"
Cohesion: 0.08
Nodes (33): BaseException, list_options(), Dropdown, Page, Every option of the dropdown at this page point ([] if it is not a dropdown).…, The page's dropdowns, read BEFORE an action (never while guard_send holds a…, read_dropdowns(), IndexPage (+25 more)

### Community 12 - "Replay decisions"
Cohesion: 0.08
Nodes (23): R10: where the compile step lives — DECIDED, R11: why compile, if `response_format` exists? — PROPOSED, R12: what each step type compiles to — PROPOSED, R13: target schema — PROPOSED, R14: what rung 2 needs that discovery doesn't record — DONE, R15: auto-approve at replay — PROPOSED, R16: dead ends and retries at compile — PROPOSED, R17: replay result statuses — PROPOSED (+15 more)

### Community 16 - "discovery/context.py"
Cohesion: 0.06
Nodes (45): dataclasses, re, Saved, The notebook's two agent middlewares, moved unchanged from discovery.py…, _count_start(), Ctx: what every discovery tool is given, plus the page wrappers the tools…, The current run (the one the send guard serves)., The start event's look bookkeeping: the page a run begins on, and how often… (+37 more)

### Community 17 - "test_cli.py"
Cohesion: 0.14
Nodes (20): _fake_session(), _patch_session(), MonkeyPatch, parametrize, Path, SimpleNamespace, cua.cli: argument parsing, --input parsing, and main() as the only asyncio.run…, _record_run() (+12 more)

### Community 18 - "test_replay_engine.py"
Cohesion: 0.16
Nodes (51): cap(), click(), extract(), Path, type_(), write_cap(), AskStop, clean() (+43 more)

### Community 19 - "test_replay_rescue.py"
Cohesion: 0.06
Nodes (44): The guard keeps its own reference to the control window: swap both., set_control(), DoneWhileSending, _env(), _fail_clicks(), FormRoute, Frame, GateControl (+36 more)

### Community 20 - "test_llm.py"
Cohesion: 0.20
Nodes (14): _clean_env(), _gateway(), fixture, MonkeyPatch, Offline tests for `cua.llm.make_chat_model`. No network, no real key. Default:…, test_ca_bundle_passthrough(), test_existing_ssl_cert_file_wins(), test_gateway_env_means_gateway() (+6 more)

### Community 21 - "test_replay_handback.py"
Cohesion: 0.14
Nodes (22): FakePage, _bctx(), Ext, Human, PanelDone, asyncio, Ctx, parametrize (+14 more)

### Community 22 - "SiteProfile"
Cohesion: 0.09
Nodes (26): Look up a secret by NAME. Raises on an unknown name or an empty/missing value.…, Secret name -> value from `.env` ("" when unset), as the notebook's SECRETS., Everything site-specific, loaded from ``configs/<name>.yaml``. Secrets: env…, Secret name -> env var name., resolve_secret(), secret_values(), SiteProfile, True if `name` is a known secret with a non-empty value in `.env` (D32: never… (+18 more)

### Community 23 - "pytest"
Cohesion: 0.05
Nodes (61): AST, Call, Module, pytest, _fake_llm_keys(), fixture, MonkeyPatch, Suite-wide: never let a real LLM key from `.env` reach a test (cua.config loads… (+53 more)

### Community 24 - "test_replay_wiring.py"
Cohesion: 0.11
Nodes (17): attach(), Session, Wire replay onto an open session and return its Ctx., _fake_session(), asyncio, attach (the replay setup cell), the guard's replay hooks, and R7: after…, C1: one cuaReply forwarder and one close listener per control page, both…, I1: the once-per-page response listener reads the current ctx. (+9 more)

### Community 25 - "recorder/__init__.py"
Cohesion: 0.08
Nodes (49): output(), Step, The {{input}} names the steps use, in order. {{secret:x}} is not an input., ``build_capability``'s refusals, unchanged: a leaked value, a blind dropdown,…, _refuse(), step_inputs(), used_inputs(), checkpoint() (+41 more)

### Community 26 - "steps.py"
Cohesion: 0.09
Nodes (49): Point, changed(), choose_option(), do_click(), do_extract(), do_extract_table(), do_navigate(), do_scroll() (+41 more)

### Community 27 - "crops_for"
Cohesion: 0.18
Nodes (15): crops_for(), Path, save_artifact(), fixture, MonkeyPatch, saved(), Path, User decision 6: artifacts/<name>.yaml + artifacts/crops/<name>/ (was… (+7 more)

### Community 29 - "test_replay_evidence.py"
Cohesion: 0.30
Nodes (17): _all_text(), fake_ocr(), _png(), Ctx, fixture, Path, save_evidence writes one masked folder per run: summary, drift, failure (only…, A capability on disk, a fake OCR that reads the value, and the last run's mask… (+9 more)

### Community 30 - "test_replay_table.py"
Cohesion: 0.23
Nodes (17): _cap(), _defs(), Page, asyncio, Ctx, MonkeyPatch, Path, do_extract_table: find the header by its label, read the rows with discovery's… (+9 more)

### Community 31 - "redact.py"
Cohesion: 0.13
Nodes (26): hide_secrets(), mask_png(), _num(), OcrFn, Value masking: ``norm``, ``is_sensitive``, ``hide_secrets``, ``redactor``,…, Each secret value -> ``<name>``. ``secrets`` maps a secret NAME to its value., Black out every OCR box whose text holds a run value. A clean image is written…, decode() (+18 more)

### Community 32 - "._held"
Cohesion: 0.09
Nodes (12): ControlLike, LookLike, Protocol, Request, Gate 1: Approve, or Edit = back to the form with every value, then again.…, What the guard reads and writes on a run (DiscoveryRun / ReplayRun satisfy it)., The two ControlWindow calls the gates use., RouteLike (+4 more)

### Community 33 - "build_capability"
Cohesion: 0.08
Nodes (67): build_capability(), Steps, inputs and secrets come from the log only. The model's text cannot fail…, _ev(), _meta(), The recorder: the event log becomes a replay-ready capability (R12, R13, R16).…, Invented inputs are ignored, a missing description gets a default, secrets stay…, Banking safety (user, 2026-09-29): replay ends logged out., Live: steps 5-6 (agent, 'From account #[') and 7-8 (send, 'From account #')… (+59 more)

### Community 34 - "test_replay_extract.py"
Cohesion: 0.19
Nodes (21): _extract(), _notebook_assign(), _pcap(), asyncio, Ctx, parametrize, Path, Extract steps on fakes: strict value types and an optional `pattern`. Ported… (+13 more)

### Community 35 - "safety/__init__.py"
Cohesion: 0.11
Nodes (26): JsonObj, Safety: what may leave the tab (hosts, the two send gates) and keeping values…, _flat(), _json(), pretty(), Protocol, What a held request sends, and the same request rebuilt with edited values.…, The fields of a ``playwright.async_api.Request`` the guard reads. (+18 more)

### Community 36 - "CLAUDE.md (project instructions)"
Cohesion: 0.12
Nodes (19): CLAUDE.md (project instructions), D101: labeled_value refuses a table-header resolution (general fix), D102: label_header/value_header flags ported into agent.py + cli.py capture path, D92: Evidence Capture Helpers (save_discovery_evidence/save_replay_evidence), D93: Pre-existing 02_artifact_schema.py IndexError bug, D95: Missing create_deep_agent import found live in BROWSER 12, D96: build_agent() goal_text vs given_text field-name bug, D97: cua replay --login flag + repeated Balance header trap (+11 more)

### Community 37 - "make_replay_ctx"
Cohesion: 0.08
Nodes (49): make_replay_ctx(), mk_look(), navigate(), Ctx, Replay test helpers: ``make_replay_ctx`` (a real Ctx on fakes), ``mk_look``,…, A real Ctx (real SendGuard, real ReplayRun) over a fake page/control/lock.…, ``take_look`` always returns this look., screen() (+41 more)

### Community 38 - "RefCounter"
Cohesion: 0.06
Nodes (44): draw_numbered(), number(), ocr(), NDArray, uint8, Fresh element refs for one run. Refs grow for the whole run and are never…, Reading order (rows top to bottom, then left to right), fresh refs., RefCounter (+36 more)

### Community 39 - "manifest.json"
Cohesion: 0.11
Nodes (18): action, default_icon, default_title, background, service_worker, 128, 16, 32 (+10 more)

### Community 41 - "choose_option_at_point"
Cohesion: 0.38
Nodes (7): Confirm, LookFn, choose_option_at_index(), choose_option_at_point(), Session, Select the first option containing this text in the dropdown at (or next to)…, Select this exact live option in the Nth <select> (``index``), else the one at…

### Community 42 - "redactor"
Cohesion: 0.20
Nodes (13): Pattern, text -> text with every value masked. Numbers match however they are written…, redactor(), test_a_short_number_is_masked_only_as_a_whole_number(), test_the_two_numbers_really_differ(), _notebook(), redactor/norm: the value masker discovery uses (numbers however written, whole…, test_a_number_matches_however_it_is_written() (+5 more)

### Community 43 - "replay/context.py"
Cohesion: 0.10
Nodes (20): pydantic, Ctx, note_takeover_send(), Page, Request, Ctx: what every replay function takes first (session, run, settings, send…, R7: nothing kept. A fresh run, and the guard reads that one from now on., wipe() (+12 more)

### Community 44 - "ReplayResult"
Cohesion: 0.16
Nodes (11): ReplayResult, test_partial_label_when_not_success(), test_result_type_is_the_schema_one(), test_the_outputs_line_shows_rows(), ReplayResult summary/outputs_line, Stop, and the Status values., test_partial_outputs_line_when_not_success(), test_result_defaults(), test_stop_carries_its_fields() (+3 more)

### Community 45 - "human.py"
Cohesion: 0.13
Nodes (27): Field, list_options(), Every option of the dropdown at this point ([] if it is not a dropdown)., Every shape the whole value matches, in precedence order. Safe to log: names,…, shapes_of(), _checked(), Result, What one_at_a_time does with a tool's result (the notebook's wrapper body after… (+19 more)

### Community 47 - "FakeTab"
Cohesion: 0.08
Nodes (42): DiscoveryConfig, Discovery-only settings., Discovery: an LLM agent learns a task once and the recorder saves it as a…, attach(), build_ctx(), _count_nav(), _hooks(), new_run() (+34 more)

### Community 48 - "locate"
Cohesion: 0.23
Nodes (22): locate(), Path, Target, (point, rung) from the first rung that hits, or None., Anchor, OcrText, _dup_target(), _look() (+14 more)

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
Cohesion: 0.14
Nodes (24): replay_control(), Asker, hand_back(), Future, Protocol, The shared take-over loop pieces. Each side's own take-over stays with that…, Done on the toolbar button or in the take-over panel hands back. No reminders…, takeover_text() (+16 more)

### Community 53 - "test_extension.py"
Cohesion: 0.11
Nodes (28): Answerable, button_clicked(), ext_call(), Extension, handback_button(), Future, Protocol, The hand-back extension (the Chrome toolbar button): its service worker, never… (+20 more)

### Community 54 - "Session"
Cohesion: 0.15
Nodes (19): BrowserContext, Playwright, playwright_async_api, Playwright, no decisions: the open session, the site lock, our own input,…, Our own input into the locked site tab: ``act`` (unlock, run steps, relock,…, _alive(), check_viewport(), _extension() (+11 more)

### Community 55 - "read_helpers.py"
Cohesion: 0.11
Nodes (29): clean_label(), column_header(), is_word(), label_near(), merged_label(), Where a point is on a look, in words: labels, anchors, page texts. Pure (no…, The value's column, walked upwards while each text is within TABLE_GAP of the…, The texts on el's row, left of it, up to its table's left edge: the first CLEAR… (+21 more)

### Community 56 - "Capability"
Cohesion: 0.14
Nodes (25): _ask(), ask_inputs(), ask_option(), _ask_rows(), given_inputs(), input_type(), _missing_crops(), mistyped() (+17 more)

### Community 57 - "read.py"
Cohesion: 0.14
Nodes (26): Cols, _columns(), headings(), is_header(), off_table(), page_texts(), The look's words, tallest text first (a page heading is its biggest text)., The words on a look (never a value: letters, no run value in them), to pick a… (+18 more)

### Community 59 - "BrowserConfig"
Cohesion: 0.14
Nodes (12): The response to a send lands after the human's approval, not after the click:…, wait_for_change(), BrowserConfig, Settings shared by discovery and replay (the same page size at both, Q10)., The handful of ``playwright.async_api.Request`` fields the project's code reads., _Request, _png(), ShotsPage (+4 more)

### Community 62 - "guard.py"
Cohesion: 0.14
Nodes (19): functools, An evidence screenshot: short timeout, None on failure (never hangs on a held…, snap(), run_goal: one goal through the discovery agent (moved from discovery.py…, _start(), after_login_click(), gate_click(), log() (+11 more)

### Community 63 - "Discovery decisions"
Cohesion: 0.08
Nodes (24): Base decisions, Cuts, Discovery decisions, Q10: window size and zoom — DECIDED, Q11: notebook format — DECIDED, Q12: dropdowns — DECIDED, Q13: scrolling — DECIDED, Q14: private data in saved pictures — DECIDED (+16 more)

### Community 64 - "2. Each box, with an example"
Cohesion: 0.12
Nodes (15): 1. Diagram, 2. Each box, with an example, 3. All tools, 4. Step by step: one discovery run, 5. Notes, Browser (Playwright), Control window and site lock (Q-A), Discovery architecture (+7 more)

### Community 65 - "test_capability.py"
Cohesion: 0.12
Nodes (17): MonkeyPatch, parametrize, Path, Every capability saved in the top-level artifacts/ folder (Decision 6) loads in…, test_a_saved_artifact_loads_in_replay(), test_a_saved_artifact_round_trips(), test_the_old_artifacts_folder_is_gone(), _data() (+9 more)

### Community 66 - "ControlWindow"
Cohesion: 0.11
Nodes (20): base64, Question, ControlWindow, discovery_control(), _img(), Protocol, ControlWindow: our own "Agent control" tab, the only place a human answers.…, Answers the question on top. Closing the window (None) answers every one: fail… (+12 more)

### Community 67 - "2. Components"
Cohesion: 0.12
Nodes (15): 1. Diagram, 2. Components, 3. Step types, 4. Worked example: ParaBank login + read balance, 5. Notes, Actor, Artifact (made by discovery, not replay), Browser setup (+7 more)

### Community 68 - "replay/evidence.py"
Cohesion: 0.16
Nodes (18): _clean(), _png(), OcrFn, Redact, _drift_lines(), masked_outputs(), Ctx, JsonValue (+10 more)

### Community 69 - "Pure-Visual Discovery Notebook: Build Plan"
Cohesion: 0.09
Nodes (22): 10. Open risks, 1. Global constraints (every task must follow these), 2. Review focus (inputs no spec line covers, but likely to bite), 3. What already exists (reuse, or its visual version), 3a. How the agent is built today (`agent.ipynb` STEP 4, `src/cua/agent.py`), 3b. Existing handoff rules: when a human is called in, 3c. Existing tools → the new tools, 4. New dependencies (checked on PyPI, 2026-09-28) (+14 more)

### Community 70 - "ReplayConfig"
Cohesion: 0.36
Nodes (8): Replay-only settings., ReplayConfig, Rung 2 anchors only. Discovery saves labels cleaned ('to account #'); live OCR…, same_label(), test_anchor_label_matches_ocr_merged_with_a_value(), test_from_label_is_not_the_to_anchor(), test_the_right_label_still_matches(), test_the_to_anchor_finds_the_to_label_not_the_from_label()

### Community 71 - "SiteLock"
Cohesion: 0.16
Nodes (12): CdpSender, Protocol, SiteLock: the site tab ignores all real input (CDP…, The one method of a Playwright ``CDPSession`` the lock uses., The site tab ignores all real input (CDP). Lifted only around our own action or…, SiteLock, FakeCdp, asyncio (+4 more)

### Community 72 - "test_recorder_reads.py"
Cohesion: 0.09
Nodes (27): flag_leaks(), Mark (never store) an event whose label, anchor, own text, hint or input name…, _FakeModel, asyncio, Stands in for a LangChain chat model: no network, records the prompt., asyncio, parametrize, What the tools log, compiled: read-only runs, tables, labels joined to values,… (+19 more)

### Community 73 - "ocr.py"
Cohesion: 0.50
Nodes (4): RapidOCR, ocr_engine(), The shared RapidOCR engine, OCR itself, numbering and the numbered-box overlay.…, The RapidOCR engine, built once per process. rapidocr is imported here only, so…

### Community 74 - "config.py"
Cohesion: 0.12
Nodes (21): dotenv, pathlib, _actions(), _find_root(), load_site(), OutcomeRule, _outcomes(), Path (+13 more)

### Community 75 - "engine.py"
Cohesion: 0.12
Nodes (41): Drift, Exception, action_allowed(), _cleanup_step(), error_page(), finish(), is_cleanup(), judge() (+33 more)

### Community 76 - "json"
Cohesion: 0.33
Nodes (3): json, The hand-back extension never touches any site: no content scripts, no host…, Exec chosen top-level defs of a notebook (the old ast-exec pattern) for parity…

### Community 77 - "test_routing.py"
Cohesion: 0.06
Nodes (49): CaptureFixture, langchain_agents_middleware, ModelKind, ModuleType, os, build_routing_middleware(), Classifier, confidence_gate() (+41 more)

### Community 79 - "masked"
Cohesion: 0.50
Nodes (4): masked(), fixture, MonkeyPatch, The OCR mask is tested in tests/unit/safety; here: that every PNG goes through…

### Community 80 - "Look"
Cohesion: 0.08
Nodes (51): crop_box(), cut_crop(), element_at(), Crops around one point: find the element there, crop around it, read text near…, Crop around the target, with every other piece of text blanked out., Pixels around the point changed. Catches password dots that OCR cannot read., read_near(), spot_changed() (+43 more)

### Community 81 - "test_session.py"
Cohesion: 0.24
Nodes (11): LivePage, _png(), asyncio, MonkeyPatch, Path, open_session reuses a live session (a notebook re-run must not leak a browser),…, _session(), test_a_live_existing_session_is_returned_unchanged() (+3 more)

### Community 82 - "test_prompt.py"
Cohesion: 0.11
Nodes (11): inspect, langgraph_checkpoint_memory, The discovery agent: system prompt, middleware, optional TypeSafe routing, and…, The discovery agent's system prompt, verbatim from…, _capture(), MonkeyPatch, build_agent: the notebook's create_deep_agent call, with routing appended only…, test_build_agent_wires_the_notebooks_agent() (+3 more)

### Community 84 - "seen_outcome"
Cohesion: 0.67
Nodes (3): The first rule whose text (whole words, any case) appeared on screen with this…, seen_outcome(), test_text_already_on_screen_before_the_step_is_not_an_outcome()

### Community 85 - "build_tools"
Cohesion: 0.16
Nodes (16): AsyncFunctionDef, build_tools(), BaseTool, Ctx, observe, click, type_text, type_secret, select_option, scroll, open_path,…, test_the_prompt_lists_every_tool(), test_every_built_tool_has_an_action_type(), _notebook_tools() (+8 more)

### Community 86 - "cua"
Cohesion: 0.50
Nodes (3): cua, Read order, Rules

### Community 87 - "cua/__init__.py"
Cohesion: 0.33
Nodes (3): cua: shared config and the LLM model factory (direct Anthropic or an optional…, host_allowed: only the site's own hosts (D15); about:blank always., test_only_allowed_hosts_and_blank()

### Community 88 - "cua.schema"
Cohesion: 0.50
Nodes (3): cua.schema, Read order, What may NOT go here

### Community 89 - "locate.py"
Cohesion: 0.13
Nodes (24): SameTextLike, Replay: runs a capability saved by discovery with plain code, no LLM (step 4:…, fill(), Put inputs into `{{name}}`. `{{secret:x}}` stays as it is: secrets go in only…, secret_name(), anchor_point(), find_template(), find_text() (+16 more)

### Community 90 - "types"
Cohesion: 0.20
Nodes (14): dropdown_options(), mismatches(), _norm_num(), Dropdown, Values a send carries that the human never gave, and the dropdown choices to…, Numbers being sent that the human never gave, e.g. account 1450 vs 1400. Only…, For each key: the options of the page dropdown whose CURRENT value is exactly…, _hide() (+6 more)

### Community 92 - "test_goal.py"
Cohesion: 0.13
Nodes (24): Agent, Ctx, Protocol, What run_goal needs of the compiled deep agent., The deadline passed: end the run STUCK, keeping what the agent did so far., New run on a fresh thread; pass an earlier thread_id to resume it with a next…, run_goal(), _timed_out() (+16 more)

### Community 93 - "test_human_tools.py"
Cohesion: 0.21
Nodes (16): ActTab, SimpleNamespace, A site tab the act/nav tools drive: ``mouse``/``keyboard`` record into…, _ctx(), asyncio, Ctx, MonkeyPatch, finish_business_outcome / request_missing_values / ask_human (the human-facing… (+8 more)

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
Cohesion: 0.16
Nodes (30): BaseModel, model_validator, _navigate(), Event log -> ``Capability``: steps, inputs, outputs and secrets come from the…, ``to_step``'s open_path branch, unchanged., target(), to_step(), input_name() (+22 more)

### Community 109 - "test_evidence.py"
Cohesion: 0.40
Nodes (12): _artifact(), Path, save_evidence: one masked folder per run. No run value or secret is ever…, _save(), test_a_failed_run_still_writes_evidence(), test_an_artifact_holding_a_run_value_is_refused(), test_capability_yaml_and_crops_are_copied(), test_final_shot_is_written_masked_for_a_stuck_run_only() (+4 more)

### Community 110 - "make_ctx"
Cohesion: 0.13
Nodes (33): make_ctx(), Ctx, Session, A discovery ``Ctx`` over fakes, built like ``attach`` but with no page wiring., helped(), _only(), asyncio, fixture (+25 more)

### Community 113 - "Replay notebook plan"
Cohesion: 0.33
Nodes (5): Decisions made here (review), Open questions for the user, Replay notebook plan, Sections, Tasks

### Community 114 - "Ctx"
Cohesion: 0.08
Nodes (68): P, act(), canvas(), choose_option(), crop(), Ctx, into_box(), look() (+60 more)

### Community 117 - "test_dropdowns.py"
Cohesion: 0.22
Nodes (15): _approve(), HeldPage, _logged(), asyncio, Ctx, A dropdown the send carries becomes a Select step; the guard hooks never read a…, Page reads (a held send blocks them); bring_to_front is the control window's…, Human values (zip, phone, SSN) are not in the goal: no mismatch form, no… (+7 more)

### Community 118 - "load_capability"
Cohesion: 0.13
Nodes (29): load_capability(), load_outcomes(), Path, The capability and the folder its crop paths are relative to., The capability's own `outcomes:` [{text, status, meaning}], else the site's…, Path, Discovery's saved artifact runs in replay unchanged: build -> save -> load ->…, test_crop_paths_resolve_to_saved_files() (+21 more)

### Community 120 - "cua/evidence.py"
Cohesion: 0.14
Nodes (19): config_hash(), git_sha(), JsonValue, Path, Evidence helpers shared by discovery and replay: masking a JSON-able tree,…, `git rev-parse HEAD`, or "unknown" (no git, not a repo, any failure)., sha256 of the repr of the frozen configs plus the site name., What ``run.json`` holds: prompt version, model, config hash, git sha. Never a… (+11 more)

### Community 123 - "discovery/evidence.py"
Cohesion: 0.23
Nodes (15): _copy_capability(), _events(), _folder(), Ctx, OcrFn, Path, Redact, One masked folder per discovery run: goal, answer, events, transcript, crops,… (+7 more)

### Community 131 - "replay/wiring.py"
Cohesion: 0.19
Nodes (9): _note_latest(), note_response(), Protocol, Page wiring for replay: :func:`attach` (the notebook's setup cell, replay.py…, The Playwright ``Response`` fields note_response reads., The once-per-page listener: note on the ctx of the latest attach to this page., Keep the main document's HTTP status (not sub-resources, not iframes)., _Request (+1 more)

### Community 134 - "bind_control"
Cohesion: 0.31
Nodes (6): bind_control(), ControlTab, Protocol, Bind the control tab to the current :class:`ControlWindow`, once per tab. A…, The Playwright calls binding makes on the control tab., Point the control tab's buttons and its close at ``control``. Re-run safe: the…

### Community 141 - "cua.discovery.agent"
Cohesion: 0.50
Nodes (3): cua.discovery.agent, Read order, What may NOT go here

## Knowledge Gaps
- **159 isolated node(s):** `MODES`, `manifest_version`, `name`, `version`, `description` (+154 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **12 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Look` connect `Look` to `fakes.py`, `test_act.py`, `test_input.py`, `test_dropdown.py`, `discovery/context.py`, `test_replay_rescue.py`, `pytest`, `steps.py`, `make_replay_ctx`, `RefCounter`, `human.py`, `FakeTab`, `locate`, `Session`, `read_helpers.py`, `read.py`, `BrowserConfig`, `locate.py`, `test_human_tools.py`, `test_human.py`, `Ctx`, `test_dropdowns.py`, `load_capability`?**
  _High betweenness centrality (0.062) - this node is a cross-community bridge._
- **Why does `BrowserConfig` connect `BrowserConfig` to `cli.py`, `fakes.py`, `test_input.py`, `test_dropdown.py`, `test_replay_handback.py`, `SiteProfile`, `make_replay_ctx`, `RefCounter`, `replay/context.py`, `FakeTab`, `test_takeover_loop.py`, `test_extension.py`, `Session`, `Capability`, `test_capability.py`, `config.py`, `Look`, `test_session.py`, `test_human_tools.py`, `Ctx`, `load_capability`, `cua/evidence.py`?**
  _High betweenness centrality (0.052) - this node is a cross-community bridge._
- **Why does `Ctx` connect `Ctx` to `fakes.py`, `replay/wiring.py`, `test_act.py`, `rescue.py`, `test_replay_inputs.py`, `test_middleware.py`, `discovery/context.py`, `test_replay_engine.py`, `test_replay_rescue.py`, `test_replay_handback.py`, `SiteProfile`, `test_replay_wiring.py`, `test_replay_table.py`, `make_replay_ctx`, `human.py`, `FakeTab`, `Session`, `read.py`, `BrowserConfig`, `guard.py`, `Look`, `test_goal.py`, `test_human_tools.py`, `test_human.py`, `test_dropdowns.py`, `discovery/evidence.py`?**
  _High betweenness centrality (0.048) - this node is a cross-community bridge._
- **Are the 26 inferred relationships involving `Look` (e.g. with `Ctx` and `DiscoveryRun`) actually correct?**
  _`Look` has 26 INFERRED edges - model-reasoned connections that need verification._
- **Are the 59 inferred relationships involving `Ctx` (e.g. with `LatestScreenshotOnly` and `NoopAnthropicPromptCachingMiddleware`) actually correct?**
  _`Ctx` has 59 INFERRED edges - model-reasoned connections that need verification._
- **Are the 35 inferred relationships involving `BrowserConfig` (e.g. with `Session` and `Answerable`) actually correct?**
  _`BrowserConfig` has 35 INFERRED edges - model-reasoned connections that need verification._
- **Are the 30 inferred relationships involving `ReplayConfig` (e.g. with `Ctx` and `_Request`) actually correct?**
  _`ReplayConfig` has 30 INFERRED edges - model-reasoned connections that need verification._