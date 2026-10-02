"""cua.config: the site profile from configs/parabank.yaml, and the notebooks' Config defaults."""

from __future__ import annotations

import dataclasses
from pathlib import Path

import pytest

from cua import config
from cua.config import (
    BrowserConfig,
    DiscoveryConfig,
    OutcomeRule,
    ReplayConfig,
    SiteProfile,
    host_allowed,
    load_site,
    resolve_secret,
    secret_values,
)

HOST = "parabank.parasoft.com"


@pytest.fixture(scope="module")
def site() -> SiteProfile:
    return load_site("parabank")


def test_site_values(site: SiteProfile) -> None:
    assert site.name == "parabank"
    assert site.start_url == f"https://{HOST}/parabank/"
    assert site.base_url == f"https://{HOST}/parabank"
    assert site.allowed_hosts == frozenset({HOST})
    assert dict(site.secret_env) == {
        "username": "PARABANK_USERNAME",
        "password": "PARABANK_PASSWORD",
    }
    assert site.deny_words == frozenset({"register", "lookup", "admin"})
    assert site.login_words == frozenset({"log in"})
    assert site.login_failure_texts == (
        "could not be verified",
        "user does not exist",
        "invalid username or password",
    )
    assert site.login_empty_texts == ("please enter a username and password",)


def test_outcomes_in_order(site: SiteProfile) -> None:
    assert [(o.text, o.status) for o in site.outcomes] == [
        ("not found", "BUSINESS_OUTCOME"),
        ("no such", "BUSINESS_OUTCOME"),
        ("does not exist", "BUSINESS_OUTCOME"),
        ("insufficient funds", "BUSINESS_OUTCOME"),
        ("could not be verified", "BUSINESS_OUTCOME"),
        ("session expired", "RECOVER"),
        ("access denied", "FAILED"),
        ("error", "FAILED"),
    ]
    assert site.outcomes[0] == OutcomeRule(
        "not found", "BUSINESS_OUTCOME", "the item asked for was not found"
    )


def test_outcomes_match_replay_notebook_dicts(site: SiteProfile) -> None:
    """Same rules as replay.py's Config.outcomes, as {text, status, meaning} dicts."""
    assert [dataclasses.asdict(o) for o in site.outcomes][-1] == {
        "text": "error",
        "status": "FAILED",
        "meaning": "the site showed an error page",
    }


def test_site_is_frozen_and_hashable(site: SiteProfile) -> None:
    with pytest.raises(dataclasses.FrozenInstanceError):
        site.name = "x"  # type: ignore[misc]
    assert hash(site) == hash(load_site("parabank"))


def test_unknown_status_is_refused(tmp_path: Path) -> None:
    (tmp_path / "configs").mkdir()
    (tmp_path / "configs/bad.yaml").write_text(
        "start_url: https://a.example/\nallowed_hosts: [a.example]\n"
        "outcomes:\n  - {text: x, status: MAYBE, meaning: m}\n"
    )
    with pytest.raises(ValueError, match="MAYBE"):
        load_site("bad", root=tmp_path)


def test_missing_site_is_a_clear_error(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError, match="nope"):
        load_site("nope", root=tmp_path)


def test_host_allowed(site: SiteProfile) -> None:
    assert host_allowed("about:blank", site)
    assert host_allowed(f"https://{HOST}/parabank/x.htm", site)
    assert not host_allowed("https://evil.example/", site)


def test_resolve_secret(site: SiteProfile, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("PARABANK_USERNAME", "u-fake")
    assert resolve_secret("username", site) == "u-fake"
    with pytest.raises(KeyError):
        resolve_secret("pin", site)
    monkeypatch.setenv("PARABANK_PASSWORD", "")
    with pytest.raises(RuntimeError, match="PARABANK_PASSWORD") as exc:
        resolve_secret("password", site)
    assert "u-fake" not in str(exc.value)


def test_secret_values_maps_name_to_env_value(
    site: SiteProfile, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("PARABANK_USERNAME", "u-fake")
    monkeypatch.delenv("PARABANK_PASSWORD", raising=False)
    assert secret_values(site) == {"username": "u-fake", "password": ""}


def test_browser_defaults() -> None:
    c = BrowserConfig()
    assert (c.viewport, c.ocr_min_score) == ((1280, 800), 0.5)
    assert (c.scroll_px, c.same_screen_mad) == (600, 1.0)
    assert (c.crop_pad, c.point_crop, c.settle_ms) == (6, (160, 34), 600)
    assert c.sensitive_words == frozenset({"password", "ssn", "social"})
    assert (c.ext_s, c.ext_poll_s) == (1.0, 0.5)


def test_discovery_defaults() -> None:
    c = DiscoveryConfig()
    assert (c.send_wait_ms, c.snap_ms, c.handback_s) == (8000, 3000, 120)
    assert (c.login_limit, c.repeat_limit, c.unsure_limit, c.step_budget) == (3, 3, 3, 40)
    assert (c.run_timeout_s,) == (900,)


def test_replay_defaults() -> None:
    c = ReplayConfig()
    assert (c.fuzzy, c.template_threshold) == (0.8, 0.8)
    assert (c.template_margin, c.scroll_retries) == (0.05, 1)
    assert (c.check_s, c.poll_ms, c.snap_s, c.page_s, c.gate_s) == (5.0, 200, 3.0, 2.0, 120.0)
    assert (c.field_min, c.short_value, c.near_px) == ((40, 16), 2, 60.0)


@pytest.mark.parametrize("cls", [BrowserConfig, DiscoveryConfig, ReplayConfig])
def test_configs_are_frozen(cls: type[BrowserConfig]) -> None:
    with pytest.raises(dataclasses.FrozenInstanceError):
        cls().anything = 1  # type: ignore[attr-defined]


def test_no_site_constants_left() -> None:
    for name in ("BASE", "ALLOWED_HOSTS", "SECRETS", "APP_ID", "SESSION_EXPIRED_TEXT"):
        assert not hasattr(config, name), name


def test_parabank_lists_its_allowed_actions(site: SiteProfile) -> None:
    assert site.allowed_actions == config.STEP_ACTIONS


def test_allowed_actions_default_to_all(tmp_path: Path) -> None:
    (tmp_path / "configs").mkdir()
    (tmp_path / "configs/s.yaml").write_text("start_url: https://a.example/\nallowed_hosts: [a]\n")
    assert load_site("s", root=tmp_path).allowed_actions == config.STEP_ACTIONS


def test_allowed_actions_subset_and_unknown(tmp_path: Path) -> None:
    (tmp_path / "configs").mkdir()
    base = "start_url: https://a.example/\nallowed_hosts: [a]\nallowed_actions: "
    (tmp_path / "configs/s.yaml").write_text(base + "[click, extract]\n")
    assert load_site("s", root=tmp_path).allowed_actions == {"click", "extract"}
    (tmp_path / "configs/bad.yaml").write_text(base + "[click, teleport]\n")
    with pytest.raises(ValueError, match="teleport"):
        load_site("bad", root=tmp_path)
