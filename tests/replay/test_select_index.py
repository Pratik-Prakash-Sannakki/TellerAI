"""Two dropdowns side by side: the step's recorded index picks its own <select>, whatever the point;
an old step without one picks by point. OCR that merges a label into the box still confirms."""
import asyncio
import json
import shutil
import subprocess

import pytest

FROM, TO = (540, 345, 718, 365), (805, 345, 940, 365)         # two selects on one row


def _js(ns, x: int, y: int, want, index):
    """Run replay's real SELECT_AT_JS in node against a fake page holding FROM and TO."""
    if not shutil.which("node"):
        pytest.skip("node not installed")
    page = f"""
    const mk = (r, opts) => ({{options: opts.map(t => ({{text: t}})), selectedIndex: 0,
      getBoundingClientRect: () => ({{left: r[0], top: r[1], right: r[2], bottom: r[3],
                                       width: r[2] - r[0], height: r[3] - r[1]}}),
      dispatchEvent: () => true, closest() {{ return this; }}}});
    const sel = [mk({list(FROM)}, ["13344", "15120"]), mk({list(TO)}, ["13344", "15120"])];
    const document = {{querySelectorAll: () => sel,
      elementFromPoint: (x, y) => sel.find(s => {{ const r = s.getBoundingClientRect();
        return r.left <= x && x <= r.right && r.top <= y && y <= r.bottom; }}) ?? {{closest: () => null}}}};
    const out = ({ns["SELECT_AT_JS"]})({json.dumps([x, y, want, index])});
    console.log(JSON.stringify({{out, picked: sel.map(s => s.selectedIndex)}}));
    """
    return json.loads(subprocess.run(["node", "-e", page], capture_output=True, text=True, check=True).stdout)


def test_an_index_picks_its_own_dropdown_from_a_point_nearer_the_other(ns) -> None:
    got = _js(ns, 760, 355, "15120", 1)          # between the two, nearer FROM's right edge
    assert got["picked"] == [0, 1] and got["out"][2] == "15120"


def test_without_an_index_the_point_decides(ns) -> None:
    assert _js(ns, 600, 355, "15120", None)["picked"] == [1, 0]
    assert _js(ns, 900, 355, None, None)["out"] == ["13344", "15120"]


class _Page:
    def __init__(self) -> None:
        self.args: list = []

    async def evaluate(self, js, args):
        self.args.append(args)
        return ["13344", "15120"] if args[2] is None else [872, 355, args[2]]

    async def wait_for_timeout(self, ms) -> None:
        return None


def _select(ns, mk_look, index, seen: str):
    ns["page"] = page = _Page()
    lk = mk_look([(seen, (720, 345, 900, 365))])

    async def take_look():
        return lk
    ns.update(take_look=take_look, read_field=lambda look, point: seen)
    ns["STATE"].values = {"to_account": "15120"}
    step = ns["SCHEMA"]["Select"](option="{{to_account}}", index=index,
                                  target={"template": "crops/t/s6.png"})
    return asyncio.run(ns["do_select"](step, (780, 355), None)), page.args


def test_the_step_index_reaches_the_page_and_merged_ocr_confirms_it(ns, mk_look) -> None:
    ok, args = _select(ns, mk_look, 1, "to account #|15120")
    assert ok is True and [a[3] for a in args] == [1, 1]


def test_an_old_step_without_an_index_selects_by_point(ns, mk_look) -> None:
    ok, args = _select(ns, mk_look, None, "15120")
    assert ok is True and [a[3] for a in args] == [None, None]


def test_the_confirm_is_not_fooled_by_a_longer_number(ns, mk_look) -> None:
    assert _select(ns, mk_look, 1, "to account #|151200")[0] is False
