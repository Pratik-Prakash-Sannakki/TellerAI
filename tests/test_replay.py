"""Tests for `cua.replay` (sync + async engines), ported from `notebooks/04_replay_engine.py`'s
offline check cells (Sections 2b/3b/4b for the sync engine, 7b/8b/9b for the async mirror) plus
the Section 5/10 integration checks against the two real example artifacts.

Zero API key, zero browser, zero network, no `import playwright` anywhere in this file or in
`cua.replay` itself -- everything runs against a hand-built `FakeSurface`/`AsyncFakeSurface`.
"""

from __future__ import annotations

import asyncio
import pathlib
from typing import Any, Callable

import pytest

from cua.replay import (
    AsyncReplaySurface,
    InputValidationError,
    ReplaySurface,
    ResolutionError,
    TransientFailure,
    matches_value_type,
    render,
    resolve_target,
    resolve_target_async,
    run_capability,
    run_capability_async,
    validate_inputs,
)
from cua.schema import (
    Capability,
    RoleLocator,
    Target,
    TextLocator,
    check_result,
    from_yaml,
)

REPO = pathlib.Path(__file__).resolve().parents[1]
EXAMPLES = REPO / "artifacts" / "examples"


# ---------- Section 2b: protocol + exceptions ----------
class _MinimalSurface:
    def navigate(self, path): pass
    def resolve(self, locator): return None
    def click(self, ref): pass
    def type_text(self, ref, value): pass
    def select_option(self, ref, value): pass
    def read_value(self, ref): return ""
    def current_url(self): return "/"
    def page_text(self): return ""


def test_minimal_surface_satisfies_protocol():
    assert isinstance(_MinimalSurface(), ReplaySurface)


def test_exceptions_are_exceptions():
    for exc_cls in (TransientFailure, ResolutionError, InputValidationError):
        assert issubclass(exc_cls, Exception)


def test_resolution_error_names_the_target():
    with pytest.raises(ResolutionError) as exc_info:
        raise ResolutionError(Target(primary=RoleLocator(role="button", name="Log In", note="n")))
    assert "primary" in str(exc_info.value)


# ---------- Section 3b: resolve_target, templates, input validation ----------
class _DictSurface:
    def __init__(self, hits: dict[tuple, Any]):
        self.hits = hits

    def resolve(self, locator):
        if locator.strategy == "role":
            return self.hits.get(("role", locator.role, locator.name))
        if locator.strategy == "text":
            return self.hits.get(("text", locator.text))
        return None


PRIMARY = RoleLocator(role="button", name="Log In", note="n")
FALLBACK = TextLocator(text="Log In", note="n")
TARGET = Target(primary=PRIMARY, fallback=FALLBACK)


def test_resolve_target_primary_resolves():
    log: list[str] = []
    assert resolve_target(_DictSurface({("role", "button", "Log In"): 1}), TARGET, logger=log.append) == 1
    assert any("primary" in line for line in log)


def test_resolve_target_falls_back():
    log: list[str] = []
    assert resolve_target(_DictSurface({("text", "Log In"): 2}), TARGET, logger=log.append) == 2
    assert any("fallback" in line for line in log)


def test_resolve_target_both_miss_raises_naming_both():
    with pytest.raises(ResolutionError) as exc_info:
        resolve_target(_DictSurface({}), TARGET)
    assert "primary" in str(exc_info.value) and "fallback" in str(exc_info.value)


def test_render_templates():
    assert render("id={{account_id}}, pw={{secret:password}}", {"account_id": "42"}, lambda name: f"SECRET[{name}]") \
        == "id=42, pw=SECRET[password]"


def test_matches_value_type():
    assert matches_value_type("42", "integer") and not matches_value_type("x", "integer")
    assert matches_value_type("$1,200.00", "currency") and not matches_value_type("free", "currency")
    assert matches_value_type("anything", "string")


CHECK_CAP = Capability.model_validate({
    "schema_version": 1, "name": "check_cap", "version": 1, "status": "draft",
    "description": "d", "base_url": "https://x.example", "risk_level": "safe",
    "inputs": [{"name": "n", "type": "string", "description": "d", "pattern": "^[0-9]+$"}],
    "outputs": [], "secrets": [],
    "steps": [{"action": "navigate", "path": "/x"}],
    "checkpoint": {"url_contains": "x", "text_present": "x"},
})


