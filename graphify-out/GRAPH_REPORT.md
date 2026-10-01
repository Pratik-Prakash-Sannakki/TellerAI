# Graph Report - BankerAgent  (2026-10-01)

## Corpus Check
- 218 files · ~283,138 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 3040 nodes · 8162 edges · 147 communities (129 shown, 18 thin omitted)
- Extraction: 95% EXTRACTED · 5% INFERRED · 0% AMBIGUOUS · INFERRED: 370 edges (avg confidence: 0.55)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `fbb77f10`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- argparse
- FakeRoute
- Productionize Plan: notebooks → `src/cua/` package
- test_act.py
- Evidence README
- agent/build.py
- table.py
- test_replay_inputs.py
- test_input.py
- Look
- test_dropdown.py
- save_discovery_evidence / save_replay_evidence (D92)
- Replay decisions
- Five Error Demos (D30)
- langchain_typesafe
- langchain_typesafe_experimental_middleware
- discovery/run.py
- test_recorder_reads.py
- test_replay_engine.py
- test_replay_rescue.py
- test_llm.py
- test_replay_handback.py
- test_read.py
- safety/__init__.py
- test_replay_wiring.py
- recorder/__init__.py
- steps.py
- json
- integration/conftest.py
- discovery.py
- test_replay_table.py
- redact.py
- walk
- _meta
- make_replay_ctx
- Look
- CLAUDE.md (project instructions)
- test_replay_steps.py
- tool
- manifest.json
- Capability
- test_recorder_runs.py
- replay.py
- nav.py
- handback_button
- human.py
- FakeTab
- DiscoveryConfig
- take_look
- test_send_guard.py
- test_control_window.py
- cua.vision
- test_takeover_loop.py
- ReplayConfig
- discovery/context.py
- vision/__init__.py
- LatestScreenshotOnly
- read.py
- test_extension.py
- Ctx
- SendGuard
- langgraph_types
- rescue.py
- Discovery decisions
- 2. Each box, with an example
- Look
- ControlWindow
- 2. Components
- ControlWindow
- Pure-Visual Discovery Notebook: Build Plan
- SiteLock
- SiteLock
- test_table.py
- guard_send
- SiteProfile
- engine.py
- loader.py
- routing.py
- norm
- ext_call
- decode
- test_session.py
- test_prompt.py
- copy
- crops.py
- build_tools
- cua
- pathlib
- cua.schema
- handoff/__init__.py
- load
- save.py
- run_goal
- test_human_tools.py
- test_screenshot.py
- take_look
- test_routing.py
- result.py
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
- ControlWindow
- test_evidence.py
- make_ctx
- pytest
- test_replay_evidence.py
- Replay notebook plan
- act.py
- yaml
- SiteLock
- test_dropdowns.py
- test_loader.py
- read_helpers.py
- test_shared_evidence.py
- test_locate.py
- .get
- discovery/evidence.py
- FakeWin
- llm.py
- background.js
- do_extract_table
- BrowserConfig
- is_word
- test_result.py
- Response
- test_middleware.py
- build_capability
- Ctx
- Box
- locate
- _noop_click
- _select
- input_name
- test_spot_changed.py
- cua.discovery.agent
- value_in_box
- failed.py
- .findable
- _EventBase
- test_capability.py

## God Nodes (most connected - your core abstractions)
1. `Ctx` - 80 edges
2. `BrowserConfig` - 78 edges
3. `make_ctx()` - 78 edges
4. `ReplayConfig` - 65 edges
5. `make_replay_ctx()` - 60 edges
6. `Look` - 58 edges
7. `_meta()` - 53 edges
8. `Session` - 45 edges
9. `SiteProfile` - 44 edges
10. `Box` - 44 edges

## Surprising Connections (you probably didn't know these)
- `make_observe_tools()` --indirect_call--> `observe()`  [INFERRED]
  src/cua/discovery/tools/observe.py → notebooks/discovery/discovery.py
- `Driven` --indirect_call--> `observe()`  [INFERRED]
  tests/unit/discovery/tools/test_act.py → notebooks/discovery/discovery.py
- `_make_type_text()` --indirect_call--> `type_text()`  [INFERRED]
  src/cua/discovery/tools/act.py → notebooks/discovery/discovery.py
- `_make_type_secret()` --indirect_call--> `type_secret()`  [INFERRED]
  src/cua/discovery/tools/act.py → notebooks/discovery/discovery.py
- `_make_select_option()` --indirect_call--> `select_option()`  [INFERRED]
  src/cua/discovery/tools/act.py → notebooks/discovery/discovery.py

