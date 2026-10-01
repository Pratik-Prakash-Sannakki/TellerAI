# Graph Report - BankerAgent  (2026-10-01)

## Corpus Check
- 207 files · ~278,589 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 2907 nodes · 7823 edges · 136 communities (118 shown, 18 thin omitted)
- Extraction: 95% EXTRACTED · 5% INFERRED · 0% AMBIGUOUS · INFERRED: 365 edges (avg confidence: 0.55)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `036b484a`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- argparse
- FakeRoute
- Productionize Plan: notebooks → `src/cua/` package
- test_act.py
- Evidence README
- langchain_agents_middleware
- vision/__init__.py
- test_replay_inputs.py
- test_input.py
- Look
- test_dropdown.py
- save_discovery_evidence / save_replay_evidence (D92)
- Replay decisions
- Five Error Demos (D30)
- langchain_typesafe
- langchain_typesafe_experimental_middleware
- discovery/run.py
- test_recorder_reads.py
- test_replay_engine.py
- test_replay_rescue.py
- test_llm.py
- test_replay_handback.py
- Ctx
- safety/__init__.py
- test_replay_wiring.py
- recorder/__init__.py
- steps.py
- request.py
- integration/conftest.py
- discovery.py
- test_replay_table.py
- redact.py
- Path
- _meta
- test_replay_extract.py
- Look
- CLAUDE.md (project instructions)
- test_replay_steps.py
- type_text
- manifest.json
- Capability
- test_recorder_runs.py
- replay.py
- nav.py
- handback_button
- human.py
- FakeTab
- DiscoveryConfig
- take_look
- test_send_guard.py
- test_control_window.py
- cua.vision
- test_takeover_loop.py
- ReplayConfig
- discovery/context.py
- HeldPage
- LatestScreenshotOnly
- read.py
- test_extension.py
- discovery/wiring.py
- ._held
- langgraph_types
- rescue.py
- Discovery decisions
- 2. Each box, with an example
- Look
- ControlWindow
- 2. Components
- ControlWindow
- Pure-Visual Discovery Notebook: Build Plan
- SiteLock
- SiteLock
- test_table.py
- guard_send
- config.py
- engine.py
- loader.py
- make_replay_ctx
- norm
- click
- look.py
- BrowserConfig
- FakePage
- copy
- crops.py
- test_build_tools.py
- cua
- replay/evidence.py
- cua.schema
- handoff/__init__.py
- is_sensitive
- save.py
- ScriptedControl
- test_human_tools.py
- test_screenshot.py
- take_look
- _checked
- result.py
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
- ControlWindow
- walk
- make_ctx
- pytest
- test_replay_evidence.py
- Replay notebook plan
- act.py
- test_saved_artifacts.py
- SiteLock
- test_dropdowns.py
- test_loader.py
- read_helpers.py
- test_shared_evidence.py
- test_locate.py
- .get
- masked_outputs
- FakeWin
- background.js
- locate
- test_result.py
- build_capability
- replay/context.py
- Box
- choose_option
- pathlib
- re
- .findable
- test_capability.py

## God Nodes (most connected - your core abstractions)
1. `BrowserConfig` - 78 edges
2. `Ctx` - 76 edges
3. `ReplayConfig` - 65 edges
4. `make_ctx()` - 63 edges
5. `make_replay_ctx()` - 60 edges
6. `Look` - 58 edges
7. `_meta()` - 53 edges
8. `Session` - 45 edges
9. `SiteProfile` - 44 edges
10. `Box` - 44 edges

## Surprising Connections (you probably didn't know these)
- `make_observe_tools()` --indirect_call--> `observe()`  [INFERRED]
  src/cua/discovery/tools/observe.py → notebooks/discovery/discovery.py
- `Driven` --indirect_call--> `observe()`  [INFERRED]
  tests/unit/discovery/tools/test_act.py → notebooks/discovery/discovery.py
- `_make_type_text()` --indirect_call--> `type_text()`  [INFERRED]
  src/cua/discovery/tools/act.py → notebooks/discovery/discovery.py
- `_make_type_secret()` --indirect_call--> `type_secret()`  [INFERRED]
  src/cua/discovery/tools/act.py → notebooks/discovery/discovery.py
- `_make_select_option()` --indirect_call--> `select_option()`  [INFERRED]
  src/cua/discovery/tools/act.py → notebooks/discovery/discovery.py