def test_validate_inputs_ok():
    assert validate_inputs(CHECK_CAP, {"n": "7"}) == {"n": "7"}


@pytest.mark.parametrize("bad_inputs", [{"n": "abc"}, {}, {"n": "1", "extra": "y"}])
def test_validate_inputs_rejects(bad_inputs):
    with pytest.raises(InputValidationError):
        validate_inputs(CHECK_CAP, bad_inputs)


# ---------- Section 4b: run_capability -- the 8 required scenarios, plus 3 bonus ----------
def _locator_key(loc) -> tuple:
    if loc.strategy == "role":
        return ("role", loc.role, loc.name)
    if loc.strategy == "label":
        return ("label", loc.label)
    if loc.strategy == "text":
        return ("text", loc.text)
    if loc.strategy == "structure":
        return ("structure", loc.tag, loc.nth, loc.within.role)
    if loc.strategy == "labeled_value":
        return ("labeled_value", loc.label)
    raise ValueError(f"unknown strategy {loc.strategy}")


class FakeSurface:
    def __init__(self):
        self.url = "/start"
        self.pages: dict[str, str] = {}
        self.registry: dict[str, dict[tuple, int]] = {}
        self.values: dict[int, str] = {}
        self.click_effects: dict[int, Callable[["FakeSurface"], None]] = {}
        self.clicked: list[int] = []
        self.typed: dict[int, str] = {}
        self.selected: dict[int, str] = {}
        self.navigated: list[str] = []
        self.transient: dict[tuple, int] = {}

    def set_page(self, url, text): self.pages[url] = text
    def register(self, url, locator, ref): self.registry.setdefault(url, {})[_locator_key(locator)] = ref
    def set_value(self, ref, value): self.values[ref] = value
    def fail_next(self, action, key, times): self.transient[(action, key)] = times

    def _maybe_fail(self, action, key):
        left = self.transient.get((action, key), 0)
        if left > 0:
            self.transient[(action, key)] = left - 1
            raise TransientFailure(f"{action} not ready yet ({key!r})")

    def navigate(self, path):
        self._maybe_fail("navigate", path)
        self.navigated.append(path)
        self.url = path

    def resolve(self, locator):
        return self.registry.get(self.url, {}).get(_locator_key(locator))

    def click(self, ref):
        self._maybe_fail("click", ref)
        self.clicked.append(ref)
        effect = self.click_effects.get(ref)
        if effect:
            effect(self)

    def type_text(self, ref, value):
        self._maybe_fail("type", ref)
        self.typed[ref] = value

    def select_option(self, ref, value):
        self._maybe_fail("select", ref)
        self.selected[ref] = value

    def read_value(self, ref): return self.values.get(ref, "")
    def current_url(self): return self.url
    def page_text(self): return self.pages.get(self.url, "")


def no_secrets(name):
    raise AssertionError(f"no secret should be needed in this test, asked for {name!r}")


TEST_CAP = Capability.model_validate({
    "schema_version": 1, "name": "test_flow", "version": 1, "status": "draft",
    "description": "A tiny capability used only to test the replay engine.",
    "base_url": "https://fake.example", "risk_level": "safe",
    "inputs": [{"name": "item_id", "type": "string", "description": "id", "pattern": "^[0-9]+$"}],
    "outputs": [{"name": "value", "type": "integer", "description": "extracted value"}],
    "secrets": [],
    "steps": [
        {"action": "navigate", "path": "/item.htm?id={{item_id}}"},
        {"action": "click", "target": {
            "primary": {"strategy": "role", "role": "button", "name": "Show", "note": "n"},
            "fallback": {"strategy": "text", "text": "Show", "note": "n"},
        }},
        {"action": "extract", "target": {
            "primary": {"strategy": "labeled_value", "label": "Value:", "note": "n"}},
            "save_as": "value"},
    ],
    "checkpoint": {"url_contains": "item.htm", "text_present": "Value:"},
    "outcome_rules": [
        {"when": {"text_present": "Not Found"}, "kind": "business", "outcome": "ITEM_NOT_FOUND", "message": "no such item"},
        {"when": {"text_present": "Internal Error"}, "kind": "hard", "message": "internal error"},
    ],
})

