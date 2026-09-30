# Graph Report - BankerAgent  (2026-09-29)

## Corpus Check
- 100 files · ~219,988 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 2390 nodes · 4766 edges · 127 communities (115 shown, 12 thin omitted)
- Extraction: 94% EXTRACTED · 6% INFERRED · 0% AMBIGUOUS · INFERRED: 277 edges (avg confidence: 0.62)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `9ca44058`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- test_cli.py
- observe
- asyncio
- test_replay.py
- Five Error Demos (D30)
- 03_recorder.py
- evidence_capture.py
- test_handback_button.py
- test_no_values_stored.py
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
- click
- test_transaction_gates.py
- DECISIONS.md (design decision log)
- PlaywrightReplaySurface
- Site
- live.py
- run_capability_async
- discovery.py
- AsyncFakeSurface
- PlaywrightReplaySurface
- REPORT.md (assignment's 7-heading design write-up)
- test_takeover.py
- test_checks.py
- Look
- CLAUDE.md (project instructions)
- PHASE3.md (Recorder write-up)
- type_text
- manifest.json
- ResolutionError
- _request_missing_values_wrapped
- replay/replay.py
- take_look
- derive_target
- types
- 01_browser_and_observe.py
- ResolutionError
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
- rescue
- _MinimalAsyncSurface
- _MinimalSurface
- 05_replay_live.py
- mk_look
- Discovery decisions
- 2. Each box, with an example
- choose_option
- REPORT: Determinism & error handling section
- 2. Components
- ControlWindow
- Pure-Visual Discovery Notebook: Build Plan
- SiteLock
- AsyncReplaySurface
- recorder.py
- guard_send
- run
- ReplaySurface
- PlaywrightSurface
- run_goal
- REPORT: Artifact schema section
- _extract_target
- test_latest_screenshot.py
- test_evidence.py
- D32: Agent-driven login via a type_secret(ref, name) tool
- 02_artifact_schema.py
- current_value
- 4. Pure-visual discovery engine (redesign, in design)
- test_recorder.py
- 04_replay_engine.py
- do_type
- Condition
- Coordination: discovery <-> replay
- my_cap scratch capability artifact (account 18672, log out)
- human_fills
- _unlocked
- Pause/Resume Human-in-the-Loop Smoke Test
- PlaywrightSurface.observe Design
- derived_routes (D65)
- ReplaySurface Protocol
- PHASE1.md (The Agent write-up)
- interface-ai-cua
- schema.py
- Capability
- InputValidationError
- Target
- pathlib
- PlaywrightSurface
- test_load_inputs.py
- test_outcomes.py
- ControlWindow
- test_round_trip.py
- test_save_artifact.py
- gather_missing_inputs
- test_control_form.py
- Replay notebook plan
- test_caller_inputs.py
- test_replay_evidence.py
- SiteLock
- PHASE2.md (Artifact Schema write-up)
- run_capability
- save_capability
- pytest
- needs_human
- missing_field_labels
- trim_tail
- norm_url
- value_matches_type
- background.js

## God Nodes (most connected - your core abstractions)
1. `run_capability()` - 41 edges
2. `DiscoveryAgent` - 40 edges
3. `CompileError` - 36 edges
4. `DECISIONS.md (design decision log)` - 32 edges
5. `FakeSurface` - 28 edges
6. `compile_run()` - 27 edges
7. `run_capability_async()` - 27 edges
8. `Target` - 27 edges
9. `run_capability_async()` - 26 edges
10. `Capability` - 26 edges

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

## Communities (127 total, 12 thin omitted)

### Community 0 - "test_cli.py"
Cohesion: 0.10
Nodes (32): _discover_args(), _fake_extract_tool(), _fake_page(), _FakePage, _minimal_events(), _patch_agent_build(), _patch_langchain_agent(), Namespace (+24 more)

### Community 1 - "observe"
Cohesion: 0.09
Nodes (44): approval_info(), _ask_for_value(), ask_human(), _blocks(), _click(), current_page(), _describe(), extract_value() (+36 more)

### Community 2 - "asyncio"
Cohesion: 0.25
Nodes (4): asyncio, FakeBox, into_box clears the field before typing, so a retry replaces instead of…, test_typing_twice_does_not_double()

### Community 3 - "test_replay.py"
Cohesion: 0.15
Nodes (29): from_yaml(), balance_cap(), pay_bill(), fixture, new_happy_async_surface(), new_happy_surface(), no_secrets(), Tests for `cua.replay` (sync + async engines), ported from… (+21 more)

### Community 4 - "Five Error Demos (D30)"
Cohesion: 0.08
Nodes (39): Roadmap + Phase 1 Plan, Agent-Driven Login (D32/type_secret), Deep Agent + Playwright Architecture, Phase 2 Artifact Schema Plan, Capability Schema Model, Risk-in-Artifact / Limit-in-Config Policy (D38), Phase 3 Recorder Plan (v1), Recorder COMPILE Pipeline (v1) (+31 more)

### Community 5 - "03_recorder.py"
Cohesion: 0.06
Nodes (42): langchain_agents_middleware, langchain_typesafe, langchain_typesafe_experimental_middleware, _amount(), _balance_events(), _balance_events_with_agent_note(), _balance_events_with_detour(), _bare_proxy() (+34 more)

### Community 6 - "evidence_capture.py"
Cohesion: 0.13
Nodes (21): Stable, human-readable YAML. Keys keep the model's field order., to_yaml(), show(), _as_text(), _assert_no_secret_values(), _default_label(), EvidenceWriteError, _find_repo() (+13 more)

### Community 7 - "test_handback_button.py"
Cohesion: 0.10
Nodes (21): _click(), env(), Ext, Human, Lock, PanelDone, fixture, parametrize (+13 more)

### Community 8 - "test_no_values_stored.py"
Cohesion: 0.36
Nodes (5): Call, _arg_keys(), _log_calls(), Banking rule: no typed or human-given value is stored. Source-level checks on…, test_typed_and_selected_values_never_reach_the_log()

### Community 9 - "cli.py"
Cohesion: 0.10
Nodes (26): argparse, ArgumentParser, build_agent(), Build a ready-to-use `DiscoveryAgent`. If `page` is None, launches a real,…, _build_capture(), build_parser(), _capture(), _first_line() (+18 more)

### Community 10 - "test_agent.py"
Cohesion: 0.07
Nodes (39): build_typesafe_middleware(), confidence_gate(), login_check(), Narrow base_tools to this job's tools, but only if the classifier is confident.…, Build the D50/D52 TypeSafe middleware list (tool router + model router),…, Pure decision (D69): after a login click, should further attempts be blocked,…, _agent(), Tests for `cua.agent`'s pure (or pure-enough-to-test-without-a-browser) logic,… (+31 more)

### Community 11 - "FakeSurface"
Cohesion: 0.17
Nodes (3): FakeSurface, _locator_key(), A dict-based fake DOM: pages by url, a locator registry per url, and per-ref…

### Community 12 - "Replay decisions"
Cohesion: 0.09
Nodes (21): R10: where the compile step lives — DECIDED, R11: why compile, if `response_format` exists? — PROPOSED, R12: what each step type compiles to — PROPOSED, R13: target schema — PROPOSED, R14: what rung 2 needs that discovery doesn't record — DONE, R15: auto-approve at replay — PROPOSED, R16: dead ends and retries at compile — PROPOSED, R17: replay result statuses — PROPOSED (+13 more)

### Community 13 - "DiscoveryAgent"
Cohesion: 0.18
Nodes (9): DiscoveryAgent, One discovery run's worth of browser control state (D33-D62). All state that…, Every button except a short safe list needs a human. Links (navigation) run…, Best available description of an element (D53): the code's own name, the…, Read whatever is currently in this field, live from the page (D54)., Package text and a screenshot as one tool result the model can read., Give the live browser to a human. Returns when they click 'Done', OR, if…, The agent tried to enter a value the user never gave. Hand the browser to a… (+1 more)

### Community 14 - "test_schema.py"
Cohesion: 0.06
Nodes (59): check_result(), malformed_template(), What a calling agent sees: what this capability does, what it needs, what it…, Check a result against the capability that produced it. Raises ValueError on a…, Return (is_secret, name) for every {{...}} reference in text., True if text contains a '{{' that is not a valid reference, e.g. {{Account}}., template_refs(), tool_contract() (+51 more)

### Community 15 - "test_models.py"
Cohesion: 0.12
Nodes (20): CaptureFixture, cua: computer-use automation -- discovery agent, capability artifact schema,…, _clean_env(), fixture, MonkeyPatch, Offline tests for `cua.models.make_chat_model` (Iliad gateway). No network, no…, The model router receives ChatAnthropic objects (not strings) and keeps them…, No model given -> create_deep_agent receives make_chat_model('sonnet'). (+12 more)

### Community 16 - "Target"
Cohesion: 0.08
Nodes (15): _no_labeled_value(), Exactly one primary locator, one optional fallback (D63). A third locator is…, All locators in try-order: primary, then fallback if present., RoleLocator, Target, TextLocator, _AsyncDictSurface, _MinimalAsyncSurface (+7 more)

### Community 17 - "CompileError"
Cohesion: 0.13
Nodes (22): _cap(), _check_specs(), _checkpoint_from_last(), clean_events(), compile_run(), CompileError, drop_dead_end_risky_clicks(), drop_detours() (+14 more)

### Community 18 - "test_human_help.py"
Cohesion: 0.11
Nodes (20): Control, Lock, _no_watch(), Page, parametrize, human_help: one open-ended panel -> answer in words, take over, or stop., Run human_help's take-over; `during(page)` is what the human does before…, Live crash: Register (a form POST) held by guard_send -> shot_after timed out… (+12 more)

### Community 19 - "agent_2_legacy_surface.py"
Cohesion: 0.08
Nodes (29): dataclasses, LegacyLocator, LegacyStrategy, AccessibleNameLocator, AnchorLocator, DriftLog, FakeLegacyPage, LegacyElement (+21 more)

### Community 20 - "agent.py"
Cohesion: 0.10
Nodes (23): BaseChatModel, functools, ModelKind, build_langchain_agent(), job_tool_names(), NoopAnthropicPromptCachingMiddleware, page_name_from_url(), AgentMiddleware (+15 more)

### Community 21 - "test_resolve_inputs.py"
Cohesion: 0.12
Nodes (23): _ask(), _cap(), ClearPage, _click(), env(), FakeForm, FakePage, fixture (+15 more)

### Community 22 - "click"
Cohesion: 0.15
Nodes (16): act(), after_login_click(), click(), gate_click(), landed(), norm(), Text the page showed in response to a send: the replay checkpoint. Fixed page…, Click a numbered box, or a spot with no number by x,y. Risky clicks ask a human… (+8 more)

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
Cohesion: 0.09
Nodes (31): InputParam, re, Look up a secret by NAME. Raises on an unknown name or an empty/missing value.…, resolve_secret(), gather_missing_inputs(), make_escalate(), missing_required_inputs(), _prompt_for_missing_input() (+23 more)

### Community 28 - "run_capability_async"
Cohesion: 0.13
Nodes (15): _is_approved(), matches_value_type(), parse_amount(), SecretResolver, Async twin of run_capability (Section 4). IDENTICAL behavior -- every surface…, Basic format check for a declared ValueType. Used for both inputs (D29) and…, Type/pattern-validate caller-supplied inputs before they are ever substituted…, {{input_name}} from validated caller inputs; {{secret:name}} from the… (+7 more)

### Community 29 - "discovery.py"
Cohesion: 0.08
Nodes (51): Anchor, build_capability(), Capability, CapabilityMeta, checkpoint(), _clean(), Config, crops_for() (+43 more)

### Community 30 - "AsyncFakeSurface"
Cohesion: 0.49
Nodes (6): AsyncFakeSurface, new_happy_async_surface(), new_happy_surface(), Async twin of FakeSurface (Section 4b). Identical state and behavior -- every…, _run_async_checks(), _run_async_integration()

### Community 31 - "PlaywrightReplaySurface"
Cohesion: 0.12
Nodes (8): host_allowed(), True if `url`'s host is on the allowlist (D15). ``about:blank`` is always…, LabeledValueRef, PlaywrightReplaySurface, A `resolve()` result for a `labeled_value` locator: not a numbered element ref…, Implements `AsyncReplaySurface` (`cua.replay`) against the real browser. Wraps…, One resolution attempt, no retry -- the exact logic `resolve()` used before D88., D78: for `labeled_value`, go straight to READ_LABELED_JS (no numbered scan at…

### Community 32 - "REPORT.md (assignment's 7-heading design write-up)"
Cohesion: 0.25
Nodes (9): D99: TypeSafe tool/model-router middleware ported into src/cua, D14: page.pause() wrapped with a control-state + intervention-request model, D16: Single redact() choke point for secrets/PII in logs and artifacts, D21: Base capability + per-tenant overrides, with a drift signal, D64: app/vendor/base/overrides multi-tenant fields cut from schema, REPORT.md (assignment's 7-heading design write-up), REPORT: Cuts section, REPORT: Escalation & handoff section (+1 more)

### Community 33 - "test_takeover.py"
Cohesion: 0.05
Nodes (41): _cap(), _click(), DoneWhileSending, env(), _fail_clicks(), FakeLock, FakePage, FormRoute (+33 more)

### Community 34 - "test_checks.py"
Cohesion: 0.31
Nodes (6): _form_png(), _Page, Step checks on fakes: whole-field read (A), tolerant word match (B), late page…, test_click_waits_for_a_late_page_change(), test_field_box_is_the_drawn_input(), test_short_value_at_left_edge_is_read()

### Community 35 - "Look"
Cohesion: 0.13
Nodes (21): Box, canvas(), crop_box(), Element, element_at(), field_box(), find(), find_text() (+13 more)

### Community 36 - "CLAUDE.md (project instructions)"
Cohesion: 0.21
Nodes (12): balance_check capability artifact, get_account_balance capability artifact (D89 hand-edited), get_account_balance_discovery_demo capability artifact, CLAUDE.md (project instructions), D101: labeled_value refuses a table-header resolution (general fix), D102: label_header/value_header flags ported into agent.py + cli.py capture path, D92: Evidence Capture Helpers (save_discovery_evidence/save_replay_evidence), D95: Missing create_deep_agent import found live in BROWSER 12 (+4 more)

### Community 37 - "PHASE3.md (Recorder write-up)"
Cohesion: 0.18
Nodes (12): my_def pay-bill capability artifact (electricity company), PHASE3.md (Recorder write-up), D41-D49: original recorder design (superseded by v2 rebuild), D42: Locator derivation only trusts a real accessible name for role locators, D43: Dropping dead-end click detours from the recording, D44: Turning matched literal values into {{inputs}}, D46: extraction limited to labeled values (known limit), D47: business-outcome rule derived from a deliberate bad-input probe run (+4 more)

### Community 38 - "type_text"
Cohesion: 0.14
Nodes (28): ask_human(), blocks(), canvas(), extract_value(), finish_business_outcome(), human_help(), log(), observe() (+20 more)

### Community 39 - "manifest.json"
Cohesion: 0.11
Nodes (18): action, default_icon, default_title, background, service_worker, 128, 16, 32 (+10 more)

### Community 40 - "ResolutionError"
Cohesion: 0.20
Nodes (7): InputValidationError, Exception, Neither the primary nor the fallback locator resolved to an element., A caller-supplied input is missing, mistyped, or does not match its declared…, A surface raises this for a step that should be retried (D26): the page was not…, ResolutionError, TransientFailure

### Community 41 - "_request_missing_values_wrapped"
Cohesion: 0.17
Nodes (19): classify_status(), current_heading(), current_value(), describe_ref(), _extract_value_wrapped(), _finish_wrapped(), _first_line(), missing_field_labels() (+11 more)

### Community 42 - "replay/replay.py"
Cohesion: 0.12
Nodes (26): _clean(), Config, discovery_schema(), dropdown_options(), _flat(), guard_send(), hide_secrets(), is_sensitive() (+18 more)

### Community 43 - "take_look"
Cohesion: 0.20
Nodes (16): decode(), draw_numbered(), encode(), find_template(), mask_png(), ocr(), open_start(), page_width() (+8 more)

### Community 44 - "derive_target"
Cohesion: 0.11
Nodes (21): derive_target(), _extract_target(), Target, D68: `label` and `labeled_value` locators have no `within` slot in the schema.…, Descriptor -> Target(primary, fallback). role+name (high, only when the name is…, D101: a `labeled_value` extract step whose CAPTURED resolution is itself a…, _refuse_if_duplicate_label(), _refuse_if_header_value() (+13 more)

### Community 45 - "types"
Cohesion: 0.36
Nodes (7): _load(), _look(), ndarray, SimpleNamespace, spot_changed: password dots are pixels, not OCR text., test_dots_count_as_change_and_blank_does_not(), types

### Community 46 - "01_browser_and_observe.py"
Cohesion: 0.11
Nodes (13): dotenv, format_elements(), Observation, PlaywrightSurface, Independent check of the balance, used only to grade the agent., The only place that touches Playwright. Agent tools talk to this., Look up a secret by name. Raises on unknown name or empty value., read_balance_ground_truth() (+5 more)

### Community 47 - "ResolutionError"
Cohesion: 0.13
Nodes (17): describe_locator(), describe_target(), Target, Pure: the try-order for a target -- primary, then fallback if present (D63). No…, Try the primary locator, then the fallback if there is one and the primary did…, Async twin of resolve_target. Same try-order (`_target_locators`, a PURE…, One line naming what a locator is looking for -- used to build a clear…, Neither the primary nor the fallback locator resolved to an element. (+9 more)

### Community 48 - "take_look"
Cohesion: 0.10
Nodes (34): Box, crop_box(), cut_crop(), decode(), draw_numbered(), Element, element_at(), encode() (+26 more)

### Community 49 - "PlaywrightSurface"
Cohesion: 0.12
Nodes (9): format_elements(), Observation, PlaywrightSurface, The only place that touches Playwright directly. Agent tools talk to this., The single unlocked click path every automated click (agent tool or replay)…, Run one Playwright action with the general lock removed for just that instant…, _unlocked(), test_format_elements_shows_current_value_and_below_the_fold() (+1 more)

### Community 50 - "test_choose_option.py"
Cohesion: 0.22
Nodes (11): _fns(), Page, Dropdowns (option B): read every option and select by value, for the <select>…, Mimics SELECT_AT_JS against one <select> at (100, 50); nothing else on the page., The user's bug: two accounts, only one showed., The red box showed the whole tool reply (URL, every OCR line) instead of the…, test_lists_every_option_values_only(), test_missing_option_is_refused() (+3 more)

### Community 51 - "Any"
Cohesion: 0.18
Nodes (5): _AsyncDictSurface, _DictSurface, Any, Just enough of a surface to test resolve_target in isolation: resolve(locator)…, Async twin of _DictSurface (Section 3b).

### Community 52 - "FakeSurface"
Cohesion: 0.09
Nodes (6): A surface raises this for a step that should be retried (D26): the page was not…, TransientFailure, AsyncFakeSurface, FakeSurface, _locator_key(), test_3_primary_fails_fallback_succeeds()

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
Nodes (30): deepagents, langchain_tools, langgraph_checkpoint_memory, ask_human(), BrowserSurface, build_agent(), click(), finish() (+22 more)

### Community 58 - "rescue"
Cohesion: 0.15
Nodes (14): Future, button_clicked(), ext_call(), hand_back(), handback_button(), Evidence screenshot. A held form POST blocks `page.screenshot()`: give up,…, R19: one bounded call into the hand-back extension's service worker, never the…, Returns once the toolbar button's click count rises above where it was at the… (+6 more)

### Community 61 - "05_replay_live.py"
Cohesion: 0.14
Nodes (15): langgraph_types, _find_repo_for_engine(), _find_repo_for_evidence(), load_evidence_capture(), load_replay_engine(), make_escalate(), Path, Load a capability YAML and replay it for real, printing the result. `secrets`… (+7 more)

### Community 62 - "mk_look"
Cohesion: 0.22
Nodes (12): mk_look(), mk_look([(text, (x1, y1, x2, y2)), ...]) -> a Look with those OCR elements., fixture, A fake site: clicks move between screens by script; `take_look` returns the…, site(), The 3 rungs + table cell; all miss -> None., test_all_miss_is_none(), test_rung1_digits_exact_words_fuzzy() (+4 more)

### Community 63 - "Discovery decisions"
Cohesion: 0.09
Nodes (21): Base decisions, Discovery decisions, Q10: window size and zoom — DECIDED, Q11: notebook format — DECIDED, Q12: dropdowns — DECIDED, Q13: scrolling — DECIDED, Q14: private data in saved pictures — DECIDED, Q15: sitemap before discovery — DECIDED (+13 more)

### Community 64 - "2. Each box, with an example"
Cohesion: 0.12
Nodes (15): 1. Diagram, 2. Each box, with an example, 3. All tools, 4. Step by step: one discovery run, 5. Notes, Browser (Playwright), Control window and site lock (Q-A), Discovery architecture (+7 more)

### Community 65 - "choose_option"
Cohesion: 0.29
Nodes (8): ask_option(), choose_option(), do_select(), into_box(), Click the box, clear what is in it, type., Select this exact live option; the dropdown's selected text and its OCR'd box…, The one mid-run prompt: the given value is not a live option. Choose one, blank…, to_page()

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

### Community 72 - "recorder.py"
Cohesion: 0.08
Nodes (48): Checkpoint, _amount_input(), build_steps(), _canon(), _cap(), _check_specs(), _checkpoint_from_last(), CompileError (+40 more)

### Community 73 - "guard_send"
Cohesion: 0.14
Nodes (18): dropdown_options(), _flat(), guard_send(), hide_secrets(), is_sensitive(), _json(), mismatches(), needs_human_value() (+10 more)

### Community 74 - "run"
Cohesion: 0.13
Nodes (15): take_over's hand-back: the extension's toolbar button (never the site), with no…, The user's rule: no "are you done?" prompts in between. Only the take-over…, test_a_click_on_the_toolbar_button_hands_back(), test_done_in_the_takeover_itself_cancels_the_watcher(), test_no_extension_still_hands_back_from_the_control_tab(), test_no_idle_reminder_ever_interrupts_the_take_over(), test_the_badge_reads_you_during_the_take_over_then_ai(), test_the_button_never_touches_the_site_page() (+7 more)

### Community 75 - "ReplaySurface"
Cohesion: 0.18
Nodes (3): Protocol, What a real Playwright-backed surface implements…, ReplaySurface

### Community 76 - "PlaywrightSurface"
Cohesion: 0.22
Nodes (5): approval_info(), format_elements(), Observation, PlaywrightSurface, The only place that touches Playwright. Agent tools talk to this.

### Community 77 - "run_goal"
Cohesion: 0.13
Nodes (16): ext_call(), flag_leaks(), HandoffState, host_allowed(), New run on a fresh thread; pass an earlier thread_id to resume it with a next…, Every value typed, entered or given this run, plus the secrets (in memory only)., Mark (never store) an event whose label, anchor or own text is one of this…, An evidence screenshot: short timeout, None on failure. A page whose navigation… (+8 more)

### Community 78 - "REPORT: Artifact schema section"
Cohesion: 0.29
Nodes (7): examples/transfer_funds.yaml (hand-written illustrative example), D15: Domain+route+action allowlist enforced in tool code before Playwright acts, D20: $500 auto-approve threshold for risky transfer/click actions, D8: Ranked locator strategy (role > label > text > structure), D9: Checkpoint requires both URL and text-content match, REPORT: Artifact schema section, REPORT: Safety section

### Community 79 - "_extract_target"
Cohesion: 0.29
Nodes (7): LabeledValueLocator, The value shown next to a label, e.g. the cell after 'Balance:'. Only valid in…, _extract_target(), D68: `label` and `labeled_value` locators have no `within` slot in the schema.…, D101: a `labeled_value` extract step whose CAPTURED resolution is itself a…, _refuse_if_duplicate_label(), _refuse_if_header_value()

### Community 80 - "test_latest_screenshot.py"
Cohesion: 0.47
Nodes (5): _cls(), LatestScreenshotOnly keeps only the newest image in the model's context., _shot(), test_only_last_image_survives(), ToolMessage

### Community 81 - "test_evidence.py"
Cohesion: 0.31
Nodes (13): _artifact(), _ns(), Path, save_evidence: one masked folder per run. No run value or secret is ever…, _save(), test_a_failed_run_still_writes_evidence(), test_an_artifact_holding_a_run_value_is_refused(), test_capability_yaml_and_crops_are_copied() (+5 more)

### Community 82 - "D32: Agent-driven login via a type_secret(ref, name) tool"
Cohesion: 0.25
Nodes (8): login_parabank capability artifact, D93: Pre-existing 02_artifact_schema.py IndexError bug, D11/D17: Separate login helper reading .env (superseded by D32), D31: Offline unit tests only, no live E2E test in CI, D32: Agent-driven login via a type_secret(ref, name) tool, D6: Replay is a plain deterministic engine, not an agent, D45: split_login() separates login into its own reusable capability, README.md (setup + demo path)

### Community 83 - "02_artifact_schema.py"
Cohesion: 0.06
Nodes (51): copy, bad_amount(), bad_click(), bad_order(), Capability, check_result(), Click, derived_routes() (+43 more)

### Community 84 - "current_value"
Cohesion: 0.40
Nodes (4): current_value(), Read whatever is currently in this field, live from the page. Empty string if…, The value shown next to `label` on the current page. Raises LookupError if…, read_labeled_value()

### Community 85 - "4. Pure-visual discovery engine (redesign, in design)"
Cohesion: 0.20
Nodes (9): 1. High-level component architecture, 2. How discovery actually happens (sequence), 3. The clean-DOM gap, explicitly, 4. Pure-visual discovery engine (redesign, in design), Architecture: Agent + Discovery Pipeline, Decided (user-confirmed), Discovery engine — block diagram, Open questions (NOT decided) (+1 more)

### Community 86 - "test_recorder.py"
Cohesion: 0.10
Nodes (44): classify_status(), clean_events(), compile_run(), drop_dead_end_risky_clicks(), _key(), Bucket a tool result's own text by the EXACT prefixes agent.ipynb's tools…, Keep only actions that worked and mattered. Returns (kept, dropped). dropped =…, D86: remove a risky click proven, by real evidence, to be a dead end. Never… (+36 more)

### Community 87 - "04_replay_engine.py"
Cohesion: 0.14
Nodes (17): _call_escalate(), _check_outcomes(), _check_outcomes_async(), condition_matches(), describe_locator(), describe_target(), _fail(), _find_outcome_rule() (+9 more)

### Community 88 - "do_type"
Cohesion: 0.12
Nodes (22): act(), do_click(), do_extract(), do_navigate(), do_scroll(), do_type(), fill(), host_allowed() (+14 more)

### Community 89 - "Condition"
Cohesion: 0.16
Nodes (12): OutcomeRule, D10/D47: a bad-input run ended with finish_business_outcome(outcome,…, relogin_rule(), rule_from_probe(), Checkpoint, Condition, OutcomeRule, model_validator (+4 more)

### Community 90 - "Coordination: discovery <-> replay"
Cohesion: 0.20
Nodes (9): Blockers for the user, Coordination: discovery <-> replay, Discovery (`notebooks/discovery/`, orchestrator ac2ad3f302f5be3b5; p1 builder a9cc1291cca0102fb done, p4 builder a4b8ff70020b5454d done), Duplication (watch list), Mismatches, Replay (`notebooks/replay/`, orchestrator a0245948081e7b9c1), Rule checks (discovery parts, check #3), Shared contract (+1 more)

### Community 92 - "human_fills"
Cohesion: 0.19
Nodes (14): choose_option(), human_fills(), into_box(), list_options(), mark_stuck(), note_call(), Pick the dropdown option that matches. Nothing is typed. Give option="" if the…, The same call N times in a row means STUCK. (+6 more)

### Community 93 - "_unlocked"
Cohesion: 0.33
Nodes (4): _click(), Run one Playwright action with the general lock (Setup 5) removed for just that…, _type_text(), _unlocked()

### Community 100 - "schema.py"
Cohesion: 0.10
Nodes (25): pydantic, show(), Capability, derived_routes(), Dismiss, InputParam, LabeledValueLocator, LabelLocator (+17 more)

### Community 101 - "Capability"
Cohesion: 0.10
Nodes (31): ask_inputs(), given_inputs(), judge(), load_capability(), load_outcomes(), login_came_back(), login_steps(), Capability (+23 more)

### Community 102 - "InputValidationError"
Cohesion: 0.18
Nodes (11): InputValidationError, matches_value_type(), Exception, Basic format check for a declared ValueType. Used for both inputs (D29) and…, Type/pattern-validate caller-supplied inputs before they are ever substituted…, A caller-supplied input is missing, mistyped, or does not match its declared…, validate_inputs(), parametrize (+3 more)

### Community 103 - "Target"
Cohesion: 0.12
Nodes (15): Checkpoint, Condition, locator_strings(), _no_labeled_value(), OutcomeRule, model_validator, Exactly one primary locator, one optional fallback (D63). A third locator is…, All locators in try-order: primary, then fallback if present. (+7 more)

### Community 104 - "pathlib"
Cohesion: 0.18
Nodes (8): json, pathlib, _ns(), parametrize, take_look's canvas: any window size or pixel density maps to one grid, and…, test_fits_canvas_and_maps_clicks_back_to_the_same_spot(), The hand-back extension never touches any site: no content scripts, no host…, The hand-back extension never touches any site: no content scripts, no host…

### Community 105 - "PlaywrightSurface"
Cohesion: 0.29
Nodes (4): format_elements(), Observation, PlaywrightSurface, The only place that touches Playwright. Agent tools talk to this.

### Community 106 - "test_load_inputs.py"
Cohesion: 0.24
Nodes (9): test_replay_stops_on_an_unknown_key_before_opening_the_site(), Loading the artifact as saved, and the inputs., test_undeclared_input_refused(), test_viewport_mismatch_refused(), test_yaml_loads_with_crops_relative(), _write(), test_unknown_outcome_status_is_refused(), test_yaml_outcomes_replace_the_defaults() (+1 more)

### Community 107 - "test_outcomes.py"
Cohesion: 0.31
Nodes (9): _cap(), R17 taxonomy after each step: a business answer stops, a lost session is re-…, test_a_second_expiry_is_not_recovered_again(), test_a_send_is_never_retried_after_an_expiry(), test_error_page_fails_with_detail(), test_expired_session_is_recovered_once(), test_login_page_back_mid_run_is_recovered(), test_not_found_screen_is_a_business_outcome_with_its_meaning() (+1 more)

### Community 108 - "ControlWindow"
Cohesion: 0.33
Nodes (4): ControlWindow, _img(), Our own page: the only place a human answers. Closing it fails closed (None)., _row()

### Community 109 - "test_round_trip.py"
Cohesion: 0.39
Nodes (7): Path, Discovery's saved artifact runs in replay unchanged: build -> save -> load ->…, _saved(), test_crop_paths_resolve_to_saved_files(), test_rung2_offset_hits_the_point_discovery_acted_on(), test_saved_artifact_loads_as_is(), test_steps_dispatch_to_replay_handlers()

### Community 110 - "test_save_artifact.py"
Cohesion: 0.11
Nodes (36): _ev(), _look_ns(), _meta(), Path, Save artifact: the event log becomes a replay-ready capability (R12, R13, R16).…, Invented inputs are ignored, a missing description gets a default, secrets stay…, Every cell of '## Save artifact', plus the helpers it uses from earlier cells., Live bug: 'From account #' dropdown showing '74838' was saved as input… (+28 more)

### Community 111 - "gather_missing_inputs"
Cohesion: 0.33
Nodes (6): gather_missing_inputs(), missing_required_inputs(), _prompt_for_missing_input(), Pure, standalone, offline-testable: which of `cap.inputs` (the Phase 2 schema's…, Prompt for exactly one missing required input, showing its own `.description`…, The pre-flight gate itself. Runs BEFORE anything else in `replay_live` -- no…

### Community 112 - "test_control_form.py"
Cohesion: 0.14
Nodes (9): base64, FakeWin, ControlWindow: form answers, and a newer question supersedes then restores the…, Regression: a gate during a take-over must win, then hand the take-over back…, test_closing_the_window_fails_every_question_closed(), test_dropdown_row_lists_every_option(), test_form_returns_answers_and_masks_sensitive(), test_gate_supersedes_takeover_then_restores_it() (+1 more)

### Community 113 - "Replay notebook plan"
Cohesion: 0.33
Nodes (5): Decisions made here (review), Open questions for the user, Replay notebook plan, Sections, Tasks

### Community 114 - "test_caller_inputs.py"
Cohesion: 0.33
Nodes (7): _cap(), FakeForm, replay(path, inputs): given values by exact name (any case); unknown keys stop;…, test_all_inputs_given_means_no_form(), test_given_inputs_match_by_exact_name_any_case(), test_only_the_missing_inputs_go_to_the_one_form(), test_unknown_key_stops_naming_what_is_accepted()

### Community 115 - "test_replay_evidence.py"
Cohesion: 0.31
Nodes (9): _all_text(), _png(), save_evidence writes one masked folder per run: summary, drift, failure (only…, _result(), test_all_files_are_written(), test_checkpoint_miss_carries_expected_and_observed(), test_failure_json_has_step_expected_observed(), test_no_failure_file_on_success() (+1 more)

### Community 117 - "PHASE2.md (Artifact Schema write-up)"
Cohesion: 0.29
Nodes (7): PHASE2.md (Artifact Schema write-up), D63: Target simplified to primary + one optional fallback, D65: routes derived from navigate steps, not separately stored, D66: when_to_use folded into description as one field, D67: element-with-no-accessible-name honest gap, D68: label/labeled_value locators cannot be scoped to a container, D70-D76: recorder rebuilt against the v2 schema and current agent.ipynb

### Community 118 - "run_capability"
Cohesion: 0.11
Nodes (33): Condition, Failure, inspect, AsyncReplaySurface, _call_escalate(), _check_outcomes(), _check_outcomes_async(), condition_matches() (+25 more)

### Community 119 - "save_capability"
Cohesion: 0.40
Nodes (5): from_yaml(), _find_repo(), Path, Validate, guard against secret values, write. Never overwrites a verified…, save_capability()

### Community 120 - "pytest"
Cohesion: 0.17
Nodes (11): pytest, stmt, _fake_llm_keys(), fixture, MonkeyPatch, Suite-wide: never let a real LLM key from `.env` reach a test (cua.config loads…, A fake Iliad key so code that builds a chat model works offline; no real key is…, _keep() (+3 more)

### Community 121 - "needs_human"
Cohesion: 0.40
Nodes (5): _amount(), human_takeover(), needs_human(), Give the live browser to a human. Returns when they click 'Done', OR, if…, Every button except a short safe list needs a human. Links (navigation) run…

### Community 122 - "missing_field_labels"
Cohesion: 0.40
Nodes (5): missing_field_labels(), Empty, visible, fillable fields, in page order. Pure: no browser, no network…, test_missing_field_labels_falls_back_to_field_n(), test_missing_field_labels_finds_empty_visible_fillable_fields(), test_missing_field_labels_uses_a_hint_for_a_nameless_field()

### Community 123 - "trim_tail"
Cohesion: 0.67
Nodes (3): _meaningful(), Link clicks after the last meaningful action changed nothing the capability…, trim_tail()

### Community 124 - "norm_url"
Cohesion: 0.67
Nodes (3): norm_url(), Relative path + query. Drops the host, the base path, ;jsessionid=... and the…, test_norm_url()

### Community 125 - "value_matches_type"
Cohesion: 0.67
Nodes (3): Same shape as replay's own `matches_value_type` (cua.replay) -- used at CAPTURE…, value_matches_type(), test_value_matches_type()

## Knowledge Gaps
- **131 isolated node(s):** `MODES`, `manifest_version`, `name`, `version`, `description` (+126 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **12 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `DiscoveryAgent` connect `DiscoveryAgent` to `test_cli.py`, `cli.py`, `test_agent.py`, `PlaywrightSurface`, `agent.py`, `live.py`, `PlaywrightReplaySurface`?**
  _High betweenness centrality (0.029) - this node is a cross-community bridge._
- **Why does `FakeSurface` connect `FakeSurface` to `ResolutionError`, `run_capability_async`, `AsyncFakeSurface`, `04_replay_engine.py`?**
  _High betweenness centrality (0.023) - this node is a cross-community bridge._
- **Why does `PlaywrightSurface` connect `PlaywrightSurface` to `05_replay_live.py`?**
  _High betweenness centrality (0.014) - this node is a cross-community bridge._
- **Are the 3 inferred relationships involving `DiscoveryAgent` (e.g. with `LabeledValueRef` and `PlaywrightReplaySurface`) actually correct?**
  _`DiscoveryAgent` has 3 INFERRED edges - model-reasoned connections that need verification._
- **Are the 18 inferred relationships involving `CompileError` (e.g. with `Capability` and `Checkpoint`) actually correct?**
  _`CompileError` has 18 INFERRED edges - model-reasoned connections that need verification._
- **What connects `MODES`, `manifest_version`, `name` to the rest of the system?**
  _131 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `test_cli.py` be split into smaller, more focused modules?**
  _Cohesion score 0.10420168067226891 - nodes in this community are weakly interconnected._