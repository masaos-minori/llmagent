#!/usr/bin/env python3
"""
config_loader.py
Shared configuration loader for agent pipeline modules.
Supports both TOML (.toml) and JSON (.json) config files.
"""

import logging
import tomllib
from pathlib import Path
from typing import Any

import orjson

# Use module-level logger (library module convention: no FileHandler)
logger = logging.getLogger(__name__)


class ConfigLoader:
    """Load and merge TOML or JSON config files from the config/ directory."""

    def __init__(self, config_dir: Path | None = None) -> None:
        # Three levels up from this file (scripts/shared/) is the repo root
        repo_root = Path(__file__).resolve().parent.parent.parent
        self._config_dir = config_dir or repo_root / "config"

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def load(self, *names: str) -> dict[str, Any]:
        """Read and merge one or more TOML or JSON config files.

        Keys starting with '_' (e.g. _doc) are treated as documentation
        metadata and excluded from the result.

        Raises ValueError if a file is missing or has a parse error.
        Raises TypeError if any name is not a str.
        """
        self._validate_names(names)
        merged: dict[str, Any] = {}
        for name in names:
            data = self._load_single(name)
            filtered = self._filter_meta_keys(data)
            merged.update(filtered)
        return merged

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _validate_names(self, names: tuple[Any, ...]) -> None:
        """Guard: all config file names must be non-empty strings."""
        if not names:
            raise ValueError("At least one config file name must be provided.")
        for name in names:
            if not isinstance(name, str) or not name.strip():
                raise TypeError(
                    f"Config file name must be a non-empty str, got: {name!r}"
                )

    def _load_single(self, name: str) -> dict[str, Any]:
        """Read and parse a single config file (TOML or JSON)."""
        path = self._config_dir / name
        suffix = path.suffix.lower()
        try:
            if suffix == ".toml":
                data: dict[str, Any] = tomllib.loads(path.read_text(encoding="utf-8"))
            else:
                data = orjson.loads(path.read_bytes())
        except FileNotFoundError as exc:
            raise ValueError(f"Config file not found: {path}") from exc
        except tomllib.TOMLDecodeError as exc:
            raise ValueError(f"Invalid TOML in config file {path}: {exc}") from exc
        except orjson.JSONDecodeError as exc:
            raise ValueError(f"Invalid JSON in config file {path}: {exc}") from exc
        except OSError as exc:
            raise ValueError(f"Cannot read config file {path}: {exc}") from exc

        # Validate top-level type so callers can rely on dict semantics
        if not isinstance(data, dict):
            raise ValueError(
                f"Config file {path} must contain a top-level mapping, "
                f"got {type(data).__name__}"
            )

        logger.debug("Loaded config: %s (%d keys)", name, len(data))
        return data

    @staticmethod
    def _filter_meta_keys(data: dict[str, Any]) -> dict[str, Any]:
        """Exclude keys that start with '_' (documentation metadata)."""
        return {k: v for k, v in data.items() if not k.startswith("_")}
