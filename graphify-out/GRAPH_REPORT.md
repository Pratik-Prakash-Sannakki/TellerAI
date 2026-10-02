# Graph Report - interface-ai-cua-v2  (2026-10-02)

## Corpus Check
- 275 files · ~572,504 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 104 file(s) not represented in the graph (top: .jsonl 90, .woff2 5, (none) 3)

## Summary
- 3197 nodes · 9263 edges · 138 communities (116 shown, 22 thin omitted)
- Extraction: 85% EXTRACTED · 15% INFERRED · 0% AMBIGUOUS · INFERRED: 1428 edges (avg confidence: 0.92)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `9e8c5e1f`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- cli.py
- FakePage
- SendGuard
- test_act.py
- Evidence README
- discovery/wiring.py
- test_recorder_types.py
- test_replay_inputs.py
- test_input.py
- build_agent
- test_dropdown.py
- save_discovery_evidence / save_replay_evidence (D92)
- Replay decisions
- Five Error Demos (D30)
- langchain_typesafe
- langchain_typesafe_experimental_middleware
- run_values
- test_cli.py
- Ctx
- test_replay_rescue.py
- test_notebooks.py
- test_replay_handback.py
- config.py
- test_recorder_runs.py
- locate.py
- recorder/__init__.py
- steps.py
- masked_outputs
- integration/conftest.py
- test_mask_ids.py
- test_replay_table.py
- test_read.py
- Brag Plan: Teller (v2), AI banking agent (repo: cua)
- build_capability
- make_replay_ctx
- test_replay_evidence.py
- CLAUDE.md (project instructions)
- test_replay_steps.py
- RefCounter
- manifest.json
- langchain_tools
- test_evidence.py
- fakes.py
- replay/wiring.py
- cua/evidence.py
- types
- test_table.py
- make_session
- test_replay_wiring.py
- test_send_guard.py
- test_control_window.py
- BrowserConfig
- test_takeover_loop.py
- test_extension.py
- session.py
- read.py
- loader.py
- save_artifact
- FakeTab
- redactor
- table.py
- langgraph_types
- test_screenshot.py
- Discovery decisions
- routing.py
- redact.py
- ControlWindow
- 2. Components
- test_middleware.py
- type_secret
- discovery/evidence.py
- SiteLock
- build_routing_middleware
- test_eval.py
- FakeLock
- Capability
- test_llm.py
- test_routing.py
- FakeWin
- ReplayResult
- look.py
- agent/build.py
- test_prompt.py
- copy
- R17: replay result statuses — PROPOSED
- build_tools
- test_saved_artifacts.py
- Box
- test_redact_more.py
- MonkeyPatch
- handoff/__init__.py
- test_capability.py
- test_goal.py
- discovery/context.py
- FakeRoute
- locate
- _patch_session
- Look
- test_human.py
- interface-ai-cua
- test_discovery_to_replay.py
- host_allowed
- test_discover_wires_like_the_notebook
- Hyperframes Composition Brief: cua
- hyperframes.json
- scripts
- schema/__init__.py
- Tab
- Ctx
- HyperFrames Composition Project
- make_ctx
- HyperFrames Composition Project
- pathlib
- Stop
- _black
- pytest
- test_after_replay_the_run_holds_no_values_given_text_or_look
- test_dropdowns.py
- load_capability
- _fake_session
- test_act_without_a_send_does_not_wait
- _FakeModel
- step_state
- confidence_gate
- Agent
- _check_login_order
- background.js
- Driven
- .name
- bind_control
- _logged_arg_keys
- Route
- .page
- screen
- discovery/__init__.py

## God Nodes (most connected - your core abstractions)
1. `Ctx` - 155 edges
2. `Ctx` - 127 edges
3. `Look` - 124 edges
4. `make_ctx()` - 102 edges
5. `build_capability()` - 81 edges
6. `make_replay_ctx()` - 67 edges
7. `_meta()` - 66 edges
8. `Capability` - 65 edges
9. `BrowserConfig` - 56 edges
10. `Box` - 54 edges

## Surprising Connections (you probably didn't know these)
- `Browser setup` --references--> `SiteLock`  [INFERRED]
  notebooks/replay/replay_architecture.md → src/cua/browser/site_lock.py
- `Decisions (user, 2026-10-01)` --references--> `SiteProfile`  [INFERRED]
  docs/PRODUCTIONIZE_PLAN.md → src/cua/config.py
- `Open questions (user's call)` --references--> `SiteProfile`  [INFERRED]
  docs/PRODUCTIONIZE_PLAN.md → src/cua/config.py
- `Control window and site lock (Q-A)` --references--> `ask_human()`  [INFERRED]
  notebooks/discovery/discovery_architecture.md → src/cua/discovery/tools/human.py
- `R16: dead ends and retries at compile — PROPOSED` --references--> `ask_human()`  [INFERRED]
  notebooks/replay/DECISIONS.md → src/cua/discovery/tools/human.py

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

## Communities (138 total, 22 thin omitted)

### Community 0 - "cli.py"
Cohesion: 0.14
Nodes (24): argparse, Namespace, _cap_name(), check_eval(), _close(), default_site(), _load_cap(), main() (+16 more)

