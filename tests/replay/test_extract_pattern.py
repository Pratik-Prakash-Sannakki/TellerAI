"""An extract's optional `pattern` cuts the value out of a longer box; phone/email/date/id shapes."""
import ast
import asyncio
from pathlib import Path

import pytest

SENTENCE = "www.parasoft.com or call 888-305-0041"
ROWS = [("Contact", (10, 10, 80, 30)), (SENTENCE, (100, 10, 400, 30))]


def _cap(ns, kind, pattern=None, label="Contact"):
    step = ns["SCHEMA"]["Extract"](save_as="v", target={"anchor": {"label": label, "offset": [200, 0]}},
                                   **({"pattern": pattern} if pattern else {}))
    return ns["Capability"](name="t", description="t", base_url="https://parabank.parasoft.com/p",
                            viewport=(1280, 800), steps=[step], checkpoint="x",
                            outputs=[{"name": "v", "type": kind, "description": "v"}])


def _extract(ns, mk_look, cap, rows=ROWS):
    ns["STATE"].look = mk_look(rows)
    hit = ns["locate"](ns["STATE"].look, cap.steps[0].target, {}, None)
    ns["STATE"].rung = hit[1]
    return asyncio.run(ns["do_extract"](cap.steps[0], hit[0], cap))


def test_a_pattern_extracts_the_phone_from_the_sentence(ns, mk_look) -> None:
    assert _extract(ns, mk_look, _cap(ns, "phone", ns["TYPES"]["phone"])) is True
    assert ns["STATE"].outputs["v"] == "888-305-0041"


def test_no_match_fails_the_step(ns, mk_look) -> None:
    with pytest.raises(ns["Stop"]) as e:
        _extract(ns, mk_look, _cap(ns, "email", ns["TYPES"]["email"]))
    assert e.value.status == "STUCK" and e.value.expected == "email" and "v" not in ns["STATE"].outputs


def test_a_no_match_tries_the_next_rung_first(ns, mk_look) -> None:
    rows = [("Contact", (10, 10, 80, 30)), ("no phone here", (100, 10, 400, 30)),
            ("Call", (10, 60, 60, 80)), (SENTENCE, (100, 60, 400, 80))]
    step = ns["SCHEMA"]["Extract"](save_as="v", pattern=ns["TYPES"]["phone"],
                                   target={"table_cell": {"row_key": "Contact", "column": "Contact"},
                                           "anchor": {"label": "Call", "offset": [200, 0]}})
    cap = ns["Capability"](name="t", description="t", base_url="https://parabank.parasoft.com/p",
                           viewport=(1280, 800), steps=[step], checkpoint="x",
                           outputs=[{"name": "v", "type": "phone", "description": "v"}])
    ns["STATE"].look = mk_look(rows)
    ns["STATE"].rung = "table"
    assert asyncio.run(ns["do_extract"](step, (250, 20), cap)) is True
    assert ns["STATE"].outputs["v"] == "888-305-0041" and ns["STATE"].rung == "rung2"


@pytest.mark.parametrize(("kind", "good", "bad"), [
    ("phone", ["888-305-0041", "(888) 305-0041", "+888.305.0041"], ["305-0041", "13566", "phone"]),
    ("email", ["a.b+c@x-y.co.uk"], ["a@b", "@x.com", "x.com"]),
    ("date", ["09/30/2026", "2026-09-30", "30.9.26"], ["2026", "Sept 30"]),
    ("id", ["13566", "AB123-X", "x9_y"], ["abc", "-1", ""]),
    ("currency", ["$0.00", "1,234.56"], ["13566"]),
])
def test_new_types_accept_and_reject(ns, kind, good, bad) -> None:
    assert all(ns["is_type"](g, kind) for g in good), kind
    assert not any(ns["is_type"](b, kind) for b in bad), kind


def test_shapes_are_identical_to_discoverys(ns) -> None:
    src = (Path(__file__).parents[2] / "notebooks/discovery/discovery.py").read_text()
    node = next(n for n in ast.parse(src).body if isinstance(n, ast.Assign) and
                getattr(n.targets[0], "id", "") == "SHAPES")
    shapes = ast.literal_eval(node.value)
    assert {k: ns["TYPES"][k] for k in shapes} == shapes


def test_an_old_artifact_without_a_pattern_is_unchanged(ns, mk_look) -> None:
    rows = [("Balance", (10, 10, 80, 30)), ("$515.50", (230, 10, 290, 30))]
    cap = _cap(ns, "currency", label="Balance")
    assert cap.steps[0].pattern is None
    assert _extract(ns, mk_look, cap, rows) is True and ns["STATE"].outputs["v"] == "$515.50"
    with pytest.raises(ns["Stop"]):                          # the whole box must be the type, as before
        _extract(ns, mk_look, _cap(ns, "phone"))
