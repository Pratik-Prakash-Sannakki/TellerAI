"""One form before step 1 asks every input, in step order; only a dropdown mismatch prompts mid-run;
caller inputs by exact name; login capabilities start logged out. Ported from tests/replay/
test_resolve_inputs.py and the ask_inputs/replay parts of test_caller_inputs.py."""

from __future__ import annotations

import dataclasses
from pathlib import Path

import numpy as np
import pytest

from cua.replay import engine, loader, steps
from cua.replay.context import Ctx
from cua.schema import Capability, Step, Stop
from tests.unit.replay.helpers import (
    cap,
    click,
    make_replay_ctx,
    mk_look,
    screen,
    select,
    set_control,
    type_,
    write_cap,
)


def _type(name: str) -> object:
    return type_(f"{{{{{name}}}}}", name, (60, 0))


def _cap(inputs: list[str], steps_: list[object]) -> Capability:
    return cap(steps_, inputs=[{"name": n, "description": f"the {n}"} for n in inputs])


class FakeForm:
    def __init__(self, *answers: object) -> None:
        self.asked: list[tuple[object, object, object]] = []
        self.answers = list(answers)

    async def form(
        self, title: str, fields: object, values: object = None, options: object = None
    ) -> object:
        self.asked.append((fields, values, options))
        return self.answers.pop(0) if self.answers else None


class FakePage:
    def __init__(self, options: list[str] | None = None) -> None:
        self.options, self.picked = list(options or []), None

    async def evaluate(self, js: str, args: list[object]) -> object:
        if args[2] is None:
            return self.options
        self.picked = next((o for o in self.options if o == args[2]), None)
        return [100, 50, self.picked] if self.picked else False

    async def wait_for_timeout(self, ms: float) -> None:
        return None


@pytest.fixture
def env(monkeypatch: pytest.MonkeyPatch) -> tuple[Ctx, list[str]]:
    ctx = make_replay_ctx(FakePage(), FakeForm())
    screen(
        ctx,
        mk_look(
            [
                ("amount", (0, 0, 40, 10)),
                ("from_account", (0, 20, 40, 30)),
                ("Pay", (0, 40, 40, 50)),
                ("Done", (0, 60, 40, 70)),
            ]
        ),
    )
    order: list[str] = []

    def action(name: str):  # noqa: ANN202
        async def act(c: Ctx, step: Step, point: tuple[int, int], cp: Capability) -> bool:
            order.append(name)
            return True

        return act

    monkeypatch.setitem(steps.ACTIONS, "type", action("type"))
    monkeypatch.setitem(steps.ACTIONS, "click", action("click"))
    return ctx, order


@pytest.mark.asyncio
async def test_all_inputs_asked_once_before_step_1_in_step_order(
    env: tuple[Ctx, list[str]],
) -> None:
    ctx, _ = env
    set_control(ctx, form := FakeForm(["5", "74838", "10"]))
    cp = _cap(
        ["amount", "from_account", "payee"],
        [_type("payee"), select("from_account"), _type("amount")],
    )
    assert await loader.ask_inputs(ctx, cp) == {
        "payee": "5",
        "from_account": "74838",
        "amount": "10",
    }
    assert len(form.asked) == 1
    fields, prefill, options = form.asked[0]
    assert [f[0].split(":")[0] for f in fields] == ["payee", "from_account", "amount"]  # type: ignore[attr-defined]
    assert fields[1][0] == "from_account: the from_account (must match an option on the page)"  # type: ignore[index]
    assert prefill is None and options is None


@pytest.mark.asyncio
async def test_blank_field_stops_before_step_1_naming_it(env: tuple[Ctx, list[str]]) -> None:
    ctx, _ = env
    set_control(ctx, FakeForm(["", "10"]))
    with pytest.raises(Stop) as e:
        await loader.ask_inputs(ctx, _cap(["payee", "amount"], [_type("payee"), _type("amount")]))
    assert e.value.status == "STUCK" and e.value.reason == "inputs not given: ['payee']"


@pytest.mark.asyncio
async def test_skipped_form_stops(env: tuple[Ctx, list[str]]) -> None:
    ctx, _ = env
    with pytest.raises(Stop) as e:
        await loader.ask_inputs(ctx, _cap(["amount"], [_type("amount")]))
    assert e.value.reason == "inputs not given: ['amount']"


