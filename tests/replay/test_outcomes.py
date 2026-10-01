"""R17 taxonomy after each step: a business answer stops, a lost session is re-logged once, an error page fails."""
import asyncio

import pytest

LOGIN = [("Username", (40, 100, 110, 120)), ("LOG IN", (40, 160, 100, 180))]
HOME = [("Welcome", (40, 40, 140, 60)), ("Pay", (40, 300, 80, 320))]


@pytest.fixture
def site(ns, mk_look):
    """A fake site: clicks move between screens by script; `take_look` returns the current screen."""
    screens = {"login": mk_look(LOGIN), "home": mk_look(HOME),
               "expired": mk_look([("Your session expired", (40, 40, 240, 60)), *LOGIN]),
               "done": mk_look([("Done", (40, 40, 90, 60))]),
               "missing": mk_look([("Account not found", (40, 40, 240, 60))]),
               "error": mk_look([("Error!", (40, 40, 100, 60)), ("An internal error occurred", (40, 70, 300, 90))])}
    state = {"now": "login", "pay": []}

    async def take_look():
        ns["STATE"].look = screens[state["now"]]
        return ns["STATE"].look

    async def click(step, point, cap):
        if step.target.ocr_text.text == "LOG IN":
            state["now"] = "home"
        else:
            state["now"] = state["pay"].pop(0)
        await take_look()
        return True

    async def typed(step, point, cap):
        return True

    ns.update(take_look=take_look, CFG=ns["Config"](check_s=0))
    ns["ACTIONS"] = {**ns["ACTIONS"], "click": click, "type": typed}
    ns["STATE"].look = screens["login"]
    ns["STATE"].outcomes = list(ns["CFG"].outcomes)
    return ns, state


def _cap(ns):
    S = ns["SCHEMA"]
    steps = [S["Type"](value="{{secret:username}}", target={"anchor": {"label": "Username", "offset": [150, 0]}}),
             S["Click"](target={"ocr_text": {"text": "LOG IN"}, "anchor": {"label": "LOG IN", "offset": [0, 0]}}),
             S["Click"](target={"ocr_text": {"text": "Pay"}, "anchor": {"label": "Pay", "offset": [0, 0]}})]
    return ns["Capability"](name="t", description="t", base_url="https://parabank.parasoft.com/p",
                            viewport=(1280, 800), steps=steps, checkpoint="Done")


def _walk(ns):
    return asyncio.run(ns["walk"](_cap(ns), None, []))


def test_not_found_screen_is_a_business_outcome_with_its_meaning(site) -> None:
    ns, state = site
    state["pay"] = ["missing"]
    with pytest.raises(ns["Stop"]) as e:
        _walk(ns)
    meaning = next(o["meaning"] for o in ns["CFG"].outcomes if o["text"] == "not found")
    assert e.value.status == "BUSINESS_OUTCOME" and e.value.reason == meaning
    assert e.value.observed.startswith("Account not found")


def test_expired_session_is_recovered_once(site) -> None:
    ns, state = site
    state["pay"] = ["expired", "done"]
    res = _walk(ns)
    assert res.status == "SUCCESS" and res.recoveries == 1


def test_a_second_expiry_is_not_recovered_again(site) -> None:
    ns, state = site
    state["pay"] = ["expired", "expired"]
    with pytest.raises(ns["Stop"]) as e:
        _walk(ns)
    assert e.value.status == "FAILED" and ns["STATE"].recoveries == 1


def test_error_page_fails_with_detail(site) -> None:
    ns, state = site
    state["pay"] = ["error"]
    with pytest.raises(ns["Stop"]) as e:
        _walk(ns)
    assert e.value.status == "FAILED" and ns["STATE"].step == 2
    assert e.value.expected == "step 3 without 'error'"
    assert e.value.observed == "Error! An internal error occurred"


def test_a_send_is_never_retried_after_an_expiry(site) -> None:
    ns, state = site
    state["pay"] = ["expired", "done"]
    click = ns["ACTIONS"]["click"]

    async def sending(step, point, cap):
        ns["STATE"].sent = step.target.ocr_text.text == "Pay"
        return await click(step, point, cap)

    ns["ACTIONS"]["click"] = sending
    with pytest.raises(ns["Stop"]) as e:
        _walk(ns)
    assert e.value.status == "FAILED" and ns["STATE"].recoveries == 0


def test_login_page_back_mid_run_is_recovered(site, mk_look) -> None:
    ns, state = site
    state["pay"] = ["login", "done"]              # no 'expired' text: just the login form again
    res = _walk(ns)
    assert res.status == "SUCCESS" and res.recoveries == 1
