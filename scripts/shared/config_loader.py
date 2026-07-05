#!/usr/bin/env python3
"""config_loader.py
Shared configuration loader for agent pipeline modules.
Supports both TOML (.toml) and JSON (.json) config files.
"""

from __future__ import annotations

import logging
import tomllib
from pathlib import Path
from typing import Any

import orjson

from shared.config_errors import (
    ConfigMissingError,
    ConfigParseError,
    ConfigPermissionError,
    ConfigReadError,
)

logger = logging.getLogger(__name__)


_BASE_CONFIG_FILES: tuple[str, ...] = ("agent.toml",)

_REQUIRED_CONFIG_FILES: frozenset[str] = frozenset(("agent.toml",))


class ConfigLoader:
    """Load and merge TOML or JSON config files from the config/ directory."""

    # Set by restrict_to() at process startup; None means unrestricted.
    _allowed_files: frozenset[str] | None = None

    @classmethod
    def restrict_to(cls, *filenames: str) -> None:
        """Restrict this process to loading only the specified config files.

        Call once at process startup (before any config is loaded). Any
        subsequent call to load() or load_all() that touches a file not in
        this set raises ConfigPermissionError.
        """
        if not filenames:
            raise ValueError("restrict_to() requires at least one filename.")
        cls._allowed_files = frozenset(filenames)

    def __init__(self, config_dir: Path | None = None) -> None:
        repo_root = Path(__file__).resolve().parent.parent.parent
        self._config_dir = config_dir or repo_root / "config"

    # -- Public API ---------------------------------------------------------

    def load(self, *names: str) -> dict[str, Any]:
        """Read and merge one or more TOML or JSON config files; keys starting with '_' are excluded; raises ValueError on missing/parse error."""
        self._validate_names(names)
        if self._allowed_files is not None:
            for name in names:
                _basename = Path(name).name
                if _basename not in self._allowed_files:
                    raise ConfigPermissionError(
                        f"This process is not permitted to load '{_basename}'. "
                        f"Allowed: {sorted(self._allowed_files)}"
                    )
        merged: dict[str, Any] = {}
        for name in names:
            merged.update(self._filter_meta_keys(self._load_single(name)))
        return merged

    def load_all(self, strict: bool = False) -> dict[str, Any]:
        """Load all base config files from config/ in dependency order.

        Args:
            strict: If True, raise ConfigMissingError for any missing required
                config file. Required files are defined in _REQUIRED_CONFIG_FILES.
                If False (default), missing files are skipped with a debug log.

        Dict-valued keys are merged one level deep so that multiple MCP server
        config files can each contribute a [mcp_servers.<key>] section without
        overwriting entries from previously loaded files.
        """
        if self._allowed_files is not None:
            for name in _BASE_CONFIG_FILES:
                if name not in self._allowed_files:
                    raise ConfigPermissionError(
                        f"This process is not permitted to load '{name}' via load_all(). "
                        f"Allowed: {sorted(self._allowed_files)}"
                    )
        merged: dict[str, Any] = {}
        for name in _BASE_CONFIG_FILES:
            try:
                data = self._filter_meta_keys(self._load_single(name))
                for key, val in data.items():
                    if isinstance(val, dict) and isinstance(merged.get(key), dict):
                        merged[key] = {**merged[key], **val}
                    else:
                        merged[key] = val
            except ConfigMissingError:
                if strict and name in _REQUIRED_CONFIG_FILES:
                    raise
                logger.debug("Config file not found: %s", name)
        return merged

    # -- Private helpers ----------------------------------------------------

    @staticmethod
    def _validate_names(names: tuple[Any, ...]) -> None:
        if not names:
            raise ValueError("At least one config file name must be provided.")
        for name in names:
            if not isinstance(name, str) or not name.strip():
                raise TypeError(
                    f"Config file name must be a non-empty str, got: {name!r}"
                )

    def _load_single(self, name: str) -> dict[str, Any]:
        path = self._resolve_path(name)
        suffix = path.suffix.lower()
        try:
            if suffix == ".toml":
                return tomllib.loads(path.read_text(encoding="utf-8"))
            parsed = orjson.loads(path.read_bytes())
            if not isinstance(parsed, dict):
                raise ValueError(
                    f"Config file {path} must be a top-level mapping, got {type(parsed).__name__}"
                )
            return dict(parsed)
        except FileNotFoundError as exc:
            raise ConfigMissingError(f"Config file not found: {path}") from exc
        except tomllib.TOMLDecodeError as exc:
            raise ConfigParseError(f"Invalid TOML in {path}: {exc}") from exc
        except orjson.JSONDecodeError as exc:
            raise ConfigParseError(f"Invalid JSON in {path}: {exc}") from exc
        except OSError as exc:
            raise ConfigReadError(f"Cannot read config file {path}: {exc}") from exc

    def _resolve_path(self, name: str) -> Path:
        p = Path(name) if name.endswith((".toml", ".json")) else Path(f"{name}.toml")
        return self._config_dir / p.name

    @staticmethod
    def _filter_meta_keys(data: dict[str, Any]) -> dict[str, Any]:
        return {k: v for k, v in data.items() if not k.startswith("_")}
