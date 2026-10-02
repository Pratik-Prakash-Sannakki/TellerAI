# Safety: mask account ids (last 3 visible), no screen text to TypeSafe, profile wiped

Design approved by the user (mask only, never replace; `id_visible_digits: 3`; amounts shown).

- [x] T1 `safety/redact.py`: `IdMask(min_digits, visible)` (text mask + hidden spans), `url_path`,
      `mask_png(..., ids=)` partial blackout; `SiteProfile.id_min_digits/id_visible_digits` + yaml.
- [x] T2 Evidence (discovery + replay): redact = values after ids; PNG ids partial; folder slug
      from the masked goal; `forget_run` clears saved/messages/answer/final_shot/dropdowns/crops.
- [x] T3 Artifact: `save_artifact(..., mask=ArtifactMask)` masks text (names slugged) + crops and
      refuses a leak BEFORE writing; `describe(..., mask=)` sees masked goal + step lines.
- [x] T4 TypeSafe `step_state`: page + last tool name + status word only; routers print exc type.
- [x] T5 Session: profile dir remembered, removed in `close_session` (to_thread).
- [x] T6 guard.log / act from_url / observe URL: `url_path` (no `;jsessionid`, no query).
- [x] T7 extract_value echo + cli answer / outputs_line: ids masked.
- [x] T8 Data: real ids in src/tests masked in place; evidence text+PNGs and artifact crops
      re-masked; id folders renamed; rescan; graphify update.
- [x] T9 Docs (REPORT Safety, decisions.md, DECISIONS.md), full checks, local commit.

## Review
- Suite 891 passed; ruff, mypy --strict, black clean. Graph updated.
- PNG ids: glyph columns counted from the box's right end (width share showed 4 digits live);
  fails closed (whole box) when glyphs touch or there is no ink.
- Masked `ocr_text` ('***010') misses rung 1 in replay; anchor / template decide that step.