@pytest.mark.asyncio
async def test_no_form_when_nothing_is_declared(env: tuple[Ctx, list[str]]) -> None:
    ctx, _ = env
    assert await loader.ask_inputs(ctx, _cap([], [click("Pay")])) == {}
    assert ctx.control.asked == []  # type: ignore[attr-defined]


@pytest.mark.asyncio
async def test_a_sensitive_input_is_masked_in_the_form(env: tuple[Ctx, list[str]]) -> None:
    ctx, _ = env
    set_control(ctx, form := FakeForm(["x"]))
    await loader.ask_inputs(ctx, _cap(["ssn"], [_type("ssn")]))
    assert form.asked[0][0] == [("ssn: the ssn", True)]


@pytest.mark.asyncio
async def test_nothing_prompts_mid_run_for_a_typed_input(env: tuple[Ctx, list[str]]) -> None:
    ctx, order = env
    ctx.run.values = {"amount": "10"}
    assert (
        await engine.walk(ctx, _cap(["amount"], [_type("amount")]), None, [])
    ).status == "SUCCESS"
    assert ctx.control.asked == [] and order == ["type"]  # type: ignore[attr-defined]


async def _run_select(
    ctx: Ctx, mp: pytest.MonkeyPatch, options: list[str], *answers: object
) -> bool:
    page = FakePage(options)
    ctx.session = dataclasses.replace(ctx.session, page=page)  # type: ignore[arg-type]
    set_control(ctx, FakeForm(*answers))
    mp.setattr(steps, "read_field", lambda c, look, point: page.picked or "")
    cp = _cap(["from_account"], [select("from_account")])
    return await steps.do_select(ctx, cp.steps[0], (100, 50), cp)


@pytest.mark.asyncio
async def test_dropdown_value_matching_a_live_option_gives_no_prompt(
    env: tuple[Ctx, list[str]], monkeypatch: pytest.MonkeyPatch
) -> None:
    ctx, _ = env
    ctx.run.values = {"from_account": "74838"}
    assert await _run_select(ctx, monkeypatch, ["13344", "74838"]) is True
    assert ctx.control.asked == [] and ctx.page.picked == "74838"  # type: ignore[attr-defined]


@pytest.mark.asyncio
async def test_dropdown_mismatch_gives_one_prompt_with_the_live_options(
    env: tuple[Ctx, list[str]], monkeypatch: pytest.MonkeyPatch
) -> None:
    ctx, _ = env
    ctx.run.values = {"from_account": "7483"}
    assert await _run_select(ctx, monkeypatch, ["13344", "74838"], ["74838"]) is True
    asked = ctx.control.asked  # type: ignore[attr-defined]
    assert len(asked) == 1
    fields, prefill, options = asked[0]
    assert fields == [("from_account: the from_account", False)]
    assert prefill == [""] and options == [["", "13344", "74838"]]
    assert ctx.page.picked == "74838" and ctx.run.values["from_account"] == "74838"  # type: ignore[attr-defined]
    assert ctx.run.given == ["74838"]


@pytest.mark.asyncio
async def test_dropdown_mismatch_answer_must_be_a_live_option(
    env: tuple[Ctx, list[str]], monkeypatch: pytest.MonkeyPatch
) -> None:
    ctx, _ = env
    ctx.run.values = {"from_account": "7483"}
    with pytest.raises(Stop):
        await _run_select(ctx, monkeypatch, ["13344", "74838"], ["7483"])


def test_login_capability_starts_logged_out() -> None:
    login = type_("{{secret:username}}", "U", (0, 0))
    assert engine.starts_with_login(_cap([], [login]))
    assert not engine.starts_with_login(_cap(["amount"], [_type("amount")]))


class ClearPage:
    def __init__(self) -> None:
        self.calls: list[str] = []
        self.context = self

    async def clear_cookies(self) -> None:
        self.calls.append("clear")

    async def goto(self, url: str) -> None:
        self.calls.append("goto")

    async def screenshot(self) -> bytes:
        return b""


