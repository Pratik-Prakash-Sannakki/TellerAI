# LLM factory and model routing

One function builds every chat model in the project. Discovery uses Claude Sonnet by default; an
optional TypeSafe router can narrow the tools and pick Haiku per step. Replay uses no model.

## Where it lives

- [`src/cua/llm.py`](../../src/cua/llm.py): `make_chat_model`, `model_name_for`.
- [`src/cua/config.py`](../../src/cua/config.py): `SONNET_MODEL_NAME` (`claude-sonnet-5`),
  `HAIKU_MODEL_NAME` (`claude-haiku-4-5-20251001`).
- [`src/cua/discovery/agent/routing.py`](../../src/cua/discovery/agent/routing.py): `ToolRouter`,
  `ModelRouter`, `build_routing_middleware`.

## How it works

### `make_chat_model(kind="sonnet", **overrides)`

- `kind` is `"sonnet"` or `"haiku"`; anything else raises `ValueError`.
- Builds a `ChatAnthropic` against `https://api.anthropic.com`, always. A stray
  `ANTHROPIC_BASE_URL` in the shell never redirects calls.
- Raises `RuntimeError` when `ANTHROPIC_API_KEY` is not set.
- TLS: if only `REQUESTS_CA_BUNDLE` is set, it is copied to `SSL_CERT_FILE` (for a corporate CA).
  Verification is never turned off.
- `overrides` pass through (e.g. `max_tokens`, `temperature`).

Who calls it:

| Caller | Model | Why |
|---|---|---|
| `cua discover` (`cli.discover`) | Sonnet | the deep agent, and `describe()` (capability metadata) |
| `cua discover`, rails on | Haiku | the input rail's unsure band ([guardrails](guardrails.md)) |
| `ModelRouter` (routing on) | Haiku or Sonnet | per step |
| `cua replay` / `cua eval` | none | replay is plain code |

### TypeSafe routing (optional)

- Off unless `TYPESAFE_API_KEY` is set: `build_routing_middleware` returns `[]` and prints
  "model router OFF". `langchain_typesafe` (extra `typesafe`) is imported only when on.
- When on, it returns two middlewares, appended last in the agent ([discovery agent](discovery-agent.md)):
  - **`ToolRouter`** asks TypeSafe which job the step is: `login`, `fill_form`, `read_value`,
    `navigate`, `need_human` or `finish`. At confidence >= 0.8 (`JOB_CONFIDENCE_THRESHOLD`), the
    offered tools narrow to that job's tools plus four always kept (`observe`, `click`,
    `type_secret`, `ask_human`). Below that, all tools stay.
  - **`ModelRouter`** asks `fast` or `powerful` on **every** model call. Haiku only when the answer
    is `fast` and confidence >= 0.8. Else Sonnet. (TypeSafe's stock router decides once per run.)
- What leaves for typesafe.ai (`step_state`): the page name (last URL path segment, no query, no
  `;jsessionid`), the last tool's name, and its status word (letters only: `OK`, `REFUSED`,
  `Saved`). Never screen text, a URL token or a value.

### Observability

LangSmith tracing is switched on by env vars only (`LANGSMITH_TRACING`, `LANGSMITH_ENDPOINT`,
`LANGSMITH_API_KEY`). No code. What the model sees (screenshots, goal, its messages) is traced;
secret values never reach the model, so they never reach a trace.

## Public API / key types

`make_chat_model(kind, **overrides) -> BaseChatModel`, `model_name_for(kind)`, `ModelKind`;
`build_routing_middleware(page_path) -> list[AgentMiddleware]`, `ToolRouter`, `ModelRouter`,
`confidence_gate`, `job_tool_names`, `step_state`, `page_name`.

## Config knobs

| Knob | Where | Effect |
|---|---|---|
| `ANTHROPIC_API_KEY` | `.env` | required for discovery |
| `TYPESAFE_API_KEY` | `.env` | turns routing on (needs `uv sync --extra typesafe`) |
| `LANGSMITH_*` | `.env` | traces |
| `SSL_CERT_FILE` / `REQUESTS_CA_BUNDLE` | `.env` | corporate CA |
| `JOB_CONFIDENCE_THRESHOLD` | `routing.py` | 0.8, the gate for both routers |

## Safety and guarantees

- **Fails open, never blocks.** Low confidence, a timeout or any classifier error keeps every tool
  and uses Sonnet. Errors print the exception type only, never its text.
- The API key is never printed or logged; `ChatAnthropic` holds it as a `SecretStr`.
- `OnlyOurTools` runs before routing, so routing only narrows within our tools.

## Tests

- `tests/unit/test_llm.py` (direct Anthropic, base-URL env ignored, fixed names, key never in
  `repr`, missing key, CA bundle).
- `tests/unit/discovery/agent/test_routing.py` (gate, job tools, step state, fail-open, per-step
  model choice).

## Limits and cuts

- Live runs: confidence was mostly 0.35-0.53, so tool narrowing rarely engaged; most steps went to
  Haiku, Sonnet near the end (REPORT §1).
- Token and cost totals stay in LangSmith; copying them into `run.json` is a "next" item
  (REPORT §7).

## Decisions

- Q22 (TypeSafe tool selection + model routing) in
  [discovery-decisions.md](../decisions/discovery-decisions.md).
- R1 (no LLM at replay) in [replay-decisions.md](../decisions/replay-decisions.md).
