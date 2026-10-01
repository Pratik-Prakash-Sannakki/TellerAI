# evidence/

One folder per run, written by the package:

- `cua discover` always writes `evidence/discovery/<UTC>-<goal>/` (`cua.discovery.evidence.save_evidence`), success or not.
- `cua replay ... --evidence` writes `evidence/replay/<UTC>-<capability>/` (`cua.replay.evidence.save_evidence`).
- `<UTC>` is `YYYYMMDDTHHMMSSZ`. The goal part of the name is masked too.

Everything is masked before it is written:

- Typed, selected and human-given values, and secrets, become `***` in text.
- In PNGs, any OCR text matching one of them gets a black box.
- Discovery refuses to copy an artifact that holds a run value.

## discovery/<UTC>-<goal>/

| File | What |
|---|---|
| `goal.txt` | the goal the agent was given |
| `answer.txt` | the agent's final answer, if any |
| `events.jsonl` | every tool call, its result, and its masked `why` (the model's reason, max 200 chars), one per line |
| `transcript.jsonl` | per model turn: its text and the tool names it called (no screenshots) |
| `step_<n>.png` | the crop logged with event n, if it had one |
| `take_over_<n>_before.png` / `_after.png` | the screen at the start and end of a take-over |
| `final.png` | the last screen |
| `capability.yaml` + `crops/<name>/` | the saved capability and its template crops, if one was saved |
| `summary.json` | status (`done`, `STUCK`, `DECLINED`, `no answer`), event count, take-overs, saved capability path |
| `run.json` | prompt version, model name, config hash, git sha. Never a value |

## replay/<UTC>-<capability>/

| File | What |
|---|---|
| `summary.json` | status (`SUCCESS`, `STUCK`, ...), reason, summary, outputs (names only, values `***`), human, failing step, cleanup |
| `drift.jsonl` | per step: which rung found it, the point, the attempt, whether the check passed |
| `failure.json` | only on a failure: step, action, expected vs observed |
| `take_over_<n>_before.png` / `_after.png` | the screen at the start and end of a take-over |
| `final.png` | the last screen |
| `capability.yaml` | the exact capability that was replayed |
| `run.json` | `prompt_version` and `model` null (replay has no LLM), config hash, git sha |

## Kept runs

These runs predate the package (written by the old notebooks). None of them has a `run.json`.

replay/:

- `20260930T223218Z-transfer_money`: SUCCESS. Files: `capability.yaml`, `drift.jsonl`, `summary.json`.
- `20260930T091210Z-get_all_account_balances`: SUCCESS, with a multi-account table output. Same files.
- `20260930T041553Z-transfer_funds`: FAILED. The site showed an error page on the step-3 click. Files: `capability.yaml`, `drift.jsonl`, `failure.json`, `final.png`, `summary.json`.
- `20260930T033412Z-pay_bill`: STUCK, then a human took over. The step-5 check failed; the human took over at step 6. Files: as above, plus `take_over_0_before.png`, `take_over_0_after.png`.

discovery/:

- `20260930T035011Z-log_in_transfer_funds`: done, saved `transfer_funds.yaml`. Files: `answer.txt`, `capability.yaml`, `events.jsonl`, `goal.txt`, `summary.json`, `transcript.jsonl`, `crops/`.
- `20260930T055623Z-log_in_get_account_balance_for_all_accou`: done, saved `get_all_account_balances.yaml`. Same files.

A fresh package run is pending the user:

1. `cua discover` (writes a discovery folder and an artifact).
2. `cua replay <artifact> --evidence` for a success.
3. `cua replay <artifact> --evidence` for an error case (e.g. a declined send or a mistyped input).

Runs whose files held an unmasked account number or a typed name were deleted, not committed.
