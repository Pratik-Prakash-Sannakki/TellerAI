"""Pixels -> text: screenshots, OCR, canvas math, crops, and the shared table reader.

Pure (no Playwright) except ``screenshot`` (not re-exported here, so importing
``cua.vision`` never imports Playwright). Imports only numpy/cv2, plus
``cua.config`` for ``BrowserConfig`` (allowed: see the import rule in ``src/cua/README.md``).
Importing this package must never load the OCR model -- ``ocr.ocr_engine()`` builds it lazily.
"""

from __future__ import annotations

from cua.vision.canvas import canvas_size, to_canvas, to_page
from cua.vision.crops import (
    crop_box,
    cut_crop,
    element_at,
    input_box,
    read_near,
    screens_same,
    spot_changed,
    typed_into_box,
)
from cua.vision.look import Box, Element, Look, decode, encode
from cua.vision.ocr import RefCounter, draw_numbered, number, ocr, ocr_engine
from cua.vision.table import (
    TABLE_GAP,
    append_rows,
    cell_shape,
    col_of,
    column_spans,
    like_rows,
    read_rows,
    row_of,
    same_line,
    table_columns,
    text_lines,
)

__all__ = [
    "TABLE_GAP",
    "Box",
    "Element",
    "Look",
    "RefCounter",
    "append_rows",
    "canvas_size",
    "cell_shape",
    "col_of",
    "column_spans",
    "crop_box",
    "cut_crop",
    "decode",
    "draw_numbered",
    "element_at",
    "encode",
    "like_rows",
    "number",
    "ocr",
    "ocr_engine",
    "read_near",
    "read_rows",
    "row_of",
    "same_line",
    "screens_same",
    "spot_changed",
    "typed_into_box",
    "input_box",
    "table_columns",
    "text_lines",
    "to_canvas",
    "to_page",
]
