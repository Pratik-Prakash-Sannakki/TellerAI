"""landed (step 8b). The act/wait_for_change tests moved to tests/unit/discovery/test_wiring.py."""
import ast
from pathlib import Path
from types import SimpleNamespace

SRC = Path(__file__).parents[2] / "notebooks/discovery/discovery.py"


def test_landed_keeps_only_new_fixed_text() -> None:
    tree = ast.parse(SRC.read_text())
    keep = [n for n in tree.body if getattr(n, "name", None) in {"landed", "norm"}]
    import re
    ns = {"re": re, "Look": object, "HANDOFF": SimpleNamespace(given=["Jane Doe"], typed_texts={"42"})}
    exec(compile(ast.Module(keep, []), str(SRC), "exec"), ns)
    look = lambda *texts: SimpleNamespace(text=" ".join(texts), elements=[SimpleNamespace(text=t) for t in texts])  # noqa: E731
    before = look("Bill Payment Service", "Request Loan")
    after = look("Bill Payment Complete", "Bill Payment to Jane Doe in the amount of $42.00", "13344",
                 "Request Loan")
    assert ns["landed"](before, after) == ["Bill Payment Complete"]
