"""Canvas-pixel <-> page-point mapping: any window size or pixel density maps to one grid.

Moved from the discovery notebook: ``to_canvas`` (discovery.py 255-261) unchanged; ``canvas``
(269-275) becomes :func:`canvas_size`, reading ``HANDOFF.look`` as an explicit ``look`` parameter
(``None`` -> the viewport, same as before); ``to_page`` (277-279) the same way. ``page_width``
stays in ``screenshot.py`` (step 5) -- it touches the page.
"""

from __future__ import annotations

from typing import cast

import cv2
import numpy as np
from numpy.typing import NDArray

from cua.vision.look import Look, decode


def to_canvas(
    img: NDArray[np.uint8], points_w: int, viewport: tuple[int, int]
) -> tuple[NDArray[np.uint8], float]:
    """Fit the screenshot inside the canvas. Returns it and canvas-pixel -> page-point scale."""
    cw, ch = viewport
    f = min(cw / img.shape[1], ch / img.shape[0])
    out = cv2.resize(
        img,
        (round(img.shape[1] * f), round(img.shape[0] * f)),
        interpolation=cv2.INTER_AREA if f < 1 else cv2.INTER_CUBIC,
    )
    # cv2.resize keeps the input dtype (uint8); its stub returns any-dtype MatLike.
    return cast("NDArray[np.uint8]", out), points_w / out.shape[1]


def canvas_size(look: Look | None, viewport: tuple[int, int]) -> tuple[int, int]:
    """The size of the image the model is looking at right now."""
    if look is None:
        return viewport
    h, w = decode(look.png).shape[:2]
    return w, h


def to_page(look: Look | None, point: tuple[int, int]) -> tuple[float, float]:
    s = look.scale if look else 1.0
    return point[0] * s, point[1] * s