## Import Cycles
- 3-file cycle: `src/cua/discovery/tools/__init__.py -> src/cua/discovery/tools/act.py -> src/cua/discovery/tools/guard.py -> src/cua/discovery/tools/__init__.py`
- 3-file cycle: `src/cua/discovery/tools/__init__.py -> src/cua/discovery/tools/act.py -> src/cua/discovery/tools/observe.py -> src/cua/discovery/tools/__init__.py`
- 3-file cycle: `src/cua/discovery/tools/__init__.py -> src/cua/discovery/tools/read.py -> src/cua/discovery/tools/guard.py -> src/cua/discovery/tools/__init__.py`
- 3-file cycle: `src/cua/discovery/tools/__init__.py -> src/cua/discovery/tools/human.py -> src/cua/discovery/tools/observe.py -> src/cua/discovery/tools/__init__.py`
- 3-file cycle: `src/cua/discovery/tools/guard.py -> src/cua/discovery/tools/human.py -> src/cua/discovery/tools/observe.py -> src/cua/discovery/tools/guard.py`
- 3-file cycle: `src/cua/discovery/tools/__init__.py -> src/cua/discovery/tools/nav.py -> src/cua/discovery/tools/observe.py -> src/cua/discovery/tools/__init__.py`
- 3-file cycle: `src/cua/discovery/tools/__init__.py -> src/cua/discovery/tools/nav.py -> src/cua/discovery/tools/guard.py -> src/cua/discovery/tools/__init__.py`
- 4-file cycle: `src/cua/discovery/tools/__init__.py -> src/cua/discovery/tools/act.py -> src/cua/discovery/tools/human.py -> src/cua/discovery/tools/observe.py -> src/cua/discovery/tools/__init__.py`
- 4-file cycle: `src/cua/discovery/tools/__init__.py -> src/cua/discovery/tools/act.py -> src/cua/discovery/tools/observe.py -> src/cua/discovery/tools/guard.py -> src/cua/discovery/tools/__init__.py`
- 4-file cycle: `src/cua/discovery/tools/__init__.py -> src/cua/discovery/tools/human.py -> src/cua/discovery/tools/observe.py -> src/cua/discovery/tools/guard.py -> src/cua/discovery/tools/__init__.py`
- 4-file cycle: `src/cua/discovery/tools/__init__.py -> src/cua/discovery/tools/nav.py -> src/cua/discovery/tools/observe.py -> src/cua/discovery/tools/guard.py -> src/cua/discovery/tools/__init__.py`
- 5-file cycle: `src/cua/discovery/tools/__init__.py -> src/cua/discovery/tools/act.py -> src/cua/discovery/tools/guard.py -> src/cua/discovery/tools/human.py -> src/cua/discovery/tools/observe.py -> src/cua/discovery/tools/__init__.py`
- 5-file cycle: `src/cua/discovery/tools/__init__.py -> src/cua/discovery/tools/act.py -> src/cua/discovery/tools/human.py -> src/cua/discovery/tools/observe.py -> src/cua/discovery/tools/guard.py -> src/cua/discovery/tools/__init__.py`
- 5-file cycle: `src/cua/discovery/tools/__init__.py -> src/cua/discovery/tools/read.py -> src/cua/discovery/tools/guard.py -> src/cua/discovery/tools/human.py -> src/cua/discovery/tools/observe.py -> src/cua/discovery/tools/__init__.py`
- 5-file cycle: `src/cua/discovery/tools/__init__.py -> src/cua/discovery/tools/nav.py -> src/cua/discovery/tools/guard.py -> src/cua/discovery/tools/human.py -> src/cua/discovery/tools/observe.py -> src/cua/discovery/tools/__init__.py`

## Communities (147 total, 18 thin omitted)

