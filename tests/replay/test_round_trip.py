"""Discovery's saved artifact runs in replay unchanged: build -> save -> load -> locate/dispatch."""
import importlib.util
from pathlib import Path

_spec = importlib.util.spec_from_file_location(
    "discovery_save_fixtures", Path(__file__).parents[1] / "discovery/test_save_artifact.py")
D = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(D)

LOG = [*D.LOGIN,
       D._ev("request_value", {"hint": "Zip Code:"}, "human entry", label="Zip Code:",
             human_entry=True, dropdown=False),
       D._ev("extract_value", {"ref": 9, "save_as": "first_balance", "value_type": "currency",
                               "description": "Balance"}, "saved", label="Balance",
             table={"row_key": "13344", "column": "Balance"})]


def _saved(tmp_path: Path) -> Path:
    cap = D.NS["build_capability"](LOG, D._meta())
    return D.NS["save_artifact"](cap, D.NS["crops_for"](LOG, cap), tmp_path)


def test_saved_artifact_loads_as_is(ns, tmp_path) -> None:
    cap, crops = ns["load_capability"](_saved(tmp_path))
    assert cap.name == "login" and crops == tmp_path
    assert cap.checkpoint == "Accounts Overview"


def test_steps_dispatch_to_replay_handlers(ns, tmp_path) -> None:
    cap, _ = ns["load_capability"](_saved(tmp_path))
    handlers = [ns["ACTIONS"][s.action].__name__ for s in cap.steps]
    assert handlers == ["do_type", "do_type", "do_click", "do_type", "do_extract"]


def test_rung2_offset_hits_the_point_discovery_acted_on(ns, mk_look, tmp_path) -> None:
    cap, crops = ns["load_capability"](_saved(tmp_path))
    ev = D.LOGIN[1]                                   # typed at ev["point"], label box ev["anchor"]["box"]
    look = mk_look([("Username", tuple(ev["anchor"]["box"]))])
    assert ns["locate"](look, cap.steps[0].target, {}, crops) == (ev["point"], "rung2")


def test_crop_paths_resolve_to_saved_files(ns, tmp_path) -> None:
    cap, crops = ns["load_capability"](_saved(tmp_path))
    rel = [s.target.template for s in cap.steps if getattr(s, "target", None) and s.target.template]
    assert rel == ["crops/login/s0.png", "crops/login/s1.png", "crops/login/s2.png", "crops/login/s3.png"]
    assert all((crops / r).read_bytes() == D.PNG for r in rel)
