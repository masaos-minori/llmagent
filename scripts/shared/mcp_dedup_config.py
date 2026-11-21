"""scripts/shared/mcp_dedup_config.py — Dedup config loading and validation.

Config-file location, per-key validation, per-process caching, and the config
fingerprint for the dedup store (REQ-010). Split from shared/mcp_dedup.py by
the scripts/ module size gate (24576 B); the public names are re-exported by
the shared.mcp_dedup facade.
"""

from __future__ import annotations

import hashlib
import json
import logging
import tomllib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from shared.config_errors import ConfigMissingError, ConfigParseError
from shared.runtime_paths import resolve_config_dir
from shared.tool_constants import RETRYABLE_TOOLS, get_all_mcp_tool_names

logger = logging.getLogger(__name__)

# Same fallback-literal shape as the workflow_db_path default in
# scripts/db/config.py; the shared-leaf contract forbids importing scripts/db here.
DEFAULT_DB_PATH = "/opt/llm/db/mcp_dedup.sqlite"
DEFAULT_RETENTION_DAYS = 14
DEFAULT_PENDING_TIMEOUT_MINUTES = 10
DEFAULT_LEASE_SECONDS = 30
DEFAULT_MAX_ATTEMPTS = 3
_LEASE_SECONDS_RANGE = (1, 3600)
_MAX_ATTEMPTS_RANGE = (1, 10)
_DEDUP_INT_KEYS: dict[str, tuple[int, int, int]] = {
    # name -> (default, low, high)
    "retention_days": (DEFAULT_RETENTION_DAYS, 1, 365),
    "pending_timeout_minutes": (DEFAULT_PENDING_TIMEOUT_MINUTES, 1, 1440),
    "lease_seconds": (DEFAULT_LEASE_SECONDS, *_LEASE_SECONDS_RANGE),
    "max_attempts": (DEFAULT_MAX_ATTEMPTS, *_MAX_ATTEMPTS_RANGE),
}

_DEDUP_CONFIG_CACHE: dict[Path, DedupConfig] = {}


@dataclass(frozen=True)
class DedupConfig:
    db_path: str = DEFAULT_DB_PATH
    retention_days: int = DEFAULT_RETENTION_DAYS
    pending_timeout_minutes: int = DEFAULT_PENDING_TIMEOUT_MINUTES
    lease_seconds: int = DEFAULT_LEASE_SECONDS
    max_attempts: int = DEFAULT_MAX_ATTEMPTS
    retry_class: dict[str, str] = field(default_factory=dict)


