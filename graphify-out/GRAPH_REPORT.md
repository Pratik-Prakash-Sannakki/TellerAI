# Graph Report - BankerAgent  (2026-10-01)

## Corpus Check
- 224 files · ~263,165 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 2577 nodes · 7310 edges · 113 communities (100 shown, 13 thin omitted)
- Extraction: 93% EXTRACTED · 7% INFERRED · 0% AMBIGUOUS · INFERRED: 497 edges (avg confidence: 0.63)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `fb1dcf70`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- cli.py
- fakes.py
- Productionize Plan: notebooks → `src/cua/` package
- test_act.py
- Evidence README
- agent/build.py
- vision/__init__.py
- test_replay_inputs.py
- BrowserConfig
- act.py
- test_dropdown.py
- save_discovery_evidence / save_replay_evidence (D92)
- Replay decisions
- Five Error Demos (D30)
- langchain_typesafe
- langchain_typesafe_experimental_middleware
- discovery/run.py
- test_cli.py
- test_replay_engine.py
- test_replay_rescue.py
- test_llm.py
- test_replay_handback.py
- redact.py
- request.py
- test_replay_wiring.py
- recorder/__init__.py
- steps.py
- test_notebooks.py
- integration/conftest.py
- pathlib
- test_replay_table.py
- test_redact_more.py
- mk_look
- build_capability
- make_replay_ctx
- safety/__init__.py
- CLAUDE.md (project instructions)
- test_replay_steps.py
- input.py
- manifest.json
- langchain_tools
- test_recorder_runs.py
- hosts.py
- test_read_helpers.py
- IndexPage
- human.py
- FakeTab
- discovery/wiring.py
- test_send_guard.py
- test_control_window.py
- cua.vision
- test_takeover_loop.py
- ReplayConfig
- Session
- RefCounter
- Look
- test_extension.py
- SendGuard
- langgraph_types
- Discovery decisions
- 2. Each box, with an example
- ControlWindow
- 2. Components
- Pure-Visual Discovery Notebook: Build Plan
- SiteLock
- config.py
- engine.py
- loader.py
- .awrap_model_call
- Box
- test_session.py
- test_prompt.py
- copy
- build_tools
- cua
- masked_outputs
- cua.schema
- handoff/__init__.py
- load
- run_goal
- test_human_tools.py
- test_screenshot.py
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
- _FakeModel
- test_evidence.py
- make_ctx
- test_replay_evidence.py
- Replay notebook plan
- Ctx
- test_dropdowns.py
- load_capability
- replay/evidence.py
- locate
- discovery/evidence.py
- FakeWin
- routing.py
- background.js
- save_artifact
- ReplayResult
- replay/wiring.py
- test_middleware.py
- replay/context.py
- cua.discovery.agent
- pytest

