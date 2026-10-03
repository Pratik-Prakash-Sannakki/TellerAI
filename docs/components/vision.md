# Vision

Pixels to text. One screenshot path, one OCR engine, one table reader, shared by discovery and
replay. Everything here is pure (no Playwright) except `screenshot.py`.

## Where it lives

- [`src/cua/vision/`](../../src/cua/vision/) (read order:
  [`vision/README.md`](../../src/cua/vision/README.md))
  - `look.py`: `Box`, `Element`, `Look`, `decode` / `encode`.
  - `ocr.py`: the cached RapidOCR engine, `ocr`, `number`, `RefCounter`, `draw_numbered`.
  - `canvas.py`: `to_canvas`, `canvas_size`, `to_page`.
  - `crops.py`: `element_at`, `crop_box`, `cut_crop`, `read_near`, `spot_changed`,
    `input_box`, `typed_into_box`, `screens_same`.
  - `table.py`: `table_columns`, `read_rows`, `like_rows`, `cell_shape`, `append_rows`.
  - `screenshot.py`: `take_look`, `page_width`, `snap_png` (discovery), `snap_look` (replay).

## How it works

- **`take_look(page, cfg, refs, on_look=None)`** is the only screenshot path:
  1. On the event loop: `page.screenshot()` and the page width.
  2. In one `asyncio.to_thread` call: decode, fit to the canvas, OCR, number, draw the boxes,
     encode.
  3. Returns a `Look`: the clean PNG, the numbered PNG (`drawn`), the elements, the URL and the
     scale.
- **OCR.** RapidOCR (PaddleOCR models on onnxruntime). The engine is built lazily and cached once
  per process, so importing `cua.vision` never loads the model. Boxes under `ocr_min_score` are
  dropped.
- **Numbering.** `number` sorts boxes into rows (top to bottom), then left to right, and gives each
  a fresh ref from the run's `RefCounter`. Refs are never reused within a run, so a number the
  model saw once always means the same element. `draw_numbered` draws the boxes and refs in red.
- **Canvas.** The page is fixed at 1280x800, scale 1 (Q10), so canvas and page points are normally
  1:1. `to_canvas` / `to_page` rescale only as a safety net.
- **Crops.** `cut_crop` cuts a tight crop around a point (rung 3 templates, evidence). `read_near`
  reads text near a point. `spot_changed` and `screens_same` compare looks (mean pixel difference
  below `same_screen_mad` = no change). `input_box` / `typed_into_box` find a drawn input box and
  tell whether ink appeared in it (a secret shows as dots).
- **Tables.** `table_columns` finds a header line's column spans from the asked column names;
  `read_rows` reads the rows under it (a gap over `TABLE_GAP` px ends the block); `like_rows`
  tells a row from a footer by cell shape; `append_rows` merges a scrolled re-read without
  duplicates. Discovery and replay use this same reader.

## Public API / key types

`Look`, `Element`, `Box`, `take_look`, `ocr`, `ocr_engine`, `number`, `RefCounter`,
`draw_numbered`, `to_canvas`, `canvas_size`, `to_page`, `element_at`, `cut_crop`, `read_near`,
`spot_changed`, `screens_same`, `table_columns`, `read_rows`, `append_rows`, `cell_shape`.

## Config knobs

`BrowserConfig`: `viewport`, `ocr_min_score` (0.5), `same_screen_mad` (1.0), `crop_pad`,
`point_crop` ([config](config.md)).

## Safety and guarantees

- Imports only `cua.config` from the package; no Playwright outside `screenshot.py`
  (`tests/unit/test_import_rules.py`).
- No site values.
- Values on screen are masked downstream, by the callers, before anything is stored
  ([safety](safety.md)).

## Tests

`tests/unit/vision/` (`test_look.py`, `test_ocr.py`, `test_canvas.py`, `test_crops.py`,
`test_spot_changed.py`, `test_table.py`, `test_screenshot.py`).

## Limits and cuts

- OCR noise is the main cost of pure visual: `1Main` for `Main`, `|` read as `I` or `l`. The
  matchers downstream are fuzzy for words and exact for digits (`ReplayConfig.fuzzy`).
- Whole-screen OCR for desktop apps is cut; desktop would swap only the screenshot and input
  layer (REPORT §4, §7).

## Decisions

Base (pure visual, RapidOCR), Q7 (no shape detector), Q8 / Q8b (tables), Q9 (OpenCV for pixel
jobs), Q10 (window size), Q14 (tight crops) in
[discovery-decisions.md](../decisions/discovery-decisions.md); R2-R5, R21 in
[replay-decisions.md](../decisions/replay-decisions.md).
