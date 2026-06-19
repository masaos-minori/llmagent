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

logger = logging.getLogger(__name__)

_BASE_CONFIG_FILES: tuple[str, ...] = (
    "common.toml",
    "llm.toml",
    "http.toml",
    "rag.toml",
    "context.toml",
    "tools.toml",
    "memory.toml",
    "otel.toml",
    "security.toml",
    "system_prompts.toml",
    "mcp_servers.toml",
    "tools_definitions.toml",
)


class ConfigLoader:
    """Load and merge TOML or JSON config files from the config/ directory."""

    def __init__(self, config_dir: Path | None = None) -> None:
        repo_root = Path(__file__).resolve().parent.parent.parent
        self._config_dir = config_dir or repo_root / "config"

    # -- Public API ---------------------------------------------------------

    def load(self, *names: str) -> dict[str, Any]:
        """Read and merge one or more TOML or JSON config files; keys starting with '_' are excluded; raises ValueError on missing/parse error."""
        self._validate_names(names)
        merged: dict[str, Any] = {}
        for name in names:
            merged.update(self._filter_meta_keys(self._load_single(name)))
        return merged

    def load_all(self) -> dict[str, Any]:
        """Load all base config files from config/ in dependency order."""
        merged: dict[str, Any] = {}
        for name in _BASE_CONFIG_FILES:
            try:
                merged.update(self._filter_meta_keys(self._load_single(name)))
            except ValueError:
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
            raise ValueError(f"Config file not found: {path}") from exc
        except tomllib.TOMLDecodeError as exc:
            raise ValueError(f"Invalid TOML in {path}: {exc}") from exc
        except orjson.JSONDecodeError as exc:
            raise ValueError(f"Invalid JSON in {path}: {exc}") from exc
        except OSError as exc:
            raise ValueError(f"Cannot read config file {path}: {exc}") from exc

    def _resolve_path(self, name: str) -> Path:
        p = Path(name) if name.endswith((".toml", ".json")) else Path(f"{name}.toml")
        return self._config_dir / p.name

    @staticmethod
    def _filter_meta_keys(data: dict[str, Any]) -> dict[str, Any]:
        return {k: v for k, v in data.items() if not k.startswith("_")}
