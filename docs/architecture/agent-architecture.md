# Agent architecture (discovery)

How Teller's discovery agent works end to end, what runs where, and where the guardrails sit.
Replay is plain code with no LLM (last section). Per-component detail:
[discovery agent](../components/discovery-agent.md), [recorder](../components/recorder.md),
[guardrails](../components/guardrails.md), [safety](../components/safety.md),
[LLM and routing](../components/llm-and-routing.md). Index: [docs/README.md](../README.md).

## 1. The whole run, in order

```
 cua discover "<goal>"                                   (src/cua/cli.py)
        |
        v
 [1] INPUT RAIL  -- NeMo Guardrails (cua.safety.rails + nemo, configs/rails/*.co)
        |   local embeddings (FastEmbed MiniLM) match the goal to intents, per sentence
        |   clear match to off-topic / jailbreak / steering / sensitive -> REFUSED
        |   unsure band -> one Haiku call decides;  any error -> REFUSED (fails closed)
        |   REFUSED = no browser, no main agent run; REFUSED evidence folder, exit 1
        v  allowed
 [2] Session  -- Playwright (cua.browser): site tab + separate control window
        |   host lock: only parabank.parasoft.com; every request passes the guard
        v
 [3] DEEP AGENT  -- deepagents + LangGraph, Sonnet (cua.llm.make_chat_model)
        |   loop, one tool per step:
        |      Look (screenshot + RapidOCR + numbered boxes)  ->  LLM picks a tool  ->  tool acts
        |   only OUR 13 tools are offered (OnlyOurTools); LatestScreenshotOnly keeps context small
        |   optional TypeSafe router (off unless TYPESAFE_API_KEY): trims tools, picks Haiku/Sonnet
        |   traced in LangSmith (env vars only)
        v
 [4] SEND GUARD  -- cua.safety.send_guard (not an LLM; wraps every non-GET request)
        |   first: a value the human never gave opens a prefilled form (mismatch check)
        |   Gate 1: human Approve / Edit in the control window
        |   Gate 2: human confirms sending
        v
 [5] OUTPUT RAIL -- cua.safety.rails.check_output
        |   masks card numbers, SSN, unmasked account ids; withholds credential-like answers
        |   applied before the answer is printed and before evidence/artifact writes
        v
 [6] RECORDER -> Capability (artifacts/<name>.yaml) + masked evidence folder
        |   leak-checked before any file is written
        v
   replay (no LLM) runs the saved capability
```

## 2. What is used where

| Stage | Tech | Code | LLM? |
|---|---|---|---|
| Input rail | NeMo Guardrails (Colang, local embeddings) | `safety/rails.py`, `safety/nemo.py`, `configs/rails/` | Haiku only in the unsure band |
| Browser, host lock | Playwright | `browser/` | no |
| Perception | screenshot + RapidOCR, numbered boxes | `vision/screenshot.py`, `vision/ocr.py` | no |
| Agent loop | deepagents (LangGraph), Sonnet | `discovery/agent/`, `llm.py` | yes |
| Tools (act/read/nav/human) | our `@tool`s | `discovery/tools/` | no (called by the LLM) |
| Send gates | Approve/Edit window, mismatch check | `safety/send_guard.py`, `handoff/` | no |
| Output rail | regex + Luhn + id mask | `safety/rails.py` (`check_output`) | no |
| Capability save | recorder; one call to the agent's model (Sonnet) for name and descriptions | `discovery/recorder/` | one call |
| Tracing | LangSmith | env vars | n/a |

## 3. The guardrail layers

```
 goal --> [Input rail: NeMo] --> agent --> [Tool layer: our tools only, site lock,
                                            allowed_actions, one-at-a-time]
      --> [Send guard: mismatch check, Gate 1 approve/edit, Gate 2 confirm send]
      --> [Output rail: mask / withhold] --> evidence + artifact (masked, leak-checked)
```

- Input rail (NeMo): refuses before any work. Embeddings decide clear goals with no LLM
  (two thresholds in `configs/rails/thresholds.yml`: upper 0.65 refuses a clear attack or auto-allows
  a close banking example, lower 0.45 caps the refused score; anything unsure goes to Haiku; a
  tripwire word list and clause scoring stop tacked-on attacks); fails closed. Modes
  `rails: off | on | required` in the site config; `on` without the extra prints "guardrails OFF".
- Tool layer: the model can only call our tools; click refuses deny-listed words; secrets are
  typed by name (`type_secret`), values never reach the model.
- Send guard: nothing is submitted without a human Approve; values are checked against what was given.
- Output rail: masks or withholds before anything is shown or stored.
- Evidence: logs and files hold rail names and scores only, never goal values or matched text.
- The original safety (host lock, SendGuard, masking) stays the primary control; NeMo is an extra
  layer at the two edges (goal in, answer out).

## 4. Replay (no LLM)

`cua replay <capability.yaml>`: a plain-code engine runs the saved steps (rungs: table cell,
OCR text, anchor, template) through the same send guard. No NeMo and no model call; there is no
free text to rail.
