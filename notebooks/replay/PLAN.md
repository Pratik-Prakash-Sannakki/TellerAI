# Replay notebook plan

Build `replay.py` (jupytext) -> `replay.ipynb`. Spec: `DECISIONS.md` R1-R18, `replay_architecture.md`.

## Sections
Setup -> Config & secrets -> Browser -> Vision (reused) -> Safety & handoff (reused) -> Artifact
schema -> Load & inputs -> Locate (rungs) -> Steps -> Replay engine -> Run.

## Tasks
- [x] Reuse discovery cells verbatim (`HANDOFF` renamed `STATE`, a small `ReplayState`).
- [x] Schema v2 per R13 (Pydantic, frozen, `extra="forbid"`).
- [x] Load: YAML -> model, crops relative to the YAML, refuse viewport/dsf mismatch, unknown
      `{{input}}` / `{{secret:x}}` names, non-allowed host.
- [x] Inputs: missing/invalid -> discovery's control-tab form, masked when sensitive.
- [x] Rungs 1 (OCR text + ordinal), 2 (anchor + offset), 3 (`matchTemplate`, threshold + margin);
      all miss -> scroll once -> help panel.
- [x] Steps: act via `act` / `into_box` / `choose_option`; verify by OCR; retry once; never retry a
      send or a secret.
- [x] Sends: discovery's `guard_send` (mismatch vs inputs, Gate 1, Gate 2). Login click exempt.
- [x] Result: status + outputs + drift; working values wiped in `finally`.
- [x] Tests in `tests/replay/` (ast-loaded, fake page).

## Decisions made here (review)
- P1. **Reconciled with discovery's schema (DONE).** Replay no longer has its own models: its
  `## Artifact schema` cell runs the models cell of discovery's `## Save artifact` via `ast`
  (single source). `tests/replay/test_round_trip.py` builds a capability with discovery's
  `build_capability`, saves it with `save_artifact`, and loads it with replay's `load_capability`
  unchanged. What changed in replay to match:
  - Steps are discovery's tagged union (`Navigate/Click/Type/Select/Scroll/Extract`); dispatch is
    still by `action`. Only some steps have `target`/`value`, so replay reads them with `getattr`.
  - `select` reads `option` (not `value`). Type values are `{{input}}` or `{{secret:name}}`.
  - `checkpoint` is plain text (was a `Condition`); `shows()` now takes text.
  - Rung 2 offset = action point minus label box centre: already what replay did.
  - Crops `crops/<name>/s<i>.png`, relative to the YAML: already what replay did.
  - Dropped: per-step `expect`, `outcome_rules`, input `pattern`/`required`. Discovery does not
    write them. So `BUSINESS_OUTCOME` is never returned now, and a missing input is just empty.
  - Old replay tests moved onto discovery's models.
- P1b. **Schema asks for discovery (not changed here, per rule):** `outcome_rules` (to return
  `BUSINESS_OUTCOME`, R17) and an optional input `pattern` (to catch a bad value before step 1).
  Neither blocks replay today.
- P1c. **R14 leftovers do not block replay.** Per-step `expect`: replay checks every step itself
  by OCR (typed text read back near the box, dots/changed spot for a secret, dropdown value via
  `choose_option`, screen changed after a click), then the final `checkpoint`. Raw log on disk:
  replay reads only the YAML + crops, never the log.
- P2. **Help panel has no free-text answer.** Discovery's help panel lets the human answer in
  words for the agent. Replay has no LLM to read words, so its panel is Take over / Stop only.
  Take over = the human does the step, clicks Done, replay carries on.
- P3. **Fuzzy text match is exact for anything with a digit.** "13344" vs "13345" is 80% similar;
  a fuzzy match would pick the wrong account. Words stay fuzzy (`CFG.fuzzy`).
- P4. **Replay opens `base_url` before step 1** (as discovery opens `START_URL`), then checks the
  screenshot size.
- P5. **Scroll retry = once** (`CFG.scroll_retries = 1`), per the build request; R2 said "e.g. 5".
- P6. **Mismatch check compares against inputs only** (R6). A constant typed from the artifact
  that is a number will open the fill-in form, prefilled. Safe, but one extra click per send.

- P7. **Pay Bill fixes (2026-09-29).** A: typed/select checks read the whole drawn field box
  (`field_box`/`read_field`), not a crop at its centre. B: `typed_ok` matches the value against the
  field's OCR words, fuzzy for words, exact for anything with a digit (`$`/`,` ignored). D: a click
  is judged by `settled_change` (poll until the screen changed and holds still, `CFG.check_s`);
  a send is still never retried. The Run cell points at `pay_bill.yaml`; `.py` is the source.