## God Nodes (most connected - your core abstractions)
1. `Look` - 116 edges
2. `BrowserConfig` - 82 edges
3. `Ctx` - 80 edges
4. `make_ctx()` - 78 edges
5. `ReplayConfig` - 67 edges
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
- 3-file cycle: `src/cua/discovery/tools/__init__.py -> src/cua/discovery/tools/act.py -> src/cua/discovery/tools/guard.py -> src/cua/discovery/tools/__init__.py`
- 3-file cycle: `src/cua/discovery/tools/__init__.py -> src/cua/discovery/tools/act.py -> src/cua/discovery/tools/observe.py -> src/cua/discovery/tools/__init__.py`
- 3-file cycle: `src/cua/discovery/tools/__init__.py -> src/cua/discovery/tools/nav.py -> src/cua/discovery/tools/guard.py -> src/cua/discovery/tools/__init__.py`
- 3-file cycle: `src/cua/discovery/tools/__init__.py -> src/cua/discovery/tools/nav.py -> src/cua/discovery/tools/observe.py -> src/cua/discovery/tools/__init__.py`
- 3-file cycle: `src/cua/discovery/tools/__init__.py -> src/cua/discovery/tools/human.py -> src/cua/discovery/tools/observe.py -> src/cua/discovery/tools/__init__.py`
- 3-file cycle: `src/cua/discovery/tools/__init__.py -> src/cua/discovery/tools/read.py -> src/cua/discovery/tools/guard.py -> src/cua/discovery/tools/__init__.py`
- 3-file cycle: `src/cua/discovery/tools/guard.py -> src/cua/discovery/tools/human.py -> src/cua/discovery/tools/observe.py -> src/cua/discovery/tools/guard.py`
- 4-file cycle: `src/cua/discovery/tools/__init__.py -> src/cua/discovery/tools/act.py -> src/cua/discovery/tools/human.py -> src/cua/discovery/tools/observe.py -> src/cua/discovery/tools/__init__.py`
- 4-file cycle: `src/cua/discovery/tools/__init__.py -> src/cua/discovery/tools/act.py -> src/cua/discovery/tools/observe.py -> src/cua/discovery/tools/guard.py -> src/cua/discovery/tools/__init__.py`
- 4-file cycle: `src/cua/discovery/tools/__init__.py -> src/cua/discovery/tools/nav.py -> src/cua/discovery/tools/observe.py -> src/cua/discovery/tools/guard.py -> src/cua/discovery/tools/__init__.py`
- 4-file cycle: `src/cua/discovery/tools/__init__.py -> src/cua/discovery/tools/human.py -> src/cua/discovery/tools/observe.py -> src/cua/discovery/tools/guard.py -> src/cua/discovery/tools/__init__.py`
- 5-file cycle: `src/cua/discovery/tools/__init__.py -> src/cua/discovery/tools/act.py -> src/cua/discovery/tools/guard.py -> src/cua/discovery/tools/human.py -> src/cua/discovery/tools/observe.py -> src/cua/discovery/tools/__init__.py`
- 5-file cycle: `src/cua/discovery/tools/__init__.py -> src/cua/discovery/tools/act.py -> src/cua/discovery/tools/human.py -> src/cua/discovery/tools/observe.py -> src/cua/discovery/tools/guard.py -> src/cua/discovery/tools/__init__.py`
- 5-file cycle: `src/cua/discovery/tools/__init__.py -> src/cua/discovery/tools/nav.py -> src/cua/discovery/tools/guard.py -> src/cua/discovery/tools/human.py -> src/cua/discovery/tools/observe.py -> src/cua/discovery/tools/__init__.py`
- 5-file cycle: `src/cua/discovery/tools/__init__.py -> src/cua/discovery/tools/read.py -> src/cua/discovery/tools/guard.py -> src/cua/discovery/tools/human.py -> src/cua/discovery/tools/observe.py -> src/cua/discovery/tools/__init__.py`

## Communities (113 total, 13 thin omitted)

### Community 0 - "cli.py"
Cohesion: 0.16
Nodes (20): argparse, Namespace, _close(), default_site(), discover(), main(), parse_args(), parse_inputs() (+12 more)