RISKY_CAP = Capability.model_validate({
    "schema_version": 1, "name": "test_pay", "version": 1, "status": "draft",
    "description": "A tiny risky capability used only to test the replay engine.",
    "base_url": "https://fake.example", "risk_level": "risky",
    "inputs": [{"name": "amount", "type": "currency", "description": "amount", "pattern": r"^\$?[0-9]+(\.[0-9]{2})?$"}],
    "outputs": [], "secrets": [],
    "steps": [
        {"action": "navigate", "path": "/pay.htm"},
        {"action": "click", "risk": "risky", "amount_input": "amount", "target": {
            "primary": {"strategy": "role", "role": "button", "name": "Pay", "note": "n"}}},
    ],
    "checkpoint": {"url_contains": "pay.htm", "text_present": "Paid"},
    "outcome_rules": [],
})


def new_happy_surface() -> FakeSurface:
    s = FakeSurface()
    url = "/item.htm?id=42"
    s.set_page(url, "Item page. Value: 99")
    s.register(url, TEST_CAP.steps[1].target.primary, 1)
    s.register(url, TEST_CAP.steps[1].target.fallback, 1)
    s.register(url, TEST_CAP.steps[2].target.primary, 2)
    s.set_value(2, "99")
    return s


def test_1_happy_path():
    result = run_capability(TEST_CAP, new_happy_surface(), {"item_id": "42"}, no_secrets)
    assert result.status == "SUCCESS" and result.outputs == {"value": "99"}


def test_2_business_outcome():
    surface = FakeSurface()
    url = "/item.htm?id=99"
    surface.set_page(url, "Not Found: no such item")
    surface.register(url, TEST_CAP.steps[1].target.primary, 1)
    result = run_capability(TEST_CAP, surface, {"item_id": "99"}, no_secrets)
    assert result.status == "BUSINESS_OUTCOME" and result.outcome == "ITEM_NOT_FOUND"


def test_3_primary_fails_fallback_succeeds():
    surface = new_happy_surface()
    del surface.registry["/item.htm?id=42"][_locator_key(TEST_CAP.steps[1].target.primary)]
    log = []
    result = run_capability(TEST_CAP, surface, {"item_id": "42"}, no_secrets, logger=log.append)
    assert result.status == "SUCCESS"
    assert any("fallback" in line for line in log)


def test_4_both_locators_fail():
    surface = FakeSurface()
    surface.set_page("/item.htm?id=1", "Item page. Value: 1")
    result = run_capability(TEST_CAP, surface, {"item_id": "1"}, no_secrets)
    assert result.status == "FAILED"
    assert result.failure.step_index == 1 and result.failure.step_action == "click"
    assert "primary" in result.failure.expected and "fallback" in result.failure.expected


def test_5_risky_under_limit_auto_approved():
    surface = FakeSurface()
    surface.register("/pay.htm", RISKY_CAP.steps[1].target.primary, 7)
    surface.click_effects[7] = lambda s: s.set_page("/pay.htm", "Paid. Thank you.")
    result = run_capability(RISKY_CAP, surface, {"amount": "100.00"}, no_secrets, auto_approve_limit=500.0)
    assert result.status == "SUCCESS"
    assert surface.clicked == [7]


def test_6_risky_at_limit_escalated_not_clicked():
    surface = FakeSurface()
    surface.register("/pay.htm", RISKY_CAP.steps[1].target.primary, 7)
    calls = []
    result = run_capability(RISKY_CAP, surface, {"amount": "600.00"}, no_secrets,
                             auto_approve_limit=500.0, escalate=lambda reason, ctx: calls.append((reason, ctx)))
    assert result.status == "NEEDS_APPROVAL" and result.pending_step == 1
    assert len(calls) == 1 and "500" in calls[0][0]
    assert 7 not in surface.clicked


def test_7_checkpoint_fails():
    surface = new_happy_surface()
    surface.set_page("/item.htm?id=42", "Item page, no value shown here")
    result = run_capability(TEST_CAP, surface, {"item_id": "42"}, no_secrets)
    assert result.status == "FAILED" and result.failure.step_action == "checkpoint"


def test_8_bad_output_type():
    surface = new_happy_surface()
    surface.set_value(2, "not-a-number")
    result = run_capability(TEST_CAP, surface, {"item_id": "42"}, no_secrets)
    assert result.status == "FAILED" and result.failure.step_action == "extract"


