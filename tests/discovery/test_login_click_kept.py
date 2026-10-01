"""Live pay_bill.yaml (2026-09-30) lost its LOG IN click: without_detours saw LOG IN and Bill Pay
as one run of page moves, and since 'Bill Pay' was already on the logged-out home page, it dropped
LOG IN as a detour. A click right after typing into a form is a submit: never a detour or no-op."""
from tests.discovery.test_save_artifact import NS, SENT, START, _ev, _meta

SITE = "https://parabank.parasoft.com/parabank/"
HOME = ["Customer Login", "Username", "Password", "LOG IN", "Bill Pay", "Transfer Funds"]
MENU = ["Accounts Overview", "Transfer Funds", "Bill Pay", "Log Out"]


def _click(text: str, frm: str, to: str, before: list[str], label: str | None = None, **kw) -> dict:
    return {**_ev("click", {"ref": 3, "x": None, "y": None}, f"Clicked {text!r}.", label=label,
                  own=text, text=text), "url": SITE + to, "from_url": SITE + frm,
            "loaded": frm != to, "navigated": frm != to, "new_texts": True, "from_texts": before, **kw}


def _type(tool: str, label: str, url: str = "index.htm") -> dict:
    args = {"secret_name": label.casefold()} if tool == "type_secret" else {"ref": 4, "x": None, "y": None}
    return {**_ev(tool, args, "Typed at (300, 200).", label=label), "url": SITE + url}


LOGIN = [_type("type_secret", "Username"), _type("type_secret", "Password"),
         _click("LOG IN", "index.htm", "overview.htm", HOME, label="Password")]
BILL_PAY = _click("Bill Pay.", "overview.htm", "billpay.htm", MENU, label="Transfer Funds")


def _names(steps) -> list[str]:
    return [s.target.ocr_text.text if s.action == "click" else s.action for s in steps]


def test_the_login_click_before_a_menu_link_is_kept() -> None:
    kept = NS["step_events"]([START, *LOGIN, BILL_PAY])
    assert [ev.get("text") or ev["tool"] for ev in kept] == \
        ["type_secret", "type_secret", "LOG IN", "Bill Pay."]


def test_a_login_click_that_stays_on_the_page_is_not_a_no_op() -> None:
    same = _click("LOG IN", "index.htm", "index.htm", HOME, label="Password", new_texts=False)
    kept = NS["step_events"]([START, *LOGIN[:2], same])
    assert [ev.get("text") for ev in kept][-1] == "LOG IN"


def test_a_pay_bill_log_keeps_login_bill_pay_fields_send_logout() -> None:
    fields = [_type("type_text", "Payee Name:", "billpay.htm"), _type("type_text", "Amount: $", "billpay.htm")]
    send = _click("SEND PAYMENT", "billpay.htm", "billpay.htm", MENU, label="From account #:")
    logout = _click("Log Out", "billpay.htm", "index.htm", MENU, label="Request Loan")
    cap = NS["build_capability"]([START, *LOGIN, BILL_PAY, *fields, send, SENT, logout], _meta(name="pay"))
    assert _names(cap.steps) == ["type", "type", "LOG IN", "Bill Pay.", "type", "type",
                                 "SEND PAYMENT", "Log Out"]
    assert cap.steps[-1].cleanup is True


def test_a_menu_detour_after_login_is_still_dropped() -> None:
    detour = _click("Transfer Funds", "overview.htm", "transfer.htm", MENU)
    bill = {**BILL_PAY, "from_url": SITE + "transfer.htm"}
    kept = NS["step_events"]([START, *LOGIN, detour, bill])
    assert [ev.get("text") for ev in kept][2:] == ["LOG IN", "Bill Pay."]


def test_a_login_click_after_a_scroll_is_still_kept() -> None:
    scroll = {**_ev("scroll", {"direction": "down"}, "Scrolled."), "url": SITE + "index.htm"}
    login = {**LOGIN[2], "login": True}
    kept = NS["step_events"]([START, *LOGIN[:2], scroll, login, BILL_PAY])
    assert [ev.get("text") for ev in kept][-2:] == ["LOG IN", "Bill Pay."]
