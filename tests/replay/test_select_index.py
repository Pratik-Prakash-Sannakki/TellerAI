"""do_select passes the step's recorded index to the page; OCR that merges a label into the box
still confirms. (The SELECT_AT_JS node tests moved to tests/unit/browser/test_dropdown.py.)"""
import asyncio

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
