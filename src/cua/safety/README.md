# cua.safety

Keeps values out of whatever is stored, logged or shown. Step 3 lands only `redact.py`; step 6
adds the send/host gates.

## Read order
1. `redact.py` - `norm` (compare texts), `redactor(values, mask=)` (mask this run's values:
   numbers however written, whole words case-insensitively). These are discovery's versions;
   replay's differ (its `NUMBER` has look-arounds, no `mask=`) and must stay a separate behaviour.

## What may NOT go here
- May import only `cua.schema`, `cua.vision`, `cua.browser`, `cua.config`.
- Never `cua.discovery` or `cua.replay` (they import this).