def test_bonus_transient_failure_retried_then_succeeds():
    surface = new_happy_surface()
    surface.fail_next("click", 1, times=2)
    result = run_capability(TEST_CAP, surface, {"item_id": "42"}, no_secrets)
    assert result.status == "SUCCESS"


def test_bonus_transient_failure_past_retry_bound():
    surface = new_happy_surface()
    surface.fail_next("click", 1, times=5)
    result = run_capability(TEST_CAP, surface, {"item_id": "42"}, no_secrets, max_retries=2)
    assert result.status == "FAILED" and "transient failure" in result.failure.observed


def test_bonus_risky_click_never_retried():
    surface = FakeSurface()
    surface.register("/pay.htm", RISKY_CAP.steps[1].target.primary, 7)
    surface.fail_next("click", 7, times=1)
    result = run_capability(RISKY_CAP, surface, {"amount": "10.00"}, no_secrets)
    assert result.status == "FAILED"


# ---------- Section 5: integration -- both real example artifacts, sync engine ----------
def resolve_secret_unused(name):
    raise AssertionError("no secret is used by either example artifact")


def test_integration_get_account_balance():
    bal = from_yaml((EXAMPLES / "get_account_balance.yaml").read_text())
    bal_surface = FakeSurface()
    bal_url = "/activity.htm?id=13344"
    bal_surface.set_page(bal_url, "Account Details\nBalance: $1,200.00")
    bal_extract = next(s for s in bal.steps if s.action == "extract")
    bal_surface.register(bal_url, bal_extract.target.primary, 1)
    bal_surface.set_value(1, "$1,200.00")

    result = run_capability(bal, bal_surface, {"account_id": "13344"}, resolve_secret_unused, run_id="evidence-1")
    assert result.status == "SUCCESS"
    assert result.outputs == {"balance": "$1,200.00"}
    check_result(bal, result)

    bad_surface = FakeSurface()
    bad_url = "/activity.htm?id=00000"
    bad_surface.set_page(bad_url, "Could not find account 00000")
    bad_result = run_capability(bal, bad_surface, {"account_id": "00000"}, resolve_secret_unused, run_id="evidence-1b")
    assert bad_result.status == "BUSINESS_OUTCOME" and bad_result.outcome == "ACCOUNT_NOT_FOUND"
    check_result(bal, bad_result)


def _xfer_surface(xfer):
    xurl = "/transfer.htm"
    surface = FakeSurface()
    surface.set_page(xurl, "Transfer Funds\nAmount: From account #: To account #:")
    xfer_type, xfer_sel1, xfer_sel2, xfer_click, xfer_extract = (s for s in xfer.steps if s.action != "navigate")
    surface.register(xurl, xfer_type.target.primary, 10)
    surface.register(xurl, xfer_type.target.fallback, 10)
    surface.register(xurl, xfer_sel1.target.primary, 11)
    surface.register(xurl, xfer_sel2.target.primary, 12)
    surface.register(xurl, xfer_click.target.primary, 13)
    return surface, xurl, xfer_extract


def test_integration_transfer_funds_under_limit():
    xfer = from_yaml((EXAMPLES / "transfer_funds.yaml").read_text())
    surface, xurl, xfer_extract = _xfer_surface(xfer)
    surface.register(xurl, xfer_extract.target.primary, 14)
    surface.set_value(14, "Transfer Complete!")
    surface.click_effects[13] = lambda s: s.set_page(xurl, "Transfer Complete! $20.00 has moved.")

    inputs = {"from_account": "13344", "to_account": "13355", "amount": "20.00"}
    result = run_capability(xfer, surface, inputs, resolve_secret_unused, run_id="evidence-2", auto_approve_limit=500.0)
    assert result.status == "SUCCESS"
    assert result.outputs == {"confirmation": "Transfer Complete!"}
    assert surface.typed[10] == "20.00" and surface.selected[11] == "13344" and surface.selected[12] == "13355"
    assert surface.clicked == [13]
    check_result(xfer, result)


def test_integration_transfer_funds_over_limit_needs_approval():
    xfer = from_yaml((EXAMPLES / "transfer_funds.yaml").read_text())
    surface, xurl, _ = _xfer_surface(xfer)
    approvals = []
    result = run_capability(
        xfer, surface, {"from_account": "13344", "to_account": "13355", "amount": "999.00"},
        resolve_secret_unused, run_id="evidence-3", auto_approve_limit=500.0,
        escalate=lambda reason, ctx: approvals.append((reason, ctx)),
    )
    assert result.status == "NEEDS_APPROVAL" and result.pending_step == 4
    assert 13 not in surface.clicked
    assert len(approvals) == 1


