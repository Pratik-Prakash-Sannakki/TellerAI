# Graph Report - BankerAgent  (2026-10-01)

## Corpus Check
- 218 files · ~230,366 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 2798 nodes · 8056 edges · 119 communities (102 shown, 17 thin omitted)
- Extraction: 93% EXTRACTED · 7% INFERRED · 0% AMBIGUOUS · INFERRED: 549 edges (avg confidence: 0.63)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `2390d61f`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- cli.py
- fakes.py
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
- Ctx
- test_cli.py
- test_replay_engine.py
- test_replay_rescue.py
- test_llm.py
- test_replay_handback.py
- SiteProfile
- crops_for
- ReplayConfig
- recorder/__init__.py
- steps.py
- vision/__init__.py
- integration/conftest.py
- test_redact_more.py
- test_replay_table.py
- norm
- test_notebooks.py
- build_capability
- make_replay_ctx
- test_replay_evidence.py
- CLAUDE.md (project instructions)
- test_replay_steps.py
- RefCounter
- manifest.json
- langchain_tools
- discovery/wiring.py
- ClearPage
- replay/wiring.py
- replay/evidence.py
- mismatch.py
- build_ctx
- FakeTab
- test_replay_wiring.py
- test_send_guard.py
- test_control_window.py
- cua.vision
- test_takeover_loop.py
- test_extension.py
- Session
- read.py
- loader.py
- .navigate
- langgraph_types
- Discovery decisions
- 2. Each box, with an example
- request.py
- ControlWindow
- 2. Components
- HeldPage
- Pure-Visual Discovery Notebook: Build Plan
- ScriptedControl
- test_site_lock.py
- log
- ReplayResult
- Capability
- GateControl
- test_routing.py
- FakeWin
- guard.py
- test_import_rules.py
- test_build.py
- copy
- HumanControl
- test_prompt.py
- cua
- pytest
- cua.schema
- rescue.py
- test_capability.py
- test_goal.py
- human.py
- pathlib
- locate
- llm.py
- Look
- test_human.py
- interface-ai-cua
- cua.browser
- cua.handoff
- cua.safety
- cua.discovery
- cua.discovery.recorder
- cua.replay
- schema/__init__.py
- act.py
- test_evidence.py
- make_ctx
- SendGuard
- Replay notebook plan
- nav.py
- config.py
- test_dropdowns.py
- load_capability
- test_recorder_reads.py
- discovery/evidence.py
- FakePage
- Element
- background.js
- bind_control
- yaml
- helpers.py
- Route
- cua.discovery.agent

## God Nodes (most connected - your core abstractions)
1. `Look` - 125 edges
2. `make_ctx()` - 96 edges
3. `Ctx` - 89 edges
4. `BrowserConfig` - 85 edges
5. `build_capability()` - 74 edges
6. `ReplayConfig` - 71 edges
7. `Element` - 63 edges
8. `make_replay_ctx()` - 63 edges
9. `_meta()` - 61 edges
10. `Box` - 55 edges

## Surprising Connections (you probably didn't know these)
- `test_typed_ok_words_tolerant_digits_exact()` --calls--> `typed_ok()`  [INFERRED]
  tests/unit/replay/test_locate.py → src/cua/replay/locate.py
- `test_anchor_label_matches_ocr_merged_with_a_value()` --calls--> `same_label()`  [INFERRED]
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
- 3-file cycle: `src/cua/discovery/tools/__init__.py -> src/cua/discovery/tools/nav.py -> src/cua/discovery/tools/observe.py -> src/cua/discovery/tools/__init__.py`
- 3-file cycle: `src/cua/discovery/tools/__init__.py -> src/cua/discovery/tools/act.py -> src/cua/discovery/tools/observe.py -> src/cua/discovery/tools/__init__.py`
- 3-file cycle: `src/cua/discovery/tools/__init__.py -> src/cua/discovery/tools/human.py -> src/cua/discovery/tools/observe.py -> src/cua/discovery/tools/__init__.py`
- 4-file cycle: `src/cua/discovery/tools/__init__.py -> src/cua/discovery/tools/human.py -> src/cua/discovery/tools/observe.py -> src/cua/discovery/tools/guard.py -> src/cua/discovery/tools/__init__.py`
- 4-file cycle: `src/cua/discovery/tools/__init__.py -> src/cua/discovery/tools/act.py -> src/cua/discovery/tools/observe.py -> src/cua/discovery/tools/guard.py -> src/cua/discovery/tools/__init__.py`
- 4-file cycle: `src/cua/discovery/tools/__init__.py -> src/cua/discovery/tools/nav.py -> src/cua/discovery/tools/observe.py -> src/cua/discovery/tools/guard.py -> src/cua/discovery/tools/__init__.py`
- 4-file cycle: `src/cua/discovery/tools/__init__.py -> src/cua/discovery/tools/act.py -> src/cua/discovery/tools/human.py -> src/cua/discovery/tools/observe.py -> src/cua/discovery/tools/__init__.py`
- 5-file cycle: `src/cua/discovery/tools/__init__.py -> src/cua/discovery/tools/act.py -> src/cua/discovery/tools/human.py -> src/cua/discovery/tools/observe.py -> src/cua/discovery/tools/guard.py -> src/cua/discovery/tools/__init__.py`
- 5-file cycle: `src/cua/discovery/tools/__init__.py -> src/cua/discovery/tools/act.py -> src/cua/discovery/tools/guard.py -> src/cua/discovery/tools/human.py -> src/cua/discovery/tools/observe.py -> src/cua/discovery/tools/__init__.py`
- 5-file cycle: `src/cua/discovery/tools/__init__.py -> src/cua/discovery/tools/nav.py -> src/cua/discovery/tools/guard.py -> src/cua/discovery/tools/human.py -> src/cua/discovery/tools/observe.py -> src/cua/discovery/tools/__init__.py`
- 5-file cycle: `src/cua/discovery/tools/__init__.py -> src/cua/discovery/tools/read.py -> src/cua/discovery/tools/guard.py -> src/cua/discovery/tools/human.py -> src/cua/discovery/tools/observe.py -> src/cua/discovery/tools/__init__.py`

