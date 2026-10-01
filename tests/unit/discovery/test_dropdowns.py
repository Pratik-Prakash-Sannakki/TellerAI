"""A dropdown the send carries becomes a Select step; the guard hooks never read a held page.

Ported from tests/discovery/test_sent_dropdowns.py and the discovery leftovers of
test_transaction_gates.py (step 6 ported the gates themselves).
"""

from __future__ import annotations

import asyncio
from pathlib import Path

import pytest
import yaml

from cua.config import DiscoveryConfig
from cua.discovery.context import Ctx
from cua.discovery.recorder import build_capability, crops_for, save_artifact
from cua.discovery.tools import dropdowns
from cua.discovery.tools.dropdowns import log_sent_dropdowns
from cua.discovery.wiring import attach, new_run
from cua.vision.look import Box, Element, Look
from tests.fakes import FakeRoute, FakeTab, make_ctx, make_session
from tests.unit.discovery.recorder.test_recorder import LOGIN, SENT, START, _ev, _meta

ACCOUNT = "74838"
BILLPAY = "https://example.test/app/billpay.htm"
STASH = [
    {
        "value": ACCOUNT,
        "text": ACCOUNT,
        "options": [ACCOUNT, "13344"],
        "at": [720, 540],
        "box": [640, 530, 800, 550],
    },
    {"value": "x", "text": "x", "options": ["x"], "at": None, "box": [0, 0, 0, 0]},  # hidden
]
LABEL = Element(1, "From account #:", Box(480, 530, 590, 550))
LOOK = Look(b"", b"", (LABEL,), BILLPAY)


class HeldPage(FakeTab):
    """While a request is held, every page read hangs (the live Register bug)."""

    async def evaluate(self, *a: object) -> object:
        self.calls.append("evaluate")
        await asyncio.sleep(3600)

    async def screenshot(self, **_: object) -> bytes:
        self.calls.append("screenshot")
        await asyncio.sleep(3600)
        return b""


