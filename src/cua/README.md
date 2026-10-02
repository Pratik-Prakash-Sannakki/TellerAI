# cua

The productionized package behind the discovery and replay notebooks. Being built up step by
step (see `docs/PRODUCTIONIZE_PLAN.md`); later steps append their folders here.

## Read order
1. `config.py` - site profile (`load_site` -> frozen `SiteProfile` from `configs/<site>.yaml`),
   `BrowserConfig` / `DiscoveryConfig` / `ReplayConfig`, model env settings, `resolve_secret`,
   `host_allowed`. Loads `.env` at import.
2. `schema/` - the contract between discovery and replay (capability, value types, results,
   events). Pure, no I/O.
3. `llm.py` - `make_chat_model`, the one place a chat model is built (direct Anthropic; an optional
   Anthropic-compatible gateway via env vars).
4. `eval.py` - `cua eval`'s report: `summarize` N `ReplayResult`s into a frozen `EvalReport`
   (status counts, rung histogram, `fallback_steps`, output stability as bools), `render`,
   `save_report`. Pure, no browser; `cli.py` runs the replays.

## Rules
- No site value (host, URL, words, env-var names) in `src/`: they live in `configs/<site>.yaml`
  only (guarded by `tests/unit/test_no_site_values.py`).
- Secrets: names only in code, logs and model context; `.env` is the only value source.
- Import rule: `schema` imports nothing else from cua; `discovery` and `replay` never import each
  other.
