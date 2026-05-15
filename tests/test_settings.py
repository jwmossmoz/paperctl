"""Tests for settings loading and env var compatibility."""

from pathlib import Path

from paperctl.config import settings as settings_module
from paperctl.config.settings import Settings, get_settings


def test_get_settings_uses_swo_api_token(monkeypatch) -> None:
    """SWO_API_TOKEN should populate api_token."""
    monkeypatch.setattr(settings_module, "get_config_paths", lambda: [])
    monkeypatch.setenv("SWO_API_TOKEN", "swo-token")
    monkeypatch.delenv("PAPERTRAIL_API_TOKEN", raising=False)

    settings = get_settings()

    assert settings.api_token == "swo-token"


def test_get_settings_accepts_legacy_papertrail_token(monkeypatch) -> None:
    """PAPERTRAIL_API_TOKEN should work as a legacy alias in 2.x."""
    monkeypatch.setattr(settings_module, "get_config_paths", lambda: [])
    monkeypatch.delenv("SWO_API_TOKEN", raising=False)
    monkeypatch.setenv("PAPERTRAIL_API_TOKEN", "legacy-token")

    settings = get_settings()

    assert settings.api_token == "legacy-token"


def test_get_settings_prefers_explicit_override(monkeypatch) -> None:
    """Explicit overrides should win over environment variables."""
    monkeypatch.setattr(settings_module, "get_config_paths", lambda: [])
    monkeypatch.setenv("SWO_API_TOKEN", "env-token")
    monkeypatch.setenv("PAPERTRAIL_API_TOKEN", "legacy-token")

    settings = get_settings(api_token="override-token")

    assert settings.api_token == "override-token"


def test_settings_accepts_api_token_field_name(monkeypatch) -> None:
    """Config-file keys use the api_token field name, not env-var aliases."""
    monkeypatch.delenv("SWO_API_TOKEN", raising=False)
    monkeypatch.delenv("PAPERTRAIL_API_TOKEN", raising=False)

    settings = Settings(api_token="config-token")

    assert settings.api_token == "config-token"


def test_get_settings_loads_api_token_from_config_file(monkeypatch, tmp_path: Path) -> None:
    """api_token written by config init should load from TOML config."""
    monkeypatch.delenv("SWO_API_TOKEN", raising=False)
    monkeypatch.delenv("PAPERTRAIL_API_TOKEN", raising=False)
    config_path = tmp_path / "paperctl.toml"
    config_path.write_text('api_token = "config-token"\n')
    monkeypatch.setattr(settings_module, "get_config_paths", lambda: [config_path])

    settings = settings_module.get_settings()

    assert settings.api_token == "config-token"


def test_get_settings_prefers_env_token_over_config_file(monkeypatch, tmp_path: Path) -> None:
    """Environment tokens should keep their documented priority over config."""
    monkeypatch.setenv("SWO_API_TOKEN", "env-token")
    monkeypatch.delenv("PAPERTRAIL_API_TOKEN", raising=False)
    config_path = tmp_path / "paperctl.toml"
    config_path.write_text('api_token = "config-token"\n')
    monkeypatch.setattr(settings_module, "get_config_paths", lambda: [config_path])

    settings = settings_module.get_settings()

    assert settings.api_token == "env-token"