## Communities (119 total, 17 thin omitted)

### Community 0 - "cli.py"
Cohesion: 0.18
Nodes (18): argparse, Namespace, _close(), default_site(), discover(), main(), parse_args(), parse_inputs() (+10 more)

### Community 1 - "fakes.py"
Cohesion: 0.10
Nodes (13): FakeControl, FakePage, FakeRoute, Shared offline fakes for the ported test suite (tests/unit, tests/integration).…, A fake discovery/replay ``CONTROL`` surface (what ``ControlWindow`` presents).…, A fake ``playwright.async_api.Route``: records every…, A fake ``playwright.async_api.Page``. Every awaited method is recorded in…, asyncio (+5 more)

### Community 2 - "Productionize Plan: notebooks → `src/cua/` package"
Cohesion: 0.12
Nodes (16): 10. Line-count offenders (today), 1. Package tree, 2. De-duplication (checked by AST diff of both notebooks), 3. State: globals → explicit objects, 4. Async and typing, 5. Notebooks after the move, 6. Tests, 7. ML-engineering practices (kept small) (+8 more)

### Community 3 - "test_act.py"
Cohesion: 0.05
Nodes (102): Items, (value, pattern) for an extract: the whole box when it is exactly the type,…, value_in_box(), blank_png(), make_look(), A plain PNG of this canvas size (canvas/crops decode the look's png)., A look whose elements are numbered 1.. in order (ref, text, box)., Driven (+94 more)

### Community 5 - "look.py"
Cohesion: 0.13
Nodes (19): canvas_size(), NDArray, uint8, Canvas-pixel <-> page-point mapping: any window size or pixel density maps to…, Fit the screenshot inside the canvas. Returns it and canvas-pixel -> page-point…, The size of the image the model is looking at right now., to_canvas(), to_page() (+11 more)

### Community 6 - "test_recorder_types.py"
Cohesion: 0.23
Nodes (14): Typed inputs: the recorder infers each input's type from the shapes of the…, Older logs (and any tool that did not log shapes) never guess a type., test_a_plain_whole_number_is_a_number_so_decimals_pass_replay_later(), test_a_value_with_no_shape_is_string(), test_all_currency_values_make_a_currency_input(), test_an_event_without_shapes_is_string(), test_human_entry_is_typed_too(), test_mixed_shapes_fall_back_to_their_common_type() (+6 more)

### Community 7 - "test_replay_inputs.py"
Cohesion: 0.15
Nodes (33): select(), type_(), _cap(), env(), FakeForm, FakePage, asyncio, Ctx (+25 more)

### Community 8 - "test_input.py"
Cohesion: 0.07
Nodes (32): act(), into_box(), Lock, Page, Session, Step, The response to a send lands after the human's approval, not after the click:…, Unlock the site tab, run our own input steps, relock, settle, take a new look. (+24 more)

### Community 9 - "test_middleware.py"
Cohesion: 0.07
Nodes (42): AIMessage, CompiledStateGraph, deepagents, Handler, langgraph_checkpoint_memory, build_agent(), BaseChatModel, Ctx (+34 more)

### Community 10 - "test_dropdown.py"
Cohesion: 0.08
Nodes (36): BaseException, Confirm, LookFn, choose_option_at_index(), choose_option_at_point(), list_options(), Session, Every option of the dropdown at this page point ([] if it is not a dropdown).… (+28 more)

### Community 12 - "Replay decisions"
Cohesion: 0.08
Nodes (23): R10: where the compile step lives — DECIDED, R11: why compile, if `response_format` exists? — PROPOSED, R12: what each step type compiles to — PROPOSED, R13: target schema — PROPOSED, R14: what rung 2 needs that discovery doesn't record — DONE, R15: auto-approve at replay — PROPOSED, R16: dead ends and retries at compile — PROPOSED, R17: replay result statuses — PROPOSED (+15 more)

### Community 16 - "Ctx"
Cohesion: 0.08
Nodes (32): Saved, The notebook's two agent middlewares, moved unchanged from discovery.py…, _count_start(), Ctx, list_options(), Page, Ctx: what every discovery tool is given, plus the page wrappers the tools…, Every option of the dropdown at this point ([] if it is not a dropdown). (+24 more)

### Community 17 - "test_cli.py"
Cohesion: 0.12
Nodes (24): _fake_session(), _patch_session(), CaptureFixture, MonkeyPatch, parametrize, Path, SimpleNamespace, cua.cli: argument parsing, --input parsing, and main() as the only asyncio.run… (+16 more)

### Community 18 - "test_replay_engine.py"
Cohesion: 0.20
Nodes (45): cap(), click(), extract(), _finish(), _login_cap(), _no_snap(), _only(), _pcap() (+37 more)

### Community 19 - "test_replay_rescue.py"
Cohesion: 0.20
Nodes (27): The guard keeps its own reference to the control window: swap both., set_control(), _env(), _fail_clicks(), HangPage, HumanSimple, asyncio, MonkeyPatch (+19 more)

### Community 20 - "test_llm.py"
Cohesion: 0.20
Nodes (14): _clean_env(), _gateway(), fixture, MonkeyPatch, Offline tests for `cua.llm.make_chat_model`. No network, no real key. Default:…, test_ca_bundle_passthrough(), test_existing_ssl_cert_file_wins(), test_gateway_env_means_gateway() (+6 more)

### Community 21 - "test_replay_handback.py"
Cohesion: 0.19
Nodes (19): _bctx(), Ext, Human, PanelDone, asyncio, Ctx, parametrize, The toolbar hand-back button during a rescue (its service worker, never the… (+11 more)

### Community 22 - "SiteProfile"
Cohesion: 0.08
Nodes (31): Look up a secret by NAME. Raises on an unknown name or an empty/missing value.…, Secret name -> value from `.env` ("" when unset), as the notebook's SECRETS., Everything site-specific, loaded from ``configs/<name>.yaml``. Secrets: env…, Secret name -> env var name., resolve_secret(), secret_values(), SiteProfile, True if `name` is a known secret with a non-empty value in `.env` (D32: never… (+23 more)

### Community 23 - "crops_for"
Cohesion: 0.15
Nodes (18): BaseChatModel, Save the run as a capability, or say plainly why not. Checked before the model…, _save(), crops_for(), Path, save_artifact(), fixture, MonkeyPatch (+10 more)

### Community 24 - "ReplayConfig"
Cohesion: 0.13
Nodes (29): SameTextLike, Replay-only settings., ReplayConfig, Replay: runs a capability saved by discovery with plain code, no LLM (step 4:…, fill(), Put inputs into `{{name}}`. `{{secret:x}}` stays as it is: secrets go in only…, anchor_point(), find_template() (+21 more)

### Community 25 - "recorder/__init__.py"
Cohesion: 0.07
Nodes (57): check_savable(), Raise NotSaved before any model call when this run cannot become a capability., ``build_capability``'s refusals, unchanged: a leaked value, a blind dropdown,…, _refuse(), checkpoint(), The capability's checkpoint: the text replay must see to call the run a…, C: after a send, the page's own response proves success (the agent's proof only…, field_area() (+49 more)

### Community 26 - "steps.py"
Cohesion: 0.09
Nodes (49): Point, choose_option(), do_click(), do_extract(), do_extract_options(), do_extract_table(), do_navigate(), do_scroll() (+41 more)

### Community 27 - "vision/__init__.py"
Cohesion: 0.13
Nodes (26): Cols, _columns(), extract_table's body once the columns are found: read the rows under the…, The table's columns and the header line's bottom (None: scrolled on, the header…, _saved_rows(), Pixels -> text: screenshots, OCR, canvas math, crops, and the shared table…, append_rows(), cell_shape() (+18 more)

### Community 29 - "test_redact_more.py"
Cohesion: 0.19
Nodes (18): mask_png(), OcrFn, Black out every OCR box whose text holds a run value. A clean image is written…, load(), Path, _ocr(), _png(), parametrize (+10 more)

### Community 30 - "test_replay_table.py"
Cohesion: 0.10
Nodes (32): _cap(), _defs(), Page, asyncio, Ctx, MonkeyPatch, Path, do_extract_table: find the header by its label, read the rows with discovery's… (+24 more)

### Community 31 - "norm"
Cohesion: 0.13
Nodes (20): Pattern, re, landed(), _landing(), Text the page showed in response to a send: the replay checkpoint. Fixed page…, The click event's fields after the click: where it came from and what it led to., norm(), _num() (+12 more)

### Community 32 - "test_notebooks.py"
Cohesion: 0.26
Nodes (16): Call, Module, _bind(), _code_cells(), _markdown(), _offline_namespace(), parametrize, Path (+8 more)

### Community 33 - "build_capability"
Cohesion: 0.08
Nodes (64): build_capability(), Steps, inputs and secrets come from the log only. The model's text cannot fail…, _ev(), _logout(), _meta(), The recorder: the event log becomes a replay-ready capability (R12, R13, R16).…, Invented inputs are ignored, a missing description gets a default, secrets stay…, Banking safety (user, 2026-09-29): replay ends logged out. (+56 more)

### Community 34 - "make_replay_ctx"
Cohesion: 0.15
Nodes (28): make_replay_ctx(), A real Ctx (real SendGuard, real ReplayRun) over a fake page/control/lock.…, _extract(), _notebook_assign(), _options_cap(), OptionsPage, _pcap(), asyncio (+20 more)

### Community 35 - "test_replay_evidence.py"
Cohesion: 0.10
Nodes (35): masked_outputs(), JsonValue, Names and shape only: a value is ***, a table keeps its rows and columns, every…, Path, write_cap(), _all_text(), fake_ocr(), _png() (+27 more)

### Community 36 - "CLAUDE.md (project instructions)"
Cohesion: 0.12
Nodes (19): CLAUDE.md (project instructions), D101: labeled_value refuses a table-header resolution (general fix), D102: label_header/value_header flags ported into agent.py + cli.py capture path, D92: Evidence Capture Helpers (save_discovery_evidence/save_replay_evidence), D93: Pre-existing 02_artifact_schema.py IndexError bug, D95: Missing create_deep_agent import found live in BROWSER 12, D96: build_agent() goal_text vs given_text field-name bug, D97: cua replay --login flag + repeated Balance header trap (+11 more)

### Community 37 - "test_replay_steps.py"
Cohesion: 0.08
Nodes (40): mk_look(), navigate(), _click_env(), _form_png(), GotoPage, _judge(), Page, asyncio (+32 more)

### Community 38 - "RefCounter"
Cohesion: 0.08
Nodes (39): RapidOCR, draw_numbered(), number(), ocr(), ocr_engine(), NDArray, uint8, The shared RapidOCR engine, OCR itself, numbering and the numbered-box overlay.… (+31 more)

### Community 39 - "manifest.json"
Cohesion: 0.11
Nodes (18): action, default_icon, default_title, background, service_worker, 128, 16, 32 (+10 more)

### Community 41 - "discovery/wiring.py"
Cohesion: 0.10
Nodes (18): Attach discovery to an open browser session: the send guard on every request,…, host_allowed(), Which hosts the browser may reach (D15). The allowlist itself lives in the site…, True if `url`'s host is on the site's allowlist (D15). ``about:blank`` is…, Safety: what may leave the tab (hosts, the two send gates) and keeping values…, Protocol, The fields of a ``playwright.async_api.Request`` the guard reads., Request (+10 more)

### Community 43 - "replay/wiring.py"
Cohesion: 0.06
Nodes (32): dataclasses, playwright_async_api, Dropdown, Page, The page's dropdowns, read BEFORE an action (never while guard_send holds a…, The index (among the page's <select>s) of the native dropdown right under this…, read_dropdowns(), select_under() (+24 more)

### Community 44 - "replay/evidence.py"
Cohesion: 0.10
Nodes (32): _clean(), config_hash(), git_sha(), _png(), JsonValue, OcrFn, Path, Redact (+24 more)

### Community 45 - "mismatch.py"
Cohesion: 0.22
Nodes (13): dropdown_options(), mismatches(), _norm_num(), Dropdown, Values a send carries that the human never gave, and the dropdown choices to…, Numbers being sent that the human never gave, e.g. account 1450 vs 1400. Only…, For each key: the options of the page dropdown whose CURRENT value is exactly…, _hide() (+5 more)

### Community 46 - "build_ctx"
Cohesion: 0.40
Nodes (6): build_ctx(), _hooks(), Ctx, Session, Discovery's post-approve steps, in guard_send's order. ``holder`` gets the ctx…, The ctx with its guard and control window, not yet wired to the page. Call…

### Community 47 - "FakeTab"
Cohesion: 0.09
Nodes (37): DiscoveryConfig, Discovery-only settings., Discovery: an LLM agent learns a task once and the recorder saves it as a…, attach(), _count_nav(), new_run(), Counts on the ctx of the latest attach to this page., A fresh run for this goal (run_goal's ``HANDOFF = HandoffState(goal=goal)``). (+29 more)

### Community 48 - "test_replay_wiring.py"
Cohesion: 0.10
Nodes (21): attach(), Session, Wire replay onto an open session and return its Ctx., _fake_session(), asyncio, MonkeyPatch, Path, attach (the replay setup cell), the guard's replay hooks, and R7: after… (+13 more)

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
Cohesion: 0.19
Nodes (18): replay_control(), takeover_text(), Ext, _modes(), asyncio, Take-over pieces and their timing (review focus 1): Done in the panel vs the…, The human pressed Pay (send held, its gate on top of the take-over), then Done…, Done in the panel (answer by mode) reaches the take-over even with a gate on… (+10 more)

### Community 53 - "test_extension.py"
Cohesion: 0.10
Nodes (31): _in_control(), The take-over itself: badge YOU, unlock the site, wait for Done (panel or…, _takeover_note(), Answerable, button_clicked(), ext_call(), Extension, handback_button() (+23 more)

### Community 54 - "Session"
Cohesion: 0.08
Nodes (36): BrowserContext, Playwright, Playwright, no decisions: the open session, the site lock, our own input,…, _alive(), check_viewport(), close_session(), _extension(), handback_dir() (+28 more)

### Community 55 - "read.py"
Cohesion: 0.08
Nodes (47): dropdown_under(), The index of the native <select> right under this point, or None (bounded; None…, log_sent_dropdowns(), Ctx, A dropdown whose value this send carries is a step, even one left on its…, clean_label(), headings(), is_header() (+39 more)

### Community 56 - "loader.py"
Cohesion: 0.09
Nodes (31): Exception, _ask(), ask_inputs(), ask_option(), _ask_rows(), given_inputs(), input_type(), mistyped() (+23 more)

### Community 63 - "Discovery decisions"
Cohesion: 0.08
Nodes (24): Base decisions, Cuts, Discovery decisions, Q10: window size and zoom — DECIDED, Q11: notebook format — DECIDED, Q12: dropdowns — DECIDED, Q13: scrolling — DECIDED, Q14: private data in saved pictures — DECIDED (+16 more)

### Community 64 - "2. Each box, with an example"
Cohesion: 0.12
Nodes (15): 1. Diagram, 2. Each box, with an example, 3. All tools, 4. Step by step: one discovery run, 5. Notes, Browser (Playwright), Control window and site lock (Q-A), Discovery architecture (+7 more)

### Community 65 - "request.py"
Cohesion: 0.13
Nodes (20): functools, json, JsonObj, _flat(), _json(), What a held request sends, and the same request rebuilt with edited values.…, Every value a request sends, from its query, a form body, or a JSON body…, The request's url and body with these values put back in, in the same format. (+12 more)

### Community 66 - "ControlWindow"
Cohesion: 0.11
Nodes (20): base64, Question, ControlWindow, discovery_control(), _img(), Protocol, ControlWindow: our own "Agent control" tab, the only place a human answers.…, Answers the question on top. Closing the window (None) answers every one: fail… (+12 more)

### Community 67 - "2. Components"
Cohesion: 0.12
Nodes (15): 1. Diagram, 2. Components, 3. Step types, 4. Worked example: ParaBank login + read balance, 5. Notes, Actor, Artifact (made by discovery, not replay), Browser setup (+7 more)

### Community 68 - "HeldPage"
Cohesion: 0.16
Nodes (6): FormRoute, HeldPage, HeldRoute, NeverAnsweredGate, Like Playwright: while a form POST (a navigation) is held, `page.screenshot()`…, The human clicks Done while their own send's Gate 1 is still open and never…

### Community 69 - "Pure-Visual Discovery Notebook: Build Plan"
Cohesion: 0.09
Nodes (22): 10. Open risks, 1. Global constraints (every task must follow these), 2. Review focus (inputs no spec line covers, but likely to bite), 3. What already exists (reuse, or its visual version), 3a. How the agent is built today (`agent.ipynb` STEP 4, `src/cua/agent.py`), 3b. Existing handoff rules: when a human is called in, 3c. Existing tools → the new tools, 4. New dependencies (checked on PyPI, 2026-09-28) (+14 more)

### Community 71 - "test_site_lock.py"
Cohesion: 0.36
Nodes (6): FakeCdp, asyncio, SiteLock: the site tab ignores real input except inside ``open()``, which…, test_an_exception_inside_open_still_relocks(), test_open_unlocks_then_relocks(), test_set_sends_the_cdp_ignore_input_command()

### Community 72 - "log"
Cohesion: 0.19
Nodes (13): An evidence screenshot: short timeout, None on failure (never hangs on a held…, snap(), Agent, Ctx, Protocol, run_goal: one goal through the discovery agent (moved from discovery.py…, What run_goal needs of the compiled deep agent., The deadline passed: end the run STUCK, keeping what the agent did so far. (+5 more)

### Community 73 - "ReplayResult"
Cohesion: 0.24
Nodes (7): ReplayResult, test_partial_label_when_not_success(), ReplayResult summary/outputs_line, Stop, and the Status values., test_partial_outputs_line_when_not_success(), test_result_defaults(), test_success_outputs_line(), test_summary_names_the_human_steps()

### Community 75 - "Capability"
Cohesion: 0.14
Nodes (40): Drift, action_allowed(), _cleanup_step(), error_page(), finish(), is_cleanup(), judge(), login_came_back() (+32 more)

### Community 77 - "test_routing.py"
Cohesion: 0.08
Nodes (39): langchain_agents_middleware, ModuleType, build_routing_middleware(), Classifier, confidence_gate(), job_tool_names(), _model_router(), page_name() (+31 more)

### Community 79 - "guard.py"
Cohesion: 0.13
Nodes (18): after_login_click(), _checked(), gate_click(), needs_human_value(), note_call(), Ctx, Result, Tool guards: the event log, one call at a time, the step budget, repeats, login… (+10 more)

### Community 81 - "test_import_rules.py"
Cohesion: 0.29
Nodes (13): _cua_imports(), _layer_files(), _module(), parametrize, Path, The package's import rule (docs/PRODUCTIONIZE_PLAN.md section 1), read from…, The top-level cua subpackage of every ``cua.*`` import (``import`` or ``from``)., Guard the guard: a planted forbidden import is caught in both spellings. (+5 more)

### Community 82 - "test_build.py"
Cohesion: 0.31
Nodes (8): The discovery agent: system prompt, middleware, optional TypeSafe routing, and…, The discovery agent's system prompt, verbatim from…, _capture(), MonkeyPatch, build_agent: the notebook's create_deep_agent call, with routing appended only…, test_build_agent_wires_the_notebooks_agent(), test_routing_is_appended_after_the_notebooks_middleware(), test_the_page_path_is_read_live()

### Community 84 - "HumanControl"
Cohesion: 0.17
Nodes (6): DoneWhileSending, Frame, HumanControl, Ctx, The human clicks Done just as their form POST is held: the gate must still show…, Takes over; while 'in control', the human opens a page and sends a form.

### Community 85 - "test_prompt.py"
Cohesion: 0.09
Nodes (17): AsyncFunctionDef, inspect, build_tools(), BaseTool, Ctx, observe, click, type_text, type_secret, select_option, scroll, open_path,…, The prompts are the first filter (user, 2026-09-30); the models and code checks…, test_the_prompt_lists_every_tool() (+9 more)

### Community 86 - "cua"
Cohesion: 0.50
Nodes (3): cua, Read order, Rules

### Community 87 - "pytest"
Cohesion: 0.29
Nodes (6): pytest, _fake_llm_keys(), fixture, MonkeyPatch, Suite-wide: never let a real LLM key from `.env` reach a test (cua.config loads…, A fake direct-Anthropic key so code that builds a chat model works offline; no…

### Community 88 - "cua.schema"
Cohesion: 0.50
Nodes (3): cua.schema, Read order, What may NOT go here

### Community 89 - "rescue.py"
Cohesion: 0.12
Nodes (19): Asker, hand_back(), Future, Lock, Protocol, The shared take-over loop pieces. Each side's own take-over stays with that…, Done on the toolbar button or in the take-over panel hands back. No reminders…, A send the human started is still held: its gate is on screen next; wait for… (+11 more)

### Community 91 - "test_capability.py"
Cohesion: 0.14
Nodes (14): pydantic, What a replay run returns: its Status, the Stop that ends a run early, and…, R17 run statuses. A member is a plain str, so ``Status.SUCCESS == "SUCCESS"``., Status, StrEnum, _data(), parametrize, Path (+6 more)

### Community 92 - "test_goal.py"
Cohesion: 0.17
Nodes (18): New run on a fresh thread; pass an earlier thread_id to resume it with a next…, run_goal(), FakeAgent, HangingAgent, asyncio, Ctx, Path, run_goal: a fresh run per goal (or a resumed thread), the start event, the… (+10 more)

### Community 93 - "human.py"
Cohesion: 0.16
Nodes (25): Field, P, Every shape the whole value matches, in precedence order. Safe to log: names,…, shapes_of(), one_at_a_time(), One tool call at a time (``ctx.run.act_lock``), counted against the step budget…, _enter(), _from_goal() (+17 more)

### Community 94 - "pathlib"
Cohesion: 0.11
Nodes (15): AST, pathlib, parametrize, Path, cua.schema.value_types matches both notebooks' SHAPES/TYPES exactly., SHAPES and TYPES as each notebook defines them (TYPES spreads SHAPES, so exec…, _tables(), test_tables_equal_the_notebooks() (+7 more)

### Community 95 - "locate"
Cohesion: 0.21
Nodes (22): locate(), Path, Target, (point, rung) from the first rung that hits, or None., Anchor, _dup_target(), _look(), Path (+14 more)

### Community 96 - "llm.py"
Cohesion: 0.11
Nodes (16): ChatAnthropic, ModelKind, os, cua: shared config and the LLM model factory (direct Anthropic or an optional…, _build(), make_chat_model(), model_name_for(), _pass_through_ca_bundle() (+8 more)

### Community 97 - "Look"
Cohesion: 0.10
Nodes (37): Our own input into the locked site tab: ``act`` (unlock, run steps, relock,…, BrowserConfig, Settings shared by discovery and replay (the same page size at both, Q10)., changed(), The pixels moved, or new text is on screen: a small answer ('Transfer…, crop_box(), cut_crop(), _ink() (+29 more)

### Community 98 - "test_human.py"
Cohesion: 0.11
Nodes (49): goal_value(), human_help(), offer_control(), The value the goal already gives for this field, or None. Code backstop for the…, Q21, open-ended: the human answers in words, takes over the site, or stops the…, Only the reason: the first line of the tool result, without its prefix or…, Q21: the one time the site unlocks for a human. What they did is kept as…, take_over() (+41 more)

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
Nodes (33): BaseModel, _check_login_order(), _navigate(), output(), Step, Event log -> ``Capability``: steps, inputs, outputs and secrets come from the…, The {{input}} names the steps use, in order. {{secret:x}} is not an input., Every secret is typed before the first click (the login). Replay clicking Log… (+25 more)

### Community 108 - "act.py"
Cohesion: 0.11
Nodes (43): act(), choose_option(), crop(), into_box(), look(), Step, Crop around the target, every other text blanked (sized to the current canvas)., Unlock the site tab, run our own input steps, relock, settle, take a new look. (+35 more)

### Community 109 - "test_evidence.py"
Cohesion: 0.23
Nodes (18): _artifact(), masked(), fixture, MonkeyPatch, Path, save_evidence: one masked folder per run. No run value or secret is ever…, Live: a form value of '1' made 'version: 1' and 's1.png' look like a leak, so a…, The OCR mask is tested in tests/unit/safety; here: that every PNG goes through… (+10 more)

### Community 110 - "make_ctx"
Cohesion: 0.13
Nodes (34): make_ctx(), Ctx, A discovery ``Ctx`` over fakes, built like ``attach`` but with no page wiring., helped(), _only(), asyncio, fixture, MonkeyPatch (+26 more)

### Community 111 - "SendGuard"
Cohesion: 0.17
Nodes (7): pretty(), address.zipCode' -> 'Address zip code' (for the human; the key itself is kept)., Request, ``await guard(route)`` is the route handler. ``guard.lock`` is the send gate:…, Gate 1: Approve, or Edit = back to the form with every value, then again.…, RouteLike, SendGuard

### Community 113 - "Replay notebook plan"
Cohesion: 0.33
Nodes (5): Decisions made here (review), Open questions for the user, Replay notebook plan, Sections, Tasks

### Community 114 - "nav.py"
Cohesion: 0.25
Nodes (13): canvas(), The size of the image the model is looking at right now., to_page(), make_nav_tools(), _make_open_path(), _make_scroll(), path_refusal(), BaseTool (+5 more)

### Community 115 - "config.py"
Cohesion: 0.19
Nodes (15): dotenv, model_validator, _actions(), _find_root(), load_site(), OutcomeRule, _outcomes(), Path (+7 more)

### Community 117 - "test_dropdowns.py"
Cohesion: 0.16
Nodes (18): _approve(), HeldPage, _logged(), _no_crop_pixels(), asyncio, Ctx, fixture, MonkeyPatch (+10 more)

### Community 118 - "load_capability"
Cohesion: 0.13
Nodes (29): load_capability(), load_outcomes(), _missing_crops(), Path, The capability and the folder its crop paths are relative to., The capability's own `outcomes:` [{text, status, meaning}], else the site's…, Path, Discovery's saved artifact runs in replay unchanged: build -> save -> load ->… (+21 more)

### Community 121 - "test_recorder_reads.py"
Cohesion: 0.07
Nodes (41): describe(), BaseChatModel, R11: name, description, input descriptions, success text. Labels only, no…, _FakeModel, asyncio, Stands in for a LangChain chat model: no network, records the prompt., _options_log(), asyncio (+33 more)

### Community 123 - "discovery/evidence.py"
Cohesion: 0.20
Nodes (17): artifact_texts(), _copy_capability(), _events(), _folder(), Ctx, OcrFn, Path, Redact (+9 more)

### Community 124 - "FakePage"
Cohesion: 0.25
Nodes (4): FakePage, The site page: any call made on it for the button is a bug., SitePage, FakePage

### Community 125 - "Element"
Cohesion: 0.07
Nodes (27): column_header(), The value's column, walked upwards while each text is within TABLE_GAP of the…, The texts on el's row, left of it, up to its table's left edge: the first CLEAR…, Row key + column header, only for a value in a real table, else None (replay…, row_block(), table_cell(), Box, Element (+19 more)

### Community 129 - "bind_control"
Cohesion: 0.31
Nodes (6): bind_control(), ControlTab, Protocol, Bind the control tab to the current :class:`ControlWindow`, once per tab. A…, The Playwright calls binding makes on the control tab., Point the control tab's buttons and its close at ``control``. Re-run safe: the…

### Community 130 - "yaml"
Cohesion: 0.27
Nodes (8): MonkeyPatch, parametrize, Path, Every capability saved in the top-level artifacts/ folder (Decision 6) loads in…, test_a_saved_artifact_loads_in_replay(), test_a_saved_artifact_round_trips(), test_the_old_artifacts_folder_is_gone(), yaml

### Community 133 - "helpers.py"
Cohesion: 0.16
Nodes (12): FakeLock, Ctx, Replay test helpers: ``make_replay_ctx`` (a real Ctx on fakes), ``mk_look``,…, SiteLock stand-in: open() unlocks for the block., ``take_look`` always returns this look., screen(), set_shoot(), AskStop (+4 more)

### Community 141 - "cua.discovery.agent"
Cohesion: 0.50
Nodes (3): cua.discovery.agent, Read order, What may NOT go here

## Knowledge Gaps
- **159 isolated node(s):** `MODES`, `manifest_version`, `name`, `version`, `description` (+154 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **17 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Look` connect `Look` to `fakes.py`, `test_act.py`, `look.py`, `helpers.py`, `test_input.py`, `test_dropdown.py`, `Ctx`, `test_replay_rescue.py`, `ReplayConfig`, `steps.py`, `vision/__init__.py`, `norm`, `make_replay_ctx`, `test_replay_evidence.py`, `test_replay_steps.py`, `RefCounter`, `discovery/wiring.py`, `replay/wiring.py`, `FakeTab`, `read.py`, `human.py`, `locate`, `test_human.py`, `act.py`, `test_dropdowns.py`, `Element`?**
  _High betweenness centrality (0.051) - this node is a cross-community bridge._
- **Why does `Ctx` connect `Ctx` to `fakes.py`, `test_act.py`, `helpers.py`, `Route`, `test_replay_inputs.py`, `test_middleware.py`, `test_replay_rescue.py`, `test_replay_handback.py`, `SiteProfile`, `test_replay_table.py`, `make_replay_ctx`, `test_replay_steps.py`, `discovery/wiring.py`, `ClearPage`, `replay/wiring.py`, `build_ctx`, `FakeTab`, `test_replay_wiring.py`, `Session`, `read.py`, `HeldPage`, `ScriptedControl`, `log`, `GateControl`, `guard.py`, `HumanControl`, `rescue.py`, `test_goal.py`, `human.py`, `Look`, `test_human.py`, `act.py`, `nav.py`, `test_dropdowns.py`, `discovery/evidence.py`, `FakePage`, `Element`?**
  _High betweenness centrality (0.043) - this node is a cross-community bridge._
- **Why does `BrowserConfig` connect `Look` to `cli.py`, `fakes.py`, `yaml`, `helpers.py`, `test_input.py`, `test_dropdown.py`, `test_replay_handback.py`, `SiteProfile`, `make_replay_ctx`, `test_replay_evidence.py`, `test_replay_steps.py`, `RefCounter`, `replay/wiring.py`, `replay/evidence.py`, `FakeTab`, `test_takeover_loop.py`, `test_extension.py`, `Session`, `loader.py`, `config.py`, `load_capability`, `FakePage`, `Element`?**
  _High betweenness centrality (0.039) - this node is a cross-community bridge._
- **Are the 27 inferred relationships involving `Look` (e.g. with `Ctx` and `DiscoveryRun`) actually correct?**
  _`Look` has 27 INFERRED edges - model-reasoned connections that need verification._
- **Are the 60 inferred relationships involving `Ctx` (e.g. with `LatestScreenshotOnly` and `NoopAnthropicPromptCachingMiddleware`) actually correct?**
  _`Ctx` has 60 INFERRED edges - model-reasoned connections that need verification._
- **Are the 36 inferred relationships involving `BrowserConfig` (e.g. with `Session` and `Answerable`) actually correct?**
  _`BrowserConfig` has 36 INFERRED edges - model-reasoned connections that need verification._
- **Are the 55 inferred relationships involving `build_capability()` (e.g. with `saved()` and `test_a_continued_table_is_one_step()`) actually correct?**
  _`build_capability()` has 55 INFERRED edges - model-reasoned connections that need verification._