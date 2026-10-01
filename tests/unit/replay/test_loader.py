"""cua.replay.loader: loading a saved capability and the inputs it needs.

Ported from tests/replay/test_load_inputs.py, test_caller_inputs.py (the given_inputs tests only;
ask_inputs/ask_option/replay need the control window and stay in the old file) and
test_outcomes.py (seen_outcome/load_outcomes only). The notebook's CFG/SECRETS globals are now
explicit `site: SiteProfile` / `cfg: BrowserConfig` parameters.
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from cua.config import BrowserConfig, load_site
from cua.replay import fill, given_inputs, load_capability, load_outcomes, secret_name, seen_outcome
from cua.schema import Anchor, Capability, Input, Stop, Target, Type

VISUAL = Path(__file__).parents[3] / "notebooks/discovery/artifacts/visual"
ARTIFACTS = sorted(VISUAL.glob("*.yaml"))

SITE = load_site("parabank")
CFG = BrowserConfig()

STEP_LOGIN: dict[str, object] = {
    "action": "type",
    "value": "{{secret:username}}",
    "target": {
        "anchor": {"label": "Username", "offset": [150, 0]},
        "template": "crops/s0.png",
    },
}

STEP_EXTRACT: dict[str, object] = {
    "action": "extract",
    "save_as": "balance",
    "target": {"table_cell": {"row_key": "{{account_id}}", "column": "Balance"}},
}

CAP: dict[str, object] = {
    "schema_version": 2,
    "name": "get_balance",
    "description": "Read a balance.",
    "base_url": "https://parabank.parasoft.com/parabank",
    "viewport": [1280, 800],
    "device_scale_factor": 1,
    "inputs": [{"name": "account_id"}],
    "outputs": [{"name": "balance", "type": "currency", "description": "Balance"}],
    "secrets": ["username"],
    "steps": [STEP_LOGIN, STEP_EXTRACT],
    "checkpoint": "Accounts Overview",
}


def _write(tmp_path: Path, cap: dict[str, object]) -> Path:
    (tmp_path / "crops").mkdir(exist_ok=True)
    (tmp_path / "crops/s0.png").write_bytes(b"png")
    path = tmp_path / "cap.yaml"
    path.write_text(yaml.safe_dump(cap))
    return path


@pytest.fixture
def username_set(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("PARABANK_USERNAME", "u-fake")


def test_yaml_loads_with_crops_relative(tmp_path: Path, username_set: None) -> None:
    cap, crops = load_capability(_write(tmp_path, CAP), SITE, CFG)
    assert cap.name == "get_balance"
    assert crops == tmp_path
    step = cap.steps[0]
    assert isinstance(step, Type)
    assert step.target.anchor is not None
    assert step.target.anchor.offset == (150, 0)


def test_viewport_mismatch_refused(tmp_path: Path, username_set: None) -> None:
    with pytest.raises(Stop) as err:
        load_capability(_write(tmp_path, CAP | {"viewport": [1440, 900]}), SITE, CFG)
    assert err.value.status == "FAILED"
    assert "1440" in err.value.reason


def test_undeclared_input_refused(tmp_path: Path, username_set: None) -> None:
    with pytest.raises(Stop, match="undeclared"):
        load_capability(_write(tmp_path, CAP | {"inputs": []}), SITE, CFG)


def test_secret_not_set_refused(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("PARABANK_USERNAME", raising=False)
    with pytest.raises(Stop, match="secrets not set"):
        load_capability(_write(tmp_path, CAP), SITE, CFG)


def test_missing_crop_refused(tmp_path: Path, username_set: None) -> None:
    bad_step: dict[str, object] = {
        "action": "type",
        "value": "{{secret:username}}",
        "target": {
            "anchor": {"label": "Username", "offset": [150, 0]},
            "template": "crops/missing.png",
        },
    }
    cap = {**CAP, "steps": [bad_step, STEP_EXTRACT]}
    with pytest.raises(Stop, match="missing crops"):
        load_capability(_write(tmp_path, cap), SITE, CFG)


def test_fill_inputs_keeps_secrets_out() -> None:
    assert (
        fill("acct {{account_id}} {{secret:password}}", {"account_id": "13344"})
        == "acct 13344 {{secret:password}}"
    )
    assert secret_name("{{secret:password}}") == "password"
    assert secret_name("{{account_id}}") is None


def _cap_with_inputs(names: list[str]) -> Capability:
    return Capability(
        name="t",
        description="t",
        base_url="https://parabank.parasoft.com/p",
        viewport=(1280, 800),
        inputs=[Input(name=n, description=f"the {n}") for n in names],
        steps=[
            Type(value=f"{{{{{n}}}}}", target=Target(anchor=Anchor(label=n, offset=(60, 0))))
            for n in names
        ],
        checkpoint="Done",
    )


def test_given_inputs_match_by_exact_name_any_case() -> None:
    cap = _cap_with_inputs(["amount", "payee_name"])
    assert given_inputs(cap, {"Amount": "10", "PAYEE_NAME": "Acme"}) == {
        "amount": "10",
        "payee_name": "Acme",
    }


def test_unknown_key_stops_naming_what_is_accepted() -> None:
    with pytest.raises(Stop) as e:
        given_inputs(_cap_with_inputs(["amount", "payee_name"]), {"account_id": "1", "payee": "x"})
    assert e.value.status == "STUCK"
    assert (
        e.value.reason == "not a permissible input: account_id, payee. Accepts: amount, payee_name."
    )


def test_text_already_on_screen_before_the_step_is_not_an_outcome() -> None:
    rules = [{"text": r.text, "status": r.status, "meaning": r.meaning} for r in SITE.outcomes]
    assert seen_outcome("Help: error codes", "Help: error codes Pay", rules) is None
    hit = seen_outcome("Pay", "Payment error", rules)
    assert hit is not None
    assert hit["status"] == "FAILED"
    assert seen_outcome("Pay", "Terrorist", rules) is None  # whole words only


def test_yaml_outcomes_replace_the_defaults(tmp_path: Path, username_set: None) -> None:
    rules = [
        {"text": "limit reached", "status": "BUSINESS_OUTCOME", "meaning": "daily limit reached"}
    ]
    path = _write(tmp_path, {**CAP, "outcomes": rules})
    cap, _ = load_capability(path, SITE, CFG)  # the schema itself is unchanged by outcomes:
    assert cap.name == "get_balance"
    assert load_outcomes(path, SITE) == rules
    defaults = [{"text": r.text, "status": r.status, "meaning": r.meaning} for r in SITE.outcomes]
    assert load_outcomes(_write(tmp_path, CAP), SITE) == defaults


def test_unknown_outcome_status_is_refused(tmp_path: Path) -> None:
    path = _write(tmp_path, {**CAP, "outcomes": [{"text": "x", "status": "MAYBE", "meaning": "?"}]})
    with pytest.raises(Stop):
        load_outcomes(path, SITE)


def test_there_are_artifacts_to_check() -> None:
    assert ARTIFACTS


@pytest.mark.parametrize("path", ARTIFACTS, ids=lambda p: p.stem)
def test_every_saved_artifact_loads_with_fake_secrets(
    path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    for env_name in dict(SITE.secret_env).values():
        monkeypatch.setenv(env_name, "fake-value")
    cap, crops = load_capability(path, SITE, CFG)
    assert cap.schema_version == 2  # noqa: PLR2004
    assert crops == path.parent
