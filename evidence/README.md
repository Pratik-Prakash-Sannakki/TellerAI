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
| `summary.json` | status (`done`, `STUCK`, `DECLINED`, `no answer`, `REFUSED`), `answer_withheld` (true if the output rail withheld the answer), event count, take-overs, saved capability path |
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

## discovery/ REFUSED runs (guardrails)

A goal the rails refuse writes a short folder and exits 1; the browser never opens.

| File | What |
|---|---|
| `goal.txt` | the refused goal (masked) |
| `summary.json` | `{status: REFUSED, rail, score}`; rail is `off_topic`, `jailbreak`, `steering`, `sensitive` or `empty_goal` |
| `run.json` | prompt version, model name, config hash, git sha |

Live examples: `discovery/20261003T06*` (six runs; list in [`docs/components/guardrails.md`](../docs/components/guardrails.md)).

## eval/<UTC>-<name>/

`cua eval <capability> --runs N` writes `report.json` (status counts, flakiness, whether outputs matched, rung histogram) and `run.json`. Kept: `eval/20261003T013804Z-get_all_account_balances` (3/3 SUCCESS, outputs stable), `eval/20261003T010917Z-get_all_account_balances` (3/3 SUCCESS, outputs differed once).

## Kept runs

Same table as the README "Evidence" section; folders are under `discovery/`, `replay/`, `eval/`.

| Capability | Discovery run (saved it) | Replay / eval |
|---|---|---|
| `get_all_account_balances` | `discovery/20261003T004411Z-log_in_and_get_the_balance_of_every_acco` | `replay/20261003T005702Z-...` SUCCESS; `replay/20261003T011355Z-...` SUCCESS; both eval runs above |
| `get_account_balance` | `discovery/20261003T110221Z-log_in_get_me_account_balance` | `replay/20261003T111830Z-get_account_balance` SUCCESS |
| `pay_bill_to_payee` | `discovery/20261002T050328Z-log_in_pay_bill_to_with_account_from_my_` | `replay/20261003T010220Z-pay_bill_to_payee` SUCCESS |
| `get_transfer_account_options` | `discovery/20261002T045655Z-log_in_pay_bill_give_me_options_from_and` | `replay/20261003T010531Z-get_transfer_account_options` SUCCESS |
| `request_loan` | `discovery/20261002T073727Z-log_in_request_for_a_loan` | `replay/20261003T010624Z-request_loan` BUSINESS_OUTCOME (loan denied) |
| `transfer_funds_between_accounts` | `discovery/20261003T015535Z-log_in_and_transfer_from_account_344_to_` | `replay/20261003T015748Z-transfer_funds_between_accounts` SUCCESS (a person picked the account) |
| `takeover_demo` (fault-injection, not discovered) | - | `replay/20261003T015212Z-takeover_demo` SUCCESS (human intervened at step 3) |
| `transfer_money` (RETIRED, replaced by `transfer_funds_between_accounts`) | - | `replay/20260930T223218Z-transfer_money` SUCCESS (pre-package) |

Older pre-package runs (no `run.json`) are also kept, e.g. `replay/20260930T033412Z-pay_bill`
(STUCK at step 6 after a take-over) and `replay/20260930T041553Z-transfer_funds` (FAILED, site
error page; retired). Take-overs during discovery are recorded in `summary.json`, e.g.
`discovery/20261002T074508Z-log_in_pay_bill`.

Runs whose files held an unmasked account number or a typed name were deleted, not committed.
