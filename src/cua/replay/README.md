# cua.replay

No LLM, deterministic: runs a capability discovery saved, step by step, on the live site.

## Read order
1. `loader.py` - `load_capability` (YAML -> `Capability`, viewport/host/input/secret/crop checks),
   `load_outcomes` (a capability's own `outcomes:` or the site's defaults), `seen_outcome` (R17),
   `given_inputs`/`fill`/`secret_name`/`step_inputs`, and the two prompts `ask_inputs` (R8: one
   form before step 1) / `ask_option` (a dropdown value that is not a live option).
2. `locate.py` - the rungs (table cell, OCR text, anchor, template) and `locate()`. Pure.
3. `run.py` - `ReplayRun` (one run's working state; satisfies `cua.safety.SendState`) and
   `LastRun` (the mask set + final screen kept for evidence, memory only).
4. `context.py` - `Ctx` (session, cfg, control window, secrets, `shoot`, run, last, guard) and
   `wipe(ctx)`. The `SendGuard` is built here with replay's hooks and `REPLAY_OPTIONS`.
5. `wiring.py` - `attach(session, site, cfg) -> Ctx` (route guard, response listener once per page,
   replay control window, `cuaReply`), and the page wrappers `look`/`canvas`/`to_page`/`snap`/
   `act`/`stash_dropdowns`/`note_response`.
6. `steps.py` - `find` (rungs, then scroll), `shows`, `do_navigate` ... `do_extract_table`,
   `do_extract_options` (the dropdown's live options, by its recorded index), `ACTIONS`.
7. `rescue.py` - `rescue` (help panel -> take-over, built from `cua.handoff` pieces).
8. `engine.py` - `judge` (R17), `run_step` (one retry, never a send or a secret), `walk`,
   `run_cleanup`, `finish`, `open_start`, `replay(ctx, path, inputs)`.
9. `evidence.py` - `save_evidence(ctx, result, cap_path, out_dir)`: one masked folder per run
   (summary, drift, failure, final, take-over shots, capability, `run.json`).

## How it fits
```python
session = await open_session(site, BrowserConfig(), existing=session)
ctx = await attach(session, site, ReplayConfig())
result = await replay(ctx, "artifacts/pay_bill.yaml", {"amount": "10"})
save_evidence(ctx, result, "artifacts/pay_bill.yaml", Path("evidence/replay"))
```
Every function takes `ctx` first. R7: `replay()`'s `finally` swaps `ctx.run` for a fresh
`ReplayRun` (and points the guard at it), so after it returns the run holds no input values,
given text or look; only `ctx.last.values` (to mask evidence) survives, in memory.
The engine looks up `steps.ACTIONS`/`steps.find`/`steps.shows`/`rescue.rescue` at call time, so a
test swaps one with `monkeypatch` (as the old notebook tests swapped globals).

## What may NOT go here
- Never import `cua.discovery` (and discovery never imports this).
- No LLM call, no site value (those live in `configs/<site>.yaml`).
- May import `cua.schema`, `cua.vision`, `cua.browser`, `cua.safety`, `cua.handoff`, `cua.config`,
  `cua.evidence`.
