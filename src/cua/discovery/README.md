# cua.discovery

The LLM side: an agent learns a task once, and the recorder saves what it did as a capability
that replay runs without an LLM. Built up step by step (`docs/PRODUCTIONIZE_PLAN.md`).

## Read order
1. `recorder/` - event log -> `Capability` -> YAML (pure; step 3).
2. `tools/` - the agent's tools. Step 3 has only `guard.FAILED`; later steps add the rest.

## What may NOT go here
- Never import `cua.replay` (and replay never imports this).
- No site value (host, URL, words): those live in `configs/<site>.yaml`.
- Secrets by name only, never a value.
