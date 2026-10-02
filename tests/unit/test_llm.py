"""Offline tests for `cua.llm.make_chat_model`. No network, no real key.

Direct Anthropic only (``ANTHROPIC_API_KEY``); no gateway of any kind.
"""

from __future__ import annotations

import os

import pytest

from cua import config, llm

FAKE = "test-key-not-real"
ELSEWHERE = "https://your-gateway.example/anthropic"
DIRECT = "https://api.anthropic.com"


@pytest.fixture(autouse=True)
def _clean_env(monkeypatch: pytest.MonkeyPatch) -> None:
    for name in (
        "ANTHROPIC_API_KEY",
        "ANTHROPIC_BASE_URL",
        "SSL_CERT_FILE",
        "REQUESTS_CA_BUNDLE",
    ):
        monkeypatch.delenv(name, raising=False)  # teardown restores any prior value


def test_direct_anthropic(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ANTHROPIC_API_KEY", FAKE)
    m = llm.make_chat_model("sonnet")
    assert m.anthropic_api_url.rstrip("/") == DIRECT
    assert m.model == config.SONNET_MODEL_NAME
    assert m.anthropic_api_key.get_secret_value() == FAKE


def test_haiku_is_direct_too(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ANTHROPIC_API_KEY", FAKE)
    m = llm.make_chat_model("haiku")
    assert m.anthropic_api_url.rstrip("/") == DIRECT
    assert m.model == config.HAIKU_MODEL_NAME


def test_a_base_url_in_the_env_never_redirects(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ANTHROPIC_API_KEY", FAKE)
    monkeypatch.setenv("ANTHROPIC_BASE_URL", ELSEWHERE)
    assert llm.make_chat_model("sonnet").anthropic_api_url.rstrip("/") == DIRECT


def test_model_names_are_fixed() -> None:
    assert "sonnet" in config.SONNET_MODEL_NAME
    assert "haiku" in config.HAIKU_MODEL_NAME


def test_overrides_pass_through(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ANTHROPIC_API_KEY", FAKE)
    m = llm.make_chat_model("sonnet", max_tokens=123)
    assert m.max_tokens == 123


def test_key_never_in_repr(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ANTHROPIC_API_KEY", FAKE)
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
    monkeypatch.setenv("ANTHROPIC_API_KEY", FAKE)
    monkeypatch.setenv("REQUESTS_CA_BUNDLE", str(bundle))
    llm.make_chat_model("sonnet")
    assert os.environ["SSL_CERT_FILE"] == str(bundle)


def test_existing_ssl_cert_file_wins(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ANTHROPIC_API_KEY", FAKE)
    monkeypatch.setenv("SSL_CERT_FILE", "/a.pem")
    monkeypatch.setenv("REQUESTS_CA_BUNDLE", "/b.pem")
    llm.make_chat_model("sonnet")
    assert os.environ["SSL_CERT_FILE"] == "/a.pem"


def test_models_shim_is_gone() -> None:
    with pytest.raises(ModuleNotFoundError):
        __import__("cua.models")
