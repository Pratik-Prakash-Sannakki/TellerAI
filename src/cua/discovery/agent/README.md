# cua.discovery.agent

The discovery agent: what the model is told, what wraps each model call, and how it is built.

## Read order
1. `prompt.py` - `VISUAL_SYSTEM_PROMPT` (the notebook's, verbatim, plus one later rule: save the
   send's confirmation before finishing) and `PROMPT_VERSION` (written to
   each run's `run.json`, never the artifact). A test pins the prompt's sha256: an edit forces a
   version bump.
2. `middleware.py` - `NoopAnthropicPromptCachingMiddleware` (prompt caching off; some
   Anthropic-compatible gateways reject cache markers), `LatestScreenshotOnly` (only the newest
   screenshot reaches the model), `RecordWhy` (the model's reason for each call, masked, max 200
   chars, put on each event as `why`).
3. `routing.py` - optional TypeSafe tool router + per-step Haiku/Sonnet model router. Off unless
   `TYPESAFE_API_KEY` is set (`build_routing_middleware(page_path) -> []`). Fails open: low
   confidence or any error keeps every tool and uses Sonnet. When on it sends the page path + last result text
   to typesafe.ai: never with real data. `langchain_typesafe` (extra `typesafe`) is imported
   only when on.
4. `build.py` - `build_agent(ctx, model)`: langchain `create_agent` over `build_tools(ctx)` (the
   model sees only these 13 tools: no deepagents filesystem or `task` sub-agent tools), the prompt,
   a `MemorySaver`, the middleware above (routing appended when on), and deepagents'
   `PatchToolCallsMiddleware` (answers a dangling tool call before a resume).

Run a goal with `cua.discovery.goal.run_goal(ctx, agent, goal)`; save the evidence with
`cua.discovery.evidence.save_evidence(ctx, out_dir, capability, model=...)`.

## What may NOT go here
- No site value (host, URL, words). The page path for routing comes from `ctx.page.url`.
- No secret value, ever. Tools name secrets; the prompt names only `'username'`/`'password'`.
- Never import `cua.replay`. `__init__` stays light (no langchain/deepagents import): use `agent.build`.