@pytest.fixture(autouse=True)
def _no_crop_pixels(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(dropdowns, "crop", lambda *a: b"crop")


async def _logged(sent: dict[str, str]) -> list[dict[str, object]]:
    ctx = make_ctx(make_session(HeldPage(BILLPAY)))
    ctx.run.dropdowns = [dict(d) for d in STASH]
    await log_sent_dropdowns(ctx, LOOK, sent)
    assert ctx.page.calls == []  # type: ignore[attr-defined]
    return ctx.run.log  # type: ignore[return-value]


@pytest.mark.asyncio
async def test_a_defaulted_dropdown_the_send_carries_is_logged_without_its_value() -> None:
    events = await _logged({"amount": "10", "fromAccountId": ACCOUNT})
    assert len(events) == 1
    assert events[0]["point"] == (720, 540)
    assert events[0]["args"] == {"hint": "From account #:"}
    assert events[0]["dropdown"] is True
    assert events[0]["field_box"] == [640, 530, 800, 550]
    assert events[0]["index"] == 0
    assert ACCOUNT not in str(events[0])


@pytest.mark.asyncio
async def test_a_dropdown_the_send_does_not_carry_is_not_a_step() -> None:
    assert await _logged({"amount": "10"}) == []


@pytest.mark.asyncio
async def test_it_becomes_a_select_input_before_the_send_click(tmp_path: Path) -> None:
    typed = _ev(
        "type_text", {"ref": 3, "x": None, "y": None}, "Typed at (300, 200).", label="Amount:"
    )
    click = _ev(
        "click",
        {"ref": 8, "x": None, "y": None},
        "Clicked 'Send Payment'.",
        label="Amount:",
        own="Send Payment",
        text="Send Payment",
        landed=["Bill Payment Complete"],
    )
    log = [*LOGIN, typed, *await _logged({"amount": "10", "fromAccountId": ACCOUNT}), SENT, click]
    cap = build_capability(log, _meta(name="pay"))  # type: ignore[arg-type]
    assert [s.action for s in cap.steps][-2:] == ["select", "click"]
    assert cap.steps[-2].option == "{{from_account}}"  # type: ignore[union-attr]
    assert cap.steps[-2].target.anchor.label == "From account #:"  # type: ignore[union-attr]
    assert "from_account" in [i.name for i in cap.inputs]
    path = save_artifact(cap, crops_for(log, cap), tmp_path)  # type: ignore[arg-type]
    assert ACCOUNT not in path.read_text()
    assert yaml.safe_load(path.read_text())["steps"][-2]["action"] == "select"


@pytest.mark.asyncio
async def test_a_select_the_agent_made_earlier_is_not_doubled() -> None:
    early = {
        **(await _logged({"a": ACCOUNT}))[0],
        "tool": "select_option",
        "args": {"ref": 5, "x": None, "y": None},
    }
    ctx = make_ctx(make_session(HeldPage(BILLPAY)))
    ctx.run.dropdowns, ctx.run.log = [dict(d) for d in STASH], [START, early]  # type: ignore[list-item]
    await log_sent_dropdowns(ctx, LOOK, {"a": ACCOUNT})
    send = _ev(
        "click",
        {"ref": 8, "x": None, "y": None},
        "Clicked 'Send'.",
        own="Send",
        text="Send",
        landed=["Done"],
    )
    cap = build_capability([*ctx.run.log, SENT, send], _meta(name="pay"))  # type: ignore[list-item]
    assert [s.action for s in cap.steps] == ["select", "click"]


def _reads(page: FakeTab) -> list[str]:
    """Page reads (a held send blocks them); bring_to_front is the control window's own."""
    return [c for c in page.calls if c in {"evaluate", "screenshot"}]


async def _approve(ctx: Ctx, route: FakeRoute, form: str | None = None) -> None:
    task = asyncio.create_task(ctx.guard(route))
    modes = (["form"] if form else []) + ["confirm", "approve"]
    for mode in modes:
        while not any(q[2] == mode for _, q in ctx.control._stack):
            await asyncio.sleep(0.001)
        if mode == "form":
            ctx.control.answer(mode, form)  # type: ignore[arg-type]
        else:
            ctx.control.answer(mode, "approve")
    await asyncio.wait_for(task, 2)


@pytest.mark.asyncio
async def test_a_humans_register_during_a_take_over_needs_no_page_read() -> None:
    """Human values (zip, phone, SSN) are not in the goal: no mismatch form, no dropdown lookup."""
    page = HeldPage(BILLPAY)
    ctx = new_run(await attach(make_session(page), DiscoveryConfig(), {}), "find a way in")
    ctx.run.takeover, ctx.run.look = [], LOOK
    page.calls.clear()
    route = FakeRoute(
        "POST",
        "https://example.test/app/register.htm",
        "customer.address.zipCode=90210&customer.phoneNumber=5551234&customer.ssn=1",
    )
    await _approve(ctx, route)
    assert _reads(page) == []
    assert route.calls[0][0] == "continue_"
    assert ctx.run.takeover == [{"kind": "send", "path": "/app/register.htm"}]


@pytest.mark.asyncio
async def test_an_agent_send_uses_the_stashed_dropdowns_and_never_reads_the_page() -> None:
    page = HeldPage(BILLPAY)
    ctx = new_run(await attach(make_session(page), DiscoveryConfig(), {}), "transfer $10")
    ctx.run.dropdowns = [
        {
            "value": "1450",
            "text": "1450",
            "options": ["1450", "1400"],
            "at": [700, 300],
            "box": [620, 290, 780, 310],
        }
    ]
    ctx.run.look = LOOK
    page.calls.clear()
    route = FakeRoute("POST", "https://x/services/bank/transfer", "amount=10&fromAccountId=1450")
    await _approve(ctx, route, form='["1400"]')
    assert "select_option" in [e["tool"] for e in ctx.run.log]  # the sent dropdown is a step
    assert _reads(page) == []
    assert "fromAccountId=1400" in str(route.calls[0][1]["post_data"])
