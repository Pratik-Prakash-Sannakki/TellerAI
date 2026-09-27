"""Tests for `cua.agent`'s pure (or pure-enough-to-test-without-a-browser) logic, ported from
`notebooks/agent.ipynb`'s own reasoning about `login_check`, `needs_human`, `_describe`,
`missing_field_labels`, and `format_elements` (D53, D54, D62, D69). None of this launches a
browser: `DiscoveryAgent` is constructed with a tiny stand-in `page` object (an object with just a
`.url` attribute, never a real Playwright page), used only for the methods that read `page.url`
without ever awaiting a real page method.

Zero API key, zero browser, zero network.
"""

from __future__ import annotations

from types import SimpleNamespace

from cua.agent import (
    DiscoveryAgent,
    PlaywrightSurface,
    format_elements,
    login_check,
    missing_field_labels,
    page_name_from_url,
)


# ---------- login_check (D69) ----------
def test_login_check_blocks_on_known_failure_text_attempt_1():
    attempts, blocked, reason = login_check(0, "Error: The username and password could not be verified.")
    assert attempts == 1 and blocked is True
    assert "could not be verified" in reason


def test_login_check_does_not_block_a_successful_looking_page():
    attempts, blocked, reason = login_check(0, "Accounts Overview")
    assert attempts == 1 and blocked is False and reason is None


def test_login_check_hard_caps_at_the_attempt_limit():
    attempts, blocked, reason = login_check(2, "Accounts Overview", limit=3)
    assert attempts == 3 and blocked is True
    assert "attempted 3 times" in reason


def test_login_check_below_limit_with_no_matching_text_does_not_block():
    attempts, blocked, reason = login_check(1, "Accounts Overview", limit=3)
    assert attempts == 2 and blocked is False


# ---------- missing_field_labels (D55) ----------
def test_missing_field_labels_finds_empty_visible_fillable_fields():
    elements = [
        {"ref": 1, "role": "textbox", "name": "City", "value": "", "inViewport": True},
        {"ref": 2, "role": "textbox", "name": "State", "value": "CA", "inViewport": True},   # already filled
        {"ref": 3, "role": "combobox", "name": "Account", "value": "", "inViewport": True},
        {"ref": 4, "role": "button", "name": "Submit", "value": "", "inViewport": True},     # not fillable
        {"ref": 5, "role": "textbox", "name": "Zip", "value": "", "inViewport": False},       # not visible
    ]
    out = missing_field_labels(elements)
    assert out == [(1, "City"), (3, "Account")]


def test_missing_field_labels_uses_a_hint_for_a_nameless_field():
    elements = [{"ref": 17, "role": "textbox", "name": "", "value": "", "inViewport": True}]
    assert missing_field_labels(elements, {"17": "loan amount"}) == [(17, "loan amount")]


def test_missing_field_labels_falls_back_to_field_n():
    elements = [{"ref": 17, "role": "textbox", "name": "", "value": "", "inViewport": True}]
    assert missing_field_labels(elements) == [(17, "field 17")]


# ---------- format_elements ----------
def test_format_elements_shows_current_value_and_below_the_fold():
    elements = [
        {"ref": 7, "role": "textbox", "name": "City", "value": "2", "inViewport": True},
        {"ref": 8, "role": "combobox", "name": "Account", "value": "", "options": ["A", "B"], "inViewport": False},
    ]
    text = format_elements(elements)
    assert "[7] textbox \"City\" = '2'" in text
    assert "options=['A', 'B']" in text and "below the fold" in text


# ---------- page_name_from_url ----------
def test_page_name_from_url_strips_query_and_session_id():
    assert page_name_from_url("https://parabank.parasoft.com/parabank/overview.htm?x=1") == "overview.htm"
    assert page_name_from_url("https://parabank.parasoft.com/parabank/index.htm;jsessionid=ABC") == "index.htm"


# ---------- DiscoveryAgent's own pure-ish methods, no browser needed ----------
def _agent(url: str = "https://parabank.parasoft.com/parabank/overview.htm") -> DiscoveryAgent:
    page = SimpleNamespace(url=url)
    return DiscoveryAgent(page, given_text="Log in and read the balance of account 14232.")


def test_discovery_agent_current_page():
    assert _agent().current_page() == "overview.htm"


def test_needs_human_flags_a_generic_submit_button():
    agent = _agent()
    agent.surface.last_elements = [{"ref": 3, "role": "button", "name": "Transfer", "submit": True}]
    assert agent.needs_human(3) is True


def test_needs_human_never_flags_a_safe_submit():
    agent = _agent()
    agent.surface.last_elements = [{"ref": 3, "role": "button", "name": "Log In", "submit": True}]
    assert agent.needs_human(3) is False


def test_needs_human_never_flags_a_plain_link():
    agent = _agent()
    agent.surface.last_elements = [{"ref": 3, "role": "link", "name": "Accounts Overview", "submit": False}]
    assert agent.needs_human(3) is False


def test_needs_human_transfer_under_auto_limit_is_safe():
    page = SimpleNamespace(url="https://parabank.parasoft.com/parabank/transfer.htm")
    agent = DiscoveryAgent(page, given_text="Transfer 20.00", auto_limit=500.0)
    agent.typed["amount"] = "20.00"
    agent.surface.last_elements = [{"ref": 5, "role": "button", "name": "Transfer", "submit": True}]
    assert agent.needs_human(5) is False


def test_needs_human_transfer_over_auto_limit_still_risky():
    page = SimpleNamespace(url="https://parabank.parasoft.com/parabank/transfer.htm")
    agent = DiscoveryAgent(page, given_text="Transfer 999.00", auto_limit=500.0)
    agent.typed["amount"] = "999.00"
    agent.surface.last_elements = [{"ref": 5, "role": "button", "name": "Transfer", "submit": True}]
    assert agent.needs_human(5) is True


def test_describe_prefers_name_and_hint_together():
    agent = _agent()
    agent.surface.last_elements = [{"ref": 4, "role": "textbox", "name": "City", "value": ""}]
    assert agent._describe(4) == "City"
    assert agent._describe(4, hint="the city field") == "City (the city field)"


def test_describe_falls_back_to_field_n_when_nothing_is_known():
    agent = _agent()
    assert agent._describe(17) == "field 17"


def test_playwright_surface_name_of_looks_up_last_elements():
    surface = PlaywrightSurface(page=SimpleNamespace(url="https://x"))
    surface.last_elements = [{"ref": 1, "role": "textbox", "name": "Username", "value": ""}]
    assert surface.name_of(1) == "Username"
    assert surface.name_of(99) is None
