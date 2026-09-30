"""Banking rule: no typed or human-given value is stored. Source-level checks on the notebook."""
import ast
from pathlib import Path

SRC = Path(__file__).parents[2] / "notebooks/discovery/discovery.py"
TREE = ast.parse(SRC.read_text())


def _log_calls(tool: str) -> list[ast.Call]:
    return [n for n in ast.walk(TREE) if isinstance(n, ast.Call) and getattr(n.func, "id", "") == "log"
            and n.args and isinstance(n.args[0], ast.Constant) and n.args[0].value == tool]


def _arg_keys(call: ast.Call) -> set[str]:
    d = call.args[1]
    return {k.value for k in d.keys} if isinstance(d, ast.Dict) else set()


def test_typed_and_selected_values_never_reach_the_log() -> None:
    for tool, banned in [("type_text", {"text"}), ("select_option", {"option"}),
                         ("type_secret", {"value"}), ("request_value", {"value"})]:
        for call in _log_calls(tool):
            assert not (_arg_keys(call) & banned), f"{tool} logs a value"


def test_no_saved_form() -> None:
    assert "last_form" not in SRC.read_text()


def test_run_goal_wipes_working_values() -> None:
    fn = next(n for n in TREE.body if getattr(n, "name", None) == "run_goal")
    src = ast.unparse(fn)
    assert "finally" in src and "HANDOFF.entered" in src and "HANDOFF.given" in src
