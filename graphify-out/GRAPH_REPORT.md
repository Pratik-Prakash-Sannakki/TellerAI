# Graph Report - BankerAgent  (2026-10-01)

## Corpus Check
- 126 files · ~234,752 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 1528 nodes · 3067 edges · 93 communities (75 shown, 18 thin omitted)
- Extraction: 96% EXTRACTED · 4% INFERRED · 0% AMBIGUOUS · INFERRED: 137 edges (avg confidence: 0.7)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `4f692a8e`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- argparse
- asyncio
- Productionize Plan: notebooks → `src/cua/` package
- test_extract_table.py
- Evidence README
- langchain_agents_middleware
- test_select_index.py
- test_handback_button.py
- value_in_box
- sys
- like_rows
- save_discovery_evidence / save_replay_evidence (D92)
- Replay decisions
- Five Error Demos (D30)
- langchain_typesafe
- langchain_typesafe_experimental_middleware
- test_cleanup.py
- test_sent_dropdowns.py
- SimpleNamespace
- json
- test_models.py
- test_resolve_inputs.py
- .click
- test_transaction_gates.py
- HeldPage
- HumanControl
- test_handback.py
- Ext
- integration/conftest.py
- discovery.py
- Capability
- HangPage
- test_checks.py
- Element
- CLAUDE.md (project instructions)
- click
- manifest.json
- replay
- test_select_anchor.py
- replay.py
- take_look
- handback_button
- take_look
- test_choose_option.py
- test_takeover.py
- test_engine.py
- LatestScreenshotOnly
- test_read_runs.py
- langgraph_types
- Discovery decisions
- 2. Each box, with an example
- Look
- 2. Components
- ControlWindow
- Pure-Visual Discovery Notebook: Build Plan
- SiteLock
- test_evidence.py
- guard_send
- test_observable.py
- mk_look
- run_goal
- test_label_values.py
- test_extract_types.py
- test_no_values_stored.py
- test_http_errors.py
- test_adjacent_selects.py
- copy
- test_partial_outputs.py
- test_round_trip.py
- interface-ai-cua
- test_replay_evidence.py
- test_table_replay.py
- ControlWindow
- HeldRoute
- _meta
- test_control_form.py
- Replay notebook plan
- FakePage
- SiteLock
- test_wandering.py
- .get
- inspect
- background.js
- Look
- test_extract_pattern.py
- Site
- read_rows
- do_type
- test_prompt_rules.py
- test_login_click_kept.py
- _fake_llm_keys
- pathlib
- _look_ns

## God Nodes (most connected - your core abstractions)
1. `_meta()` - 58 edges
2. `_ev()` - 46 edges
3. `mk_look()` - 37 edges
4. `Capability` - 28 edges
5. `Look` - 24 edges
6. `click()` - 23 edges
7. `Replay decisions` - 23 edges
8. `Discovery decisions` - 22 edges
9. `Element` - 21 edges
10. `take_look()` - 20 edges

## Surprising Connections (you probably didn't know these)
- `test_the_right_label_still_matches()` --calls--> `same_label()`  [INFERRED]
  tests/replay/test_adjacent_selects.py → notebooks/replay/replay.py
- `test_value_glued_to_hash_confirms_the_option()` --calls--> `shows()`  [INFERRED]
  tests/replay/test_adjacent_selects.py → notebooks/replay/replay.py
- `_logged()` --indirect_call--> `where()`  [INFERRED]
  tests/discovery/test_sent_dropdowns.py → notebooks/discovery/discovery.py
- `test_offer_control_shows_only_the_reason()` --indirect_call--> `human_help()`  [INFERRED]
  tests/discovery/test_choose_option.py → notebooks/discovery/discovery.py
- `_open_path()` --indirect_call--> `reply()`  [INFERRED]
  tests/discovery/test_wandering.py → notebooks/discovery/discovery.py

## Import Cycles
- None detected.

## Communities (93 total, 18 thin omitted)

