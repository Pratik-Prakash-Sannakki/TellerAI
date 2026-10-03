"""SendGuard: nothing that sends data leaves the tab without two human approvals.

Each case runs the new guard (discovery- and replay-configured) and the notebook's own
``guard_send`` (ast-exec) on the same inputs, and compares verdicts, route calls and prompts.
"""

from __future__ import annotations

import asyncio
import json
from dataclasses import dataclass, field
from types import SimpleNamespace

import pytest

from cua.safety.mismatch import dropdown_options, mismatches
from cua.safety.redact import is_sensitive
from cua.safety.send_guard import DISCOVERY_OPTIONS, REPLAY_OPTIONS, SendGuard, SendHooks
from tests.fakes import FakeControl, FakePage, FakeRoute
from tests.unit.safety._notebook import DISCOVERY, REPLAY, load

WORDS = frozenset({"password", "ssn", "social"})
URL = "https://x/services/bank/transfer"
STASH = [{"value": "1450", "text": "1450", "options": ["1450", "1400"]}]


class Control(FakeControl):
    """Records every prompt (title, image) and every form; scripted answers."""

    def __init__(self, *answers: str | None, form: list[str] | None = None) -> None:
        super().__init__()
        self.queue = list(answers)
        self.prompts: list[tuple[str, bytes | None]] = []
        self.forms: list[tuple[object, ...]] = []
        self.form_answer = form

    async def ask(  # type: ignore[override]
        self, title: str, text: str, kind: str, image: bytes | None = None
    ) -> str | None:
        self.prompts.append((title, image))
        return self.queue.pop(0) if self.queue else None

    async def form(
        self,
        title: str,
        rows: list[tuple[str, bool]],
        values: list[str] | None = None,
        options: list[list[str]] | None = None,
    ) -> list[str] | None:
        self.forms.append((title, rows, values, options))
        return self.form_answer


@dataclass
class State:
    goal: str = ""
    given: list[str] = field(default_factory=list)
    allow_send: bool = False
    takeover: object = None
    look: object = None
    dropdowns: list[dict[str, object]] = field(default_factory=lambda: [dict(d) for d in STASH])
    verdict: str = ""
    sent: bool = False
    gated: bool = False
    joined_goal: bool = True
    redact: set[str] = field(default_factory=set)  # discovery's notebook guard writes these two
    entered: dict[str, str] = field(default_factory=dict)

    def given_text(self) -> str:
        return " ".join([self.goal, *self.given] if self.joined_goal else self.given)


def _route(method: str, body: str | None) -> FakeRoute:
    return FakeRoute(method, URL, body)


def _new(side: str, st: State, ctl: Control) -> SendGuard:
    calls: list[str] = []
    st.log = calls  # type: ignore[attr-defined]
    if side == "discovery":

        async def on_sent(req: object, original: object, fields: object, look: object) -> None:
            calls.append("on_sent")

        hooks = SendHooks(on_sent=on_sent, after_verdict=lambda *a: calls.append("after"))
        return SendGuard(st, ctl, {}, WORDS, hooks, options=DISCOVERY_OPTIONS)

    def on_request(req: object) -> None:
        st.sent = True

    def on_gated() -> None:
        st.gated = True

    hooks = SendHooks(on_request=on_request, on_gated=on_gated)
    return SendGuard(st, ctl, {}, WORDS, hooks, options=REPLAY_OPTIONS)


async def _no_dropdowns(look: object, sent: object) -> None:
    return None


def _old(side: str, st: State, ctl: Control) -> dict:
    names = {"guard_send", "_flat", "_json", "sent_fields", "rebuilt", "pretty"}
    common = {
        "CONTROL": ctl,
        "SEND_GATE": asyncio.Lock(),
        "hide_secrets": lambda t: t,
        "is_sensitive": lambda k: is_sensitive(k, WORDS),
        "mismatches": lambda f: mismatches(f, st.given_text(), WORDS),
    }
    if side == "discovery":

        async def opts(fields: dict[str, str], keys: list[str]) -> list[list[str]]:
            return dropdown_options(fields, keys, st.dropdowns, lambda t: t)

        return load(
            DISCOVERY,
            names,
            HANDOFF=st,
            DECLINED=DISCOVERY_OPTIONS.decline_text,
            dropdown_options=opts,
            log=lambda *a, **k: None,
            log_sent_dropdowns=_no_dropdowns,
            **common,
        )
    return load(
        REPLAY,
        names | {"note_takeover_send"},
        STATE=st,
        url_path=lambda u: u,
        dropdown_options=lambda f, k: dropdown_options(f, k, st.dropdowns, lambda t: t),
        **common,
    )