def test_integration_transfer_funds_escalate_approves_over_limit_click():
    """D85: escalate returning 'approve' makes the engine click for real and continue on to
    SUCCESS with the real confirmation, not stop at NEEDS_APPROVAL."""
    xfer = from_yaml((EXAMPLES / "transfer_funds.yaml").read_text())
    surface, xurl, xfer_extract = _xfer_surface(xfer)
    surface.register(xurl, xfer_extract.target.primary, 14)
    surface.set_value(14, "Transfer Complete!")
    surface.click_effects[13] = lambda s: s.set_page(xurl, "Transfer Complete! $999.00 has moved.")
    calls = []
    result = run_capability(
        xfer, surface, {"from_account": "13344", "to_account": "13355", "amount": "999.00"},
        resolve_secret_unused, run_id="evidence-4", auto_approve_limit=500.0,
        escalate=lambda reason, ctx: (calls.append((reason, ctx)), "approve")[1],
    )
    assert result.status == "SUCCESS"
    assert result.outputs == {"confirmation": "Transfer Complete!"}
    assert surface.clicked == [13]
    assert len(calls) == 1
    check_result(xfer, result)


def test_integration_transfer_funds_escalate_approves_but_target_unresolvable():
    """D85: an approved click that cannot be resolved is a FAILED, never a silent success."""
    xfer = from_yaml((EXAMPLES / "transfer_funds.yaml").read_text())
    surface = FakeSurface()
    xurl = "/transfer.htm"
    surface.set_page(xurl, "Transfer Funds\nAmount: From account #: To account #:")
    xfer_type, xfer_sel1, xfer_sel2, _click, _extract = (s for s in xfer.steps if s.action != "navigate")
    surface.register(xurl, xfer_type.target.primary, 10)
    surface.register(xurl, xfer_sel1.target.primary, 11)
    surface.register(xurl, xfer_sel2.target.primary, 12)
    result = run_capability(
        xfer, surface, {"from_account": "13344", "to_account": "13355", "amount": "999.00"},
        resolve_secret_unused, run_id="evidence-5", auto_approve_limit=500.0,
        escalate=lambda reason, ctx: "approve",
    )
    assert result.status == "FAILED" and result.failure.step_action == "click"
    assert 13 not in surface.clicked


def test_integration_transfer_funds_escalate_non_approve_string_stays_needs_approval():
    xfer = from_yaml((EXAMPLES / "transfer_funds.yaml").read_text())
    surface, xurl, _ = _xfer_surface(xfer)
    result = run_capability(
        xfer, surface, {"from_account": "13344", "to_account": "13355", "amount": "999.00"},
        resolve_secret_unused, run_id="evidence-6", auto_approve_limit=500.0,
        escalate=lambda reason, ctx: "reject",
    )
    assert result.status == "NEEDS_APPROVAL" and result.pending_step == 4
    assert 13 not in surface.clicked


# ---------- Section 7b-9b: the async mirror ----------
class _MinimalAsyncSurface:
    async def navigate(self, path): pass
    async def resolve(self, locator): return None
    async def click(self, ref): pass
    async def type_text(self, ref, value): pass
    async def select_option(self, ref, value): pass
    async def read_value(self, ref): return ""
    async def current_url(self): return "/"
    async def page_text(self): return ""


def test_minimal_async_surface_satisfies_protocol():
    assert isinstance(_MinimalAsyncSurface(), AsyncReplaySurface)


class _AsyncDictSurface:
    def __init__(self, hits):
        self.hits = hits

    async def resolve(self, locator):
        if locator.strategy == "role":
            return self.hits.get(("role", locator.role, locator.name))
        if locator.strategy == "text":
            return self.hits.get(("text", locator.text))
        return None


def test_resolve_target_async_primary_and_fallback():
    async def run():
        log = []
        assert await resolve_target_async(_AsyncDictSurface({("role", "button", "Log In"): 1}), TARGET, logger=log.append) == 1
        assert any("primary" in line for line in log)

        log.clear()
        assert await resolve_target_async(_AsyncDictSurface({("text", "Log In"): 2}), TARGET, logger=log.append) == 2
        assert any("fallback" in line for line in log)

        with pytest.raises(ResolutionError):
            await resolve_target_async(_AsyncDictSurface({}), TARGET)

    asyncio.run(run())