## Import Cycles
- 3-file cycle: `src/cua/discovery/tools/__init__.py -> src/cua/discovery/tools/nav.py -> src/cua/discovery/tools/guard.py -> src/cua/discovery/tools/__init__.py`
- 3-file cycle: `src/cua/discovery/tools/__init__.py -> src/cua/discovery/tools/nav.py -> src/cua/discovery/tools/observe.py -> src/cua/discovery/tools/__init__.py`
- 3-file cycle: `src/cua/discovery/tools/__init__.py -> src/cua/discovery/tools/human.py -> src/cua/discovery/tools/observe.py -> src/cua/discovery/tools/__init__.py`
- 3-file cycle: `src/cua/discovery/tools/__init__.py -> src/cua/discovery/tools/act.py -> src/cua/discovery/tools/guard.py -> src/cua/discovery/tools/__init__.py`
- 3-file cycle: `src/cua/discovery/tools/__init__.py -> src/cua/discovery/tools/act.py -> src/cua/discovery/tools/observe.py -> src/cua/discovery/tools/__init__.py`
- 3-file cycle: `src/cua/discovery/tools/__init__.py -> src/cua/discovery/tools/read.py -> src/cua/discovery/tools/guard.py -> src/cua/discovery/tools/__init__.py`
- 3-file cycle: `src/cua/discovery/tools/guard.py -> src/cua/discovery/tools/human.py -> src/cua/discovery/tools/observe.py -> src/cua/discovery/tools/guard.py`
- 4-file cycle: `src/cua/discovery/tools/__init__.py -> src/cua/discovery/tools/nav.py -> src/cua/discovery/tools/observe.py -> src/cua/discovery/tools/guard.py -> src/cua/discovery/tools/__init__.py`
- 4-file cycle: `src/cua/discovery/tools/__init__.py -> src/cua/discovery/tools/human.py -> src/cua/discovery/tools/observe.py -> src/cua/discovery/tools/guard.py -> src/cua/discovery/tools/__init__.py`
- 4-file cycle: `src/cua/discovery/tools/__init__.py -> src/cua/discovery/tools/act.py -> src/cua/discovery/tools/human.py -> src/cua/discovery/tools/observe.py -> src/cua/discovery/tools/__init__.py`
- 4-file cycle: `src/cua/discovery/tools/__init__.py -> src/cua/discovery/tools/act.py -> src/cua/discovery/tools/observe.py -> src/cua/discovery/tools/guard.py -> src/cua/discovery/tools/__init__.py`
- 5-file cycle: `src/cua/discovery/tools/__init__.py -> src/cua/discovery/tools/nav.py -> src/cua/discovery/tools/guard.py -> src/cua/discovery/tools/human.py -> src/cua/discovery/tools/observe.py -> src/cua/discovery/tools/__init__.py`
- 5-file cycle: `src/cua/discovery/tools/__init__.py -> src/cua/discovery/tools/act.py -> src/cua/discovery/tools/guard.py -> src/cua/discovery/tools/human.py -> src/cua/discovery/tools/observe.py -> src/cua/discovery/tools/__init__.py`
- 5-file cycle: `src/cua/discovery/tools/__init__.py -> src/cua/discovery/tools/act.py -> src/cua/discovery/tools/human.py -> src/cua/discovery/tools/observe.py -> src/cua/discovery/tools/guard.py -> src/cua/discovery/tools/__init__.py`
- 5-file cycle: `src/cua/discovery/tools/__init__.py -> src/cua/discovery/tools/read.py -> src/cua/discovery/tools/guard.py -> src/cua/discovery/tools/human.py -> src/cua/discovery/tools/observe.py -> src/cua/discovery/tools/__init__.py`

## Communities (136 total, 18 thin omitted)

