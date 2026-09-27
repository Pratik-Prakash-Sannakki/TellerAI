# Graph Report - interface-ai-cua-v2  (2026-09-27)

## Corpus Check
- 60 files · ~167,199 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 20 file(s) not represented in the graph (top: .log 8, .ipynb 7, (none) 3)

## Summary
- 1487 nodes · 2779 edges · 96 communities (80 shown, 16 thin omitted)
- Extraction: 90% EXTRACTED · 10% INFERRED · 0% AMBIGUOUS · INFERRED: 277 edges (avg confidence: 0.88)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `baa984d3`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- test_cli.py
- _blocks
- schema.py
- compile_run
- Five Error Demos (D30)
- 03_recorder.py
- AsyncFakeSurface
- replay.py
- test_replay.py
- cli.py
- test_agent.py
- AsyncFakeSurface
- run_capability_async
- DiscoveryAgent
- test_schema.py
- AsyncReplaySurface
- CompileError
- CompileError
- Capability
- agent_2_legacy_surface.py
- ReplaySurface
- agent.py
- FakeSurface
- test_live.py
- DECISIONS.md (design decision log)
- PlaywrightReplaySurface
- live.py
- 05_replay_live.py
- .build_tools
- PlaywrightReplaySurface
- 04_replay_engine.py
- from_yaml
- test_recorder.py
- Target
- 3.3 Deterministic Replay (Production Execution Path)
- PlaywrightSurface
- CLAUDE.md (project instructions)
- PHASE3.md (Recorder write-up)
- 02_artifact_schema.py
- human_takeover
- drop_detours
- AsyncReplaySurface
- clean_events
- Section 4: Explicitly Your Call
- Condition
- resolve_target_async
- recorder.py
- Take-Home Project: Computer-Use Automation System (Assignment Brief)
- 3.7 Design for Heterogeneity & Scale
- render
- Capability
- Any
- replay_live
- ResolutionError
- TypeSafeToolRouterMiddleware
- ReplaySurface
- _literal_re
- validate_inputs
- _MinimalAsyncSurface
- _MinimalSurface
- host_allowed
- model_validator
- _MinimalAsyncSurface
- _MinimalSurface
- REPORT.md (assignment's 7-heading design write-up)
- REPORT: Determinism & error handling section
- Depth Over Breadth Principle
- Section 10: Glossary
- Deliverable: /REPORT.md
- Section 7: Evaluation Criteria
- Section 2: The Problem
- 3.2 Structured Artifact (Agent-Invocable Capability)
- Section 3: Core Requirements (Must-Have)
- PlaywrightSurface
- PlaywrightSurface
- PlaywrightSurface
- README.md (setup + demo path)
- 3.6 Human-in-the-Loop Escalation & Handoff
- PHASE2.md (Artifact Schema write-up)
- D32: Agent-driven login via a type_secret(ref, name) tool
- Human-in-the-Loop Escalation & Handoff
- current_value
- Architecture: Agent + Discovery Pipeline
- norm_url
- value_matches_type
- my_cap scratch capability artifact (account 18672, log out)
- Untitled.md (empty Obsidian note)
- Section 11: Submission
- Pause/Resume Human-in-the-Loop Smoke Test
- PlaywrightSurface.observe Design
- derived_routes (D65)
- ReplaySurface Protocol
- PHASE1.md (The Agent write-up)
- interface-ai-cua
- _AsyncDictSurface
- classify_status

## God Nodes (most connected - your core abstractions)
1. `DiscoveryAgent` - 41 edges
2. `run_capability()` - 34 edges
3. `DECISIONS.md (design decision log)` - 32 edges
4. `compile_run()` - 27 edges
5. `Capability` - 27 edges
6. `CompileError` - 25 edges
7. `FakeSurface` - 25 edges
8. `run_capability_async()` - 23 edges
9. `run_capability_async()` - 21 edges
10. `Target` - 21 edges

## Surprising Connections (you probably didn't know these)
- `1. High-level component architecture` --references--> `DiscoveryAgent`  [INFERRED]
  ARCHITECTURE.md → src/cua/agent.py
- `test_playwright_surface_name_of_looks_up_last_elements()` --uses--> `PlaywrightSurface`  [INFERRED]
  tests/test_agent.py → src/cua/agent.py
- `test_needs_human_transfer_over_auto_limit_still_risky()` --uses--> `DiscoveryAgent`  [INFERRED]
  tests/test_agent.py → src/cua/agent.py
- `test_needs_human_transfer_under_auto_limit_is_safe()` --uses--> `DiscoveryAgent`  [INFERRED]
  tests/test_agent.py → src/cua/agent.py
- `D1: Target Application = ParaBank` --conceptually_related_to--> `Tenant`  [INFERRED]
  DECISIONS.md → Assignment A — Computer-Use Automation System (1).pdf

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **The Five Required Error Demo Capabilities (D30)** — evidence_replay_get_account_balance_error_account_not_found_capability, evidence_replay_get_account_balance_error_slow_page_capability, evidence_replay_transfer_funds_error_element_missing_capability, evidence_replay_transfer_funds_error_session_expired_capability, evidence_replay_transfer_funds_error_transfer_over_limit_capability [EXTRACTED 0.90]
- **Sequential Phase Plan Roadmap** — docs_superpowers_plans_2026_09_19_roadmap_and_phase1, docs_superpowers_plans_2026_09_20_phase2_artifact_schema, docs_superpowers_plans_2026_09_20_phase3_recorder, docs_superpowers_plans_2026_09_22_phase2_v2_and_replay, docs_superpowers_plans_2026_09_25_phase3_recorder_v2, docs_superpowers_plans_2026_09_26_phase4_live_wiring, docs_superpowers_plans_2026_09_26_recorder_human_entry_fix [EXTRACTED 0.90]
- **Core Requirements Vertical Slice (Section 3.1-3.7)** — assignment_a_computer_use_automation_system_1_section_3_1_goal_driven_agent_loop, assignment_a_computer_use_automation_system_1_section_3_2_structured_artifact, assignment_a_computer_use_automation_system_1_section_3_3_deterministic_replay, assignment_a_computer_use_automation_system_1_section_3_4_safety_policy_guardrails, assignment_a_computer_use_automation_system_1_section_3_5_evidence_observability, assignment_a_computer_use_automation_system_1_section_3_6_human_in_the_loop_escalation_handoff, assignment_a_computer_use_automation_system_1_section_3_7_design_for_heterogeneity_scale [EXTRACTED 1.00]
- **Evaluation Criteria Ranking (Section 7)** — assignment_a_computer_use_automation_system_1_eval_system_design, assignment_a_computer_use_automation_system_1_eval_correctness_of_core_loop, assignment_a_computer_use_automation_system_1_eval_robustness_error_handling, assignment_a_computer_use_automation_system_1_eval_human_in_the_loop_escalation, assignment_a_computer_use_automation_system_1_eval_generalization_to_real_environment, assignment_a_computer_use_automation_system_1_eval_safety_data_handling, assignment_a_computer_use_automation_system_1_eval_code_quality, assignment_a_computer_use_automation_system_1_eval_communication [EXTRACTED 1.00]
- **Replay Result Taxonomy (Expected Outcome / Recoverable / Hard Failure)** — assignment_a_computer_use_automation_system_1_expected_business_outcomes, assignment_a_computer_use_automation_system_1_recoverable_conditions, assignment_a_computer_use_automation_system_1_hard_failures [EXTRACTED 1.00]
- **REPORT.md Seven Required Headings** — assignment_a_computer_use_automation_system_1_report_heading_architecture, assignment_a_computer_use_automation_system_1_report_heading_artifact_schema, assignment_a_computer_use_automation_system_1_report_heading_determinism_error_handling, assignment_a_computer_use_automation_system_1_report_heading_heterogeneity_multi_tenant, assignment_a_computer_use_automation_system_1_report_heading_escalation_handoff, assignment_a_computer_use_automation_system_1_report_heading_safety, assignment_a_computer_use_automation_system_1_report_heading_cuts [EXTRACTED 1.00]
- **The Three Required Deliverables (Section 6)** — assignment_a_computer_use_automation_system_1_deliverable_readme, assignment_a_computer_use_automation_system_1_deliverable_report, assignment_a_computer_use_automation_system_1_deliverable_evidence [EXTRACTED 1.00]
- **Human-Entered Value Capture-to-Artifact Pipeline** — phase3_d82_d84_human_entry_recordable_fix, phase3_d90_auto_declare_human_input, artifacts_pay_bill, artifacts_my_def [INFERRED 0.85]
- **Sync-Async-Live Replay Engine Stack** — docs_superpowers_plans_2026_09_22_phase2_v2_and_replay_run_capability_engine, docs_superpowers_plans_2026_09_26_phase4_live_wiring_async_mirror, docs_superpowers_plans_2026_09_26_phase4_live_wiring_playwrightreplaysurface, docs_superpowers_plans_2026_09_26_phase4_live_wiring_make_escalate [INFERRED 0.85]
- **Three Real Bugs Found Only Live Against ParaBank** — phase5_d87_label_footnote_mismatch, phase5_d88_async_content_race_polling, phase5_d89_wrong_extraction_target_total_row, phase5 [INFERRED 0.85]
- **Business/Recoverable/Hard Outcome Taxonomy** — assignment_a_computer_use_automation_system_1_business_outcome_vs_failure, decisions_d10_error_handling_buckets, decisions_d27_replay_result_contract, artifacts_examples_get_account_balance [INFERRED 0.85]

## Communities (96 total, 16 thin omitted)

### Community 0 - "test_cli.py"
Cohesion: 0.06
Nodes (43): argparse, pytest, SimpleNamespace, format_elements(), Observation, cua: computer-use automation -- discovery agent, capability artifact schema,…, test_format_elements_shows_current_value_and_below_the_fold(), _discover_args() (+35 more)

### Community 1 - "_blocks"
Cohesion: 0.07
Nodes (48): approval_info(), _ask_for_value(), ask_human(), _blocks(), _click(), current_page(), _describe(), extract_value() (+40 more)

### Community 2 - "schema.py"
Cohesion: 0.14
Nodes (24): pydantic, _amount_input(), build_steps(), Events -> (steps, outputs, secrets, paths). Adds a navigate for the start page,…, Click, Dismiss, Extract, LabeledValueLocator (+16 more)

### Community 3 - "compile_run"
Cohesion: 0.26
Nodes (14): compile_run(), The whole pipeline. Returns {"login": Capability|None, "task": Capability,…, _balance_events(), _e(), test_compile_run_ask_human_handoff_refuses_the_whole_run(), test_compile_run_dead_end_click_is_removed(), test_compile_run_does_not_flag_a_footer_row_value_d101(), test_compile_run_good_balance_flow_login_split() (+6 more)

### Community 4 - "Five Error Demos (D30)"
Cohesion: 0.08
Nodes (39): Roadmap + Phase 1 Plan, Agent-Driven Login (D32/type_secret), Deep Agent + Playwright Architecture, Phase 2 Artifact Schema Plan, Capability Schema Model, Risk-in-Artifact / Limit-in-Config Policy (D38), Phase 3 Recorder Plan (v1), Recorder COMPILE Pipeline (v1) (+31 more)

### Community 5 - "03_recorder.py"
Cohesion: 0.07
Nodes (46): deepagents, langchain_agents_middleware, langchain_tools, langchain_typesafe, langchain_typesafe_experimental_middleware, langgraph_checkpoint_memory, _amount(), _balance_events() (+38 more)

### Community 6 - "AsyncFakeSurface"
Cohesion: 0.14
Nodes (5): AsyncFakeSurface, _locator_key(), new_happy_async_surface(), test_async_engine_all_scenarios(), run()

### Community 7 - "replay.py"
Cohesion: 0.11
Nodes (32): _call_escalate(), _check_outcomes(), _check_outcomes_async(), condition_matches(), _fail(), _find_outcome_rule(), _is_approved(), matches_value_type() (+24 more)

### Community 8 - "test_replay.py"
Cohesion: 0.32
Nodes (16): Run every step of `cap` against `surface`, no LLM in the loop (D6, 3.3).…, run_capability(), new_happy_surface(), no_secrets(), Tests for `cua.replay` (sync + async engines), ported from…, test_1_happy_path(), test_2_business_outcome(), test_3_primary_fails_fallback_succeeds() (+8 more)

### Community 9 - "cli.py"
Cohesion: 0.12
Nodes (30): ArgumentParser, build_agent(), Build a ready-to-use `DiscoveryAgent`. If `page` is None, launches a real,…, _build_capture(), build_parser(), _capture(), wrapped(), _current_heading() (+22 more)

### Community 10 - "test_agent.py"
Cohesion: 0.06
Nodes (49): build_typesafe_middleware(), awrap_model_call(), confidence_gate(), login_check(), missing_field_labels(), page_name_from_url(), Narrow base_tools to this job's tools, but only if the classifier is confident.…, Build the D50/D52 TypeSafe middleware list (tool router + model router),… (+41 more)

### Community 11 - "AsyncFakeSurface"
Cohesion: 0.08
Nodes (6): AsyncFakeSurface, FakeSurface, _locator_key(), new_happy_surface(), Async twin of FakeSurface (Section 4b). Identical state and behavior -- every…, A dict-based fake DOM: pages by url, a locator registry per url, and per-ref…

### Community 12 - "run_capability_async"
Cohesion: 0.13
Nodes (24): ok(), What replay returns to the caller (D27). Unchanged by the schema simplification., ReplayResult, _call_escalate(), _check_outcomes(), _check_outcomes_async(), condition_matches(), _fail() (+16 more)

### Community 13 - "DiscoveryAgent"
Cohesion: 0.15
Nodes (8): DiscoveryAgent, One discovery run's worth of browser control state (D33-D62). All state that…, Every button except a short safe list needs a human. Links (navigation) run…, Best available description of an element (D53): the code's own name, the…, Read whatever is currently in this field, live from the page (D54)., Package text and a screenshot as one tool result the model can read., Give the live browser to a human. Returns when they click 'Done', OR, if…, The agent tried to enter a value the user never gave. Hand the browser to a…

### Community 14 - "test_schema.py"
Cohesion: 0.06
Nodes (53): copy, check_result(), What a calling agent sees: what this capability does, what it needs, what it…, Check a result against the capability that produced it. Raises ValueError on a…, tool_contract(), bal(), _bal_data_with_three_outcome_rules(), _ok() (+45 more)

### Community 15 - "AsyncReplaySurface"
Cohesion: 0.20
Nodes (3): AsyncReplaySurface, Protocol, The async twin of ReplaySurface (Section 2). Same method names, same meanings…

### Community 16 - "CompileError"
Cohesion: 0.17
Nodes (12): _check_specs(), CompileError, _find_repo(), Exception, Path, Top-level refusals, BEFORE any cleanup runs. A run that hit the login attempt…, Validate, guard against secret values, write. Never overwrites a verified…, The recording cannot become a valid capability. `.problems` lists every reason. (+4 more)

### Community 17 - "CompileError"
Cohesion: 0.10
Nodes (27): _cap(), _check_specs(), _checkpoint_from_last(), clean_events(), compile_run(), CompileError, drop_dead_end_risky_clicks(), drop_detours() (+19 more)

### Community 18 - "Capability"
Cohesion: 0.15
Nodes (14): _cap(), contains_literal(), find_leftovers(), walk(), D29/D44: no declared literal may survive anywhere in the capability, except in…, show(), Capability, derived_routes() (+6 more)

### Community 19 - "agent_2_legacy_surface.py"
Cohesion: 0.08
Nodes (28): LegacyLocator, LegacyStrategy, AccessibleNameLocator, AnchorLocator, DriftLog, FakeLegacyPage, LegacyElement, LegacyTarget (+20 more)

### Community 20 - "ReplaySurface"
Cohesion: 0.18
Nodes (3): Protocol, What a real Playwright-backed surface implements…, ReplaySurface

### Community 21 - "agent.py"
Cohesion: 0.11
Nodes (19): asyncio, base64, dataclasses, dotenv, functools, json, Independent check of the balance, used only to grade the agent., Look up a secret by name. Raises on unknown name or empty value. (+11 more)

### Community 22 - "FakeSurface"
Cohesion: 0.13
Nodes (3): A surface raises this for a step that should be retried (D26): the page was not…, TransientFailure, FakeSurface

### Community 23 - "test_live.py"
Cohesion: 0.07
Nodes (37): _as_text(), _assert_no_secret_values(), _default_label(), EvidenceWriteError, _find_repo(), _load_schema_once(), Exception, Path (+29 more)

### Community 24 - "DECISIONS.md (design decision log)"
Cohesion: 0.12
Nodes (20): examples/get_account_balance.yaml (hand-written illustrative example), Tenant, DECISIONS.md (design decision log), D10: Business/Recoverable/Hard three-way error taxonomy, D12: Typed, locator-based output extraction, D13: get_account_balance (safe) + transfer_funds (risky) demo flows, D18: Cover sensitive fields before screenshot capture, D1: Target Application = ParaBank (+12 more)

### Community 25 - "PlaywrightReplaySurface"
Cohesion: 0.13
Nodes (8): describe_ref(), host_allowed(), LabeledValueRef, PlaywrightReplaySurface, A `resolve()` result for a `labeled_value` locator: not a numbered element ref…, Implements AsyncReplaySurface (04_replay_engine.py Section 7) against the real…, One resolution attempt, no retry -- the exact logic `resolve()` used before D88., D78: for `labeled_value`, go straight to READ_LABELED_JS (no numbered scan at…

### Community 26 - "live.py"
Cohesion: 0.11
Nodes (20): parametrize, re, Look up a secret by NAME. Raises on an unknown name or an empty/missing value.…, resolve_secret(), make_escalate(), escalate(), _prompt_for_missing_input(), Wires the async replay engine (`cua.replay.run_capability_async`) to a REAL… (+12 more)

### Community 27 - "05_replay_live.py"
Cohesion: 0.17
Nodes (11): langgraph_types, _click(), _find_repo_for_engine(), _find_repo_for_evidence(), load_evidence_capture(), load_replay_engine(), Path, Run one Playwright action with the general lock (Setup 5) removed for just that… (+3 more)

### Community 29 - "PlaywrightReplaySurface"
Cohesion: 0.15
Nodes (6): LabeledValueRef, PlaywrightReplaySurface, A `resolve()` result for a `labeled_value` locator: not a numbered element ref…, Implements `AsyncReplaySurface` (`cua.replay`) against the real browser. Wraps…, One resolution attempt, no retry -- the exact logic `resolve()` used before D88., D78: for `labeled_value`, go straight to READ_LABELED_JS (no numbered scan at…

### Community 30 - "04_replay_engine.py"
Cohesion: 0.11
Nodes (13): inspect, describe_locator(), describe_target(), _find_repo(), load_schema(), new_happy_async_surface(), no_secrets(), Path (+5 more)

### Community 31 - "from_yaml"
Cohesion: 0.27
Nodes (13): from_yaml(), D85: escalate returning 'approve' makes the engine click for real and continue…, D85: an approved click that cannot be resolved is a FAILED, never a silent…, resolve_secret_unused(), test_async_integration_both_examples(), run(), test_integration_get_account_balance(), test_integration_transfer_funds_escalate_approves_but_target_unresolvable() (+5 more)

### Community 32 - "test_recorder.py"
Cohesion: 0.12
Nodes (23): Turn what a human filled in during a request_value/request_missing_values…, synthesize_human_entries(), _billpay_handoff_events(), _expect_raises(), Tests for `cua.recorder`'s COMPILE half, ported from…, test_compile_run_leftover_literal_still_refuses(), test_compile_run_request_missing_values_handoff_compiles_with_synthetic_steps(), test_compile_run_unmatched_human_value_is_auto_declared_not_a_constant() (+15 more)

### Community 33 - "Target"
Cohesion: 0.11
Nodes (23): derive_target(), _extract_target(), D68: `label` and `labeled_value` locators have no `within` slot in the schema.…, Descriptor -> Target(primary, fallback). role+name (high, only when the name is…, D101: a `labeled_value` extract step whose CAPTURED resolution is itself a…, _refuse_if_duplicate_label(), _refuse_if_header_value(), _sub() (+15 more)

### Community 34 - "3.3 Deterministic Replay (Production Execution Path)"
Cohesion: 0.19
Nodes (14): Artifact Property: Versioned, Expected Business Outcomes, Glossary: Business Outcome vs. Failure, Hard Failures, Recoverable Conditions, Risky vs. Safe/Reversible Actions Distinction, 3.3 Deterministic Replay (Production Execution Path), Section 8: Optional Stretch Goals (+6 more)

### Community 35 - "PlaywrightSurface"
Cohesion: 0.15
Nodes (5): PlaywrightSurface, The only place that touches Playwright directly. Agent tools talk to this., The single unlocked click path every automated click (agent tool or replay)…, Run one Playwright action with the general lock removed for just that instant…, _unlocked()

### Community 36 - "CLAUDE.md (project instructions)"
Cohesion: 0.19
Nodes (13): balance_check capability artifact, get_account_balance capability artifact (D89 hand-edited), get_account_balance_discovery_demo capability artifact, CLAUDE.md (project instructions), D101: labeled_value refuses a table-header resolution (general fix), D102: label_header/value_header flags ported into agent.py + cli.py capture path, D92: Evidence Capture Helpers (save_discovery_evidence/save_replay_evidence), D95: Missing create_deep_agent import found live in BROWSER 12 (+5 more)

### Community 37 - "PHASE3.md (Recorder write-up)"
Cohesion: 0.18
Nodes (13): my_def pay-bill capability artifact (electricity company), pay_bill capability artifact, PHASE3.md (Recorder write-up), D41-D49: original recorder design (superseded by v2 rebuild), D42: Locator derivation only trusts a real accessible name for role locators, D43: Dropping dead-end click detours from the recording, D44: Turning matched literal values into {{inputs}}, D46: extraction limited to labeled values (known limit) (+5 more)

### Community 38 - "02_artifact_schema.py"
Cohesion: 0.07
Nodes (39): Click, Dismiss, Extract, Failure, InputParam, LabeledValueLocator, LabelLocator, Navigate (+31 more)

### Community 39 - "human_takeover"
Cohesion: 0.17
Nodes (11): _amount(), approval_info(), human_takeover(), make_escalate(), escalate(), needs_human(), Give the live browser to a human. Returns when they click 'Done', OR, if…, Every button except a short safe list needs a human. Links (navigation) run… (+3 more)

### Community 40 - "drop_detours"
Cohesion: 0.17
Nodes (12): drop_detours(), _meaningful(), A click/open_path that changed the page, then a later one that returned to the…, Link clicks after the last meaningful action changed nothing the capability…, D32/D45: everything up to and including the first click after the last…, split_login(), trim_tail(), _ev() (+4 more)

### Community 42 - "clean_events"
Cohesion: 0.31
Nodes (9): clean_events(), drop_dead_end_risky_clicks(), _key(), Keep only actions that worked and mattered. Returns (kept, dropped). dropped =…, D86: remove a risky click proven, by real evidence, to be a dead end. Never…, OFFLINE 13d equivalent (D86): a risky click that changed nothing, retried later…, test_drop_dead_end_risky_click_never_touches_a_real_state_change(), test_drop_dead_end_risky_click_refuses_two_real_state_changes() (+1 more)

### Community 43 - "Section 4: Explicitly Your Call"
Cohesion: 0.17
Nodes (12): Allowlist Guardrail, Architecture & Boundaries Choice, Artifact Schema & Storage/Serialization Choice, Computer-Use Technology Choice, How Determinism Is Achieved on Replay, Language, Runtime & Frameworks Choice, LLM Provider/Model Choice, Section 4: Explicitly Your Call (+4 more)

### Community 44 - "Condition"
Cohesion: 0.18
Nodes (9): Checkpoint, Condition, OutcomeRule, model_validator, The final success check. Both signals must agree (D9)., When `when` matches after a step, treat the page as a business outcome, a…, D10/D47: a bad-input run ended with finish_business_outcome(outcome,…, relogin_rule() (+1 more)

### Community 45 - "resolve_target_async"
Cohesion: 0.22
Nodes (8): Neither the primary nor the fallback locator resolved to an element., Pure: the try-order for a target -- primary, then fallback if present (D63). No…, Try the primary locator, then the fallback if there is one and the primary did…, Async twin of resolve_target (Section 3). Same try-order (`_target_locators`,…, ResolutionError, resolve_target(), resolve_target_async(), _target_locators()

### Community 46 - "recorder.py"
Cohesion: 0.11
Nodes (26): _canon(), _checkpoint_from_last(), _declare_human_input(), _literal_re(), _params(), path_only(), The recorder's COMPILE half: events + declared inputs -> Capability. Ported…, The literal, but not inside a longer word or number: '5' is not found in '$50'… (+18 more)

### Community 47 - "Take-Home Project: Computer-Use Automation System (Assignment Brief)"
Cohesion: 0.25
Nodes (11): Take-Home Project: Computer-Use Automation System (Assignment Brief), Accessibility Tree, Checkpoint, Computer Use, DOM (Document Object Model), Locator / Selector, Test ID, D2: Hybrid screenshot + numbered-element LOOK-THINK-ACT loop (+3 more)

### Community 48 - "3.7 Design for Heterogeneity & Scale"
Cohesion: 0.22
Nodes (11): Eval Criterion: Generalization to the Real Environment, Glossary: Tenant, Multi-Tenant at Scale, Multi-Tenant Artifact Reuse & Specialization, Per-Tenant/Version Drift Detection & Management, REPORT.md Heading 4: Heterogeneity & Multi-Tenant, Section 1: Context, The Real Environment (+3 more)

### Community 49 - "render"
Cohesion: 0.40
Nodes (4): SecretResolver, {{input_name}} from validated caller inputs; {{secret:name}} from the…, render(), test_render_templates()

### Community 50 - "Capability"
Cohesion: 0.09
Nodes (22): Capability, check(), check_result(), derived_routes(), from_yaml(), locator_strings(), malformed_template(), Every text field of a locator that may contain a {{template}}. (+14 more)

### Community 51 - "Any"
Cohesion: 0.15
Nodes (7): _AsyncDictSurface, _DictSurface, _is_approved(), Any, Just enough of a surface to test resolve_target in isolation: resolve(locator)…, Pure: what a risky click's `escalate(reason, ctx)` return value means (D85).…, Async twin of _DictSurface (Section 3b).

### Community 52 - "replay_live"
Cohesion: 0.18
Nodes (10): gather_missing_inputs(), missing_required_inputs(), _prompt_for_missing_input(), Pure, standalone, offline-testable: which of `cap.inputs` (the Phase 2 schema's…, Prompt for exactly one missing required input, showing its own `.description`…, The pre-flight gate itself. Runs BEFORE anything else in `replay_live` -- no…, Load a capability YAML and replay it for real, printing the result. `secrets`…, Look up a secret by name. Raises on unknown name or empty value. (+2 more)

### Community 53 - "ResolutionError"
Cohesion: 0.21
Nodes (10): Try the primary locator, then the fallback if there is one and the primary did…, Neither the primary nor the fallback locator resolved to an element., ResolutionError, resolve_target(), _DictSurface, Any, test_exceptions_are_exceptions(), test_resolve_target_both_miss_raises_naming_both() (+2 more)

### Community 54 - "TypeSafeToolRouterMiddleware"
Cohesion: 0.20
Nodes (7): AgentMiddleware, confidence_gate(), job_tool_names(), Tools this job needs, plus the always-allowed set. Pure: no network, no LLM., Narrow base_tools to this job's tools, but only if the classifier is confident.…, Classifies the step's job with TypeSafe's Choice primitive and narrows the tool…, TypeSafeToolRouterMiddleware

### Community 57 - "_literal_re"
Cohesion: 0.14
Nodes (14): _canon(), contains_literal(), _declare_human_input(), walk(), _literal_re(), _params(), The literal, but not inside a longer word or number: '5' is not found in '$50'…, Replace declared literals with {{name}}. Longest literal first, so a longer… (+6 more)

### Community 58 - "validate_inputs"
Cohesion: 0.20
Nodes (9): InputValidationError, matches_value_type(), Exception, A caller-supplied input is missing, mistyped, or does not match its declared…, Basic format check for a declared ValueType. Used for both inputs (D29) and…, Type/pattern-validate caller-supplied inputs before they are ever substituted…, A surface raises this for a step that should be retried (D26): the page was not…, TransientFailure (+1 more)

### Community 61 - "host_allowed"
Cohesion: 0.22
Nodes (6): _new_tools(), one_at_a_time(), open_path(), The three additive tools the recorder's compiler needs (D73), ported from…, host_allowed(), True if `url`'s host is on the allowlist (D15). ``about:blank`` is always…

### Community 62 - "model_validator"
Cohesion: 0.14
Nodes (10): check(), locator_strings(), malformed_template(), model_validator, Every text field of a locator that may contain a {{template}}., Return (is_secret, name) for every {{...}} reference in text., True if text contains a '{{' that is not a valid reference, e.g. {{Account}}., template_refs() (+2 more)

### Community 65 - "REPORT.md (assignment's 7-heading design write-up)"
Cohesion: 0.28
Nodes (9): examples/transfer_funds.yaml (hand-written illustrative example), Safety & Policy Guardrails, D16: Single redact() choke point for secrets/PII in logs and artifacts, D20: $500 auto-approve threshold for risky transfer/click actions, D64: app/vendor/base/overrides multi-tenant fields cut from schema, REPORT.md (assignment's 7-heading design write-up), REPORT: Cuts section, REPORT: Heterogeneity & multi-tenant section (+1 more)

### Community 66 - "REPORT: Determinism & error handling section"
Cohesion: 0.28
Nodes (9): transfer_funds capability artifact (top-level, real captured), D23: Verify a recorded capability by an immediate no-LLM replay before saving, PHASE4.md (Replay Engine write-up), D77: AsyncReplaySurface / run_capability_async async mirror of the sync engine, PHASE5.md (Replay Against the Real Browser write-up), D85: escalate's return value, not a side effect, decides the click, D87: label normalization must strip a trailing footnote character, D88: resolve() polls (0.4s/5s) to survive an async-loaded account table (+1 more)

### Community 67 - "Depth Over Breadth Principle"
Cohesion: 0.25
Nodes (9): AI-Assisted Development Assumption, Depth Over Breadth Principle, End-to-End Vertical Slice Requirement, Ground Rule: AI-Assisted Development Assumed, Ground Rule: No ToS Violation / Real Credentials, Ground Rule: Time-Box It Yourself, Section 5: Scope & Expectations, Section 9: Ground Rules (+1 more)

### Community 68 - "Section 10: Glossary"
Cohesion: 0.28
Nodes (9): Artifact Field: Target Element/Control Identification, Glossary: Accessibility Tree, Glossary: Deterministic Replay, Glossary: DOM, Glossary: Locator/Selector, Glossary: Test ID, Heterogeneous, Often Legacy Surfaces, Replay Requirement: Stable Element/Control Targeting (+1 more)

### Community 69 - "Deliverable: /REPORT.md"
Cohesion: 0.22
Nodes (9): Cut Depth, Not Whole Capabilities, Deliverable: /REPORT.md, Eval Criterion: Communication, REPORT.md Heading 1: Architecture, REPORT.md Heading 2: Artifact Schema, REPORT.md Heading 7: Cuts, REPORT.md Heading 3: Determinism & Error Handling, REPORT.md Heading 5: Escalation & Handoff (+1 more)

### Community 70 - "Section 7: Evaluation Criteria"
Cohesion: 0.22
Nodes (9): Eval Criterion: Code Quality, Eval Criterion: Robustness & Error Handling, Eval Criterion: Safety & Data Handling, Eval Criterion: System Design, Ground Rule: Keep Secrets Out of the Repo, Problem Step: Stay Within Safety Guardrails, Secrets & Sensitive Data Redaction, 3.4 Safety & Policy Guardrails (+1 more)

### Community 71 - "Section 2: The Problem"
Cohesion: 0.25
Nodes (9): Eval Criterion: Correctness of the Core Loop, Glossary: Computer Use, Problem Step: Escalate to Human When Stuck, Problem Step: Take Natural-Language Goal, Problem Step: LLM Drives Application Surface, Problem Step: Record Successful Run as Artifact, Problem Step: Replay Artifact Deterministically, Section 2: The Problem (+1 more)

### Community 72 - "3.2 Structured Artifact (Agent-Invocable Capability)"
Cohesion: 0.25
Nodes (8): Artifact Field: Checkpoint/Success Condition, Artifact Field: Ordered Steps/Actions, Artifact Property: Reviewable, Artifact Field: Typed Input Parameters, Artifact Field: Typed Outputs/Data to Extract, Glossary: Checkpoint, Replay Requirement: Verify Checkpoint/Success Condition, 3.2 Structured Artifact (Agent-Invocable Capability)

### Community 73 - "Section 3: Core Requirements (Must-Have)"
Cohesion: 0.25
Nodes (8): Deliverable: /evidence/, Deliverable: /README.md, Discovery Run Must Be Real (Non-Negotiable), Richer Failure Signal (Screenshot/DOM Snapshot/Trace), 3.5 Evidence / Observability, Section 3: Core Requirements (Must-Have), Section 6: Deliverables, Structured Log of Agent Actions

### Community 75 - "PlaywrightSurface"
Cohesion: 0.25
Nodes (4): format_elements(), Observation, PlaywrightSurface, The only place that touches Playwright. Agent tools talk to this.

### Community 76 - "PlaywrightSurface"
Cohesion: 0.25
Nodes (4): format_elements(), Observation, PlaywrightSurface, The only place that touches Playwright. Agent tools talk to this.

### Community 77 - "PlaywrightSurface"
Cohesion: 0.25
Nodes (4): format_elements(), Observation, PlaywrightSurface, The only place that touches Playwright. Agent tools talk to this.

### Community 78 - "README.md (setup + demo path)"
Cohesion: 0.29
Nodes (7): Business Outcome vs. Failure, Deterministic Replay, D93: Pre-existing 02_artifact_schema.py IndexError bug, D27: Four-status ReplayResult contract (SUCCESS/BUSINESS_OUTCOME/NEEDS_APPROVAL/FAILED), D31: Offline unit tests only, no live E2E test in CI, D6: Replay is a plain deterministic engine, not an agent, README.md (setup + demo path)

### Community 79 - "3.6 Human-in-the-Loop Escalation & Handoff"
Cohesion: 0.29
Nodes (7): Control-Transfer Model (Pause/Cede/Resume), Eval Criterion: Human-in-the-Loop Escalation, Hand Control Back, Intervention Request, Operator Console Scope Note (Mock Operator UI Allowed), 3.6 Human-in-the-Loop Escalation & Handoff, Take Control of the Live Session

### Community 80 - "PHASE2.md (Artifact Schema write-up)"
Cohesion: 0.29
Nodes (7): PHASE2.md (Artifact Schema write-up), D63: Target simplified to primary + one optional fallback, D65: routes derived from navigate steps, not separately stored, D66: when_to_use folded into description as one field, D67: element-with-no-accessible-name honest gap, D68: label/labeled_value locators cannot be scoped to a container, D70-D76: recorder rebuilt against the v2 schema and current agent.ipynb

### Community 81 - "D32: Agent-driven login via a type_secret(ref, name) tool"
Cohesion: 0.33
Nodes (6): login_parabank capability artifact, Reusable Capability Artifact, D11/D17: Separate login helper reading .env (superseded by D32), D32: Agent-driven login via a type_secret(ref, name) tool, D7: YAML artifact format, validated through Pydantic, D45: split_login() separates login into its own reusable capability

### Community 83 - "Human-in-the-Loop Escalation & Handoff"
Cohesion: 0.40
Nodes (5): Human-in-the-Loop Escalation & Handoff, D14: page.pause() wrapped with a control-state + intervention-request model, D19: Six triggers for detecting a discovery agent is stuck, D91: pre-flight gather_missing_inputs prompts before replay starts, REPORT: Escalation & handoff section

### Community 84 - "current_value"
Cohesion: 0.40
Nodes (4): current_value(), Read whatever is currently in this field, live from the page. Empty string if…, The value shown next to `label` on the current page. Raises LookupError if…, read_labeled_value()

### Community 85 - "Architecture: Agent + Discovery Pipeline"
Cohesion: 0.40
Nodes (4): 1. High-level component architecture, 2. How discovery actually happens (sequence), 3. The clean-DOM gap, explicitly, Architecture: Agent + Discovery Pipeline

### Community 89 - "norm_url"
Cohesion: 0.67
Nodes (3): norm_url(), Relative path + query. Drops the host, the base path, ;jsessionid=... and the…, test_norm_url()

### Community 90 - "value_matches_type"
Cohesion: 0.67
Nodes (3): Same shape as replay's own `matches_value_type` (cua.replay) -- used at CAPTURE…, value_matches_type(), test_value_matches_type()

### Community 100 - "_AsyncDictSurface"
Cohesion: 0.40
Nodes (3): _AsyncDictSurface, test_resolve_target_async_primary_and_fallback(), run()

### Community 102 - "classify_status"
Cohesion: 0.67
Nodes (3): classify_status(), Bucket a tool result's own text by the EXACT prefixes agent.ipynb's tools…, test_classify_status()

## Knowledge Gaps
- **45 isolated node(s):** `interface-ai-cua`, `2. How discovery actually happens (sequence)`, `3. The clean-DOM gap, explicitly`, `Recoverable Conditions`, `Structured Result Reporting` (+40 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 553 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **16 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `DiscoveryAgent` connect `DiscoveryAgent` to `test_cli.py`, `PlaywrightSurface`, `cli.py`, `test_agent.py`, `PlaywrightReplaySurface`, `agent.py`, `Architecture: Agent + Discovery Pipeline`, `live.py`, `.build_tools`, `host_allowed`?**
  _High betweenness centrality (0.075) - this node is a cross-community bridge._
- **Why does `AsyncReplaySurface` connect `AsyncReplaySurface` to `Any`, `run_capability_async`, `resolve_target_async`, `04_replay_engine.py`?**
  _High betweenness centrality (0.021) - this node is a cross-community bridge._
- **Why does `FakeSurface` connect `AsyncFakeSurface` to `validate_inputs`, `04_replay_engine.py`?**
  _High betweenness centrality (0.015) - this node is a cross-community bridge._
- **Are the 11 inferred relationships involving `DiscoveryAgent` (e.g. with `1. High-level component architecture` and `make_escalate()`) actually correct?**
  _`DiscoveryAgent` has 11 INFERRED edges - model-reasoned connections that need verification._
- **Are the 15 inferred relationships involving `Capability` (e.g. with `gather_missing_inputs()` and `make_escalate()`) actually correct?**
  _`Capability` has 15 INFERRED edges - model-reasoned connections that need verification._
- **What connects `interface-ai-cua`, `2. How discovery actually happens (sequence)`, `3. The clean-DOM gap, explicitly` to the rest of the system?**
  _45 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `test_cli.py` be split into smaller, more focused modules?**
  _Cohesion score 0.061224489795918366 - nodes in this community are weakly interconnected._