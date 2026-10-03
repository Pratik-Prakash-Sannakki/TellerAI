# Capability format (schema)

The contract between the two sides. Discovery writes a capability; replay reads it. Nothing else
crosses: `discovery` and `replay` never import each other.

A capability is one YAML file plus a few small template crops. It holds steps, targets, input
names and types, output names and types, and secret *names*. Never a value.

## Where it lives

- [`src/cua/schema/`](../../src/cua/schema/) (read order: [`schema/README.md`](../../src/cua/schema/README.md))
  - `capability.py`: `Capability`, steps, targets, `Input` / `Output`, `CapabilityMeta`.
  - `value_types.py`: `SHAPES`, `TYPES`, `value_matches_type` (one table for both sides).
  - `result.py`: `Status`, `Stop`, `ReplayResult`.
  - `events.py`: `Event`, one discovery event-log entry (a type only).
- Saved capabilities: [`artifacts/<name>.yaml`](../../artifacts/) + `artifacts/crops/<name>/s<i>.png`.

## How it works

- Pydantic v2, strict: every model forbids extra keys (`extra="forbid"`).
- `schema_version` is `2` (`SCHEMA_VERSION`); any other value fails validation.
- A **step** is one of 8 actions, chosen by its `action` field:

| Action | Fields | Notes |
|---|---|---|
| `navigate` | `path` (starts with `/`) | |
| `click` | `target`, `cleanup` | `cleanup: true` = the final logout; runs after the checkpoint, always |
| `type` | `target`, `value` | `value` is `{{input}}` or `{{secret:name}}`, never a literal |
| `select` | `target`, `option`, `index` | `index` = Nth `<select>` on the page; `None` = by point |
| `scroll` | `direction` (`up` / `down`) | |
| `extract` | `target`, `save_as`, `pattern` | `pattern`: first match inside the box (a phone in a sentence) |
| `extract_table` | `header`, `columns`, `save_as`, `row_limit` (default 50) | header found like a rung-2 label |
| `extract_options` | `target`, `save_as`, `index` | a native dropdown's live option texts |

- A **target** is found by rungs, never by raw x,y. It must have an `anchor`, a `template` or a
  `table_cell` (validator `findable`):

| Field | Rung | Finds it by |
|---|---|---|
| `table_cell` | table | row key + column name |
| `ocr_text` | 1 | its own OCR text (+ `ordinal`) |
| `anchor` | 2 | a nearby label (+ `ordinal`) and a saved `offset` from the label's centre |
| `template` | 3 | a crop path, relative to the YAML |

- **Inputs:** `name` (snake_case), `type` (default `string`), `description`.
- **Outputs:** `name`, `type`, `description`, and `columns` for a table. `type` is a value type,
  `table` (a list of `{column: text}` rows) or `options` (a list of strings).
- **Value types** (`TYPES`): `string`, `number`, `boolean`, plus the shapes `phone`, `currency`,
  `date`, `integer`, `email`, `id`. `value_matches_type` is a full match on the stripped value.
- **Top level:** `name`, `version`, `description`, `base_url`, `viewport`,
  `device_scale_factor`, `inputs`, `outputs`, `secrets` (names), `steps` (at least one),
  `checkpoint` (text on the final screen that proves success).
- **Optional `outcomes:`** (replay only): a capability may carry its own outcome rules. The loader
  pops the key before validation; when present it replaces the site's defaults
  ([config](config.md)).
- **`CapabilityMeta`** is the only part the model writes: `name`, `description`, input
  descriptions, `success_text`. It is loose on purpose; the recorder slugs the name and ignores
  unknown input names ([recorder](recorder.md)).

Example: [`artifacts/get_account_balance.yaml`](../../artifacts/get_account_balance.yaml)
(two `{{secret:...}}` types, the login click, one `extract` with output type `currency`, and a
`cleanup: true` logout).

### Results

- `Status` (StrEnum): `SUCCESS`, `BUSINESS_OUTCOME`, `DECLINED`, `STUCK`, `FAILED`.
- `Stop(status, reason, expected, observed)`: raised to end a replay early.
- `ReplayResult`: `status`, `outputs`, `drift` (per step: rung, point, attempt; no values),
  `reason`, `human` (take-overs and option choices), `failure`, `recoveries`, `cleanup`.
  `summary` renders e.g. `SUCCESS (human input at step 2; human intervened at step 4)`.

## Public API / key types

`Capability`, `Step` (discriminated union), `Target`, `OcrText`, `Anchor`, `TableCell`, `Header`,
`Input`, `Output`, `CapabilityMeta`, `SCHEMA_VERSION`, `TYPES`, `SHAPES`, `value_matches_type`,
`Status`, `Stop`, `ReplayResult`, `Event`. All re-exported from `cua.schema`.

## Config knobs

None. The schema is fixed. Page size is recorded per capability (`viewport`,
`device_scale_factor`) and checked by replay against `BrowserConfig.viewport`.

## Safety and guarantees

- No I/O and no imports from the rest of `cua` (`tests/unit/test_import_rules.py`).
- A `type` step's value is a placeholder, so a typed value can never be stored in a step.
- Secrets are listed by name only. Values come from `.env` at replay time.
- Crops are tight and other text is blanked, so a crop holds no customer data (Q14). Saving masks
  and leak-checks the whole artifact first ([recorder](recorder.md)).

## Tests

- `tests/unit/schema/test_capability.py`, `test_value_types.py`, `test_result.py`.
- `tests/integration/test_saved_artifacts.py`: every file in `artifacts/` loads and validates.
- `tests/integration/test_discovery_to_replay.py`: `build_capability` -> `save_artifact` ->
  replay's `load_capability`, unchanged.

## Limits and cuts

- One base capability per site. Per-tenant overlays over a base capability are designed, not
  built (REPORT §4).
- Discovery never writes `outcomes:`; that key is added by hand (REPORT §7).
- No per-step `expect` text (R14 cut); each step is checked by its action instead.

## Decisions

- Replay: R2 (rungs), R10-R13 (compile step, schema v2, target schema), R21 (table reads) in
  [replay-decisions.md](../decisions/replay-decisions.md).
- Discovery: Q7 / Q7b (text-less targets), Q8 / Q8b (tables), Q14 (private data in crops) in
  [discovery-decisions.md](../decisions/discovery-decisions.md).
