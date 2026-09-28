"""Offline tests for `cua.models.make_chat_model` (Iliad gateway). No network, no real key."""

from __future__ import annotations

import pytest

from cua import config, models

FAKE = "test-key-not-real"


@pytest.fixture(autouse=True)
def _clean_env(monkeypatch: pytest.MonkeyPatch) -> None:
    for name in ("ILIAD_API_KEY", "ANTHROPIC_API_KEY", "SSL_CERT_FILE", "REQUESTS_CA_BUNDLE"):
        monkeypatch.delenv(name, raising=False)   # teardown restores any prior value
    monkeypatch.setattr(models, "_FALLBACK_NOTED", False)


def test_sonnet_uses_iliad_url_and_sonnet_name(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ILIAD_API_KEY", FAKE)
    m = models.make_chat_model("sonnet")
    assert m.anthropic_api_url == config.ILIAD_BASE_URL
    assert m.model == config.SONNET_MODEL_NAME
    assert m.anthropic_api_key.get_secret_value() == FAKE


def test_haiku_uses_haiku_name(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ILIAD_API_KEY", FAKE)
    m = models.make_chat_model("haiku")
    assert m.model == config.HAIKU_MODEL_NAME
    assert m.anthropic_api_url == config.ILIAD_BASE_URL


def test_defaults_match_gateway_snippet() -> None:
    assert config.ILIAD_BASE_URL.endswith("/anthropic")
    assert "sonnet" in config.SONNET_MODEL_NAME
    assert "haiku" in config.HAIKU_MODEL_NAME


def test_overrides_pass_through(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ILIAD_API_KEY", FAKE)
    m = models.make_chat_model("sonnet", max_tokens=123)
    assert m.max_tokens == 123


def test_key_never_in_repr(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ILIAD_API_KEY", FAKE)
    m = models.make_chat_model("sonnet")
    assert FAKE not in repr(m)
    assert FAKE not in str(m)


def test_missing_key_raises_clear_error() -> None:
    with pytest.raises(RuntimeError) as exc:
        models.make_chat_model("sonnet")
    assert "ILIAD_API_KEY is not set in .env" in str(exc.value)


def test_unknown_kind_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ILIAD_API_KEY", FAKE)
    with pytest.raises(ValueError) as exc:
        models.make_chat_model("opus")  # type: ignore[arg-type]
    assert FAKE not in str(exc.value)


def test_fallback_to_anthropic_key(monkeypatch: pytest.MonkeyPatch,
                                   capsys: pytest.CaptureFixture[str]) -> None:
    monkeypatch.setenv("ANTHROPIC_API_KEY", FAKE)
    m = models.make_chat_model("haiku")
    assert m.anthropic_api_url != config.ILIAD_BASE_URL
    assert m.model == config.HAIKU_MODEL_NAME
    models.make_chat_model("sonnet")
    out = capsys.readouterr().out
    assert out.count("ILIAD_API_KEY not set") == 1   # said once, not per call
    assert FAKE not in out
    assert FAKE not in repr(m)


def test_ca_bundle_passthrough(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:  # noqa: ANN001
    import os

    bundle = tmp_path / "ca.pem"
    monkeypatch.setenv("ILIAD_API_KEY", FAKE)
    monkeypatch.setenv("REQUESTS_CA_BUNDLE", str(bundle))
    models.make_chat_model("sonnet")
    assert os.environ["SSL_CERT_FILE"] == str(bundle)


def test_existing_ssl_cert_file_wins(monkeypatch: pytest.MonkeyPatch) -> None:
    import os

    monkeypatch.setenv("ILIAD_API_KEY", FAKE)
    monkeypatch.setenv("SSL_CERT_FILE", "/a.pem")
    monkeypatch.setenv("REQUESTS_CA_BUNDLE", "/b.pem")
    models.make_chat_model("sonnet")
    assert os.environ["SSL_CERT_FILE"] == "/a.pem"


def test_typesafe_router_gets_haiku_and_sonnet_instances(monkeypatch: pytest.MonkeyPatch) -> None:
    """The model router receives ChatAnthropic objects (not strings) and keeps them as-is."""
    from langchain_anthropic import ChatAnthropic

    from cua.agent import build_typesafe_middleware

    class _Page:
        url = "https://parabank.parasoft.com/parabank/index.htm"

    class _Agent:
        page = _Page()

    monkeypatch.setenv("ILIAD_API_KEY", FAKE)
    monkeypatch.setenv("TYPESAFE_API_KEY", "typesafe-key-not-real")
    router = build_typesafe_middleware(_Agent())[1]  # type: ignore[arg-type]
    fast, powerful = router.models["fast"], router.models["powerful"]
    assert isinstance(fast, ChatAnthropic) and isinstance(powerful, ChatAnthropic)
    assert fast.model == config.HAIKU_MODEL_NAME
    assert powerful.model == config.SONNET_MODEL_NAME
    assert fast.anthropic_api_url == config.ILIAD_BASE_URL


def test_build_langchain_agent_defaults_to_iliad_sonnet(monkeypatch: pytest.MonkeyPatch) -> None:
    """No model given -> create_deep_agent receives make_chat_model('sonnet')."""
    import deepagents

    from cua.agent import build_langchain_agent

    seen: dict[str, object] = {}
    monkeypatch.setenv("ILIAD_API_KEY", FAKE)
    monkeypatch.setattr(deepagents, "create_deep_agent", lambda **kw: seen.update(kw))
    build_langchain_agent([])
    assert seen["model"].model == config.SONNET_MODEL_NAME  # type: ignore[attr-defined]
    assert seen["model"].anthropic_api_url == config.ILIAD_BASE_URL  # type: ignore[attr-defined]
