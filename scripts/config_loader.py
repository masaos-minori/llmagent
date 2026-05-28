#!/usr/bin/env python3
"""
config_loader.py
Shared configuration loader for agent pipeline modules.
"""

import logging
from pathlib import Path
from typing import Any

import orjson

# Use module-level logger (library module convention: no FileHandler)
logger = logging.getLogger(__name__)


class ConfigLoader:
    """Load and merge JSON config files from the config/ directory."""

    def __init__(self, config_dir: Path | None = None) -> None:
        # Two levels up from this file is the repo root; config/ lives there
        repo_root = Path(__file__).resolve().parent.parent
        self._config_dir = config_dir or repo_root / "config"

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def load(self, *names: str) -> dict[str, Any]:
        """
        Read and merge one or more JSON config files.

        Keys starting with '_' (e.g. _doc) are treated as documentation
        metadata and excluded from the result.

        Raises ValueError if a file is missing or contains invalid JSON.
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
        """Read and parse a single JSON config file; raise ValueError on failure."""
        path = self._config_dir / name
        try:
            data: dict[str, Any] = orjson.loads(path.read_bytes())
        except FileNotFoundError as exc:
            raise ValueError(f"Config file not found: {path}") from exc
        except orjson.JSONDecodeError as exc:
            raise ValueError(f"Invalid JSON in config file {path}: {exc}") from exc
        except OSError as exc:
            raise ValueError(f"Cannot read config file {path}: {exc}") from exc

        # Validate the top-level type so callers can rely on dict semantics
        if not isinstance(data, dict):
            raise ValueError(
                f"Config file {path} must contain a JSON object, "
                f"got {type(data).__name__}"
            )

        logger.debug("Loaded config: %s (%d keys)", name, len(data))
        return data

    @staticmethod
    def _filter_meta_keys(data: dict[str, Any]) -> dict[str, Any]:
        """Exclude keys that start with '_' (documentation metadata)."""
        return {k: v for k, v in data.items() if not k.startswith("_")}