class AsyncFakeSurface:
    def __init__(self):
        self.url = "/start"
        self.pages: dict[str, str] = {}
        self.registry: dict[str, dict[tuple, int]] = {}
        self.values: dict[int, str] = {}
        self.click_effects: dict[int, Callable[["AsyncFakeSurface"], None]] = {}
        self.clicked: list[int] = []
        self.typed: dict[int, str] = {}
        self.selected: dict[int, str] = {}
        self.navigated: list[str] = []
        self.transient: dict[tuple, int] = {}

    def set_page(self, url, text): self.pages[url] = text
    def register(self, url, locator, ref): self.registry.setdefault(url, {})[_locator_key(locator)] = ref
    def set_value(self, ref, value): self.values[ref] = value
    def fail_next(self, action, key, times): self.transient[(action, key)] = times

    def _maybe_fail(self, action, key):
        left = self.transient.get((action, key), 0)
        if left > 0:
            self.transient[(action, key)] = left - 1
            raise TransientFailure(f"{action} not ready yet ({key!r})")

    async def navigate(self, path):
        self._maybe_fail("navigate", path)
        self.navigated.append(path)
        self.url = path

    async def resolve(self, locator):
        return self.registry.get(self.url, {}).get(_locator_key(locator))

    async def click(self, ref):
        self._maybe_fail("click", ref)
        self.clicked.append(ref)
        effect = self.click_effects.get(ref)
        if effect:
            effect(self)

    async def type_text(self, ref, value):
        self._maybe_fail("type", ref)
        self.typed[ref] = value

    async def select_option(self, ref, value):
        self._maybe_fail("select", ref)
        self.selected[ref] = value

    async def read_value(self, ref): return self.values.get(ref, "")
    async def current_url(self): return self.url
    async def page_text(self): return self.pages.get(self.url, "")


def new_happy_async_surface() -> AsyncFakeSurface:
    s = AsyncFakeSurface()
    url = "/item.htm?id=42"
    s.set_page(url, "Item page. Value: 99")
    s.register(url, TEST_CAP.steps[1].target.primary, 1)
    s.register(url, TEST_CAP.steps[1].target.fallback, 1)
    s.register(url, TEST_CAP.steps[2].target.primary, 2)
    s.set_value(2, "99")
    return s