### Community 1 - "FakeRoute"
Cohesion: 0.10
Nodes (11): FakeControl, FakePage, FakeRoute, A fake discovery/replay ``CONTROL`` surface (what ``ControlWindow`` presents).…, A fake ``playwright.async_api.Route``: records every…, A fake ``playwright.async_api.Page``. Every awaited method is recorded in…, asyncio, Tests for the shared offline fakes in tests/fakes.py (TDD: written before the… (+3 more)

### Community 2 - "Productionize Plan: notebooks → `src/cua/` package"
Cohesion: 0.12
Nodes (16): 10. Line-count offenders (today), 1. Package tree, 2. De-duplication (checked by AST diff of both notebooks), 3. State: globals → explicit objects, 4. Async and typing, 5. Notebooks after the move, 6. Tests, 7. ML-engineering practices (kept small) (+8 more)

### Community 3 - "test_act.py"
Cohesion: 0.06
Nodes (78): Items, (value, pattern) for an extract: the whole box when it is exactly the type,…, value_in_box(), make_look(), Look, A look whose elements are numbered 1.. in order (ref, text, box)., Driven, _head() (+70 more)

### Community 6 - "vision/__init__.py"
Cohesion: 0.15
Nodes (24): Pixels -> text: screenshots, OCR, canvas math, crops, and the shared table…, append_rows(), cell_shape(), col_of(), column_spans(), like_rows(), Box, Element (+16 more)

### Community 7 - "test_replay_inputs.py"
Cohesion: 0.13
Nodes (30): select(), type_(), _cap(), ClearPage, env(), FakeForm, FakePage, asyncio (+22 more)

### Community 8 - "test_input.py"
Cohesion: 0.09
Nodes (28): act(), into_box(), Lock, Look, Page, Step, The response to a send lands after the human's approval, not after the click:…, Unlock the site tab, run our own input steps, relock, settle, take a new look. (+20 more)

### Community 9 - "Look"
Cohesion: 0.06
Nodes (45): RapidOCR, Box, Element, Look, draw_numbered(), number(), ocr(), ocr_engine() (+37 more)

### Community 10 - "test_dropdown.py"
Cohesion: 0.07
Nodes (37): BaseException, Confirm, LookFn, choose_option_at_index(), choose_option_at_point(), list_options(), Page, Every option of the dropdown at this page point ([] if it is not a dropdown).… (+29 more)

### Community 12 - "Replay decisions"
Cohesion: 0.08
Nodes (23): R10: where the compile step lives — DECIDED, R11: why compile, if `response_format` exists? — PROPOSED, R12: what each step type compiles to — PROPOSED, R13: target schema — PROPOSED, R14: what rung 2 needs that discovery doesn't record — DONE, R15: auto-approve at replay — PROPOSED, R16: dead ends and retries at compile — PROPOSED, R17: replay result statuses — PROPOSED (+15 more)

### Community 16 - "discovery/run.py"
Cohesion: 0.09
Nodes (24): Saved, The current run (the one the send guard serves)., flag_leaks(), input_name(), Mark (never store) an event whose label, anchor, own text, hint or input name…, DiscoveryRun, DiscoveryRun: one discovery run's working state (was the notebook's…, What the human gave: the goal and every answer (the send guard's mismatch text). (+16 more)

### Community 17 - "test_recorder_reads.py"
Cohesion: 0.10
Nodes (31): asyncio, parametrize, Path, What the tools log, compiled: read-only runs, tables, labels joined to values,…, An event with no page_texts (an older log) proves nothing: the proof is kept., A box's own text with nothing cut from it (a value, a button) stays off the…, Live: steps 5-6 (agent, 'From account #[') and 7-8 (send, 'From account #')…, _read_log() (+23 more)

### Community 18 - "test_replay_engine.py"
Cohesion: 0.18
Nodes (45): cap(), click(), extract(), Capability, _finish(), _login_cap(), _no_snap(), _pcap() (+37 more)

### Community 19 - "test_replay_rescue.py"
Cohesion: 0.17
Nodes (29): The guard keeps its own reference to the control window: swap both., set_control(), _env(), _fail_clicks(), HangPage, HumanControl, asyncio, MonkeyPatch (+21 more)

### Community 20 - "test_llm.py"
Cohesion: 0.08
Nodes (28): CaptureFixture, ModelKind, os, cua: shared config and the LLM model factory (Iliad gateway) for the pure-…, make_chat_model(), model_name_for(), _note_fallback(), _pass_through_ca_bundle() (+20 more)

### Community 21 - "test_replay_handback.py"
Cohesion: 0.19
Nodes (18): _bctx(), Ext, Human, PanelDone, asyncio, Ctx, parametrize, The toolbar hand-back button during a rescue (its service worker, never the… (+10 more)

### Community 22 - "Ctx"
Cohesion: 0.17
Nodes (5): Ctx, Page, GateControl, HumanSimple, Req

### Community 23 - "safety/__init__.py"
Cohesion: 0.12
Nodes (13): Safety: what may leave the tab (hosts, the two send gates) and keeping values…, Protocol, The fields of a ``playwright.async_api.Request`` the guard reads., Request, ControlLike, GuardOptions, LookLike, Protocol (+5 more)

### Community 24 - "test_replay_wiring.py"
Cohesion: 0.12
Nodes (12): asyncio, MonkeyPatch, Path, attach (the replay setup cell), the guard's replay hooks, and R7: after…, Route, _session(), Tab, test_after_replay_the_run_holds_no_values_given_text_or_look() (+4 more)

### Community 25 - "recorder/__init__.py"
Cohesion: 0.13
Nodes (31): checkpoint(), The capability's checkpoint: the text replay must see to call the run a…, C: after a send, the page's own response proves success (the agent's proof only…, field_area(), goes_to_a_page(), is_select(), mark_submits(), needed_moves() (+23 more)

### Community 26 - "steps.py"
Cohesion: 0.10
Nodes (50): Point, changed(), choose_option(), do_click(), do_extract(), do_extract_table(), do_navigate(), do_scroll() (+42 more)

### Community 27 - "request.py"
Cohesion: 0.14
Nodes (22): functools, json, JsonObj, _flat(), _json(), pretty(), What a held request sends, and the same request rebuilt with edited values.…, Every value a request sends, from its query, a form body, or a JSON body… (+14 more)

### Community 29 - "discovery.py"
Cohesion: 0.07
Nodes (53): deepagents, langchain_tools, langgraph_checkpoint_memory, Anchor, append_rows(), build_capability(), Capability, CapabilityMeta (+45 more)

### Community 30 - "test_replay_table.py"
Cohesion: 0.19
Nodes (18): _cap(), _defs(), Page, asyncio, Capability, Ctx, MonkeyPatch, Path (+10 more)

### Community 31 - "redact.py"
Cohesion: 0.10
Nodes (32): Pattern, mask_png(), _num(), OcrFn, Value masking: ``norm``, ``is_sensitive``, ``hide_secrets``, ``redactor``,…, text -> text with every value masked. Numbers match however they are written…, Black out every OCR box whose text holds a run value. A clean image is written…, redactor() (+24 more)

### Community 32 - "Path"
Cohesion: 0.09
Nodes (27): ask_inputs(), _clean(), find(), finish(), given_inputs(), load_outcomes(), masked_outputs(), _png() (+19 more)

### Community 33 - "_meta"
Cohesion: 0.12
Nodes (33): _ev(), _meta(), Path, The recorder: the event log becomes a replay-ready capability (R12, R13, R16).…, Invented inputs are ignored, a missing description gets a default, secrets stay…, User decision 6: artifacts/<name>.yaml + artifacts/crops/<name>/ (was…, Banking safety (user, 2026-09-29): replay ends logged out., test_a_number_that_only_resembles_a_value_is_not_a_leak() (+25 more)

### Community 34 - "test_replay_extract.py"
Cohesion: 0.20
Nodes (20): _extract(), _notebook_assign(), _pcap(), asyncio, Capability, Ctx, parametrize, Extract steps on fakes: strict value types and an optional `pattern`. Ported… (+12 more)

### Community 35 - "Look"
Cohesion: 0.10
Nodes (28): Box, canvas(), col_of(), column_spans(), crop_box(), Element, element_at(), field_box() (+20 more)

### Community 36 - "CLAUDE.md (project instructions)"
Cohesion: 0.12
Nodes (19): CLAUDE.md (project instructions), D101: labeled_value refuses a table-header resolution (general fix), D102: label_header/value_header flags ported into agent.py + cli.py capture path, D92: Evidence Capture Helpers (save_discovery_evidence/save_replay_evidence), D93: Pre-existing 02_artifact_schema.py IndexError bug, D95: Missing create_deep_agent import found live in BROWSER 12, D96: build_agent() goal_text vs given_text field-name bug, D97: cua replay --login flag + repeated Balance header trap (+11 more)

### Community 37 - "test_replay_steps.py"
Cohesion: 0.08
Nodes (37): navigate(), _click_env(), GotoPage, _judge(), Page, asyncio, Ctx, Look (+29 more)

### Community 38 - "type_text"
Cohesion: 0.08
Nodes (38): canvas(), choose_option(), crop_box(), cut_crop(), element_at(), human_fills(), into_box(), is_sensitive() (+30 more)

### Community 39 - "manifest.json"
Cohesion: 0.11
Nodes (18): action, default_icon, default_title, background, service_worker, 128, 16, 32 (+10 more)

### Community 40 - "Capability"
Cohesion: 0.10
Nodes (37): act(), ask_option(), do_click(), do_extract(), do_navigate(), do_scroll(), do_select(), do_type() (+29 more)

### Community 41 - "test_recorder_runs.py"
Cohesion: 0.12
Nodes (27): _click(), _clicks(), _go(), _names(), _nav(), _noop_click(), _paths(), Recorder behaviour pinned by live runs: detours, 404s, login clicks kept, no-op… (+19 more)

### Community 42 - "replay.py"
Cohesion: 0.07
Nodes (42): dotenv, cell_shape(), Config, discovery_schema(), dropdown_options(), _flat(), guard_send(), hand_back() (+34 more)

### Community 43 - "nav.py"
Cohesion: 0.14
Nodes (27): act(), canvas(), look(), Unlock the site tab, run our own input steps, relock, settle, take a new look., The only screenshot path; stores the look on the run., The size of the image the model is looking at right now., to_page(), _press() (+19 more)

### Community 44 - "handback_button"
Cohesion: 0.40
Nodes (6): button_clicked(), ext_call(), handback_button(), R19: one bounded call into the hand-back extension's service worker, never the…, Returns once the toolbar button's click count rises above where it was at the…, Badge YOU while the human is in control; yields the task a toolbar click…

### Community 45 - "human.py"
Cohesion: 0.16
Nodes (23): Field, into_box(), list_options(), Step, Click the box, clear what is in it, type. Retries replace instead of doubling…, Every option of the dropdown at this point ([] if it is not a dropdown)., _enter(), human_fills() (+15 more)

### Community 46 - "FakeTab"
Cohesion: 0.12
Nodes (3): FakeTab, SimpleNamespace, A fake site or control tab with the Playwright calls discovery's wiring and…

### Community 47 - "DiscoveryConfig"
Cohesion: 0.19
Nodes (26): DiscoveryConfig, Discovery-only settings., Discovery: an LLM agent learns a task once and the recorder saves it as a…, attach(), new_run(), A fresh run for this goal (run_goal's ``HANDOFF = HandoffState(goal=goal)``)., Route every request through a new send guard, open the control window. Re-run…, make_session() (+18 more)

### Community 48 - "take_look"
Cohesion: 0.11
Nodes (26): act(), blocks(), decode(), draw_numbered(), encode(), _img(), mask_png(), observe() (+18 more)

### Community 49 - "test_send_guard.py"
Cohesion: 0.13
Nodes (25): ``await guard(route)`` is the route handler. ``guard.lock`` is the send gate:…, Side-specific steps, each at the exact point its notebook ran it. on_request:…, SendGuard, SendHooks, Control, _new(), _no_dropdowns(), _old() (+17 more)

### Community 50 - "test_control_window.py"
Cohesion: 0.26
Nodes (23): Factory, SIDES, asyncio, ControlWindow, parametrize, ControlWindow: one class, both sides' behaviour. Ported from…, Discovery calls _front inside try (the question is removed on failure); replay…, Regression: a gate during a take-over must win, then hand the take-over back… (+15 more)

### Community 51 - "cua.vision"
Cohesion: 0.50
Nodes (3): cua.vision, Read order, What may NOT go here

### Community 52 - "test_takeover_loop.py"
Cohesion: 0.13
Nodes (25): replay_control(), Asker, hand_back(), Future, Protocol, The shared take-over loop pieces. Each side's own take-over stays with that…, Done on the toolbar button or in the take-over panel hands back. No reminders…, takeover_text() (+17 more)

### Community 53 - "ReplayConfig"
Cohesion: 0.10
Nodes (39): Anchor, OcrText, SameTextLike, Replay-only settings., ReplayConfig, Replay: runs a capability saved by discovery with plain code, no LLM (step 4:…, fill(), Put inputs into `{{name}}`. `{{secret:x}}` stays as it is: secrets go in only… (+31 more)

### Community 54 - "discovery/context.py"
Cohesion: 0.08
Nodes (38): BrowserContext, Playwright, playwright_async_api, Dropdown, The page's dropdowns, read BEFORE an action (never while guard_send holds a…, read_dropdowns(), Playwright, no decisions: the open session, the site lock, our own input,…, Our own input into the locked site tab: ``act`` (unlock, run steps, relock,… (+30 more)

### Community 55 - "HeldPage"
Cohesion: 0.11
Nodes (9): DoneWhileSending, FormRoute, HeldPage, HeldRoute, NeverAnsweredGate, Ctx, Like Playwright: while a form POST (a navigation) is held, `page.screenshot()`…, The human clicks Done just as their form POST is held: the gate must still show… (+1 more)

### Community 56 - "LatestScreenshotOnly"
Cohesion: 0.24
Nodes (5): AgentMiddleware, LatestScreenshotOnly, NoopAnthropicPromptCachingMiddleware, Disable prompt caching on the Iliad gateway; it rejects Anthropic cache markers., Old screenshots are stale (their numbers no longer work); send the model only…

### Community 57 - "read.py"
Cohesion: 0.17
Nodes (22): Cols, crop(), Element, Crop around the target, every other text blanked (sized to the current canvas)., _columns(), is_header(), _log_table(), _make_extract_table() (+14 more)

### Community 58 - "test_extension.py"
Cohesion: 0.19
Nodes (14): Control, Ext, asyncio, parametrize, The hand-back extension's toolbar button: its service worker only, never the…, The extension's service worker: a click counter and a badge., test_a_click_count_rise_returns(), test_a_missing_or_broken_extension_gives_none() (+6 more)

### Community 59 - "discovery/wiring.py"
Cohesion: 0.23
Nodes (11): log_sent_dropdowns(), Ctx, Look, A dropdown whose value this send carries is a step, even one left on its…, build_ctx(), _count_nav(), _hooks(), Ctx (+3 more)

### Community 60 - "._held"
Cohesion: 0.21
Nodes (3): Request, Gate 1: Approve, or Edit = back to the form with every value, then again.…, RouteLike

### Community 62 - "rescue.py"
Cohesion: 0.14
Nodes (16): pydantic, Lock, A send the human started is still held: its gate is on screen next; wait for…, wait_held_send(), Frame, Ctx, JsonValue, Protocol (+8 more)

### Community 63 - "Discovery decisions"
Cohesion: 0.08
Nodes (23): Base decisions, Cuts, Discovery decisions, Q10: window size and zoom — DECIDED, Q11: notebook format — DECIDED, Q12: dropdowns — DECIDED, Q13: scrolling — DECIDED, Q14: private data in saved pictures — DECIDED (+15 more)

### Community 64 - "2. Each box, with an example"
Cohesion: 0.12
Nodes (15): 1. Diagram, 2. Each box, with an example, 3. All tools, 4. Step by step: one discovery run, 5. Notes, Browser (Playwright), Control window and site lock (Q-A), Discovery architecture (+7 more)

### Community 65 - "Look"
Cohesion: 0.10
Nodes (40): clean_label(), column_header(), column_spans(), Element, extract_table(), extract_value(), headings(), is_word() (+32 more)

### Community 66 - "ControlWindow"
Cohesion: 0.11
Nodes (18): Question, ControlWindow, discovery_control(), _img(), Protocol, ControlWindow: our own "Agent control" tab, the only place a human answers.…, Answers the question on top. Closing the window (None) answers every one: fail…, Answers the newest open question of this mode, wherever it sits on the stack. (+10 more)

### Community 67 - "2. Components"
Cohesion: 0.12
Nodes (15): 1. Diagram, 2. Components, 3. Step types, 4. Worked example: ParaBank login + read balance, 5. Notes, Actor, Artifact (made by discovery, not replay), Browser setup (+7 more)

### Community 68 - "ControlWindow"
Cohesion: 0.17
Nodes (8): ControlWindow, Our own page: the only place a human answers. Closing it fails closed (None)., Answers the question on top. Closing the window (None) answers every one: fail…, Answers the newest open question of this mode, wherever it sits on the stack., A new question supersedes the one on screen (e.g. a gate during a take-over);…, One labelled input per field (label, masked), optionally prefilled. A dropdown…, A dropdown becomes a real <select> of its options; anything else a…, _row()

### Community 69 - "Pure-Visual Discovery Notebook: Build Plan"
Cohesion: 0.09
Nodes (22): 10. Open risks, 1. Global constraints (every task must follow these), 2. Review focus (inputs no spec line covers, but likely to bite), 3. What already exists (reuse, or its visual version), 3a. How the agent is built today (`agent.ipynb` STEP 4, `src/cua/agent.py`), 3b. Existing handoff rules: when a human is called in, 3c. Existing tools → the new tools, 4. New dependencies (checked on PyPI, 2026-09-28) (+14 more)

### Community 71 - "SiteLock"
Cohesion: 0.17
Nodes (11): CdpSender, Protocol, The one method of a Playwright ``CDPSession`` the lock uses., The site tab ignores all real input (CDP). Lifted only around our own action or…, SiteLock, FakeCdp, asyncio, SiteLock: the site tab ignores real input except inside ``open()``, which… (+3 more)

### Community 72 - "test_table.py"
Cohesion: 0.07
Nodes (40): AST, _artifact(), _ns(), Path, save_evidence: one masked folder per run. No run value or secret is ever…, _save(), test_a_failed_run_still_writes_evidence(), test_an_artifact_holding_a_run_value_is_refused() (+32 more)

### Community 73 - "guard_send"
Cohesion: 0.19
Nodes (13): dropdown_options(), _flat(), guard_send(), hide_secrets(), _json(), pretty(), For each key: the options of the page dropdown whose CURRENT value is exactly…, Every value a request sends, from its query, a form body, or a JSON body… (+5 more)

### Community 74 - "config.py"
Cohesion: 0.08
Nodes (35): _find_root(), load_site(), OutcomeRule, _outcomes(), Path, Shared configuration: the site profile, browser/discovery/replay settings, and…, The nearest folder at or above `start` that has a ``configs/`` folder., Read and validate ``configs/<name>.yaml`` (root defaults to the repo root). (+27 more)

### Community 75 - "engine.py"
Cohesion: 0.12
Nodes (43): Drift, _cleanup_step(), error_page(), finish(), is_cleanup(), judge(), login_came_back(), login_steps() (+35 more)

### Community 76 - "loader.py"
Cohesion: 0.14
Nodes (23): ask_inputs(), ask_option(), _ask_rows(), given_inputs(), load_capability(), load_outcomes(), _missing_crops(), Capability (+15 more)

### Community 77 - "make_replay_ctx"
Cohesion: 0.15
Nodes (21): FakeLock, make_replay_ctx(), mk_look(), Ctx, Look, Replay test helpers: ``make_replay_ctx`` (a real Ctx on fakes), ``mk_look``,…, SiteLock stand-in: open() unlocks for the block., A real Ctx (real SendGuard, real ReplayRun) over a fake page/control/lock.… (+13 more)

### Community 78 - "norm"
Cohesion: 0.17
Nodes (18): choose_option(), _count_start(), Look, Select the first option containing this text in the dropdown at (or next to)…, The start event's look bookkeeping: the page a run begins on, and how often…, Every value typed, entered, given or sent this run, plus the secrets (in memory…, run_values(), landed() (+10 more)

### Community 79 - "click"
Cohesion: 0.07
Nodes (36): after_login_click(), ask_human(), click(), ext_call(), finish_business_outcome(), gate_click(), HandoffState, host_allowed() (+28 more)

### Community 80 - "look.py"
Cohesion: 0.08
Nodes (36): An evidence screenshot: short timeout, None on failure (never hangs on a held…, snap(), canvas_size(), Look, NDArray, uint8, Canvas-pixel <-> page-point mapping: any window size or pixel density maps to…, Fit the screenshot inside the canvas. Returns it and canvas-pixel -> page-point… (+28 more)

### Community 81 - "BrowserConfig"
Cohesion: 0.11
Nodes (24): BrowserConfig, Settings shared by discovery and replay (the same page size at both, Q10)., fixture, MonkeyPatch, Path, Discovery's saved artifact runs in replay unchanged: build -> save -> load ->…, saved(), test_crop_paths_resolve_to_saved_files() (+16 more)

### Community 82 - "FakePage"
Cohesion: 0.17
Nodes (5): FakePage, The site page: any call made on it for the button is a bug., SitePage, FakePage, Frame

### Community 84 - "crops.py"
Cohesion: 0.12
Nodes (25): crop_box(), cut_crop(), Box, Element, Look, Crops around one point: find the element there, crop around it, read text near…, Crop around the target, with every other piece of text blanked out., Pixels around the point changed. Catches password dots that OCR cannot read. (+17 more)

### Community 85 - "test_build_tools.py"
Cohesion: 0.18
Nodes (15): AsyncFunctionDef, inspect, build_tools(), BaseTool, Ctx, observe, click, type_text, type_secret, select_option, scroll, open_path,…, _notebook_tools(), _params() (+7 more)

### Community 86 - "cua"
Cohesion: 0.50
Nodes (3): cua, Read order, Rules

### Community 87 - "replay/evidence.py"
Cohesion: 0.22
Nodes (15): _clean(), _png(), OcrFn, Redact, _drift_lines(), Ctx, OcrFn, Path (+7 more)

### Community 88 - "cua.schema"
Cohesion: 0.50
Nodes (3): cua.schema, Read order, What may NOT go here

### Community 89 - "handoff/__init__.py"
Cohesion: 0.17
Nodes (18): _in_control(), The take-over itself: badge YOU, unlock the site, wait for Done (panel or…, _takeover_note(), Answerable, button_clicked(), ext_call(), Extension, handback_button() (+10 more)

### Community 90 - "is_sensitive"
Cohesion: 0.18
Nodes (16): dropdown_options(), mismatches(), _norm_num(), Dropdown, Values a send carries that the human never gave, and the dropdown choices to…, Numbers being sent that the human never gave, e.g. account 1450 vs 1400. Only…, For each key: the options of the page dropdown whose CURRENT value is exactly…, is_sensitive() (+8 more)

### Community 91 - "save.py"
Cohesion: 0.16
Nodes (13): Step, The {{input}} names the steps use, in order. {{secret:x}} is not an input., step_inputs(), used_inputs(), crops_for(), describe(), BaseChatModel, Capability (+5 more)

### Community 93 - "test_human_tools.py"
Cohesion: 0.35
Nodes (13): _ctx(), asyncio, Ctx, MonkeyPatch, finish_business_outcome / request_missing_values / ask_human (the human-facing…, test_ask_human_asks_with_the_question(), test_finish_needs_the_proof_on_the_screen(), test_no_fields_given() (+5 more)

### Community 94 - "test_screenshot.py"
Cohesion: 0.27
Nodes (9): _png(), asyncio, MonkeyPatch, take_look: page calls on the loop, the CPU part (OCR, drawing, encoding) in one…, ShotPage, test_page_width_reads_the_window_width(), test_snap_look_gives_the_look_png_or_none_on_timeout(), test_snap_png_passes_the_timeout_and_gives_none_on_error() (+1 more)

### Community 95 - "take_look"
Cohesion: 0.15
Nodes (19): changed(), decode(), draw_numbered(), encode(), find_template(), mask_png(), ocr(), page_width() (+11 more)

### Community 96 - "_checked"
Cohesion: 0.20
Nodes (10): _checked(), Result, What one_at_a_time does with a tool's result (the notebook's wrapper body after…, offer_control(), Only the reason: the first line of the tool result, without its prefix or…, entry(), fixture, MonkeyPatch (+2 more)

### Community 97 - "result.py"
Cohesion: 0.40
Nodes (4): What a replay run returns: its Status, the Stop that ends a run early, and…, R17 run statuses. A member is a plain str, so ``Status.SUCCESS == "SUCCESS"``., Status, StrEnum

### Community 98 - "test_human.py"
Cohesion: 0.17
Nodes (36): human_help(), Q21, open-ended: the human answers in words, takes over the site, or stops the…, Q21: the one time the site unlocks for a human. What they did is kept as…, take_over(), _answer(), _badge(), _ctx(), _dirty() (+28 more)

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
Cohesion: 0.25
Nodes (24): _navigate(), Event log -> ``Capability``: steps, inputs, outputs and secrets come from the…, ``to_step``'s open_path branch, unchanged., target(), to_step(), Capability, CapabilityMeta, Click (+16 more)

### Community 107 - "_FakeModel"
Cohesion: 0.20
Nodes (6): _FakeModel, asyncio, CapabilityMeta, Stands in for a LangChain chat model: no network, records the prompt., _Structured, test_describe_asks_the_given_model_with_labels_and_input_names_only()

### Community 108 - "ControlWindow"
Cohesion: 0.33
Nodes (4): ControlWindow, _img(), Our own page: the only place a human answers. Closing it fails closed (None)., _row()

### Community 109 - "walk"
Cohesion: 0.25
Nodes (9): is_cleanup(), Step i ended in a take-over, and the human went on to the final screen: the…, The main steps (every step not marked cleanup), then the checkpoint and the…, R17: a read-only run whose last main step read the last output, and every…, R5: bounded OCR poll until the text is on screen., read_only_done(), shows(), took_over_to_checkpoint() (+1 more)

### Community 110 - "make_ctx"
Cohesion: 0.16
Nodes (28): make_ctx(), Ctx, A discovery ``Ctx`` over fakes, built like ``attach`` but with no page wiring., helped(), asyncio, fixture, MonkeyPatch, Tool guards: the event log, the step budget, repeats, login tries, click gates,… (+20 more)

### Community 111 - "pytest"
Cohesion: 0.29
Nodes (6): pytest, _fake_llm_keys(), fixture, MonkeyPatch, Suite-wide: never let a real LLM key from `.env` reach a test (cua.config loads…, A fake Iliad key so code that builds a chat model works offline; no real key is…

### Community 112 - "test_replay_evidence.py"
Cohesion: 0.23
Nodes (21): Path, write_cap(), _all_text(), fake_ocr(), _png(), Box, Ctx, fixture (+13 more)

### Community 113 - "Replay notebook plan"
Cohesion: 0.33
Nodes (5): Decisions made here (review), Open questions for the user, Replay notebook plan, Sections, Tasks

### Community 114 - "act.py"
Cohesion: 0.13
Nodes (34): base64, P, make_act_tools(), _make_click(), _make_select_option(), _make_type_secret(), _make_type_text(), BaseTool (+26 more)

### Community 115 - "test_saved_artifacts.py"
Cohesion: 0.33
Nodes (4): parametrize, Path, Every capability discovery saved loads, and re-saves through save_artifact…, test_a_saved_artifact_round_trips()

### Community 117 - "test_dropdowns.py"
Cohesion: 0.15
Nodes (20): _approve(), HeldPage, _logged(), _no_crop_pixels(), asyncio, Ctx, fixture, MonkeyPatch (+12 more)

### Community 118 - "test_loader.py"
Cohesion: 0.16
Nodes (19): _cap_with_inputs(), Capability, fixture, MonkeyPatch, parametrize, Path, cua.replay.loader: loading a saved capability and the inputs it needs. Ported…, test_every_saved_artifact_loads_with_fake_secrets() (+11 more)

### Community 119 - "read_helpers.py"
Cohesion: 0.10
Nodes (38): A dropdown whose value a send carries becomes a step (discovery's send-guard…, clean_label(), column_header(), headings(), is_word(), label_near(), merged_label(), off_table() (+30 more)

### Community 120 - "test_shared_evidence.py"
Cohesion: 0.14
Nodes (19): config_hash(), git_sha(), JsonValue, Path, Evidence helpers shared by discovery and replay: masking a JSON-able tree,…, `git rev-parse HEAD`, or "unknown" (no git, not a repo, any failure)., sha256 of the repr of the frozen configs plus the site name., What ``run.json`` holds: prompt version, model, config hash, git sha. Never a… (+11 more)

### Community 121 - "test_locate.py"
Cohesion: 0.24
Nodes (15): _dup_target(), _look(), Path, Target, cua.replay.locate: the 3 rungs + table cell; all miss -> None. Ported from…, test_a_single_text_match_is_rung1_as_before(), test_all_miss_is_none(), test_duplicate_text_picks_the_copy_nearest_the_anchor() (+7 more)

### Community 122 - ".get"
Cohesion: 0.11
Nodes (25): field_area(), goes_to_a_page(), is_select(), log_sent_dropdowns(), mark_submits(), needed_moves(), no_op(), one_read_per_table() (+17 more)

### Community 123 - "masked_outputs"
Cohesion: 0.40
Nodes (5): masked_outputs(), JsonValue, Names and shape only: a value is ***, a table keeps its rows and columns, every…, parametrize, test_masked_outputs_keep_the_shape()

### Community 127 - "locate"
Cohesion: 0.11
Nodes (26): anchor_point(), append_rows(), do_extract_table(), fill(), find_text(), locate(), next_rung(), norm() (+18 more)

### Community 133 - "build_capability"
Cohesion: 0.29
Nodes (7): build_capability(), output(), Capability, CapabilityMeta, Steps, inputs and secrets come from the log only. The model's text cannot fail…, ``build_capability``'s refusals, unchanged: a leaked value, a blind dropdown,…, _refuse()

### Community 134 - "replay/context.py"
Cohesion: 0.12
Nodes (16): dataclasses, Ctx, note_takeover_send(), Page, Request, Ctx: what every replay function takes first (session, run, settings, send…, R7: nothing kept. A fresh run, and the guard reads that one from now on., wipe() (+8 more)

### Community 135 - "Box"
Cohesion: 0.12
Nodes (16): Box, cell_shape(), col_of(), like_rows(), number(), The column the box overlaps most, or None when it overlaps none (outside the…, Texts grouped into lines, top to bottom., A line's texts in the asked columns, left to right; two texts in one column are… (+8 more)

### Community 139 - "choose_option"
Cohesion: 0.50
Nodes (4): choose_option(), The option is in the box's OCR, even merged with its label ('to account…, Select this exact live option in the Nth <select> (`index`), else the one at…, shows_option()

### Community 140 - "pathlib"
Cohesion: 0.11
Nodes (6): pathlib, The prompts are the first filter (user, 2026-09-30); the models and code checks…, Moved from test_read_runs.py / test_extract_table.py (their tool code is now in…, test_the_prompt_keeps_the_read_and_table_rules(), The hand-back extension never touches any site: no content scripts, no host…, Guard: no site value lives in src/. Site values belong in configs/<site>.yaml…

### Community 142 - "re"
Cohesion: 0.40
Nodes (4): re, Value types an extract may declare. Shared by discovery and replay (one table,…, True when the whole value is exactly that type (string, number, boolean, or a…, value_matches_type()

### Community 149 - "test_capability.py"
Cohesion: 0.23
Nodes (7): _data(), parametrize, Path, cua.schema.Capability loads every saved artifact and refuses an unknown schema…, test_a_wrong_schema_version_is_refused(), test_an_unknown_key_is_refused(), test_every_saved_artifact_loads()

## Knowledge Gaps
- **158 isolated node(s):** `MODES`, `manifest_version`, `name`, `version`, `description` (+153 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **18 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `BrowserConfig` connect `BrowserConfig` to `FakeRoute`, `replay/context.py`, `test_input.py`, `Look`, `test_dropdown.py`, `test_replay_handback.py`, `test_replay_steps.py`, `FakeTab`, `DiscoveryConfig`, `test_takeover_loop.py`, `discovery/context.py`, `test_extension.py`, `config.py`, `loader.py`, `make_replay_ctx`, `look.py`, `FakePage`, `crops.py`, `handoff/__init__.py`, `test_screenshot.py`, `test_shared_evidence.py`?**
  _High betweenness centrality (0.033) - this node is a cross-community bridge._
- **Why does `Ctx` connect `Ctx` to `FakeRoute`, `test_act.py`, `test_replay_inputs.py`, `Look`, `discovery/run.py`, `test_replay_rescue.py`, `test_replay_handback.py`, `test_replay_wiring.py`, `test_replay_table.py`, `test_replay_steps.py`, `nav.py`, `human.py`, `FakeTab`, `DiscoveryConfig`, `discovery/context.py`, `HeldPage`, `read.py`, `discovery/wiring.py`, `rescue.py`, `config.py`, `make_replay_ctx`, `norm`, `look.py`, `FakePage`, `ScriptedControl`, `test_human.py`, `act.py`, `test_dropdowns.py`, `read_helpers.py`?**
  _High betweenness centrality (0.027) - this node is a cross-community bridge._
- **Why does `FakeRoute` connect `FakeRoute` to `Look`, `config.py`, `DiscoveryConfig`, `BrowserConfig`, `test_send_guard.py`, `test_dropdowns.py`, `Ctx`, `discovery/context.py`?**
  _High betweenness centrality (0.023) - this node is a cross-community bridge._
- **Are the 35 inferred relationships involving `BrowserConfig` (e.g. with `Session` and `Answerable`) actually correct?**
  _`BrowserConfig` has 35 INFERRED edges - model-reasoned connections that need verification._
- **Are the 52 inferred relationships involving `Ctx` (e.g. with `Session` and `DiscoveryConfig`) actually correct?**
  _`Ctx` has 52 INFERRED edges - model-reasoned connections that need verification._
- **Are the 29 inferred relationships involving `ReplayConfig` (e.g. with `Ctx` and `_Request`) actually correct?**
  _`ReplayConfig` has 29 INFERRED edges - model-reasoned connections that need verification._
- **What connects `MODES`, `manifest_version`, `name` to the rest of the system?**
  _158 weakly-connected nodes found - possible documentation gaps or missing edges._