### Community 1 - "fakes.py"
Cohesion: 0.08
Nodes (16): blank_png(), FakeControl, FakePage, FakeRoute, Shared offline fakes for the ported test suite (tests/unit, tests/integration).…, A fake discovery/replay ``CONTROL`` surface (what ``ControlWindow`` presents).…, A plain PNG of this canvas size (canvas/crops decode the look's png)., The handful of ``playwright.async_api.Request`` fields the project's code reads. (+8 more)

### Community 2 - "Productionize Plan: notebooks → `src/cua/` package"
Cohesion: 0.12
Nodes (16): 10. Line-count offenders (today), 1. Package tree, 2. De-duplication (checked by AST diff of both notebooks), 3. State: globals → explicit objects, 4. Async and typing, 5. Notebooks after the move, 6. Tests, 7. ML-engineering practices (kept small) (+8 more)

### Community 3 - "test_act.py"
Cohesion: 0.07
Nodes (72): Items, make_look(), A look whose elements are numbered 1.. in order (ref, text, box)., Driven, _head(), _helped(), _logged_arg_keys(), asyncio (+64 more)

### Community 5 - "agent/build.py"
Cohesion: 0.13
Nodes (19): CompiledStateGraph, deepagents, Handler, langchain_agents_middleware, build_agent(), BaseChatModel, Ctx, build_agent: the notebook's ``AGENT = create_deep_agent(...)`` (discovery.py… (+11 more)

### Community 6 - "vision/__init__.py"
Cohesion: 0.11
Nodes (30): Pixels -> text: screenshots, OCR, canvas math, crops, and the shared table…, cell_shape(), col_of(), column_spans(), like_rows(), The shared OCR table reader: discovery and replay use it to find a table's…, A table's end: a line that no longer looks like its rows (a footer, a menu, a…, date', 'amount', or 'text': enough to tell a row cell from a footer line in its… (+22 more)

### Community 7 - "test_replay_inputs.py"
Cohesion: 0.13
Nodes (31): Path, select(), type_(), write_cap(), _cap(), ClearPage, env(), FakeForm (+23 more)

### Community 8 - "BrowserConfig"
Cohesion: 0.09
Nodes (30): act(), into_box(), Lock, Page, Session, Step, The response to a send lands after the human's approval, not after the click:…, Unlock the site tab, run our own input steps, relock, settle, take a new look. (+22 more)

### Community 9 - "act.py"
Cohesion: 0.12
Nodes (40): P, landed(), _landing(), make_act_tools(), _make_click(), _make_select_option(), _make_type_secret(), _make_type_text() (+32 more)

### Community 10 - "test_dropdown.py"
Cohesion: 0.08
Nodes (40): BaseException, Confirm, LookFn, playwright_async_api, choose_option_at_index(), choose_option_at_point(), list_options(), Dropdown (+32 more)

### Community 12 - "Replay decisions"
Cohesion: 0.08
Nodes (23): R10: where the compile step lives — DECIDED, R11: why compile, if `response_format` exists? — PROPOSED, R12: what each step type compiles to — PROPOSED, R13: target schema — PROPOSED, R14: what rung 2 needs that discovery doesn't record — DONE, R15: auto-approve at replay — PROPOSED, R16: dead ends and retries at compile — PROPOSED, R17: replay result statuses — PROPOSED (+15 more)

### Community 16 - "discovery/run.py"
Cohesion: 0.09
Nodes (25): Saved, The current run (the one the send guard serves)., DiscoveryRun, DiscoveryRun: one discovery run's working state (was the notebook's…, What the human gave: the goal and every answer (the send guard's mismatch text)., Every value typed, entered, given or sent this run, plus the secrets (in memory…, Every saved text, table cells included (evidence masking only)., Banking: values live only for the run. Keep the log (labels only), drop the… (+17 more)

### Community 17 - "test_cli.py"
Cohesion: 0.14
Nodes (21): _fake_session(), _patch_session(), MonkeyPatch, parametrize, Path, SimpleNamespace, cua.cli: argument parsing, --input parsing, and main() as the only asyncio.run…, _record_run() (+13 more)

### Community 18 - "test_replay_engine.py"
Cohesion: 0.22
Nodes (40): cap(), click(), extract(), _finish(), _login_cap(), _no_snap(), _pcap(), asyncio (+32 more)

### Community 19 - "test_replay_rescue.py"
Cohesion: 0.06
Nodes (44): The guard keeps its own reference to the control window: swap both., set_control(), DoneWhileSending, _env(), _fail_clicks(), FormRoute, Frame, GateControl (+36 more)

### Community 20 - "test_llm.py"
Cohesion: 0.18
Nodes (13): _clean_env(), CaptureFixture, fixture, MonkeyPatch, Offline tests for `cua.llm.make_chat_model` (Iliad gateway). No network, no…, test_ca_bundle_passthrough(), test_existing_ssl_cert_file_wins(), test_fallback_to_anthropic_key() (+5 more)

### Community 21 - "test_replay_handback.py"
Cohesion: 0.13
Nodes (23): FakePage, _bctx(), Ext, Human, PanelDone, asyncio, Ctx, parametrize (+15 more)

### Community 22 - "redact.py"
Cohesion: 0.18
Nodes (14): Pattern, _num(), Value masking: ``norm``, ``is_sensitive``, ``hide_secrets``, ``redactor``,…, text -> text with every value masked. Numbers match however they are written…, redactor(), test_a_short_number_is_masked_only_as_a_whole_number(), _notebook(), redactor/norm: the value masker discovery uses (numbers however written, whole… (+6 more)

### Community 23 - "request.py"
Cohesion: 0.16
Nodes (19): functools, json, JsonObj, _flat(), _json(), What a held request sends, and the same request rebuilt with edited values.…, Every value a request sends, from its query, a form body, or a JSON body…, The request's url and body with these values put back in, in the same format. (+11 more)

### Community 24 - "test_replay_wiring.py"
Cohesion: 0.10
Nodes (15): Working values for one run. Replaced by a new one in ``replay``'s ``finally``…, What the mismatch check compares a send against (SendState)., ReplayRun, asyncio, MonkeyPatch, Path, attach (the replay setup cell), the guard's replay hooks, and R7: after…, Route (+7 more)

### Community 25 - "recorder/__init__.py"
Cohesion: 0.09
Nodes (43): output(), ``build_capability``'s refusals, unchanged: a leaked value, a blind dropdown,…, _refuse(), used_inputs(), checkpoint(), The capability's checkpoint: the text replay must see to call the run a…, C: after a send, the page's own response proves success (the agent's proof only…, field_area() (+35 more)

### Community 26 - "steps.py"
Cohesion: 0.10
Nodes (44): Point, changed(), choose_option(), do_click(), do_extract(), do_navigate(), do_scroll(), do_select() (+36 more)

### Community 27 - "test_notebooks.py"
Cohesion: 0.08
Nodes (41): AST, Call, Module, _bind(), _code_cells(), _markdown(), _offline_namespace(), parametrize (+33 more)

### Community 29 - "pathlib"
Cohesion: 0.12
Nodes (8): pathlib, The hand-back extension never touches any site: no content scripts, no host…, Frozen notebook sources for the parity tests (step 10 replaced the notebooks…, Guard: no site value lives in src/. Site values belong in configs/<site>.yaml…, parametrize, Path, The frozen notebook snapshots the parity tests read must never drift (see…, test_snapshot_is_unchanged()

### Community 30 - "test_replay_table.py"
Cohesion: 0.21
Nodes (18): _cap(), _defs(), Page, asyncio, Ctx, MonkeyPatch, Path, do_extract_table: find the header by its label, read the rows with discovery's… (+10 more)

### Community 31 - "test_redact_more.py"
Cohesion: 0.16
Nodes (19): mask_png(), OcrFn, Black out every OCR box whose text holds a run value. A clean image is written…, encode(), NDArray, uint8, _ocr(), _png() (+11 more)

### Community 32 - "mk_look"
Cohesion: 0.16
Nodes (14): FakeLock, mk_look(), Ctx, Replay test helpers: ``make_replay_ctx`` (a real Ctx on fakes), ``mk_look``,…, SiteLock stand-in: open() unlocks for the block., ``take_look`` always returns this look., screen(), set_shoot() (+6 more)

### Community 33 - "build_capability"
Cohesion: 0.07
Nodes (69): build_capability(), Steps, inputs and secrets come from the log only. The model's text cannot fail…, flag_leaks(), Mark (never store) an event whose label, anchor, own text, hint or input name…, _ev(), _meta(), Path, The recorder: the event log becomes a replay-ready capability (R12, R13, R16).… (+61 more)

### Community 34 - "make_replay_ctx"
Cohesion: 0.18
Nodes (24): make_replay_ctx(), A real Ctx (real SendGuard, real ReplayRun) over a fake page/control/lock.…, _extract(), _notebook_assign(), _pcap(), asyncio, Ctx, parametrize (+16 more)

### Community 35 - "safety/__init__.py"
Cohesion: 0.12
Nodes (14): dataclasses, Safety: what may leave the tab (hosts, the two send gates) and keeping values…, Protocol, The fields of a ``playwright.async_api.Request`` the guard reads., Request, ControlLike, GuardOptions, LookLike (+6 more)

### Community 36 - "CLAUDE.md (project instructions)"
Cohesion: 0.12
Nodes (19): CLAUDE.md (project instructions), D101: labeled_value refuses a table-header resolution (general fix), D102: label_header/value_header flags ported into agent.py + cli.py capture path, D92: Evidence Capture Helpers (save_discovery_evidence/save_replay_evidence), D93: Pre-existing 02_artifact_schema.py IndexError bug, D95: Missing create_deep_agent import found live in BROWSER 12, D96: build_agent() goal_text vs given_text field-name bug, D97: cua replay --login flag + repeated Balance header trap (+11 more)

### Community 37 - "test_replay_steps.py"
Cohesion: 0.08
Nodes (38): navigate(), _click_env(), _form_png(), GotoPage, _judge(), Page, asyncio, Ctx (+30 more)

### Community 38 - "input.py"
Cohesion: 0.15
Nodes (14): Our own input into the locked site tab: ``act`` (unlock, run steps, relock,…, canvas_size(), NDArray, uint8, Canvas-pixel <-> page-point mapping: any window size or pixel density maps to…, Fit the screenshot inside the canvas. Returns it and canvas-pixel -> page-point…, The size of the image the model is looking at right now., to_canvas() (+6 more)

### Community 39 - "manifest.json"
Cohesion: 0.11
Nodes (18): action, default_icon, default_title, background, service_worker, 128, 16, 32 (+10 more)

### Community 41 - "test_recorder_runs.py"
Cohesion: 0.13
Nodes (25): _click(), _clicks(), _go(), _names(), _nav(), _noop_click(), _paths(), Recorder behaviour pinned by live runs: detours, 404s, login clicks kept, no-op… (+17 more)

### Community 42 - "hosts.py"
Cohesion: 0.25
Nodes (4): cua: shared config and the LLM model factory (Iliad gateway) for the pure-…, Which hosts the browser may reach (D15). The allowlist itself lives in the site…, host_allowed: only the site's own hosts (D15); about:blank always., test_only_allowed_hosts_and_blank()

### Community 43 - "test_read_helpers.py"
Cohesion: 0.33
Nodes (8): _look(), where / label_near / spot / page_texts: a point's label in words, never a…, Live bug: 'From account #' dropdown showing '74838' was saved as input…, Live bug: 'Sean' typed into Payee Name became the Address step's label and…, test_a_dropdowns_own_number_is_never_its_label(), test_a_typed_value_above_is_never_the_next_fields_label(), test_page_texts_and_headings_are_words_without_run_values(), test_where_records_label_box_ordinal_offset_but_not_the_box_contents()

### Community 45 - "human.py"
Cohesion: 0.24
Nodes (16): Field, _enter(), human_fills(), _make_ask_human(), _make_finish(), make_human_tools(), _make_request_missing_values(), _options() (+8 more)

### Community 46 - "FakeTab"
Cohesion: 0.09
Nodes (7): ActTab, FakeInput, FakeTab, SimpleNamespace, A fake site or control tab with the Playwright calls discovery's wiring and…, A fake ``page.mouse`` / ``page.keyboard``: every call is recorded as ``(name,…, A site tab the act/nav tools drive: ``mouse``/``keyboard`` record into…

### Community 47 - "discovery/wiring.py"
Cohesion: 0.11
Nodes (37): DiscoveryConfig, Discovery-only settings., Discovery: an LLM agent learns a task once and the recorder saves it as a…, attach(), build_ctx(), _count_nav(), _hooks(), new_run() (+29 more)

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

### Community 53 - "ReplayConfig"
Cohesion: 0.13
Nodes (31): SameTextLike, Replay-only settings., ReplayConfig, Replay: runs a capability saved by discovery with plain code, no LLM (step 4:…, fill(), Put inputs into `{{name}}`. `{{secret:x}}` stays as it is: secrets go in only…, anchor_point(), find_template() (+23 more)

### Community 54 - "Session"
Cohesion: 0.18
Nodes (17): BrowserContext, Playwright, Playwright, no decisions: the open session, the site lock, our own input,…, _alive(), check_viewport(), _extension(), handback_dir(), _launch() (+9 more)

### Community 55 - "RefCounter"
Cohesion: 0.09
Nodes (33): RapidOCR, draw_numbered(), number(), ocr(), ocr_engine(), NDArray, uint8, The shared RapidOCR engine, OCR itself, numbering and the numbered-box overlay.… (+25 more)

### Community 57 - "Look"
Cohesion: 0.08
Nodes (52): Cols, _columns(), clean_label(), column_header(), headings(), is_header(), is_word(), merged_label() (+44 more)

### Community 58 - "test_extension.py"
Cohesion: 0.19
Nodes (14): Control, Ext, asyncio, parametrize, The hand-back extension's toolbar button: its service worker only, never the…, The extension's service worker: a click counter and a badge., test_a_click_count_rise_returns(), test_a_missing_or_broken_extension_gives_none() (+6 more)

### Community 60 - "SendGuard"
Cohesion: 0.15
Nodes (9): is_sensitive(), pretty(), address.zipCode' -> 'Address zip code' (for the human; the key itself is kept)., Request, ``await guard(route)`` is the route handler. ``guard.lock`` is the send gate:…, Gate 1: Approve, or Edit = back to the form with every value, then again.…, RouteLike, SendGuard (+1 more)

### Community 63 - "Discovery decisions"
Cohesion: 0.08
Nodes (24): Base decisions, Cuts, Discovery decisions, Q10: window size and zoom — DECIDED, Q11: notebook format — DECIDED, Q12: dropdowns — DECIDED, Q13: scrolling — DECIDED, Q14: private data in saved pictures — DECIDED (+16 more)

### Community 64 - "2. Each box, with an example"
Cohesion: 0.12
Nodes (15): 1. Diagram, 2. Each box, with an example, 3. All tools, 4. Step by step: one discovery run, 5. Notes, Browser (Playwright), Control window and site lock (Q-A), Discovery architecture (+7 more)

### Community 66 - "ControlWindow"
Cohesion: 0.11
Nodes (19): base64, Question, ControlWindow, discovery_control(), _img(), Protocol, ControlWindow: our own "Agent control" tab, the only place a human answers.…, Answers the question on top. Closing the window (None) answers every one: fail… (+11 more)

### Community 67 - "2. Components"
Cohesion: 0.12
Nodes (15): 1. Diagram, 2. Components, 3. Step types, 4. Worked example: ParaBank login + read balance, 5. Notes, Actor, Artifact (made by discovery, not replay), Browser setup (+7 more)

### Community 69 - "Pure-Visual Discovery Notebook: Build Plan"
Cohesion: 0.09
Nodes (22): 10. Open risks, 1. Global constraints (every task must follow these), 2. Review focus (inputs no spec line covers, but likely to bite), 3. What already exists (reuse, or its visual version), 3a. How the agent is built today (`agent.ipynb` STEP 4, `src/cua/agent.py`), 3b. Existing handoff rules: when a human is called in, 3c. Existing tools → the new tools, 4. New dependencies (checked on PyPI, 2026-09-28) (+14 more)

### Community 71 - "SiteLock"
Cohesion: 0.16
Nodes (12): CdpSender, Protocol, SiteLock: the site tab ignores all real input (CDP…, The one method of a Playwright ``CDPSession`` the lock uses., The site tab ignores all real input (CDP). Lifted only around our own action or…, SiteLock, FakeCdp, asyncio (+4 more)

### Community 74 - "config.py"
Cohesion: 0.07
Nodes (37): dotenv, _find_root(), load_site(), OutcomeRule, _outcomes(), Path, Shared configuration: the site profile, browser/discovery/replay settings, and…, The nearest folder at or above `start` that has a ``configs/`` folder. (+29 more)

### Community 75 - "engine.py"
Cohesion: 0.14
Nodes (39): Drift, _cleanup_step(), error_page(), finish(), is_cleanup(), judge(), login_came_back(), login_steps() (+31 more)

### Community 76 - "loader.py"
Cohesion: 0.11
Nodes (22): Exception, re, ask_inputs(), ask_option(), _ask_rows(), given_inputs(), Ctx, Loading a saved capability (schema v2) and the inputs it needs. Moved unchanged… (+14 more)

### Community 77 - ".awrap_model_call"
Cohesion: 0.13
Nodes (13): Classifier, confidence_gate(), job_tool_names(), page_name(), AsyncHandler, ModelRequest, ModelResponse, Protocol (+5 more)

### Community 80 - "Box"
Cohesion: 0.09
Nodes (29): crop_box(), cut_crop(), Crops around one point: find the element there, crop around it, read text near…, Crop around the target, with every other piece of text blanked out., Pixels around the point changed. Catches password dots that OCR cannot read., spot_changed(), Box, decode() (+21 more)

### Community 81 - "test_session.py"
Cohesion: 0.24
Nodes (11): LivePage, _png(), asyncio, MonkeyPatch, Path, open_session reuses a live session (a notebook re-run must not leak a browser),…, _session(), test_a_live_existing_session_is_returned_unchanged() (+3 more)

### Community 82 - "test_prompt.py"
Cohesion: 0.12
Nodes (10): langgraph_checkpoint_memory, The discovery agent: system prompt, middleware, optional TypeSafe routing, and…, The discovery agent's system prompt, verbatim from…, _capture(), MonkeyPatch, build_agent: the notebook's create_deep_agent call, with routing appended only…, test_build_agent_wires_the_notebooks_agent(), test_routing_is_appended_after_the_notebooks_middleware() (+2 more)

### Community 85 - "build_tools"
Cohesion: 0.16
Nodes (16): AsyncFunctionDef, inspect, build_tools(), BaseTool, Ctx, observe, click, type_text, type_secret, select_option, scroll, open_path,…, test_the_prompt_lists_every_tool(), _notebook_tools() (+8 more)

### Community 86 - "cua"
Cohesion: 0.50
Nodes (3): cua, Read order, Rules

### Community 87 - "masked_outputs"
Cohesion: 0.40
Nodes (5): masked_outputs(), JsonValue, Names and shape only: a value is ***, a table keeps its rows and columns, every…, parametrize, test_masked_outputs_keep_the_shape()

### Community 88 - "cua.schema"
Cohesion: 0.50
Nodes (3): cua.schema, Read order, What may NOT go here

### Community 89 - "handoff/__init__.py"
Cohesion: 0.17
Nodes (18): _in_control(), The take-over itself: badge YOU, unlock the site, wait for Done (panel or…, _takeover_note(), Answerable, button_clicked(), ext_call(), Extension, handback_button() (+10 more)

### Community 90 - "load"
Cohesion: 0.17
Nodes (17): dropdown_options(), mismatches(), _norm_num(), Dropdown, Values a send carries that the human never gave, and the dropdown choices to…, Numbers being sent that the human never gave, e.g. account 1450 vs 1400. Only…, For each key: the options of the page dropdown whose CURRENT value is exactly…, load() (+9 more)

### Community 92 - "run_goal"
Cohesion: 0.17
Nodes (15): Agent, Ctx, Protocol, What run_goal needs of the compiled deep agent., New run on a fresh thread; pass an earlier thread_id to resume it with a next…, run_goal(), _start(), FakeAgent (+7 more)

### Community 93 - "test_human_tools.py"
Cohesion: 0.35
Nodes (13): _ctx(), asyncio, Ctx, MonkeyPatch, finish_business_outcome / request_missing_values / ask_human (the human-facing…, test_ask_human_asks_with_the_question(), test_finish_needs_the_proof_on_the_screen(), test_no_fields_given() (+5 more)

### Community 94 - "test_screenshot.py"
Cohesion: 0.27
Nodes (9): _png(), asyncio, MonkeyPatch, take_look: page calls on the loop, the CPU part (OCR, drawing, encoding) in one…, ShotPage, test_page_width_reads_the_window_width(), test_snap_look_gives_the_look_png_or_none_on_timeout(), test_snap_png_passes_the_timeout_and_gives_none_on_error() (+1 more)

### Community 96 - "test_routing.py"
Cohesion: 0.19
Nodes (17): Classifies the step's job with TypeSafe's Choice primitive and narrows the tool…, ToolRouter, _choice(), FakeClassifier, FakeRequest, _names(), asyncio, CaptureFixture (+9 more)

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
Cohesion: 0.14
Nodes (34): BaseModel, model_validator, _navigate(), Step, Event log -> ``Capability``: steps, inputs, outputs and secrets come from the…, ``to_step``'s open_path branch, unchanged., The {{input}} names the steps use, in order. {{secret:x}} is not an input., step_inputs() (+26 more)

### Community 107 - "_FakeModel"
Cohesion: 0.22
Nodes (5): _FakeModel, asyncio, Stands in for a LangChain chat model: no network, records the prompt., _Structured, test_describe_asks_the_given_model_with_labels_and_input_names_only()

### Community 109 - "test_evidence.py"
Cohesion: 0.26
Nodes (16): _artifact(), masked(), fixture, MonkeyPatch, Path, save_evidence: one masked folder per run. No run value or secret is ever…, The OCR mask is tested in tests/unit/safety; here: that every PNG goes through…, _save() (+8 more)

### Community 110 - "make_ctx"
Cohesion: 0.16
Nodes (28): make_ctx(), Ctx, Session, A discovery ``Ctx`` over fakes, built like ``attach`` but with no page wiring., helped(), asyncio, fixture, MonkeyPatch (+20 more)

### Community 112 - "test_replay_evidence.py"
Cohesion: 0.30
Nodes (17): _all_text(), fake_ocr(), _png(), Ctx, fixture, Path, save_evidence writes one masked folder per run: summary, drift, failure (only…, A capability on disk, a fake OCR that reads the value, and the last run's mask… (+9 more)

### Community 113 - "Replay notebook plan"
Cohesion: 0.33
Nodes (5): Decisions made here (review), Open questions for the user, Replay notebook plan, Sections, Tasks

### Community 114 - "Ctx"
Cohesion: 0.07
Nodes (57): act(), canvas(), choose_option(), _count_start(), crop(), Ctx, into_box(), list_options() (+49 more)

### Community 117 - "test_dropdowns.py"
Cohesion: 0.15
Nodes (20): _approve(), HeldPage, _logged(), _no_crop_pixels(), asyncio, Ctx, fixture, MonkeyPatch (+12 more)

### Community 118 - "load_capability"
Cohesion: 0.13
Nodes (27): load_capability(), load_outcomes(), _missing_crops(), Path, The capability and the folder its crop paths are relative to., The capability's own `outcomes:` [{text, status, meaning}], else the site's…, Path, Discovery's saved artifact runs in replay unchanged: build -> save -> load ->… (+19 more)

### Community 120 - "replay/evidence.py"
Cohesion: 0.10
Nodes (32): _clean(), config_hash(), git_sha(), _png(), JsonValue, OcrFn, Path, Redact (+24 more)

### Community 121 - "locate"
Cohesion: 0.21
Nodes (22): locate(), Path, Target, (point, rung) from the first rung that hits, or None., Anchor, _dup_target(), _look(), Path (+14 more)

### Community 123 - "discovery/evidence.py"
Cohesion: 0.23
Nodes (15): _copy_capability(), _events(), _folder(), Ctx, OcrFn, Path, Redact, One masked folder per discovery run: goal, answer, events, transcript, crops,… (+7 more)

### Community 125 - "routing.py"
Cohesion: 0.14
Nodes (20): ModelKind, ModuleType, os, build_routing_middleware(), _model_router(), AgentMiddleware, TypeSafe tool selection + model routing, restored (user, 2026-10-01;…, Haiku for a simple step, Sonnet otherwise (both through cua.llm). (+12 more)

### Community 128 - "save_artifact"
Cohesion: 0.29
Nodes (7): Path, save_artifact(), fixture, MonkeyPatch, saved(), Path, test_the_select_step_keeps_the_dropdowns_index()

### Community 130 - "ReplayResult"
Cohesion: 0.21
Nodes (8): ReplayResult, test_partial_label_when_not_success(), ReplayResult summary/outputs_line, Stop, and the Status values., test_partial_outputs_line_when_not_success(), test_result_defaults(), test_stop_carries_its_fields(), test_success_outputs_line(), test_summary_names_the_human_steps()

### Community 131 - "replay/wiring.py"
Cohesion: 0.13
Nodes (16): attach(), _expose(), note_response(), Ctx, Protocol, Session, Page wiring for replay: :func:`attach` (the notebook's setup cell, replay.py…, Evidence screenshot. A held form POST blocks `page.screenshot()`: give up,… (+8 more)

### Community 132 - "test_middleware.py"
Cohesion: 0.29
Nodes (9): asyncio, SimpleNamespace, LatestScreenshotOnly keeps only the newest image in the model's context; the…, _req(), _shot(), test_async_call_trims_too(), test_noop_caching_passes_the_request_through(), test_only_last_image_survives() (+1 more)

### Community 134 - "replay/context.py"
Cohesion: 0.09
Nodes (23): pydantic, Ctx, note_takeover_send(), Page, Request, Ctx: what every replay function takes first (session, run, settings, send…, R7: nothing kept. A fresh run, and the guard reads that one from now on., wipe() (+15 more)

### Community 141 - "cua.discovery.agent"
Cohesion: 0.50
Nodes (3): cua.discovery.agent, Read order, What may NOT go here

### Community 149 - "pytest"
Cohesion: 0.09
Nodes (23): pytest, _fake_llm_keys(), fixture, MonkeyPatch, Suite-wide: never let a real LLM key from `.env` reach a test (cua.config loads…, A fake Iliad key so code that builds a chat model works offline; no real key is…, MonkeyPatch, parametrize (+15 more)

## Knowledge Gaps
- **159 isolated node(s):** `MODES`, `manifest_version`, `name`, `version`, `description` (+154 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **13 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Look` connect `Look` to `fakes.py`, `replay/wiring.py`, `test_act.py`, `vision/__init__.py`, `BrowserConfig`, `act.py`, `test_dropdown.py`, `discovery/run.py`, `test_replay_rescue.py`, `steps.py`, `mk_look`, `make_replay_ctx`, `test_replay_steps.py`, `input.py`, `test_read_helpers.py`, `IndexPage`, `human.py`, `FakeTab`, `discovery/wiring.py`, `ReplayConfig`, `RefCounter`, `Box`, `test_screenshot.py`, `test_human.py`, `Ctx`, `test_dropdowns.py`, `load_capability`, `locate`?**
  _High betweenness centrality (0.100) - this node is a cross-community bridge._
- **Why does `Ctx` connect `Ctx` to `fakes.py`, `replay/wiring.py`, `test_act.py`, `agent/build.py`, `replay/context.py`, `test_replay_inputs.py`, `act.py`, `discovery/run.py`, `test_replay_rescue.py`, `test_replay_handback.py`, `test_replay_wiring.py`, `test_replay_table.py`, `mk_look`, `test_replay_steps.py`, `human.py`, `FakeTab`, `discovery/wiring.py`, `Session`, `Look`, `config.py`, `run_goal`, `test_human.py`, `test_dropdowns.py`, `discovery/evidence.py`?**
  _High betweenness centrality (0.059) - this node is a cross-community bridge._
- **Why does `BrowserConfig` connect `BrowserConfig` to `cli.py`, `fakes.py`, `replay/context.py`, `test_dropdown.py`, `pytest`, `test_replay_handback.py`, `mk_look`, `make_replay_ctx`, `test_replay_steps.py`, `input.py`, `IndexPage`, `FakeTab`, `discovery/wiring.py`, `test_takeover_loop.py`, `Session`, `RefCounter`, `test_extension.py`, `config.py`, `loader.py`, `Box`, `test_session.py`, `handoff/__init__.py`, `test_screenshot.py`, `Ctx`, `load_capability`, `replay/evidence.py`?**
  _High betweenness centrality (0.055) - this node is a cross-community bridge._
- **Are the 26 inferred relationships involving `Look` (e.g. with `Ctx` and `DiscoveryRun`) actually correct?**
  _`Look` has 26 INFERRED edges - model-reasoned connections that need verification._
- **Are the 35 inferred relationships involving `BrowserConfig` (e.g. with `Session` and `Answerable`) actually correct?**
  _`BrowserConfig` has 35 INFERRED edges - model-reasoned connections that need verification._
- **Are the 53 inferred relationships involving `Ctx` (e.g. with `Session` and `DiscoveryConfig`) actually correct?**
  _`Ctx` has 53 INFERRED edges - model-reasoned connections that need verification._
- **Are the 29 inferred relationships involving `ReplayConfig` (e.g. with `Ctx` and `_Request`) actually correct?**
  _`ReplayConfig` has 29 INFERRED edges - model-reasoned connections that need verification._