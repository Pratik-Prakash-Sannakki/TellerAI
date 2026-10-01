# Graph Report - BankerAgent  (2026-10-01)

## Corpus Check
- 224 files · ~263,643 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 2578 nodes · 7313 edges · 119 communities (107 shown, 12 thin omitted)
- Extraction: 93% EXTRACTED · 7% INFERRED · 0% AMBIGUOUS · INFERRED: 497 edges (avg confidence: 0.63)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `e7e34702`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- cli.py
- FakeRoute
- Productionize Plan: notebooks → `src/cua/` package
- test_act.py
- Evidence README
- agent/build.py
- vision/__init__.py
- test_replay_inputs.py
- test_input.py
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
- ReplayConfig
- test_llm.py
- test_replay_handback.py
- test_recorder_reads.py
- request.py
- test_replay_wiring.py
- recorder/__init__.py
- steps.py
- test_notebooks.py
- integration/conftest.py
- pathlib
- test_replay_table.py
- redact.py
- pytest
- build_capability
- test_replay_extract.py
- safety/__init__.py
- CLAUDE.md (project instructions)
- make_replay_ctx
- look.py
- manifest.json
- langchain_tools
- test_recorder_runs.py
- config.py
- test_read_helpers.py
- BrowserConfig
- human.py
- FakeTab
- DiscoveryConfig
- fakes.py
- test_send_guard.py
- test_control_window.py
- cua.vision
- test_takeover_loop.py
- test_table.py
- Session
- RefCounter
- discovery/wiring.py
- Look
- test_extension.py
- browser/__init__.py
- ._held
- langgraph_types
- guard.py
- Discovery decisions
- 2. Each box, with an example
- test_import_rules.py
- ControlWindow
- 2. Components
- norm
- Pure-Visual Discovery Notebook: Build Plan
- read_dropdowns
- SiteLock
- Ctx
- test_a_saved_artifact_loads_in_replay
- SiteProfile
- engine.py
- loader.py
- .awrap_model_call
- Element
- test_session.py
- test_build.py
- copy
- build_tools
- cua
- replay/evidence.py
- cua.schema
- mismatch.py
- run_goal
- test_human_tools.py
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
- cua/evidence.py
- locate.py
- discovery/evidence.py
- FakeWin
- routing.py
- background.js
- ReplayResult
- replay/wiring.py
- test_middleware.py
- rescue.py
- cua.discovery.agent
- test_capability.py

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
- `test_a_target_needs_a_findable_rung()` --calls--> `Target`  [INFERRED]
  tests/unit/schema/test_capability.py → src/cua/schema/capability.py
- `test_an_old_select_without_an_index_still_loads()` --calls--> `Select`  [INFERRED]
  tests/unit/discovery/recorder/test_recorder_reads.py → src/cua/schema/capability.py
- `test_meta_is_loose()` --calls--> `CapabilityMeta`  [INFERRED]
  tests/unit/schema/test_capability.py → src/cua/schema/capability.py
- `test_stop_carries_its_fields()` --calls--> `Stop`  [INFERRED]
  tests/unit/schema/test_result.py → src/cua/schema/result.py

## Import Cycles
- 3-file cycle: `src/cua/discovery/tools/__init__.py -> src/cua/discovery/tools/read.py -> src/cua/discovery/tools/guard.py -> src/cua/discovery/tools/__init__.py`
- 3-file cycle: `src/cua/discovery/tools/__init__.py -> src/cua/discovery/tools/nav.py -> src/cua/discovery/tools/guard.py -> src/cua/discovery/tools/__init__.py`
- 3-file cycle: `src/cua/discovery/tools/__init__.py -> src/cua/discovery/tools/nav.py -> src/cua/discovery/tools/observe.py -> src/cua/discovery/tools/__init__.py`
- 3-file cycle: `src/cua/discovery/tools/__init__.py -> src/cua/discovery/tools/human.py -> src/cua/discovery/tools/observe.py -> src/cua/discovery/tools/__init__.py`
- 3-file cycle: `src/cua/discovery/tools/__init__.py -> src/cua/discovery/tools/act.py -> src/cua/discovery/tools/guard.py -> src/cua/discovery/tools/__init__.py`
- 3-file cycle: `src/cua/discovery/tools/__init__.py -> src/cua/discovery/tools/act.py -> src/cua/discovery/tools/observe.py -> src/cua/discovery/tools/__init__.py`
- 3-file cycle: `src/cua/discovery/tools/guard.py -> src/cua/discovery/tools/human.py -> src/cua/discovery/tools/observe.py -> src/cua/discovery/tools/guard.py`
- 4-file cycle: `src/cua/discovery/tools/__init__.py -> src/cua/discovery/tools/nav.py -> src/cua/discovery/tools/observe.py -> src/cua/discovery/tools/guard.py -> src/cua/discovery/tools/__init__.py`
- 4-file cycle: `src/cua/discovery/tools/__init__.py -> src/cua/discovery/tools/human.py -> src/cua/discovery/tools/observe.py -> src/cua/discovery/tools/guard.py -> src/cua/discovery/tools/__init__.py`
- 4-file cycle: `src/cua/discovery/tools/__init__.py -> src/cua/discovery/tools/act.py -> src/cua/discovery/tools/human.py -> src/cua/discovery/tools/observe.py -> src/cua/discovery/tools/__init__.py`
- 4-file cycle: `src/cua/discovery/tools/__init__.py -> src/cua/discovery/tools/act.py -> src/cua/discovery/tools/observe.py -> src/cua/discovery/tools/guard.py -> src/cua/discovery/tools/__init__.py`
- 5-file cycle: `src/cua/discovery/tools/__init__.py -> src/cua/discovery/tools/read.py -> src/cua/discovery/tools/guard.py -> src/cua/discovery/tools/human.py -> src/cua/discovery/tools/observe.py -> src/cua/discovery/tools/__init__.py`
- 5-file cycle: `src/cua/discovery/tools/__init__.py -> src/cua/discovery/tools/nav.py -> src/cua/discovery/tools/guard.py -> src/cua/discovery/tools/human.py -> src/cua/discovery/tools/observe.py -> src/cua/discovery/tools/__init__.py`
- 5-file cycle: `src/cua/discovery/tools/__init__.py -> src/cua/discovery/tools/act.py -> src/cua/discovery/tools/guard.py -> src/cua/discovery/tools/human.py -> src/cua/discovery/tools/observe.py -> src/cua/discovery/tools/__init__.py`
- 5-file cycle: `src/cua/discovery/tools/__init__.py -> src/cua/discovery/tools/act.py -> src/cua/discovery/tools/human.py -> src/cua/discovery/tools/observe.py -> src/cua/discovery/tools/guard.py -> src/cua/discovery/tools/__init__.py`

