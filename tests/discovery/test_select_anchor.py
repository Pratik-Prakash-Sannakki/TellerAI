"""A dropdown's point inside an OCR box that merged its label and value ('to account #|15120')
still gets that label as its anchor; each select step records which <select> it is (its index);
a select with no anchor is never saved."""
import ast
import asyncio
from pathlib import Path
from types import SimpleNamespace
from urllib.parse import urlparse

import pytest
import yaml

from tests.discovery.test_label_values import TRANSFER, _look_ns
from tests.discovery.test_save_artifact import NS, SENT, START, _ev, _meta

SRC = Path(__file__).parents[2] / "notebooks/discovery/discovery.py"


def _where_at(values: set[str], point: tuple[int, int], *texts) -> dict:
    ns = _look_ns(values)
    els = tuple(ns["Element"](i, t, ns["Box"](*b)) for i, (t, b) in enumerate(texts, 1))
    return ns["where"](ns["Look"](b"", b"", els, "u"), point)


def test_a_point_inside_a_merged_label_and_value_box_anchors_on_the_cleaned_label() -> None:
    merged = ("to account #|15120", (720, 345, 840, 365))          # centre (780, 355)
    got = _where_at({"15120"}, (800, 355), ("From account #", (484, 345, 586, 365)), merged)
    assert got["label"] == "to account #" and got["anchor"]["text"] == "to account #"
    assert got["offset"] == [20, 0]
    assert "15120" not in str(got)


def test_a_plain_word_under_the_point_is_still_never_the_anchor() -> None:
    """A box's own text with nothing cut from it (a value, a button) stays off the anchor."""
    got = _where_at(set(), (800, 355), ("Checking", (760, 345, 840, 365)))
    assert "anchor" not in got


def _select_ev(**extra) -> dict:
    return {**_ev("select_option", {"ref": 5, "x": None, "y": None}, "Selected.", label="to account #",
                  url=TRANSFER), **extra}


def test_the_select_step_keeps_the_dropdowns_index(tmp_path: Path) -> None:
    log = [START, _select_ev(index=1), SENT]
    cap = NS["build_capability"](log, _meta(name="t"))
    assert cap.steps[0].index == 1
    path = NS["save_artifact"](cap, NS["crops_for"](log, cap), tmp_path)
    assert yaml.safe_load(path.read_text())["steps"][0]["index"] == 1


def test_an_old_select_without_an_index_still_loads() -> None:
    step = NS["Select"](option="{{a}}", target={"anchor": {"label": "a", "offset": [0, 0]}})
    assert step.index is None


def test_a_select_with_no_anchor_is_refused_not_saved() -> None:
    ev = _select_ev(index=1)
    for k in ("anchor", "label", "offset"):
        ev.pop(k)
    ev["args"] = {"hint": "option"}
    with pytest.raises(ValueError, match="no label to find it by") as err:
        NS["build_capability"]([START, ev, SENT], _meta(name="t"))
    assert "Re-run discovery" in str(err.value)


def test_a_sent_dropdown_is_logged_with_its_index_on_the_page() -> None:
    tree = ast.parse(SRC.read_text())
    keep = [n for n in tree.body if getattr(n, "name", None) in
            {"log_sent_dropdowns", "is_select", "field_area", "same_spot"}
            or (isinstance(n, ast.Assign) and getattr(n.targets[0], "id", "") == "FIELD_GAP")]
    stash = [{"value": "1", "text": "1", "options": ["1"], "at": [600, 355], "box": [586, 345, 718, 365]},
             {"value": "15120", "text": "15120", "options": ["15120"], "at": [872, 355],
              "box": [805, 345, 940, 365]}]
    events: list[dict] = []
    ns = {"HANDOFF": SimpleNamespace(dropdowns=stash, log=[]), "urlparse": urlparse,
          "where": lambda look, p: {"label": "to account #"}, "cut_crop": lambda *a: b"", "Look": object,
          "log": lambda tool, args, result, point=None, crop=None, **extra: events.append(extra)}
    exec(compile(ast.Module(keep, []), str(SRC), "exec"), ns)
    asyncio.run(ns["log_sent_dropdowns"](SimpleNamespace(scale=1.0, url=TRANSFER), {"to": "15120"}))
    assert [e["index"] for e in events] == [1]
