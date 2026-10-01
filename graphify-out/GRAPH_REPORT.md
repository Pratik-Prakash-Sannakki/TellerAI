# Graph Report - BankerAgent  (2026-10-01)

## Corpus Check
- 122 files · ~231,018 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 1470 nodes · 2979 edges · 92 communities (75 shown, 17 thin omitted)
- Extraction: 96% EXTRACTED · 4% INFERRED · 0% AMBIGUOUS · INFERRED: 128 edges (avg confidence: 0.72)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `1a3fe565`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- argparse
- Page
- ask_inputs
- test_extract_table.py
- Evidence README
- langchain_agents_middleware
- Win
- test_handback_button.py
- value_in_box
- sys
- like_rows
- save_discovery_evidence / save_replay_evidence (D92)
- Replay decisions
- Five Error Demos (D30)
- langchain_typesafe
- langchain_typesafe_experimental_middleware
- test_human_help.py
- test_models.py
- test_resolve_inputs.py
- .click
- test_transaction_gates.py
- test_handback.py
- discovery.py
- Capability
- HangPage
- test_checks.py
- Box
- CLAUDE.md (project instructions)
- click
- manifest.json
- Stop
- asyncio
- replay.py
- take_look
- rescue
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
- Route
- _meta
- test_control_form.py
- Replay notebook plan
- FakePage
- SiteLock
- test_spot_changed.py
- test_wandering.py
- .get
- test_send_settle.py
- inspect
- background.js
- Look
- test_extract_pattern.py
- Site
- read_rows
- HeldRoute
- do_type
- test_prompt_rules.py
- test_login_click_kept.py
- _fake_llm_keys
- pathlib
- test_latest_screenshot.py
- _look_ns
- SimpleNamespace
- FormRoute

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

## Communities (92 total, 17 thin omitted)

### Community 1 - "Page"
Cohesion: 0.22
Nodes (4): Page, Live crash: Register (a form POST) held by guard_send -> shot_after timed out…, Fires framenavigated like Playwright, for the main frame and for an iframe., test_a_screenshot_that_times_out_still_hands_back_cleanly()

### Community 2 - "ask_inputs"
Cohesion: 0.40
Nodes (5): ask_inputs(), Every `{{input}}` the steps use, in step order, once each., R8: ONE form before step 1 for every input the caller did not give. Nothing is…, step_inputs(), test_no_cleanup_when_stopped_before_step_1()

