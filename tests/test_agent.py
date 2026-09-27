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

import pytest

from cua.agent import (
    JOB_CONFIDENCE_THRESHOLD,
    JOB_CRITERIA,
    JOB_EXTRA_TOOLS,
    NEVER_HIDE,
    READ_LABELED_JS,
    DiscoveryAgent,
    PlaywrightSurface,
    build_typesafe_middleware,
    confidence_gate,
    format_elements,
    job_tool_names,
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


# ---------- D50/D52/D76/D99: TypeSafe job mapping, confidence gate, middleware construction ----------
# Ported directly from `03_recorder.py`'s own OFFLINE 13b/13c offline checks (same values, same
# expected sets), proving `cua.agent`'s copy of this logic behaves identically to the reference
# notebook's. Zero network, zero API key -- `confidence_gate`/`job_tool_names` are pure.
_ALL_TOOL_NAMES = {"observe", "click", "type_text", "type_secret", "select_option", "page_text",
                    "request_value", "request_missing_values", "ask_human", "finish"}


def test_never_hide_matches_agent_ipynb_original_four():
    assert NEVER_HIDE == {"observe", "click", "type_secret", "finish"}


def test_confidence_gate_narrows_when_confident():
    assert confidence_gate(_ALL_TOOL_NAMES, "login", 0.9) == NEVER_HIDE | {"type_secret"}
    assert confidence_gate(_ALL_TOOL_NAMES, "fill_form", 0.85) == NEVER_HIDE | {"type_text", "select_option"}
    assert confidence_gate(_ALL_TOOL_NAMES, "read_value", 0.8) == NEVER_HIDE | {"page_text"}
    assert confidence_gate(_ALL_TOOL_NAMES, "need_human", 0.99) == NEVER_HIDE | {"request_value", "ask_human"}


def test_confidence_gate_fails_open_below_threshold():
    assert confidence_gate(_ALL_TOOL_NAMES, "login", 0.59) == _ALL_TOOL_NAMES


def test_confidence_gate_boundary_is_inclusive():
    assert confidence_gate(_ALL_TOOL_NAMES, "login", JOB_CONFIDENCE_THRESHOLD) == NEVER_HIDE | {"type_secret"}


def test_confidence_gate_never_hide_survives_an_already_reduced_base_set():
    reduced = _ALL_TOOL_NAMES - {"request_value", "ask_human"}
    assert NEVER_HIDE <= confidence_gate(reduced, "fill_form", 0.9)


def test_confidence_gate_unknown_job_returns_never_hide_only():
    assert confidence_gate(_ALL_TOOL_NAMES, "not_a_real_job", 0.95) == NEVER_HIDE


def test_job_criteria_has_all_four_jobs_and_matches_job_extra_tools():
    assert set(JOB_CRITERIA) == set(JOB_EXTRA_TOOLS) == {"login", "fill_form", "read_value", "need_human"}


def test_confidence_gate_extra_never_hide_survives_confident_narrowing():
    """D76's own extension, ported: caller-specific tool names (cua.cli's recorder-only tools)
    passed as `never_hide` must survive confidence_gate under every job, confident or not --
    matching 03_recorder.py's own D76 offline check exactly."""
    new_tools = {"request_missing_values", "extract_value", "open_path", "finish_business_outcome"}
    all_tools = _ALL_TOOL_NAMES | new_tools
    never_hide = NEVER_HIDE | new_tools
    for job in ("login", "fill_form", "read_value", "need_human", "not_a_real_job"):
        assert new_tools <= confidence_gate(all_tools, job, 0.99, never_hide), f"job {job!r} must not strip the new tools"


# ---------- D99: build_typesafe_middleware itself (the actual bug fix) ----------
def _typesafe_agent() -> DiscoveryAgent:
    page = SimpleNamespace(url="https://parabank.parasoft.com/parabank/overview.htm")
    return DiscoveryAgent(page, given_text="Log in and read the balance of account 18672.")


def test_build_typesafe_middleware_is_off_by_default(monkeypatch):
    """No TYPESAFE_API_KEY in the environment: returns [] -- the caller's agent then behaves
    exactly as before this function existed (D50's own 'off by default' contract, unchanged)."""
    monkeypatch.delenv("TYPESAFE_API_KEY", raising=False)
    assert build_typesafe_middleware(_typesafe_agent()) == []


def test_build_typesafe_middleware_empty_key_is_also_off(monkeypatch):
    monkeypatch.setenv("TYPESAFE_API_KEY", "")
    assert build_typesafe_middleware(_typesafe_agent()) == []


def test_build_typesafe_middleware_builds_both_layers_when_key_set(monkeypatch):
    """THE fix under test: when TYPESAFE_API_KEY is set, this must build the SAME two middleware
    objects `03_recorder.py`'s BROWSER 12 builds (`recorder_middleware = [TypeSafeToolRouterMiddleware(...),
    recorder_router]`) -- never a real network call, just object construction. A fake key value is
    used (per this task's own hard rule: never a real TYPESAFE_API_KEY) -- `TypeSafeClassifier()`'s
    constructor only builds httpx clients, it makes no request at construction time."""
    from langchain.agents.middleware import AgentMiddleware
    from langchain_typesafe.experimental.middleware import ModelRouterMiddleware

    monkeypatch.setenv("TYPESAFE_API_KEY", "not-a-real-key-offline-test-only")
    middleware = build_typesafe_middleware(_typesafe_agent())

    assert len(middleware) == 2
    tool_router, model_router = middleware
    assert isinstance(tool_router, AgentMiddleware)
    assert type(tool_router).__name__ == "TypeSafeToolRouterMiddleware"
    assert isinstance(model_router, ModelRouterMiddleware)


def test_build_typesafe_middleware_extra_never_hide_reaches_the_tool_router(monkeypatch):
    """D76's extension must actually reach the constructed middleware, not just exist as a
    parameter -- read directly off the constructed instance's own `.never_hide` attribute (not
    re-derived independently), proving `extra_never_hide` was actually threaded through."""
    monkeypatch.setenv("TYPESAFE_API_KEY", "not-a-real-key-offline-test-only")
    extra = {"extract_value", "open_path", "finish_business_outcome", "request_missing_values"}
    middleware = build_typesafe_middleware(_typesafe_agent(), extra_never_hide=extra)
    tool_router = middleware[0]

    assert tool_router.never_hide == NEVER_HIDE | extra
    all_tools = _ALL_TOOL_NAMES | extra
    kept = confidence_gate(all_tools, "read_value", 0.99, tool_router.never_hide)
    assert extra <= kept, "extract_value and friends must survive a confident, unrelated job classification"


# ---------- D101 follow-up: READ_LABELED_JS parity with notebooks/03_recorder.py ----------
# `notebooks/03_recorder.py`'s own BROWSER 8 copy, transcribed here verbatim (same source text,
# same escaping) so this test can prove -- offline, no notebook import (03_recorder.py's own
# BROWSER cells are Playwright-live and never imported by the test suite) -- that agent.py's copy
# stayed byte-identical after the D101 port, matching D78's own established discipline of keeping
# this project's shared browser-side JS in sync across files by construction, not by trust.
_RECORDER_READ_LABELED_JS = """
(label) => {
  const norm = (s) => (s || '').replace(/\\s+/g, ' ').trim();
  const bare = (s) => norm(s).replace(/[^a-zA-Z0-9]$/, '').toLowerCase();
  const want = bare(label);
  const vis = (e) => { const r = e.getBoundingClientRect(); return r.width > 1 && r.height > 1; };
  const all = Array.from(document.body.querySelectorAll('td, th, dt, label, b, strong, span, div, p, li')).filter(vis);
  const hits = all.filter(e => bare(e.innerText || e.textContent) === want &&
                               !Array.from(e.children).some(c => bare(c.innerText || c.textContent) === want));
  const valueOf = (el) => {
    const cell = el.closest('td, th, dt');
    if (cell && cell.nextElementSibling) return norm(cell.nextElementSibling.innerText);
    if (el.tagName === 'LABEL' && el.htmlFor) { const t = document.getElementById(el.htmlFor); if (t) return norm(t.value || t.innerText); }
    if (el.nextElementSibling) return norm(el.nextElementSibling.innerText);
    let n = el.nextSibling;
    while (n) { const t = norm(n.textContent); if (t) return t; n = n.nextSibling; }
    return '';
  };
  const valueElementOf = (el) => {
    const cell = el.closest('td, th, dt');
    if (cell && cell.nextElementSibling) return cell.nextElementSibling;
    if (el.tagName === 'LABEL' && el.htmlFor) { return null; }
    if (el.nextElementSibling) return el.nextElementSibling;
    let n = el.nextSibling;
    while (n) { if (norm(n.textContent)) return (n.nodeType === 1 ? n : null); n = n.nextSibling; }
    return null;
  };
  const headerLike = (node) => {
    if (!node || node.nodeType !== 1) return false;
    if (node.tagName === 'TH') return true;
    if ((node.getAttribute('role') || '').toLowerCase() === 'columnheader') return true;
    if (node.closest && node.closest('thead')) return true;
    return false;
  };
  for (const h of hits) {
    const v = valueOf(h);
    if (v) {
      return {
        value: v, matches: hits.length,
        label_header: headerLike(h.closest('td, th, dt')) || headerLike(h),
        value_header: headerLike(valueElementOf(h)),
      };
    }
  }
  return { value: '', matches: hits.length, label_header: false, value_header: false };
}
"""


def test_read_labeled_js_matches_notebooks_03_recorder_byte_for_byte():
    """D101's own stated follow-up: `src/cua/agent.py`'s `READ_LABELED_JS` (what a real `cua
    discover` run actually evaluates, via `cli.py`'s capture glue) must stay byte-identical to
    `notebooks/03_recorder.py` BROWSER 8's copy (what `compile_run`'s D101 refusal was proven
    against). Byte-identical, not just whitespace-normalized, since both source files embed this
    JS the same way (a plain, non-raw triple-quoted Python string) -- there is no reason for them
    to differ at all, and this test would catch even a single-character drift (e.g. a future edit
    to one copy's `headerLike`/`valueElementOf` that forgets the other)."""
    assert READ_LABELED_JS == _RECORDER_READ_LABELED_JS


def test_read_labeled_js_reports_structural_header_flags():
    """Sanity check that the ported JS source itself (not just its byte-equality with the other
    copy) actually contains D101's two new helpers and both new return fields -- catches a
    byte-identical-but-wrong copy-paste of stale text into both places at once."""
    assert "valueElementOf" in READ_LABELED_JS
    assert "headerLike" in READ_LABELED_JS
    assert "label_header" in READ_LABELED_JS
    assert "value_header" in READ_LABELED_JS