@pytest.mark.asyncio
async def test_open_start_clears_cookies_before_goto_for_a_login(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    page = ClearPage()
    ctx = make_replay_ctx(page)
    monkeypatch.setattr(engine, "decode", lambda png: np.zeros((800, 1280, 3)))
    await engine.open_start(ctx, _cap([], [type_("{{secret:username}}", "U", (0, 0))]))
    assert page.calls == ["clear", "goto"]


# --- caller inputs (test_caller_inputs.py) -------------------------------------------------


@pytest.mark.asyncio
async def test_all_inputs_given_means_no_form() -> None:
    ctx = make_replay_ctx(control=(form := FakeForm()))
    assert await loader.ask_inputs(ctx, _cap(["amount"], [_type("amount")]), {"amount": "10"}) == {
        "amount": "10"
    }
    assert form.asked == []


@pytest.mark.asyncio
async def test_only_the_missing_inputs_go_to_the_one_form() -> None:
    ctx = make_replay_ctx(control=(form := FakeForm(["Acme"])))
    cp = _cap(["amount", "payee_name"], [_type("amount"), _type("payee_name")])
    assert await loader.ask_inputs(ctx, cp, {"amount": "10"}) == {
        "amount": "10",
        "payee_name": "Acme",
    }
    assert form.asked[0][0] == [("payee_name: the payee_name", False)]


@pytest.mark.asyncio
async def test_replay_stops_on_an_unknown_key_before_opening_the_site(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("PARABANK_USERNAME", "u-secret")
    opened: list[str] = []

    async def open_start(c: Ctx, cp: Capability) -> None:
        opened.append(cp.name)

    async def no_snap(c: Ctx) -> None:
        return None

    monkeypatch.setattr(engine, "open_start", open_start)
    monkeypatch.setattr(engine, "snap", no_snap)
    res = await engine.replay(make_replay_ctx(), write_cap(tmp_path), inputs={"acct": "1"})
    assert (
        res.status == "STUCK"
        and res.reason == "not a permissible input: acct. Accepts: account_id."
    )
    assert opened == []


# --- typed inputs: a given value must match its declared type ---


def _typed_cap(**types: str) -> Capability:
    return cap(
        [_type(n) for n in types],
        inputs=[{"name": n, "type": t, "description": f"the {n}"} for n, t in types.items()],
    )


def test_a_given_value_of_the_declared_type_is_accepted() -> None:
    cp = _typed_cap(amount="currency", when="date", memo="string")
    given = {"amount": "123.45", "when": "2026-01-01", "memo": "anything at all"}
    assert loader.given_inputs(cp, given) == given


def test_a_given_value_of_the_wrong_type_stops_naming_input_and_type() -> None:
    with pytest.raises(Stop) as e:
        loader.given_inputs(_typed_cap(amount="currency"), {"amount": "ten dollars"})
    assert e.value.status == "STUCK"
    assert e.value.reason == "amount must be of type currency"
    assert "ten dollars" not in e.value.reason


def test_the_form_states_each_inputs_type() -> None:
    assert loader.type_hint("currency") == " (currency, e.g. 123.45)"
    assert loader.type_hint("string") == ""


@pytest.mark.asyncio
async def test_a_form_answer_of_the_wrong_type_is_asked_again(
    env: tuple[Ctx, list[str]],
) -> None:
    ctx, _ = env
    set_control(ctx, form := FakeForm(["abc"], ["123.45"]))
    assert await loader.ask_inputs(ctx, _typed_cap(amount="currency")) == {"amount": "123.45"}
    assert len(form.asked) == 2  # noqa: PLR2004
    assert form.asked[0][0] == [("amount: the amount (currency, e.g. 123.45)", False)]
    again = "amount: the amount (currency, e.g. 123.45) -- must be currency"
    assert form.asked[1][0] == [(again, False)]


@pytest.mark.asyncio
async def test_a_form_answer_still_wrong_after_the_retry_stops(
    env: tuple[Ctx, list[str]],
) -> None:
    ctx, _ = env
    set_control(ctx, FakeForm(["abc"], ["abc"]))
    with pytest.raises(Stop) as e:
        await loader.ask_inputs(ctx, _typed_cap(amount="currency"))
    assert e.value.reason == "amount must be of type currency"
