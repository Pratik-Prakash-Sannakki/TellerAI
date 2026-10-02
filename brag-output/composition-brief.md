# Hyperframes Composition Brief: cua

## Objective
Create a short launch-style brag video for cua (pure-visual computer-use agent + no-LLM replay).

## Output
- Composition directory: `brag-output/composition/`
- Rendered video: `brag-output/brag.mp4`
- Format: landscape — 1920x1080, 30fps
- Duration: 22s

## Source Material
- Project root: repo root
- Primary files read: README.md, REPORT.md, src/cua/vision/ocr.py (`draw_numbered`), artifacts/pay_bill_to_payee.yaml,
  artifacts/crops/pay_bill_to_payee/*.png, evidence/discovery/*/events.jsonl, evidence/replay/*/drift.jsonl
- Product name: cua
- Tagline / strongest claim: "Replay needs no LLM key at all." / "No DOM reads, no accessibility tree."
- Key UI moment: real ParaBank screenshots with the project's own OCR numbered boxes (boxes computed by
  `cua.vision.ocr` and stored in `work/ocr_boxes.json`)
- Copy that must appear verbatim:
  - `type_secret('password')`, `click [32] 'SEND PAYMENT'`, `send → approved by human` (event log)
  - `cua replay artifacts/transfer_money.yaml --evidence`, drift lines, `SUCCESS`
  - "772 passed", "mypy --strict src: 0 errors"

## Creative Direction
- Tone preset: default — "terminal meets a 2005 bank website"
- Angle: learn once with a model, replay with plain code
- Hook: numbered boxes ripple onto ParaBank; "No DOM. Just pixels."
- Outro: "Learn it once. Replay it with plain code."
- Avoid: generic SaaS language, abstract filler, invented numbers

## Visual Identity
- Background #0b1220, text #e8edf5, overlay red #ff0000, ParaBank navy #1f4e8c, orange #f0a020
- Display: Inter (local woff2); Code: JetBrains Mono (local woff2)

## Storyboard
See `brag-plan.md`. Scenes: Hook 3.0 · Reveal 3.5 · Discover 5.0 · Capability 3.5 · Replay 4.0 · Outro 3.0.

## Audio
- Music: assets/music/happy-beats-business-moves-vol-1-by-ende-dot-app.mp3, 0.34, fade out over last 1.2s
- Cue source: bundled preset; beat-lock SUCCESS at 17.02, wordmark at 20.02
- Audio-reactive: subtle stage glow from bass bands (extract-audio-data.py)
- SFX: soft ticks, clicks, card slides, one bell — chosen after animation exists; low HF-risk picks

## Hyperframes Instructions
Domain-skill conventions (core/animation/creative/keyframes/cli) read from the upstream repo. Run
`hyperframes check` before render. Local only.
