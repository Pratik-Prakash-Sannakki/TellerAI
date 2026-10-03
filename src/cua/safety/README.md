# cua.safety

What may leave the tab, and keeping values out of whatever is stored, logged or shown.

## Read order
1. `hosts.py` - `host_allowed(url, site)` (D15). `cua.config` re-exports it.
2. `redact.py` - `norm`, `is_sensitive(label, words)`, `hide_secrets(text, secrets)`,
   `redactor(values, mask=, number=)`, `mask_png(png, redact, ocr_fn)`. `NUMBER` is discovery's
   pattern; replay passes `number=REPLAY_NUMBER` (whole numbers only, never the 1 in 'rung1').
3. `request.py` - `sent_fields`, `rebuilt`, `pretty` over a small `Request` Protocol.
4. `mismatch.py` - `mismatches(fields, given_text, words)`, `dropdown_options(fields, keys,
   dropdowns, hide)`. The run supplies the given text and the pre-click dropdown stash.
5. `send_guard.py` - `SendGuard(state, control, secrets, words, hooks, *, options)`: Gate 1
   (Approve/Edit) and Gate 2 for every non-GET request. `guard.lock` is the send gate.
   `SendState`/`ControlLike` are Protocols; `SendHooks` and `GuardOptions`
   (`DISCOVERY_OPTIONS`/`REPLAY_OPTIONS`) carry each side's exact differences.

## Rules
- The guard is never given a page: a held form POST blocks every page call.
- Locks are built in `SendGuard.__init__`, so build the guard inside the running loop.

## What may NOT go here
- May import only `cua.schema`, `cua.vision`, `cua.browser`, `cua.config`.
- Never `cua.discovery` or `cua.replay` (they import this). Route install is theirs.