SIDES = ["discovery", "replay"]
CASES = {
    # name: (method, body, given, answers, form answer, allow_send)
    "get": ("GET", None, [], [], None, False),
    "allow_send": ("POST", "amount=10", [], [], None, True),
    "approve": (
        "POST",
        "amount=10&fromAccountId=1400",
        ["10", "1400"],
        ["approve", "approve"],
        None,
        False,
    ),
    "mismatch_fixed": (
        "POST",
        "amount=10&fromAccountId=1450",
        ["10"],
        ["approve", "approve"],
        ["1400"],
        False,
    ),
    "mismatch_blank": ("POST", "amount=10&fromAccountId=1450", ["10"], [], [""], False),
    "gate1_closed": ("POST", "amount=10", ["10"], [None], None, False),
    "gate1_edit": (
        "POST",
        "amount=10&fromAccountId=1400",
        ["10", "1400"],
        ["edit", "approve", "approve"],
        ["25", "1400"],
        False,
    ),
    "gate2_decline": ("POST", "amount=10", ["10"], ["approve", "reject"], None, False),
}


def _state(side: str, given: list[str], allow: bool, takeover: object = None) -> State:
    return State(
        given=list(given),
        allow_send=allow,
        takeover=takeover,
        look=SimpleNamespace(png=b"shot"),
        joined_goal=side == "discovery",
    )


def _play(side: str, case: str, new: bool, takeover: object = None):
    method, body, given, answers, form, allow = CASES[case]
    st, ctl, route = (
        _state(side, given, allow, takeover),
        Control(*answers, form=form),
        _route(method, body),
    )
    handler = _new(side, st, ctl) if new else _old(side, st, ctl)["guard_send"]
    asyncio.run(asyncio.wait_for(handler(route), 2))
    return st, ctl, route


@pytest.mark.parametrize("side", SIDES)
@pytest.mark.parametrize("case", list(CASES))
def test_each_side_matches_its_notebook(side: str, case: str) -> None:
    new, old = _play(side, case, True), _play(side, case, False)
    (st, ctl, route), (st0, ctl0, route0) = new, old
    assert st.verdict == st0.verdict
    assert route.calls == route0.calls
    assert ctl.prompts == ctl0.prompts
    assert ctl.forms == ctl0.forms
    assert st.given == st0.given
    assert (st.sent, st.gated) == (st0.sent, st0.gated)


@pytest.mark.parametrize("side", SIDES)
@pytest.mark.parametrize("case", ["approve", "gate1_edit", "gate2_decline"])
def test_a_human_send_during_a_take_over_matches_its_notebook(side: str, case: str) -> None:
    takeover = [] if side == "discovery" else {"sends": []}
    (st, ctl, route), (st0, ctl0, route0) = (
        _play(side, case, True, takeover),
        _play(side, case, False, type(takeover)(takeover)),
    )
    assert (st.verdict, route.calls, ctl.prompts, ctl.forms) == (
        st0.verdict,
        route0.calls,
        ctl0.prompts,
        ctl0.forms,
    )


def test_verdict_strings() -> None:
    got = {c: _play("discovery", c, True)[0].verdict for c in CASES}
    assert got["approve"] == "SENT: a human approved both gates."
    assert got["mismatch_blank"].startswith("STUCK: No value confirmed for fromAccountId")
    assert got["gate1_closed"] == "STUCK: the details were not confirmed. Nothing was sent."
    assert got["gate2_decline"].startswith("DECLINED by a human.")
    rep = _play("replay", "gate2_decline", True)[0].verdict
    assert rep == "DECLINED: a human said no at Gate 2. Nothing was sent."


def test_discovery_hooks_run_on_sent_before_after_verdict() -> None:
    st, _, route = _play("discovery", "approve", True)
    assert st.log == ["on_sent", "after"]  # type: ignore[attr-defined]
    assert route.calls[-1][0] == "continue_"


def test_options_differ_only_where_the_notebooks_do() -> None:
    d, r = DISCOVERY_OPTIONS, REPLAY_OPTIONS
    assert (d.human_in_lock, d.image_on_takeover, d.plain_edit_boxes) == (True, False, True)
    assert (r.human_in_lock, r.image_on_takeover, r.plain_edit_boxes) == (False, True, False)


def test_gate1_edit_sends_the_edit_as_json() -> None:
    body = json.dumps({"name": "Acme", "n": 777})
    st = State(given=["777"], look=SimpleNamespace(png=b"shot"))
    ctl = Control("edit", "approve", "approve", form=["Acme Power", "777"])
    route = _route("POST", body)
    asyncio.run(SendGuard(st, ctl, {}, WORDS, SendHooks(), options=DISCOVERY_OPTIONS)(route))
    sent = json.loads(str(route.calls[-1][1]["post_data"]))
    assert sent == {"name": "Acme Power", "n": 777}
    assert [img for _, img in ctl.prompts] == [b"shot", None, None]