### Community 1 - "FakePage"
Cohesion: 0.13
Nodes (8): FakeControl, FakePage, A fake discovery/replay ``CONTROL`` surface (what ``ControlWindow`` presents).…, A fake ``playwright.async_api.Page``. Every awaited method is recorded in…, asyncio, Tests for the shared offline fakes in tests/fakes.py (TDD: written before the…, TestFakeControl, TestFakePage

### Community 2 - "SendGuard"
Cohesion: 0.08
Nodes (20): 1. Package tree, 3. State: globals → explicit objects, 4. Async and typing, 5. Notebooks after the move, 6. Tests, 7. ML-engineering practices (kept small), 8. Migration order (strictly sequential; one sub-agent per step; notebooks untouched until step 10), 9. Risks (+12 more)

### Community 3 - "test_act.py"
Cohesion: 0.16
Nodes (37): make_look(), A look whose elements are numbered 1.. in order (ref, text, box)., _head(), _helped(), asyncio, MonkeyPatch, parametrize, click / type_text / type_secret / select_option / scroll / open_path / observe:… (+29 more)

### Community 5 - "discovery/wiring.py"
Cohesion: 0.08
Nodes (39): run_goal: one goal through the discovery agent (moved from discovery.py…, The deadline passed: end the run STUCK, keeping what the agent did so far., _start(), _timed_out(), log_sent_dropdowns(), A dropdown whose value a send carries becomes a step (discovery's send-guard…, A dropdown whose value this send carries is a step, even one left on its…, _checked() (+31 more)

### Community 6 - "test_recorder_types.py"
Cohesion: 0.16
Nodes (20): pick_type(), One input's type from each of its values' shapes. Unknown shapes (None) ->…, _entry(), Typed inputs: the recorder infers each input's type from the shapes of the…, Older logs (and any tool that did not log shapes) never guess a type., Bug: a human typed fake digits ("1") into City during discovery and City became…, test_a_digit_only_human_entry_does_not_make_a_number_input(), test_a_goal_value_the_agent_types_still_makes_a_number_input() (+12 more)

### Community 7 - "test_replay_inputs.py"
Cohesion: 0.11
Nodes (33): select(), type_(), _cap(), ClearPage, env(), FakeForm, FakePage, asyncio (+25 more)

### Community 8 - "test_input.py"
Cohesion: 0.07
Nodes (28): act(), Lock, Step, Unlock the site tab, run our own input steps, relock, settle, take a new look., FakeBox, FocusPage, _hooks(), look_fn() (+20 more)

### Community 9 - "build_agent"
Cohesion: 0.12
Nodes (20): AIMessage, CompiledStateGraph, Handler, build_agent(), BaseChatModel, The discovery deep agent, with a checkpointer so a run can be resumed…, _arg_values(), _has_image() (+12 more)

### Community 10 - "test_dropdown.py"
Cohesion: 0.05
Nodes (48): BaseException, Confirm, LookFn, choose_option_at_index(), choose_option_at_point(), list_options(), Dropdown, Page (+40 more)

### Community 12 - "Replay decisions"
Cohesion: 0.11
Nodes (17): R10: where the compile step lives — DECIDED, R13: target schema — PROPOSED, R15: auto-approve at replay — PROPOSED, R16: dead ends and retries at compile — PROPOSED, R18: drift log — DECIDED, R19: hand-back button during a take-over — DECIDED (user), R1: no LLM at replay — DECIDED, R20: replay ends logged out — DECIDED (user) (+9 more)

### Community 16 - "run_values"
Cohesion: 0.10
Nodes (23): asyncio, Saved, The current run (the one the send guard serves)., DiscoveryRun, DiscoveryRun: one discovery run's working state (was the notebook's…, What the human gave: the goal and every answer (the send guard's mismatch text)., Every value typed, entered, given or sent this run, plus the secrets (in memory…, Every saved text, table cells and dropdown options included (evidence masking… (+15 more)

### Community 17 - "test_cli.py"
Cohesion: 0.17
Nodes (4): parametrize, cua.cli: argument parsing, --input parsing, and main() as the only asyncio.run…, test_a_bad_input_is_refused(), test_eval_refuses_a_run_count_below_one()

### Community 18 - "Ctx"
Cohesion: 0.14
Nodes (45): Ctx, cap(), click(), extract(), _finish(), _login_cap(), _no_snap(), _only() (+37 more)

### Community 19 - "test_replay_rescue.py"
Cohesion: 0.05
Nodes (46): The guard keeps its own reference to the control window: swap both., set_control(), DoneWhileSending, _env(), _fail_clicks(), clicked(), FakePage, FormRoute (+38 more)

### Community 20 - "test_notebooks.py"
Cohesion: 0.08
Nodes (43): AST, builtins, Call, jupytext, Module, _bind(), _code_cells(), _markdown() (+35 more)

### Community 21 - "test_replay_handback.py"
Cohesion: 0.17
Nodes (20): _bctx(), Ext, Human, PanelDone, asyncio, parametrize, The toolbar hand-back button during a rescue (its service worker, never the…, The site page: any call made on it for the button is a bug. (+12 more)

### Community 22 - "config.py"
Cohesion: 0.07
Nodes (47): dotenv, _actions(), _find_root(), load_site(), OutcomeRule, _outcomes(), Path, Shared configuration: the site profile, browser/discovery/replay settings, and… (+39 more)

### Community 23 - "test_recorder_runs.py"
Cohesion: 0.14
Nodes (23): _click(), _clicks(), _go(), _names(), _nav(), _noop_click(), _paths(), Recorder behaviour pinned by live runs: detours, 404s, login clicks kept, no-op… (+15 more)

### Community 24 - "locate.py"
Cohesion: 0.13
Nodes (20): difflib, math, SameTextLike, Replay: runs a capability saved by discovery with plain code, no LLM (step 4:…, anchor_point(), find_template(), find_text(), _ocr_hit() (+12 more)

### Community 25 - "recorder/__init__.py"
Cohesion: 0.08
Nodes (56): BaseChatModel, Save the run as a capability, or say plainly why not. Checked before the model…, _save(), check_savable(), Raise NotSaved before any model call when this run cannot become a capability., ``build_capability``'s refusals, unchanged: a leaked value, a blind dropdown,…, _refuse(), used_inputs() (+48 more)

### Community 26 - "steps.py"
Cohesion: 0.08
Nodes (46): Point, ask_option(), fill(), Put inputs into `{{name}}`. `{{secret:x}}` stays as it is: secrets go in only…, The one mid-run prompt: the given value is not a live option. Choose one, blank…, Exact for anything with a digit (13344 is not 13345); fuzzy for words (PLAN P3)., Bug B: the value is one of the OCR words. Digits exact ($10.00 is 10.00); words…, same_text() (+38 more)

### Community 27 - "masked_outputs"
Cohesion: 0.33
Nodes (6): masked_outputs(), JsonValue, Names and shape only: a value is ***, a table keeps its rows and columns, every…, parametrize, test_masked_outputs_hide_every_option(), test_masked_outputs_keep_the_shape()

### Community 29 - "test_mask_ids.py"
Cohesion: 0.11
Nodes (27): mask_png(), OcrFn, Black out every OCR box whose text holds a run value or secret. With ``ids``, a…, encode(), NDArray, uint8, _digit_columns(), _drawn() (+19 more)

### Community 30 - "test_replay_table.py"
Cohesion: 0.21
Nodes (18): _cap(), _defs(), Page, asyncio, MonkeyPatch, Path, do_extract_table: find the header by its label, read the rows with discovery's…, Each scroll shows the next look. (+10 more)

### Community 31 - "test_read.py"
Cohesion: 0.09
Nodes (40): Items, _cell(), _extract_options(), _no_crop_pixels(), _options_ctx(), asyncio, fixture, MonkeyPatch (+32 more)

### Community 32 - "Brag Plan: Teller (v2), AI banking agent (repo: cua)"
Cohesion: 0.09
Nodes (21): Audio direction, Brag Plan: Teller (v2), AI banking agent (repo: cua), Duration: 22s, Format: landscape — 1920x1080, Hook (first 2-3 seconds), Key moments (the middle), Outro / punchline, Privacy / masking (+13 more)

### Community 33 - "build_capability"
Cohesion: 0.06
Nodes (81): build_capability(), Steps, inputs and secrets come from the log only. The model's text cannot fail…, flag_leaks(), Mark (never store) an event whose label, anchor, own text, hint or input name…, _ev(), _id_cap(), _logout(), _meta() (+73 more)

### Community 34 - "make_replay_ctx"
Cohesion: 0.12
Nodes (32): FakeLock, make_replay_ctx(), Replay test helpers: ``make_replay_ctx`` (a real Ctx on fakes), ``mk_look``,…, SiteLock stand-in: open() unlocks for the block., A real Ctx (real SendGuard, real ReplayRun) over a fake page/control/lock.…, set_shoot(), _extract(), _notebook_assign() (+24 more)

### Community 35 - "test_replay_evidence.py"
Cohesion: 0.20
Nodes (22): Path, write_cap(), _all_text(), fake_ocr(), _png(), fixture, Path, save_evidence writes one masked folder per run: summary, drift, failure (only… (+14 more)

### Community 36 - "CLAUDE.md (project instructions)"
Cohesion: 0.12
Nodes (19): CLAUDE.md (project instructions), D101: labeled_value refuses a table-header resolution (general fix), D102: label_header/value_header flags ported into agent.py + cli.py capture path, D92: Evidence Capture Helpers (save_discovery_evidence/save_replay_evidence), D93: Pre-existing 02_artifact_schema.py IndexError bug, D95: Missing create_deep_agent import found live in BROWSER 12, D96: build_agent() goal_text vs given_text field-name bug, D97: cua replay --login flag + repeated Balance header trap (+11 more)

### Community 37 - "test_replay_steps.py"
Cohesion: 0.07
Nodes (47): Replay-only settings., ReplayConfig, mk_look(), navigate(), _click_env(), click(), gates_then_answer(), _form_png() (+39 more)

### Community 38 - "RefCounter"
Cohesion: 0.12
Nodes (20): number(), Fresh element refs for one run. Refs grow for the whole run and are never…, Reading order (rows top to bottom, then left to right), fresh refs., RefCounter, sys, The page heading 'Accounts Overview' sits above the menu link with the same…, test_the_menu_links_ordinal_is_counted_on_its_own_look_in_reading_order(), number()'s reading order and ref continuity; ocr_engine() built lazily, never… (+12 more)

### Community 39 - "manifest.json"
Cohesion: 0.11
Nodes (18): action, default_icon, default_title, background, service_worker, 128, 16, 32 (+10 more)

### Community 41 - "test_evidence.py"
Cohesion: 0.24
Nodes (20): _artifact(), Path, save_evidence: one masked folder per run. No run value or secret is ever…, Live: a form value of '1' made 'version: 1' and 's1.png' look like a leak, so a…, Live: the goal's account number (never a typed value) was written in clear in…, _save(), test_a_failed_run_still_writes_evidence(), test_a_refused_artifact_still_forgets_the_run() (+12 more)

### Community 42 - "fakes.py"
Cohesion: 0.12
Nodes (21): ActTab, blank_png(), FakeInput, SimpleNamespace, Shared offline fakes for the ported test suite (tests/unit, tests/integration).…, A fake ``page.mouse`` / ``page.keyboard``: every call is recorded as ``(name,…, A site tab the act/nav tools drive: ``mouse``/``keyboard`` record into…, A page script: recorded, answered by ``answer`` (default: no dropdown anywhere). (+13 more)

### Community 43 - "replay/wiring.py"
Cohesion: 0.07
Nodes (29): note_takeover_send(), Ctx: what every replay function takes first (session, run, settings, send…, R7: nothing kept. A fresh run, and the guard reads that one from now on., wipe(), Frame, Protocol, R8: the help panel. Take over (the human does this step) or stop. Moved from…, The human is in control until Done or the toolbar button; pages they visit are… (+21 more)

### Community 44 - "cua/evidence.py"
Cohesion: 0.12
Nodes (21): pydantic, config_hash(), git_sha(), JsonValue, Path, Evidence helpers shared by discovery and replay: masking a JSON-able tree,…, `git rev-parse HEAD`, or "unknown" (no git, not a repo, any failure)., sha256 of the repr of the frozen configs plus the site name. (+13 more)

### Community 45 - "types"
Cohesion: 0.20
Nodes (13): dropdown_options(), Dropdown, For each key: the options of the page dropdown whose CURRENT value is exactly…, _hide(), mismatches/dropdown_options: numbers the human never gave; a dropdown's…, test_discovery_parity(), test_only_numbers_never_given_are_mismatches(), test_only_the_real_dropdown_becomes_a_dropdown() (+5 more)

### Community 46 - "test_table.py"
Cohesion: 0.26
Nodes (10): _is_header(), _look(), The shared OCR table reader: parity between cua.vision.table and both…, tests/replay/test_table_replay.py's own SHARED set is the contract this module…, _read(), test_a_table_that_runs_to_the_bottom_of_the_screen_may_continue(), test_a_three_column_table_is_read_into_rows_even_when_cells_are_a_few_px_off(), test_only_the_asked_columns_are_kept_and_the_row_limit_holds() (+2 more)

### Community 47 - "make_session"
Cohesion: 0.22
Nodes (24): DiscoveryConfig, Discovery-only settings., attach(), Route every request through a new send guard, open the control window. Re-run…, make_session(), A ``cua.browser.Session`` over fakes (no Playwright launched)., asyncio, attach / new_run and the page wrappers (look, act, snap) over fakes. (+16 more)

### Community 48 - "test_replay_wiring.py"
Cohesion: 0.21
Nodes (15): attach(), Wire replay onto an open session and return its Ctx., _fake_session(), asyncio, attach (the replay setup cell), the guard's replay hooks, and R7: after…, C1: one cuaReply forwarder and one close listener per control page, both…, I1: the once-per-page response listener reads the current ctx., _Resp (+7 more)

### Community 49 - "test_send_guard.py"
Cohesion: 0.11
Nodes (24): Side-specific steps, each at the exact point its notebook ran it. on_request:…, SendHooks, Control, _new(), on_request(), _play(), parametrize, SendGuard: nothing that sends data leaves the tab without two human approvals.… (+16 more)

### Community 50 - "test_control_window.py"
Cohesion: 0.28
Nodes (22): Factory, SIDES, asyncio, parametrize, ControlWindow: one class, both sides' behaviour. Ported from…, Discovery calls _front inside try (the question is removed on failure); replay…, Regression: a gate during a take-over must win, then hand the take-over back…, _settle() (+14 more)

### Community 51 - "BrowserConfig"
Cohesion: 0.13
Nodes (22): Source Material, 2. De-duplication (checked by AST diff of both notebooks), BrowserConfig, Settings shared by discovery and replay (the same page size at both, Q10)., NDArray, uint8, Fit the screenshot inside the canvas. Returns it and canvas-pixel -> page-point…, to_canvas() (+14 more)

### Community 52 - "test_takeover_loop.py"
Cohesion: 0.12
Nodes (27): replay_control(), Asker, hand_back(), Future, Lock, Protocol, The shared take-over loop pieces. Each side's own take-over stays with that…, Done on the toolbar button or in the take-over panel hands back. No reminders… (+19 more)

### Community 53 - "test_extension.py"
Cohesion: 0.19
Nodes (14): Control, Ext, asyncio, parametrize, The hand-back extension's toolbar button: its service worker only, never the…, The extension's service worker: a click counter and a badge., test_a_click_count_rise_returns(), test_a_missing_or_broken_extension_gives_none() (+6 more)

### Community 54 - "session.py"
Cohesion: 0.08
Nodes (34): BrowserContext, Playwright, shutil, Playwright, no decisions: the open session, the site lock, our own input,…, _alive(), check_viewport(), close_session(), _extension() (+26 more)

### Community 55 - "read.py"
Cohesion: 0.06
Nodes (60): list_options(), Every option of the dropdown at this point ([] if it is not a dropdown)., Contracts for the tools / agent (steps 8b, 8c), cua.discovery, Read order, What may NOT go here, clean_label(), column_header() (+52 more)

### Community 56 - "loader.py"
Cohesion: 0.12
Nodes (24): missing_inputs(), Every input the capability needs that ``inputs`` does not give (names in any…, _ask(), ask_inputs(), _ask_rows(), row(), given_inputs(), input_type() (+16 more)

### Community 57 - "save_artifact"
Cohesion: 0.14
Nodes (20): cua.discovery.recorder, What may NOT go here, artifact_texts(), walk(), ArtifactMask, _crop(), _mask_ids(), masked() (+12 more)

### Community 59 - "redactor"
Cohesion: 0.13
Nodes (19): Pattern, _num(), text -> text with every value masked. Numbers match however they are written…, redactor(), redact(), masked(), mask(), fixture (+11 more)

### Community 60 - "table.py"
Cohesion: 0.14
Nodes (25): Cols, Q8b: reading a whole table — DECIDED (2026-09-30), R21: table reads — DECIDED (2026-09-30), _columns(), extract_table(), extract_table's body once the columns are found: read the rows under the…, The table's columns and the header line's bottom (None: scrolled on, the header…, _saved_rows() (+17 more)

### Community 62 - "test_screenshot.py"
Cohesion: 0.20
Nodes (11): _png(), asyncio, MonkeyPatch, take_look: page calls on the loop, the CPU part (OCR, drawing, encoding) in one…, ShotPage, test_page_width_reads_the_window_width(), test_snap_look_gives_the_look_png_or_none_on_timeout(), quick() (+3 more)

### Community 63 - "Discovery decisions"
Cohesion: 0.06
Nodes (33): Base decisions, Cuts, Discovery decisions, Q10: window size and zoom — DECIDED, Q11: notebook format — DECIDED, Q12: dropdowns — DECIDED, Q13: scrolling — DECIDED, Q14: private data in saved pictures — DECIDED (+25 more)

### Community 64 - "routing.py"
Cohesion: 0.15
Nodes (17): ChatAnthropic, langchain_agents_middleware, langchain_anthropic, langchain_core_language_models, ModelKind, os, TypeSafe tool selection + model routing, restored (user, 2026-10-01;…, _build() (+9 more)

### Community 65 - "redact.py"
Cohesion: 0.05
Nodes (54): base64, Generates composition/index.html for the Teller brag video (v2). Run from brag-…, collections_abc, dataclasses, 10. Line-count offenders (today), functools, html, json (+46 more)

### Community 66 - "ControlWindow"
Cohesion: 0.16
Nodes (11): Question, ControlWindow, _img(), Answers the question on top. Closing the window (None) answers every one: fail…, Answers the newest open question of this mode, wherever it sits on the stack., A new question supersedes the one on screen (e.g. a gate during a take-over);…, One labelled input per field (label, masked), optionally prefilled. A dropdown…, After a question closes: the one below comes back, else the working page + site… (+3 more)

### Community 67 - "2. Components"
Cohesion: 0.14
Nodes (13): 1. Diagram, 2. Components, 4. Worked example: ParaBank login + read balance, 5. Notes, Actor, Artifact (made by discovery, not replay), Browser setup, Checker (+5 more)

### Community 68 - "test_middleware.py"
Cohesion: 0.14
Nodes (22): langchain_core_messages, 3.5: keep the text the model wrote before its tool calls as ``ctx.run.why``…, RecordWhy, _answer(), asyncio, parametrize, SimpleNamespace, LatestScreenshotOnly keeps only the newest image in the model's context; the… (+14 more)

### Community 69 - "type_secret"
Cohesion: 0.09
Nodes (38): Q22: TypeSafe tool selection + model routing — DECIDED, Q7: things with no text — DECIDED, Summary, Tools: typing into boxes with no number — DECIDED, 5. Notes, 10. Open risks, 1. Global constraints (every task must follow these), 2. Review focus (inputs no spec line covers, but likely to bite) (+30 more)

### Community 70 - "discovery/evidence.py"
Cohesion: 0.09
Nodes (42): discover(), The discovery notebook's cells: setup, run, save artifact, evidence., artifact_mask(), _copy_capability(), _events(), _folder(), OcrFn, Path (+34 more)

### Community 71 - "SiteLock"
Cohesion: 0.11
Nodes (17): contextlib, Q16: handoff UI and site lock — DECIDED, R4: reuse discovery's code — DECIDED, Read order, CdpSender, Protocol, SiteLock: the site tab ignores all real input (CDP…, The one method of a Playwright ``CDPSession`` the lock uses. ``params`` is a… (+9 more)

### Community 72 - "build_routing_middleware"
Cohesion: 0.15
Nodes (16): ModuleType, build_routing_middleware(), Classifier, ModelRouter, _models(), AgentMiddleware, BaseChatModel, Protocol (+8 more)

### Community 73 - "test_eval.py"
Cohesion: 0.18
Nodes (19): _cap(), _ok(), JsonValue, Path, cua.eval: summarize N replay results into a stability report. Pure, no browser., _row(), test_a_click_after_typing_an_input_sends_data(), test_a_step_that_left_its_first_choice_rung_is_a_fallback() (+11 more)

### Community 75 - "Capability"
Cohesion: 0.12
Nodes (42): Drift, action_allowed(), _cleanup_step(), finish(), is_cleanup(), judge(), login_came_back(), login_steps() (+34 more)

### Community 76 - "test_llm.py"
Cohesion: 0.16
Nodes (13): cua: shared config and the LLM model factory (direct Anthropic) for the pure-…, _clean_env(), fixture, MonkeyPatch, Offline tests for `cua.llm.make_chat_model`. No network, no real key. Direct…, test_a_base_url_in_the_env_never_redirects(), test_ca_bundle_passthrough(), test_direct_anthropic() (+5 more)

### Community 77 - "test_routing.py"
Cohesion: 0.19
Nodes (18): _choice(), FakeClassifier, FakeRequest, _model(), _names(), handler(), asyncio, CaptureFixture (+10 more)

### Community 79 - "ReplayResult"
Cohesion: 0.09
Nodes (29): collections, Histogram, EvalReport, fallback_steps(), _hist_line(), _histograms(), _is_fallback(), _output_stability() (+21 more)

### Community 80 - "look.py"
Cohesion: 0.11
Nodes (23): cv2, numpy, numpy_typing, playwright_async_api, RapidOCR, rapidocr_utils_output, into_box(), Our own input into the locked site tab: ``act`` (unlock, run steps, relock,… (+15 more)

### Community 81 - "agent/build.py"
Cohesion: 0.18
Nodes (12): deepagents, langgraph_checkpoint_memory, langgraph_graph_state, build_agent: the notebook's ``AGENT = create_deep_agent(...)`` (discovery.py…, The discovery agent: system prompt, middleware, optional TypeSafe routing, and…, The discovery agent's system prompt, verbatim from…, _capture(), MonkeyPatch (+4 more)

### Community 82 - "test_prompt.py"
Cohesion: 0.10
Nodes (9): hashlib, inspect, The prompts are the first filter (user, 2026-09-30); the models and code checks…, test_the_prompt_lists_every_tool(), Frozen notebook sources for the parity tests (step 10 replaced the notebooks…, parametrize, Path, The frozen notebook snapshots the parity tests read must never drift (see… (+1 more)

### Community 85 - "build_tools"
Cohesion: 0.21
Nodes (13): AsyncFunctionDef, build_tools(), BaseTool, observe, click, type_text, type_secret, select_option, scroll, open_path,…, _notebook_tools(), _params(), asyncio, build_tools(ctx): the notebook's 12 tools, in its TOOLS order, with its names,… (+5 more)

### Community 86 - "test_saved_artifacts.py"
Cohesion: 0.19
Nodes (13): MonkeyPatch, parametrize, Path, Every capability saved in the top-level artifacts/ folder (Decision 6) loads in…, The latest discovery run that saved this capability with exactly these steps., Regression: inputs typed "number" from a human's placeholder digits ("1" in…, A plain-text value passes replay's type check for every input the site would…, _source_run() (+5 more)

### Community 87 - "Box"
Cohesion: 0.13
Nodes (22): Box, Element, _form(), _look(), _png(), ndarray, crop_box/cut_crop/read_near/element_at/screens_same: the crop and comparison…, A 200x60 page: one bordered input box at (20,20)-(167,39), optionally with… (+14 more)

### Community 88 - "test_redact_more.py"
Cohesion: 0.23
Nodes (15): load(), Path, _ocr(), _png(), parametrize, is_sensitive, hide_secrets, replay's NUMBER variant, mask_png -- each against…, test_a_clean_image_is_returned_as_is(), test_hide_secrets_parity() (+7 more)

### Community 89 - "MonkeyPatch"
Cohesion: 0.23
Nodes (14): _cap_file(), MonkeyPatch, Path, _record_run(), _result(), test_a_bad_input_exits_before_any_browser(), test_eval_stops_on_a_missing_input_before_any_run(), test_eval_warns_when_the_capability_sends_data() (+6 more)

### Community 90 - "handoff/__init__.py"
Cohesion: 0.10
Nodes (24): _in_control(), The take-over itself: badge YOU, unlock the site, wait for Done (panel or…, _takeover_note(), Protocol, The two Playwright pages this class touches: the control tab and the site tab., What differs between the discovery and replay control windows., Side, Tab (+16 more)

### Community 91 - "test_capability.py"
Cohesion: 0.23
Nodes (9): _data(), parametrize, Path, cua.schema.Capability loads every saved artifact and refuses an unknown schema…, test_a_target_needs_a_findable_rung(), test_a_wrong_schema_version_is_refused(), test_an_unknown_key_is_refused(), test_every_saved_artifact_loads() (+1 more)

### Community 92 - "test_goal.py"
Cohesion: 0.16
Nodes (18): New run on a fresh thread; pass an earlier thread_id to resume it with a next…, run_goal(), FakeAgent, HangingAgent, asyncio, Path, run_goal: a fresh run per goal (or a resumed thread), the start event, the…, _state_with() (+10 more)

### Community 93 - "discovery/context.py"
Cohesion: 0.10
Nodes (26): langchain_core_tools, Page, The response to a send lands after the human's approval, not after the click:…, wait_for_change(), settled(), _count_start(), on_look(), Ctx: what every discovery tool is given, plus the page wrappers the tools… (+18 more)

### Community 94 - "FakeRoute"
Cohesion: 0.19
Nodes (5): FakeRoute, The handful of ``playwright.async_api.Request`` fields the project's code reads., A fake ``playwright.async_api.Route``: records every…, _Request, TestFakeRoute

### Community 95 - "locate"
Cohesion: 0.19
Nodes (21): locate(), Path, Target, (point, rung) from the first rung that hits, or None., _dup_target(), _look(), Path, Target (+13 more)

### Community 96 - "_patch_session"
Cohesion: 0.21
Nodes (7): _patch_session(), attach(), test_eval_replays_n_times_in_one_session(), test_replay_wires_like_the_notebook(), replay(), test_replay_without_evidence_saves_none(), replay()

### Community 97 - "Look"
Cohesion: 0.18
Nodes (25): canvas_size(), The size of the image the model is looking at right now., crop_box(), cut_crop(), _ink(), input_box(), Crops around one point: find the element there, crop around it, read text near…, New ink appeared INSIDE the input box (text, or a password's dots). A click… (+17 more)

### Community 98 - "test_human.py"
Cohesion: 0.09
Nodes (50): goal_value(), The value the goal already gives for this field, or None. Code backstop for the…, Q21: the one time the site unlocks for a human. What they did is kept as…, take_over(), _answer(), _badge(), _ctx(), _dirty() (+42 more)

### Community 100 - "test_discovery_to_replay.py"
Cohesion: 0.25
Nodes (9): fixture, MonkeyPatch, Path, Discovery's saved artifact runs in replay unchanged: build -> save -> load ->…, saved(), test_crop_paths_resolve_to_saved_files(), test_rung2_offset_hits_the_point_discovery_acted_on(), test_saved_artifact_loads_as_is() (+1 more)

### Community 101 - "host_allowed"
Cohesion: 0.10
Nodes (17): cua.handoff, How it fits, What may NOT go here, cua.replay, How it fits, What may NOT go here, JsonValue, Step (+9 more)

### Community 102 - "test_discover_wires_like_the_notebook"
Cohesion: 0.20
Nodes (8): CaptureFixture, Live: a take-over run crashed with a traceback after a wasted describe() call., test_a_leak_found_while_masking_is_not_saved_and_says_so(), refuse(), test_a_run_that_cannot_be_saved_prints_why_and_never_asks_the_model(), test_discover_wires_like_the_notebook(), describe(), test_the_terminal_shows_ids_by_their_last_digits_and_amounts_as_is()

### Community 103 - "Hyperframes Composition Brief: cua"
Cohesion: 0.22
Nodes (8): Audio, Creative Direction, Hyperframes Composition Brief: cua, Hyperframes Instructions, Objective, Output, Storyboard, Visual Identity

### Community 104 - "hyperframes.json"
Cohesion: 0.22
Nodes (8): media, autoProxy, paths, assets, blocks, components, registry, $schema

### Community 105 - "scripts"
Cohesion: 0.22
Nodes (8): name, private, scripts, check, dev, publish, render, type

### Community 106 - "schema/__init__.py"
Cohesion: 0.11
Nodes (44): BaseModel, enum, model_validator, _navigate(), output(), Event log -> ``Capability``: steps, inputs, outputs and secrets come from the…, ``to_step``'s open_path branch, unchanged., target() (+36 more)

### Community 108 - "Ctx"
Cohesion: 0.07
Nodes (80): Field, P, act(), canvas(), choose_option(), shown(), crop(), Ctx (+72 more)

### Community 109 - "HyperFrames Composition Project"
Cohesion: 0.25
Nodes (7): Commands, Documentation, HyperFrames Composition Project, Key Rules, Linting — ALWAYS RUN AFTER CHANGES, Project Structure, Skills — USE THESE FIRST

### Community 110 - "make_ctx"
Cohesion: 0.09
Nodes (38): after_login_click(), D69: at most N login tries; a failure text on screen stops login for the run., make_ctx(), A discovery ``Ctx`` over fakes, built like ``attach`` but with no page wiring., helped(), _only(), asyncio, fixture (+30 more)

### Community 111 - "HyperFrames Composition Project"
Cohesion: 0.25
Nodes (7): Commands, Documentation, HyperFrames Composition Project, Key Rules, Linting — ALWAYS RUN AFTER CHANGES, Project Structure, Skills — USE THESE FIRST

### Community 112 - "pathlib"
Cohesion: 0.25
Nodes (3): pathlib, The hand-back extension never touches any site: no content scripts, no host…, Guard: no site value lives in src/. Site values belong in configs/<site>.yaml…

### Community 113 - "Stop"
Cohesion: 0.10
Nodes (20): Exception, Decisions made here (review), Open questions for the user, Replay notebook plan, Sections, Tasks, 3. Step types, Loader + pre-flight (+12 more)

### Community 114 - "_black"
Cohesion: 0.39
Nodes (8): _black(), _glyphs(), _hidden_x(), NDArray, uint8, The box's ink column runs, left to right (x ranges): one per glyph when glyphs…, The x range of the id's hidden digits, found by counting glyphs from the box's…, The whole box, or (``cut``) the id's digits before its last visible ones.

### Community 115 - "pytest"
Cohesion: 0.29
Nodes (6): pytest, _fake_llm_keys(), fixture, MonkeyPatch, Suite-wide: never let a real LLM key from `.env` reach a test (cua.config loads…, A fake Anthropic key so code that builds a chat model works offline.

### Community 116 - "test_after_replay_the_run_holds_no_values_given_text_or_look"
Cohesion: 0.29
Nodes (4): MonkeyPatch, Path, test_after_replay_the_run_holds_no_values_given_text_or_look(), open_start()

### Community 117 - "test_dropdowns.py"
Cohesion: 0.24
Nodes (14): _approve(), HeldPage, _logged(), asyncio, A dropdown the send carries becomes a Select step; the guard hooks never read a…, Page reads (a held send blocks them); bring_to_front is the control window's…, Human values (zip, phone, SSN) are not in the goal: no mismatch form, no…, While a request is held, every page read hangs (the live Register bug). (+6 more)

### Community 118 - "load_capability"
Cohesion: 0.17
Nodes (25): load_capability(), load_outcomes(), _missing_crops(), Path, The capability and the folder its crop paths are relative to., The capability's own `outcomes:` [{text, status, meaning}], else the site's…, fixture, MonkeyPatch (+17 more)

### Community 119 - "_fake_session"
Cohesion: 0.33
Nodes (4): _fake_session(), SimpleNamespace, _Session, SITE_NS()

### Community 120 - "test_act_without_a_send_does_not_wait"
Cohesion: 0.15
Nodes (15): _no_crop_pixels(), fixture, MonkeyPatch, _look(), MonkeyPatch, test_act_reads_dropdowns_first_and_waits_for_a_response_after_a_send(), changed(), dropdowns() (+7 more)

### Community 121 - "_FakeModel"
Cohesion: 0.14
Nodes (10): _FakeModel, asyncio, Stands in for a LangChain chat model: no network, records the prompt., asyncio, test_describe_names_the_options_outputs(), test_describe_names_the_table_outputs(), _Structured, test_describe_asks_the_given_model_with_labels_and_input_names_only() (+2 more)

### Community 122 - "step_state"
Cohesion: 0.15
Nodes (14): page_name(), AsyncHandler, ModelRequest, ModelResponse, The URL's last path segment: no query, no ``;jsessionid=``, no trailing slash,…, The first word of the last tool result ('OK', 'REFUSED', 'Saved'), never its…, What the classifier sees for a step: the page name, the last tool's name and…, _status_word() (+6 more)

### Community 123 - "confidence_gate"
Cohesion: 0.47
Nodes (6): Restore: TypeSafe tool selection + model routing (user, 2026-10-01), confidence_gate(), job_tool_names(), Tools this job needs, plus the always-allowed set. Pure: no network, no LLM., Narrow base_tools to this job's tools, but only if the classifier is confident.…, test_job_tool_names_and_gate()

### Community 124 - "Agent"
Cohesion: 0.40
Nodes (3): Agent, Protocol, What run_goal needs of the compiled deep agent.

### Community 125 - "_check_login_order"
Cohesion: 0.40
Nodes (5): _check_login_order(), Step, The {{input}} names the steps use, in order. {{secret:x}} is not an input., Every secret is typed before the first click (the login). Replay clicking Log…, step_inputs()

### Community 127 - "Driven"
Cohesion: 0.40
Nodes (3): Driven, The stubbed page work: every ``act`` call and the looks it returns., nav()

### Community 128 - ".name"
Cohesion: 0.50
Nodes (3): R11: why compile, if `response_format` exists? — PROPOSED, For a name or a path (``[a-z0-9_]`` only): the last digits, no stars., test_only_main_calls_asyncio_run()

### Community 129 - "bind_control"
Cohesion: 0.25
Nodes (5): bind_control(), ControlTab, Protocol, The Playwright calls binding makes on the control tab., Point the control tab's buttons and its close at ``control``. Re-run safe: the…

### Community 130 - "_logged_arg_keys"
Cohesion: 0.50
Nodes (4): _logged_arg_keys(), The arg-dict keys of every ``log(ctx, "<tool>", {...}, ...)`` call in the tool…, Banking rule (ported from test_no_values_stored.py, now on the package's own…, test_typed_and_selected_values_never_reach_the_log()

### Community 133 - "screen"
Cohesion: 0.14
Nodes (10): shoot(), ``take_look`` always returns this look., screen(), AskStop, clean(), ectx(), pctx(), fixture (+2 more)

## Knowledge Gaps
- **133 isolated node(s):** `$schema`, `registry`, `blocks`, `components`, `assets` (+128 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 1190 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **22 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Look` connect `Look` to `test_act.py`, `discovery/wiring.py`, `screen`, `test_input.py`, `test_dropdown.py`, `run_values`, `test_replay_rescue.py`, `locate.py`, `steps.py`, `test_read.py`, `make_replay_ctx`, `test_replay_steps.py`, `RefCounter`, `test_table.py`, `BrowserConfig`, `read.py`, `table.py`, `test_screenshot.py`, `type_secret`, `look.py`, `Box`, `discovery/context.py`, `locate`, `test_human.py`, `test_discovery_to_replay.py`, `Ctx`, `make_ctx`, `Stop`, `test_act_without_a_send_does_not_wait`, `Driven`?**
  _High betweenness centrality (0.057) - this node is a cross-community bridge._
- **Why does `Ctx` connect `Ctx` to `test_act.py`, `discovery/wiring.py`, `build_agent`, `run_values`, `config.py`, `test_read.py`, `fakes.py`, `make_session`, `session.py`, `read.py`, `table.py`, `redact.py`, `test_middleware.py`, `discovery/evidence.py`, `agent/build.py`, `build_tools`, `handoff/__init__.py`, `test_goal.py`, `discovery/context.py`, `test_human.py`, `make_ctx`, `test_dropdowns.py`, `Driven`?**
  _High betweenness centrality (0.047) - this node is a cross-community bridge._
- **Why does `Ctx` connect `Ctx` to `SendGuard`, `.page`, `screen`, `test_replay_inputs.py`, `test_replay_rescue.py`, `test_replay_handback.py`, `config.py`, `steps.py`, `test_replay_table.py`, `make_replay_ctx`, `test_replay_evidence.py`, `test_replay_steps.py`, `replay/wiring.py`, `test_replay_wiring.py`, `test_send_guard.py`, `BrowserConfig`, `session.py`, `loader.py`, `redact.py`, `ControlWindow`, `discovery/evidence.py`, `Capability`, `host_allowed`, `Stop`, `test_after_replay_the_run_holds_no_values_given_text_or_look`?**
  _High betweenness centrality (0.046) - this node is a cross-community bridge._
- **Are the 136 inferred relationships involving `Ctx` (e.g. with `Session` and `BrowserConfig`) actually correct?**
  _`Ctx` has 136 INFERRED edges - model-reasoned connections that need verification._
- **Are the 93 inferred relationships involving `Ctx` (e.g. with `build_agent()` and `RecordWhy`) actually correct?**
  _`Ctx` has 93 INFERRED edges - model-reasoned connections that need verification._
- **Are the 83 inferred relationships involving `Look` (e.g. with `act()` and `into_box()`) actually correct?**
  _`Look` has 83 INFERRED edges - model-reasoned connections that need verification._
- **Are the 4 inferred relationships involving `make_ctx()` (e.g. with `6. Tests` and `Session`) actually correct?**
  _`make_ctx()` has 4 INFERRED edges - model-reasoned connections that need verification._