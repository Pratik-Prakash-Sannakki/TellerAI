# Docs

Start with the top-level [README](../README.md) (problem, demo path, architecture) and
[REPORT](../REPORT.md) (design and trade-offs). Code-level read order:
[`src/cua/README.md`](../src/cua/README.md).

## Components

One doc per major part: purpose, where it lives, how it works, API, config, guarantees, tests,
limits, decision IDs.

| Doc | What it covers |
|---|---|
| [capability-format.md](components/capability-format.md) | the schema: capability YAML, steps, targets (rungs), value types, `ReplayResult` |
| [config.md](components/config.md) | site profiles (`configs/<site>.yaml`), run settings, secrets, multi-tenant |
| [llm-and-routing.md](components/llm-and-routing.md) | `make_chat_model`, Sonnet / Haiku, TypeSafe tool and model routing, LangSmith |
| [discovery-agent.md](components/discovery-agent.md) | the deep agent: middleware, 13 tools, tool guards, run lifecycle |
| [recorder.md](components/recorder.md) | event log to capability: step filters, checkpoint, typed inputs, masked save |
| [replay.md](components/replay.md) | the no-LLM engine: loader, rungs, step checks, outcome rules, rescue, cleanup |
| [vision.md](components/vision.md) | screenshot, RapidOCR, numbering, crops, the shared table reader |
| [browser.md](components/browser.md) | Playwright session, site lock, our own input, native dropdowns |
| [safety.md](components/safety.md) | SendGuard (mismatch check, Gate 1, Gate 2), host lock, allowlists, masking |
| [guardrails.md](components/guardrails.md) | NeMo input rail on the goal, output rail on the answer |
| [handoff.md](components/handoff.md) | the "Agent control" tab, take-over, the hand-back extension |
| [cli-and-eval.md](components/cli-and-eval.md) | `cua discover` / `replay` / `eval`, the stability report |
| [evidence.md](components/evidence.md) | the masked run folders and the code that writes them |

## Decisions

- [discovery-decisions.md](decisions/discovery-decisions.md): Base, Q7-Q23.
- [replay-decisions.md](decisions/replay-decisions.md): R1-R22.

## Architecture

- [agent-architecture.md](architecture/agent-architecture.md): the discovery run end to end, and
  the guardrail layers.
- [discovery-architecture.md](architecture/discovery-architecture.md) and
  [replay-architecture.md](architecture/replay-architecture.md): notebook-era design walkthroughs.

## Plans (historical)

- [PRODUCTIONIZE_PLAN.md](PRODUCTIONIZE_PLAN.md): notebooks to the `src/cua/` package (done).
- [plans/discovery-plan.md](plans/discovery-plan.md), [plans/replay-plan.md](plans/replay-plan.md):
  the two notebook builds.
- [superpowers/specs/2026-10-03-nemo-guardrails-design.md](superpowers/specs/2026-10-03-nemo-guardrails-design.md)
  and [superpowers/plans/2026-10-03-nemo-guardrails.md](superpowers/plans/2026-10-03-nemo-guardrails.md):
  the guardrails design and build plan.

## Elsewhere

- [`evidence/README.md`](../evidence/README.md): evidence folder layout and the kept runs.
- Per-subpackage READMEs under `src/cua/*/`: read order and import rules for each package.