- P8. **Transfer Funds fixes (2026-09-29).** 1: a capability that types a secret before its first
  click starts logged out (`clear_cookies` then `base_url`). 2: a dropdown picks the exact live
  option and checks the option the page reports as selected (no substring pick). 3: `replay(path)`
  takes no inputs. ONE control-tab form before step 1 (after the logout reset) asks every
  `{{input}}` in step order, with its description; nothing pre-filled, nothing from discovery. A
  blank or skipped field = STUCK before step 1. Dropdown inputs are text there ("must match an
  option on the page"); only if the value is not a live option does that step show one prompt
  with the live options, blank first. Supersedes P1's "a missing input is just empty".
- P9. **Held-send screenshots (2026-09-29).** A held form POST (a navigation) blocks
  `page.screenshot()`. `guard_send` never screenshots: the gates show the last look. Take-over
  evidence uses `snap()` (`CFG.snap_s` = 3s, None on timeout or Playwright error). Hand-back waits
  on `SEND_GATE`, so a send the human made is gated and released before the end snap.
- P10. **Held-send `evaluate` (2026-09-29).** `page.evaluate` blocks on a held request like
  `screenshot`. `guard_send` never touches the page: `do_click` stashes the dropdowns first
  (`stash_dropdowns`, `CFG.page_s`), and the gates read only that stash. A human's own send during a
  take-over skips the mismatch check and dropdown lookups: Gate 1 (Edit = plain text) -> Gate 2.
  Hand-back waits on `SEND_GATE` at most `CFG.gate_s`, then STUCK.
- P11. **Evidence (2026-09-29, spec 3.5/6.3).** `save_evidence(result, cap_path)` writes
  `evidence/replay/<UTC>-<name>/`: `summary.json`, `drift.jsonl` (+ `take_over_<n>_before/after.png`),
  `failure.json` (not SUCCESS: step, action, expected, observed), `final.png` (a `snap()` on failure),
  `capability.yaml`. `Stop` carries expected/observed; a checkpoint miss sends the first 200 chars of
  the final OCR text. Masking copies discovery's `redactor`/`mask_png`; the mask set (the human's
  values) is kept in `LAST_RUN` in memory only, captured before `replay`'s `finally` wipes STATE.
- P12. **Taxonomy, caller inputs, hand-back reminder (2026-09-29).** R17 outcome rules after
  every step (see DECISIONS R17). `replay(path, inputs=None)`: given values by exact name (any
  case); an unknown key = STUCK before the site opens; the rest goes to the one upfront form.
  Take-over: an idle site tab (no navigation, no screen change for `CFG.idle_s` = 20s) brings up
  "Done? Hand back to agent" (Done / Not yet); Not yet re-arms. Screenshots only, no page injection.
- P13. **Hand-back button (2026-09-29, R19).** A browser-extension toolbar button
  (`extensions/handback/`, no content scripts, no host permissions) hands back during a take-over;
  the site page is never touched. It replaced a separate small window; the site-page bar before
  that was removed on the user's rule (no target DOM).
- P14. **Merged anchor labels (2026-09-29).** Discovery now saves cleaned labels ("to account #").
  Rung 2 matches with `same_label`: strip `[ ] |`, then OCR text that starts with the label counts
  ("to account #16785"), else the usual fuzzy match. Rung 1 (a value to click) stays exact for digits.
- P15. **Cleanup steps (2026-09-29, R20).** `finish()` = `walk()` then `run_cleanup()` in `finally`.
- P16. **Live Transfer/Pay Bill bugs (2026-09-30).** (1) `settled_change` never judges a click
  while its send sits at the gates; the check window restarts at release, and "changed" = pixels
  OR new OCR text. (2) A typed value of <= 2 chars (`CFG.short_value`) that OCR misses passes on the
  field's pixels. (3) A take-over that reaches the checkpoint skips the remaining main steps
  (`rung: skipped`). (4) The evidence redactor masks whole numbers only (no more `rung***`).
- P17. **Partial outputs (2026-09-30).** Every result carries what was read; `outputs_line` labels
  partial ones. A read-only run with every output read accepts a post-logout checkpoint (R17).
- P18. **Strict extract types (2026-09-30).** Replay's own `TYPES`/`is_type` (no longer
  `cua.recorder.value_matches_type`): currency needs a `$` or exactly 2 decimals. A mismatch tries
  the next rung once (`next_rung`), then STUCK, expected = the type, observed = masked text.
- P19. **Navigate + HTTP errors (2026-09-30).** `site_url` joins like a browser (an absolute path
  is from the site root; it used to be forced under base_url, doubling `/parabank`). `error_page`
  runs before the outcome rules (R17).
- P20. **Extract `pattern` + shapes (2026-09-30).** `value_of`: with a saved `pattern`, the first
  match inside the box, else the whole box; either way it must be the type. `SHAPES` copied
  verbatim from discovery (phone/currency/date/integer/email/id); a test keeps them identical.
- P21. **Duplicate text + same-URL clicks (2026-09-30).** Rung 1 with the same text twice picks the
  copy nearest the anchor's point (`CFG.near_px` = 60), drift `rung1+anchor` when that overrides the
  ordinal; none near = rung 2. A click followed by a main-frame response (`STATE.navs`, even the same
  URL) counts as a change.

## Open questions for the user
- Q-A. Should constants from the artifact count as "given" in the mismatch check (P6)?
- Q-B. After a take-over, replay trusts the human (no `expect` to re-check). OK?
- Q-C. Should discovery add `outcome_rules` + input `pattern` to the schema (P1b)?
