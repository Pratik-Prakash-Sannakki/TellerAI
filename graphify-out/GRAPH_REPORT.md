# Graph Report - BankerAgent  (2026-09-30)

## Corpus Check
- 155 files · ~353,083 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 2626 nodes · 5331 edges · 137 communities (123 shown, 14 thin omitted)
- Extraction: 94% EXTRACTED · 6% INFERRED · 0% AMBIGUOUS · INFERRED: 298 edges (avg confidence: 0.64)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `4785a890`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- test_cli.py
- observe
- Capability
- Capability
- Five Error Demos (D30)
- 03_recorder.py
- test_evidence.py
- test_handback_button.py
- recorder.py
- cli.py
- test_agent.py
- FakeSurface
- Replay decisions
- DiscoveryAgent
- test_schema.py
- test_models.py
- Target
- CompileError
- test_human_help.py
- agent_2_legacy_surface.py
- agent.py
- test_resolve_inputs.py
- test_takeover.py
- test_transaction_gates.py
- DECISIONS.md (design decision log)
- PlaywrightReplaySurface
- Site
- live.py
- run_capability_async
- discovery.py
- _run_async_checks
- PlaywrightReplaySurface
- Capability
- HangPage
- test_checks.py
- Look
- CLAUDE.md (project instructions)
- PHASE3.md (Recorder write-up)
- click
- manifest.json
- Path
- 04_replay_engine.py
- replay/replay.py
- take_look
- rescue
- types
- 01_browser_and_observe.py
- _literal_re
- take_look
- PlaywrightSurface
- test_choose_option.py
- Any
- FakeSurface
- test_send_settle.py
- TypeSafeToolRouterMiddleware
- test_engine.py
- LatestScreenshotOnly
- discovery2.py
- test_read_runs.py
- _MinimalAsyncSurface
- _MinimalSurface
- 05_replay_live.py
- SitePage
- Discovery decisions
- 2. Each box, with an example
- Look
- REPORT: Determinism & error handling section
- 2. Components
- ControlWindow
- Pure-Visual Discovery Notebook: Build Plan
- SiteLock
- AsyncReplaySurface
- build_typesafe_middleware
- guard_send
- run
- mk_look
- PlaywrightSurface
- human_help
- test_label_values.py
- test_extract_types.py
- test_no_values_stored.py
- test_http_errors.py
- HeldPage
- 02_artifact_schema.py
- current_value
- 4. Pure-visual discovery engine (redesign, in design)
- test_recorder.py
- test_partial_outputs.py
- _MinimalAsyncSurface
- Condition
- Coordination: discovery <-> replay
- my_cap scratch capability artifact (account 18672, log out)
- test_round_trip.py
- _unlocked
- Pause/Resume Human-in-the-Loop Smoke Test
- PlaywrightSurface.observe Design
- derived_routes (D65)
- ReplaySurface Protocol
- PHASE1.md (The Agent write-up)
- interface-ai-cua
- schema.py
- _MinimalSurface
- test_replay.py
- Condition
- ReplaySurface
- PlaywrightSurface
- test_replay_evidence.py
- test_outcomes.py
- ControlWindow
- Route
- _meta
- gather_missing_inputs
- test_control_form.py
- Replay notebook plan
- HeldRoute
- FakePage
- SiteLock
- REPORT: Artifact schema section
- pathlib
- replay_live
- test_wandering.py
- REPORT.md (assignment's 7-heading design write-up)
- .get
- asyncio
- test_sent_dropdowns.py
- malformed_template
- background.js
- walk
- D32: Agent-driven login via a type_secret(ref, name) tool
- test_extract_pattern.py
- _look_ns
- needs_human
- PHASE2.md (Artifact Schema write-up)
- run_capability
- ask_inputs
- NoopAnthropicPromptCachingMiddleware
- DoneWhileSending

## God Nodes (most connected - your core abstractions)
1. `_meta()` - 49 edges
2. `run_capability()` - 41 edges
3. `DiscoveryAgent` - 40 edges
4. `_ev()` - 37 edges
5. `CompileError` - 36 edges
6. `mk_look()` - 34 edges
7. `DECISIONS.md (design decision log)` - 32 edges
8. `FakeSurface` - 28 edges
9. `compile_run()` - 27 edges
10. `run_capability_async()` - 27 edges

## Surprising Connections (you probably didn't know these)
- `PHASE4.md (Replay Engine write-up)` --semantically_similar_to--> `D23: Verify a recorded capability by an immediate no-LLM replay before saving`  [INFERRED] [semantically similar]
  PHASE4.md → DECISIONS.md
- `test_labeled_value_in_a_click_is_rejected()` --indirect_call--> `bad_click()`  [INFERRED]
  tests/test_schema.py → notebooks/02_artifact_schema.py
- `test_locators_out_of_order_is_rejected()` --indirect_call--> `bad_order()`  [INFERRED]
  tests/test_schema.py → notebooks/02_artifact_schema.py
- `test_page_wide_index_is_rejected()` --indirect_call--> `page_wide_index()`  [INFERRED]
  tests/test_schema.py → notebooks/02_artifact_schema.py
- `test_locator_missing_note_is_rejected()` --indirect_call--> `missing_note()`  [INFERRED]
  tests/test_schema.py → notebooks/02_artifact_schema.py

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **The Five Required Error Demo Capabilities (D30)** — evidence_replay_get_account_balance_error_account_not_found_capability, evidence_replay_get_account_balance_error_slow_page_capability, evidence_replay_transfer_funds_error_element_missing_capability, evidence_replay_transfer_funds_error_session_expired_capability, evidence_replay_transfer_funds_error_transfer_over_limit_capability [EXTRACTED 0.90]
- **Sequential Phase Plan Roadmap** — docs_superpowers_plans_2026_09_19_roadmap_and_phase1, docs_superpowers_plans_2026_09_20_phase2_artifact_schema, docs_superpowers_plans_2026_09_20_phase3_recorder, docs_superpowers_plans_2026_09_22_phase2_v2_and_replay, docs_superpowers_plans_2026_09_25_phase3_recorder_v2, docs_superpowers_plans_2026_09_26_phase4_live_wiring, docs_superpowers_plans_2026_09_26_recorder_human_entry_fix [EXTRACTED 0.90]
- **Sync-Async-Live Replay Engine Stack** — docs_superpowers_plans_2026_09_22_phase2_v2_and_replay_run_capability_engine, docs_superpowers_plans_2026_09_26_phase4_live_wiring_async_mirror, docs_superpowers_plans_2026_09_26_phase4_live_wiring_playwrightreplaysurface, docs_superpowers_plans_2026_09_26_phase4_live_wiring_make_escalate [INFERRED 0.85]
- **Three Real Bugs Found Only Live Against ParaBank** — phase5_d87_label_footnote_mismatch, phase5_d88_async_content_race_polling, phase5_d89_wrong_extraction_target_total_row, phase5 [INFERRED 0.85]

## Communities (137 total, 14 thin omitted)

### Community 0 - "test_cli.py"
Cohesion: 0.10
Nodes (33): argparse, _discover_args(), _fake_extract_tool(), _fake_page(), _FakePage, _minimal_events(), _patch_agent_build(), _patch_langchain_agent() (+25 more)

### Community 1 - "observe"
Cohesion: 0.08
Nodes (47): _amount(), approval_info(), _ask_for_value(), ask_human(), _blocks(), _click(), current_page(), _describe() (+39 more)

### Community 2 - "Capability"
Cohesion: 0.17
Nodes (13): Capability, derived_routes(), from_yaml(), The pages this capability may touch, derived from its own navigate steps (D65)…, Stable, human-readable YAML. Keys keep the model's field order., What a calling agent sees: what this capability does, what it needs, what it…, to_yaml(), tool_contract() (+5 more)

### Community 3 - "Capability"
Cohesion: 0.14
Nodes (16): describe_locator(), describe_target(), InputValidationError, Exception, Target, Pure: the try-order for a target -- primary, then fallback if present (D63). No…, Async twin of resolve_target. Same try-order (`_target_locators`, a PURE…, One line naming what a locator is looking for -- used to build a clear… (+8 more)

### Community 4 - "Five Error Demos (D30)"
Cohesion: 0.08
Nodes (39): Roadmap + Phase 1 Plan, Agent-Driven Login (D32/type_secret), Deep Agent + Playwright Architecture, Phase 2 Artifact Schema Plan, Capability Schema Model, Risk-in-Artifact / Limit-in-Config Policy (D38), Phase 3 Recorder Plan (v1), Recorder COMPILE Pipeline (v1) (+31 more)

### Community 5 - "03_recorder.py"
Cohesion: 0.06
Nodes (47): langchain_agents_middleware, langchain_typesafe, langchain_typesafe_experimental_middleware, _balance_events(), _balance_events_with_agent_note(), _balance_events_with_detour(), _bare_proxy(), _canon() (+39 more)

### Community 6 - "test_evidence.py"
Cohesion: 0.08
Nodes (34): json, _as_text(), _assert_no_secret_values(), _default_label(), EvidenceWriteError, _find_repo(), _load_schema_once(), Exception (+26 more)

### Community 7 - "test_handback_button.py"
Cohesion: 0.18
Nodes (16): _click(), Ext, Human, PanelDone, parametrize, Take-over: the hand-back extension's toolbar button (its service worker, never…, The extension's service worker: a click counter and a badge., Takes over, then (optionally) clicks the toolbar button; never clicks the… (+8 more)

### Community 8 - "recorder.py"
Cohesion: 0.06
Nodes (45): Checkpoint, _canon(), _cap(), _checkpoint_from_last(), contains_literal(), _declare_human_input(), drop_detours(), find_leftovers() (+37 more)

### Community 9 - "cli.py"
Cohesion: 0.10
Nodes (26): ArgumentParser, functools, build_agent(), Build a ready-to-use `DiscoveryAgent`. If `page` is None, launches a real,…, _build_capture(), build_parser(), _capture(), _first_line() (+18 more)

### Community 10 - "test_agent.py"
Cohesion: 0.08
Nodes (34): confidence_gate(), login_check(), missing_field_labels(), Narrow base_tools to this job's tools, but only if the classifier is confident.…, Pure decision (D69): after a login click, should further attempts be blocked,…, Empty, visible, fillable fields, in page order. Pure: no browser, no network…, _agent(), Tests for `cua.agent`'s pure (or pure-enough-to-test-without-a-browser) logic,… (+26 more)

### Community 11 - "FakeSurface"
Cohesion: 0.13
Nodes (5): FakeSurface, _locator_key(), A dict-based fake DOM: pages by url, a locator registry per url, and per-ref…, A surface raises this for a step that should be retried (D26): the page was not…, TransientFailure

### Community 12 - "Replay decisions"
Cohesion: 0.09
Nodes (22): R10: where the compile step lives — DECIDED, R11: why compile, if `response_format` exists? — PROPOSED, R12: what each step type compiles to — PROPOSED, R13: target schema — PROPOSED, R14: what rung 2 needs that discovery doesn't record — DONE, R15: auto-approve at replay — PROPOSED, R16: dead ends and retries at compile — PROPOSED, R17: replay result statuses — PROPOSED (+14 more)

### Community 13 - "DiscoveryAgent"
Cohesion: 0.18
Nodes (9): DiscoveryAgent, One discovery run's worth of browser control state (D33-D62). All state that…, Every button except a short safe list needs a human. Links (navigation) run…, Best available description of an element (D53): the code's own name, the…, Read whatever is currently in this field, live from the page (D54)., Package text and a screenshot as one tool result the model can read., Give the live browser to a human. Returns when they click 'Done', OR, if…, The agent tried to enter a value the user never gave. Hand the browser to a… (+1 more)

### Community 14 - "test_schema.py"
Cohesion: 0.07
Nodes (51): check_result(), derived_routes(), The pages this capability may touch, derived from its own navigate steps (D65)…, What a calling agent sees: what this capability does, what it needs, what it…, Check a result against the capability that produced it. Raises ValueError on a…, tool_contract(), bal(), _bal_data_with_three_outcome_rules() (+43 more)

### Community 15 - "test_models.py"
Cohesion: 0.11
Nodes (22): CaptureFixture, build_langchain_agent(), Wrap a tool list in a deep agent (D4) with the standard checkpointer. Kept as a…, cua: computer-use automation -- discovery agent, capability artifact schema,…, _clean_env(), fixture, MonkeyPatch, Offline tests for `cua.models.make_chat_model` (Iliad gateway). No network, no… (+14 more)

### Community 16 - "Target"
Cohesion: 0.08
Nodes (30): derive_target(), _extract_target(), Target, D68: `label` and `labeled_value` locators have no `within` slot in the schema.…, Descriptor -> Target(primary, fallback). role+name (high, only when the name is…, D101: a `labeled_value` extract step whose CAPTURED resolution is itself a…, _refuse_if_duplicate_label(), _refuse_if_header_value() (+22 more)

### Community 17 - "CompileError"
Cohesion: 0.12
Nodes (24): _cap(), _check_specs(), _checkpoint_from_last(), clean_events(), compile_run(), CompileError, drop_dead_end_risky_clicks(), drop_detours() (+16 more)

### Community 18 - "test_human_help.py"
Cohesion: 0.11
Nodes (20): Control, Lock, _no_watch(), Page, parametrize, human_help: one open-ended panel -> answer in words, take over, or stop., Run human_help's take-over; `during(page)` is what the human does before…, Live crash: Register (a form POST) held by guard_send -> shot_after timed out… (+12 more)

### Community 19 - "agent_2_legacy_surface.py"
Cohesion: 0.08
Nodes (29): dataclasses, LegacyLocator, LegacyStrategy, AccessibleNameLocator, AnchorLocator, DriftLog, FakeLegacyPage, LegacyElement (+21 more)

### Community 20 - "agent.py"
Cohesion: 0.11
Nodes (23): BaseChatModel, ModelKind, os, job_tool_names(), page_name_from_url(), The discovery agent: deep agents + Playwright tools, safety/lock/takeover…, Tools this job needs, plus the always-allowed set. Pure: no network, no LLM., Page name from the URL: no query, no ;jsessionid=, no trailing slash, lower… (+15 more)

### Community 21 - "test_resolve_inputs.py"
Cohesion: 0.12
Nodes (23): _ask(), _cap(), ClearPage, _click(), env(), FakeForm, FakePage, fixture (+15 more)

### Community 22 - "test_takeover.py"
Cohesion: 0.41
Nodes (11): _cap(), _click(), _fail_clicks(), A take-over is recorded as evidence (shots, page paths, send paths, no values)…, Live: the human finished the whole form during a take-over; step 6 then 'target…, test_checkpoint_reached_by_the_human_skips_the_remaining_steps(), test_click_stashes_the_dropdowns_before_clicking(), test_no_take_over_means_an_empty_list() (+3 more)

### Community 23 - "test_transaction_gates.py"
Cohesion: 0.10
Nodes (35): Control, _guard_ns(), _held_navigation(), HeldPage, _no_dropdowns(), _opts(), parametrize, guard_send: nothing that sends data leaves the tab without two human approvals. (+27 more)

### Community 24 - "DECISIONS.md (design decision log)"
Cohesion: 0.10
Nodes (22): examples/get_account_balance.yaml (hand-written illustrative example), DECISIONS.md (design decision log), D10: Business/Recoverable/Hard three-way error taxonomy, D12: Typed, locator-based output extraction, D13: get_account_balance (safe) + transfer_funds (risky) demo flows, D18: Cover sensitive fields before screenshot capture, D19: Six triggers for detecting a discovery agent is stuck, D1: Target Application = ParaBank (+14 more)

### Community 25 - "PlaywrightReplaySurface"
Cohesion: 0.14
Nodes (8): describe_ref(), host_allowed(), LabeledValueRef, PlaywrightReplaySurface, A `resolve()` result for a `labeled_value` locator: not a numbered element ref…, Implements AsyncReplaySurface (04_replay_engine.py Section 7) against the real…, One resolution attempt, no retry -- the exact logic `resolve()` used before D88., D78: for `labeled_value`, go straight to READ_LABELED_JS (no numbered scan at…

### Community 26 - "Site"
Cohesion: 0.11
Nodes (7): Ext, _load(), Lock, The site tab: a still screen unless `screen` changes; fires framenavigated.…, The hand-back extension's service worker: a click counter and a badge. Never…, Site, Win

### Community 27 - "live.py"
Cohesion: 0.10
Nodes (28): InputParam, gather_missing_inputs(), make_escalate(), missing_required_inputs(), _prompt_for_missing_input(), Capability, ReplayResult, Wires the async replay engine (`cua.replay.run_capability_async`) to a REAL… (+20 more)

### Community 28 - "run_capability_async"
Cohesion: 0.13
Nodes (21): AsyncFakeSurface, _call_escalate(), _check_outcomes(), _check_outcomes_async(), condition_matches(), _fail(), _find_outcome_rule(), parse_amount() (+13 more)

### Community 29 - "discovery.py"
Cohesion: 0.08
Nodes (46): after_login_click(), Anchor, build_capability(), Capability, CapabilityMeta, checkpoint(), _clean(), Config (+38 more)

### Community 30 - "_run_async_checks"
Cohesion: 0.36
Nodes (6): new_happy_async_surface(), new_happy_surface(), no_secrets(), resolve_secret(), _run_async_checks(), _run_async_integration()

### Community 31 - "PlaywrightReplaySurface"
Cohesion: 0.14
Nodes (6): LabeledValueRef, PlaywrightReplaySurface, A `resolve()` result for a `labeled_value` locator: not a numbered element ref…, Implements `AsyncReplaySurface` (`cua.replay`) against the real browser. Wraps…, One resolution attempt, no retry -- the exact logic `resolve()` used before D88., D78: for `labeled_value`, go straight to READ_LABELED_JS (no numbered scan at…

### Community 32 - "Capability"
Cohesion: 0.08
Nodes (42): act(), ask_option(), choose_option(), do_click(), do_navigate(), do_scroll(), do_select(), do_type() (+34 more)

### Community 33 - "HangPage"
Cohesion: 0.12
Nodes (13): FormRoute, HangPage, NeverAnsweredGate, take_look screenshots the page, as the real one does., `evaluate` also never returns while a request is held, as live., Answers each gate from a script; records what each form offered., The human clicks Done while their own send's Gate 1 is still open and never…, _real_shots() (+5 more)

### Community 34 - "test_checks.py"
Cohesion: 0.14
Nodes (19): _click_env(), _form_png(), _Lock, _Page, parametrize, Step checks on fakes: whole-field read (A), tolerant word match (B), late page…, Live bug: the Transfer click sent (both gates approved) but its check said…, Live: Address '1' failed twice: OCR does not read a lone character. The field's… (+11 more)

### Community 35 - "Look"
Cohesion: 0.10
Nodes (29): anchor_point(), Box, canvas(), crop_box(), Element, element_at(), field_box(), fill() (+21 more)

### Community 36 - "CLAUDE.md (project instructions)"
Cohesion: 0.21
Nodes (12): balance_check capability artifact, get_account_balance capability artifact (D89 hand-edited), get_account_balance_discovery_demo capability artifact, CLAUDE.md (project instructions), D101: labeled_value refuses a table-header resolution (general fix), D102: label_header/value_header flags ported into agent.py + cli.py capture path, D92: Evidence Capture Helpers (save_discovery_evidence/save_replay_evidence), D95: Missing create_deep_agent import found live in BROWSER 12 (+4 more)

### Community 37 - "PHASE3.md (Recorder write-up)"
Cohesion: 0.18
Nodes (12): my_def pay-bill capability artifact (electricity company), PHASE3.md (Recorder write-up), D41-D49: original recorder design (superseded by v2 rebuild), D42: Locator derivation only trusts a real accessible name for role locators, D43: Dropping dead-end click detours from the recording, D44: Turning matched literal values into {{inputs}}, D46: extraction limited to labeled values (known limit), D47: business-outcome rule derived from a deliberate bad-input probe run (+4 more)

### Community 38 - "click"
Cohesion: 0.10
Nodes (45): act(), blocks(), choose_option(), click(), finish_business_outcome(), gate_click(), host_allowed(), human_fills() (+37 more)

### Community 39 - "manifest.json"
Cohesion: 0.11
Nodes (18): action, default_icon, default_title, background, service_worker, 128, 16, 32 (+10 more)

### Community 40 - "Path"
Cohesion: 0.11
Nodes (23): _clean(), find(), finish(), given_inputs(), load_outcomes(), _png(), Path, Evidence screenshot. A held form POST blocks `page.screenshot()`: give up,… (+15 more)

### Community 41 - "04_replay_engine.py"
Cohesion: 0.13
Nodes (15): inspect, describe_locator(), describe_target(), InputValidationError, load_schema(), matches_value_type(), Exception, Neither the primary nor the fallback locator resolved to an element. (+7 more)

### Community 42 - "replay/replay.py"
Cohesion: 0.12
Nodes (28): Config, discovery_schema(), do_extract(), dropdown_options(), _flat(), guard_send(), hide_secrets(), is_sensitive() (+20 more)

### Community 43 - "take_look"
Cohesion: 0.17
Nodes (18): changed(), decode(), draw_numbered(), encode(), find_template(), mask_png(), ocr(), open_start() (+10 more)

### Community 44 - "rescue"
Cohesion: 0.18
Nodes (12): Future, button_clicked(), ext_call(), hand_back(), handback_button(), R19: one bounded call into the hand-back extension's service worker, never the…, Returns once the toolbar button's click count rises above where it was at the…, Badge YOU while the human is in control; yields the task a toolbar click… (+4 more)

### Community 45 - "types"
Cohesion: 0.20
Nodes (12): _cls(), LatestScreenshotOnly keeps only the newest image in the model's context., _shot(), test_only_last_image_survives(), _load(), _look(), ndarray, SimpleNamespace (+4 more)

### Community 46 - "01_browser_and_observe.py"
Cohesion: 0.13
Nodes (10): base64, format_elements(), Observation, PlaywrightSurface, Independent check of the balance, used only to grade the agent., The only place that touches Playwright. Agent tools talk to this., Look up a secret by name. Raises on unknown name or empty value., read_balance_ground_truth() (+2 more)

### Community 47 - "_literal_re"
Cohesion: 0.17
Nodes (12): contains_literal(), _declare_human_input(), _literal_re(), _params(), The literal, but not inside a longer word or number: '5' is not found in '$50'…, Replace declared literals with {{name}}. Longest literal first, so a longer…, Address:' -> 'address', 'Zip Code:' -> 'zip_code', 'Phone #:' -> 'phone'.…, D90: a human-entered value that matches no already-declared input gets its OWN… (+4 more)

### Community 48 - "take_look"
Cohesion: 0.11
Nodes (24): Box, canvas(), crop_box(), cut_crop(), decode(), draw_numbered(), encode(), _img() (+16 more)

### Community 49 - "PlaywrightSurface"
Cohesion: 0.12
Nodes (9): format_elements(), Observation, PlaywrightSurface, The only place that touches Playwright directly. Agent tools talk to this., The single unlocked click path every automated click (agent tool or replay)…, Run one Playwright action with the general lock removed for just that instant…, _unlocked(), test_format_elements_shows_current_value_and_below_the_fold() (+1 more)

### Community 50 - "test_choose_option.py"
Cohesion: 0.22
Nodes (11): _fns(), Page, Dropdowns (option B): read every option and select by value, for the <select>…, Mimics SELECT_AT_JS against one <select> at (100, 50); nothing else on the page., The user's bug: two accounts, only one showed., The red box showed the whole tool reply (URL, every OCR line) instead of the…, test_lists_every_option_values_only(), test_missing_option_is_refused() (+3 more)

### Community 51 - "Any"
Cohesion: 0.15
Nodes (7): _AsyncDictSurface, _DictSurface, _is_approved(), Any, Just enough of a surface to test resolve_target in isolation: resolve(locator)…, Pure: what a risky click's `escalate(reason, ctx)` return value means (D85).…, Async twin of _DictSurface (Section 3b).

### Community 52 - "FakeSurface"
Cohesion: 0.10
Nodes (3): AsyncFakeSurface, FakeSurface, _locator_key()

### Community 53 - "test_send_settle.py"
Cohesion: 0.23
Nodes (7): _act(), _none(), Page, D: after an approved send, act waits for the page's response before its…, The response lands 3 polls after the gate is released., test_after_an_approved_send_the_look_shows_the_response(), test_no_send_means_no_extra_wait()

### Community 54 - "TypeSafeToolRouterMiddleware"
Cohesion: 0.20
Nodes (7): confidence_gate(), job_tool_names(), AgentMiddleware, Tools this job needs, plus the always-allowed set. Pure: no network, no LLM., Narrow base_tools to this job's tools, but only if the classifier is confident.…, Classifies the step's job with TypeSafe's Choice primitive and narrows the tool…, TypeSafeToolRouterMiddleware

### Community 55 - "test_engine.py"
Cohesion: 0.25
Nodes (16): _cap(), _click(), engine(), FakeControl, fixture, The step loop on a fake page: success, one retry, never re-send, stuck on a…, ns with a fake page: `take_look` returns the fixed look; actions are scripted., _script() (+8 more)

### Community 56 - "LatestScreenshotOnly"
Cohesion: 0.24
Nodes (5): LatestScreenshotOnly, NoopAnthropicPromptCachingMiddleware, AgentMiddleware, Disable prompt caching on the Iliad gateway; it rejects Anthropic cache markers., Old screenshots are stale (their numbers no longer work); send the model only…

### Community 57 - "discovery2.py"
Cohesion: 0.07
Nodes (31): deepagents, dotenv, langchain_tools, langgraph_checkpoint_memory, ask_human(), BrowserSurface, build_agent(), click() (+23 more)

### Community 58 - "test_read_runs.py"
Cohesion: 0.15
Nodes (23): _cell(), _look(), _ns(), Read-only runs (live: view_account_details_and_transactions): the checkpoint…, Live: available_amount got row_key 'Transfer Funds', column 'Welcome to Account…, Menu gap == column gap: nothing tells them apart, so no row key (the anchor is…, Only text seen on that look can be the checkpoint: an event with no page_texts…, Live: row_key 'Transfer Funds' (menu), column 'Accounts Overview' (title);… (+15 more)

### Community 61 - "05_replay_live.py"
Cohesion: 0.19
Nodes (9): langgraph_types, _find_repo_for_engine(), _find_repo_for_evidence(), load_evidence_capture(), load_replay_engine(), Path, Exec the non-check cells of 04_replay_engine.py into this namespace -- the same…, Runs the SAME DECISION_JS bar agent.ipynb's click() tool shows. The general… (+1 more)

### Community 62 - "SitePage"
Cohesion: 0.18
Nodes (5): env(), Lock, fixture, The site page: any call made on it for the button is a bug., SitePage

### Community 63 - "Discovery decisions"
Cohesion: 0.09
Nodes (21): Base decisions, Discovery decisions, Q10: window size and zoom — DECIDED, Q11: notebook format — DECIDED, Q12: dropdowns — DECIDED, Q13: scrolling — DECIDED, Q14: private data in saved pictures — DECIDED, Q15: sitemap before discovery — DECIDED (+13 more)

### Community 64 - "2. Each box, with an example"
Cohesion: 0.12
Nodes (15): 1. Diagram, 2. Each box, with an example, 3. All tools, 4. Step by step: one discovery run, 5. Notes, Browser (Playwright), Control window and site lock (Q-A), Discovery architecture (+7 more)

### Community 65 - "Look"
Cohesion: 0.11
Nodes (34): clean_label(), column_header(), Element, element_at(), extract_value(), headings(), is_word(), label_near() (+26 more)

### Community 66 - "REPORT: Determinism & error handling section"
Cohesion: 0.22
Nodes (11): transfer_funds capability artifact (top-level, real captured), D23: Verify a recorded capability by an immediate no-LLM replay before saving, D27: Four-status ReplayResult contract (SUCCESS/BUSINESS_OUTCOME/NEEDS_APPROVAL/FAILED), PHASE4.md (Replay Engine write-up), D77: AsyncReplaySurface / run_capability_async async mirror of the sync engine, PHASE5.md (Replay Against the Real Browser write-up), D85: escalate's return value, not a side effect, decides the click, D87: label normalization must strip a trailing footnote character (+3 more)

### Community 67 - "2. Components"
Cohesion: 0.12
Nodes (15): 1. Diagram, 2. Components, 3. Step types, 4. Worked example: ParaBank login + read balance, 5. Notes, Actor, Artifact (made by discovery, not replay), Browser setup (+7 more)

### Community 68 - "ControlWindow"
Cohesion: 0.17
Nodes (8): ControlWindow, Our own page: the only place a human answers. Closing it fails closed (None)., Answers the question on top. Closing the window (None) answers every one: fail…, Answers the newest open question of this mode, wherever it sits on the stack., A new question supersedes the one on screen (e.g. a gate during a take-over);…, One labelled input per field (label, masked), optionally prefilled. A dropdown…, A dropdown becomes a real <select> of its options; anything else a…, _row()

### Community 69 - "Pure-Visual Discovery Notebook: Build Plan"
Cohesion: 0.09
Nodes (22): 10. Open risks, 1. Global constraints (every task must follow these), 2. Review focus (inputs no spec line covers, but likely to bite), 3. What already exists (reuse, or its visual version), 3a. How the agent is built today (`agent.ipynb` STEP 4, `src/cua/agent.py`), 3b. Existing handoff rules: when a human is called in, 3c. Existing tools → the new tools, 4. New dependencies (checked on PyPI, 2026-09-28) (+14 more)

### Community 71 - "AsyncReplaySurface"
Cohesion: 0.08
Nodes (13): AsyncReplaySurface, _find_repo(), Path, Protocol, Pure: the try-order for a target -- primary, then fallback if present (D63). No…, Try the primary locator, then the fallback if there is one and the primary did…, What a real Playwright-backed surface will implement in Phase 9 (see the…, The async twin of ReplaySurface (Section 2). Same method names, same meanings… (+5 more)

### Community 72 - "build_typesafe_middleware"
Cohesion: 0.27
Nodes (10): build_typesafe_middleware(), Build the D50/D52 TypeSafe middleware list (tool router + model router),…, No TYPESAFE_API_KEY in the environment: returns [] -- the caller's agent then…, THE fix under test: when TYPESAFE_API_KEY is set, this must build the SAME two…, D76's extension must actually reach the constructed middleware, not just exist…, test_build_typesafe_middleware_builds_both_layers_when_key_set(), test_build_typesafe_middleware_empty_key_is_also_off(), test_build_typesafe_middleware_extra_never_hide_reaches_the_tool_router() (+2 more)

### Community 73 - "guard_send"
Cohesion: 0.14
Nodes (18): dropdown_options(), _flat(), guard_send(), hide_secrets(), is_sensitive(), _json(), list_options(), mismatches() (+10 more)

### Community 74 - "run"
Cohesion: 0.13
Nodes (15): take_over's hand-back: the extension's toolbar button (never the site), with no…, The user's rule: no "are you done?" prompts in between. Only the take-over…, test_a_click_on_the_toolbar_button_hands_back(), test_done_in_the_takeover_itself_cancels_the_watcher(), test_no_extension_still_hands_back_from_the_control_tab(), test_no_idle_reminder_ever_interrupts_the_take_over(), test_the_badge_reads_you_during_the_take_over_then_ai(), test_the_button_never_touches_the_site_page() (+7 more)

### Community 75 - "mk_look"
Cohesion: 0.23
Nodes (14): mk_look(), mk_look([(text, (x1, y1, x2, y2)), ...]) -> a Look with those OCR elements., _dup_target(), The 3 rungs + table cell; all miss -> None., test_a_single_text_match_is_rung1_as_before(), test_all_miss_is_none(), test_duplicate_text_picks_the_copy_nearest_the_anchor(), test_duplicate_text_with_no_copy_near_the_anchor_uses_rung2() (+6 more)

### Community 76 - "PlaywrightSurface"
Cohesion: 0.22
Nodes (5): approval_info(), format_elements(), Observation, PlaywrightSurface, The only place that touches Playwright. Agent tools talk to this.

### Community 77 - "human_help"
Cohesion: 0.11
Nodes (20): ask_human(), ext_call(), HandoffState, human_help(), mark_stuck(), note_call(), offer_control(), Ask a human whenever you are unsure: what to do, which option, what the goal… (+12 more)

### Community 78 - "test_label_values.py"
Cohesion: 0.17
Nodes (17): re, _look_ns(), parametrize, OCR joins a label to the dropdown beside it ('to account #16785') and reads its…, Live: steps 5-6 (agent, 'From account #[') and 7-8 (send, 'From account #')…, _select(), _sent(), test_a_box_border_read_as_a_bracket_is_not_part_of_the_label() (+9 more)

### Community 79 - "test_extract_types.py"
Cohesion: 0.29
Nodes (10): _cap(), _extract(), parametrize, Replay's own strict value types for extracts: an account number is never a…, test_an_account_number_cell_for_a_currency_output_stops(), test_an_integer_or_id_is_not_currency(), test_currency_needs_a_dollar_or_two_decimals(), test_the_next_rung_is_tried_once_on_a_type_mismatch() (+2 more)

### Community 80 - "test_no_values_stored.py"
Cohesion: 0.36
Nodes (5): Call, _arg_keys(), _log_calls(), Banking rule: no typed or human-given value is stored. Source-level checks on…, test_typed_and_selected_values_never_reach_the_log()

### Community 81 - "test_http_errors.py"
Cohesion: 0.18
Nodes (12): _judge(), Page, parametrize, Navigate joins paths like a browser; an HTTP error page is FAILED, never a…, Resp, test_a_200_page_with_not_found_text_is_still_a_business_outcome(), test_a_404_navigation_is_failed_not_a_business_outcome(), test_a_normal_page_passes() (+4 more)

### Community 82 - "HeldPage"
Cohesion: 0.33
Nodes (4): HeldPage, HumanControlSimple, Like Playwright: while a form POST (a navigation) is held, `page.screenshot()`…, test_take_over_survives_a_screenshot_timeout()

### Community 83 - "02_artifact_schema.py"
Cohesion: 0.05
Nodes (56): copy, bad_amount(), bad_click(), bad_order(), check_result(), Click, Dismiss, Extract (+48 more)

### Community 84 - "current_value"
Cohesion: 0.40
Nodes (4): current_value(), Read whatever is currently in this field, live from the page. Empty string if…, The value shown next to `label` on the current page. Raises LookupError if…, read_labeled_value()

### Community 85 - "4. Pure-visual discovery engine (redesign, in design)"
Cohesion: 0.20
Nodes (9): 1. High-level component architecture, 2. How discovery actually happens (sequence), 3. The clean-DOM gap, explicitly, 4. Pure-visual discovery engine (redesign, in design), Architecture: Agent + Discovery Pipeline, Decided (user-confirmed), Discovery engine — block diagram, Open questions (NOT decided) (+1 more)

### Community 86 - "test_recorder.py"
Cohesion: 0.08
Nodes (52): classify_status(), clean_events(), compile_run(), drop_dead_end_risky_clicks(), _key(), _meaningful(), Bucket a tool result's own text by the EXACT prefixes agent.ipynb's tools…, Keep only actions that worked and mattered. Returns (kept, dropped). dropped =… (+44 more)

### Community 87 - "test_partial_outputs.py"
Cohesion: 0.35
Nodes (12): _cap(), _click(), env(), _extract(), _finish(), fixture, Every status returns what was read. A read-only run whose checkpoint was picked…, test_a_failed_run_still_returns_what_it_read() (+4 more)

### Community 89 - "Condition"
Cohesion: 0.14
Nodes (14): OutcomeRule, D10/D47: a bad-input run ended with finish_business_outcome(outcome,…, relogin_rule(), rule_from_probe(), Checkpoint, Condition, OutcomeRule, model_validator (+6 more)

### Community 90 - "Coordination: discovery <-> replay"
Cohesion: 0.20
Nodes (9): Blockers for the user, Coordination: discovery <-> replay, Discovery (`notebooks/discovery/`, orchestrator ac2ad3f302f5be3b5; p1 builder a9cc1291cca0102fb done, p4 builder a4b8ff70020b5454d done), Duplication (watch list), Mismatches, Replay (`notebooks/replay/`, orchestrator a0245948081e7b9c1), Rule checks (discovery parts, check #3), Shared contract (+1 more)

### Community 92 - "test_round_trip.py"
Cohesion: 0.39
Nodes (7): Path, Discovery's saved artifact runs in replay unchanged: build -> save -> load ->…, _saved(), test_crop_paths_resolve_to_saved_files(), test_rung2_offset_hits_the_point_discovery_acted_on(), test_saved_artifact_loads_as_is(), test_steps_dispatch_to_replay_handlers()

### Community 93 - "_unlocked"
Cohesion: 0.33
Nodes (4): _click(), Run one Playwright action with the general lock (Setup 5) removed for just that…, _type_text(), _unlocked()

### Community 100 - "schema.py"
Cohesion: 0.11
Nodes (30): pydantic, _amount_input(), build_steps(), _check_specs(), CompileError, Exception, Events -> (steps, outputs, secrets, paths). Adds a navigate for the start page,…, The recording cannot become a valid capability. `.problems` lists every reason. (+22 more)

### Community 102 - "test_replay.py"
Cohesion: 0.15
Nodes (30): from_yaml(), balance_cap(), pay_bill(), fixture, new_happy_async_surface(), new_happy_surface(), no_secrets(), Tests for `cua.replay` (sync + async engines), ported from… (+22 more)

### Community 103 - "Condition"
Cohesion: 0.19
Nodes (9): Checkpoint, Condition, OutcomeRule, model_validator, The final success check. Both signals must agree (D9)., When `when` matches after a step, treat the page as a business outcome, a…, D10/D47: a bad-input run ended with finish_business_outcome(outcome,…, relogin_rule() (+1 more)

### Community 104 - "ReplaySurface"
Cohesion: 0.11
Nodes (10): Protocol, Try the primary locator, then the fallback if there is one and the primary did…, What a real Playwright-backed surface implements…, ReplaySurface, resolve_target(), _DictSurface, Any, test_resolve_target_both_miss_raises_naming_both() (+2 more)

### Community 105 - "PlaywrightSurface"
Cohesion: 0.29
Nodes (4): format_elements(), Observation, PlaywrightSurface, The only place that touches Playwright. Agent tools talk to this.

### Community 106 - "test_replay_evidence.py"
Cohesion: 0.27
Nodes (9): _all_text(), _png(), save_evidence writes one masked folder per run: summary, drift, failure (only…, _result(), test_all_files_are_written(), test_checkpoint_miss_carries_expected_and_observed(), test_failure_json_has_step_expected_observed(), test_no_failure_file_on_success() (+1 more)

### Community 107 - "test_outcomes.py"
Cohesion: 0.08
Nodes (39): _cap(), FakeForm, replay(path, inputs): given values by exact name (any case); unknown keys stop;…, test_all_inputs_given_means_no_form(), test_given_inputs_match_by_exact_name_any_case(), test_only_the_missing_inputs_go_to_the_one_form(), test_replay_stops_on_an_unknown_key_before_opening_the_site(), test_unknown_key_stops_naming_what_is_accepted() (+31 more)

### Community 108 - "ControlWindow"
Cohesion: 0.33
Nodes (4): ControlWindow, _img(), Our own page: the only place a human answers. Closing it fails closed (None)., _row()

### Community 109 - "Route"
Cohesion: 0.22
Nodes (5): test_the_gate_marks_a_human_approved_send(), HumanControl, Takes over; while 'in control', the human opens a page and sends a form., Route, test_sends_are_noted_only_during_a_take_over()

### Community 110 - "_meta"
Cohesion: 0.11
Nodes (40): _click(), Live: find_accounts_and_transactions.yaml saved `outputs: []`, no extract, and…, navigated: the page loaded (a link, even back to the same URL); new: new text…, After login the site is already on Accounts Overview; clicking it, scrolling,…, The page heading 'Accounts Overview' sits above the menu link with the same…, test_a_click_that_changes_the_screen_on_the_same_page_is_kept(), test_a_click_that_lands_on_the_page_it_left_is_dropped(), test_a_read_or_a_send_is_enough() (+32 more)

### Community 111 - "gather_missing_inputs"
Cohesion: 0.33
Nodes (6): gather_missing_inputs(), missing_required_inputs(), _prompt_for_missing_input(), Pure, standalone, offline-testable: which of `cap.inputs` (the Phase 2 schema's…, Prompt for exactly one missing required input, showing its own `.description`…, The pre-flight gate itself. Runs BEFORE anything else in `replay_live` -- no…

### Community 112 - "test_control_form.py"
Cohesion: 0.15
Nodes (8): FakeWin, ControlWindow: form answers, and a newer question supersedes then restores the…, Regression: a gate during a take-over must win, then hand the take-over back…, test_closing_the_window_fails_every_question_closed(), test_dropdown_row_lists_every_option(), test_form_returns_answers_and_masks_sensitive(), test_gate_supersedes_takeover_then_restores_it(), _window()

### Community 113 - "Replay notebook plan"
Cohesion: 0.33
Nodes (5): Decisions made here (review), Open questions for the user, Replay notebook plan, Sections, Tasks

### Community 114 - "HeldRoute"
Cohesion: 0.25
Nodes (3): GateControl, HeldRoute, test_navigation_send_never_screenshots_and_the_gate_shows()

### Community 115 - "FakePage"
Cohesion: 0.18
Nodes (5): env(), FakeLock, FakePage, Frame, fixture

### Community 117 - "REPORT: Artifact schema section"
Cohesion: 0.40
Nodes (5): examples/transfer_funds.yaml (hand-written illustrative example), D20: $500 auto-approve threshold for risky transfer/click actions, D8: Ranked locator strategy (role > label > text > structure), D9: Checkpoint requires both URL and text-content match, REPORT: Artifact schema section

### Community 118 - "pathlib"
Cohesion: 0.12
Nodes (16): pathlib, pytest, stmt, _fake_llm_keys(), fixture, MonkeyPatch, Suite-wide: never let a real LLM key from `.env` reach a test (cua.config loads…, A fake Iliad key so code that builds a chat model works offline; no real key is… (+8 more)

### Community 119 - "replay_live"
Cohesion: 0.33
Nodes (6): make_escalate(), Load a capability YAML and replay it for real, printing the result. `secrets`…, Look up a secret by name. Raises on unknown name or empty value., Returns an escalate(reason, ctx) closure for this one capability. Passed as…, replay_live(), resolve_secret()

### Community 120 - "test_wandering.py"
Cohesion: 0.17
Nodes (18): _go(), _nav(), _open_path(), _paths(), parametrize, Live run 'Log in, bank phone number' (navigate_to_request_loan.yaml): a 404 and…, _shapes(), test_a_404_and_detour_navigations_are_dropped() (+10 more)

### Community 121 - "REPORT.md (assignment's 7-heading design write-up)"
Cohesion: 0.25
Nodes (9): D99: TypeSafe tool/model-router middleware ported into src/cua, D14: page.pause() wrapped with a control-state + intervention-request model, D16: Single redact() choke point for secrets/PII in logs and artifacts, D21: Base capability + per-tenant overrides, with a drift signal, D64: app/vendor/base/overrides multi-tenant fields cut from schema, REPORT.md (assignment's 7-heading design write-up), REPORT: Cuts section, REPORT: Escalation & handoff section (+1 more)

### Community 122 - ".get"
Cohesion: 0.14
Nodes (20): field_area(), goes_to_a_page(), is_select(), log_sent_dropdowns(), needed_moves(), no_op(), C: the agent logs out to leave the site clean. Banking safety (user,…, R16: drop failures, keep the last success per field. Refuse a take-over. (+12 more)

### Community 123 - "asyncio"
Cohesion: 0.25
Nodes (4): asyncio, FakeBox, into_box clears the field before typing, so a retry replaces instead of…, test_typing_twice_does_not_double()

### Community 124 - "test_sent_dropdowns.py"
Cohesion: 0.29
Nodes (9): _logged(), Path, A dropdown the send carries becomes a Select step, even when left on its page…, test_a_defaulted_dropdown_the_send_carries_is_logged_without_its_value(), test_a_dropdown_the_send_does_not_carry_is_not_a_step(), test_a_select_the_agent_made_earlier_is_not_doubled(), test_it_becomes_a_select_input_before_the_send_click(), urllib_parse (+1 more)

### Community 125 - "malformed_template"
Cohesion: 0.33
Nodes (6): malformed_template(), Return (is_secret, name) for every {{...}} reference in text., True if text contains a '{{' that is not a valid reference, e.g. {{Account}}., template_refs(), test_malformed_template(), test_template_refs()

### Community 127 - "walk"
Cohesion: 0.18
Nodes (14): is_cleanup(), norm(), Step i ended in a take-over, and the human went on to the final screen: the…, The main steps (every step not marked cleanup), then the checkpoint and the…, R17: a read-only run whose last main step read the last output, and every…, Exact for anything with a digit (13344 is not 13345); fuzzy for words (PLAN P3)., Rung 2 anchors only. Discovery saves labels cleaned ('to account #'); live OCR…, R5: bounded OCR poll until the text is on screen. (+6 more)

### Community 128 - "D32: Agent-driven login via a type_secret(ref, name) tool"
Cohesion: 0.33
Nodes (6): login_parabank capability artifact, D11/D17: Separate login helper reading .env (superseded by D32), D15: Domain+route+action allowlist enforced in tool code before Playwright acts, D32: Agent-driven login via a type_secret(ref, name) tool, D45: split_login() separates login into its own reusable capability, REPORT: Safety section

### Community 129 - "test_extract_pattern.py"
Cohesion: 0.29
Nodes (9): _cap(), _extract(), parametrize, An extract's optional `pattern` cuts the value out of a longer box;…, test_a_no_match_tries_the_next_rung_first(), test_a_pattern_extracts_the_phone_from_the_sentence(), test_an_old_artifact_without_a_pattern_is_unchanged(), test_new_types_accept_and_reject() (+1 more)

### Community 130 - "_look_ns"
Cohesion: 0.33
Nodes (6): _look_ns(), Live bug: 'From account #' dropdown showing '74838' was saved as input…, Live bug: 'Sean' typed into Payee Name became the Address step's label and…, test_a_dropdowns_own_number_is_never_its_label(), test_a_typed_value_above_is_never_the_next_fields_label(), test_where_records_label_box_ordinal_offset_but_not_the_box_contents()

### Community 131 - "needs_human"
Cohesion: 0.40
Nodes (5): _amount(), human_takeover(), needs_human(), Give the live browser to a human. Returns when they click 'Done', OR, if…, Every button except a short safe list needs a human. Links (navigation) run…

### Community 132 - "PHASE2.md (Artifact Schema write-up)"
Cohesion: 0.18
Nodes (11): D93: Pre-existing 02_artifact_schema.py IndexError bug, D31: Offline unit tests only, no live E2E test in CI, D6: Replay is a plain deterministic engine, not an agent, PHASE2.md (Artifact Schema write-up), D63: Target simplified to primary + one optional fallback, D65: routes derived from navigate steps, not separately stored, D66: when_to_use folded into description as one field, D67: element-with-no-accessible-name honest gap (+3 more)

### Community 133 - "run_capability"
Cohesion: 0.09
Nodes (40): Condition, Failure, AsyncReplaySurface, _call_escalate(), _check_outcomes(), _check_outcomes_async(), condition_matches(), _fail() (+32 more)

### Community 134 - "ask_inputs"
Cohesion: 0.40
Nodes (5): ask_inputs(), Every `{{input}}` the steps use, in step order, once each., R8: ONE form before step 1 for every input the caller did not give. Nothing is…, step_inputs(), test_no_cleanup_when_stopped_before_step_1()

### Community 135 - "NoopAnthropicPromptCachingMiddleware"
Cohesion: 0.40
Nodes (3): NoopAnthropicPromptCachingMiddleware, AgentMiddleware, Disable Anthropic prompt-caching on the Iliad gateway. The gateway rejects the…

### Community 136 - "DoneWhileSending"
Cohesion: 0.40
Nodes (3): DoneWhileSending, The human clicks Done just as their form POST is held: the gate must still show…, test_no_deadlock_between_a_pending_gate_and_done()

## Knowledge Gaps
- **132 isolated node(s):** `MODES`, `manifest_version`, `name`, `version`, `description` (+127 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **14 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `FakeSurface` connect `FakeSurface` to `04_replay_engine.py`, `_run_async_checks`?**
  _High betweenness centrality (0.022) - this node is a cross-community bridge._
- **Why does `PlaywrightSurface` connect `PlaywrightSurface` to `05_replay_live.py`?**
  _High betweenness centrality (0.014) - this node is a cross-community bridge._
- **Why does `DiscoveryAgent` connect `DiscoveryAgent` to `test_cli.py`, `build_typesafe_middleware`, `cli.py`, `test_agent.py`, `PlaywrightSurface`, `agent.py`, `live.py`, `PlaywrightReplaySurface`?**
  _High betweenness centrality (0.013) - this node is a cross-community bridge._
- **Are the 3 inferred relationships involving `DiscoveryAgent` (e.g. with `LabeledValueRef` and `PlaywrightReplaySurface`) actually correct?**
  _`DiscoveryAgent` has 3 INFERRED edges - model-reasoned connections that need verification._
- **What connects `MODES`, `manifest_version`, `name` to the rest of the system?**
  _132 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `test_cli.py` be split into smaller, more focused modules?**
  _Cohesion score 0.1 - nodes in this community are weakly interconnected._
- **Should `observe` be split into smaller, more focused modules?**
  _Cohesion score 0.08333333333333333 - nodes in this community are weakly interconnected._