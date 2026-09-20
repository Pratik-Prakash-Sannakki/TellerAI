# Phase 3: the recorder (agent run -> draft capability)

**Goal:** turn a real agent run into a valid draft capability (YAML) that the Phase 2 schema accepts.
The model discovers. The recorder turns what it did into a capability. Thin but real, for two flows:
`get_account_balance` (safe) and `transfer_funds` (risky).

**Spec:** DECISIONS.md D2, D5, D8, D9, D10, D12, D20, D23, D29, D32, D33, D34, D37-D40;
FINDINGS.md "Carry forward" (phase 3 rows). Schema: `notebooks/02_artifact_schema.py`.

## Two parts

| Part | Needs | What it does |
|---|---|---|
| A. CAPTURE | browser + API key | While the agent works, every tool call is logged as an **event**: tool, ok/failed, page before and after, and a rich **descriptor** of the element it touched. |
| B. COMPILE | nothing (pure Python) | `events + declared inputs -> Capability`. Tested offline with hand-made events. |

The two parts meet at one plain data shape (the event), so B can be tested without A.

## Files

| File | Action |
|---|---|
| `docs/superpowers/plans/2026-09-20-phase3-recorder.md` | this plan |
| `notebooks/03_recorder.py` (+ paired `.ipynb`) | new. Pure cells first (schema loader, compile, tests), browser cells after |
| `DECISIONS.md` | append section M (D41+) |
| `CLAUDE.md` | add the Phase 3 notebook line |
| `artifacts/*.yaml` | written by the user's run (drafts) |

Not touched: `agent.ipynb`, other notebooks. Setup/scanner/tool cells are **copied** from `agent.ipynb`
(temporary duplication, Phase 9 consolidates).

## Event shape (the contract between A and B)

```
{i, tool, status, before:{url, heading}, after:{url, heading},
 el: descriptor | None, value, approved, save_as, value_type, label,
 outcome, proof, final}
```
- `tool`: observe, page_text, click, type_text, type_secret, select_option, extract_value, open_path, request_value, ask_human, finish.
- `status`: ok, failed, denied, blocked, declined, handoff.
- `url` is relative to the app base, no `;jsessionid`. `value` for `type_secret` is the secret NAME.
- Descriptor: role, name, name_source, tag, type, label, text, submit, options, container{role,name}, nth.
  `data-cua-ref` is never in it.

## Compile pipeline (part B)

1. **Clean (D23):** drop observe/page_text/finish, failed/denied/blocked/declined calls, repeated identical
   consecutive actions, dead-end detours (leave a page, return to it, nothing typed/extracted in between),
   trailing safe clicks after the last meaningful action. Any human handoff -> refuse (a step would be missing).
2. **Login split (D32):** kept events up to and including the first click after the last `type_secret`
   become `login_<app>`. The task capability has no secret steps.
3. **Steps:** click, type, select, extract, navigate. A navigate is added for the start page, and where the URL
   changed without a click.
4. **Locators (D8):** ranked `role+name` (only if the name is a real accessible name), `label`, `text`,
   `structure` inside a container. Never a page-wide index.
5. **Parameterise (D29):** declared literals -> `{{name}}` in typed values, options, paths, locator strings.
6. **Leftover check:** any declared literal still anywhere except `inputs` -> refuse. Typed values that match no
   input are reported as constants.
7. **Risk (D33/D38):** click approved by a human -> `risky`, `amount_input` = the declared currency/number input.
8. **Checkpoint (D9):** `url_contains` = last path segment, `text_present` = heading on the last kept step's page.
9. **Outcome rules (D10):** from a bad-input probe run (`finish(outcome, proof_text)`), plus the relogin rule.
10. **Save:** `Capability.model_validate`, secret-value guard, then `to_yaml` to `artifacts/<name>.yaml`.

## Browser additions (part A)

- New `OBSERVE_JS` that also returns the descriptor fields. Model-facing text is unchanged.
- Every tool logs an event. `click` records `approved` when the human approved.
- `extract_value(label, save_as, value_type, description)` uses `read_labeled_value(page, label)` (reusable by Phase 4).
- `open_path(path)`: navigate inside the allowed site (needed to reach a bad-input page). Query values must come from the goal.
- `finish(summary, values, outcome, proof_text)`: proof must be text really on the page.
- Kept from Phase 1: approval inside click, value grounding, `request_value`, START_PAGES guard, lock, DECLINED set.
  Grounding now prefers declared input values and uses word-boundary matching for the rest.
- Dropped in this copy: `web_search` (sends text off-site, outside the allowlist).

## Tests

| Where | What |
|---|---|
| Offline (I run, `uv run python`) | good balance flow; dead-end click; login split; leftover-literal refusal; risky click (+ safe control); bad-input outcome; handoff refusal; secret-value guard; sensitive-field refusal; helpers (`norm_url`, literal boundaries); YAML round trip |
| Browser (the user runs) | run 1: balance flow -> `login_parabank.yaml` + `get_account_balance.yaml`. Run 2: bad account -> outcome rule, merged. Run 3 (optional): transfer with approval -> risky capability |

## Tasks

- [ ] T1 plan (this file)
- [ ] T2 pure cells: schema loader, helpers, clean/split/steps/compile/save
- [ ] T3 offline tests, run with `uv run python`
- [ ] T4 browser cells: scanner, tools, capture, agent, run cells
- [ ] T5 how-to block at the top, `.ipynb` generated, DECISIONS D41+, CLAUDE.md
- [ ] Stop. The user runs the browser parts and sends results.
