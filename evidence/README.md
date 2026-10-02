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

| Capability | Discovery run (saved it) | Replay |
|---|---|---|
| `pay_bill` | `discovery/20261002T075648Z-log_in_pay_bill` | `replay/20260930T033412Z-pay_bill` (older artifact: step-5 check failed, human took over; STUCK at step 6) |
| `pay_bill_to_payee` | `discovery/20261002T050328Z-log_in_pay_bill_to_with_account_from_my_` | - |
| `request_loan` | `discovery/20261002T073727Z-log_in_request_for_a_loan` | - |
| `get_transfer_account_options` | `discovery/20261002T045655Z-log_in_pay_bill_give_me_options_from_and` | - |
| `get_all_account_balances` | `discovery/20260930T055623Z-log_in_get_account_balance_for_all_accou` | `replay/20260930T091210Z-get_all_account_balances` (SUCCESS) |
| `transfer_money` | - (older notebook run) | `replay/20260930T223218Z-transfer_money` (SUCCESS) |
| `transfer_funds` (retired) | `discovery/20260930T035011Z-log_in_transfer_funds` | `replay/20260930T041553Z-transfer_funds` (FAILED: site error page at step 3) |

Take-overs during discovery (failed login, re-register, hand back) are recorded in
`summary.json`, e.g. `discovery/20261002T074508Z-log_in_pay_bill`.
Replay runs predate the `cua` package (no `run.json`).

Discovery runs on the package are done; replay and eval runs on the new artifacts are pending.

Runs whose files held an unmasked account number or a typed name were deleted, not committed.
