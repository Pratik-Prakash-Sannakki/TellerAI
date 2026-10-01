# Graph Report - BankerAgent  (2026-10-01)

## Corpus Check
- 176 files · ~134,072 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 2702 nodes · 7751 edges · 110 communities (96 shown, 14 thin omitted)
- Extraction: 93% EXTRACTED · 7% INFERRED · 0% AMBIGUOUS · INFERRED: 524 edges (avg confidence: 0.63)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `40d1326e`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- cli.py
- FakeRoute
- Productionize Plan: notebooks → `src/cua/` package
- test_act.py
- Evidence README
- Look
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
- _FakeModel
- integration/conftest.py
- test_recorder_runs.py
- test_replay_table.py
- redact.py
- SendGuard
- build_capability
- test_replay_extract.py
- test_replay_evidence.py
- CLAUDE.md (project instructions)
- make_replay_ctx
- RefCounter
- manifest.json
- langchain_tools
- safety/__init__.py
- fakes.py
- replay/context.py
- test_shared_evidence.py
- human.py
- BrowserConfig
- DiscoveryConfig
- locate
- test_send_guard.py
- test_control_window.py
- cua.vision
- test_takeover_loop.py
- test_extension.py
- replay/wiring.py
- read_helpers.py
- loader.py
- read.py
- FakeTab
- test_screenshot.py
- mk_look
- langgraph_types
- guard.py
- Discovery decisions
- 2. Each box, with an example
- choose_option_at_point
- ControlWindow
- 2. Components
- HeldPage
- Pure-Visual Discovery Notebook: Build Plan
- ScriptedControl
- SiteLock
- test_recorder_reads.py
- fill
- config.py
- engine.py
- GateControl
- test_routing.py
- FakeWin
- Element
- test_session.py
- test_build.py
- copy
- FakePage
- build_tools
- cua
- cua.schema
- ReplayConfig
- load
- test_goal.py
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
- pytest
- ReplayResult
- discovery/evidence.py
- background.js
- Response
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
- `test_the_login_click_before_a_menu_link_is_kept()` --calls--> `step_events()`  [INFERRED]
  tests/unit/discovery/recorder/test_recorder_runs.py → src/cua/discovery/recorder/events.py
- `test_text_already_on_screen_before_the_step_is_not_an_outcome()` --calls--> `seen_outcome()`  [INFERRED]
  tests/unit/replay/test_loader.py → src/cua/replay/loader.py
- `test_typed_ok_words_tolerant_digits_exact()` --calls--> `typed_ok()`  [INFERRED]
  tests/unit/replay/test_locate.py → src/cua/replay/locate.py
- `test_a_target_needs_a_findable_rung()` --calls--> `Target`  [INFERRED]
  tests/unit/schema/test_capability.py → src/cua/schema/capability.py
- `test_an_old_select_without_an_index_still_loads()` --calls--> `Select`  [INFERRED]
  tests/unit/discovery/recorder/test_recorder_reads.py → src/cua/schema/capability.py

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

## Communities (110 total, 14 thin omitted)

### Community 0 - "cli.py"
Cohesion: 0.11
Nodes (25): argparse, CompiledStateGraph, deepagents, Namespace, _close(), default_site(), discover(), main() (+17 more)

