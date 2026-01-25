"""
Configuration management for the recipe tool.

This module defines the Config class, responsible for validating
and exposing configuration values provided as a Python dictionary.
"""

from types import SimpleNamespace


class ConfigError(Exception):
    """Raised when the configuration is invalid."""
    pass


class Config:
    """
    Loads, validates, and exposes application configuration.

    Responsibilities:
    - Validate required configuration sections and keys
    - Apply default values where applicable
    - Expose configuration values as attributes
    """

    DEFAULTS = {
        "logging": {
            "enabled": True,
            "dir": "Logs",
            "level": "INFO",
            "rotate": False,
            "max_size_mb": 5,
            "backups": 3,
        },
        "lint": {
            "strict_sections": True,
        },
        "fix": {
            "enabled": True,
            "overwrite": False,
        },
        "ai": {
            "enabled": False,
            "model": "gpt-4.1-mini",
            "temperature": 0.3,
            "max_tokens": 300,
        },
        "report": {
            "generate_html": True,
            "highlight_color": "#fff59d",
        },
    }

    REQUIRED_SECTIONS = ["paths", "lint", "fix"]

    REQUIRED_PATH_KEYS = ["recipes_dir", "fixed_dir"]

    def __init__(self, config_dict: dict):
        if not isinstance(config_dict, dict):
            raise ConfigError("Configuration must be a dictionary")

        self._raw = config_dict
        self._validate_required_sections()
        merged = self._apply_defaults()
        self._validate_types(merged)
        self._load_attributes(merged)

    def _validate_required_sections(self) -> None:
        for section in self.REQUIRED_SECTIONS:
            if section not in self._raw:
                raise ConfigError(f"Missing required config section: '{section}'")

        if "paths" not in self._raw:
            raise ConfigError("Missing required config section: 'paths'")

        for key in self.REQUIRED_PATH_KEYS:
            if key not in self._raw["paths"]:
                raise ConfigError(f"Missing required path key: 'paths.{key}'")

    def _apply_defaults(self) -> dict:
        merged = {}

        for section, defaults in self.DEFAULTS.items():
            user_section = self._raw.get(section, {})
            merged[section] = {**defaults, **user_section}

        for section, value in self._raw.items():
            if section not in merged:
                merged[section] = value

        return merged

    def _validate_types(self, cfg: dict) -> None:
        if not isinstance(cfg["fix"]["overwrite"], bool):
            raise ConfigError("fix.overwrite must be a boolean")

        if not isinstance(cfg["lint"]["strict_sections"], bool):
            raise ConfigError("lint.strict_sections must be a boolean")

        if not isinstance(cfg["logging"]["enabled"], bool):
            raise ConfigError("logging.enabled must be a boolean")

    def _load_attributes(self, cfg: dict) -> None:
        for section, values in cfg.items():
            if isinstance(values, dict):
                setattr(self, section, SimpleNamespace(**values))
            else:
                setattr(self, section, values)