### Community 1 - "asyncio"
Cohesion: 0.09
Nodes (14): asyncio, FakeControl, FakePage, FakeRoute, Shared offline fakes for the ported test suite (tests/unit, tests/integration).…, The handful of ``playwright.async_api.Request`` fields the project's code reads., A fake ``playwright.async_api.Route``: records every…, A fake ``playwright.async_api.Page``. Every awaited method is recorded in… (+6 more)

### Community 2 - "Productionize Plan: notebooks → `src/cua/` package"
Cohesion: 0.12
Nodes (16): 10. Line-count offenders (today), 1. Package tree, 2. De-duplication (checked by AST diff of both notebooks), 3. State: globals → explicit objects, 4. Async and typing, 5. Notebooks after the move, 6. Tests, 7. ML-engineering practices (kept small) (+8 more)

### Community 3 - "test_extract_table.py"
Cohesion: 0.16
Nodes (23): Handoff, _look(), _ns(), extract_table: the agent points at a header, code reads the rows from OCR (live…, Live run: the page footer ('Home | About Us I Services …', '© Parasoft …') sat…, _read(), _table_ev(), test_a_header_holding_a_run_value_is_refused() (+15 more)

### Community 6 - "test_select_index.py"
Cohesion: 0.21
Nodes (10): _js(), _Page, Two dropdowns side by side: the step's recorded index picks its own <select>,…, Run replay's real SELECT_AT_JS in node against a fake page holding FROM and TO., _select(), test_an_index_picks_its_own_dropdown_from_a_point_nearer_the_other(), test_an_old_step_without_an_index_selects_by_point(), test_the_confirm_is_not_fooled_by_a_longer_number() (+2 more)

### Community 7 - "test_handback_button.py"
Cohesion: 0.08
Nodes (25): playwright_async_api, FakeBox, into_box clears the field before typing, so a retry replaces instead of…, test_typing_twice_does_not_double(), _click(), env(), Ext, Human (+17 more)

### Community 8 - "value_in_box"
Cohesion: 0.50
Nodes (4): True when the whole value is exactly that type (string, number, boolean, or a…, (value, pattern) for an extract: the whole box when it is exactly the type,…, value_in_box(), value_matches_type()

### Community 10 - "like_rows"
Cohesion: 0.50
Nodes (4): cell_shape(), like_rows(), A table's end: a line that no longer looks like its rows (a footer, a menu, a…, date', 'amount', or 'text': enough to tell a row cell from a footer line in its…

### Community 12 - "Replay decisions"
Cohesion: 0.08
Nodes (23): R10: where the compile step lives — DECIDED, R11: why compile, if `response_format` exists? — PROPOSED, R12: what each step type compiles to — PROPOSED, R13: target schema — PROPOSED, R14: what rung 2 needs that discovery doesn't record — DONE, R15: auto-approve at replay — PROPOSED, R16: dead ends and retries at compile — PROPOSED, R17: replay result statuses — PROPOSED (+15 more)

### Community 16 - "test_cleanup.py"
Cohesion: 0.38
Nodes (12): _cap(), _click(), fixture, Cleanup steps (e.g. Log Out) run last, always, best-effort, and never change…, _run(), site(), test_a_cleanup_failure_keeps_success_and_records_failed(), test_a_cleanup_miss_is_retried_once_then_recorded_without_a_rescue() (+4 more)

### Community 17 - "test_sent_dropdowns.py"
Cohesion: 0.33
Nodes (8): _logged(), Path, A dropdown the send carries becomes a Select step, even when left on its page…, test_a_defaulted_dropdown_the_send_carries_is_logged_without_its_value(), test_a_dropdown_the_send_does_not_carry_is_not_a_step(), test_a_select_the_agent_made_earlier_is_not_doubled(), test_it_becomes_a_select_input_before_the_send_click(), urllib_parse

### Community 18 - "SimpleNamespace"
Cohesion: 0.05
Nodes (42): SimpleNamespace, Control, Lock, _no_watch(), Page, parametrize, human_help: one open-ended panel -> answer in words, take over, or stop., Run human_help's take-over; `during(page)` is what the human does before… (+34 more)

### Community 19 - "json"
Cohesion: 0.29
Nodes (3): json, The hand-back extension never touches any site: no content scripts, no host…, The hand-back extension never touches any site: no content scripts, no host…

### Community 20 - "test_models.py"
Cohesion: 0.07
Nodes (32): BaseChatModel, CaptureFixture, dotenv, ModelKind, os, host_allowed(), Shared configuration: the app this system points at, secret lookup, and the…, Look up a secret by NAME. Raises on an unknown name or an empty/missing value.… (+24 more)

### Community 21 - "test_resolve_inputs.py"
Cohesion: 0.12
Nodes (23): _ask(), _cap(), ClearPage, _click(), env(), FakeForm, FakePage, fixture (+15 more)

### Community 22 - ".click"
Cohesion: 0.36
Nodes (10): _cap(), _click(), _fail_clicks(), Live: the human finished the whole form during a take-over; step 6 then 'target…, test_checkpoint_reached_by_the_human_skips_the_remaining_steps(), test_click_stashes_the_dropdowns_before_clicking(), test_no_take_over_means_an_empty_list(), test_no_values_in_the_take_over_entry() (+2 more)

### Community 23 - "test_transaction_gates.py"
Cohesion: 0.11
Nodes (34): functools, Control, _guard_ns(), _held_navigation(), HeldPage, _no_dropdowns(), _opts(), parametrize (+26 more)

### Community 24 - "HeldPage"
Cohesion: 0.29
Nodes (5): DoneWhileSending, HeldPage, Like Playwright: while a form POST (a navigation) is held, `page.screenshot()`…, The human clicks Done just as their form POST is held: the gate must still show…, test_no_deadlock_between_a_pending_gate_and_done()

### Community 25 - "HumanControl"
Cohesion: 0.29
Nodes (3): Frame, HumanControl, Takes over; while 'in control', the human opens a page and sends a form.

### Community 26 - "test_handback.py"
Cohesion: 0.16
Nodes (12): take_over's hand-back: the extension's toolbar button (never the site), with no…, The user's rule: no "are you done?" prompts in between. Only the take-over…, test_a_click_on_the_toolbar_button_hands_back(), test_done_in_the_takeover_itself_cancels_the_watcher(), test_no_extension_still_hands_back_from_the_control_tab(), test_no_idle_reminder_ever_interrupts_the_take_over(), test_the_badge_reads_you_during_the_take_over_then_ai(), test_the_button_never_touches_the_site_page() (+4 more)

### Community 29 - "discovery.py"
Cohesion: 0.07
Nodes (52): BaseModel, deepagents, langchain_tools, langgraph_checkpoint_memory, model_validator, after_login_click(), Anchor, build_capability() (+44 more)

### Community 32 - "Capability"
Cohesion: 0.07
Nodes (49): Exception, Capability, act(), do_click(), do_extract(), do_navigate(), do_scroll(), error_page() (+41 more)

### Community 33 - "HangPage"
Cohesion: 0.12
Nodes (9): FormRoute, HangPage, NeverAnsweredGate, `evaluate` also never returns while a request is held, as live., Answers each gate from a script; records what each form offered., The human clicks Done while their own send's Gate 1 is still open and never…, ScriptedControl, test_agent_send_uses_the_stash_not_the_page() (+1 more)

### Community 34 - "test_checks.py"
Cohesion: 0.13
Nodes (19): _click_env(), _form_png(), _Lock, _Page, parametrize, Step checks on fakes: whole-field read (A), tolerant word match (B), late page…, Live bug: the Transfer click sent (both gates approved) but its check said…, Live: Address '1' failed twice: OCR does not read a lone character. The field's… (+11 more)

### Community 35 - "Element"
Cohesion: 0.10
Nodes (25): Box, canvas(), col_of(), column_spans(), crop_box(), Element, element_at(), field_box() (+17 more)

### Community 36 - "CLAUDE.md (project instructions)"
Cohesion: 0.12
Nodes (19): CLAUDE.md (project instructions), D101: labeled_value refuses a table-header resolution (general fix), D102: label_header/value_header flags ported into agent.py + cli.py capture path, D92: Evidence Capture Helpers (save_discovery_evidence/save_replay_evidence), D93: Pre-existing 02_artifact_schema.py IndexError bug, D95: Missing create_deep_agent import found live in BROWSER 12, D96: build_agent() goal_text vs given_text field-name bug, D97: cua replay --login flag + repeated Balance header trap (+11 more)

### Community 38 - "click"
Cohesion: 0.09
Nodes (49): act(), ask_human(), blocks(), choose_option(), click(), cut_crop(), extract_value(), finish_business_outcome() (+41 more)

### Community 39 - "manifest.json"
Cohesion: 0.11
Nodes (18): action, default_icon, default_title, background, service_worker, 128, 16, 32 (+10 more)

### Community 40 - "replay"
Cohesion: 0.12
Nodes (15): ask_inputs(), given_inputs(), load_outcomes(), A run that stopped: its status, the failure detail (R17) and the final screen…, Working values for one run. Wiped in `replay`'s `finally` (R7)., The capability's own `outcomes:` [{text, status, meaning}], else the generic…, The caller's values, by the capability's own input names (any case). Any other…, Every `{{input}}` the steps use, in step order, once each. (+7 more)

### Community 41 - "test_select_anchor.py"
Cohesion: 0.22
Nodes (11): _look_ns(), Path, A dropdown's point inside an OCR box that merged its label and value ('to…, A box's own text with nothing cut from it (a value, a button) stays off the…, _select_ev(), test_a_plain_word_under_the_point_is_still_never_the_anchor(), test_a_point_inside_a_merged_label_and_value_box_anchors_on_the_cleaned_label(), test_a_select_with_no_anchor_is_refused_not_saved() (+3 more)

### Community 42 - "replay.py"
Cohesion: 0.09
Nodes (37): Future, _clean(), Config, discovery_schema(), dropdown_options(), _flat(), guard_send(), hand_back() (+29 more)

### Community 43 - "take_look"
Cohesion: 0.19
Nodes (16): decode(), draw_numbered(), encode(), find_template(), _img(), mask_png(), ocr(), open_start() (+8 more)

### Community 44 - "handback_button"
Cohesion: 0.40
Nodes (6): button_clicked(), ext_call(), handback_button(), R19: one bounded call into the hand-back extension's service worker, never the…, Returns once the toolbar button's click count rises above where it was at the…, Badge YOU while the human is in control; yields the task a toolbar click…

### Community 48 - "take_look"
Cohesion: 0.10
Nodes (25): Box, canvas(), crop_box(), decode(), draw_numbered(), encode(), _img(), mask_png() (+17 more)

### Community 50 - "test_choose_option.py"
Cohesion: 0.22
Nodes (11): _fns(), Page, Dropdowns (option B): read every option and select by value, for the <select>…, Mimics SELECT_AT_JS against one <select> at (100, 50); nothing else on the page., The user's bug: two accounts, only one showed., The red box showed the whole tool reply (URL, every OCR line) instead of the…, test_lists_every_option_values_only(), test_missing_option_is_refused() (+3 more)

### Community 53 - "test_takeover.py"
Cohesion: 0.23
Nodes (9): GateControl, HumanControlSimple, A take-over is recorded as evidence (shots, page paths, send paths, no values)…, take_look screenshots the page, as the real one does., _real_shots(), test_done_hands_back_within_a_timeout_as_stuck(), test_navigation_send_never_screenshots_and_the_gate_shows(), test_stash_read_on_a_held_page_times_out_to_empty() (+1 more)

### Community 55 - "test_engine.py"
Cohesion: 0.25
Nodes (16): _cap(), _click(), engine(), FakeControl, fixture, The step loop on a fake page: success, one retry, never re-send, stuck on a…, ns with a fake page: `take_look` returns the fixed look; actions are scripted., _script() (+8 more)

### Community 56 - "LatestScreenshotOnly"
Cohesion: 0.24
Nodes (5): AgentMiddleware, LatestScreenshotOnly, NoopAnthropicPromptCachingMiddleware, Disable prompt caching on the Iliad gateway; it rejects Anthropic cache markers., Old screenshots are stale (their numbers no longer work); send the model only…

### Community 58 - "test_read_runs.py"
Cohesion: 0.15
Nodes (23): _cell(), _look(), _ns(), Read-only runs (live: view_account_details_and_transactions): the checkpoint…, Live: available_amount got row_key 'Transfer Funds', column 'Welcome to Account…, Menu gap == column gap: nothing tells them apart, so no row key (the anchor is…, Only text seen on that look can be the checkpoint: an event with no page_texts…, Live: row_key 'Transfer Funds' (menu), column 'Accounts Overview' (title);… (+15 more)

### Community 63 - "Discovery decisions"
Cohesion: 0.08
Nodes (23): Base decisions, Cuts, Discovery decisions, Q10: window size and zoom — DECIDED, Q11: notebook format — DECIDED, Q12: dropdowns — DECIDED, Q13: scrolling — DECIDED, Q14: private data in saved pictures — DECIDED (+15 more)

### Community 64 - "2. Each box, with an example"
Cohesion: 0.12
Nodes (15): 1. Diagram, 2. Each box, with an example, 3. All tools, 4. Step by step: one discovery run, 5. Notes, Browser (Playwright), Control window and site lock (Q-A), Discovery architecture (+7 more)

### Community 65 - "Look"
Cohesion: 0.09
Nodes (44): append_rows(), clean_label(), column_header(), column_spans(), Element, element_at(), extract_table(), headings() (+36 more)

### Community 67 - "2. Components"
Cohesion: 0.12
Nodes (15): 1. Diagram, 2. Components, 3. Step types, 4. Worked example: ParaBank login + read balance, 5. Notes, Actor, Artifact (made by discovery, not replay), Browser setup (+7 more)

### Community 68 - "ControlWindow"
Cohesion: 0.17
Nodes (8): ControlWindow, Our own page: the only place a human answers. Closing it fails closed (None)., Answers the question on top. Closing the window (None) answers every one: fail…, Answers the newest open question of this mode, wherever it sits on the stack., A new question supersedes the one on screen (e.g. a gate during a take-over);…, One labelled input per field (label, masked), optionally prefilled. A dropdown…, A dropdown becomes a real <select> of its options; anything else a…, _row()

### Community 69 - "Pure-Visual Discovery Notebook: Build Plan"
Cohesion: 0.09
Nodes (22): 10. Open risks, 1. Global constraints (every task must follow these), 2. Review focus (inputs no spec line covers, but likely to bite), 3. What already exists (reuse, or its visual version), 3a. How the agent is built today (`agent.ipynb` STEP 4, `src/cua/agent.py`), 3b. Existing handoff rules: when a human is called in, 3c. Existing tools → the new tools, 4. New dependencies (checked on PyPI, 2026-09-28) (+14 more)

### Community 72 - "test_evidence.py"
Cohesion: 0.31
Nodes (13): _artifact(), _ns(), Path, save_evidence: one masked folder per run. No run value or secret is ever…, _save(), test_a_failed_run_still_writes_evidence(), test_an_artifact_holding_a_run_value_is_refused(), test_capability_yaml_and_crops_are_copied() (+5 more)

### Community 73 - "guard_send"
Cohesion: 0.14
Nodes (17): dropdown_options(), _flat(), guard_send(), hide_secrets(), _json(), list_options(), mismatches(), pretty() (+9 more)

### Community 74 - "test_observable.py"
Cohesion: 0.20
Nodes (13): dataclasses, _click(), Live: find_accounts_and_transactions.yaml saved `outputs: []`, no extract, and…, navigated: the page loaded (a link, even back to the same URL); new: new text…, After login the site is already on Accounts Overview; clicking it, scrolling,…, The page heading 'Accounts Overview' sits above the menu link with the same…, test_a_click_that_changes_the_screen_on_the_same_page_is_kept(), test_a_click_that_lands_on_the_page_it_left_is_dropped() (+5 more)

### Community 75 - "mk_look"
Cohesion: 0.23
Nodes (14): mk_look(), mk_look([(text, (x1, y1, x2, y2)), ...]) -> a Look with those OCR elements., _dup_target(), The 3 rungs + table cell; all miss -> None., test_a_single_text_match_is_rung1_as_before(), test_all_miss_is_none(), test_duplicate_text_picks_the_copy_nearest_the_anchor(), test_duplicate_text_with_no_copy_near_the_anchor_uses_rung2() (+6 more)

### Community 77 - "run_goal"
Cohesion: 0.11
Nodes (20): ext_call(), HandoffState, human_help(), mark_stuck(), note_call(), offer_control(), Every saved text, table cells included (evidence masking only)., New run on a fresh thread; pass an earlier thread_id to resume it with a next… (+12 more)

### Community 78 - "test_label_values.py"
Cohesion: 0.18
Nodes (17): re, parametrize, OCR joins a label to the dropdown beside it ('to account #16785') and reads its…, Live: steps 5-6 (agent, 'From account #[') and 7-8 (send, 'From account #')…, _select(), _sent(), test_a_box_border_read_as_a_bracket_is_not_part_of_the_label(), test_a_label_that_is_only_a_value_falls_back_to_the_next_nearest() (+9 more)

### Community 79 - "test_extract_types.py"
Cohesion: 0.29
Nodes (10): _cap(), _extract(), parametrize, Replay's own strict value types for extracts: an account number is never a…, test_an_account_number_cell_for_a_currency_output_stops(), test_an_integer_or_id_is_not_currency(), test_currency_needs_a_dollar_or_two_decimals(), test_the_next_rung_is_tried_once_on_a_type_mismatch() (+2 more)

### Community 80 - "test_no_values_stored.py"
Cohesion: 0.36
Nodes (5): Call, _arg_keys(), _log_calls(), Banking rule: no typed or human-given value is stored. Source-level checks on…, test_typed_and_selected_values_never_reach_the_log()

### Community 81 - "test_http_errors.py"
Cohesion: 0.18
Nodes (12): _judge(), Page, parametrize, Navigate joins paths like a browser; an HTTP error page is FAILED, never a…, Resp, test_a_200_page_with_not_found_text_is_still_a_business_outcome(), test_a_404_navigation_is_failed_not_a_business_outcome(), test_a_normal_page_passes() (+4 more)

### Community 82 - "test_adjacent_selects.py"
Cohesion: 0.33
Nodes (4): Transfer's second dropdown: the 'to account #' anchor must never land on 'From…, test_the_right_label_still_matches(), test_the_to_anchor_finds_the_to_label_not_the_from_label(), test_value_glued_to_hash_confirms_the_option()

### Community 87 - "test_partial_outputs.py"
Cohesion: 0.35
Nodes (12): _cap(), _click(), env(), _extract(), _finish(), fixture, Every status returns what was read. A read-only run whose checkpoint was picked…, test_a_failed_run_still_returns_what_it_read() (+4 more)

### Community 92 - "test_round_trip.py"
Cohesion: 0.39
Nodes (7): Path, Discovery's saved artifact runs in replay unchanged: build -> save -> load ->…, _saved(), test_crop_paths_resolve_to_saved_files(), test_rung2_offset_hits_the_point_discovery_acted_on(), test_saved_artifact_loads_as_is(), test_steps_dispatch_to_replay_handlers()

### Community 106 - "test_replay_evidence.py"
Cohesion: 0.27
Nodes (9): _all_text(), _png(), save_evidence writes one masked folder per run: summary, drift, failure (only…, _result(), test_all_files_are_written(), test_checkpoint_miss_carries_expected_and_observed(), test_failure_json_has_step_expected_observed(), test_no_failure_file_on_success() (+1 more)

### Community 107 - "test_table_replay.py"
Cohesion: 0.06
Nodes (43): _cap(), FakeForm, replay(path, inputs): given values by exact name (any case); unknown keys stop;…, test_all_inputs_given_means_no_form(), test_given_inputs_match_by_exact_name_any_case(), test_only_the_missing_inputs_go_to_the_one_form(), test_replay_stops_on_an_unknown_key_before_opening_the_site(), test_unknown_key_stops_naming_what_is_accepted() (+35 more)

### Community 108 - "ControlWindow"
Cohesion: 0.39
Nodes (3): ControlWindow, Our own page: the only place a human answers. Closing it fails closed (None)., _row()

### Community 109 - "HeldRoute"
Cohesion: 0.22
Nodes (4): test_the_gate_marks_a_human_approved_send(), HeldRoute, Route, test_sends_are_noted_only_during_a_take_over()

### Community 110 - "_meta"
Cohesion: 0.13
Nodes (31): pydantic, test_a_continued_table_is_one_step(), test_a_scroll_before_a_read_is_kept(), _ev(), _meta(), Path, Save artifact: the event log becomes a replay-ready capability (R12, R13, R16).…, Invented inputs are ignored, a missing description gets a default, secrets stay… (+23 more)

### Community 112 - "test_control_form.py"
Cohesion: 0.14
Nodes (9): base64, FakeWin, ControlWindow: form answers, and a newer question supersedes then restores the…, Regression: a gate during a take-over must win, then hand the take-over back…, test_closing_the_window_fails_every_question_closed(), test_dropdown_row_lists_every_option(), test_form_returns_answers_and_masks_sensitive(), test_gate_supersedes_takeover_then_restores_it() (+1 more)

### Community 113 - "Replay notebook plan"
Cohesion: 0.33
Nodes (5): Decisions made here (review), Open questions for the user, Replay notebook plan, Sections, Tasks

### Community 115 - "FakePage"
Cohesion: 0.25
Nodes (4): env(), FakeLock, FakePage, fixture

### Community 120 - "test_wandering.py"
Cohesion: 0.19
Nodes (17): _go(), _nav(), _open_path(), _paths(), parametrize, Live run 'Log in, bank phone number' (navigate_to_request_loan.yaml): a 404 and…, _shapes(), test_a_404_and_detour_navigations_are_dropped() (+9 more)

### Community 122 - ".get"
Cohesion: 0.11
Nodes (26): crops_for(), field_area(), goes_to_a_page(), is_select(), log_sent_dropdowns(), mark_submits(), needed_moves(), no_op() (+18 more)

### Community 127 - "Look"
Cohesion: 0.09
Nodes (32): anchor_point(), append_rows(), changed(), do_extract_table(), fill(), find_text(), locate(), Look (+24 more)

### Community 129 - "test_extract_pattern.py"
Cohesion: 0.29
Nodes (9): _cap(), _extract(), parametrize, An extract's optional `pattern` cuts the value out of a longer box;…, test_a_no_match_tries_the_next_rung_first(), test_a_pattern_extracts_the_phone_from_the_sentence(), test_an_old_artifact_without_a_pattern_is_unchanged(), test_new_types_accept_and_reject() (+1 more)

### Community 134 - "Site"
Cohesion: 0.14
Nodes (5): _load(), Lock, The site tab: a still screen unless `screen` changes; fires framenavigated.…, Site, Win

### Community 135 - "read_rows"
Cohesion: 0.22
Nodes (10): cell_shape(), col_of(), like_rows(), The column the box overlaps most, or None when it overlaps none (outside the…, A line's texts in the asked columns, left to right; two texts in one column are…, (rows under the header, whether the table may continue past the look's bottom).…, A table's end: a line that no longer looks like its rows (a footer, a menu, a…, date', 'amount', or 'text': enough to tell a row cell from a footer line in its… (+2 more)

### Community 139 - "do_type"
Cohesion: 0.18
Nodes (13): ask_option(), choose_option(), do_select(), do_type(), into_box(), Click the box, clear what is in it, type., Text inside the whole field: short values sit at its left edge, not near the…, The option is in the box's OCR, even merged with its label ('to account… (+5 more)

### Community 143 - "test_login_click_kept.py"
Cohesion: 0.31
Nodes (8): _click(), _names(), Live pay_bill.yaml (2026-09-30) lost its LOG IN click: without_detours saw LOG…, test_a_login_click_after_a_scroll_is_still_kept(), test_a_login_click_that_stays_on_the_page_is_not_a_no_op(), test_a_menu_detour_after_login_is_still_dropped(), test_a_pay_bill_log_keeps_login_bill_pay_fields_send_logout(), _type()

### Community 147 - "_fake_llm_keys"
Cohesion: 0.33
Nodes (5): _fake_llm_keys(), fixture, MonkeyPatch, Suite-wide: never let a real LLM key from `.env` reach a test (cua.config loads…, A fake Iliad key so code that builds a chat model works offline; no real key is…

### Community 149 - "pathlib"
Cohesion: 0.18
Nodes (12): pathlib, pytest, stmt, _ns(), parametrize, take_look's canvas: any window size or pixel density maps to one grid, and…, test_fits_canvas_and_maps_clicks_back_to_the_same_spot(), _keep() (+4 more)

### Community 151 - "_look_ns"
Cohesion: 0.33
Nodes (6): _look_ns(), Live bug: 'From account #' dropdown showing '74838' was saved as input…, Live bug: 'Sean' typed into Payee Name became the Address step's label and…, test_a_dropdowns_own_number_is_never_its_label(), test_a_typed_value_above_is_never_the_next_fields_label(), test_where_records_label_box_ordinal_offset_but_not_the_box_contents()

## Knowledge Gaps
- **135 isolated node(s):** `MODES`, `manifest_version`, `name`, `version`, `description` (+130 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **18 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `mk_look()` connect `mk_look` to `test_extract_pattern.py`, `test_checks.py`, `test_select_index.py`, `test_handback_button.py`, `test_replay_evidence.py`, `test_table_replay.py`, `test_extract_types.py`, `test_cleanup.py`, `test_http_errors.py`, `test_adjacent_selects.py`, `FakePage`, `pathlib`, `test_partial_outputs.py`, `test_engine.py`, `test_resolve_inputs.py`, `test_round_trip.py`?**
  _High betweenness centrality (0.034) - this node is a cross-community bridge._
- **Why does `ScriptedControl` connect `HangPage` to `test_takeover.py`?**
  _High betweenness centrality (0.020) - this node is a cross-community bridge._
- **Why does `site()` connect `test_table_replay.py` to `mk_look`, `.click`?**
  _High betweenness centrality (0.019) - this node is a cross-community bridge._
- **Are the 34 inferred relationships involving `mk_look()` (e.g. with `test_the_to_anchor_finds_the_to_label_not_the_from_label()` and `_click_env()`) actually correct?**
  _`mk_look()` has 34 INFERRED edges - model-reasoned connections that need verification._
- **Are the 27 inferred relationships involving `SimpleNamespace` (e.g. with `_ns()` and `test_fits_canvas_and_maps_clicks_back_to_the_same_spot()`) actually correct?**
  _`SimpleNamespace` has 27 INFERRED edges - model-reasoned connections that need verification._
- **What connects `MODES`, `manifest_version`, `name` to the rest of the system?**
  _135 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `asyncio` be split into smaller, more focused modules?**
  _Cohesion score 0.08974358974358974 - nodes in this community are weakly interconnected._