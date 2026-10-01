# cua.vision

Pixels -> text: screenshots, OCR, canvas math, crops, and the shared table reader. Pure
(no Playwright) except `screenshot.py`.

## Read order
1. `look.py` - `Box`, `Element`, `Look` (the shapes everything else here reads/writes),
   `decode`/`encode`.
2. `ocr.py` - the cached RapidOCR engine (`ocr_engine()`, built lazily -- importing this module
   never loads the model), `ocr()`, `number()` (fresh refs via `RefCounter`, owned by the run),
   `draw_numbered()`.
3. `canvas.py` - `to_canvas` (fit a screenshot to the canvas), `canvas_size` (the current look's
   own size, or the viewport before the first look), `to_page` (canvas point -> page point).
4. `crops.py` - `element_at`, `crop_box`, `cut_crop`, `read_near`, `spot_changed`, `screens_same`:
   look closely at one point.
5. `table.py` - the OCR table reader shared byte-for-byte by discovery and replay: find a header's
   columns (`table_columns`), read the rows under it (`read_rows`), tell a row from a footer
   (`like_rows`/`cell_shape`), and merge a scrolled re-read (`append_rows`).
6. `screenshot.py` - the only screenshot path: `take_look(page, cfg, refs, on_look=None)` (page
   calls on the loop, decode/canvas/OCR/numbering/drawing in one `asyncio.to_thread` call),
   `page_width`, and the two evidence snaps: `snap_png` (discovery) and `snap_look` (replay).

## What may NOT go here
- No Playwright import outside `screenshot.py`.
- No site value (host, URL, words): those live in `configs/<site>.yaml`.
- May import `cua.config` for `BrowserConfig` (the only cua import allowed here); may not import
  `cua.schema`, `cua.browser`, `cua.safety`, `cua.handoff`, `cua.discovery`, or `cua.replay`.
