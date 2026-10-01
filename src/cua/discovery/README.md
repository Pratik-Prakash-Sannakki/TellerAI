# cua.discovery

The LLM side: an agent learns a task once, and the recorder saves what it did as a capability
that replay runs without an LLM. Built up step by step (`docs/PRODUCTIONIZE_PLAN.md`).

## Read order
1. `recorder/` - event log -> `Capability` -> YAML (pure; step 3).
2. `run.py` - `DiscoveryRun` (was `HandoffState`): one run's working state, fresh per goal. Also
   `navs` (main-frame navigations) and `act_lock` (one tool call at a time). Satisfies
   `cua.safety.SendState` (`given_text()` = goal + every answer). `run_values(run, secrets)`,
   `saved_texts`, `wipe(run, secrets)` (run_goal's `finally`: flag leaks, keep `redact`, drop
   entered/given/look/typed_texts), `DECLINED`.
3. `context.py` - `Ctx(session, cfg, guard, control, secrets)`, frozen. `ctx.run` is
   `ctx.guard.state` (a property), `ctx.site`, `ctx.page`. Page wrappers, all `ctx` first:
   `look` (take_look + run.look + start-event bookkeeping), `canvas`, `to_page`, `crop`
   (cut_crop at the current canvas), `snap`, `act(ctx, *steps)`, `into_box`, `list_options`,
   `choose_option`.
4. `wiring.py` - `build_ctx(session, cfg, secrets)` (guard + discovery control window, no page
   wiring), `attach(session, cfg, secrets) -> Ctx` (the setup cell: unroute/route the guard,
   nav counter, expose `cuaReply` tolerating "already registered", close -> fail closed, show
   "Agent is working", site to front), `new_run(ctx, goal) -> Ctx`.
5. `tools/` - `failed.FAILED`; `guard.py` (`log`, `mark_stuck`, `note_call`, `after_login_click`,
   `gate_click`, `needs_human_value`, `resolve_point`, `one_at_a_time(ctx)`); `human.py`
   (`human_help`, `take_over`, `offer_control`, `human_fills`); `dropdowns.py`
   (`log_sent_dropdowns`, the guard's on_sent hook); `read_helpers.py` (`clean_label`,
   `label_near`, `spot`, `merged_label`, `where`, `is_word`, `headings`, `page_texts`,
   `column_header`, `row_block`, `table_cell`, `read_target`, `value_in_box`, `is_header`,
   `off_table`; the run's values are an explicit `values` argument).
6. `tools/` @tools (step 8b) - `build_tools(ctx)` returns the notebook's 12 tools in TOOLS order:
   `observe.py` (`blocks`, `reply`, observe), `act.py` (`landed`, click, type_text, type_secret,
   select_option), `nav.py` (scroll, open_path), `read.py` (extract_value, extract_table),
   `human.py` (finish_business_outcome, request_missing_values, ask_human, `start_page_refusal`).
   Each module has `make_<group>_tools(ctx)`. Names, signatures and docstrings are the notebook's
   (the model reads them; `tests/unit/discovery/tools/test_build_tools.py` pins them).

7. `agent/` (step 8c) - prompt, middleware, optional TypeSafe routing, `build_agent(ctx, model)`
   (see `agent/README.md`).
8. `goal.py` - `run_goal(ctx, agent, goal, thread_id=None) -> str`: `new_run` + the start event
   (new thread only), the answer, the final shot on STUCK/DECLINED or a crash, `wipe` in `finally`.
9. `evidence.py` - `save_evidence(ctx, out_dir, capability=None, model=None, ocr_fn=None)`: one
   masked folder per run, plus `run.json` (prompt version, model, config hash, git sha).

## Contracts for the tools / agent (steps 8b, 8c)
- Build the ctx once per session (`attach`), then `new_run(ctx, goal)` per goal. The run swap
  assigns `ctx.guard.state`; the same ctx (and every tool closed over it) sees the new run. Never
  cache `ctx.run` across a `new_run`.
- A tool: `@tool(parse_docstring=True)` over `@one_at_a_time(ctx)` over an `async def` closure.
  `tools/__init__` stays import-light (it is loaded while `context` is still importing, via
  `tools.failed`), so `build_tools` imports the tool modules inside itself. `observe` imports
  `guard` as a module (guard -> human -> observe -> guard).
  `one_at_a_time` counts steps, checks repeats on the call's keyword args, resets
  `run.verdict`, and turns STUCK/STOP/BLOCKED results or `unsure_limit` failures into
  `human_help`. A result is `str` or content blocks (text block first).
- `log(ctx, tool, args, result, point, crop, **extra)` - point/crop positional or keyword.
- Values for `where`/`page_texts`: `run_values(ctx.run, ctx.secrets)`.
- Site words: `ctx.site`; limits: `ctx.cfg` (DiscoveryConfig), `ctx.session.cfg` (BrowserConfig).
- `secrets` maps secret NAME -> value (from `.env` via `cua.config.resolve_secret`), in memory
  only; tools name secrets, never show values.

## What may NOT go here
- Never import `cua.replay` (and replay never imports this).
- No site value (host, URL, words): those live in `configs/<site>.yaml`.
- Secrets by name only, never a value in code, logs or the model's context.
- `tools/dropdowns.py` and the guard hooks in `wiring.py` run while a send is held: no page call.
