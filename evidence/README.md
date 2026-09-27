# `evidence/`

This folder is the take-home's own required deliverable (`DECISIONS.md` line 35, Section 6):

> `/evidence/` with a saved artifact and logs from a discovery run and a replay run, ideally
> including one replay that hits an error.

and Phase 8 of the roadmap (`docs/superpowers/plans/2026-09-19-roadmap-and-phase1.md`, row 8):
`transfer_funds` end to end + all five error demos saved here.

**As of this commit, `evidence/` is empty except this file and two placeholder folders.** No real
discovery or replay run has been saved yet. That is deliberate: producing real evidence means
opening a real browser against the real, live ParaBank site, and that is explicitly reserved for
the project owner's own supervised session (`CLAUDE.md`: "sub-agent writes the notebook, the user
runs it"). This commit only builds the harness that captures evidence when a human runs it. The
numbered checklist at the bottom is exactly what still needs to be run, by hand, to fill this
folder in.

## Why it looks like this

Two capture helpers (`notebooks/evidence_capture.py`, added this phase, pure Python, no browser)
turn an already-completed run into one self-contained folder. Nothing here is guessed or
reconstructed after the fact -- each folder is written straight from the real objects a run
already produces: `03_recorder.py` CAPTURE's own `events` list and `compile_run`'s own output, or
`05_replay_live.py`'s own `Capability`/inputs/`ReplayResult`. See `DECISIONS.md` D92 for the full
design writeup, and the docstrings in `notebooks/evidence_capture.py` for exact behavior.

