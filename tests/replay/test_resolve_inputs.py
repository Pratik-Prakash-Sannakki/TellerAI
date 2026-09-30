"""One form before step 1 asks every input, in step order. Only a dropdown mismatch prompts mid-run."""
import asyncio

import pytest


def _type(ns, name):
    return ns["SCHEMA"]["Type"](value=f"{{{{{name}}}}}", target={"anchor": {"label": name, "offset": [60, 0]}})


def _select(ns, name):
    return ns["SCHEMA"]["Select"](option=f"{{{{{name}}}}}", target={"anchor": {"label": name, "offset": [60, 0]}})


def _click(ns, text):
    return ns["SCHEMA"]["Click"](target={"ocr_text": {"text": text}, "anchor": {"label": text, "offset": [0, 0]}})


def _cap(ns, inputs, steps):
    return ns["Capability"](name="t", description="t", base_url="https://parabank.parasoft.com/p",
                            viewport=(1280, 800), inputs=[{"name": n, "description": f"the {n}"} for n in inputs],
                            steps=steps, checkpoint="Done")


class FakeForm:
    def __init__(self, *answers) -> None:
        self.asked: list = []
        self.answers = list(answers)

    async def form(self, title, fields, values=None, options=None):
        self.asked.append((fields, values, options))
        return self.answers.pop(0) if self.answers else None


class FakePage:
    def __init__(self, options=()) -> None:
        self.options, self.picked = list(options), None

    async def evaluate(self, js, args):
        if args[2] is None:
            return self.options
        self.picked = next((o for o in self.options if o == args[2]), None)
        return [100, 50, self.picked] if self.picked else False

    async def wait_for_timeout(self, ms) -> None:
        return None


@pytest.fixture
def env(ns, mk_look):
    lk = mk_look([("amount", (0, 0, 40, 10)), ("from_account", (0, 20, 40, 30)), ("Pay", (0, 40, 40, 50)),
                  ("Done", (0, 60, 40, 70))])

    async def take_look():
        ns["STATE"].look = lk
        return lk

    order: list = []

    def action(name):
        async def act(step, point, cap):
            order.append(name)
            return True
        return act

    ns.update(take_look=take_look, page=FakePage(), CONTROL=FakeForm())
    ns["ACTIONS"] = {**ns["ACTIONS"], "type": action("type"), "click": action("click")}
    ns["STATE"].look = lk
    return ns, order


def _walk(ns, cap):
    return asyncio.run(ns["walk"](cap, None, []))


def _ask(ns, cap):
    return asyncio.run(ns["ask_inputs"](cap))


def test_all_inputs_asked_once_before_step_1_in_step_order(env) -> None:
    ns, order = env
    ns["CONTROL"] = form = FakeForm(["5", "74838", "10"])
    cap = _cap(ns, ["amount", "from_account", "payee"],       # declared order differs from step order
               [_type(ns, "payee"), _select(ns, "from_account"), _type(ns, "amount")])
    assert _ask(ns, cap) == {"payee": "5", "from_account": "74838", "amount": "10"}
    assert len(form.asked) == 1
    fields, prefill, options = form.asked[0]
    assert [f[0].split(":")[0] for f in fields] == ["payee", "from_account", "amount"]
    assert fields[1][0] == "from_account: the from_account (must match an option on the page)"
    assert prefill is None and options is None                 # nothing pre-filled, no choice lists yet


def test_blank_field_stops_before_step_1_naming_it(env) -> None:
    ns, _ = env
    ns["CONTROL"] = FakeForm(["", "10"])
    with pytest.raises(ns["Stop"]) as e:
        _ask(ns, _cap(ns, ["payee", "amount"], [_type(ns, "payee"), _type(ns, "amount")]))
    assert e.value.status == "STUCK" and e.value.reason == "inputs not given: ['payee']"


def test_skipped_form_stops(env) -> None:
    ns, _ = env
    with pytest.raises(ns["Stop"]) as e:
        _ask(ns, _cap(ns, ["amount"], [_type(ns, "amount")]))
    assert e.value.reason == "inputs not given: ['amount']"


def test_no_form_when_nothing_is_declared(env) -> None:
    ns, _ = env
    assert _ask(ns, _cap(ns, [], [_click(ns, "Pay")])) == {} and ns["CONTROL"].asked == []


def test_nothing_prompts_mid_run_for_a_typed_input(env) -> None:
    ns, order = env
    ns["STATE"].values = {"amount": "10"}
    assert _walk(ns, _cap(ns, ["amount"], [_type(ns, "amount")])).status == "SUCCESS"
    assert ns["CONTROL"].asked == [] and order == ["type"]


def _run_select(ns, options, *answers):
    ns["page"], ns["CONTROL"] = FakePage(options), FakeForm(*answers)
    ns["read_field"] = lambda look, point: ns["page"].picked or ""      # the box shows the pick
    cap = _cap(ns, ["from_account"], [_select(ns, "from_account")])
    return asyncio.run(ns["do_select"](cap.steps[0], (100, 50), cap))


def test_dropdown_value_matching_a_live_option_gives_no_prompt(env) -> None:
    ns, _ = env
    ns["STATE"].values = {"from_account": "74838"}
    assert _run_select(ns, ["13344", "74838"]) is True
    assert ns["CONTROL"].asked == [] and ns["page"].picked == "74838"


def test_dropdown_mismatch_gives_one_prompt_with_the_live_options(env) -> None:
    ns, _ = env
    ns["STATE"].values = {"from_account": "7483"}
    assert _run_select(ns, ["13344", "74838"], ["74838"]) is True
    assert len(ns["CONTROL"].asked) == 1
    fields, prefill, options = ns["CONTROL"].asked[0]
    assert fields == [("from_account: the from_account", False)]
    assert prefill == [""] and options == [["", "13344", "74838"]]
    assert ns["page"].picked == "74838" and ns["STATE"].values["from_account"] == "74838"


def test_dropdown_mismatch_answer_must_be_a_live_option(env) -> None:
    ns, _ = env
    ns["STATE"].values = {"from_account": "7483"}
    with pytest.raises(ns["Stop"]):
        _run_select(ns, ["13344", "74838"], ["7483"])


def test_login_capability_starts_logged_out(ns) -> None:
    login = ns["SCHEMA"]["Type"](value="{{secret:username}}", target={"anchor": {"label": "U", "offset": [0, 0]}})
    assert ns["starts_with_login"](_cap(ns, [], [login]))
    assert not ns["starts_with_login"](_cap(ns, ["amount"], [_type(ns, "amount")]))


class ClearPage:
    def __init__(self) -> None:
        self.calls: list[str] = []
        self.context = self

    async def clear_cookies(self) -> None:
        self.calls.append("clear")

    async def goto(self, url) -> None:
        self.calls.append("goto")

    async def screenshot(self) -> bytes:
        return b""


def test_open_start_clears_cookies_before_goto_for_a_login(ns) -> None:
    login = ns["SCHEMA"]["Type"](value="{{secret:username}}", target={"anchor": {"label": "U", "offset": [0, 0]}})
    ns["page"] = ClearPage()
    ns["decode"] = lambda png: __import__("numpy").zeros((800, 1280, 3))

    async def take_look():
        return None

    ns["take_look"] = take_look
    asyncio.run(ns["open_start"](_cap(ns, [], [login])))
    assert ns["page"].calls == ["clear", "goto"]