def test_async_engine_all_scenarios():
    async def run():
        # (1) happy path
        result = await run_capability_async(TEST_CAP, new_happy_async_surface(), {"item_id": "42"}, no_secrets)
        assert result.status == "SUCCESS" and result.outputs == {"value": "99"}

        # (2) business outcome
        surface = AsyncFakeSurface()
        surface.set_page("/item.htm?id=99", "Not Found: no such item")
        surface.register("/item.htm?id=99", TEST_CAP.steps[1].target.primary, 1)
        result = await run_capability_async(TEST_CAP, surface, {"item_id": "99"}, no_secrets)
        assert result.status == "BUSINESS_OUTCOME" and result.outcome == "ITEM_NOT_FOUND"

        # (3) primary fails, fallback succeeds
        surface = new_happy_async_surface()
        del surface.registry["/item.htm?id=42"][_locator_key(TEST_CAP.steps[1].target.primary)]
        log = []
        result = await run_capability_async(TEST_CAP, surface, {"item_id": "42"}, no_secrets, logger=log.append)
        assert result.status == "SUCCESS"
        assert any("fallback" in line for line in log)

        # (4) both locators fail
        surface = AsyncFakeSurface()
        surface.set_page("/item.htm?id=1", "Item page. Value: 1")
        result = await run_capability_async(TEST_CAP, surface, {"item_id": "1"}, no_secrets)
        assert result.status == "FAILED"
        assert result.failure.step_index == 1 and result.failure.step_action == "click"

        # (5) risky under limit
        surface = AsyncFakeSurface()
        surface.register("/pay.htm", RISKY_CAP.steps[1].target.primary, 7)
        surface.click_effects[7] = lambda s: s.set_page("/pay.htm", "Paid. Thank you.")
        result = await run_capability_async(RISKY_CAP, surface, {"amount": "100.00"}, no_secrets, auto_approve_limit=500.0)
        assert result.status == "SUCCESS" and surface.clicked == [7]

        # (6) risky at limit, async fake escalate
        surface = AsyncFakeSurface()
        surface.register("/pay.htm", RISKY_CAP.steps[1].target.primary, 7)
        calls = []

        async def fake_escalate(reason, ctx):
            calls.append((reason, ctx))

        result = await run_capability_async(RISKY_CAP, surface, {"amount": "600.00"}, no_secrets,
                                             auto_approve_limit=500.0, escalate=fake_escalate)
        assert result.status == "NEEDS_APPROVAL" and result.pending_step == 1
        assert len(calls) == 1 and 7 not in surface.clicked

        # (7) checkpoint fails
        surface = new_happy_async_surface()
        surface.set_page("/item.htm?id=42", "Item page, no value shown here")
        result = await run_capability_async(TEST_CAP, surface, {"item_id": "42"}, no_secrets)
        assert result.status == "FAILED" and result.failure.step_action == "checkpoint"

        # (8) bad output type
        surface = new_happy_async_surface()
        surface.set_value(2, "not-a-number")
        result = await run_capability_async(TEST_CAP, surface, {"item_id": "42"}, no_secrets)
        assert result.status == "FAILED" and result.failure.step_action == "extract"

        # bonus: retried transient failure
        surface = new_happy_async_surface()
        surface.fail_next("click", 1, times=2)
        result = await run_capability_async(TEST_CAP, surface, {"item_id": "42"}, no_secrets)
        assert result.status == "SUCCESS"

        # bonus: retries exhausted
        surface = new_happy_async_surface()
        surface.fail_next("click", 1, times=5)
        result = await run_capability_async(TEST_CAP, surface, {"item_id": "42"}, no_secrets, max_retries=2)
        assert result.status == "FAILED" and "transient failure" in result.failure.observed

        # bonus: risky click never retried
        surface = AsyncFakeSurface()
        surface.register("/pay.htm", RISKY_CAP.steps[1].target.primary, 7)
        surface.fail_next("click", 7, times=1)
        result = await run_capability_async(RISKY_CAP, surface, {"amount": "10.00"}, no_secrets)
        assert result.status == "FAILED"

    asyncio.run(run())


def test_async_integration_both_examples():
    async def run():
        bal = from_yaml((EXAMPLES / "get_account_balance.yaml").read_text())
        xfer = from_yaml((EXAMPLES / "transfer_funds.yaml").read_text())

        bal_surface = AsyncFakeSurface()
        bal_url = "/activity.htm?id=13344"
        bal_surface.set_page(bal_url, "Account Details\nBalance: $1,200.00")
        bal_extract = next(s for s in bal.steps if s.action == "extract")
        bal_surface.register(bal_url, bal_extract.target.primary, 1)
        bal_surface.set_value(1, "$1,200.00")
        result = await run_capability_async(bal, bal_surface, {"account_id": "13344"}, resolve_secret_unused, run_id="async-evidence-1")
        assert result.status == "SUCCESS" and result.outputs == {"balance": "$1,200.00"}
        check_result(bal, result)

        xurl = "/transfer.htm"
        xfer_surface = AsyncFakeSurface()
        xfer_surface.set_page(xurl, "Transfer Funds\nAmount: From account #: To account #:")
        xfer_type, xfer_sel1, xfer_sel2, xfer_click, xfer_extract = (s for s in xfer.steps if s.action != "navigate")
        xfer_surface.register(xurl, xfer_type.target.primary, 10)
        xfer_surface.register(xurl, xfer_sel1.target.primary, 11)
        xfer_surface.register(xurl, xfer_sel2.target.primary, 12)
        xfer_surface.register(xurl, xfer_click.target.primary, 13)
        xfer_surface.register(xurl, xfer_extract.target.primary, 14)
        xfer_surface.set_value(14, "Transfer Complete!")
        xfer_surface.click_effects[13] = lambda s: s.set_page(xurl, "Transfer Complete! $20.00 has moved.")
        result = await run_capability_async(
            xfer, xfer_surface, {"from_account": "13344", "to_account": "13355", "amount": "20.00"},
            resolve_secret_unused, run_id="async-evidence-2", auto_approve_limit=500.0,
        )
        assert result.status == "SUCCESS" and result.outputs == {"confirmation": "Transfer Complete!"}
        check_result(xfer, result)

    asyncio.run(run())
