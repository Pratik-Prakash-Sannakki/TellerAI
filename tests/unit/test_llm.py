"""Offline tests for `cua.llm.make_chat_model` (Iliad gateway). No network, no real key."""

from __future__ import annotations

import pytest

import cua.models
from cua import config, llm

FAKE = "test-key-not-real"


@pytest.fixture(autouse=True)
def _clean_env(monkeypatch: pytest.MonkeyPatch) -> None:
    for name in ("ILIAD_API_KEY", "ANTHROPIC_API_KEY", "SSL_CERT_FILE", "REQUESTS_CA_BUNDLE"):
        monkeypatch.delenv(name, raising=False)  # teardown restores any prior value
    monkeypatch.setattr(llm, "_FALLBACK_NOTED", False)


def test_sonnet_uses_iliad_url_and_sonnet_name(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ILIAD_API_KEY", FAKE)
    m = llm.make_chat_model("sonnet")
    assert m.anthropic_api_url == config.ILIAD_BASE_URL
    assert m.model == config.SONNET_MODEL_NAME
    assert m.anthropic_api_key.get_secret_value() == FAKE


def test_haiku_uses_haiku_name(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ILIAD_API_KEY", FAKE)
    m = llm.make_chat_model("haiku")
    assert m.model == config.HAIKU_MODEL_NAME
    assert m.anthropic_api_url == config.ILIAD_BASE_URL


def test_defaults_match_gateway_snippet() -> None:
    assert config.ILIAD_BASE_URL.endswith("/anthropic")
    assert "sonnet" in config.SONNET_MODEL_NAME
    assert "haiku" in config.HAIKU_MODEL_NAME


def test_overrides_pass_through(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ILIAD_API_KEY", FAKE)
    m = llm.make_chat_model("sonnet", max_tokens=123)
    assert m.max_tokens == 123


def test_key_never_in_repr(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ILIAD_API_KEY", FAKE)
    m = llm.make_chat_model("sonnet")
    assert FAKE not in repr(m)
    assert FAKE not in str(m)


def test_missing_key_raises_clear_error() -> None:
    with pytest.raises(RuntimeError) as exc:
        llm.make_chat_model("sonnet")
    assert "ILIAD_API_KEY is not set in .env" in str(exc.value)


def test_unknown_kind_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ILIAD_API_KEY", FAKE)
    with pytest.raises(ValueError) as exc:
        llm.make_chat_model("opus")  # type: ignore[arg-type]
    assert FAKE not in str(exc.value)


def test_fallback_to_anthropic_key(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setenv("ANTHROPIC_API_KEY", FAKE)
    m = llm.make_chat_model("haiku")
    assert m.anthropic_api_url != config.ILIAD_BASE_URL
    assert m.model == config.HAIKU_MODEL_NAME
    llm.make_chat_model("sonnet")
    out = capsys.readouterr().out
    assert out.count("ILIAD_API_KEY not set") == 1  # said once, not per call
    assert FAKE not in out
    assert FAKE not in repr(m)


def test_ca_bundle_passthrough(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:  # noqa: ANN001
    import os

    bundle = tmp_path / "ca.pem"
    monkeypatch.setenv("ILIAD_API_KEY", FAKE)
    monkeypatch.setenv("REQUESTS_CA_BUNDLE", str(bundle))
    llm.make_chat_model("sonnet")
    assert os.environ["SSL_CERT_FILE"] == str(bundle)


def test_existing_ssl_cert_file_wins(monkeypatch: pytest.MonkeyPatch) -> None:
    import os

    monkeypatch.setenv("ILIAD_API_KEY", FAKE)
    monkeypatch.setenv("SSL_CERT_FILE", "/a.pem")
    monkeypatch.setenv("REQUESTS_CA_BUNDLE", "/b.pem")
    llm.make_chat_model("sonnet")
    assert os.environ["SSL_CERT_FILE"] == "/a.pem"


def test_models_shim_reexports_the_factory() -> None:
    assert cua.models.make_chat_model is llm.make_chat_model
    assert cua.models.ModelKind is llm.ModelKind