### Community 1 - "FakeRoute"
Cohesion: 0.11
Nodes (11): FakeControl, FakePage, FakeRoute, A fake discovery/replay ``CONTROL`` surface (what ``ControlWindow`` presents).…, A fake ``playwright.async_api.Route``: records every…, A fake ``playwright.async_api.Page``. Every awaited method is recorded in…, asyncio, Tests for the shared offline fakes in tests/fakes.py (TDD: written before the… (+3 more)

### Community 2 - "Productionize Plan: notebooks → `src/cua/` package"
Cohesion: 0.12
Nodes (16): 10. Line-count offenders (today), 1. Package tree, 2. De-duplication (checked by AST diff of both notebooks), 3. State: globals → explicit objects, 4. Async and typing, 5. Notebooks after the move, 6. Tests, 7. ML-engineering practices (kept small) (+8 more)

### Community 3 - "test_act.py"
Cohesion: 0.07
Nodes (75): Items, (value, pattern) for an extract: the whole box when it is exactly the type,…, value_in_box(), make_look(), A look whose elements are numbered 1.. in order (ref, text, box)., Driven, _head(), _helped() (+67 more)

### Community 5 - "Look"
Cohesion: 0.11
Nodes (22): dataclasses, Ctx: what every discovery tool is given, plus the page wrappers the tools…, DiscoveryRun: one discovery run's working state (was the notebook's…, A dropdown whose value a send carries becomes a step (discovery's send-guard…, The discovery event log entry: one tool call, as discovery's ``log()`` writes…, canvas_size(), Canvas-pixel <-> page-point mapping: any window size or pixel density maps to…, The size of the image the model is looking at right now. (+14 more)

### Community 6 - "test_recorder_types.py"
Cohesion: 0.23
Nodes (14): Typed inputs: the recorder infers each input's type from the shapes of the…, Older logs (and any tool that did not log shapes) never guess a type., test_a_plain_whole_number_is_a_number_so_decimals_pass_replay_later(), test_a_value_with_no_shape_is_string(), test_all_currency_values_make_a_currency_input(), test_an_event_without_shapes_is_string(), test_human_entry_is_typed_too(), test_mixed_shapes_fall_back_to_their_common_type() (+6 more)

### Community 7 - "test_replay_inputs.py"
Cohesion: 0.12
Nodes (34): select(), type_(), _cap(), ClearPage, env(), FakeForm, FakePage, asyncio (+26 more)

### Community 8 - "test_input.py"
Cohesion: 0.09
Nodes (28): act(), into_box(), Lock, Page, Session, Step, The response to a send lands after the human's approval, not after the click:…, Unlock the site tab, run our own input steps, relock, settle, take a new look. (+20 more)

### Community 9 - "test_middleware.py"
Cohesion: 0.09
Nodes (34): AIMessage, Handler, _arg_values(), _has_image(), LatestScreenshotOnly, NoopAnthropicPromptCachingMiddleware, AgentMiddleware, AsyncHandler (+26 more)

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
Cohesion: 0.14
Nodes (21): _fake_session(), _patch_session(), MonkeyPatch, parametrize, Path, SimpleNamespace, cua.cli: argument parsing, --input parsing, and main() as the only asyncio.run…, _record_run() (+13 more)

### Community 18 - "test_replay_engine.py"
Cohesion: 0.21
Nodes (44): cap(), click(), extract(), _finish(), _login_cap(), _no_snap(), _only(), _pcap() (+36 more)

### Community 19 - "test_replay_rescue.py"
Cohesion: 0.17
Nodes (30): The guard keeps its own reference to the control window: swap both., set_control(), _env(), _fail_clicks(), FormRoute, HangPage, HumanControl, HumanSimple (+22 more)

### Community 20 - "test_llm.py"
Cohesion: 0.20
Nodes (14): _clean_env(), _gateway(), fixture, MonkeyPatch, Offline tests for `cua.llm.make_chat_model`. No network, no real key. Default:…, test_ca_bundle_passthrough(), test_existing_ssl_cert_file_wins(), test_gateway_env_means_gateway() (+6 more)

### Community 21 - "test_replay_handback.py"
Cohesion: 0.19
Nodes (19): _bctx(), Ext, Human, PanelDone, asyncio, Ctx, parametrize, The toolbar hand-back button during a rescue (its service worker, never the… (+11 more)

### Community 22 - "SiteProfile"
Cohesion: 0.07
Nodes (37): load_site(), OutcomeRule, _outcomes(), Read and validate ``configs/<name>.yaml`` (root defaults to the repo root)., Look up a secret by NAME. Raises on an unknown name or an empty/missing value.…, Secret name -> value from `.env` ("" when unset), as the notebook's SECRETS., R17: text seen after a step -> status. First match wins., Everything site-specific, loaded from ``configs/<name>.yaml``. Secrets: env… (+29 more)

### Community 23 - "test_table.py"
Cohesion: 0.06
Nodes (54): AST, Call, Module, append_rows(), A scrolled second read repeats the rows still on screen: drop only that overlap., _bind(), _code_cells(), _markdown() (+46 more)

### Community 24 - "test_replay_wiring.py"
Cohesion: 0.10
Nodes (21): attach(), Session, Wire replay onto an open session and return its Ctx., _fake_session(), asyncio, MonkeyPatch, Path, attach (the replay setup cell), the guard's replay hooks, and R7: after… (+13 more)

### Community 25 - "recorder/__init__.py"
Cohesion: 0.07
Nodes (53): output(), ``build_capability``'s refusals, unchanged: a leaked value, a blind dropdown,…, _refuse(), used_inputs(), checkpoint(), The capability's checkpoint: the text replay must see to call the run a…, C: after a send, the page's own response proves success (the agent's proof only…, field_area() (+45 more)

### Community 26 - "steps.py"
Cohesion: 0.10
Nodes (47): Point, changed(), choose_option(), do_click(), do_extract(), do_extract_table(), do_navigate(), do_scroll() (+39 more)

### Community 27 - "_FakeModel"
Cohesion: 0.22
Nodes (5): _FakeModel, asyncio, Stands in for a LangChain chat model: no network, records the prompt., _Structured, test_describe_asks_the_given_model_with_labels_and_input_names_only()

### Community 29 - "test_recorder_runs.py"
Cohesion: 0.13
Nodes (25): _click(), _clicks(), _go(), _names(), _nav(), _noop_click(), _paths(), Recorder behaviour pinned by live runs: detours, 404s, login clicks kept, no-op… (+17 more)

### Community 30 - "test_replay_table.py"
Cohesion: 0.21
Nodes (18): _cap(), _defs(), Page, asyncio, Ctx, MonkeyPatch, Path, do_extract_table: find the header by its label, read the rows with discovery's… (+10 more)

### Community 31 - "redact.py"
Cohesion: 0.08
Nodes (40): Pattern, re, The notebook's two agent middlewares, moved unchanged from discovery.py…, hide_secrets(), mask_png(), _num(), OcrFn, Value masking: ``norm``, ``is_sensitive``, ``hide_secrets``, ``redactor``,… (+32 more)

### Community 32 - "SendGuard"
Cohesion: 0.16
Nodes (8): is_sensitive(), pretty(), address.zipCode' -> 'Address zip code' (for the human; the key itself is kept)., Request, ``await guard(route)`` is the route handler. ``guard.lock`` is the send gate:…, Gate 1: Approve, or Edit = back to the form with every value, then again.…, RouteLike, SendGuard

### Community 33 - "build_capability"
Cohesion: 0.09
Nodes (55): build_capability(), Steps, inputs and secrets come from the log only. The model's text cannot fail…, crops_for(), Path, save_artifact(), fixture, MonkeyPatch, saved() (+47 more)

### Community 34 - "test_replay_extract.py"
Cohesion: 0.19
Nodes (21): _extract(), _notebook_assign(), _pcap(), asyncio, Ctx, parametrize, Path, Extract steps on fakes: strict value types and an optional `pattern`. Ported… (+13 more)

### Community 35 - "test_replay_evidence.py"
Cohesion: 0.26
Nodes (19): Path, write_cap(), _all_text(), fake_ocr(), _png(), Ctx, fixture, Path (+11 more)

### Community 36 - "CLAUDE.md (project instructions)"
Cohesion: 0.12
Nodes (19): CLAUDE.md (project instructions), D101: labeled_value refuses a table-header resolution (general fix), D102: label_header/value_header flags ported into agent.py + cli.py capture path, D92: Evidence Capture Helpers (save_discovery_evidence/save_replay_evidence), D93: Pre-existing 02_artifact_schema.py IndexError bug, D95: Missing create_deep_agent import found live in BROWSER 12, D96: build_agent() goal_text vs given_text field-name bug, D97: cua replay --login flag + repeated Balance header trap (+11 more)

### Community 37 - "make_replay_ctx"
Cohesion: 0.08
Nodes (41): make_replay_ctx(), navigate(), A real Ctx (real SendGuard, real ReplayRun) over a fake page/control/lock.…, _click_env(), _form_png(), GotoPage, _judge(), Page (+33 more)

### Community 38 - "RefCounter"
Cohesion: 0.08
Nodes (39): RapidOCR, NDArray, uint8, Fit the screenshot inside the canvas. Returns it and canvas-pixel -> page-point…, to_canvas(), draw_numbered(), number(), ocr() (+31 more)

### Community 39 - "manifest.json"
Cohesion: 0.11
Nodes (18): action, default_icon, default_title, background, service_worker, 128, 16, 32 (+10 more)

### Community 41 - "safety/__init__.py"
Cohesion: 0.07
Nodes (34): functools, JsonObj, Which hosts the browser may reach (D15). The allowlist itself lives in the site…, Safety: what may leave the tab (hosts, the two send gates) and keeping values…, _flat(), _json(), Protocol, What a held request sends, and the same request rebuilt with edited values.… (+26 more)

### Community 42 - "fakes.py"
Cohesion: 0.11
Nodes (22): ActTab, blank_png(), FakeInput, FakeLock, Shared offline fakes for the ported test suite (tests/unit, tests/integration).…, A fake ``cua.browser.SiteLock``: ``open()`` records unlock/lock, nothing else., A fake ``page.mouse`` / ``page.keyboard``: every call is recorded as ``(name,…, A site tab the act/nav tools drive: ``mouse``/``keyboard`` record into… (+14 more)

### Community 43 - "replay/context.py"
Cohesion: 0.08
Nodes (26): pydantic, Ctx, note_takeover_send(), Page, Request, Ctx: what every replay function takes first (session, run, settings, send…, R7: nothing kept. A fresh run, and the guard reads that one from now on., wipe() (+18 more)

### Community 44 - "test_shared_evidence.py"
Cohesion: 0.15
Nodes (17): config_hash(), git_sha(), JsonValue, Path, `git rev-parse HEAD`, or "unknown" (no git, not a repo, any failure)., sha256 of the repr of the frozen configs plus the site name., What ``run.json`` holds: prompt version, model, config hash, git sha. Never a…, run_info() (+9 more)

### Community 45 - "human.py"
Cohesion: 0.17
Nodes (22): Field, P, into_box(), Step, Click the box, clear what is in it, type. Retries replace instead of doubling…, one_at_a_time(), One tool call at a time (``ctx.run.act_lock``), counted against the step budget…, _enter() (+14 more)

### Community 46 - "BrowserConfig"
Cohesion: 0.16
Nodes (20): BrowserConfig, Settings shared by discovery and replay (the same page size at both, Q10)., _in_control(), The take-over itself: badge YOU, unlock the site, wait for Done (panel or…, _takeover_note(), Answerable, button_clicked(), ext_call() (+12 more)

### Community 47 - "DiscoveryConfig"
Cohesion: 0.12
Nodes (40): DiscoveryConfig, Discovery-only settings., Discovery: an LLM agent learns a task once and the recorder saves it as a…, attach(), build_ctx(), _count_nav(), _hooks(), new_run() (+32 more)

### Community 48 - "locate"
Cohesion: 0.23
Nodes (20): locate(), Path, Target, (point, rung) from the first rung that hits, or None., _dup_target(), _look(), Path, Target (+12 more)

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

### Community 53 - "test_extension.py"
Cohesion: 0.19
Nodes (14): Control, Ext, asyncio, parametrize, The hand-back extension's toolbar button: its service worker only, never the…, The extension's service worker: a click counter and a badge., test_a_click_count_rise_returns(), test_a_missing_or_broken_extension_gives_none() (+6 more)

### Community 54 - "replay/wiring.py"
Cohesion: 0.16
Nodes (19): BrowserContext, Playwright, playwright_async_api, Playwright, no decisions: the open session, the site lock, our own input,…, Our own input into the locked site tab: ``act`` (unlock, run steps, relock,…, _alive(), _extension(), handback_dir() (+11 more)

### Community 55 - "read_helpers.py"
Cohesion: 0.09
Nodes (34): log_sent_dropdowns(), Ctx, A dropdown whose value this send carries is a step, even one left on its…, clean_label(), column_header(), is_word(), merged_label(), Where a point is on a look, in words: labels, anchors, page texts. Pure (no… (+26 more)

### Community 56 - "loader.py"
Cohesion: 0.10
Nodes (31): Exception, _ask(), ask_inputs(), ask_option(), _ask_rows(), given_inputs(), input_type(), load_outcomes() (+23 more)

### Community 57 - "read.py"
Cohesion: 0.14
Nodes (25): Cols, _count_start(), The start event's look bookkeeping: the page a run begins on, and how often…, _columns(), headings(), is_header(), off_table(), page_texts() (+17 more)

### Community 58 - "FakeTab"
Cohesion: 0.12
Nodes (3): FakeTab, SimpleNamespace, A fake site or control tab with the Playwright calls discovery's wiring and…

### Community 59 - "test_screenshot.py"
Cohesion: 0.27
Nodes (9): _png(), asyncio, MonkeyPatch, take_look: page calls on the loop, the CPU part (OCR, drawing, encoding) in one…, ShotPage, test_page_width_reads_the_window_width(), test_snap_look_gives_the_look_png_or_none_on_timeout(), test_snap_png_passes_the_timeout_and_gives_none_on_error() (+1 more)

### Community 60 - "mk_look"
Cohesion: 0.16
Nodes (14): FakeLock, mk_look(), Ctx, Replay test helpers: ``make_replay_ctx`` (a real Ctx on fakes), ``mk_look``,…, SiteLock stand-in: open() unlocks for the block., ``take_look`` always returns this look., screen(), set_shoot() (+6 more)

### Community 62 - "guard.py"
Cohesion: 0.14
Nodes (21): json, An evidence screenshot: short timeout, None on failure (never hangs on a held…, snap(), Ctx, run_goal: one goal through the discovery agent (moved from discovery.py…, The deadline passed: end the run STUCK, keeping what the agent did so far., _start(), _timed_out() (+13 more)

### Community 63 - "Discovery decisions"
Cohesion: 0.08
Nodes (24): Base decisions, Cuts, Discovery decisions, Q10: window size and zoom — DECIDED, Q11: notebook format — DECIDED, Q12: dropdowns — DECIDED, Q13: scrolling — DECIDED, Q14: private data in saved pictures — DECIDED (+16 more)

### Community 64 - "2. Each box, with an example"
Cohesion: 0.12
Nodes (15): 1. Diagram, 2. Each box, with an example, 3. All tools, 4. Step by step: one discovery run, 5. Notes, Browser (Playwright), Control window and site lock (Q-A), Discovery architecture (+7 more)

### Community 65 - "choose_option_at_point"
Cohesion: 0.38
Nodes (7): Confirm, LookFn, choose_option_at_index(), choose_option_at_point(), Session, Select the first option containing this text in the dropdown at (or next to)…, Select this exact live option in the Nth <select> (``index``), else the one at…

### Community 66 - "ControlWindow"
Cohesion: 0.11
Nodes (19): base64, Question, ControlWindow, discovery_control(), _img(), Protocol, ControlWindow: our own "Agent control" tab, the only place a human answers.…, Answers the question on top. Closing the window (None) answers every one: fail… (+11 more)

### Community 67 - "2. Components"
Cohesion: 0.12
Nodes (15): 1. Diagram, 2. Components, 3. Step types, 4. Worked example: ParaBank login + read balance, 5. Notes, Actor, Artifact (made by discovery, not replay), Browser setup (+7 more)

### Community 68 - "HeldPage"
Cohesion: 0.12
Nodes (8): DoneWhileSending, HeldPage, HeldRoute, NeverAnsweredGate, Ctx, Like Playwright: while a form POST (a navigation) is held, `page.screenshot()`…, The human clicks Done just as their form POST is held: the gate must still show…, The human clicks Done while their own send's Gate 1 is still open and never…

### Community 69 - "Pure-Visual Discovery Notebook: Build Plan"
Cohesion: 0.09
Nodes (22): 10. Open risks, 1. Global constraints (every task must follow these), 2. Review focus (inputs no spec line covers, but likely to bite), 3. What already exists (reuse, or its visual version), 3a. How the agent is built today (`agent.ipynb` STEP 4, `src/cua/agent.py`), 3b. Existing handoff rules: when a human is called in, 3c. Existing tools → the new tools, 4. New dependencies (checked on PyPI, 2026-09-28) (+14 more)

### Community 71 - "SiteLock"
Cohesion: 0.16
Nodes (12): CdpSender, Protocol, SiteLock: the site tab ignores all real input (CDP…, The one method of a Playwright ``CDPSession`` the lock uses. ``params`` is a…, The site tab ignores all real input (CDP). Lifted only around our own action or…, SiteLock, FakeCdp, asyncio (+4 more)

### Community 72 - "test_recorder_reads.py"
Cohesion: 0.12
Nodes (25): flag_leaks(), Mark (never store) an event whose label, anchor, own text, hint or input name…, asyncio, parametrize, What the tools log, compiled: read-only runs, tables, labels joined to values,…, An event with no page_texts (an older log) proves nothing: the proof is kept., A box's own text with nothing cut from it (a value, a button) stays off the…, _read_log() (+17 more)

### Community 73 - "fill"
Cohesion: 0.33
Nodes (6): fill(), Put inputs into `{{name}}`. `{{secret:x}}` stays as it is: secrets go in only…, secret_name(), R5: bounded OCR poll until the text is on screen., shows(), test_fill_inputs_keeps_secrets_out()

### Community 74 - "config.py"
Cohesion: 0.09
Nodes (17): dotenv, os, pathlib, _actions(), _find_root(), Path, Shared configuration: the site profile, browser/discovery/replay settings, and…, The nearest folder at or above `start` that has a ``configs/`` folder. (+9 more)

### Community 75 - "engine.py"
Cohesion: 0.13
Nodes (41): Drift, action_allowed(), _cleanup_step(), error_page(), finish(), is_cleanup(), judge(), login_came_back() (+33 more)

### Community 77 - "test_routing.py"
Cohesion: 0.06
Nodes (51): CaptureFixture, ChatAnthropic, langchain_agents_middleware, ModelKind, ModuleType, The discovery agent: system prompt, middleware, optional TypeSafe routing, and…, build_routing_middleware(), Classifier (+43 more)

### Community 80 - "Element"
Cohesion: 0.07
Nodes (49): crop_box(), cut_crop(), element_at(), Crops around one point: find the element there, crop around it, read text near…, Crop around the target, with every other piece of text blanked out., Pixels around the point changed. Catches password dots that OCR cannot read., spot_changed(), Pixels -> text: screenshots, OCR, canvas math, crops, and the shared table… (+41 more)

### Community 81 - "test_session.py"
Cohesion: 0.21
Nodes (13): check_viewport(), Q10: refuse rather than record a mismatch between the screenshot and the…, LivePage, _png(), asyncio, MonkeyPatch, Path, open_session reuses a live session (a notebook re-run must not leak a browser),… (+5 more)

### Community 82 - "test_build.py"
Cohesion: 0.46
Nodes (7): langgraph_checkpoint_memory, _capture(), MonkeyPatch, build_agent: the notebook's create_deep_agent call, with routing appended only…, test_build_agent_wires_the_notebooks_agent(), test_routing_is_appended_after_the_notebooks_middleware(), test_the_page_path_is_read_live()

### Community 84 - "FakePage"
Cohesion: 0.11
Nodes (7): FakePage, The site page: any call made on it for the button is a bug., SitePage, FakePage, Frame, Req, Route

### Community 85 - "build_tools"
Cohesion: 0.09
Nodes (17): AsyncFunctionDef, inspect, build_tools(), BaseTool, Ctx, observe, click, type_text, type_secret, select_option, scroll, open_path,…, The prompts are the first filter (user, 2026-09-30); the models and code checks…, test_the_prompt_lists_every_tool() (+9 more)

### Community 86 - "cua"
Cohesion: 0.50
Nodes (3): cua, Read order, Rules

### Community 88 - "cua.schema"
Cohesion: 0.50
Nodes (3): cua.schema, Read order, What may NOT go here

### Community 89 - "ReplayConfig"
Cohesion: 0.13
Nodes (28): SameTextLike, Replay-only settings., ReplayConfig, Replay: runs a capability saved by discovery with plain code, no LLM (step 4:…, anchor_point(), find_template(), find_text(), _ocr_hit() (+20 more)

### Community 90 - "load"
Cohesion: 0.20
Nodes (15): dropdown_options(), mismatches(), _norm_num(), Dropdown, Values a send carries that the human never gave, and the dropdown choices to…, Numbers being sent that the human never gave, e.g. account 1450 vs 1400. Only…, For each key: the options of the page dropdown whose CURRENT value is exactly…, load() (+7 more)

### Community 92 - "test_goal.py"
Cohesion: 0.14
Nodes (21): Agent, Protocol, What run_goal needs of the compiled deep agent., New run on a fresh thread; pass an earlier thread_id to resume it with a next…, run_goal(), FakeAgent, HangingAgent, asyncio (+13 more)

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
Nodes (33): BaseModel, model_validator, _navigate(), Step, Event log -> ``Capability``: steps, inputs, outputs and secrets come from the…, The {{input}} names the steps use, in order. {{secret:x}} is not an input., ``to_step``'s open_path branch, unchanged., step_inputs() (+25 more)

### Community 109 - "test_evidence.py"
Cohesion: 0.26
Nodes (16): _artifact(), masked(), fixture, MonkeyPatch, Path, save_evidence: one masked folder per run. No run value or secret is ever…, The OCR mask is tested in tests/unit/safety; here: that every PNG goes through…, _save() (+8 more)

### Community 110 - "make_ctx"
Cohesion: 0.12
Nodes (36): after_login_click(), D69: at most N login tries; a failure text on screen stops login for the run., make_ctx(), Ctx, Session, A discovery ``Ctx`` over fakes, built like ``attach`` but with no page wiring., helped(), _only() (+28 more)

### Community 113 - "Replay notebook plan"
Cohesion: 0.33
Nodes (5): Decisions made here (review), Open questions for the user, Replay notebook plan, Sections, Tasks

### Community 114 - "Ctx"
Cohesion: 0.07
Nodes (71): act(), canvas(), choose_option(), crop(), Ctx, list_options(), look(), Page (+63 more)

### Community 117 - "test_dropdowns.py"
Cohesion: 0.16
Nodes (18): _approve(), HeldPage, _logged(), _no_crop_pixels(), asyncio, Ctx, fixture, MonkeyPatch (+10 more)

### Community 118 - "pytest"
Cohesion: 0.05
Nodes (52): pytest, load_capability(), The capability and the folder its crop paths are relative to., _fake_llm_keys(), fixture, MonkeyPatch, Suite-wide: never let a real LLM key from `.env` reach a test (cua.config loads…, A fake direct-Anthropic key so code that builds a chat model works offline; no… (+44 more)

### Community 120 - "ReplayResult"
Cohesion: 0.09
Nodes (27): _clean(), _png(), OcrFn, Redact, _drift_lines(), masked_outputs(), Ctx, JsonValue (+19 more)

### Community 123 - "discovery/evidence.py"
Cohesion: 0.20
Nodes (16): The discovery agent's system prompt, verbatim from…, _copy_capability(), _events(), _folder(), Ctx, OcrFn, Path, Redact (+8 more)

### Community 131 - "Response"
Cohesion: 0.12
Nodes (14): bind_control(), ControlTab, Protocol, Bind the control tab to the current :class:`ControlWindow`, once per tab. A…, The Playwright calls binding makes on the control tab., Point the control tab's buttons and its close at ``control``. Re-run safe: the…, _note_latest(), note_response() (+6 more)

### Community 141 - "cua.discovery.agent"
Cohesion: 0.50
Nodes (3): cua.discovery.agent, Read order, What may NOT go here

## Knowledge Gaps
- **159 isolated node(s):** `MODES`, `manifest_version`, `name`, `version`, `description` (+154 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **14 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Look` connect `Look` to `FakeRoute`, `test_act.py`, `test_input.py`, `test_dropdown.py`, `DiscoveryRun`, `test_replay_rescue.py`, `test_table.py`, `steps.py`, `make_replay_ctx`, `RefCounter`, `fakes.py`, `human.py`, `DiscoveryConfig`, `locate`, `replay/wiring.py`, `read_helpers.py`, `read.py`, `FakeTab`, `test_screenshot.py`, `mk_look`, `Element`, `ReplayConfig`, `test_human.py`, `Ctx`, `test_dropdowns.py`?**
  _High betweenness centrality (0.065) - this node is a cross-community bridge._
- **Why does `Ctx` connect `Ctx` to `cli.py`, `FakeRoute`, `Response`, `test_act.py`, `Look`, `test_replay_inputs.py`, `test_middleware.py`, `DiscoveryRun`, `test_replay_rescue.py`, `test_replay_handback.py`, `SiteProfile`, `test_replay_wiring.py`, `test_replay_table.py`, `redact.py`, `make_replay_ctx`, `fakes.py`, `replay/context.py`, `human.py`, `DiscoveryConfig`, `replay/wiring.py`, `read.py`, `FakeTab`, `mk_look`, `guard.py`, `HeldPage`, `ScriptedControl`, `GateControl`, `Element`, `FakePage`, `test_goal.py`, `test_human.py`, `test_dropdowns.py`, `discovery/evidence.py`?**
  _High betweenness centrality (0.050) - this node is a cross-community bridge._
- **Why does `BrowserConfig` connect `BrowserConfig` to `cli.py`, `FakeRoute`, `test_input.py`, `test_dropdown.py`, `test_replay_handback.py`, `SiteProfile`, `make_replay_ctx`, `RefCounter`, `fakes.py`, `replay/context.py`, `test_shared_evidence.py`, `DiscoveryConfig`, `test_takeover_loop.py`, `test_extension.py`, `replay/wiring.py`, `loader.py`, `FakeTab`, `test_screenshot.py`, `mk_look`, `config.py`, `Element`, `test_session.py`, `FakePage`, `Ctx`, `pytest`?**
  _High betweenness centrality (0.042) - this node is a cross-community bridge._
- **Are the 26 inferred relationships involving `Look` (e.g. with `Ctx` and `DiscoveryRun`) actually correct?**
  _`Look` has 26 INFERRED edges - model-reasoned connections that need verification._
- **Are the 59 inferred relationships involving `Ctx` (e.g. with `LatestScreenshotOnly` and `NoopAnthropicPromptCachingMiddleware`) actually correct?**
  _`Ctx` has 59 INFERRED edges - model-reasoned connections that need verification._
- **Are the 35 inferred relationships involving `BrowserConfig` (e.g. with `Session` and `Answerable`) actually correct?**
  _`BrowserConfig` has 35 INFERRED edges - model-reasoned connections that need verification._
- **Are the 30 inferred relationships involving `ReplayConfig` (e.g. with `Ctx` and `_Request`) actually correct?**
  _`ReplayConfig` has 30 INFERRED edges - model-reasoned connections that need verification._