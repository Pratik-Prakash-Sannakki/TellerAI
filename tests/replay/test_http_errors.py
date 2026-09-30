"""Navigate joins paths like a browser; an HTTP error page is FAILED, never a BUSINESS_OUTCOME."""
import asyncio

import pytest

BASE = "https://parabank.parasoft.com/parabank"


class Page:
    def __init__(self) -> None:
        self.went, self.main_frame = [], object()

    async def goto(self, url):
        self.went.append(url)


@pytest.mark.parametrize(("path", "want"), [
    ("/parabank/contact.htm", f"{BASE}/contact.htm"),
    ("about.htm", f"{BASE}/about.htm"),
    ("/", "https://parabank.parasoft.com/"),
])
def test_site_url_joins_like_a_browser(ns, path, want) -> None:
    assert ns["site_url"](BASE, path) == want


def test_navigate_goes_to_the_joined_url_once(ns) -> None:
    ns["page"], ns["STATE"].values = Page(), {"page": "contact.htm"}

    async def take_look():
        return None

    ns["take_look"] = take_look
    cap = ns["Capability"](name="t", description="t", base_url=BASE, viewport=(1280, 800),
                           steps=[ns["SCHEMA"]["Navigate"](path="/parabank/{{page}}")], checkpoint="x")
    asyncio.run(ns["do_navigate"](cap.steps[0], None, cap))
    assert ns["page"].went == [f"{BASE}/contact.htm"]


class Resp:
    def __init__(self, url, status, main=True, nav=True) -> None:
        self.url, self.status = url, status
        self.frame = PAGE_FRAME if main else object()
        self.request = type("Q", (), {"is_navigation_request": lambda s: nav, "frame": self.frame})()


PAGE_FRAME = object()


def test_only_the_main_documents_status_is_kept(ns) -> None:
    ns["page"] = type("P", (), {"main_frame": PAGE_FRAME})()
    ns["STATE"].http = None
    ns["note_response"](Resp(f"{BASE}/img.png", 404, nav=False))            # a sub-resource: ignored
    ns["note_response"](Resp("https://x/frame", 500, main=False))            # an iframe: ignored
    assert ns["STATE"].http is None
    ns["note_response"](Resp("https://parabank.parasoft.com/parabank/parabank/contact.htm;jsessionid=AB?x=1", 404))
    assert ns["STATE"].http == (404, "/parabank/parabank/contact.htm")


def _judge(ns, mk_look, http, text):
    ns["STATE"].look = mk_look([(text, (0, 0, 200, 20))])
    ns["STATE"].http, ns["STATE"].outcomes = http, list(ns["CFG"].outcomes)
    cap = ns["Capability"](name="t", description="t", base_url=BASE, viewport=(1280, 800),
                           steps=[ns["SCHEMA"]["Navigate"](path="/x")], checkpoint="x")
    return asyncio.run(ns["judge"](0, "", cap, None, []))


def test_a_404_navigation_is_failed_not_a_business_outcome(ns, mk_look) -> None:
    with pytest.raises(ns["Stop"]) as e:
        _judge(ns, mk_look, (404, "/parabank/parabank/contact.htm"), "Not Found")
    assert e.value.status == "FAILED" and e.value.reason == "page returned HTTP 404"
    assert e.value.observed == "/parabank/parabank/contact.htm"


def test_a_200_page_with_not_found_text_is_still_a_business_outcome(ns, mk_look) -> None:
    with pytest.raises(ns["Stop"]) as e:
        _judge(ns, mk_look, (200, "/parabank/find.htm"), "Account not found")
    assert e.value.status == "BUSINESS_OUTCOME"


@pytest.mark.parametrize("body", ['{"title":"Not Found","status":404}', 'x {"type":"err","status":500} y'])
def test_a_raw_json_error_body_is_failed(ns, mk_look, body) -> None:
    with pytest.raises(ns["Stop"]) as e:
        _judge(ns, mk_look, None, body)
    assert e.value.status == "FAILED" and e.value.reason == "page is a raw error response"


def test_a_normal_page_passes(ns, mk_look) -> None:
    assert _judge(ns, mk_look, (200, "/parabank/overview.htm"), "Accounts Overview") is False
