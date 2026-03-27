"""Tests for settings loading and env var compatibility."""

from paperctl.config.settings import get_settings


def test_get_settings_uses_swo_api_token(monkeypatch) -> None:
    """SWO_API_TOKEN should populate api_token."""
    monkeypatch.setenv("SWO_API_TOKEN", "swo-token")
    monkeypatch.delenv("PAPERTRAIL_API_TOKEN", raising=False)

    settings = get_settings()

    assert settings.api_token == "swo-token"


def test_get_settings_accepts_legacy_papertrail_token(monkeypatch) -> None:
    """PAPERTRAIL_API_TOKEN should work as a legacy alias in 2.x."""
    monkeypatch.delenv("SWO_API_TOKEN", raising=False)
    monkeypatch.setenv("PAPERTRAIL_API_TOKEN", "legacy-token")

    settings = get_settings()

    assert settings.api_token == "legacy-token"


def test_get_settings_prefers_explicit_override(monkeypatch) -> None:
    """Explicit overrides should win over environment variables."""
    monkeypatch.setenv("SWO_API_TOKEN", "env-token")
    monkeypatch.setenv("PAPERTRAIL_API_TOKEN", "legacy-token")

    settings = get_settings(api_token="override-token")

    assert settings.api_token == "override-token"
