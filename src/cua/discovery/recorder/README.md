# cua.discovery.recorder

Turns discovery's event log (one `Event` per tool call) into a replay-ready `Capability` and
writes it to disk. Pure Python: no browser, no network; only `describe` calls a model, which the
caller passes in.

## Read order
1. `events.py` - which events become steps (R16): `step_events` and its filters
   (`mark_submits`, `one_read_per_table`, `without_no_ops`, `without_detours`, `without_logout`),
   field helpers (`is_select`, `same_spot`, `input_name`), and `flag_leaks` (marks an event whose
   label holds a value typed this run, so the build refuses it).
2. `checkpoint.py` - the text replay must see to call the run a success.
3. `build.py` - `to_step`, `build_capability` (steps/inputs/secrets from the log only; refuses
   take-overs, leaked values, blind dropdowns and runs that read or sent nothing).
4. `save.py` - `crops_for`, `save_artifact` (default `artifacts/<name>.yaml` +
   `artifacts/crops/<name>/`), `describe(goal, log, model)` (the model writes only metadata).

## What may NOT go here
- No browser, no Playwright, no I/O other than `save_artifact`'s file writes.
- Never stores a typed, selected or secret value: labels, points and crops only.
- May import `cua.schema`, `cua.safety`, `cua.discovery.tools.guard`; never `cua.replay`.