### Community 1 - "FakeRoute"
Cohesion: 0.11
Nodes (11): FakeControl, FakePage, FakeRoute, A fake discovery/replay ``CONTROL`` surface (what ``ControlWindow`` presents).…, A fake ``playwright.async_api.Route``: records every…, A fake ``playwright.async_api.Page``. Every awaited method is recorded in…, asyncio, Tests for the shared offline fakes in tests/fakes.py (TDD: written before the… (+3 more)

### Community 2 - "Productionize Plan: notebooks → `src/cua/` package"
Cohesion: 0.12
Nodes (16): 10. Line-count offenders (today), 1. Package tree, 2. De-duplication (checked by AST diff of both notebooks), 3. State: globals → explicit objects, 4. Async and typing, 5. Notebooks after the move, 6. Tests, 7. ML-engineering practices (kept small) (+8 more)

### Community 3 - "test_act.py"
Cohesion: 0.15
Nodes (40): make_look(), Look, A look whose elements are numbered 1.. in order (ref, text, box)., Driven, _head(), _helped(), _logged_arg_keys(), asyncio (+32 more)

### Community 5 - "agent/build.py"
Cohesion: 0.13
Nodes (19): CompiledStateGraph, deepagents, Handler, langchain_agents_middleware, build_agent(), BaseChatModel, Ctx, build_agent: the notebook's ``AGENT = create_deep_agent(...)`` (discovery.py… (+11 more)

### Community 6 - "table.py"
Cohesion: 0.13
Nodes (24): append_rows(), cell_shape(), col_of(), column_spans(), like_rows(), Box, Element, Look (+16 more)

### Community 7 - "test_replay_inputs.py"
Cohesion: 0.13
Nodes (30): select(), type_(), _cap(), ClearPage, env(), FakeForm, FakePage, asyncio (+22 more)

### Community 8 - "test_input.py"
Cohesion: 0.09
Nodes (28): act(), into_box(), Lock, Look, Page, Step, The response to a send lands after the human's approval, not after the click:…, Unlock the site tab, run our own input steps, relock, settle, take a new look. (+20 more)

### Community 9 - "Look"
Cohesion: 0.07
Nodes (30): Box, Element, Look, ActTab, FakeInput, FakeLock, Shared offline fakes for the ported test suite (tests/unit, tests/integration).…, A fake ``cua.browser.SiteLock``: ``open()`` records unlock/lock, nothing else. (+22 more)

### Community 10 - "test_dropdown.py"
Cohesion: 0.07
Nodes (37): BaseException, Confirm, LookFn, choose_option_at_index(), choose_option_at_point(), list_options(), Page, Every option of the dropdown at this page point ([] if it is not a dropdown).… (+29 more)

### Community 12 - "Replay decisions"
Cohesion: 0.08
Nodes (23): R10: where the compile step lives — DECIDED, R11: why compile, if `response_format` exists? — PROPOSED, R12: what each step type compiles to — PROPOSED, R13: target schema — PROPOSED, R14: what rung 2 needs that discovery doesn't record — DONE, R15: auto-approve at replay — PROPOSED, R16: dead ends and retries at compile — PROPOSED, R17: replay result statuses — PROPOSED (+15 more)

### Community 16 - "discovery/run.py"
Cohesion: 0.10
Nodes (22): Saved, The current run (the one the send guard serves)., run_goal: one goal through the discovery agent (moved from discovery.py…, DiscoveryRun, DiscoveryRun: one discovery run's working state (was the notebook's…, What the human gave: the goal and every answer (the send guard's mismatch text)., Every saved text, table cells included (evidence masking only)., Banking: values live only for the run. Keep the log (labels only), drop the… (+14 more)

### Community 17 - "test_recorder_reads.py"
Cohesion: 0.12
Nodes (25): asyncio, parametrize, What the tools log, compiled: read-only runs, tables, labels joined to values,…, An event with no page_texts (an older log) proves nothing: the proof is kept., A box's own text with nothing cut from it (a value, a button) stays off the…, _read_log(), _table_ev(), test_a_box_border_read_as_a_bracket_is_not_part_of_the_label() (+17 more)

### Community 18 - "test_replay_engine.py"
Cohesion: 0.15
Nodes (51): cap(), click(), extract(), Capability, AskStop, clean(), ectx(), _finish() (+43 more)

### Community 19 - "test_replay_rescue.py"
Cohesion: 0.06
Nodes (44): The guard keeps its own reference to the control window: swap both., set_control(), DoneWhileSending, _env(), _fail_clicks(), FormRoute, Frame, GateControl (+36 more)

### Community 20 - "test_llm.py"
Cohesion: 0.15
Nodes (14): cua: shared config and the LLM model factory (Iliad gateway) for the pure-…, _clean_env(), CaptureFixture, fixture, MonkeyPatch, Offline tests for `cua.llm.make_chat_model` (Iliad gateway). No network, no…, test_ca_bundle_passthrough(), test_existing_ssl_cert_file_wins() (+6 more)

### Community 21 - "test_replay_handback.py"
Cohesion: 0.13
Nodes (22): FakePage, _bctx(), Ext, Human, PanelDone, asyncio, Ctx, parametrize (+14 more)

### Community 22 - "test_read.py"
Cohesion: 0.11
Nodes (32): Items, _cell(), _no_crop_pixels(), asyncio, Ctx, fixture, MonkeyPatch, extract_value / extract_table: the agent points at a box or a header, our code… (+24 more)

### Community 23 - "safety/__init__.py"
Cohesion: 0.10
Nodes (23): JsonObj, Safety: what may leave the tab (hosts, the two send gates) and keeping values…, _flat(), _json(), Protocol, What a held request sends, and the same request rebuilt with edited values.…, The fields of a ``playwright.async_api.Request`` the guard reads., Every value a request sends, from its query, a form body, or a JSON body… (+15 more)

### Community 24 - "test_replay_wiring.py"
Cohesion: 0.09
Nodes (19): Working values for one run. Replaced by a new one in ``replay``'s ``finally``…, What the mismatch check compares a send against (SendState)., ReplayRun, attach(), Wire replay onto an open session and return its Ctx., Path, write_cap(), asyncio (+11 more)

### Community 25 - "recorder/__init__.py"
Cohesion: 0.16
Nodes (28): field_area(), goes_to_a_page(), is_select(), mark_submits(), needed_moves(), no_op(), one_read_per_table(), Event-log filters: which logged tool calls become steps (R16), plus the… (+20 more)

### Community 26 - "steps.py"
Cohesion: 0.09
Nodes (55): Point, fill(), Put inputs into `{{name}}`. `{{secret:x}}` stays as it is: secrets go in only…, changed(), choose_option(), do_click(), do_extract(), do_extract_table() (+47 more)

### Community 27 - "json"
Cohesion: 0.16
Nodes (11): AST, json, The hand-back extension never touches any site: no content scripts, no host…, Exec chosen top-level defs of a notebook (the old ast-exec pattern) for parity…, parametrize, Path, cua.schema.value_types matches both notebooks' SHAPES/TYPES exactly., SHAPES and TYPES as each notebook defines them (TYPES spreads SHAPES, so exec… (+3 more)

### Community 29 - "discovery.py"
Cohesion: 0.06
Nodes (56): langchain_tools, after_login_click(), Anchor, append_rows(), build_capability(), Capability, CapabilityMeta, checkpoint() (+48 more)

### Community 30 - "test_replay_table.py"
Cohesion: 0.19
Nodes (18): _cap(), _defs(), Page, asyncio, Capability, Ctx, MonkeyPatch, Path (+10 more)

### Community 31 - "redact.py"
Cohesion: 0.09
Nodes (33): Pattern, re, mask_png(), _num(), OcrFn, Value masking: ``norm``, ``is_sensitive``, ``hide_secrets``, ``redactor``,…, text -> text with every value masked. Numbers match however they are written…, Black out every OCR box whose text holds a run value. A clean image is written… (+25 more)

### Community 32 - "walk"
Cohesion: 0.09
Nodes (30): ask_inputs(), _clean(), finish(), is_cleanup(), load_outcomes(), masked_outputs(), _png(), Path (+22 more)

### Community 33 - "_meta"
Cohesion: 0.13
Nodes (30): _ev(), _meta(), Path, The recorder: the event log becomes a replay-ready capability (R12, R13, R16).…, Invented inputs are ignored, a missing description gets a default, secrets stay…, User decision 6: artifacts/<name>.yaml + artifacts/crops/<name>/ (was…, Banking safety (user, 2026-09-29): replay ends logged out., test_it_saves_as_an_anchored_extract_on_the_balance_header() (+22 more)

### Community 34 - "make_replay_ctx"
Cohesion: 0.13
Nodes (31): FakeLock, make_replay_ctx(), Ctx, Look, Replay test helpers: ``make_replay_ctx`` (a real Ctx on fakes), ``mk_look``,…, SiteLock stand-in: open() unlocks for the block., A real Ctx (real SendGuard, real ReplayRun) over a fake page/control/lock.…, ``take_look`` always returns this look. (+23 more)

### Community 35 - "Look"
Cohesion: 0.08
Nodes (34): anchor_point(), Box, canvas(), col_of(), column_spans(), crop_box(), Element, element_at() (+26 more)

### Community 36 - "CLAUDE.md (project instructions)"
Cohesion: 0.12
Nodes (19): CLAUDE.md (project instructions), D101: labeled_value refuses a table-header resolution (general fix), D102: label_header/value_header flags ported into agent.py + cli.py capture path, D92: Evidence Capture Helpers (save_discovery_evidence/save_replay_evidence), D93: Pre-existing 02_artifact_schema.py IndexError bug, D95: Missing create_deep_agent import found live in BROWSER 12, D96: build_agent() goal_text vs given_text field-name bug, D97: cua replay --login flag + repeated Balance header trap (+11 more)

### Community 37 - "test_replay_steps.py"
Cohesion: 0.08
Nodes (41): mk_look(), navigate(), _click_env(), _form_png(), GotoPage, _judge(), Page, asyncio (+33 more)

### Community 38 - "tool"
Cohesion: 0.07
Nodes (61): ask_human(), blocks(), canvas(), choose_option(), click(), cut_crop(), element_at(), extract_value() (+53 more)

### Community 39 - "manifest.json"
Cohesion: 0.11
Nodes (18): action, default_icon, default_title, background, service_worker, 128, 16, 32 (+10 more)

### Community 40 - "Capability"
Cohesion: 0.09
Nodes (41): act(), ask_option(), choose_option(), do_click(), do_extract(), do_navigate(), do_scroll(), do_select() (+33 more)

### Community 41 - "test_recorder_runs.py"
Cohesion: 0.14
Nodes (20): _click(), _go(), _names(), _nav(), _paths(), Recorder behaviour pinned by live runs: detours, 404s, login clicks kept, no-op…, test_a_404_and_detour_navigations_are_dropped(), test_a_click_that_stays_on_the_page_is_never_a_detour() (+12 more)

### Community 42 - "replay.py"
Cohesion: 0.07
Nodes (43): base64, dotenv, cell_shape(), Config, discovery_schema(), dropdown_options(), _flat(), guard_send() (+35 more)

### Community 43 - "nav.py"
Cohesion: 0.17
Nodes (20): canvas(), look(), The only screenshot path; stores the look on the run., The size of the image the model is looking at right now., to_page(), log(), One event (the notebook's ``log(tool, args, result, point=None, crop=None,…, make_nav_tools() (+12 more)

### Community 44 - "handback_button"
Cohesion: 0.40
Nodes (6): button_clicked(), ext_call(), handback_button(), R19: one bounded call into the hand-back extension's service worker, never the…, Returns once the toolbar button's click count rises above where it was at the…, Badge YOU while the human is in control; yields the task a toolbar click…

### Community 45 - "human.py"
Cohesion: 0.13
Nodes (26): Field, choose_option(), list_options(), Every option of the dropdown at this point ([] if it is not a dropdown)., Select the first option containing this text in the dropdown at (or next to)…, _enter(), human_fills(), _in_control() (+18 more)

### Community 46 - "FakeTab"
Cohesion: 0.12
Nodes (3): FakeTab, SimpleNamespace, A fake site or control tab with the Playwright calls discovery's wiring and…

### Community 47 - "DiscoveryConfig"
Cohesion: 0.17
Nodes (28): DiscoveryConfig, Discovery-only settings., Discovery: an LLM agent learns a task once and the recorder saves it as a…, attach(), _count_nav(), new_run(), Ctx, A fresh run for this goal (run_goal's ``HANDOFF = HandoffState(goal=goal)``). (+20 more)

### Community 48 - "take_look"
Cohesion: 0.13
Nodes (21): act(), decode(), draw_numbered(), encode(), _img(), mask_png(), ocr(), page_width() (+13 more)

### Community 49 - "test_send_guard.py"
Cohesion: 0.16
Nodes (23): Side-specific steps, each at the exact point its notebook ran it. on_request:…, SendHooks, Control, _new(), _no_dropdowns(), _old(), _play(), parametrize (+15 more)

### Community 50 - "test_control_window.py"
Cohesion: 0.26
Nodes (23): Factory, SIDES, asyncio, ControlWindow, parametrize, ControlWindow: one class, both sides' behaviour. Ported from…, Discovery calls _front inside try (the question is removed on failure); replay…, Regression: a gate during a take-over must win, then hand the take-over back… (+15 more)

### Community 51 - "cua.vision"
Cohesion: 0.50
Nodes (3): cua.vision, Read order, What may NOT go here

### Community 52 - "test_takeover_loop.py"
Cohesion: 0.18
Nodes (19): replay_control(), takeover_text(), Ext, _modes(), asyncio, ControlWindow, Take-over pieces and their timing (review focus 1): Done in the panel vs the…, The human pressed Pay (send held, its gate on top of the take-over), then Done… (+11 more)

### Community 53 - "ReplayConfig"
Cohesion: 0.11
Nodes (36): Anchor, OcrText, SameTextLike, Replay-only settings., ReplayConfig, Replay: runs a capability saved by discovery with plain code, no LLM (step 4:…, anchor_point(), find_template() (+28 more)

### Community 54 - "discovery/context.py"
Cohesion: 0.11
Nodes (31): BrowserContext, dataclasses, Playwright, playwright_async_api, Dropdown, The page's dropdowns, read BEFORE an action (never while guard_send holds a…, read_dropdowns(), Playwright, no decisions: the open session, the site lock, our own input,… (+23 more)

### Community 55 - "vision/__init__.py"
Cohesion: 0.11
Nodes (27): functools, RapidOCR, Pixels -> text: screenshots, OCR, canvas math, crops, and the shared table…, draw_numbered(), number(), ocr(), ocr_engine(), Box (+19 more)

### Community 56 - "LatestScreenshotOnly"
Cohesion: 0.24
Nodes (5): LatestScreenshotOnly, NoopAnthropicPromptCachingMiddleware, AgentMiddleware, Disable prompt caching on the Iliad gateway; it rejects Anthropic cache markers., Old screenshots are stale (their numbers no longer work); send the model only…

### Community 57 - "read.py"
Cohesion: 0.16
Nodes (25): Cols, _columns(), headings(), is_header(), off_table(), page_texts(), The look's words, tallest text first (a page heading is its biggest text)., The words on a look (never a value: letters, no run value in them), to pick a… (+17 more)

### Community 58 - "test_extension.py"
Cohesion: 0.19
Nodes (14): Control, Ext, asyncio, parametrize, The hand-back extension's toolbar button: its service worker only, never the…, The extension's service worker: a click counter and a badge., test_a_click_count_rise_returns(), test_a_missing_or_broken_extension_gives_none() (+6 more)

### Community 59 - "Ctx"
Cohesion: 0.14
Nodes (17): crop(), Ctx, Element, Page, Crop around the target, every other text blanked (sized to the current canvas)., What a click aims at, worked out before it happens., _Target, log_sent_dropdowns() (+9 more)

### Community 60 - "SendGuard"
Cohesion: 0.17
Nodes (7): pretty(), address.zipCode' -> 'Address zip code' (for the human; the key itself is kept)., Request, ``await guard(route)`` is the route handler. ``guard.lock`` is the send gate:…, Gate 1: Approve, or Edit = back to the form with every value, then again.…, RouteLike, SendGuard

### Community 62 - "rescue.py"
Cohesion: 0.12
Nodes (19): Asker, hand_back(), Future, Lock, Protocol, The shared take-over loop pieces. Each side's own take-over stays with that…, Done on the toolbar button or in the take-over panel hands back. No reminders…, A send the human started is still held: its gate is on screen next; wait for… (+11 more)

### Community 63 - "Discovery decisions"
Cohesion: 0.08
Nodes (24): Base decisions, Cuts, Discovery decisions, Q10: window size and zoom — DECIDED, Q11: notebook format — DECIDED, Q12: dropdowns — DECIDED, Q13: scrolling — DECIDED, Q14: private data in saved pictures — DECIDED (+16 more)

### Community 64 - "2. Each box, with an example"
Cohesion: 0.12
Nodes (15): 1. Diagram, 2. Each box, with an example, 3. All tools, 4. Step by step: one discovery run, 5. Notes, Browser (Playwright), Control window and site lock (Q-A), Discovery architecture (+7 more)

### Community 65 - "Look"
Cohesion: 0.10
Nodes (39): clean_label(), column_header(), column_spans(), Element, extract_table(), headings(), is_header(), is_word() (+31 more)

### Community 66 - "ControlWindow"
Cohesion: 0.11
Nodes (18): Question, ControlWindow, discovery_control(), _img(), Protocol, ControlWindow: our own "Agent control" tab, the only place a human answers.…, Answers the question on top. Closing the window (None) answers every one: fail…, Answers the newest open question of this mode, wherever it sits on the stack. (+10 more)

### Community 67 - "2. Components"
Cohesion: 0.12
Nodes (15): 1. Diagram, 2. Components, 3. Step types, 4. Worked example: ParaBank login + read balance, 5. Notes, Actor, Artifact (made by discovery, not replay), Browser setup (+7 more)

### Community 68 - "ControlWindow"
Cohesion: 0.17
Nodes (8): ControlWindow, Our own page: the only place a human answers. Closing it fails closed (None)., Answers the question on top. Closing the window (None) answers every one: fail…, Answers the newest open question of this mode, wherever it sits on the stack., A new question supersedes the one on screen (e.g. a gate during a take-over);…, One labelled input per field (label, masked), optionally prefilled. A dropdown…, A dropdown becomes a real <select> of its options; anything else a…, _row()

### Community 69 - "Pure-Visual Discovery Notebook: Build Plan"
Cohesion: 0.09
Nodes (22): 10. Open risks, 1. Global constraints (every task must follow these), 2. Review focus (inputs no spec line covers, but likely to bite), 3. What already exists (reuse, or its visual version), 3a. How the agent is built today (`agent.ipynb` STEP 4, `src/cua/agent.py`), 3b. Existing handoff rules: when a human is called in, 3c. Existing tools → the new tools, 4. New dependencies (checked on PyPI, 2026-09-28) (+14 more)

### Community 71 - "SiteLock"
Cohesion: 0.16
Nodes (12): CdpSender, Protocol, SiteLock: the site tab ignores all real input (CDP…, The one method of a Playwright ``CDPSession`` the lock uses., The site tab ignores all real input (CDP). Lifted only around our own action or…, SiteLock, FakeCdp, asyncio (+4 more)

### Community 72 - "test_table.py"
Cohesion: 0.19
Nodes (14): _defs(), _is_header(), _look(), Path, The shared OCR table reader: parity between cua.vision.table and both…, ast.dump compare, ignoring docstrings -- the functions this step did not have…, tests/replay/test_table_replay.py's own SHARED set is the contract this module…, _read() (+6 more)

### Community 73 - "guard_send"
Cohesion: 0.16
Nodes (16): dropdown_options(), _flat(), guard_send(), hide_secrets(), is_sensitive(), _json(), mismatches(), pretty() (+8 more)

### Community 74 - "SiteProfile"
Cohesion: 0.06
Nodes (40): _find_root(), load_site(), OutcomeRule, _outcomes(), Path, The nearest folder at or above `start` that has a ``configs/`` folder., Read and validate ``configs/<name>.yaml`` (root defaults to the repo root)., Look up a secret by NAME. Raises on an unknown name or an empty/missing value.… (+32 more)

### Community 75 - "engine.py"
Cohesion: 0.13
Nodes (41): Drift, _cleanup_step(), error_page(), finish(), is_cleanup(), judge(), login_came_back(), login_steps() (+33 more)

### Community 76 - "loader.py"
Cohesion: 0.14
Nodes (23): ask_inputs(), ask_option(), _ask_rows(), given_inputs(), load_capability(), load_outcomes(), _missing_crops(), Capability (+15 more)

### Community 77 - "routing.py"
Cohesion: 0.11
Nodes (23): ModuleType, build_routing_middleware(), Classifier, confidence_gate(), job_tool_names(), _model_router(), page_name(), AgentMiddleware (+15 more)

### Community 78 - "norm"
Cohesion: 0.14
Nodes (26): act(), _count_start(), into_box(), Look, Step, Unlock the site tab, run our own input steps, relock, settle, take a new look., Click the box, clear what is in it, type. Retries replace instead of doubling…, The start event's look bookkeeping: the page a run begins on, and how often… (+18 more)

### Community 79 - "ext_call"
Cohesion: 0.50
Nodes (4): ext_call(), Q16: one bounded call into the hand-back extension's service worker, never the…, Hands back once the toolbar button's click count rises above where it was at…, watch_button()

### Community 80 - "decode"
Cohesion: 0.08
Nodes (36): An evidence screenshot: short timeout, None on failure (never hangs on a held…, snap(), canvas_size(), Look, NDArray, uint8, Canvas-pixel <-> page-point mapping: any window size or pixel density maps to…, Fit the screenshot inside the canvas. Returns it and canvas-pixel -> page-point… (+28 more)

### Community 81 - "test_session.py"
Cohesion: 0.21
Nodes (13): check_viewport(), Q10: refuse rather than record a mismatch between the screenshot and the…, LivePage, _png(), asyncio, MonkeyPatch, Path, open_session reuses a live session (a notebook re-run must not leak a browser),… (+5 more)

### Community 82 - "test_prompt.py"
Cohesion: 0.12
Nodes (10): langgraph_checkpoint_memory, The discovery agent: system prompt, middleware, optional TypeSafe routing, and…, The discovery agent's system prompt, verbatim from…, _capture(), MonkeyPatch, build_agent: the notebook's create_deep_agent call, with routing appended only…, test_build_agent_wires_the_notebooks_agent(), test_routing_is_appended_after_the_notebooks_middleware() (+2 more)

### Community 84 - "crops.py"
Cohesion: 0.29
Nodes (11): crop_box(), cut_crop(), element_at(), Box, Element, Look, Crops around one point: find the element there, crop around it, read text near…, Crop around the target, with every other piece of text blanked out. (+3 more)

### Community 85 - "build_tools"
Cohesion: 0.16
Nodes (16): AsyncFunctionDef, inspect, build_tools(), BaseTool, Ctx, observe, click, type_text, type_secret, select_option, scroll, open_path,…, test_the_prompt_lists_every_tool(), _notebook_tools() (+8 more)

### Community 86 - "cua"
Cohesion: 0.50
Nodes (3): cua, Read order, Rules

### Community 87 - "pathlib"
Cohesion: 0.13
Nodes (24): pathlib, pydantic, _clean(), _png(), OcrFn, Path, Redact, Evidence helpers shared by discovery and replay: masking a JSON-able tree,… (+16 more)

### Community 88 - "cua.schema"
Cohesion: 0.50
Nodes (3): cua.schema, Read order, What may NOT go here

### Community 89 - "handoff/__init__.py"
Cohesion: 0.20
Nodes (15): Answerable, button_clicked(), ext_call(), Extension, handback_button(), Future, Protocol, The hand-back extension (the Chrome toolbar button): its service worker, never… (+7 more)

### Community 90 - "load"
Cohesion: 0.12
Nodes (22): dropdown_options(), mismatches(), _norm_num(), Dropdown, Values a send carries that the human never gave, and the dropdown choices to…, Numbers being sent that the human never gave, e.g. account 1450 vs 1400. Only…, For each key: the options of the page dropdown whose CURRENT value is exactly…, load() (+14 more)

### Community 91 - "save.py"
Cohesion: 0.17
Nodes (12): Step, The {{input}} names the steps use, in order. {{secret:x}} is not an input., step_inputs(), used_inputs(), describe(), BaseChatModel, Capability, CapabilityMeta (+4 more)

### Community 92 - "run_goal"
Cohesion: 0.17
Nodes (15): Agent, Ctx, Protocol, What run_goal needs of the compiled deep agent., New run on a fresh thread; pass an earlier thread_id to resume it with a next…, run_goal(), _start(), FakeAgent (+7 more)

### Community 93 - "test_human_tools.py"
Cohesion: 0.35
Nodes (13): _ctx(), asyncio, Ctx, MonkeyPatch, finish_business_outcome / request_missing_values / ask_human (the human-facing…, test_ask_human_asks_with_the_question(), test_finish_needs_the_proof_on_the_screen(), test_no_fields_given() (+5 more)

### Community 94 - "test_screenshot.py"
Cohesion: 0.27
Nodes (9): _png(), asyncio, MonkeyPatch, take_look: page calls on the loop, the CPU part (OCR, drawing, encoding) in one…, ShotPage, test_page_width_reads_the_window_width(), test_snap_look_gives_the_look_png_or_none_on_timeout(), test_snap_png_passes_the_timeout_and_gives_none_on_error() (+1 more)

### Community 95 - "take_look"
Cohesion: 0.21
Nodes (15): changed(), decode(), draw_numbered(), encode(), mask_png(), ocr(), page_width(), ndarray (+7 more)

### Community 96 - "test_routing.py"
Cohesion: 0.21
Nodes (15): _choice(), FakeClassifier, FakeRequest, _names(), asyncio, CaptureFixture, MonkeyPatch, SimpleNamespace (+7 more)

### Community 97 - "result.py"
Cohesion: 0.40
Nodes (4): What a replay run returns: its Status, the Stop that ends a run early, and…, R17 run statuses. A member is a plain str, so ``Status.SUCCESS == "SUCCESS"``., Status, StrEnum

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
Cohesion: 0.27
Nodes (23): Event log -> ``Capability``: steps, inputs, outputs and secrets come from the…, target(), to_step(), Anchor, Capability, CapabilityMeta, Click, Extract (+15 more)

### Community 107 - "_FakeModel"
Cohesion: 0.20
Nodes (6): _FakeModel, asyncio, CapabilityMeta, Stands in for a LangChain chat model: no network, records the prompt., _Structured, test_describe_asks_the_given_model_with_labels_and_input_names_only()

### Community 108 - "ControlWindow"
Cohesion: 0.33
Nodes (4): ControlWindow, _img(), Our own page: the only place a human answers. Closing it fails closed (None)., _row()

### Community 109 - "test_evidence.py"
Cohesion: 0.26
Nodes (16): _artifact(), masked(), fixture, MonkeyPatch, Path, save_evidence: one masked folder per run. No run value or secret is ever…, The OCR mask is tested in tests/unit/safety; here: that every PNG goes through…, _save() (+8 more)

### Community 110 - "make_ctx"
Cohesion: 0.16
Nodes (28): make_ctx(), Ctx, A discovery ``Ctx`` over fakes, built like ``attach`` but with no page wiring., helped(), asyncio, fixture, MonkeyPatch, Tool guards: the event log, the step budget, repeats, login tries, click gates,… (+20 more)

### Community 111 - "pytest"
Cohesion: 0.29
Nodes (6): pytest, _fake_llm_keys(), fixture, MonkeyPatch, Suite-wide: never let a real LLM key from `.env` reach a test (cua.config loads…, A fake Iliad key so code that builds a chat model works offline; no real key is…

### Community 112 - "test_replay_evidence.py"
Cohesion: 0.26
Nodes (19): _all_text(), fake_ocr(), _png(), Box, Ctx, fixture, Path, ReplayResult (+11 more)

### Community 113 - "Replay notebook plan"
Cohesion: 0.33
Nodes (5): Decisions made here (review), Open questions for the user, Replay notebook plan, Sections, Tasks

### Community 114 - "act.py"
Cohesion: 0.12
Nodes (35): P, make_act_tools(), _make_click(), _make_select_option(), _make_type_secret(), _make_type_text(), BaseTool, The tools that act on the page: click, type_text, type_secret, select_option.… (+27 more)

### Community 115 - "yaml"
Cohesion: 0.29
Nodes (5): parametrize, Path, Every capability discovery saved loads, and re-saves through save_artifact…, test_a_saved_artifact_round_trips(), yaml

### Community 117 - "test_dropdowns.py"
Cohesion: 0.15
Nodes (20): _approve(), HeldPage, _logged(), _no_crop_pixels(), asyncio, Ctx, fixture, MonkeyPatch (+12 more)

### Community 118 - "test_loader.py"
Cohesion: 0.16
Nodes (19): _cap_with_inputs(), Capability, fixture, MonkeyPatch, parametrize, Path, cua.replay.loader: loading a saved capability and the inputs it needs. Ported…, test_every_saved_artifact_loads_with_fake_secrets() (+11 more)

### Community 119 - "read_helpers.py"
Cohesion: 0.20
Nodes (21): clean_label(), column_header(), label_near(), merged_label(), Element, Look, Where a point is on a look, in words: labels, anchors, page texts. Pure (no…, The value's column, walked upwards while each text is within TABLE_GAP of the… (+13 more)

### Community 120 - "test_shared_evidence.py"
Cohesion: 0.16
Nodes (16): config_hash(), git_sha(), JsonValue, `git rev-parse HEAD`, or "unknown" (no git, not a repo, any failure)., sha256 of the repr of the frozen configs plus the site name., What ``run.json`` holds: prompt version, model, config hash, git sha. Never a…, run_info(), _body() (+8 more)

### Community 121 - "test_locate.py"
Cohesion: 0.24
Nodes (15): _dup_target(), _look(), Path, Target, cua.replay.locate: the 3 rungs + table cell; all miss -> None. Ported from…, test_a_single_text_match_is_rung1_as_before(), test_all_miss_is_none(), test_duplicate_text_picks_the_copy_nearest_the_anchor() (+7 more)

### Community 122 - ".get"
Cohesion: 0.10
Nodes (28): describe(), field_area(), goes_to_a_page(), is_select(), log_sent_dropdowns(), mark_submits(), needed_moves(), no_op() (+20 more)

### Community 123 - "discovery/evidence.py"
Cohesion: 0.23
Nodes (15): _copy_capability(), _events(), _folder(), Ctx, OcrFn, Path, Redact, One masked folder per discovery run: goal, answer, events, transcript, crops,… (+7 more)

### Community 125 - "llm.py"
Cohesion: 0.20
Nodes (12): ModelKind, os, make_chat_model(), model_name_for(), _note_fallback(), _pass_through_ca_bundle(), BaseChatModel, The one place that builds a chat model. Every LLM call in the project goes… (+4 more)

### Community 127 - "do_extract_table"
Cohesion: 0.12
Nodes (21): append_rows(), do_extract_table(), fill(), norm(), A scrolled second read repeats the rows still on screen: drop only that overlap., Find the header by its label (rung 2's matching), read the rows with…, Step i ended in a take-over, and the human went on to the final screen: the…, The option is in the box's OCR, even merged with its label ('to account… (+13 more)

### Community 128 - "BrowserConfig"
Cohesion: 0.24
Nodes (11): BrowserConfig, Settings shared by discovery and replay (the same page size at both, Q10)., fixture, MonkeyPatch, Path, Discovery's saved artifact runs in replay unchanged: build -> save -> load ->…, saved(), test_crop_paths_resolve_to_saved_files() (+3 more)

### Community 129 - "is_word"
Cohesion: 0.25
Nodes (10): is_word(), A header or row key: has a letter and holds no run value (an account number…, _look(), where / label_near / spot / page_texts: a point's label in words, never a…, Live bug: 'From account #' dropdown showing '74838' was saved as input…, Live bug: 'Sean' typed into Payee Name became the Address step's label and…, test_a_dropdowns_own_number_is_never_its_label(), test_a_typed_value_above_is_never_the_next_fields_label() (+2 more)

### Community 131 - "Response"
Cohesion: 0.22
Nodes (6): note_response(), Protocol, The Playwright ``Response`` fields note_response reads., Keep the main document's HTTP status (not sub-resources, not iframes)., _Request, Response

### Community 132 - "test_middleware.py"
Cohesion: 0.29
Nodes (9): asyncio, SimpleNamespace, LatestScreenshotOnly keeps only the newest image in the model's context; the…, _req(), _shot(), test_async_call_trims_too(), test_noop_caching_passes_the_request_through(), test_only_last_image_survives() (+1 more)

### Community 133 - "build_capability"
Cohesion: 0.18
Nodes (10): build_capability(), output(), Capability, CapabilityMeta, Steps, inputs and secrets come from the log only. The model's text cannot fail…, ``build_capability``'s refusals, unchanged: a leaked value, a blind dropdown,…, _refuse(), checkpoint() (+2 more)

### Community 134 - "Ctx"
Cohesion: 0.20
Nodes (6): Ctx, note_takeover_send(), Page, Request, R7: nothing kept. A fresh run, and the guard reads that one from now on., wipe()

### Community 135 - "Box"
Cohesion: 0.10
Nodes (20): Box, cell_shape(), col_of(), crop_box(), like_rows(), number(), The column the box overlaps most, or None when it overlaps none (outside the…, Texts grouped into lines, top to bottom. (+12 more)

### Community 136 - "locate"
Cohesion: 0.28
Nodes (9): find(), find_template(), locate(), next_rung(), Target, Where the rungs after `rung` point (e.g. the anchor after a wrong table cell),…, Centre of the one clear best match; two near-equal peaks count as a miss., (point, rung) from the first rung that hits, or None. (+1 more)

### Community 137 - "_noop_click"
Cohesion: 0.28
Nodes (9): _clicks(), _noop_click(), navigated: the page loaded (a link, even back to the same URL); new: new text…, After login the site is already on Accounts Overview; clicking it, scrolling,…, test_a_click_that_changes_the_screen_on_the_same_page_is_kept(), test_a_click_that_lands_on_the_page_it_left_is_dropped(), test_a_run_that_neither_reads_nor_sends_is_refused(), test_identical_consecutive_clicks_on_one_target_are_one() (+1 more)

### Community 138 - "_select"
Cohesion: 0.29
Nodes (7): Path, Live: steps 5-6 (agent, 'From account #[') and 7-8 (send, 'From account #')…, _select(), test_a_select_with_no_anchor_is_refused_not_saved(), test_the_agents_select_and_the_same_sent_dropdown_are_one_step(), test_the_select_step_keeps_the_dropdowns_index(), test_two_dropdowns_far_apart_with_one_label_stay_two_steps()

### Community 139 - "input_name"
Cohesion: 0.40
Nodes (5): _navigate(), ``to_step``'s open_path branch, unchanged., flag_leaks(), input_name(), Mark (never store) an event whose label, anchor, own text, hint or input name…

### Community 140 - "test_spot_changed.py"
Cohesion: 0.50
Nodes (4): _look(), ndarray, spot_changed: password dots are pixels, not OCR text. Ported from…, test_dots_count_as_change_and_blank_does_not()

### Community 141 - "cua.discovery.agent"
Cohesion: 0.50
Nodes (3): cua.discovery.agent, Read order, What may NOT go here

### Community 142 - "value_in_box"
Cohesion: 0.20
Nodes (9): (value, pattern) for an extract: the whole box when it is exactly the type,…, value_in_box(), Value types an extract may declare. Shared by discovery and replay (one table,…, True when the whole value is exactly that type (string, number, boolean, or a…, value_matches_type(), parametrize, test_a_box_without_the_shape_is_refused(), test_a_whole_box_type_takes_the_whole_box() (+1 more)

### Community 149 - "test_capability.py"
Cohesion: 0.23
Nodes (7): _data(), parametrize, Path, cua.schema.Capability loads every saved artifact and refuses an unknown schema…, test_a_wrong_schema_version_is_refused(), test_an_unknown_key_is_refused(), test_every_saved_artifact_loads()

## Knowledge Gaps
- **161 isolated node(s):** `MODES`, `manifest_version`, `name`, `version`, `description` (+156 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **18 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Ctx` connect `Ctx` to `FakeRoute`, `Response`, `test_act.py`, `agent/build.py`, `test_replay_inputs.py`, `Look`, `discovery/run.py`, `test_replay_engine.py`, `test_replay_rescue.py`, `test_replay_handback.py`, `test_replay_wiring.py`, `test_replay_table.py`, `make_replay_ctx`, `test_replay_steps.py`, `nav.py`, `human.py`, `FakeTab`, `DiscoveryConfig`, `discovery/context.py`, `read.py`, `rescue.py`, `SiteProfile`, `norm`, `decode`, `run_goal`, `test_human.py`, `act.py`, `test_dropdowns.py`, `discovery/evidence.py`?**
  _High betweenness centrality (0.046) - this node is a cross-community bridge._
- **Why does `ControlWindow` connect `ControlWindow` to `make_replay_ctx`, `Ctx`, `test_takeover_loop.py`, `discovery/context.py`, `handoff/__init__.py`, `FakeWin`?**
  _High betweenness centrality (0.025) - this node is a cross-community bridge._
- **Why does `BrowserConfig` connect `BrowserConfig` to `FakeRoute`, `Ctx`, `test_input.py`, `Look`, `test_dropdown.py`, `test_replay_handback.py`, `make_replay_ctx`, `test_replay_steps.py`, `nav.py`, `FakeTab`, `DiscoveryConfig`, `test_takeover_loop.py`, `discovery/context.py`, `test_extension.py`, `SiteProfile`, `loader.py`, `decode`, `test_session.py`, `crops.py`, `handoff/__init__.py`, `test_screenshot.py`, `test_shared_evidence.py`?**
  _High betweenness centrality (0.024) - this node is a cross-community bridge._
- **Are the 53 inferred relationships involving `Ctx` (e.g. with `Session` and `DiscoveryConfig`) actually correct?**
  _`Ctx` has 53 INFERRED edges - model-reasoned connections that need verification._
- **Are the 35 inferred relationships involving `BrowserConfig` (e.g. with `Session` and `Answerable`) actually correct?**
  _`BrowserConfig` has 35 INFERRED edges - model-reasoned connections that need verification._
- **Are the 29 inferred relationships involving `ReplayConfig` (e.g. with `Ctx` and `_Request`) actually correct?**
  _`ReplayConfig` has 29 INFERRED edges - model-reasoned connections that need verification._
- **What connects `MODES`, `manifest_version`, `name` to the rest of the system?**
  _161 weakly-connected nodes found - possible documentation gaps or missing edges._