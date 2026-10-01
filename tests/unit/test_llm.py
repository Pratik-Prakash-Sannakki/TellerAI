"""Offline tests for `cua.llm.make_chat_model`. No network, no real key.

Default: direct Anthropic (``ANTHROPIC_API_KEY``). A gateway is opt-in: only when both
``ILIAD_BASE_URL`` and ``ILIAD_API_KEY`` are set.
"""

from __future__ import annotations

import os

import pytest

from cua import config, llm

FAKE = "test-key-not-real"
GATEWAY = "https://your-gateway.example/anthropic"
DIRECT = "https://api.anthropic.com"


@pytest.fixture(autouse=True)
def _clean_env(monkeypatch: pytest.MonkeyPatch) -> None:
    for name in (
        "ILIAD_API_KEY",
        "ILIAD_BASE_URL",
        "ANTHROPIC_API_KEY",
        "ANTHROPIC_BASE_URL",
        "SSL_CERT_FILE",
        "REQUESTS_CA_BUNDLE",
    ):
        monkeypatch.delenv(name, raising=False)  # teardown restores any prior value


def _gateway(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ILIAD_BASE_URL", GATEWAY)
    monkeypatch.setenv("ILIAD_API_KEY", FAKE)


def test_no_gateway_env_means_direct_anthropic(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ANTHROPIC_API_KEY", FAKE)
    m = llm.make_chat_model("sonnet")
    assert m.anthropic_api_url.rstrip("/") == DIRECT
    assert m.model == config.SONNET_MODEL_NAME
    assert m.anthropic_api_key.get_secret_value() == FAKE


def test_gateway_env_means_gateway(monkeypatch: pytest.MonkeyPatch) -> None:
    _gateway(monkeypatch)
    m = llm.make_chat_model("haiku")
    assert m.anthropic_api_url == GATEWAY
    assert m.model == config.HAIKU_MODEL_NAME
    assert m.anthropic_api_key.get_secret_value() == FAKE


def test_gateway_key_without_url_is_ignored(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ILIAD_API_KEY", "gateway-only-key")
    monkeypatch.setenv("ANTHROPIC_API_KEY", FAKE)
    m = llm.make_chat_model("sonnet")
    assert m.anthropic_api_url.rstrip("/") == DIRECT
    assert m.anthropic_api_key.get_secret_value() == FAKE


def test_gateway_url_without_key_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ILIAD_BASE_URL", GATEWAY)
    monkeypatch.setenv("ANTHROPIC_API_KEY", FAKE)
    with pytest.raises(RuntimeError, match="ILIAD_API_KEY"):
        llm.make_chat_model("sonnet")


def test_no_hardcoded_gateway_host() -> None:
    assert not hasattr(config, "ILIAD_BASE_URL")
    assert "sonnet" in config.SONNET_MODEL_NAME
    assert "haiku" in config.HAIKU_MODEL_NAME


def test_overrides_pass_through(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ANTHROPIC_API_KEY", FAKE)
    m = llm.make_chat_model("sonnet", max_tokens=123)
    assert m.max_tokens == 123


def test_key_never_in_repr(monkeypatch: pytest.MonkeyPatch) -> None:
    _gateway(monkeypatch)
    m = llm.make_chat_model("sonnet")
    assert FAKE not in repr(m)
    assert FAKE not in str(m)


def test_missing_key_raises_clear_error() -> None:
    with pytest.raises(RuntimeError) as exc:
        llm.make_chat_model("sonnet")
    assert "ANTHROPIC_API_KEY is not set" in str(exc.value)


def test_unknown_kind_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ANTHROPIC_API_KEY", FAKE)
    with pytest.raises(ValueError) as exc:
        llm.make_chat_model("opus")  # type: ignore[arg-type]
    assert FAKE not in str(exc.value)


def test_ca_bundle_passthrough(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:  # noqa: ANN001
    bundle = tmp_path / "ca.pem"
    _gateway(monkeypatch)
    monkeypatch.setenv("REQUESTS_CA_BUNDLE", str(bundle))
    llm.make_chat_model("sonnet")
    assert os.environ["SSL_CERT_FILE"] == str(bundle)


def test_existing_ssl_cert_file_wins(monkeypatch: pytest.MonkeyPatch) -> None:
    _gateway(monkeypatch)
    monkeypatch.setenv("SSL_CERT_FILE", "/a.pem")
    monkeypatch.setenv("REQUESTS_CA_BUNDLE", "/b.pem")
    llm.make_chat_model("sonnet")
    assert os.environ["SSL_CERT_FILE"] == "/a.pem"


def test_models_shim_is_gone() -> None:
    with pytest.raises(ModuleNotFoundError):
        __import__("cua.models")