### Community 3 - "test_extract_table.py"
Cohesion: 0.16
Nodes (23): Handoff, _look(), _ns(), extract_table: the agent points at a header, code reads the rows from OCR (live…, Live run: the page footer ('Home | About Us I Services …', '© Parasoft …') sat…, _read(), _table_ev(), test_a_header_holding_a_run_value_is_refused() (+15 more)

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

### Community 18 - "test_human_help.py"
Cohesion: 0.14
Nodes (17): dataclasses, Control, Lock, _no_watch(), parametrize, human_help: one open-ended panel -> answer in words, take over, or stop., Run human_help's take-over; `during(page)` is what the human does before…, The human pressed Register (gate held, its question on top), then clicked Done… (+9 more)

### Community 20 - "test_models.py"
Cohesion: 0.07
Nodes (32): BaseChatModel, CaptureFixture, dotenv, ModelKind, os, host_allowed(), Shared configuration: the app this system points at, secret lookup, and the…, Look up a secret by NAME. Raises on an unknown name or an empty/missing value.… (+24 more)

### Community 21 - "test_resolve_inputs.py"
Cohesion: 0.12
Nodes (23): _ask(), _cap(), ClearPage, _click(), env(), FakeForm, FakePage, fixture (+15 more)

### Community 22 - ".click"
Cohesion: 0.29
Nodes (10): _cap(), _fail_clicks(), HumanControl, Live: the human finished the whole form during a take-over; step 6 then 'target…, Takes over; while 'in control', the human opens a page and sends a form., test_checkpoint_reached_by_the_human_skips_the_remaining_steps(), test_no_take_over_means_an_empty_list(), test_no_values_in_the_take_over_entry() (+2 more)

### Community 23 - "test_transaction_gates.py"
Cohesion: 0.11
Nodes (33): Control, _guard_ns(), _held_navigation(), HeldPage, _no_dropdowns(), _opts(), parametrize, guard_send: nothing that sends data leaves the tab without two human approvals. (+25 more)

### Community 26 - "test_handback.py"
Cohesion: 0.16
Nodes (12): take_over's hand-back: the extension's toolbar button (never the site), with no…, The user's rule: no "are you done?" prompts in between. Only the take-over…, test_a_click_on_the_toolbar_button_hands_back(), test_done_in_the_takeover_itself_cancels_the_watcher(), test_no_extension_still_hands_back_from_the_control_tab(), test_no_idle_reminder_ever_interrupts_the_take_over(), test_the_badge_reads_you_during_the_take_over_then_ai(), test_the_button_never_touches_the_site_page() (+4 more)

### Community 29 - "discovery.py"
Cohesion: 0.07
Nodes (50): BaseModel, deepagents, langchain_tools, langgraph_checkpoint_memory, model_validator, after_login_click(), Anchor, append_rows() (+42 more)

### Community 32 - "Capability"
Cohesion: 0.12
Nodes (28): Capability, find(), is_cleanup(), judge(), login_came_back(), login_steps(), norm(), Path (+20 more)

### Community 33 - "HangPage"
Cohesion: 0.16
Nodes (7): HangPage, HeldPage, NeverAnsweredGate, Like Playwright: while a form POST (a navigation) is held, `page.screenshot()`…, `evaluate` also never returns while a request is held, as live., The human clicks Done while their own send's Gate 1 is still open and never…, test_done_hands_back_within_a_timeout_as_stuck()

### Community 34 - "test_checks.py"
Cohesion: 0.13
Nodes (19): _click_env(), _form_png(), _Lock, _Page, parametrize, Step checks on fakes: whole-field read (A), tolerant word match (B), late page…, Live bug: the Transfer click sent (both gates approved) but its check said…, Live: Address '1' failed twice: OCR does not read a lone character. The field's… (+11 more)

### Community 35 - "Box"
Cohesion: 0.21
Nodes (10): Box, canvas(), crop_box(), field_box(), number(), Reading order (rows top to bottom, then left to right), fresh refs., The smallest drawn rectangle around the point (the input's own border), else…, Text inside the whole field: short values sit at its left edge, not near the… (+2 more)

### Community 36 - "CLAUDE.md (project instructions)"
Cohesion: 0.12
Nodes (19): CLAUDE.md (project instructions), D101: labeled_value refuses a table-header resolution (general fix), D102: label_header/value_header flags ported into agent.py + cli.py capture path, D92: Evidence Capture Helpers (save_discovery_evidence/save_replay_evidence), D93: Pre-existing 02_artifact_schema.py IndexError bug, D95: Missing create_deep_agent import found live in BROWSER 12, D96: build_agent() goal_text vs given_text field-name bug, D97: cua replay --login flag + repeated Balance header trap (+11 more)

### Community 38 - "click"
Cohesion: 0.08
Nodes (54): blocks(), checkpoint(), choose_option(), click(), cut_crop(), element_at(), extract_table(), extract_value() (+46 more)

### Community 39 - "manifest.json"
Cohesion: 0.11
Nodes (18): action, default_icon, default_title, background, service_worker, 128, 16, 32 (+10 more)

### Community 40 - "Stop"
Cohesion: 0.09
Nodes (25): Exception, ask_option(), do_navigate(), error_page(), finish(), given_inputs(), host_allowed(), load_capability() (+17 more)

### Community 41 - "asyncio"
Cohesion: 0.13
Nodes (20): asyncio, _look_ns(), Path, A dropdown's point inside an OCR box that merged its label and value ('to…, A box's own text with nothing cut from it (a value, a button) stays off the…, _select_ev(), test_a_plain_word_under_the_point_is_still_never_the_anchor(), test_a_point_inside_a_merged_label_and_value_box_anchors_on_the_cleaned_label() (+12 more)

### Community 42 - "replay.py"
Cohesion: 0.08
Nodes (41): functools, append_rows(), _clean(), Config, discovery_schema(), do_extract(), dropdown_options(), _flat() (+33 more)

### Community 43 - "take_look"
Cohesion: 0.16
Nodes (19): changed(), decode(), draw_numbered(), encode(), find_template(), _img(), mask_png(), ocr() (+11 more)

### Community 44 - "rescue"
Cohesion: 0.15
Nodes (14): Future, button_clicked(), ext_call(), hand_back(), handback_button(), Evidence screenshot. A held form POST blocks `page.screenshot()`: give up,…, R19: one bounded call into the hand-back extension's service worker, never the…, Returns once the toolbar button's click count rises above where it was at the… (+6 more)

### Community 48 - "take_look"
Cohesion: 0.08
Nodes (32): act(), Box, canvas(), crop_box(), decode(), draw_numbered(), encode(), _img() (+24 more)

### Community 50 - "test_choose_option.py"
Cohesion: 0.22
Nodes (11): _fns(), Page, Dropdowns (option B): read every option and select by value, for the <select>…, Mimics SELECT_AT_JS against one <select> at (100, 50); nothing else on the page., The user's bug: two accounts, only one showed., The red box showed the whole tool reply (URL, every OCR line) instead of the…, test_lists_every_option_values_only(), test_missing_option_is_refused() (+3 more)

### Community 53 - "test_takeover.py"
Cohesion: 0.22
Nodes (11): _click(), DoneWhileSending, HumanControlSimple, A take-over is recorded as evidence (shots, page paths, send paths, no values)…, take_look screenshots the page, as the real one does., The human clicks Done just as their form POST is held: the gate must still show…, _real_shots(), test_click_stashes_the_dropdowns_before_clicking() (+3 more)

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
Cohesion: 0.12
Nodes (29): clean_label(), column_header(), Element, headings(), is_word(), label_near(), Look, merged_label() (+21 more)

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
Cohesion: 0.10
Nodes (26): json, _artifact(), _ns(), Path, save_evidence: one masked folder per run. No run value or secret is ever…, _save(), test_a_failed_run_still_writes_evidence(), test_an_artifact_holding_a_run_value_is_refused() (+18 more)

### Community 73 - "guard_send"
Cohesion: 0.16
Nodes (16): dropdown_options(), _flat(), guard_send(), hide_secrets(), is_sensitive(), _json(), mismatches(), pretty() (+8 more)

### Community 74 - "test_observable.py"
Cohesion: 0.25
Nodes (10): _click(), Live: find_accounts_and_transactions.yaml saved `outputs: []`, no extract, and…, navigated: the page loaded (a link, even back to the same URL); new: new text…, After login the site is already on Accounts Overview; clicking it, scrolling,…, The page heading 'Accounts Overview' sits above the menu link with the same…, test_a_click_that_changes_the_screen_on_the_same_page_is_kept(), test_a_click_that_lands_on_the_page_it_left_is_dropped(), test_identical_consecutive_clicks_on_one_target_are_one() (+2 more)

### Community 75 - "mk_look"
Cohesion: 0.23
Nodes (14): mk_look(), mk_look([(text, (x1, y1, x2, y2)), ...]) -> a Look with those OCR elements., _dup_target(), The 3 rungs + table cell; all miss -> None., test_a_single_text_match_is_rung1_as_before(), test_all_miss_is_none(), test_duplicate_text_picks_the_copy_nearest_the_anchor(), test_duplicate_text_with_no_copy_near_the_anchor_uses_rung2() (+6 more)

### Community 77 - "run_goal"
Cohesion: 0.11
Nodes (19): ask_human(), ext_call(), HandoffState, human_help(), offer_control(), Every saved text, table cells included (evidence masking only)., Ask a human whenever you are unsure: what to do, which option, what the goal…, New run on a fresh thread; pass an earlier thread_id to resume it with a next… (+11 more)

### Community 78 - "test_label_values.py"
Cohesion: 0.21
Nodes (15): parametrize, OCR joins a label to the dropdown beside it ('to account #16785') and reads its…, Live: steps 5-6 (agent, 'From account #[') and 7-8 (send, 'From account #')…, _select(), _sent(), test_a_box_border_read_as_a_bracket_is_not_part_of_the_label(), test_a_label_that_is_only_a_value_falls_back_to_the_next_nearest(), test_a_number_that_only_resembles_a_value_is_not_a_leak() (+7 more)

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
Cohesion: 0.05
Nodes (55): _cap(), FakeForm, replay(path, inputs): given values by exact name (any case); unknown keys stop;…, test_all_inputs_given_means_no_form(), test_given_inputs_match_by_exact_name_any_case(), test_only_the_missing_inputs_go_to_the_one_form(), test_replay_stops_on_an_unknown_key_before_opening_the_site(), test_unknown_key_stops_naming_what_is_accepted() (+47 more)

### Community 108 - "ControlWindow"
Cohesion: 0.39
Nodes (3): ControlWindow, Our own page: the only place a human answers. Closing it fails closed (None)., _row()

### Community 109 - "Route"
Cohesion: 0.22
Nodes (4): test_the_gate_marks_a_human_approved_send(), Frame, Route, test_sends_are_noted_only_during_a_take_over()

### Community 110 - "_meta"
Cohesion: 0.13
Nodes (31): test_a_continued_table_is_one_step(), test_a_read_or_a_send_is_enough(), test_a_run_that_neither_reads_nor_sends_is_refused(), test_a_scroll_before_a_read_is_kept(), _ev(), _meta(), Path, Save artifact: the event log becomes a replay-ready capability (R12, R13, R16).… (+23 more)

### Community 112 - "test_control_form.py"
Cohesion: 0.14
Nodes (9): base64, FakeWin, ControlWindow: form answers, and a newer question supersedes then restores the…, Regression: a gate during a take-over must win, then hand the take-over back…, test_closing_the_window_fails_every_question_closed(), test_dropdown_row_lists_every_option(), test_form_returns_answers_and_masks_sensitive(), test_gate_supersedes_takeover_then_restores_it() (+1 more)

### Community 113 - "Replay notebook plan"
Cohesion: 0.33
Nodes (5): Decisions made here (review), Open questions for the user, Replay notebook plan, Sections, Tasks

### Community 115 - "FakePage"
Cohesion: 0.25
Nodes (4): env(), FakeLock, FakePage, fixture

### Community 118 - "test_spot_changed.py"
Cohesion: 0.47
Nodes (5): _load(), _look(), ndarray, spot_changed: password dots are pixels, not OCR text., test_dots_count_as_change_and_blank_does_not()

### Community 120 - "test_wandering.py"
Cohesion: 0.16
Nodes (19): re, _go(), _nav(), _open_path(), _paths(), parametrize, Live run 'Log in, bank phone number' (navigate_to_request_loan.yaml): a 404 and…, _shapes() (+11 more)

### Community 122 - ".get"
Cohesion: 0.11
Nodes (26): crops_for(), field_area(), goes_to_a_page(), is_select(), log_sent_dropdowns(), mark_submits(), needed_moves(), no_op() (+18 more)

### Community 123 - "test_send_settle.py"
Cohesion: 0.25
Nodes (7): _act(), _none(), Page, D: after an approved send, act waits for the page's response before its…, The response lands 3 polls after the gate is released., test_after_an_approved_send_the_look_shows_the_response(), test_no_send_means_no_extra_wait()

### Community 127 - "Look"
Cohesion: 0.09
Nodes (33): anchor_point(), col_of(), column_spans(), do_extract_table(), Element, element_at(), fill(), find_text() (+25 more)

### Community 129 - "test_extract_pattern.py"
Cohesion: 0.29
Nodes (9): _cap(), _extract(), parametrize, An extract's optional `pattern` cuts the value out of a longer box;…, test_a_no_match_tries_the_next_rung_first(), test_a_pattern_extracts_the_phone_from_the_sentence(), test_an_old_artifact_without_a_pattern_is_unchanged(), test_new_types_accept_and_reject() (+1 more)

### Community 134 - "Site"
Cohesion: 0.14
Nodes (6): Ext, _load(), Lock, The site tab: a still screen unless `screen` changes; fires framenavigated.…, The hand-back extension's service worker: a click counter and a badge. Never…, Site

### Community 135 - "read_rows"
Cohesion: 0.12
Nodes (17): cell_shape(), col_of(), column_spans(), like_rows(), Each header's x-range: out to the midpoint with its neighbours on the header…, (every header-line column as (asked name or None, lo, hi), the header line's…, The column the box overlaps most, or None when it overlaps none (outside the…, Texts grouped into lines, top to bottom. (+9 more)

### Community 136 - "HeldRoute"
Cohesion: 0.25
Nodes (3): GateControl, HeldRoute, test_navigation_send_never_screenshots_and_the_gate_shows()

### Community 139 - "do_type"
Cohesion: 0.13
Nodes (20): act(), choose_option(), do_click(), do_scroll(), do_select(), do_type(), into_box(), Step (+12 more)

### Community 143 - "test_login_click_kept.py"
Cohesion: 0.31
Nodes (8): _click(), _names(), Live pay_bill.yaml (2026-09-30) lost its LOG IN click: without_detours saw LOG…, test_a_login_click_after_a_scroll_is_still_kept(), test_a_login_click_that_stays_on_the_page_is_not_a_no_op(), test_a_menu_detour_after_login_is_still_dropped(), test_a_pay_bill_log_keeps_login_bill_pay_fields_send_logout(), _type()

### Community 147 - "_fake_llm_keys"
Cohesion: 0.33
Nodes (5): _fake_llm_keys(), fixture, MonkeyPatch, Suite-wide: never let a real LLM key from `.env` reach a test (cua.config loads…, A fake Iliad key so code that builds a chat model works offline; no real key is…

### Community 149 - "pathlib"
Cohesion: 0.22
Nodes (9): pathlib, pytest, stmt, take_look's canvas: any window size or pixel density maps to one grid, and…, _keep(), ns(), fixture, Load replay.py's definitions via ast (no browser, no OCR model), as… (+1 more)

### Community 150 - "test_latest_screenshot.py"
Cohesion: 0.47
Nodes (5): _cls(), LatestScreenshotOnly keeps only the newest image in the model's context., _shot(), test_only_last_image_survives(), ToolMessage

### Community 151 - "_look_ns"
Cohesion: 0.33
Nodes (6): _look_ns(), Live bug: 'From account #' dropdown showing '74838' was saved as input…, Live bug: 'Sean' typed into Payee Name became the Address step's label and…, test_a_dropdowns_own_number_is_never_its_label(), test_a_typed_value_above_is_never_the_next_fields_label(), test_where_records_label_box_ordinal_offset_but_not_the_box_contents()

### Community 152 - "SimpleNamespace"
Cohesion: 0.22
Nodes (9): SimpleNamespace, _ns(), parametrize, test_fits_canvas_and_maps_clicks_back_to_the_same_spot(), test_sent_values_count_as_run_values(), test_a_sent_dropdown_is_logged_with_its_index_on_the_page(), test_landed_keeps_only_new_fixed_text(), The user's screenshot: every field set to "1", amount 124677, one real dropdown… (+1 more)

### Community 153 - "FormRoute"
Cohesion: 0.25
Nodes (5): FormRoute, Answers each gate from a script; records what each form offered., ScriptedControl, test_agent_send_uses_the_stash_not_the_page(), test_human_post_during_a_take_over_passes_both_gates_with_no_evaluate()

## Knowledge Gaps
- **120 isolated node(s):** `MODES`, `manifest_version`, `name`, `version`, `description` (+115 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **17 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `mk_look()` connect `mk_look` to `test_extract_pattern.py`, `test_checks.py`, `test_handback_button.py`, `test_evidence.py`, `test_replay_evidence.py`, `test_table_replay.py`, `test_extract_types.py`, `test_http_errors.py`, `test_adjacent_selects.py`, `FakePage`, `pathlib`, `test_partial_outputs.py`, `test_engine.py`, `test_resolve_inputs.py`, `test_round_trip.py`?**
  _High betweenness centrality (0.025) - this node is a cross-community bridge._
- **Why does `Route` connect `test_transaction_gates.py` to `SimpleNamespace`?**
  _High betweenness centrality (0.019) - this node is a cross-community bridge._
- **Why does `Capability` connect `Capability` to `ask_inputs`, `Stop`, `replay.py`, `do_type`, `take_look`, `.get`, `discovery.py`, `Look`?**
  _High betweenness centrality (0.014) - this node is a cross-community bridge._
- **Are the 34 inferred relationships involving `mk_look()` (e.g. with `test_the_to_anchor_finds_the_to_label_not_the_from_label()` and `_click_env()`) actually correct?**
  _`mk_look()` has 34 INFERRED edges - model-reasoned connections that need verification._
- **Are the 27 inferred relationships involving `SimpleNamespace` (e.g. with `_ns()` and `test_fits_canvas_and_maps_clicks_back_to_the_same_spot()`) actually correct?**
  _`SimpleNamespace` has 27 INFERRED edges - model-reasoned connections that need verification._
- **What connects `MODES`, `manifest_version`, `name` to the rest of the system?**
  _120 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `test_handback_button.py` be split into smaller, more focused modules?**
  _Cohesion score 0.07781649245063879 - nodes in this community are weakly interconnected._