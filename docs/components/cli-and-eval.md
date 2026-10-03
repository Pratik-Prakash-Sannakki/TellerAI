# CLI and eval

The `cua` command wires everything: `cua discover`, `cua replay`, `cua eval`. `cua eval` replays a
capability N times in one session and reports how stable it is.

## Where it lives

- [`src/cua/cli.py`](../../src/cua/cli.py): `main`, `entry` (the console script), `discover`,
  `run_replay`, `run_eval`, `check_eval`, `parse_args`, `parse_inputs`, `default_site`.
- [`src/cua/eval.py`](../../src/cua/eval.py): `EvalReport`, `summarize`, `render`,
  `save_report`, `run_rows`, `missing_inputs`, `sends_data`, `fallback_steps`. Pure: no browser,
  no LLM.

## How it works

### `cua discover "<goal>" [--site S] [--out DIR]`

1. Load the site profile. Build the NeMo classifier only if `rails` is not `off` and the extra is
   installed; warm it up (embedding download) before the check. A load error fails closed.
2. `check_goal`. Refused: print why, write a `REFUSED` evidence folder, exit **1**. No browser
   ([guardrails](guardrails.md)).
3. Open the browser, go to `start_url`, check the viewport, `attach`, build Sonnet and the agent,
   `run_goal` ([discovery agent](discovery-agent.md)).
4. Print the answer through the output rail (`safe_output`).
5. Save: `check_savable`, then `describe`, `build_capability`, `save_artifact` (masked and
   leak-checked). `NotSaved` prints the reason; evidence is still written ([recorder](recorder.md)).
6. Always write discovery evidence, then close the browser ([evidence](evidence.md)).

### `cua replay <capability.yaml> [--input k=v ...] [--site S] [--evidence]`

Open the browser, `attach`, `replay`, print status, outputs and drift (account ids by their last
digits), optionally save evidence. Exit 0 only on `SUCCESS` ([replay](replay.md)).

### `cua eval <capability.yaml> --runs N [--input k=v ...] [--site S] [--evidence]`

- `check_eval` runs before any browser: every input must come via `--input` (unattended runs);
  it warns when the capability sends data (each run will stop at the two gates).
- Replays N times in **one** browser session, re-attaching per run.
- `summarize` builds an `EvalReport`:
  - status counts, success rate, `assisted` (runs a human helped), `flaky` (statuses differ);
  - a per-step rung histogram (cleanup steps kept apart);
  - `fallback_steps`, the drift signal: steps whose first-choice rung (`rung1` / `table`) was not
    used every time (a step with no OCR text of its own starts at rung 2, so rung 2 there is not
    drift);
  - `output_stable` per output (same value in every `SUCCESS` run) and, for an unstable one, a
    value-free description (row counts, columns, cell shape and length).
- Writes `evidence/eval/<UTC>-<name>/report.json` + `run.json`. Exit 0 only if every run is
  `SUCCESS`.

### Process exit

`entry()` runs `main()`, flushes, then `os._exit(code)`: it skips interpreter teardown, where the
cached RapidOCR engine can abort on macOS and hide the real exit code. `main()` is the only
`asyncio.run` in the package.

## Public API / key types

`main(argv) -> int`, `entry()`, `discover(goal, site, out)`, `run_replay(...)`,
`run_eval(...)`; `EvalReport`, `summarize(results, cap)`, `render(report)`, `save_report(...)`.

## Config knobs

`--site` (default: the only profile in `configs/`), `--out` (default `artifacts`), `--input`
(repeatable, split on the first `=`), `--evidence`, `--runs` (default 3, at least 1).

## Safety and guarantees

- A refused goal never opens the browser.
- The eval report never holds an output value: only bools and value-free shape notes. Each run's
  reason is masked with that run's values and secrets.
- Terminal output masks account ids to their last digits; amounts are shown.

## Tests

`tests/unit/test_cli.py` (argument parsing, wiring with monkeypatched browser and agent, rails
modes, unsavable runs, eval in one session, exit codes); `tests/unit/test_eval.py`.

## Limits and cuts

- Eval needs every input up front; it cannot answer a form.
- A capability that sends data stops at the gates on every eval run.

## Decisions

R17 (statuses), R18 (drift log) in [replay-decisions.md](../decisions/replay-decisions.md).
