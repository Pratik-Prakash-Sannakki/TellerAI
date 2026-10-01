"""Discovery's saved artifact runs in replay unchanged: build -> save -> load -> locate/dispatch.
Ported from tests/replay/test_round_trip.py (tests may import both sides; src never does)."""

from __future__ import annotations

from pathlib import Path

import pytest

from cua.config import BrowserConfig, ReplayConfig, load_site
from cua.discovery.recorder import build_capability, crops_for, save_artifact
from cua.replay import load_capability, locate
from cua.replay.steps import ACTIONS
from cua.schema import CapabilityMeta
from cua.vision import Box, Element, Look

SITE = load_site("parabank")
PNG = b"\x89PNG fake"
START = {
    "tool": "start",
    "args": {
        "base_url": "https://parabank.parasoft.com/parabank",
        "viewport": [1280, 800],
        "device_scale_factor": 1,
    },
    "result": "run started",
    "point": None,
    "url": "https://parabank.parasoft.com/parabank/",
    "crop": None,
}


def _ev(
    tool: str,
    args: dict[str, object],
    result: str,
    label: str | None = None,
    own: str | None = None,
    **extra: object,
) -> dict[str, object]:
    ev: dict[str, object] = {
        "tool": tool,
        "args": args,
        "result": result,
        "point": (300, 200),
        "url": "https://parabank.parasoft.com/parabank/index.htm",
        "crop": PNG,
        **extra,
    }
    if label:
        ev["anchor"] = {"text": label, "box": [100, 190, 180, 210], "ordinal": 1}
        ev["offset"] = [160, 0]
        ev["label"] = label
    if own:
        ev["own"] = {"text": own, "box": [280, 190, 320, 210], "ordinal": 1}
    return ev


LOGIN = [
    START,
    _ev(
        "type_secret",
        {"secret_name": "username"},
        "Typed secret 'username' at (300, 200).",
        label="Username",
    ),
    _ev(
        "type_secret",
        {"secret_name": "password"},
        "Typed secret 'password' at (300, 230).",
        label="Password",
    ),
    _ev(
        "click",
        {"ref": 7, "x": None, "y": None},
        "Clicked 'Log In'.",
        label="Log In",
        own="Log In",
        text="Log In",
    ),
]
LOG = [
    *LOGIN,
    _ev(
        "request_value",
        {"hint": "Zip Code:"},
        "human entry",
        label="Zip Code:",
        human_entry=True,
        dropdown=False,
    ),
    _ev(
        "extract_value",
        {"ref": 9, "save_as": "first_balance", "value_type": "currency", "description": "Balance"},
        "saved",
        label="Balance",
        table={"row_key": "13344", "column": "Balance"},
    ),
]


@pytest.fixture
def saved(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    monkeypatch.setenv("PARABANK_USERNAME", "u-fake")
    monkeypatch.setenv("PARABANK_PASSWORD", "p-fake")
    meta = CapabilityMeta(name="login", description="Log in.", success_text="Accounts Overview")
    cap = build_capability(LOG, meta)  # type: ignore[arg-type]
    return save_artifact(cap, crops_for(LOG, cap), tmp_path)  # type: ignore[arg-type]


def test_saved_artifact_loads_as_is(saved: Path) -> None:
    cap, crops = load_capability(saved, SITE, BrowserConfig())
    assert cap.name == "login" and crops == saved.parent
    assert cap.checkpoint == "Accounts Overview"


def test_steps_dispatch_to_replay_handlers(saved: Path) -> None:
    cap, _ = load_capability(saved, SITE, BrowserConfig())
    assert [ACTIONS[s.action].__name__ for s in cap.steps] == [
        "do_type",
        "do_type",
        "do_click",
        "do_type",
        "do_extract",
    ]


def test_rung2_offset_hits_the_point_discovery_acted_on(saved: Path) -> None:
    cap, crops = load_capability(saved, SITE, BrowserConfig())
    ev = LOGIN[1]
    look = Look(b"", b"", (Element(1, "Username", Box(*ev["anchor"]["box"])),), "")  # type: ignore[index]
    assert locate(look, cap.steps[0].target, {}, crops, ReplayConfig()) == (ev["point"], "rung2")  # type: ignore[union-attr]


def test_crop_paths_resolve_to_saved_files(saved: Path) -> None:
    cap, crops = load_capability(saved, SITE, BrowserConfig())
    rel = [s.target.template for s in cap.steps if getattr(s, "target", None) and s.target.template]  # type: ignore[union-attr]
    assert rel == [
        "crops/login/s0.png",
        "crops/login/s1.png",
        "crops/login/s2.png",
        "crops/login/s3.png",
    ]
    assert all((crops / r).read_bytes() == PNG for r in rel)  # type: ignore[operator]