**No secret ever appears in any file in here, only names** (D32). This is enforced structurally
(a captured `type_secret` event's `value` field is already the secret's NAME, never its value; a
replay's `inputs` dict never contains a secret at all -- secrets are resolved separately) and,
belt-and-suspenders, by an explicit guard in both capture helpers that refuses to write anything
at all if a known secret value is ever found in what's about to be written. Both are proven by
`uv run python notebooks/evidence_capture.py`'s own offline fixtures (see that file, Sections 5-6).

## Layout

```
evidence/
  README.md                              -- this file
  discovery/
    <run-name>/                          -- one folder per real discovery run, name is yours (e.g. a date)
      goal.txt                           -- the exact goal text given to the agent
      events.json                        -- the raw captured event list (03_recorder.py CAPTURE)
      capability.yaml                    -- the compiled task capability (compile_run(...)["task"])
      login_capability.yaml              -- only written when a login capability was also compiled
      compile_report.json                -- compile_run's own report (dropped events, constants, warnings)
      transcript.log                     -- the agent's own step-by-step printed output during discovery
  replay/
    <capability-name>-<case>/            -- one folder per real replay run
      capability.yaml                    -- copy of the artifacts/*.yaml capability that was replayed
      inputs.json                        -- the inputs used (never a secret value -- see above)
      result.json                        -- the ReplayResult, serialized
      transcript.log                     -- the full printed log from the replay run
```

`<case>` for `replay/` is `success` for a clean run, or `error-<name>` for one of the five error
demos below (`error-account-not-found`, `error-slow-page`, `error-session-expired`,
`error-element-missing`, `error-transfer-over-limit`).

### What a real folder will contain (proven against fixtures, not yet against real runs)

`notebooks/evidence_capture.py`'s own offline checks build exactly this layout against
hand-made fixtures (shaped like `03_recorder.py`'s and `04_replay_engine.py`'s own fixtures) and
write it to a throwaway temp directory -- never into this folder, so a test run never plants fake
data next to real evidence. Example of what came out of that run (paths under
`/tmp/evidence_capture_test_*/`, not committed anywhere):

```
discovery/20260926-fixture-balance/
  goal.txt              "Log in and read the balance of account 13344.\n"
  events.json           [{"i": 0, "tool": "observe", ...}, ..., {"i": 2, "tool": "type_secret",
                          "value": "password", ...}, ...]   <- "password" is the NAME, never a value
  capability.yaml        (the real get_account_balance.yaml example, byte-identical after a round trip)
  compile_report.json    {"dropped": [[0, "observe", "not an action"]], "constants": [], "warnings": []}
  transcript.log          six printed step lines, ending "AGENT SAID: Recorded. Stop now."

replay/transfer_funds-error-transfer-over-limit/
  capability.yaml         (the real transfer_funds.yaml)
  inputs.json             {"amount": "750.00"}
  result.json             {"run_id": "fixture-run", "capability": "transfer_funds",
                            "capability_version": 1, "status": "NEEDS_APPROVAL", "outputs": {},
                            "pending_step": 3,
                            "reason": "amount 750.0 is at or above the auto-approve limit 500.0"}
  transcript.log          the escalate + REPLAY RESULT lines
```

## The five error demos

Found stated explicitly in `DECISIONS.md` **D30** ("Error cases shown in `/evidence/`"), which
Phase 8 of the roadmap cites by number (D13, D24, D30) -- this is not a list proposed fresh here,
it is the plan already agreed and recorded before this phase started:

| # | Case | Capability + setup | Expected `ReplayResult.status` |
|---|---|---|---|
| 1 | **Account not found** | `artifacts/examples/get_account_balance.yaml`, `{"account_id": "00000"}` (or any id ParaBank has no account for) | `BUSINESS_OUTCOME`, `outcome="ACCOUNT_NOT_FOUND"` -- the artifact's own declared rule |
| 2 | **Slow page** | Any safe capability (e.g. `artifacts/get_account_balance.yaml`); inject an artificial delay on the page it loads (see snippet below) | `SUCCESS` if the delay is under `PlaywrightReplaySurface`'s own ~5s resolve poll budget (D88); `FAILED` (a `ResolutionError`-driven hard failure) if the delay exceeds it. Note (see caveat below): there is no separate "recovered" status distinct from `SUCCESS` |
| 3 | **Session expired** | `artifacts/transfer_funds.yaml` or `artifacts/pay_bill.yaml` (both declare a `relogin` outcome rule); clear the session cookie right after navigating in, before the next step | `FAILED`, but the transcript shows a `step N: recoverable condition matched (action=relogin): ...` line first -- see caveat below |
| 4 | **Element missing** | `artifacts/transfer_funds.yaml` or `artifacts/pay_bill.yaml`; remove/hide the final submit button before the replay reaches it (see snippet below) | `FAILED`, `failure.step_action="click"`, `failure.observed` naming that neither locator resolved |
| 5 | **Transfer over limit** | `artifacts/transfer_funds.yaml`, `{"amount": "750.00"}` (>= the $500 `auto_approve_limit` default) | `NEEDS_APPROVAL`, `pending_step` at the risky click, `reason` naming the amount and limit -- **reject it** (do not approve) so the money never actually moves |

**Two honest caveats, not glossed over:**

- **Case 2 (slow page):** `04_replay_engine.py`'s own step-level `TransientFailure`-retry loop
  (D26) is only exercised by the offline `FakeSurface` tests today -- the real, live
  `PlaywrightReplaySurface.resolve()` (D88) has its own internal, silent 5-second poll/retry
  instead, and never raises `TransientFailure`. So this demo is real and reproducible, but what it
  actually shows is that bounded live-poll working (or timing out into a hard failure past its
  budget), not the `TransientFailure` code path itself. Worth demonstrating either way -- just
  don't expect a `"transient failure"` string in the transcript.
- **Case 3 (session expired):** `04_replay_engine.py` itself documents (see the comment at its
  `recoverable` branch, both sync and async) that actually re-running the login capability and
  continuing is unbuilt -- today a recoverable match is only logged, then the run falls through to
  the *next* step of the *same* capability, which will then almost certainly hard-fail against
  what is now the login page. That is genuinely useful evidence: it proves detection works, and it
  documents a real, known gap (relogin-and-continue is explicit Phase 9 scope) rather than
  pretending the run silently self-heals.

**Snippets for cases 2 and 4** (paste into your own live `05_replay_live.ipynb` session, in a new
cell, before calling `replay_live` -- these are illustrative starting points for you to run
yourself, never run by any agent):

```python
# Case 2: slow page -- delay every request to overview.htm by 3 seconds
async def _slow_route(route):
    await asyncio.sleep(3)
    await route.continue_()
await page.route("**/overview.htm", _slow_route)
```

```python
# Case 4: element missing -- remove the Transfer button before the capability ever reaches it.
# add_init_script runs on every subsequent navigation, so it applies once transfer.htm loads.
await page.add_init_script("""
document.addEventListener('DOMContentLoaded', () => {
  document.querySelectorAll('input[value="Transfer"], button:contains("Transfer")').forEach(el => el.remove());
});
""")
```

## How to save evidence from a real run

**Discovery side.** After a real discovery run (`notebooks/agent.ipynb` or `03_recorder.py`
CAPTURE) and a successful `compile_run(events, spec)`, in a new scratch cell in that same live
session:

```python
import sys, pathlib
sys.path.insert(0, str(pathlib.Path.cwd().parent / "notebooks"))  # if running from notebooks/
exec(open("evidence_capture.py").read().split("# %% [markdown]\n# ## Offline fixtures")[0])

result = compile_run(events, spec)   # you already ran this
save_discovery_evidence(
    "20260927-transfer-funds-discovery",      # pick a unique name, e.g. today's date + flow
    GOAL,                                      # the exact goal text you gave the agent
    events,
    result["task"],
    result["report"],
    transcript_lines,                          # your own collected print output, or a list of lines
    login=result["login"],                     # omit if this run had no separate login capability
)
```

**Replay side.** `05_replay_live.py`'s `replay_live()` now takes one new, optional
`evidence_dir` parameter (default `None` = today's unchanged behavior -- nothing is saved unless
you pass this). Pass it to auto-save:

```python
result = await replay_live(
    REPO / "artifacts" / "transfer_funds.yaml",
    {"amount": "750.00"},
    evidence_dir=REPO / "evidence" / "replay",
)
```

Every call with `evidence_dir` set writes one folder named `<capability-name>-<label>` (label
defaults from the result's own status; pass `label="error-transfer-over-limit"` etc. explicitly
for each of the five cases so the folder names read as the checklist above, not five capabilities
all colliding on the same default `-failed`/`-needs-approval` suffix). There is no `label=`
parameter on `replay_live` itself -- call `save_replay_evidence` directly instead if you want an
explicit label:

```python
from evidence_capture import save_replay_evidence   # if evidence_capture.py is on sys.path
save_replay_evidence(cap, inputs, result, transcript_lines,
                      evidence_dir=REPO / "evidence" / "replay",
                      label="error-transfer-over-limit")
```

## Exactly what's still needed (do these, in order, to fill this folder)

1. **One discovery run.** Run `agent.ipynb`/`03_recorder.py` CAPTURE for real (login + a real
   flow -- `transfer_funds` per Phase 8, or `get_account_balance`/`pay_bill`), `compile_run` it,
   then call `save_discovery_evidence(...)` as shown above. -> `evidence/discovery/<name>/`
2. **One clean replay success.** `replay_live(artifacts/transfer_funds.yaml, {"amount": "20.00"},
   evidence_dir=...)` (or any capability, with valid inputs, amount safely under $500) ->
   `evidence/replay/transfer_funds-success/`
3. **Error demo 1 -- account not found.** `replay_live(artifacts/examples/get_account_balance.yaml,
   {"account_id": "00000"}, evidence_dir=...)` -> expect `BUSINESS_OUTCOME`
4. **Error demo 2 -- slow page.** Inject the case-2 snippet above, then replay any safe
   capability -> expect `SUCCESS` (slow) or `FAILED` past the poll budget; save with
   `label="error-slow-page"`
5. **Error demo 3 -- session expired.** Clear the session cookie mid-flow (e.g.
   `await page.context.clear_cookies()` right after logging in, before replaying
   `transfer_funds`/`pay_bill`) -> expect `FAILED`, transcript shows the recoverable-match line;
   save with `label="error-session-expired"`
6. **Error demo 4 -- element missing.** Inject the case-4 snippet above, then replay
   `transfer_funds`/`pay_bill` -> expect `FAILED`, `failure.step_action="click"`; save with
   `label="error-element-missing"`
7. **Error demo 5 -- transfer over limit.** `replay_live(artifacts/transfer_funds.yaml,
   {"amount": "750.00"}, evidence_dir=...)`, **reject** the approval prompt -> expect
   `NEEDS_APPROVAL`; save with `label="error-transfer-over-limit"`

None of the above should be run by an agent. Every step opens a real browser against the real,
live ParaBank site.
