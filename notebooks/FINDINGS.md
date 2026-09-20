# Phase 1 findings

Notebook: `agent.ipynb` (agent + Playwright on ParaBank). Setup and screenshot proofs: `01_browser_and_observe.ipynb`.

## Verdict

**GO on deep agents (D4).** A deep agent drove a real browser through our own Playwright tools, logged in without seeing credentials, and completed tasks. Approval for risky clicks ended up living in our own tool, not in the framework (see "Design changes").

## What was tested

| Test | Result | Notes |
|---|---|---|
| Happy path: log in, open the first account, read the balance | Pass | Agent used `type_secret`; values never appeared in the trace |
| Impossible goal (account 99999999) | Pass | Ended with `finish("STUCK: ...")`, invented nothing, 4 steps |
| Runaway guard | Pass | Hit `recursion_limit` (40) once and stopped instead of looping |
| Pause before a risky click, browser survives | Pass | Approve moved to `transfer.htm`; Reject left it on overview |
| Reject ends the attempt | Pass, after fix | First attempt: agent retried 3 times. Fixed with a firmer message, then in code (`DECLINED` set) |
| Human takes over the live browser and hands back | Pass | Red bar + "Done" button; agent got the pages visited and the page text |
| Fill From/To dropdowns and amount | Pass | Needed a new `select_option` tool and dropdown options in the element list |
| Bill payment: full goal, human approves at the button | Pass (final version) | Two earlier runs paid without approval (see bugs) |

**Built but only lightly tested**
- `ask_human` (agent-initiated handoff) and "values must come from the goal" (`GIVEN` check): built and used in the bill-payment run with a full goal. Not yet tested with a vague goal in the final notebook.
- `web_search` (built-in Anthropic search): wired in, not exercised.
- Cost and step counts: **not measured**.

## Bugs found and fixes

| # | Problem | Cause | Fix |
|---|---|---|---|
| 1 | Login looped | Model sent two tool calls at once; both ran on one page at the same time | `one_at_a_time` lock on every tool |
| 2 | Agent saw a stale page after Log In | Screenshot taken before navigation finished | Wait 600 ms + `load` state after each click |
| 3 | Agent retried a rejected step 3 times | Only the prompt said "don't" | Firmer reject text, and code-level `DECLINED` set |
| 4 | Agent invented payee, address, amount | Goal was "pay a bill"; nothing forced it to ask | `GIVEN` check: a typed or chosen value must appear in the goal, otherwise the tool hands the browser to a human |
| 5 | **Bill payment sent with no approval (twice)** | Pause depended on an element flag, the framework's `when` rule, and cell order. Send Payment slipped through. The approval bar also said "Transfer" (hard-coded), so the human approved something else | Approval moved into the `click` tool: every button except a short safe list asks a human first. Bar shows the real button and the values entered |
| 6 | Human "Take over" opened the Playwright Inspector (code) | `page.pause()` is a developer tool | Own red bar with a "Done, hand back" button |
| 7 | ParaBank test-user credentials were in `.env.example` (committed locally, never pushed) | Copied in during notebook work | Local history rewritten before anything was pushed; `.env.example` blank; `.gitignore` hardened; `nbstripout` added |

## Design changes (also recorded in DECISIONS.md, section K)

- **D4:** deep agents kept for discovery. Their pause rule (`interrupt_on`) is **not** used for safety anymore.
- **D14:** own "Done" button replaced `page.pause()`. Same idea: pause, human acts in the same live session, hand back.
- **D20:** risky = every button except a safe list (deny by default), not a name list. Approval enforced inside our tool.
- **D32 (login):** worked. Agent-driven login costs a few steps and can be flaky; verify-by-replay (D23) must catch a bad login recording.

## Carry forward

| Phase | Item |
|---|---|
| 2 | Artifact needs `{{secret:name}}` references and typed inputs; schema must express "this step needs human approval" |
| 3 | Balances are not clickable, so they get no number. Needs a `mark_text` tool so the recorder can build an extract locator (D12) |
| 3/5 | `finish` cannot report a business outcome ("account not found" showed up as `STUCK:`). Add an outcome field (D10) |
| 3 | Grounding check is a crude substring match (`5` matches inside `$50`). Replace with declared typed inputs (D29) |
| 6 | The model writes real values into its own summary (account and balance seen in `finish`). Redaction must cover summaries and logs, not only screenshots |
| 6 | `web_search` sends query text to a third party and is outside the allowlist. Needs a rule |
| 7 | Code-level stuck triggers (same action 3x, repeated failures, step limit → offer takeover). Today only the model, and the recursion limit, catch it |
| 7 | Human actions are captured only as pages visited and final page text, not click by click |
| all | Deep agents ships 8 built-in tools we don't use (`ls`, `write_file`, `task`, ...). None were called in the runs seen, but they can't be removed |
