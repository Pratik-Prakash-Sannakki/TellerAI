# cua

The package behind the `cua` CLI (`cua discover` / `cua replay` / `cua eval`).
Design docs, one per component: [`docs/README.md`](../../docs/README.md).

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
5. `evidence.py` - masking helpers shared by discovery and replay evidence.
6. Subpackages, each with its own `README.md`, in dependency order:
   - `vision/` - pixels to text: screenshots, OCR, crops, table reader.
   - `browser/` - Playwright session, site lock, our own input, native dropdowns.
   - `safety/` - send gates, masking, what may leave the tab.
   - `handoff/` - control tab, hand-back button, take-over.
   - `discovery/` - the LLM side: deep agent, tools, recorder.
   - `replay/` - no LLM: loader, locate rungs, engine.
7. `cli.py` - `cua discover` / `cua replay` / `cua eval`.

## Rules
- No site value (host, URL, words, env-var names) in `src/`: they live in `configs/<site>.yaml`
  only (guarded by `tests/unit/test_no_site_values.py`).
- Secrets: names only in code, logs and model context; `.env` is the only value source.
- Import rule: `schema` imports nothing else from cua; `discovery` and `replay` never import each
  other.