def test_secrets_and_sensitive_values_never_reach_the_gate_text() -> None:
    seen: list[str] = []

    class Ctl(Control):
        async def ask(self, title: str, text: str, kind: str, image: bytes | None = None) -> str:
            seen.append(text)
            return "approve"

    st = State()
    route = FakeRoute("POST", "https://x/login", "user=bob&password=hunter2&note=bob")
    guard = SendGuard(st, Ctl(), {"username": "bob"}, WORDS, SendHooks(), options=DISCOVERY_OPTIONS)
    asyncio.run(guard(route))
    assert "hunter2" not in seen[0]
    assert "Password: ******" in seen[0]
    assert "bob" not in seen[0]
    assert "User: <username>" in seen[0]


@pytest.mark.parametrize("opts", [DISCOVERY_OPTIONS, REPLAY_OPTIONS])
def test_a_held_send_never_touches_the_page(opts: object) -> None:
    """Review focus 2: while a send is held, every page call would hang. The guard has no page
    at all; a raise_all page exists alongside and is never called through both gates."""
    page = FakePage(raise_all=True)
    st = State(given=["10"], look=SimpleNamespace(png=b"shot"))
    ctl = Control("edit", "approve", "approve", form=["1400", "10"])
    route = _route("POST", "amount=10&fromAccountId=1450")
    guard = SendGuard(st, ctl, {}, WORDS, SendHooks(), options=opts)  # type: ignore[arg-type]
    asyncio.run(asyncio.wait_for(guard(route), 2))
    assert page.calls == []
    assert route.calls[-1][0] == "continue_"
    assert not any("page" in name for name in vars(guard))


def test_the_lock_is_held_while_the_gates_wait() -> None:
    async def scenario() -> bool:
        release = asyncio.Event()

        class Slow(Control):
            async def ask(self, title: str, text: str, kind: str, image: bytes | None = None):
                await release.wait()
                return "approve"

        st, opts = State(given=["10"]), REPLAY_OPTIONS
        guard = SendGuard(st, Slow(), {}, WORDS, SendHooks(), options=opts)
        task = asyncio.create_task(guard(_route("POST", "amount=10")))
        await asyncio.sleep(0)
        held = guard.lock.locked()
        release.set()
        await task
        return held and not guard.lock.locked()

    assert asyncio.run(scenario())


def test_bill_pay_json_every_field_is_editable_and_sent_back_as_json() -> None:
    body = json.dumps(
        {
            "name": "Acme",
            "address": {"street": "1 Main", "city": "Troy", "zipCode": "12180"},
            "phoneNumber": "5551234",
            "accountNumber": 777,
        }
    )
    st = State(given=["124677", "2", "1", "12180", "5551234", "777"])
    edited = ["124677", "2", "Acme Power", "1 Main", "Troy", "12180", "5551234", "777"]
    ctl = Control("edit", "approve", "approve", form=edited)
    route = FakeRoute("POST", "https://x/services/bank/billpay?accountId=124677&amount=2", body)
    asyncio.run(SendGuard(st, ctl, {}, WORDS, SendHooks(), options=DISCOVERY_OPTIONS)(route))
    names = [
        "Account id",
        "Amount",
        "Name",
        "Address street",
        "Address city",
        "Address zip code",
        "Phone number",
        "Account number",
    ]
    assert [f for f, _ in ctl.forms[0][1]] == names  # type: ignore[attr-defined]
    sent = json.loads(str(route.calls[-1][1]["post_data"]))
    assert sent["name"] == "Acme Power"
    assert sent["address"]["city"] == "Troy"
    assert sent["accountNumber"] == 777  # noqa: PLR2004


@pytest.mark.parametrize(
    ("opts", "images"),
    [
        (DISCOVERY_OPTIONS, [None, None]),  # a human's send: no current look, so no image
        (REPLAY_OPTIONS, [b"last", b"last"]),
    ],
)
def test_a_take_over_send_image_per_side(opts: object, images: list[object]) -> None:
    st = State(takeover=[], look=SimpleNamespace(png=b"last"))
    ctl = Control("approve", "approve")
    guard = SendGuard(st, ctl, {}, WORDS, SendHooks(), options=opts)  # type: ignore[arg-type]
    asyncio.run(guard(_route("POST", "customer.firstName=Ann")))
    assert [img for _, img in ctl.prompts] == images
    assert ctl.forms == []


def test_after_verdict_gets_human_so_discovery_can_keep_the_take_over_path() -> None:
    st = State(takeover=[])

    def keep_path(req: object, original: object, fields: object, human: bool) -> None:
        if human and st.takeover is not None:
            st.takeover.append({"kind": "send", "path": "/services/bank/billpay"})  # type: ignore[attr-defined]

    hooks = SendHooks(after_verdict=keep_path)
    ctl = Control("approve", "approve")
    route = FakeRoute("POST", "https://x/services/bank/billpay?accountId=13344&amount=10", None)
    asyncio.run(SendGuard(st, ctl, {}, WORDS, hooks, options=DISCOVERY_OPTIONS)(route))
    assert st.takeover == [{"kind": "send", "path": "/services/bank/billpay"}]