## Communities (119 total, 12 thin omitted)

### Community 0 - "cli.py"
Cohesion: 0.18
Nodes (16): argparse, Namespace, _close(), default_site(), main(), parse_args(), parse_inputs(), _print_result() (+8 more)

### Community 1 - "FakeRoute"
Cohesion: 0.11
Nodes (11): FakeControl, FakePage, FakeRoute, A fake discovery/replay ``CONTROL`` surface (what ``ControlWindow`` presents).…, A fake ``playwright.async_api.Route``: records every…, A fake ``playwright.async_api.Page``. Every awaited method is recorded in…, asyncio, Tests for the shared offline fakes in tests/fakes.py (TDD: written before the… (+3 more)

### Community 2 - "Productionize Plan: notebooks → `src/cua/` package"
Cohesion: 0.12
Nodes (16): 10. Line-count offenders (today), 1. Package tree, 2. De-duplication (checked by AST diff of both notebooks), 3. State: globals → explicit objects, 4. Async and typing, 5. Notebooks after the move, 6. Tests, 7. ML-engineering practices (kept small) (+8 more)

### Community 3 - "test_act.py"
Cohesion: 0.07
Nodes (76): Items, (value, pattern) for an extract: the whole box when it is exactly the type,…, value_in_box(), make_look(), A look whose elements are numbered 1.. in order (ref, text, box)., Driven, _head(), _helped() (+68 more)

### Community 5 - "agent/build.py"
Cohesion: 0.12
Nodes (20): CompiledStateGraph, deepagents, Handler, langchain_agents_middleware, langgraph_checkpoint_memory, build_agent(), BaseChatModel, Ctx (+12 more)

### Community 6 - "vision/__init__.py"
Cohesion: 0.15
Nodes (22): Pixels -> text: screenshots, OCR, canvas math, crops, and the shared table…, append_rows(), cell_shape(), col_of(), column_spans(), like_rows(), The shared OCR table reader: discovery and replay use it to find a table's…, A table's end: a line that no longer looks like its rows (a footer, a menu, a… (+14 more)

### Community 7 - "test_replay_inputs.py"
Cohesion: 0.14
Nodes (29): select(), type_(), _cap(), ClearPage, env(), FakeForm, FakePage, asyncio (+21 more)

### Community 8 - "test_input.py"
Cohesion: 0.13
Nodes (18): FakeBox, _hooks(), _png(), asyncio, act/into_box/wait_for_change: our own input runs only inside the unlocked site…, A text box: Ctrl/Cmd+A then Backspace clears it; type appends., _session(), ShotsPage (+10 more)

### Community 9 - "act.py"
Cohesion: 0.19
Nodes (27): crop(), Crop around the target, every other text blanked (sized to the current canvas)., make_act_tools(), _make_click(), _make_select_option(), _make_type_secret(), _make_type_text(), BaseTool (+19 more)

### Community 10 - "test_dropdown.py"
Cohesion: 0.10
Nodes (31): Confirm, LookFn, choose_option_at_index(), choose_option_at_point(), list_options(), Session, Every option of the dropdown at this page point ([] if it is not a dropdown).…, Select the first option containing this text in the dropdown at (or next to)… (+23 more)

### Community 12 - "Replay decisions"
Cohesion: 0.08
Nodes (23): R10: where the compile step lives — DECIDED, R11: why compile, if `response_format` exists? — PROPOSED, R12: what each step type compiles to — PROPOSED, R13: target schema — PROPOSED, R14: what rung 2 needs that discovery doesn't record — DONE, R15: auto-approve at replay — PROPOSED, R16: dead ends and retries at compile — PROPOSED, R17: replay result statuses — PROPOSED (+15 more)

### Community 16 - "discovery/run.py"
Cohesion: 0.12
Nodes (20): Saved, The current run (the one the send guard serves)., DiscoveryRun, DiscoveryRun: one discovery run's working state (was the notebook's…, What the human gave: the goal and every answer (the send guard's mismatch text)., Every value typed, entered, given or sent this run, plus the secrets (in memory…, Every saved text, table cells included (evidence masking only)., Banking: values live only for the run. Keep the log (labels only), drop the… (+12 more)

### Community 17 - "test_cli.py"
Cohesion: 0.14
Nodes (21): _fake_session(), _patch_session(), MonkeyPatch, parametrize, Path, SimpleNamespace, cua.cli: argument parsing, --input parsing, and main() as the only asyncio.run…, _record_run() (+13 more)

### Community 18 - "test_replay_engine.py"
Cohesion: 0.17
Nodes (46): cap(), click(), extract(), AskStop, clean(), ectx(), _finish(), _login_cap() (+38 more)

### Community 19 - "ReplayConfig"
Cohesion: 0.06
Nodes (49): Replay-only settings., ReplayConfig, The guard keeps its own reference to the control window: swap both., set_control(), DoneWhileSending, _env(), _fail_clicks(), FormRoute (+41 more)

### Community 20 - "test_llm.py"
Cohesion: 0.18
Nodes (13): _clean_env(), CaptureFixture, fixture, MonkeyPatch, Offline tests for `cua.llm.make_chat_model` (Iliad gateway). No network, no…, test_ca_bundle_passthrough(), test_existing_ssl_cert_file_wins(), test_fallback_to_anthropic_key() (+5 more)

### Community 21 - "test_replay_handback.py"
Cohesion: 0.13
Nodes (23): FakePage, _bctx(), Ext, Human, PanelDone, asyncio, Ctx, parametrize (+15 more)

### Community 22 - "test_recorder_reads.py"
Cohesion: 0.12
Nodes (25): flag_leaks(), Mark (never store) an event whose label, anchor, own text, hint or input name…, asyncio, parametrize, What the tools log, compiled: read-only runs, tables, labels joined to values,…, An event with no page_texts (an older log) proves nothing: the proof is kept., A box's own text with nothing cut from it (a value, a button) stays off the…, _read_log() (+17 more)

### Community 23 - "request.py"
Cohesion: 0.13
Nodes (20): functools, json, JsonObj, _flat(), _json(), What a held request sends, and the same request rebuilt with edited values.…, Every value a request sends, from its query, a form body, or a JSON body…, The request's url and body with these values put back in, in the same format. (+12 more)

### Community 24 - "test_replay_wiring.py"
Cohesion: 0.11
Nodes (14): Path, write_cap(), asyncio, MonkeyPatch, Path, attach (the replay setup cell), the guard's replay hooks, and R7: after…, Route, _session() (+6 more)

### Community 25 - "recorder/__init__.py"
Cohesion: 0.10
Nodes (40): output(), ``build_capability``'s refusals, unchanged: a leaked value, a blind dropdown,…, _refuse(), used_inputs(), checkpoint(), The capability's checkpoint: the text replay must see to call the run a…, C: after a send, the page's own response proves success (the agent's proof only…, field_area() (+32 more)

### Community 26 - "steps.py"
Cohesion: 0.10
Nodes (46): Point, fill(), Put inputs into `{{name}}`. `{{secret:x}}` stays as it is: secrets go in only…, choose_option(), do_click(), do_extract(), do_extract_table(), do_navigate() (+38 more)

### Community 27 - "test_notebooks.py"
Cohesion: 0.26
Nodes (16): Call, Module, _bind(), _code_cells(), _markdown(), _offline_namespace(), parametrize, Path (+8 more)

### Community 29 - "pathlib"
Cohesion: 0.13
Nodes (8): pathlib, Every capability saved in the top-level artifacts/ folder (Decision 6) loads in…, Frozen notebook sources for the parity tests (step 10 replaced the notebooks…, Guard: no site value lives in src/. Site values belong in configs/<site>.yaml…, parametrize, Path, The frozen notebook snapshots the parity tests read must never drift (see…, test_snapshot_is_unchanged()

### Community 30 - "test_replay_table.py"
Cohesion: 0.21
Nodes (18): _cap(), _defs(), Page, asyncio, Ctx, MonkeyPatch, Path, do_extract_table: find the header by its label, read the rows with discovery's… (+10 more)

### Community 31 - "redact.py"
Cohesion: 0.10
Nodes (36): Pattern, mask_png(), _num(), OcrFn, Value masking: ``norm``, ``is_sensitive``, ``hide_secrets``, ``redactor``,…, text -> text with every value masked. Numbers match however they are written…, Black out every OCR box whose text holds a run value. A clean image is written…, redactor() (+28 more)

### Community 32 - "pytest"
Cohesion: 0.12
Nodes (16): pytest, Value types an extract may declare. Shared by discovery and replay (one table,…, True when the whole value is exactly that type (string, number, boolean, or a…, value_matches_type(), _fake_llm_keys(), fixture, MonkeyPatch, Suite-wide: never let a real LLM key from `.env` reach a test (cua.config loads… (+8 more)

### Community 33 - "build_capability"
Cohesion: 0.08
Nodes (58): discover(), The discovery notebook's cells: setup, run, save artifact, evidence., build_capability(), Steps, inputs and secrets come from the log only. The model's text cannot fail…, crops_for(), Path, save_artifact(), fixture (+50 more)

### Community 34 - "test_replay_extract.py"
Cohesion: 0.19
Nodes (21): _extract(), _notebook_assign(), _pcap(), asyncio, Ctx, parametrize, Path, Extract steps on fakes: strict value types and an optional `pattern`. Ported… (+13 more)

### Community 35 - "safety/__init__.py"
Cohesion: 0.11
Nodes (16): Safety: what may leave the tab (hosts, the two send gates) and keeping values…, hide_secrets(), Each secret value -> ``<name>``. ``secrets`` maps a secret NAME to its value., Protocol, The fields of a ``playwright.async_api.Request`` the guard reads., Request, ControlLike, GuardOptions (+8 more)

### Community 36 - "CLAUDE.md (project instructions)"
Cohesion: 0.12
Nodes (19): CLAUDE.md (project instructions), D101: labeled_value refuses a table-header resolution (general fix), D102: label_header/value_header flags ported into agent.py + cli.py capture path, D92: Evidence Capture Helpers (save_discovery_evidence/save_replay_evidence), D93: Pre-existing 02_artifact_schema.py IndexError bug, D95: Missing create_deep_agent import found live in BROWSER 12, D96: build_agent() goal_text vs given_text field-name bug, D97: cua replay --login flag + repeated Balance header trap (+11 more)

### Community 37 - "make_replay_ctx"
Cohesion: 0.08
Nodes (49): FakeLock, make_replay_ctx(), mk_look(), navigate(), Ctx, Replay test helpers: ``make_replay_ctx`` (a real Ctx on fakes), ``mk_look``,…, SiteLock stand-in: open() unlocks for the block., A real Ctx (real SendGuard, real ReplayRun) over a fake page/control/lock.… (+41 more)

### Community 38 - "look.py"
Cohesion: 0.12
Nodes (17): canvas_size(), NDArray, uint8, Canvas-pixel <-> page-point mapping: any window size or pixel density maps to…, Fit the screenshot inside the canvas. Returns it and canvas-pixel -> page-point…, The size of the image the model is looking at right now., to_canvas(), Box, Element, Look: the shapes every vision/discovery/replay function reads and… (+9 more)

### Community 39 - "manifest.json"
Cohesion: 0.11
Nodes (18): action, default_icon, default_title, background, service_worker, 128, 16, 32 (+10 more)

### Community 41 - "test_recorder_runs.py"
Cohesion: 0.14
Nodes (23): _click(), _clicks(), _go(), _names(), _nav(), _noop_click(), _paths(), Recorder behaviour pinned by live runs: detours, 404s, login clicks kept, no-op… (+15 more)

### Community 42 - "config.py"
Cohesion: 0.13
Nodes (14): dotenv, _find_root(), OutcomeRule, _outcomes(), Path, Shared configuration: the site profile, browser/discovery/replay settings, and…, The nearest folder at or above `start` that has a ``configs/`` folder., R17: text seen after a step -> status. First match wins. (+6 more)

### Community 43 - "test_read_helpers.py"
Cohesion: 0.36
Nodes (7): _look(), where / label_near / spot / page_texts: a point's label in words, never a…, Live bug: 'From account #' dropdown showing '74838' was saved as input…, Live bug: 'Sean' typed into Payee Name became the Address step's label and…, test_a_dropdowns_own_number_is_never_its_label(), test_a_typed_value_above_is_never_the_next_fields_label(), test_where_records_label_box_ordinal_offset_but_not_the_box_contents()

### Community 44 - "BrowserConfig"
Cohesion: 0.21
Nodes (9): BrowserConfig, Settings shared by discovery and replay (the same page size at both, Q10)., Path, Discovery's saved artifact runs in replay unchanged: build -> save -> load ->…, test_crop_paths_resolve_to_saved_files(), test_rung2_offset_hits_the_point_discovery_acted_on(), test_saved_artifact_loads_as_is(), test_steps_dispatch_to_replay_handlers() (+1 more)

### Community 45 - "human.py"
Cohesion: 0.16
Nodes (24): Field, P, into_box(), Step, Click the box, clear what is in it, type. Retries replace instead of doubling…, one_at_a_time(), One tool call at a time (``ctx.run.act_lock``), counted against the step budget…, _enter() (+16 more)

### Community 46 - "FakeTab"
Cohesion: 0.12
Nodes (3): FakeTab, SimpleNamespace, A fake site or control tab with the Playwright calls discovery's wiring and…

### Community 47 - "DiscoveryConfig"
Cohesion: 0.13
Nodes (34): DiscoveryConfig, Discovery-only settings., Discovery: an LLM agent learns a task once and the recorder saves it as a…, attach(), build_ctx(), _count_nav(), new_run(), Ctx (+26 more)

### Community 48 - "fakes.py"
Cohesion: 0.11
Nodes (9): ActTab, FakeInput, FakeLock, Shared offline fakes for the ported test suite (tests/unit, tests/integration).…, A fake ``cua.browser.SiteLock``: ``open()`` records unlock/lock, nothing else., A fake ``page.mouse`` / ``page.keyboard``: every call is recorded as ``(name,…, A site tab the act/nav tools drive: ``mouse``/``keyboard`` record into…, The handful of ``playwright.async_api.Request`` fields the project's code reads. (+1 more)

### Community 49 - "test_send_guard.py"
Cohesion: 0.13
Nodes (25): ``await guard(route)`` is the route handler. ``guard.lock`` is the send gate:…, Side-specific steps, each at the exact point its notebook ran it. on_request:…, SendGuard, SendHooks, Control, _new(), _no_dropdowns(), _old() (+17 more)

### Community 50 - "test_control_window.py"
Cohesion: 0.28
Nodes (22): Factory, SIDES, asyncio, parametrize, ControlWindow: one class, both sides' behaviour. Ported from…, Discovery calls _front inside try (the question is removed on failure); replay…, Regression: a gate during a take-over must win, then hand the take-over back…, _settle() (+14 more)

### Community 51 - "cua.vision"
Cohesion: 0.50
Nodes (3): cua.vision, Read order, What may NOT go here

### Community 52 - "test_takeover_loop.py"
Cohesion: 0.14
Nodes (23): replay_control(), Asker, hand_back(), Future, Protocol, Done on the toolbar button or in the take-over panel hands back. No reminders…, takeover_text(), Ext (+15 more)

### Community 53 - "test_table.py"
Cohesion: 0.18
Nodes (15): AST, _defs(), _is_header(), _look(), Path, The shared OCR table reader: parity between cua.vision.table and both…, ast.dump compare, ignoring docstrings -- the functions this step did not have…, tests/replay/test_table_replay.py's own SHARED set is the contract this module… (+7 more)

### Community 54 - "Session"
Cohesion: 0.18
Nodes (15): BrowserContext, Playwright, playwright_async_api, _alive(), _extension(), handback_dir(), _launch(), open_session() (+7 more)

### Community 55 - "RefCounter"
Cohesion: 0.09
Nodes (33): RapidOCR, draw_numbered(), number(), ocr(), ocr_engine(), NDArray, uint8, The shared RapidOCR engine, OCR itself, numbering and the numbered-box overlay.… (+25 more)

### Community 56 - "discovery/wiring.py"
Cohesion: 0.18
Nodes (12): run_goal: one goal through the discovery agent (moved from discovery.py…, log_sent_dropdowns(), Ctx, A dropdown whose value a send carries becomes a step (discovery's send-guard…, A dropdown whose value this send carries is a step, even one left on its…, log(), One event (the notebook's ``log(tool, args, result, point=None, crop=None,…, _hooks() (+4 more)

### Community 57 - "Look"
Cohesion: 0.10
Nodes (42): Cols, _columns(), clean_label(), column_header(), headings(), is_header(), is_word(), merged_label() (+34 more)

### Community 58 - "test_extension.py"
Cohesion: 0.10
Nodes (31): _in_control(), The take-over itself: badge YOU, unlock the site, wait for Done (panel or…, _takeover_note(), Answerable, button_clicked(), ext_call(), Extension, handback_button() (+23 more)

### Community 59 - "browser/__init__.py"
Cohesion: 0.19
Nodes (13): Playwright, no decisions: the open session, the site lock, our own input,…, act(), into_box(), Lock, Page, Session, Step, Our own input into the locked site tab: ``act`` (unlock, run steps, relock,… (+5 more)

### Community 60 - "._held"
Cohesion: 0.17
Nodes (6): pretty(), address.zipCode' -> 'Address zip code' (for the human; the key itself is kept)., Request, Gate 1: Approve, or Edit = back to the form with every value, then again.…, RouteLike, test_pretty()

### Community 62 - "guard.py"
Cohesion: 0.19
Nodes (14): after_login_click(), _checked(), gate_click(), mark_stuck(), needs_human_value(), note_call(), Ctx, Result (+6 more)

### Community 63 - "Discovery decisions"
Cohesion: 0.08
Nodes (24): Base decisions, Cuts, Discovery decisions, Q10: window size and zoom — DECIDED, Q11: notebook format — DECIDED, Q12: dropdowns — DECIDED, Q13: scrolling — DECIDED, Q14: private data in saved pictures — DECIDED (+16 more)

### Community 64 - "2. Each box, with an example"
Cohesion: 0.12
Nodes (15): 1. Diagram, 2. Each box, with an example, 3. All tools, 4. Step by step: one discovery run, 5. Notes, Browser (Playwright), Control window and site lock (Q-A), Discovery architecture (+7 more)

### Community 65 - "test_import_rules.py"
Cohesion: 0.29
Nodes (13): _cua_imports(), _layer_files(), _module(), parametrize, Path, The package's import rule (docs/PRODUCTIONIZE_PLAN.md section 1), read from…, The top-level cua subpackage of every ``cua.*`` import (``import`` or ``from``)., Guard the guard: a planted forbidden import is caught in both spellings. (+5 more)

### Community 66 - "ControlWindow"
Cohesion: 0.11
Nodes (19): Question, ControlWindow, discovery_control(), _img(), Protocol, ControlWindow: our own "Agent control" tab, the only place a human answers.…, Answers the question on top. Closing the window (None) answers every one: fail…, Answers the newest open question of this mode, wherever it sits on the stack. (+11 more)

### Community 67 - "2. Components"
Cohesion: 0.12
Nodes (15): 1. Diagram, 2. Components, 3. Step types, 4. Worked example: ParaBank login + read balance, 5. Notes, Actor, Artifact (made by discovery, not replay), Browser setup (+7 more)

### Community 68 - "norm"
Cohesion: 0.22
Nodes (11): _count_start(), The start event's look bookkeeping: the page a run begins on, and how often…, landed(), _landing(), _press(), What a click aims at, worked out before it happens., Text the page showed in response to a send: the replay checkpoint. Fixed page…, The click event's fields after the click: where it came from and what it led to. (+3 more)

### Community 69 - "Pure-Visual Discovery Notebook: Build Plan"
Cohesion: 0.09
Nodes (22): 10. Open risks, 1. Global constraints (every task must follow these), 2. Review focus (inputs no spec line covers, but likely to bite), 3. What already exists (reuse, or its visual version), 3a. How the agent is built today (`agent.ipynb` STEP 4, `src/cua/agent.py`), 3b. Existing handoff rules: when a human is called in, 3c. Existing tools → the new tools, 4. New dependencies (checked on PyPI, 2026-09-28) (+14 more)

### Community 70 - "read_dropdowns"
Cohesion: 0.22
Nodes (8): BaseException, Dropdown, Page, The page's dropdowns, read BEFORE an action (never while guard_send holds a…, read_dropdowns(), ReadPage, test_read_dropdowns_is_empty_on_an_error_or_timeout(), test_read_dropdowns_returns_the_page_list_with_the_given_script()

### Community 71 - "SiteLock"
Cohesion: 0.16
Nodes (12): CdpSender, Protocol, SiteLock: the site tab ignores all real input (CDP…, The one method of a Playwright ``CDPSession`` the lock uses., The site tab ignores all real input (CDP). Lifted only around our own action or…, SiteLock, FakeCdp, asyncio (+4 more)

### Community 72 - "Ctx"
Cohesion: 0.25
Nodes (3): Ctx, Page, Request

### Community 73 - "test_a_saved_artifact_loads_in_replay"
Cohesion: 0.40
Nodes (6): MonkeyPatch, parametrize, Path, test_a_saved_artifact_loads_in_replay(), test_a_saved_artifact_round_trips(), test_the_old_artifacts_folder_is_gone()

### Community 74 - "SiteProfile"
Cohesion: 0.08
Nodes (30): load_site(), Read and validate ``configs/<name>.yaml`` (root defaults to the repo root)., Look up a secret by NAME. Raises on an unknown name or an empty/missing value.…, Secret name -> value from `.env` ("" when unset), as the notebook's SECRETS., Everything site-specific, loaded from ``configs/<name>.yaml``. Secrets: env…, Secret name -> env var name., resolve_secret(), secret_values() (+22 more)

### Community 75 - "engine.py"
Cohesion: 0.14
Nodes (38): Drift, _cleanup_step(), error_page(), finish(), is_cleanup(), judge(), login_came_back(), login_steps() (+30 more)

### Community 76 - "loader.py"
Cohesion: 0.12
Nodes (20): Exception, re, ask_inputs(), ask_option(), _ask_rows(), given_inputs(), Ctx, Loading a saved capability (schema v2) and the inputs it needs. Moved unchanged… (+12 more)

### Community 77 - ".awrap_model_call"
Cohesion: 0.13
Nodes (13): Classifier, confidence_gate(), job_tool_names(), page_name(), AsyncHandler, ModelRequest, ModelResponse, Protocol (+5 more)

### Community 80 - "Element"
Cohesion: 0.13
Nodes (24): crop_box(), cut_crop(), Crops around one point: find the element there, crop around it, read text near…, Crop around the target, with every other piece of text blanked out., Pixels around the point changed. Catches password dots that OCR cannot read., spot_changed(), Box, Element (+16 more)

### Community 81 - "test_session.py"
Cohesion: 0.21
Nodes (13): check_viewport(), Q10: refuse rather than record a mismatch between the screenshot and the…, LivePage, _png(), asyncio, MonkeyPatch, Path, open_session reuses a live session (a notebook re-run must not leak a browser),… (+5 more)

### Community 82 - "test_build.py"
Cohesion: 0.31
Nodes (8): The discovery agent: system prompt, middleware, optional TypeSafe routing, and…, The discovery agent's system prompt, verbatim from…, _capture(), MonkeyPatch, build_agent: the notebook's create_deep_agent call, with routing appended only…, test_build_agent_wires_the_notebooks_agent(), test_routing_is_appended_after_the_notebooks_middleware(), test_the_page_path_is_read_live()

### Community 85 - "build_tools"
Cohesion: 0.10
Nodes (17): AsyncFunctionDef, inspect, build_tools(), BaseTool, Ctx, observe, click, type_text, type_secret, select_option, scroll, open_path,…, The prompts are the first filter (user, 2026-09-30); the models and code checks…, test_the_prompt_lists_every_tool() (+9 more)

### Community 86 - "cua"
Cohesion: 0.50
Nodes (3): cua, Read order, Rules

### Community 87 - "replay/evidence.py"
Cohesion: 0.22
Nodes (12): _drift_lines(), masked_outputs(), Ctx, JsonValue, OcrFn, Path, Redact, One folder per replay run (spec 3.5, 6.3): summary, drift, failure, the final… (+4 more)

### Community 88 - "cua.schema"
Cohesion: 0.50
Nodes (3): cua.schema, Read order, What may NOT go here

### Community 90 - "mismatch.py"
Cohesion: 0.22
Nodes (13): dropdown_options(), mismatches(), _norm_num(), Dropdown, Values a send carries that the human never gave, and the dropdown choices to…, Numbers being sent that the human never gave, e.g. account 1450 vs 1400. Only…, For each key: the options of the page dropdown whose CURRENT value is exactly…, _hide() (+5 more)

### Community 92 - "run_goal"
Cohesion: 0.17
Nodes (15): Agent, Ctx, Protocol, What run_goal needs of the compiled deep agent., New run on a fresh thread; pass an earlier thread_id to resume it with a next…, run_goal(), _start(), FakeAgent (+7 more)

### Community 93 - "test_human_tools.py"
Cohesion: 0.28
Nodes (15): blank_png(), A plain PNG of this canvas size (canvas/crops decode the look's png)., _ctx(), asyncio, Ctx, MonkeyPatch, finish_business_outcome / request_missing_values / ask_human (the human-facing…, test_ask_human_asks_with_the_question() (+7 more)

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
Cohesion: 0.16
Nodes (31): BaseModel, model_validator, _navigate(), Step, Event log -> ``Capability``: steps, inputs, outputs and secrets come from the…, ``to_step``'s open_path branch, unchanged., The {{input}} names the steps use, in order. {{secret:x}} is not an input., step_inputs() (+23 more)

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
Cohesion: 0.13
Nodes (28): _all_text(), fake_ocr(), _png(), Ctx, fixture, parametrize, Path, save_evidence writes one masked folder per run: summary, drift, failure (only… (+20 more)

### Community 113 - "Replay notebook plan"
Cohesion: 0.33
Nodes (5): Decisions made here (review), Open questions for the user, Replay notebook plan, Sections, Tasks

### Community 114 - "Ctx"
Cohesion: 0.11
Nodes (33): base64, act(), canvas(), choose_option(), Ctx, list_options(), look(), Page (+25 more)

### Community 117 - "test_dropdowns.py"
Cohesion: 0.16
Nodes (18): _approve(), HeldPage, _logged(), _no_crop_pixels(), asyncio, Ctx, fixture, MonkeyPatch (+10 more)

### Community 118 - "load_capability"
Cohesion: 0.18
Nodes (22): load_capability(), load_outcomes(), _missing_crops(), Path, The capability and the folder its crop paths are relative to., The capability's own `outcomes:` [{text, status, meaning}], else the site's…, fixture, MonkeyPatch (+14 more)

### Community 120 - "cua/evidence.py"
Cohesion: 0.15
Nodes (18): config_hash(), git_sha(), JsonValue, Path, Evidence helpers shared by discovery and replay: masking a JSON-able tree,…, `git rev-parse HEAD`, or "unknown" (no git, not a repo, any failure)., sha256 of the repr of the frozen configs plus the site name., What ``run.json`` holds: prompt version, model, config hash, git sha. Never a… (+10 more)

### Community 121 - "locate.py"
Cohesion: 0.10
Nodes (43): SameTextLike, Replay: runs a capability saved by discovery with plain code, no LLM (step 4:…, anchor_point(), find_template(), find_text(), locate(), NDArray, Path (+35 more)

### Community 123 - "discovery/evidence.py"
Cohesion: 0.18
Nodes (20): _copy_capability(), _events(), _folder(), Ctx, OcrFn, Path, Redact, One masked folder per discovery run: goal, answer, events, transcript, crops,… (+12 more)

### Community 125 - "routing.py"
Cohesion: 0.14
Nodes (20): ModelKind, ModuleType, os, build_routing_middleware(), _model_router(), AgentMiddleware, TypeSafe tool selection + model routing, restored (user, 2026-10-01;…, Haiku for a simple step, Sonnet otherwise (both through cua.llm). (+12 more)

### Community 130 - "ReplayResult"
Cohesion: 0.14
Nodes (12): What a replay run returns: its Status, the Stop that ends a run early, and…, R17 run statuses. A member is a plain str, so ``Status.SUCCESS == "SUCCESS"``., ReplayResult, Status, StrEnum, test_partial_label_when_not_success(), ReplayResult summary/outputs_line, Stop, and the Status values., test_partial_outputs_line_when_not_success() (+4 more)

### Community 131 - "replay/wiring.py"
Cohesion: 0.08
Nodes (31): dataclasses, note_takeover_send(), Ctx: what every replay function takes first (session, run, settings, send…, R7: nothing kept. A fresh run, and the guard reads that one from now on., wipe(), LastRun, One replay run's working state: :class:`ReplayRun` (was the notebook's…, Working values for one run. Replaced by a new one in ``replay``'s ``finally``… (+23 more)

### Community 132 - "test_middleware.py"
Cohesion: 0.29
Nodes (9): asyncio, SimpleNamespace, LatestScreenshotOnly keeps only the newest image in the model's context; the…, _req(), _shot(), test_async_call_trims_too(), test_noop_caching_passes_the_request_through(), test_only_last_image_survives() (+1 more)

### Community 134 - "rescue.py"
Cohesion: 0.14
Nodes (15): Lock, The shared take-over loop pieces. Each side's own take-over stays with that…, A send the human started is still held: its gate is on screen next; wait for…, wait_held_send(), Frame, Ctx, JsonValue, Protocol (+7 more)

### Community 141 - "cua.discovery.agent"
Cohesion: 0.50
Nodes (3): cua.discovery.agent, Read order, What may NOT go here

### Community 149 - "test_capability.py"
Cohesion: 0.14
Nodes (14): pydantic, _EventBase, The discovery event log entry: one tool call, as discovery's ``log()`` writes…, _data(), parametrize, Path, cua.schema.Capability loads every saved artifact and refuses an unknown schema…, test_a_target_needs_a_findable_rung() (+6 more)

## Knowledge Gaps
- **159 isolated node(s):** `MODES`, `manifest_version`, `name`, `version`, `description` (+154 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **12 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Look` connect `Look` to `FakeRoute`, `replay/wiring.py`, `test_act.py`, `vision/__init__.py`, `test_input.py`, `act.py`, `test_dropdown.py`, `discovery/run.py`, `ReplayConfig`, `steps.py`, `make_replay_ctx`, `look.py`, `test_read_helpers.py`, `BrowserConfig`, `human.py`, `FakeTab`, `DiscoveryConfig`, `fakes.py`, `test_table.py`, `Session`, `RefCounter`, `discovery/wiring.py`, `browser/__init__.py`, `norm`, `read_dropdowns`, `Element`, `test_human.py`, `schema/__init__.py`, `test_replay_evidence.py`, `Ctx`, `test_dropdowns.py`, `locate.py`?**
  _High betweenness centrality (0.100) - this node is a cross-community bridge._
- **Why does `BrowserConfig` connect `BrowserConfig` to `cli.py`, `FakeRoute`, `replay/wiring.py`, `test_input.py`, `act.py`, `test_dropdown.py`, `ReplayConfig`, `test_replay_handback.py`, `build_capability`, `make_replay_ctx`, `config.py`, `FakeTab`, `DiscoveryConfig`, `fakes.py`, `test_takeover_loop.py`, `Session`, `RefCounter`, `test_extension.py`, `browser/__init__.py`, `read_dropdowns`, `Ctx`, `test_a_saved_artifact_loads_in_replay`, `SiteProfile`, `loader.py`, `Element`, `test_session.py`, `test_replay_evidence.py`, `Ctx`, `load_capability`, `cua/evidence.py`?**
  _High betweenness centrality (0.058) - this node is a cross-community bridge._
- **Why does `Ctx` connect `Ctx` to `FakeRoute`, `replay/wiring.py`, `test_act.py`, `agent/build.py`, `rescue.py`, `test_replay_inputs.py`, `act.py`, `discovery/run.py`, `test_replay_engine.py`, `ReplayConfig`, `test_replay_handback.py`, `test_replay_wiring.py`, `test_replay_table.py`, `make_replay_ctx`, `human.py`, `FakeTab`, `DiscoveryConfig`, `fakes.py`, `Session`, `discovery/wiring.py`, `Look`, `guard.py`, `norm`, `SiteProfile`, `Element`, `run_goal`, `test_human.py`, `test_dropdowns.py`, `discovery/evidence.py`?**
  _High betweenness centrality (0.056) - this node is a cross-community bridge._
- **Are the 26 inferred relationships involving `Look` (e.g. with `Ctx` and `DiscoveryRun`) actually correct?**
  _`Look` has 26 INFERRED edges - model-reasoned connections that need verification._
- **Are the 35 inferred relationships involving `BrowserConfig` (e.g. with `Session` and `Answerable`) actually correct?**
  _`BrowserConfig` has 35 INFERRED edges - model-reasoned connections that need verification._
- **Are the 53 inferred relationships involving `Ctx` (e.g. with `Session` and `DiscoveryConfig`) actually correct?**
  _`Ctx` has 53 INFERRED edges - model-reasoned connections that need verification._
- **Are the 29 inferred relationships involving `ReplayConfig` (e.g. with `Ctx` and `_Request`) actually correct?**
  _`ReplayConfig` has 29 INFERRED edges - model-reasoned connections that need verification._