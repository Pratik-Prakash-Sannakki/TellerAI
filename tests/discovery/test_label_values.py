"""OCR joins a label to the dropdown beside it ('to account #16785') and reads its border as [ ].
Labels are cleaned of values and brackets; a value left in a label refuses the save; one dropdown
chosen by the agent and carried by the send is one step (live: transfer_money_between_accounts)."""
import ast
import asyncio
import re
from dataclasses import dataclass, replace
from pathlib import Path
from types import SimpleNamespace

import pytest

from tests.discovery.test_save_artifact import NS, SENT, START, _ev, _meta

SRC = Path(__file__).parents[2] / "notebooks/discovery/discovery.py"
TRANSFER = "https://parabank.parasoft.com/parabank/transfer.htm"
LABEL_FNS = {"Box", "Element", "Look", "element_at", "label_near", "spot", "where", "norm",
             "clean_label", "redactor", "_num"}


def _look_ns(values: set[str]) -> dict:
    tree = ast.parse(SRC.read_text())
    keep = [n for n in tree.body if getattr(n, "name", None) in LABEL_FNS
            or (isinstance(n, ast.Assign) and getattr(n.targets[0], "id", "") == "NUMBER")]
    ns: dict = {"dataclass": dataclass, "replace": replace, "re": re, "run_values": lambda: values,
                "__name__": "discovery_labels"}
    exec(compile(ast.Module(keep, []), str(SRC), "exec"), ns)
    return ns


def _where(values: set[str], *texts: tuple[str, tuple[int, int, int, int]], at=(300, 70)) -> dict:
    ns = _look_ns(values)
    els = tuple(ns["Element"](i, t, ns["Box"](*b)) for i, (t, b) in enumerate(texts, 1))
    return ns["where"](ns["Look"](b"", b"", els, "u"), at)


def test_a_sent_value_joined_to_a_label_is_cut_from_it_and_from_the_input_name() -> None:
    got = _where({"16785"}, ("to account #16785", (10, 60, 200, 80)))
    assert got["label"] == "to account #" and got["anchor"]["text"] == "to account #"
    assert NS["input_name"](got["label"]) == "to_account"
    assert "16785" not in str(got)


@pytest.mark.parametrize(("ocr", "label"), [("From account #[", "From account #"),
                                             ("]to account #[", "to account #"),
                                             ("| Amount: $", "Amount: $")])
def test_a_box_border_read_as_a_bracket_is_not_part_of_the_label(ocr, label) -> None:
    assert _where(set(), (ocr, (10, 60, 200, 80)))["label"] == label


def test_a_label_that_is_only_a_value_falls_back_to_the_next_nearest() -> None:
    got = _where({"16785"}, ("Transfer to", (10, 20, 120, 40)), ("[16785]", (10, 60, 120, 80)),
                 at=(200, 70))
    assert got["label"] == "Transfer to"


def test_sent_values_count_as_run_values() -> None:
    tree = ast.parse(SRC.read_text())
    keep = [n for n in tree.body if getattr(n, "name", None) in {"run_values", "norm"}]
    handoff = SimpleNamespace(typed_texts=set(), given=[], entered={}, redact={"16785"})
    ns = {"HANDOFF": handoff, "SECRETS": {"password": "pw"}}
    exec(compile(ast.Module(keep, []), str(SRC), "exec"), ns)
    assert "16785" in ns["run_values"]()


@pytest.mark.parametrize("where_it_hides", ["label", "hint", "own"])
def test_a_value_inside_a_label_refuses_the_save(where_it_hides) -> None:
    text = "to account #16785"
    ev = _ev("select_option", {"hint": text if where_it_hides == "hint" else "to account #"},
             "Selected.", label=text if where_it_hides == "label" else "to account #",
             own=text if where_it_hides == "own" else None, url=TRANSFER)
    log = [START, ev]
    NS["flag_leaks"](log, {"16785"})
    with pytest.raises(ValueError, match="value typed this run") as err:
        NS["build_capability"](log, _meta(name="transfer"))
    assert "16785" not in str(err.value)


def test_a_number_that_only_resembles_a_value_is_not_a_leak() -> None:
    log = [START, _ev("select_option", {}, "Selected.", label="to account #", url=TRANSFER)]
    NS["flag_leaks"](log, {"167", "account 1"})
    assert not log[1].get("leak")


def _select(label: str, point: tuple[int, int], **extra) -> dict:
    return {**_ev("select_option", {"ref": 5, "x": None, "y": None}, "Selected.", label=label,
                  url=TRANSFER), "point": point, **extra}


def test_the_agents_select_and_the_same_sent_dropdown_are_one_step() -> None:
    """Live: steps 5-6 (agent, 'From account #[') and 7-8 (send, 'From account #') were 4 selects."""
    log = [START,
           _select("From account #[", (560, 300)), _select("]to account #[", (560, 340)),
           _select("From account #", (620, 300), dropdown=True, field_box=[540, 290, 700, 310]),
           _select("to account #", (620, 340), dropdown=True, field_box=[540, 330, 700, 350]), SENT,
           {**_ev("click", {"ref": 8, "x": None, "y": None}, "Clicked 'Transfer'.", own="TRANSFER",
                  text="TRANSFER", landed=["Transfer Complete!"]), "url": TRANSFER}]
    cap = NS["build_capability"](log, _meta(name="transfer"))
    assert [s.action for s in cap.steps] == ["select", "select", "click"]
    assert [s.target.anchor.label for s in cap.steps[:2]] == ["From account #", "to account #"]


def test_two_dropdowns_far_apart_with_one_label_stay_two_steps() -> None:
    log = [START, _select("Account", (560, 300)), _select("Account", (560, 500)), SENT]
    assert len(NS["build_capability"](log, _meta(name="t")).steps) == 2


def _sent(logged_before: list[dict]) -> list[dict]:
    tree = ast.parse(SRC.read_text())
    names = {"log_sent_dropdowns", "is_select", "field_area", "same_spot"}
    keep = [n for n in tree.body if getattr(n, "name", None) in names
            or (isinstance(n, ast.Assign) and getattr(n.targets[0], "id", "") == "FIELD_GAP")]
    events = list(logged_before)
    stash = [{"value": "16785", "text": "16785", "options": ["16785"], "at": [620, 300],
              "box": [540, 290, 700, 310]}]
    ns = {"HANDOFF": SimpleNamespace(dropdowns=stash, log=events), "urlparse": __import__("urllib.parse").parse.urlparse,
          "where": lambda look, p: {"label": "From account #"}, "cut_crop": lambda *a: b"",
          "Look": object,
          "log": lambda tool, args, result, point=None, crop=None, **extra: events.append(
              {"tool": tool, "args": args, "result": result, "point": point, "url": TRANSFER, **extra})}
    exec(compile(ast.Module(keep, []), str(SRC), "exec"), ns)
    asyncio.run(ns["log_sent_dropdowns"](SimpleNamespace(scale=1.0, url=TRANSFER), {"f": "16785"}))
    return events[len(logged_before):]


def test_a_sent_dropdown_the_agent_already_chose_is_not_logged_again() -> None:
    assert _sent([_select("From account #[", (560, 300))]) == []


def test_a_sent_dropdown_the_agent_never_touched_is_logged_with_its_box() -> None:
    (ev,) = _sent([_select("Amount", (560, 500))])
    assert ev["point"] == (620, 300) and ev["field_box"] == [540, 290, 700, 310]
