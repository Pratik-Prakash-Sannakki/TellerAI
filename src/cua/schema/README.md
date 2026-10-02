# cua.schema

The contract: what discovery writes and replay reads. Pure Pydantic / dataclasses, no I/O.

## Read order
1. `capability.py` - `Capability` (schema v2, `SCHEMA_VERSION = 2`), its steps and targets
   (rungs: `OcrText`, `Anchor`, template, `TableCell`; `ExtractOptions` reads a dropdown's
   options, an output of type `"options"`), `Input`/`Output`, `CapabilityMeta`
   (the only part the model writes).
2. `value_types.py` - `SHAPES`, `TYPES`, `value_matches_type`: the extract value types, one table
   for both sides.
3. `result.py` - `Status` (StrEnum), `Stop` (ends a run with a status), `ReplayResult`.
4. `events.py` - `Event` TypedDict: one discovery event-log entry (a type only).

## What may NOT go here
- No I/O (files, browser, network, env), no site values, no secret values.
- Imports nothing else from `cua`. Everything else may import this.