def _config_fingerprint(config: DedupConfig) -> str:
    payload = json.dumps(
        {
            "db_path": config.db_path,
            "retention_days": config.retention_days,
            "pending_timeout_minutes": config.pending_timeout_minutes,
            "lease_seconds": config.lease_seconds,
            "max_attempts": config.max_attempts,
        },
        sort_keys=True,
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _default_config_path() -> Path:
    """Resolve config/mcp_dedup.toml through the shared config-directory resolver.

    Precedence follows resolve_config_dir(): LLMAGENT_CONFIG_DIR override first;
    resolution happens at call time so test and deploy overrides take effect.
    """
    return resolve_config_dir() / "mcp_dedup.toml"


def _validated_int(
    filename: str, dedup: dict[str, Any], name: str, default: int, low: int, high: int
) -> int:
    raw = dedup.get(name, default)
    if isinstance(raw, bool) or not isinstance(raw, int):
        raise ConfigParseError(filename, ValueError(f"dedup.{name} must be an integer"))
    if not low <= raw <= high:
        raise ConfigParseError(
            filename,
            ValueError(f"dedup.{name} out of range {low}..{high}: {raw}"),
        )
    return int(raw)


def _validated_retry_class(filename: str, retry_section: Any) -> dict[str, str]:
    """Validate the `[retry_class]` mirror and report drift against reference data.

    The declared `retry_policy` carried by each tool's metadata is the authority
    for retry classification (agentcfg003). This config map is the dispatcher's
    own mirror; a disagreement with the `RETRYABLE_TOOLS` reference set is
    reported as a drift finding and never changes the classification loaded
    for a call. Structural validation (table shape, known tool names, allowed
    values) stays fail-closed.
    """
    if not isinstance(retry_section, dict):
        raise ConfigParseError(
            filename, ValueError("[retry_class] section must be a table")
        )
    retry_class: dict[str, str] = {}
    known_tool_names = get_all_mcp_tool_names()
    for tool_name, cls in retry_section.items():
        if not isinstance(cls, str):
            raise ConfigParseError(
                filename, ValueError(f"retry_class.{tool_name} must be a string")
            )
        if tool_name not in known_tool_names:
            raise ConfigParseError(
                filename,
                ValueError(f"retry_class.{tool_name} is not a known MCP tool name"),
            )
        if cls not in ("retryable", "non_retryable"):
            raise ConfigParseError(
                filename,
                ValueError(
                    f"retry_class.{tool_name} must be 'retryable' or 'non_retryable'"
                ),
            )
        if (tool_name in RETRYABLE_TOOLS) != (cls == "retryable"):
            logger.warning(
                "[retry_class] drift finding: retry_class.%s = %r contradicts "
                "RETRYABLE_TOOLS reference membership; the declared "
                "retry_policy field is the authority",
                tool_name,
                cls,
            )
        retry_class[str(tool_name)] = cls
    return retry_class


def load_dedup_config(path: str | Path | None = None) -> DedupConfig:
    """Load the dedup config once per process, keyed by resolved absolute path.

    With path=None the file is located by _default_config_path(). The first
    successful load parses and caches the config; later loads serve the cache
    with no filesystem access until the process restarts. Missing file and bad
    values raise typed ConfigErrors and are never cached. Unknown [dedup] keys
    and out-of-range integers are rejected (REQ-010).
    """
    key = (
        (_default_config_path() if path is None else Path(path)).expanduser().resolve()
    )
    cached = _DEDUP_CONFIG_CACHE.get(key)
    if cached is not None:
        return cached

    filename = key.name
    try:
        raw = key.read_bytes()
    except FileNotFoundError as exc:
        raise ConfigMissingError(filename) from exc

    try:
        data = tomllib.loads(raw.decode("utf-8"))
    except (tomllib.TOMLDecodeError, UnicodeDecodeError) as exc:
        raise ConfigParseError(filename, exc) from exc

    dedup = data.get("dedup", {})
    if not isinstance(dedup, dict):
        raise ConfigParseError(filename, ValueError("[dedup] section must be a table"))

    db_path = dedup.get("db_path", DEFAULT_DB_PATH)
    if not isinstance(db_path, str) or not db_path:
        raise ConfigParseError(
            filename, ValueError("dedup.db_path must be a non-empty string")
        )

    unknown_keys = sorted(set(dedup) - {"db_path"} - set(_DEDUP_INT_KEYS))
    if unknown_keys:
        raise ConfigParseError(
            filename, ValueError(f"unknown dedup keys: {', '.join(unknown_keys)}")
        )

    values = {
        name: _validated_int(filename, dedup, name, spec[0], spec[1], spec[2])
        for name, spec in _DEDUP_INT_KEYS.items()
    }
    retry_class = _validated_retry_class(filename, data.get("retry_class", {}))

    config = DedupConfig(
        db_path=db_path,
        retention_days=values["retention_days"],
        pending_timeout_minutes=values["pending_timeout_minutes"],
        lease_seconds=values["lease_seconds"],
        max_attempts=values["max_attempts"],
        retry_class=retry_class,
    )
    _DEDUP_CONFIG_CACHE[key] = config
    return config


def clear_dedup_config_cache() -> None:
    """Drop every cached dedup config.

    Test and tooling seam; production reload happens at service restart.
    """
    _DEDUP_CONFIG_CACHE.clear()
