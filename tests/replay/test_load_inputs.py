"""Loading the artifact as saved, and the inputs."""
import pytest
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


def test_yaml_loads_with_crops_relative(ns, tmp_path) -> None:
    cap, crops = ns["load_capability"](_write(tmp_path, CAP))
    assert cap.name == "get_balance" and crops == tmp_path
    assert cap.steps[0].target.anchor.offset == (150, 0)


def test_viewport_mismatch_refused(ns, tmp_path) -> None:
    with pytest.raises(ns["Stop"]) as err:
        ns["load_capability"](_write(tmp_path, CAP | {"viewport": [1440, 900]}))
    assert err.value.status == "FAILED" and "1440" in err.value.reason


def test_undeclared_input_refused(ns, tmp_path) -> None:
    with pytest.raises(ns["Stop"], match="undeclared"):
        ns["load_capability"](_write(tmp_path, CAP | {"inputs": []}))


def test_fill_inputs_keeps_secrets_out(ns) -> None:
    assert ns["fill"]("acct {{account_id}} {{secret:password}}", {"account_id": "13344"}) == \
        "acct 13344 {{secret:password}}"
    assert ns["secret_name"]("{{secret:password}}") == "password"
    assert ns["secret_name"]("{{account_id}}") is None

