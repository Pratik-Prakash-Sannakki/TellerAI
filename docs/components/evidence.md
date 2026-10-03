# Evidence

One masked folder per run, so a reviewer can see what happened without seeing a value. The
folder layout and the kept runs are in [`evidence/README.md`](../../evidence/README.md); this doc
covers the code that writes them.

## Where it lives

- [`src/cua/evidence.py`](../../src/cua/evidence.py): shared helpers: `_clean` (mask a JSON
  tree), `_png` (write a masked PNG), `run_info`, `config_hash`, `git_sha`.
- [`src/cua/discovery/evidence.py`](../../src/cua/discovery/evidence.py): `save_evidence`,
  `save_refused`, `artifact_mask`, `transcript`.
- [`src/cua/replay/evidence.py`](../../src/cua/replay/evidence.py): `save_evidence`,
  `masked_outputs`.
- [`src/cua/eval.py`](../../src/cua/eval.py): `save_report` ([CLI and eval](cli-and-eval.md)).
- Output: `evidence/discovery/`, `evidence/replay/`, `evidence/eval/`, each
  `<UTC YYYYMMDDTHHMMSSZ>-<name>/`.

## How it works

- **Discovery** (`save_evidence(ctx, out_dir, capability, model)`), after every run, success or
  not:
  - builds one redactor (`safe_redactor`): secrets, account ids, every run value;
  - refuses (`ValueError`) if the saved capability YAML holds a run value;
  - writes `goal.txt`, `answer.txt` and `transcript.jsonl` (both through the output rail),
    `events.jsonl` (each event's crop as `step_<n>.png`), take-over shots, `final.png`, a copy of
    the capability and its crops, `summary.json`, `run.json`;
  - then `forget(run)`: drops reads, chat, answer, final screen and every crop from memory.
- **Refused goal** (`save_refused`): `goal.txt` (masked), `summary.json`
  (`{status: REFUSED, rail, score}`), `run.json`. No browser ran.
- **Replay** (`save_evidence(ctx, result, cap_path, out_dir)`), only with `--evidence`:
  `summary.json` (outputs as names and shape only, every value `***`), `drift.jsonl`,
  `failure.json` (on a failure), take-over shots, `final.png`, `capability.yaml`, `run.json`.
  Uses `ctx.last.values` (kept in memory after the run's wipe, for masking only).
- **`run.json`** is provenance, never a value: `prompt_version` (discovery) or null, model name or
  null, a sha256 of the frozen configs plus the site name, and the git sha.
- **PNGs** go through `mask_png`: OCR, then a black box over any run value or secret; account ids
  keep their last digits ([safety](safety.md)).
- The folder name is masked too (the goal or capability name).

## Public API / key types

`cua.discovery.evidence.save_evidence`, `save_refused`, `artifact_mask`;
`cua.replay.evidence.save_evidence`, `masked_outputs`; `cua.evidence.run_info`.

## Config knobs

None. `cua replay --evidence` and `cua eval --evidence` opt in; `cua discover` always writes.
Masking follows the site's `id_min_digits` / `id_visible_digits`.

## Safety and guarantees

- Typed, selected and human-given values and secrets become `***` in text and black boxes in PNGs.
- URLs drop `;jsessionid=` (`no_session`).
- `tests/integration/test_evidence_clean.py` scans the committed evidence and fails on a session
  token or a raw account id.
- `scripts/remask_evidence.py` re-masks stored evidence in place (used once for older runs).

## Tests

`tests/unit/test_shared_evidence.py`, `tests/unit/discovery/test_evidence.py`,
`tests/unit/discovery/test_evidence_refused.py`, `tests/unit/replay/test_replay_evidence.py`,
`tests/integration/test_evidence_clean.py`.

## Limits and cuts

- Masking is only as good as OCR.
- Older runs logged a session id and two raw account ids before masking covered them; they were
  re-masked, but the old values remain in git history (REPORT §6).
- LangSmith token and cost totals are not copied into `run.json` yet (REPORT §7).

## Decisions

R7 (nothing stored), R18 (drift log), R22 (account ids in replay evidence) in
[replay-decisions.md](../decisions/replay-decisions.md); Q14, Q23 in
[discovery-decisions.md](../decisions/discovery-decisions.md).
