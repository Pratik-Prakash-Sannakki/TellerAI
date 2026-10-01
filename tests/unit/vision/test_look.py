"""Box, Element, Look: the small frozen types vision reads/writes, plus decode/encode."""

from __future__ import annotations

from dataclasses import FrozenInstanceError

import cv2
import numpy as np
import pytest

from cua.vision.look import Box, Element, Look, decode, encode


def test_box_center_is_the_midpoint() -> None:
    assert Box(0, 0, 10, 20).center == (5, 10)


def test_box_contains_a_point_inside_its_edges() -> None:
    b = Box(0, 0, 10, 10)
    assert b.contains(5, 5)
    assert b.contains(0, 0)
    assert not b.contains(11, 5)


def test_box_overlaps_only_when_the_rectangles_intersect() -> None:
    assert Box(0, 0, 10, 10).overlaps(Box(5, 5, 15, 15))
    assert not Box(0, 0, 10, 10).overlaps(Box(10, 10, 20, 20))


def test_look_get_finds_an_element_by_ref_or_none() -> None:
    el = Element(1, "Log In", Box(0, 0, 10, 10))
    look = Look(b"", b"", (el,), "https://example.test/")
    assert look.get(1) is el
    assert look.get(2) is None


def test_look_text_joins_every_elements_text() -> None:
    els = (Element(1, "Log", Box(0, 0, 1, 1)), Element(2, "In", Box(0, 0, 1, 1)))
    assert Look(b"", b"", els, "u").text == "Log In"


def test_decode_encode_round_trips_a_png() -> None:
    img = np.zeros((4, 4, 3), np.uint8)
    img[:] = (1, 2, 3)
    png = cv2.imencode(".png", img)[1].tobytes()
    out = decode(png)
    assert out.shape == (4, 4, 3)
    assert tuple(out[0, 0]) == (1, 2, 3)
    assert decode(encode(out)).tolist() == out.tolist()


def test_box_and_element_are_frozen() -> None:
    b = Box(0, 0, 1, 1)
    with pytest.raises(FrozenInstanceError):
        b.x1 = 2  # type: ignore[misc]
    el = Element(1, "x", b)
    with pytest.raises(FrozenInstanceError):
        el.ref = 2  # type: ignore[misc]
