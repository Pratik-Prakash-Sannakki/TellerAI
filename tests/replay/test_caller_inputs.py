"""replay(path, inputs): given values by exact name (any case); unknown keys stop; only the rest is asked."""
import asyncio

from test_load_inputs import CAP, _write


def _cap(ns, inputs):
    steps = [ns["SCHEMA"]["Type"](value=f"{{{{{n}}}}}", target={"anchor": {"label": n, "offset": [60, 0]}})
             for n in inputs]
    return ns["Capability"](name="t", description="t", base_url="https://parabank.parasoft.com/p",
                            viewport=(1280, 800), inputs=[{"name": n, "description": f"the {n}"} for n in inputs],
                            steps=steps, checkpoint="Done")


class FakeForm:
    def __init__(self, answer=None) -> None:
        self.asked, self.answer = [], answer

    async def form(self, title, fields, values=None, options=None):
        self.asked.append(fields)
        return self.answer


def test_all_inputs_given_means_no_form(ns) -> None:
    ns["CONTROL"] = form = FakeForm()
    cap = _cap(ns, ["amount"])
    assert asyncio.run(ns["ask_inputs"](cap, {"amount": "10"})) == {"amount": "10"} and form.asked == []


def test_only_the_missing_inputs_go_to_the_one_form(ns) -> None:
    ns["CONTROL"] = form = FakeForm(["Acme"])
    cap = _cap(ns, ["amount", "payee_name"])
    assert asyncio.run(ns["ask_inputs"](cap, {"amount": "10"})) == {"amount": "10", "payee_name": "Acme"}
    assert form.asked == [[("payee_name: the payee_name", False)]]


def test_replay_stops_on_an_unknown_key_before_opening_the_site(ns, tmp_path) -> None:
    opened = []

    async def open_start(cap):
        opened.append(cap.name)

    async def snap():
        return None

    ns.update(open_start=open_start, snap=snap)
    res = asyncio.run(ns["replay"](str(_write(tmp_path, CAP)), inputs={"acct": "1"}))
    assert res.status == "STUCK" and res.reason == "not a permissible input: acct. Accepts: account_id."
    assert opened == []
