"""Settings management with config file and environment variable support."""

from pathlib import Path
from typing import Any

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings with multiple configuration sources."""

    api_token: str = Field(default="", description="Papertrail API token")
    default_limit: int = Field(default=1000, description="Default event limit")
    default_output: str = Field(default="text", description="Default output format")
    timeout: float = Field(default=30.0, description="API request timeout")

    model_config = SettingsConfigDict(
        env_prefix="PAPERTRAIL_",
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @field_validator("api_token")
    @classmethod
    def validate_api_token(cls, v: str) -> str:
        """Validate API token is not empty."""
        if not v:
            raise ValueError("API token is required")
        return v

    @field_validator("default_output")
    @classmethod
    def validate_output_format(cls, v: str) -> str:
        """Validate output format."""
        valid_formats = ["text", "json", "csv"]
        if v not in valid_formats:
            raise ValueError(f"Output format must be one of {valid_formats}")
        return v


def get_config_paths() -> list[Path]:
    """Get list of config file paths to search, in priority order.

    Returns:
        List of config file paths (highest priority first)
    """
    paths = []

    # 1. Local config
    local_config = Path.cwd() / "paperctl.toml"
    if local_config.exists():
        paths.append(local_config)

    # 2. Home config
    home_config = Path.home() / ".paperctl.toml"
    if home_config.exists():
        paths.append(home_config)

    # 3. XDG config
    xdg_config_home = Path(
        Path.home() / ".config" if not Path.home() / ".config" else Path.home() / ".config"
    )
    xdg_config = xdg_config_home / "paperctl" / "config.toml"
    if xdg_config.exists():
        paths.append(xdg_config)

    return paths


def load_config_file(path: Path) -> dict[str, Any]:
    """Load configuration from TOML file.

    Args:
        path: Path to config file

    Returns:
        Configuration dictionary
    """
    try:
        import tomllib
    except ImportError:
        import tomli as tomllib  # type: ignore[import-not-found,no-redef]

    with open(path, "rb") as f:
        return tomllib.load(f)


def get_settings(**overrides: Any) -> Settings:
    """Get settings with config file and environment variable support.

    Configuration priority (highest to lowest):
    1. Keyword arguments (overrides)
    2. Environment variables (PAPERTRAIL_*)
    3. Local config (./paperctl.toml)
    4. Home config (~/.paperctl.toml)
    5. XDG config (~/.config/paperctl/config.toml)

    Args:
        **overrides: Override specific settings

    Returns:
        Settings instance
    """
    # Load from config files
    config_data: dict[str, Any] = {}
    for config_path in reversed(get_config_paths()):
        config_data.update(load_config_file(config_path))

    # Merge with overrides
    config_data.update(overrides)

    # Create settings (env vars take precedence via pydantic-settings)
    return Settings(**config_data)
