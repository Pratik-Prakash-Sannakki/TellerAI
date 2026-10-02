# Brag Plan: Teller (v2), AI banking agent (repo: cua)

v2 (2026-10-02): user asked to drop the OCR boxes, brand it "Teller", show the agent typing and clicking, both gates, the artifact, and a replay of the same task. 36s (user OK with longer). Storyboard below is v1; v2 timings live in work/build.py + work/template.html.

## What is this app?
An AI agent learns a banking task on ParaBank purely from screenshots (OCR + mouse/keyboard, no DOM),
writes it down as a YAML "capability" + template crops, and a plain-code engine replays it with no LLM.

## The angle
"Learn once with a model. Replay forever with plain code." The video shows the agent's literal view of the
world — red numbered OCR boxes slapped over a 2005-era bank site — then the receipt it leaves behind (a YAML
recipe), then that recipe running with zero model calls. The joke writes itself: a very modern agent,
politely filling in a very old bank form, and never once looking at your password.

## Hook (first 2-3 seconds)
The real ParaBank login page. Red numbered boxes ([1] PARA BANK … [39]) snap onto every word in a fast
ripple — this is exactly what the model sees (output of `cua.vision.ocr.draw_numbered`). Line slams in:
"No DOM. Just pixels."

## Key moments (the middle)
- The Bill Payment form under the numbered overlay; a cursor visits fields; a tool-call log ticks in
  (`type_secret('password')`, `click [32] 'SEND PAYMENT'`). Caption: "Sees the secret's name. Never the value."
- Send gate: a "send → approved by human" chip lands before the click. Caption: "Payments wait for a human."
- The capability gets written: real `pay_bill_to_payee.yaml` lines + the real template crops fly into a stack.
- Replay terminal: `cua replay artifacts/transfer_money.yaml --evidence` streams real drift lines
  (`step 0 type rung2 ✓` …) → SUCCESS. Caption: "Replay needs no LLM key at all."

## Outro / punchline
"Learn it once. Replay it with plain code." → `cua discover` · `cua replay` wordmark,
footer "772 tests passed · mypy --strict: 0 errors".

## User flow worth showing
discover (agent looks at ParaBank, fills Bill Pay, human approves the send) → capability YAML + crops
saved → replay runs the YAML with no model → SUCCESS.

## Tone
- Preset: default
- Creative direction: "terminal meets a 2005 bank website" — crisp dev-tool launch, a bit cheeky
- Interpretation: punchy cuts, clean dark stage, the real ParaBank screenshots as the bright "product"
  inserts; humor only from the contrast between the agent and the site.

## Format: landscape — 1920x1080
## Duration: 22s

## Visual identity (from the project)
- Background: #0b1220 (dark stage; project has no UI of its own)
- Overlay red: #ff0000 (`draw_numbered` draws BGR (0,0,255) 1px boxes + Hershey numbers)
- ParaBank navy: #1f4e8c, ParaBank orange (LOG IN / SEND PAYMENT buttons): #f0a020
- Text: #e8edf5
- Display font: Inter; Body/code: JetBrains Mono
- Strongest visual element: the numbered-box overlay on real ParaBank screenshots

## Privacy / masking
All screenshots come from `evidence/` (already masked: values are black boxes). Visible numbers (e.g.
"15231" in a dropdown) are ParaBank demo data. No usernames, passwords, keys, or emails appear.

## Share copy (draft)
My agent learned to pay a bill on ParaBank from screenshots alone, then wrote it down as YAML so it can do it
again with zero LLM calls.

## Audio direction
- Role: warm bed + light, motion-matched UI accents
- Music: happy-beats-business-moves-vol-1 (120.19 BPM), volume ~0.34, fade in 0.3s, fade out last 1.2s
- Music cue guidance: preset `assets/music/cues/happy-beats-business-moves-vol-1-by-ende-dot-app.music-cues.json`.
  Strong cues: 17.02s (SUCCESS slam), 20.02s (outro wordmark). Beat grid 0.5s from 3.02s; crops land on
  12.02 / 12.52 / 13.01 / 13.51 (images, every beat OK); tool-log lines on every other beat (≥1s apart).
- Audio-reactive treatment: subtle; music bass makes the dark-stage glow behind the screenshot frame breathe.
- SFX posture: moderate; soft ticks under the box ripple, clicks on simulated clicks, card-slides for crops,
  bell on SUCCESS.
- Restraint rule: no SFX on every OCR box; nothing louder than the music bed.

## Storyboard

### Scene 1 — Hook: what the model sees — 3.0s (0.0–3.0)
Real ParaBank login screenshot in a browser frame. 39 red numbered boxes ripple on (0.3–1.4s).
"No DOM. Just pixels." slams in at ~1.0s, holds to 3.0.
Sequential/interaction: yes — boxes appear one by one in reading order.
Audio intent: curiosity → snap. Audio-coupled idea: soft tick cluster under the ripple.
Transition mood: hard → Scene 2

### Scene 2 — Reveal: cua — 3.5s (3.0–6.5)
Wordmark "cua" + "Learns a banking task from screenshots." Below: the README pipeline as three chips:
`discover` → `artifacts/<name>.yaml + crops` → `replay (no LLM)`; chips arrive 4.02 / 4.53 / 5.03, hold.
Audio: drop/whoosh on title; small clicks per chip. Transition: clean wipe → Scene 3

### Scene 3 — Discover: Bill Pay — 5.0s (6.5–11.5)
Bill Payment Service screenshot with numbered overlay. Right side: tool-call log card, lines at
7.0 / 8.0 / 9.0 / 10.0: `type_secret('username')`, `type_secret('password')`, `send → approved by human`,
`click [32] 'SEND PAYMENT'`. Cursor moves to SEND PAYMENT and clicks at 10.0.
Captions: "Sees the secret's name. Never the value." (7.0–9.0) → "Payments wait for a human." (9.2–11.5).
Audio: key ticks, click at 10.0. Transition: slide → Scene 4

### Scene 4 — The capability — 3.5s (11.5–15.0)
YAML card (real lines from `artifacts/pay_bill_to_payee.yaml`) + 6 real template crops stacking in on beats.
Caption: "Then it writes the recipe down." Label `artifacts/pay_bill_to_payee.yaml`.
Audio: card slides on each crop. Transition: hard → Scene 5

### Scene 5 — Replay — 4.0s (15.0–19.0)
Terminal: `$ cua replay artifacts/transfer_money.yaml --evidence`; real drift lines stream 15.4–16.8 (texture);
"SUCCESS" slams at 17.02 (beat-locked). Caption: "Replay needs no LLM key at all." (17.1–19.0)
Audio: soft ticks, bell on SUCCESS. Transition: dip → Scene 6

### Scene 6 — Outro — 3.0s (19.0–22.0)
"Learn it once. Replay it with plain code." → wordmark `cua discover · cua replay` lands at 20.02,
footer "772 tests passed · mypy --strict: 0 errors". Music fades out.

**Music mood for this video:** upbeat
**Audio summary:** a bright business-beat bed with tiny UI ticks that turn into a bell when replay succeeds.
