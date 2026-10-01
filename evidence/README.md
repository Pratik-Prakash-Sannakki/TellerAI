# evidence/

Run folders written by the pure-visual notebooks: `save_evidence(...)` in
`notebooks/discovery/discovery.py` and `replay(...)` in `notebooks/replay/replay.py`. One folder
per run, named `<UTC timestamp>-<goal or capability name>`. Everything is masked before it is
written: typed or human-given values become `***` in text, and black boxes in PNGs.

## discovery/<UTC>-<goal>/

| File | What |
|---|---|
| `goal.txt` | the goal the agent was given |
| `answer.txt` | the agent's final answer, when it gave one |
| `events.jsonl` | every tool call and its result, one per line |
| `transcript.jsonl` | the model conversation (messages and tool calls) |
| `summary.json` | status, event count, take-overs, which capability was saved |
| `step_<n>.png` | the screenshot the agent saw at step n |
| `take_over_*.png` | the screen before/after a human take-over, if any |
| `final.png` | the last screen |
| `capability.yaml` + `crops/` | the saved capability and its template crops, if one was saved |

## replay/<UTC>-<capability>/

| File | What |
|---|---|
| `summary.json` | status (`SUCCESS`, `STUCK`, ...), reason, outputs, human steps, failing step, cleanup |
| `drift.jsonl` | which rung found each step |
| `failure.json` | the failing step, its action, expected vs observed |
| `take_over_*.png` | the screen before/after a human take-over, if any |
| `final.png` | the last screen |
| `capability.yaml` | the exact capability that was replayed |

Runs whose files held an unmasked account number or a typed name were deleted, not committed.
