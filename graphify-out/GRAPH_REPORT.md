# Graph Report - BankerAgent  (2026-09-28)

## Corpus Check
- 59 files · ~172,554 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 1468 nodes · 2912 edges · 88 communities (75 shown, 13 thin omitted)
- Extraction: 90% EXTRACTED · 10% INFERRED · 0% AMBIGUOUS · INFERRED: 278 edges (avg confidence: 0.63)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `8e1b8c88`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- test_cli.py
- observe
- test_live.py
- test_recorder.py
- Five Error Demos (D30)
- 03_recorder.py
- evidence_capture.py
- replay.py
- test_replay.py
- cli.py
- test_agent.py
- FakeSurface
- 02_artifact_schema.py
- DiscoveryAgent
- test_schema.py
- 04_replay_engine.py
- schema.py
- CompileError
- Section 3: Core Requirements (Must-Have)
- agent_2_legacy_surface.py
- validate_inputs
- _unlocked
- FakeSurface
- PlaywrightReplaySurface
- DECISIONS.md (design decision log)
- PlaywrightReplaySurface
- 3.6 Human-in-the-Loop Escalation & Handoff
- 05_replay_live.py
- run_capability_async
- _check_outcomes_async
- _run_async_checks
- _request_missing_values_wrapped
- derive_target
- gather_missing_inputs
- 3.2 Structured Artifact (Agent-Invocable Capability)
- PlaywrightSurface
- CLAUDE.md (project instructions)
- PHASE3.md (Recorder write-up)
- Strict
- _extract_target
- Target
- classify_status
- 01_browser_and_observe.py
- PHASE2.md (Artifact Schema write-up)
- Condition
- build_steps
- recorder.py
- Take-Home Project: Computer-Use Automation System (Assignment Brief)
- 3.7 Design for Heterogeneity & Scale
- agent.py
- Capability
- Any
- Section 4: Explicitly Your Call
- ReplaySurface
- TypeSafeToolRouterMiddleware
- _MinimalSurface
- build_typesafe_middleware
- _e
- _MinimalAsyncSurface
- _MinimalAsyncSurface
- _MinimalSurface
- live.py
- Condition
- Discovery decisions
- 2. Each box, with an example
- _click
- REPORT.md (assignment's 7-heading design write-up)
- 3.4 Safety & Policy Guardrails
- Section 10: Glossary
- Deliverable: /REPORT.md
- 3.3 Deterministic Replay (Production Execution Path)
- Section 2: The Problem
- D32: Agent-driven login via a type_secret(ref, name) tool
- InputParam
- PlaywrightSurface
- PlaywrightSurface
- AsyncReplaySurface
- REPORT: Cuts section
- current_value
- 4. Pure-visual discovery engine (redesign, in design)
- my_cap scratch capability artifact (account 18672, log out)
- Section 11: Submission
- Pause/Resume Human-in-the-Loop Smoke Test
- PlaywrightSurface.observe Design
- derived_routes (D65)
- ReplaySurface Protocol
- PHASE1.md (The Agent write-up)
- interface-ai-cua

## God Nodes (most connected - your core abstractions)
1. `run_capability()` - 41 edges
2. `DiscoveryAgent` - 40 edges
3. `CompileError` - 36 edges
4. `FakeSurface` - 33 edges
5. `DECISIONS.md (design decision log)` - 32 edges
6. `compile_run()` - 27 edges
7. `AsyncReplaySurface` - 27 edges
8. `run_capability_async()` - 27 edges
9. `Target` - 27 edges
10. `run_capability_async()` - 26 edges

## Surprising Connections (you probably didn't know these)
- `D1: Target Application = ParaBank` --conceptually_related_to--> `Tenant`  [INFERRED]
  DECISIONS.md → Assignment A — Computer-Use Automation System (1).pdf
- `D8: Ranked locator strategy (role > label > text > structure)` --rationale_for--> `Locator / Selector`  [EXTRACTED]
  DECISIONS.md → Assignment A — Computer-Use Automation System (1).pdf
- `D8: Ranked locator strategy (role > label > text > structure)` --conceptually_related_to--> `Test ID`  [EXTRACTED]
  DECISIONS.md → Assignment A — Computer-Use Automation System (1).pdf
- `PHASE4.md (Replay Engine write-up)` --semantically_similar_to--> `D23: Verify a recorded capability by an immediate no-LLM replay before saving`  [INFERRED] [semantically similar]
  PHASE4.md → DECISIONS.md
- `test_labeled_value_in_a_click_is_rejected()` --indirect_call--> `bad_click()`  [INFERRED]
  tests/test_schema.py → notebooks/02_artifact_schema.py

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

## Communities (88 total, 13 thin omitted)

### Community 0 - "test_cli.py"
Cohesion: 0.09
Nodes (37): argparse, pytest, SimpleNamespace, test_needs_human_transfer_over_auto_limit_still_risky(), test_needs_human_transfer_under_auto_limit_is_safe(), _discover_args(), _fake_extract_tool(), _fake_page() (+29 more)

### Community 1 - "observe"
Cohesion: 0.10
Nodes (41): _ask_for_value(), ask_human(), _blocks(), current_page(), _describe(), extract_value(), finish(), finish_business_outcome() (+33 more)

### Community 2 - "test_live.py"
Cohesion: 0.12
Nodes (23): InputParam, pathlib, gather_missing_inputs(), missing_required_inputs(), _prompt_for_missing_input(), Pure, standalone, offline-testable: which of `cap.inputs` are `.required` and…, Prompt for exactly one missing required input, showing its own `.description`…, The pre-flight gate itself (D91). Runs BEFORE anything else in `replay_live` --… (+15 more)

### Community 3 - "test_recorder.py"
Cohesion: 0.10
Nodes (43): clean_events(), compile_run(), drop_dead_end_risky_clicks(), _key(), Keep only actions that worked and mattered. Returns (kept, dropped). dropped =…, D86: remove a risky click proven, by real evidence, to be a dead end. Never…, D32/D45: everything up to and including the first click after the last…, Turn what a human filled in during a request_value/request_missing_values… (+35 more)

### Community 4 - "Five Error Demos (D30)"
Cohesion: 0.08
Nodes (39): Roadmap + Phase 1 Plan, Agent-Driven Login (D32/type_secret), Deep Agent + Playwright Architecture, Phase 2 Artifact Schema Plan, Capability Schema Model, Risk-in-Artifact / Limit-in-Config Policy (D38), Phase 3 Recorder Plan (v1), Recorder COMPILE Pipeline (v1) (+31 more)

### Community 5 - "03_recorder.py"
Cohesion: 0.06
Nodes (31): deepagents, langchain_agents_middleware, langchain_tools, langchain_typesafe, langchain_typesafe_experimental_middleware, langgraph_checkpoint_memory, _bare_proxy(), _canon() (+23 more)

### Community 6 - "evidence_capture.py"
Cohesion: 0.13
Nodes (20): json, _as_text(), _assert_no_secret_values(), _default_label(), EvidenceWriteError, _find_repo(), _load_schema_once(), Exception (+12 more)

### Community 7 - "replay.py"
Cohesion: 0.11
Nodes (27): Condition, Failure, _call_escalate(), _check_outcomes(), _check_outcomes_async(), condition_matches(), _fail(), _find_outcome_rule() (+19 more)

### Community 8 - "test_replay.py"
Cohesion: 0.16
Nodes (29): Run every step of `cap` against `surface`, no LLM in the loop (D6, 3.3).…, run_capability(), from_yaml(), new_happy_async_surface(), new_happy_surface(), no_secrets(), Tests for `cua.replay` (sync + async engines), ported from…, D85: escalate returning 'approve' makes the engine click for real and continue… (+21 more)

### Community 9 - "cli.py"
Cohesion: 0.10
Nodes (25): ArgumentParser, functools, build_agent(), Build a ready-to-use `DiscoveryAgent`. If `page` is None, launches a real,…, _build_capture(), build_parser(), _capture(), _first_line() (+17 more)

### Community 10 - "test_agent.py"
Cohesion: 0.08
Nodes (32): confidence_gate(), login_check(), missing_field_labels(), Narrow base_tools to this job's tools, but only if the classifier is confident.…, Pure decision (D69): after a login click, should further attempts be blocked,…, Empty, visible, fillable fields, in page order. Pure: no browser, no network…, _agent(), Tests for `cua.agent`'s pure (or pure-enough-to-test-without-a-browser) logic,… (+24 more)

### Community 11 - "FakeSurface"
Cohesion: 0.15
Nodes (4): FakeSurface, A dict-based fake DOM: pages by url, a locator registry per url, and per-ref…, A surface raises this for a step that should be retried (D26): the page was not…, TransientFailure

### Community 12 - "02_artifact_schema.py"
Cohesion: 0.11
Nodes (18): copy, bad_amount(), bad_click(), bad_order(), check_result(), malformed_template(), missing_note(), ok() (+10 more)

### Community 13 - "DiscoveryAgent"
Cohesion: 0.18
Nodes (9): DiscoveryAgent, One discovery run's worth of browser control state (D33-D62). All state that…, Every button except a short safe list needs a human. Links (navigation) run…, Best available description of an element (D53): the code's own name, the…, Read whatever is currently in this field, live from the page (D54)., Package text and a screenshot as one tool result the model can read., Give the live browser to a human. Returns when they click 'Done', OR, if…, The agent tried to enter a value the user never gave. Hand the browser to a… (+1 more)

### Community 14 - "test_schema.py"
Cohesion: 0.06
Nodes (61): check_result(), derived_routes(), malformed_template(), The pages this capability may touch, derived from its own navigate steps (D65)…, What a calling agent sees: what this capability does, what it needs, what it…, Check a result against the capability that produced it. Raises ValueError on a…, Return (is_secret, name) for every {{...}} reference in text., True if text contains a '{{' that is not a valid reference, e.g. {{Account}}. (+53 more)

### Community 15 - "04_replay_engine.py"
Cohesion: 0.11
Nodes (19): inspect, describe_locator(), describe_target(), _find_repo(), InputValidationError, load_schema(), Exception, Path (+11 more)

### Community 16 - "schema.py"
Cohesion: 0.09
Nodes (40): build_steps(), _check_specs(), CompileError, Exception, Events -> (steps, outputs, secrets, paths). Adds a navigate for the start page,…, The recording cannot become a valid capability. `.problems` lists every reason., Click, Dismiss (+32 more)

### Community 17 - "CompileError"
Cohesion: 0.12
Nodes (24): _cap(), _check_specs(), _checkpoint_from_last(), clean_events(), compile_run(), CompileError, drop_dead_end_risky_clicks(), drop_detours() (+16 more)

### Community 18 - "Section 3: Core Requirements (Must-Have)"
Cohesion: 0.25
Nodes (8): Deliverable: /evidence/, Deliverable: /README.md, Discovery Run Must Be Real (Non-Negotiable), Richer Failure Signal (Screenshot/DOM Snapshot/Trace), 3.5 Evidence / Observability, Section 3: Core Requirements (Must-Have), Section 6: Deliverables, Structured Log of Agent Actions

### Community 19 - "agent_2_legacy_surface.py"
Cohesion: 0.08
Nodes (29): LegacyLocator, LegacyStrategy, AccessibleNameLocator, AnchorLocator, DriftLog, FakeLegacyPage, LegacyElement, LegacyTarget (+21 more)

### Community 20 - "validate_inputs"
Cohesion: 0.25
Nodes (8): parametrize, matches_value_type(), Basic format check for a declared ValueType. Used for both inputs (D29) and…, Type/pattern-validate caller-supplied inputs before they are ever substituted…, validate_inputs(), test_matches_value_type(), test_validate_inputs_ok(), test_validate_inputs_rejects()

### Community 21 - "_unlocked"
Cohesion: 0.33
Nodes (4): _click(), Run one Playwright action with the general lock (Setup 5) removed for just that…, _type_text(), _unlocked()

### Community 22 - "FakeSurface"
Cohesion: 0.10
Nodes (3): AsyncFakeSurface, FakeSurface, _locator_key()

### Community 23 - "PlaywrightReplaySurface"
Cohesion: 0.18
Nodes (4): PlaywrightReplaySurface, Implements `AsyncReplaySurface` (`cua.replay`) against the real browser. Wraps…, One resolution attempt, no retry -- the exact logic `resolve()` used before D88., D78: for `labeled_value`, go straight to READ_LABELED_JS (no numbered scan at…

### Community 24 - "DECISIONS.md (design decision log)"
Cohesion: 0.10
Nodes (24): examples/get_account_balance.yaml (hand-written illustrative example), Business Outcome vs. Failure, Deterministic Replay, Human-in-the-Loop Escalation & Handoff, DECISIONS.md (design decision log), D10: Business/Recoverable/Hard three-way error taxonomy, D12: Typed, locator-based output extraction, D13: get_account_balance (safe) + transfer_funds (risky) demo flows (+16 more)

### Community 25 - "PlaywrightReplaySurface"
Cohesion: 0.14
Nodes (8): describe_ref(), host_allowed(), LabeledValueRef, PlaywrightReplaySurface, A `resolve()` result for a `labeled_value` locator: not a numbered element ref…, Implements AsyncReplaySurface (04_replay_engine.py Section 7) against the real…, One resolution attempt, no retry -- the exact logic `resolve()` used before D88., D78: for `labeled_value`, go straight to READ_LABELED_JS (no numbered scan at…

### Community 26 - "3.6 Human-in-the-Loop Escalation & Handoff"
Cohesion: 0.25
Nodes (8): Control-Transfer Model (Pause/Cede/Resume), Eval Criterion: Human-in-the-Loop Escalation, Hand Control Back, Intervention Request, Operator Console Scope Note (Mock Operator UI Allowed), Problem Step: Escalate to Human When Stuck, 3.6 Human-in-the-Loop Escalation & Handoff, Take Control of the Live Session

### Community 27 - "05_replay_live.py"
Cohesion: 0.11
Nodes (20): langgraph_types, _amount(), _find_repo_for_engine(), _find_repo_for_evidence(), human_takeover(), load_evidence_capture(), load_replay_engine(), make_escalate() (+12 more)

### Community 28 - "run_capability_async"
Cohesion: 0.16
Nodes (17): AsyncFakeSurface, condition_matches(), _fail(), matches_value_type(), parse_amount(), SecretResolver, Async twin of run_capability (Section 4). IDENTICAL behavior -- every surface…, Async twin of FakeSurface (Section 4b). Identical state and behavior -- every… (+9 more)

### Community 29 - "_check_outcomes_async"
Cohesion: 0.25
Nodes (8): _call_escalate(), _check_outcomes(), _check_outcomes_async(), _find_outcome_rule(), Async twin of _check_outcomes (Section 4). Uses the SAME `_find_outcome_rule`…, Pure: the first outcome rule (in declared order) whose condition matches (D10…, First matching rule wins, in declared order (D10's documented order rule)., Call `escalate` and, if it returns something awaitable (a real live…

### Community 30 - "_run_async_checks"
Cohesion: 0.26
Nodes (7): _locator_key(), new_happy_async_surface(), new_happy_surface(), no_secrets(), resolve_secret(), _run_async_checks(), _run_async_integration()

### Community 31 - "_request_missing_values_wrapped"
Cohesion: 0.17
Nodes (19): classify_status(), current_heading(), current_value(), describe_ref(), _extract_value_wrapped(), _finish_wrapped(), _first_line(), missing_field_labels() (+11 more)

### Community 32 - "derive_target"
Cohesion: 0.11
Nodes (21): derive_target(), _extract_target(), Target, D68: `label` and `labeled_value` locators have no `within` slot in the schema.…, Descriptor -> Target(primary, fallback). role+name (high, only when the name is…, D101: a `labeled_value` extract step whose CAPTURED resolution is itself a…, _refuse_if_duplicate_label(), _refuse_if_header_value() (+13 more)

### Community 33 - "gather_missing_inputs"
Cohesion: 0.33
Nodes (6): gather_missing_inputs(), missing_required_inputs(), _prompt_for_missing_input(), Pure, standalone, offline-testable: which of `cap.inputs` (the Phase 2 schema's…, Prompt for exactly one missing required input, showing its own `.description`…, The pre-flight gate itself. Runs BEFORE anything else in `replay_live` -- no…

### Community 34 - "3.2 Structured Artifact (Agent-Invocable Capability)"
Cohesion: 0.18
Nodes (13): Artifact Field: Ordered Steps/Actions, Artifact Property: Reviewable, Artifact Field: Typed Input Parameters, Artifact Field: Typed Outputs/Data to Extract, Artifact Property: Versioned, Risky vs. Safe/Reversible Actions Distinction, 3.2 Structured Artifact (Agent-Invocable Capability), Section 8: Optional Stretch Goals (+5 more)

### Community 35 - "PlaywrightSurface"
Cohesion: 0.18
Nodes (6): PlaywrightSurface, The only place that touches Playwright directly. Agent tools talk to this., The single unlocked click path every automated click (agent tool or replay)…, Run one Playwright action with the general lock removed for just that instant…, _unlocked(), test_playwright_surface_name_of_looks_up_last_elements()

### Community 36 - "CLAUDE.md (project instructions)"
Cohesion: 0.21
Nodes (12): balance_check capability artifact, get_account_balance capability artifact (D89 hand-edited), get_account_balance_discovery_demo capability artifact, CLAUDE.md (project instructions), D101: labeled_value refuses a table-header resolution (general fix), D102: label_header/value_header flags ported into agent.py + cli.py capture path, D92: Evidence Capture Helpers (save_discovery_evidence/save_replay_evidence), D95: Missing create_deep_agent import found live in BROWSER 12 (+4 more)

### Community 37 - "PHASE3.md (Recorder write-up)"
Cohesion: 0.18
Nodes (13): my_def pay-bill capability artifact (electricity company), pay_bill capability artifact, PHASE3.md (Recorder write-up), D41-D49: original recorder design (superseded by v2 rebuild), D42: Locator derivation only trusts a real accessible name for role locators, D43: Dropping dead-end click detours from the recording, D44: Turning matched literal values into {{inputs}}, D46: extraction limited to labeled values (known limit) (+5 more)

### Community 38 - "Strict"
Cohesion: 0.17
Nodes (16): Dismiss, Failure, LabelLocator, BaseModel, Base for every model. Unknown keys are errors, so a typo in a YAML file cannot…, Scope a locator to a container, e.g. the login form., The nth <tag> inside a container'. `within` is required: a page-wide index…, RoleLocator (+8 more)

### Community 39 - "_extract_target"
Cohesion: 0.40
Nodes (5): LabeledValueLocator, The value shown next to a label, e.g. the cell after 'Balance:'. Only valid in…, _extract_target(), D68: `label` and `labeled_value` locators have no `within` slot in the schema.…, _refuse_if_duplicate_label()

### Community 40 - "Target"
Cohesion: 0.16
Nodes (9): Checkpoint, locator_strings(), _no_labeled_value(), model_validator, Exactly one primary locator, one optional fallback (D63). A third locator is…, All locators in try-order: primary, then fallback if present., Every text field of a locator that may contain a {{template}}., The final success check. Both signals must agree (D9). (+1 more)

### Community 41 - "classify_status"
Cohesion: 0.67
Nodes (3): classify_status(), Bucket a tool result's own text by the EXACT prefixes agent.ipynb's tools…, test_classify_status()

### Community 42 - "01_browser_and_observe.py"
Cohesion: 0.10
Nodes (14): asyncio, base64, dataclasses, dotenv, format_elements(), Observation, PlaywrightSurface, Independent check of the balance, used only to grade the agent. (+6 more)

### Community 43 - "PHASE2.md (Artifact Schema write-up)"
Cohesion: 0.20
Nodes (10): Tenant, D1: Target Application = ParaBank, D21: Base capability + per-tenant overrides, with a drift signal, PHASE2.md (Artifact Schema write-up), D64: app/vendor/base/overrides multi-tenant fields cut from schema, D65: routes derived from navigate steps, not separately stored, D66: when_to_use folded into description as one field, D67: element-with-no-accessible-name honest gap (+2 more)

### Community 44 - "Condition"
Cohesion: 0.17
Nodes (11): Condition, OutcomeRule, When `when` matches after a step, treat the page as a business outcome, a…, contains_literal(), _literal_re(), D10/D47: a bad-input run ended with finish_business_outcome(outcome,…, The literal, but not inside a longer word or number: '5' is not found in '$50'…, Replace declared literals with {{name}}. Longest literal first, so a longer… (+3 more)

### Community 45 - "build_steps"
Cohesion: 0.29
Nodes (10): Click, Extract, Navigate, OutputParam, Select, StepBase, TypeText, _amount_input() (+2 more)

### Community 46 - "recorder.py"
Cohesion: 0.06
Nodes (46): Checkpoint, pydantic, _amount_input(), _canon(), _cap(), _checkpoint_from_last(), contains_literal(), _declare_human_input() (+38 more)

### Community 47 - "Take-Home Project: Computer-Use Automation System (Assignment Brief)"
Cohesion: 0.25
Nodes (11): Take-Home Project: Computer-Use Automation System (Assignment Brief), Accessibility Tree, Checkpoint, Computer Use, DOM (Document Object Model), Locator / Selector, Test ID, D2: Hybrid screenshot + numbered-element LOOK-THINK-ACT loop (+3 more)

### Community 48 - "3.7 Design for Heterogeneity & Scale"
Cohesion: 0.22
Nodes (11): Eval Criterion: Generalization to the Real Environment, Glossary: Tenant, Multi-Tenant at Scale, Multi-Tenant Artifact Reuse & Specialization, Per-Tenant/Version Drift Detection & Management, REPORT.md Heading 4: Heterogeneity & Multi-Tenant, Section 1: Context, The Real Environment (+3 more)

### Community 49 - "agent.py"
Cohesion: 0.11
Nodes (17): os, build_langchain_agent(), format_elements(), job_tool_names(), Observation, page_name_from_url(), The discovery agent: deep agents + Playwright tools, safety/lock/takeover…, Wrap a tool list in a deep agent (D4) with the standard checkpointer. Kept as a… (+9 more)

### Community 50 - "Capability"
Cohesion: 0.17
Nodes (13): Capability, derived_routes(), from_yaml(), The pages this capability may touch, derived from its own navigate steps (D65)…, Stable, human-readable YAML. Keys keep the model's field order., What a calling agent sees: what this capability does, what it needs, what it…, to_yaml(), tool_contract() (+5 more)

### Community 51 - "Any"
Cohesion: 0.15
Nodes (7): _AsyncDictSurface, _DictSurface, _is_approved(), Any, Just enough of a surface to test resolve_target in isolation: resolve(locator)…, Pure: what a risky click's `escalate(reason, ctx)` return value means (D85).…, Async twin of _DictSurface (Section 3b).

### Community 52 - "Section 4: Explicitly Your Call"
Cohesion: 0.18
Nodes (11): Architecture & Boundaries Choice, Artifact Schema & Storage/Serialization Choice, Computer-Use Technology Choice, How Determinism Is Achieved on Replay, Ground Rule: No ToS Violation / Real Credentials, Language, Runtime & Frameworks Choice, LLM Provider/Model Choice, Section 4: Explicitly Your Call (+3 more)

### Community 53 - "ReplaySurface"
Cohesion: 0.08
Nodes (19): describe_locator(), describe_target(), _is_approved(), Any, Protocol, Target, Pure: the try-order for a target -- primary, then fallback if present (D63). No…, Try the primary locator, then the fallback if there is one and the primary did… (+11 more)

### Community 54 - "TypeSafeToolRouterMiddleware"
Cohesion: 0.20
Nodes (7): AgentMiddleware, confidence_gate(), job_tool_names(), Tools this job needs, plus the always-allowed set. Pure: no network, no LLM., Narrow base_tools to this job's tools, but only if the classifier is confident.…, Classifies the step's job with TypeSafe's Choice primitive and narrows the tool…, TypeSafeToolRouterMiddleware

### Community 56 - "build_typesafe_middleware"
Cohesion: 0.27
Nodes (10): build_typesafe_middleware(), Build the D50/D52 TypeSafe middleware list (tool router + model router),…, No TYPESAFE_API_KEY in the environment: returns [] -- the caller's agent then…, THE fix under test: when TYPESAFE_API_KEY is set, this must build the SAME two…, D76's extension must actually reach the constructed middleware, not just exist…, test_build_typesafe_middleware_builds_both_layers_when_key_set(), test_build_typesafe_middleware_empty_key_is_also_off(), test_build_typesafe_middleware_extra_never_hide_reaches_the_tool_router() (+2 more)

### Community 57 - "_e"
Cohesion: 0.60
Nodes (5): _balance_events(), _balance_events_with_agent_note(), _balance_events_with_detour(), _e(), Same shape as `_ev` above, kept separate so a message/status default of 'ok'…

### Community 61 - "live.py"
Cohesion: 0.10
Nodes (23): LabeledValueRef, make_escalate(), Capability, ReplayResult, Wires the async replay engine (`cua.replay.run_capability_async`) to a REAL…, Runs the SAME DECISION_JS bar `DiscoveryAgent.click()` shows. The general lock…, Returns an `escalate(reason, ctx)` closure for this one capability. Passed as…, Load a capability YAML and replay it for real, printing the result. `secrets`… (+15 more)

### Community 62 - "Condition"
Cohesion: 0.16
Nodes (12): OutcomeRule, D10/D47: a bad-input run ended with finish_business_outcome(outcome,…, relogin_rule(), rule_from_probe(), Checkpoint, Condition, OutcomeRule, model_validator (+4 more)

### Community 63 - "Discovery decisions"
Cohesion: 0.13
Nodes (14): Base decisions, Discovery decisions, Q10: window size and zoom — DECIDED, Q11: notebook format — DECIDED, Q12: dropdowns — DECIDED, Q13: scrolling — DECIDED, Q14: private data in saved pictures — DECIDED, Q7: things with no text — DECIDED (+6 more)

### Community 64 - "2. Each box, with an example"
Cohesion: 0.14
Nodes (13): 1. Diagram, 2. Each box, with an example, 3. All tools, 4. Step by step: one discovery run, 5. Notes, Browser (Playwright), Discovery architecture, DiscoveryAgent (LLM) (+5 more)

### Community 65 - "_click"
Cohesion: 0.22
Nodes (10): _amount(), approval_info(), _click(), human_takeover(), login_check(), needs_human(), Give the live browser to a human. Returns when they click 'Done', OR, if…, Every button except a short safe list needs a human. Links (navigation) run… (+2 more)

### Community 66 - "REPORT.md (assignment's 7-heading design write-up)"
Cohesion: 0.21
Nodes (12): transfer_funds capability artifact (top-level, real captured), D23: Verify a recorded capability by an immediate no-LLM replay before saving, PHASE4.md (Replay Engine write-up), D77: AsyncReplaySurface / run_capability_async async mirror of the sync engine, PHASE5.md (Replay Against the Real Browser write-up), D85: escalate's return value, not a side effect, decides the click, D87: label normalization must strip a trailing footnote character, D88: resolve() polls (0.4s/5s) to survive an async-loaded account table (+4 more)

### Community 67 - "3.4 Safety & Policy Guardrails"
Cohesion: 0.17
Nodes (13): AI-Assisted Development Assumption, Depth Over Breadth Principle, End-to-End Vertical Slice Requirement, Eval Criterion: Safety & Data Handling, Ground Rule: AI-Assisted Development Assumed, Ground Rule: Keep Secrets Out of the Repo, Ground Rule: Time-Box It Yourself, Problem Step: Stay Within Safety Guardrails (+5 more)

### Community 68 - "Section 10: Glossary"
Cohesion: 0.22
Nodes (11): Artifact Field: Checkpoint/Success Condition, Artifact Field: Target Element/Control Identification, Glossary: Checkpoint, Glossary: Deterministic Replay, Glossary: DOM, Glossary: Locator/Selector, Glossary: Test ID, Heterogeneous, Often Legacy Surfaces (+3 more)

### Community 69 - "Deliverable: /REPORT.md"
Cohesion: 0.22
Nodes (9): Cut Depth, Not Whole Capabilities, Deliverable: /REPORT.md, Eval Criterion: Communication, REPORT.md Heading 1: Architecture, REPORT.md Heading 2: Artifact Schema, REPORT.md Heading 7: Cuts, REPORT.md Heading 3: Determinism & Error Handling, REPORT.md Heading 5: Escalation & Handoff (+1 more)

### Community 70 - "3.3 Deterministic Replay (Production Execution Path)"
Cohesion: 0.27
Nodes (10): Eval Criterion: Code Quality, Eval Criterion: Robustness & Error Handling, Eval Criterion: System Design, Expected Business Outcomes, Glossary: Business Outcome vs. Failure, Hard Failures, Recoverable Conditions, 3.3 Deterministic Replay (Production Execution Path) (+2 more)

### Community 71 - "Section 2: The Problem"
Cohesion: 0.25
Nodes (9): Eval Criterion: Correctness of the Core Loop, Glossary: Accessibility Tree, Glossary: Computer Use, Problem Step: Take Natural-Language Goal, Problem Step: LLM Drives Application Surface, Problem Step: Record Successful Run as Artifact, Problem Step: Replay Artifact Deterministically, Section 2: The Problem (+1 more)

### Community 73 - "D32: Agent-driven login via a type_secret(ref, name) tool"
Cohesion: 0.18
Nodes (11): login_parabank capability artifact, Reusable Capability Artifact, D93: Pre-existing 02_artifact_schema.py IndexError bug, D11/D17: Separate login helper reading .env (superseded by D32), D31: Offline unit tests only, no live E2E test in CI, D32: Agent-driven login via a type_secret(ref, name) tool, D7: YAML artifact format, validated through Pydantic, D63: Target simplified to primary + one optional fallback (+3 more)

### Community 75 - "PlaywrightSurface"
Cohesion: 0.29
Nodes (4): format_elements(), Observation, PlaywrightSurface, The only place that touches Playwright. Agent tools talk to this.

### Community 76 - "PlaywrightSurface"
Cohesion: 0.22
Nodes (5): approval_info(), format_elements(), Observation, PlaywrightSurface, The only place that touches Playwright. Agent tools talk to this.

### Community 77 - "AsyncReplaySurface"
Cohesion: 0.11
Nodes (5): AsyncReplaySurface, Protocol, What a real Playwright-backed surface will implement in Phase 9 (see the…, The async twin of ReplaySurface (Section 2). Same method names, same meanings…, ReplaySurface

### Community 78 - "REPORT: Cuts section"
Cohesion: 0.22
Nodes (9): examples/transfer_funds.yaml (hand-written illustrative example), Allowlist Guardrail, Safety & Policy Guardrails, D99: TypeSafe tool/model-router middleware ported into src/cua, D15: Domain+route+action allowlist enforced in tool code before Playwright acts, D16: Single redact() choke point for secrets/PII in logs and artifacts, D20: $500 auto-approve threshold for risky transfer/click actions, REPORT: Cuts section (+1 more)

### Community 84 - "current_value"
Cohesion: 0.40
Nodes (4): current_value(), Read whatever is currently in this field, live from the page. Empty string if…, The value shown next to `label` on the current page. Raises LookupError if…, read_labeled_value()

### Community 85 - "4. Pure-visual discovery engine (redesign, in design)"
Cohesion: 0.20
Nodes (9): 1. High-level component architecture, 2. How discovery actually happens (sequence), 3. The clean-DOM gap, explicitly, 4. Pure-visual discovery engine (redesign, in design), Architecture: Agent + Discovery Pipeline, Decided (user-confirmed), Discovery engine — block diagram, Open questions (NOT decided) (+1 more)

## Knowledge Gaps
- **71 isolated node(s):** `interface-ai-cua`, `1. High-level component architecture`, `2. How discovery actually happens (sequence)`, `3. The clean-DOM gap, explicitly`, `Why` (+66 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **13 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `DiscoveryAgent` connect `DiscoveryAgent` to `test_cli.py`, `observe`, `PlaywrightSurface`, `cli.py`, `test_agent.py`, `agent.py`, `PlaywrightReplaySurface`, `build_typesafe_middleware`, `live.py`?**
  _High betweenness centrality (0.055) - this node is a cross-community bridge._
- **Why does `PlaywrightReplaySurface` connect `PlaywrightReplaySurface` to `05_replay_live.py`, `current_value`, `_unlocked`?**
  _High betweenness centrality (0.030) - this node is a cross-community bridge._
- **Why does `_MinimalAsyncSurface` connect `_MinimalAsyncSurface` to `04_replay_engine.py`?**
  _High betweenness centrality (0.021) - this node is a cross-community bridge._
- **Are the 3 inferred relationships involving `DiscoveryAgent` (e.g. with `LabeledValueRef` and `PlaywrightReplaySurface`) actually correct?**
  _`DiscoveryAgent` has 3 INFERRED edges - model-reasoned connections that need verification._
- **Are the 18 inferred relationships involving `CompileError` (e.g. with `Capability` and `Checkpoint`) actually correct?**
  _`CompileError` has 18 INFERRED edges - model-reasoned connections that need verification._
- **Are the 9 inferred relationships involving `FakeSurface` (e.g. with `AsyncReplaySurface` and `InputValidationError`) actually correct?**
  _`FakeSurface` has 9 INFERRED edges - model-reasoned connections that need verification._
- **What connects `interface-ai-cua`, `1. High-level component architecture`, `2. How discovery actually happens (sequence)` to the rest of the system?**
  _71 weakly-connected nodes found - possible documentation gaps or missing edges._