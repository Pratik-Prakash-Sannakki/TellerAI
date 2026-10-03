# Discovery agent

The LLM side. A deep agent learns a task once from screenshots, one tool call per turn. Our code
decides whether each action may happen. Its event log feeds the [recorder](recorder.md).

Overview of the whole run, with the guardrail layers:
[agent-architecture.md](../architecture/agent-architecture.md).

## Where it lives

- [`src/cua/discovery/`](../../src/cua/discovery/) (read order:
  [`discovery/README.md`](../../src/cua/discovery/README.md))
  - `agent/` ([`agent/README.md`](../../src/cua/discovery/agent/README.md)): `prompt.py`,
    `middleware.py`, `routing.py`, `build.py`.
  - `tools/`: `observe.py`, `act.py`, `nav.py`, `read.py`, `human.py`, plus `guard.py` (the
    shared tool guards), `read_helpers.py`, `dropdowns.py`, `failed.py`.
  - `run.py` (`DiscoveryRun`), `context.py` (`Ctx`), `wiring.py` (`attach`, `new_run`),
    `goal.py` (`run_goal`), `evidence.py` ([evidence](evidence.md)).

## How it works

- **Build.** `build_agent(ctx, model)` calls deepagents' `create_deep_agent` with our 13 tools,
  `VISUAL_SYSTEM_PROMPT`, a `MemorySaver` checkpointer, and middleware in this order:
  1. `RecordWhy`: keeps the model's text before its tool calls as `run.why`, masked (run values,
     secrets, the calls' own args, then any email / phone / amount / date / 4+ digit run), max
     200 chars. Each logged event carries it.
  2. `NoopAnthropicPromptCachingMiddleware`: prompt caching off.
  3. `LatestScreenshotOnly`: only the newest screenshot reaches the model.
  4. `OnlyOurTools`: deepagents' built-in file and `task` tools are never offered; a call to any
     other name returns `REFUSED` and never runs.
  5. TypeSafe `ToolRouter` + `ModelRouter`, only when on ([LLM and routing](llm-and-routing.md)).
- **Wire.** `attach(session, cfg, secrets)` builds the `SendGuard` and the control window,
  routes every request on the site tab through the guard, counts main-frame navigations, binds
  `cuaReply`, and shows "Agent is working".
- **Run.** `run_goal(ctx, agent, goal)` starts a fresh `DiscoveryRun` (`new_run`), logs a `start`
  event (base URL, viewport, scale), and invokes the agent under `run_timeout_s`. Past the
  deadline the run ends `STUCK` and keeps what it did. A `finally` always calls `wipe`.
- **See.** `observe` and the acting tools return content blocks: text first (the URL without its
  session id, then `[ref] 'text' box=(...)` per OCR box, secrets hidden), then the numbered
  screenshot. The model points with a box number or x,y.

### The 13 tools

| Group | Tool | What it does |
|---|---|---|
| see | `observe` | new screenshot, OCR, number every text box |
| act | `click` | a box or x,y; refuses a native `<select>` (use `select_option`) |
| act | `type_text` | click a box, clear, type |
| act | `type_secret` | type a secret by NAME; the model never sees the value |
| act | `select_option` | set a native dropdown (the one non-visual exception, see [browser](browser.md)) |
| nav | `scroll` | scroll, then a new look |
| nav | `open_path` | open a path on the allowed site |
| read | `extract_value` | save a value from a box, with a declared type |
| read | `extract_table` | read a table by header and columns |
| read | `extract_options` | save a dropdown's option texts |
| ask | `request_missing_values` | a human fills fields the goal gives no value for; our code types them |
| ask | `ask_human` | answer in words, take over, or stop |
| finish | `finish_business_outcome` | report the result with proof text that must be on screen |

### Tool guards (`tools/guard.py`)

Every tool is `@tool` over `@one_at_a_time(ctx)`:

- One call at a time (`run.act_lock`), counted against `step_budget` (40).
- The same call `repeat_limit` (3) times in a row is `STUCK`.
- `allowed_actions`: a tool whose action the site does not allow returns `REFUSED`
  (`TOOL_ACTIONS` maps tools to actions; `extract_options` counts as `extract`).
- A `STUCK` / `STOP` / `BLOCKED` result, or `unsure_limit` (3) failures in a row, calls
  `human_help`: answer, take over, or stop ([handoff](handoff.md)).
- `gate_click`: deny words are refused; a click a human declined is not retried; the login click
  waits until every secret is typed; login stops after `login_limit` failures.
- No per-click approval. Moving around needs none; anything that sends data meets the two gates
  ([safety](safety.md)).

## Public API / key types

`build_agent(ctx, model)`, `run_goal(ctx, agent, goal, thread_id=None) -> str`,
`attach(session, cfg, secrets) -> Ctx`, `new_run(ctx, goal)`, `build_tools(ctx)`, `Ctx`,
`DiscoveryRun`, `run_values`, `wipe`, `VISUAL_SYSTEM_PROMPT`, `PROMPT_VERSION`.

## Config knobs

- `DiscoveryConfig`: `step_budget`, `repeat_limit`, `unsure_limit`, `login_limit`,
  `run_timeout_s`, `send_wait_ms`, `handback_s`, `snap_ms` ([config](config.md)).
- Site profile: `deny_words`, `login_words`, `login_failure_texts`, `login_empty_texts`,
  `allowed_actions`, `secret_env`.
- `PROMPT_VERSION` (`agent/prompt.py`): a test pins the prompt's sha256, so an edit forces a bump.

## Safety and guarantees

- The model picks; our code decides. Every action passes the guards, the host lock and the send
  gates.
- Secrets by name only: `type_secret(name)`; human-entered values go through
  `request_missing_values`, typed by our code. Neither reaches the model.
- `wipe` (end of every run) flags leaks in the log, then drops entered, given and typed values
  and the last look. `forget` (after evidence) drops reads, chat, answer and every crop.
- The final answer passes the output rail before it is printed or stored ([guardrails](guardrails.md)).

## Tests

- `tests/unit/discovery/agent/` (`test_build.py`, `test_middleware.py`, `test_prompt.py`,
  `test_routing.py`).
- `tests/unit/discovery/tools/` (`test_act.py`, `test_read.py`, `test_read_helpers.py`,
  `test_human_tools.py`, `test_build_tools.py` pins the 13 names, signatures and docstrings).
- `tests/unit/discovery/` (`test_guard.py`, `test_human.py`, `test_goal.py`, `test_run.py`,
  `test_wiring.py`, `test_dropdowns.py`).

## Limits and cuts

- Pure visual is slower and OCR-noisy; it is chosen because it works with no clean DOM (REPORT §1).
- Sitemap hint before discovery (Q15): designed only.
- No hostile local test page (Q18); ParaBank only.

## Decisions

- Base, Q7, Q12, Q13, the "Tools" decision, Q15, Q17, Q22 in
  [discovery-decisions.md](../decisions/discovery-decisions.md). Q12 (keyboard dropdowns) and Q17
  (per-click approval) were later replaced in code by the native-dropdown script and the
  network-level send gates.
- Notebook-era walkthrough: [discovery-architecture.md](../architecture/discovery-architecture.md).
