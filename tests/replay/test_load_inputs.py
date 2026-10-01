"""Shared CAP fixture + _write helper for the old ast-exec tests still in this folder.

step 4 (src/cua/replay) ported every test that used to live in this file (load_capability,
fill, secret_name) to tests/unit/replay/test_loader.py; this file is kept, with no tests of its
own, only because test_caller_inputs.py / test_cleanup.py / test_outcomes.py /
test_replay_evidence.py / test_table_replay.py still import CAP/_write from it to exercise
ask_inputs/replay/walk/do_extract_table/save_evidence (none of those are step 4's scope).
"""

import yaml

CAP = {"schema_version": 2, "name": "get_balance", "description": "Read a balance.", "base_url": "https://parabank.parasoft.com/parabank",
       "viewport": [1280, 800], "device_scale_factor": 1,
       "inputs": [{"name": "account_id"}],
       "outputs": [{"name": "balance", "type": "currency", "description": "Balance"}], "secrets": ["username"],
       "steps": [{"action": "type", "value": "{{secret:username}}",
                  "target": {"anchor": {"label": "Username", "offset": [150, 0]}, "template": "crops/s0.png"}},
                 {"action": "extract", "save_as": "balance",
                  "target": {"table_cell": {"row_key": "{{account_id}}", "column": "Balance"}}}],
       "checkpoint": "Accounts Overview"}


def _write(tmp_path, cap: dict):
    (tmp_path / "crops").mkdir(exist_ok=True)
    (tmp_path / "crops/s0.png").write_bytes(b"png")
    path = tmp_path / "cap.yaml"
    path.write_text(yaml.safe_dump(cap))
    return path

