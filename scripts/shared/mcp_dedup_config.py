"""scripts/shared/mcp_dedup_config.py — Dedup store config contract and validation.

Pure validator over an already-loaded `[dedup]` mapping (REQ-003): no file
discovery, no module cache, no `[retry_class]` mirror validation. Callers own
where the table came from (per-server `config/{server}_mcp_server.toml` via
`ConfigLoader.restrict_to()`), and the immutable typed `DedupStoreConfig` is
injected once at process bootstrap. Split from shared/mcp_dedup.py by the
scripts/ module size gate (24576 B); the public names are re-exported by the
shared.mcp_dedup facade.
"""

from __future__ import annotations

import hashlib
import json
import os
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from shared.config_errors import ConfigMissingError, ConfigParseError

# Same fallback-literal shape as the workflow_db_path default in
# scripts/db/config.py; the shared-leaf contract forbids importing scripts/db here.
DEFAULT_DB_PATH = "/opt/llm/db/mcp_dedup.sqlite"
DEFAULT_RETENTION_DAYS = 14
DEFAULT_PENDING_TIMEOUT_MINUTES = 10
DEFAULT_LEASE_SECONDS = 30
DEFAULT_MAX_ATTEMPTS = 3

# Dedup database directory contract (REQ-006): db_path must live inside this
# directory; LLMAGENT_DB_DIR overrides it for test and development runs.
DB_DIR_ENV_VAR = "LLMAGENT_DB_DIR"

_LEASE_SECONDS_RANGE = (1, 3600)
_MAX_ATTEMPTS_RANGE = (1, 10)
_DEDUP_INT_KEYS: dict[str, tuple[int, int, int]] = {
    # name -> (default, low, high)
    "retention_days": (DEFAULT_RETENTION_DAYS, 1, 365),
    "pending_timeout_minutes": (DEFAULT_PENDING_TIMEOUT_MINUTES, 1, 1440),
    "lease_seconds": (DEFAULT_LEASE_SECONDS, *_LEASE_SECONDS_RANGE),
    "max_attempts": (DEFAULT_MAX_ATTEMPTS, *_MAX_ATTEMPTS_RANGE),
}

_MAX_DEDUP_ROWS_RANGE = (1, 10000000)
_MAX_DEDUP_GROWTH_PER_HOUR_RANGE = (1, 1000000)
_MAX_DEDUP_WAL_MB_RANGE = (1, 4096)

# Optional capacity keys (REQ-007). These are validation ranges, not threshold values:
# the values themselves are operator-supplied (U-1), so no default is invented here and an
# absent key stays unset. None of these names is part of `_config_fingerprint`, so store
# identity is unchanged (owner decision D-5).
DEDUP_OPTIONAL_INT_KEYS: dict[str, tuple[int, int]] = {
    # name -> (low, high)
    "max_dedup_rows": _MAX_DEDUP_ROWS_RANGE,
    "max_dedup_growth_per_hour": _MAX_DEDUP_GROWTH_PER_HOUR_RANGE,
    "max_dedup_wal_mb": _MAX_DEDUP_WAL_MB_RANGE,
}

# States the legal-hold list may name (REQ-003), the four row states of the `status` CHECK in
# shared/mcp_dedup_schema.py. Kept as a module-level frozenset so the shared leaf gains no new
# import.
LEGAL_HOLD_STATES = frozenset({"pending", "completed", "failed", "interrupted"})


@dataclass(frozen=True)
class DedupStoreConfig:
    """Immutable validated store settings for one shared dedup store."""

    db_path: str = DEFAULT_DB_PATH
    retention_days: int = DEFAULT_RETENTION_DAYS
    pending_timeout_minutes: int = DEFAULT_PENDING_TIMEOUT_MINUTES
    lease_seconds: int = DEFAULT_LEASE_SECONDS
    max_attempts: int = DEFAULT_MAX_ATTEMPTS
    # Unset when the key is absent: these report-only boundaries never change store or
    # dispatcher behaviour (owner decision D-6) and are excluded from _config_fingerprint (D-5).
    max_dedup_rows: int | None = None
    max_dedup_growth_per_hour: int | None = None
    max_dedup_wal_mb: int | None = None
    legal_hold_states: tuple[str, ...] = ()


def _config_fingerprint(config: DedupStoreConfig) -> str:
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


def dedup_db_dir() -> Path:
    """Return the dedup database directory contract root (REQ-006).

    ``LLMAGENT_DB_DIR`` overrides the ``DEFAULT_DB_PATH`` parent so tests and
    development runs can point the store at a scratch directory; production
    launches leave the variable unset.
    """
    override = os.environ.get(DB_DIR_ENV_VAR)
    if override:
        return Path(override)
    return Path(DEFAULT_DB_PATH).parent


def _validated_int(
    filename: str,
    dedup: Mapping[str, Any],
    name: str,
    default: int,
    low: int,
    high: int,
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


def _validated_optional_int(
    filename: str,
    dedup: Mapping[str, Any],
    name: str,
    low: int,
    high: int,
) -> int | None:
    """Validate one optional capacity key (REQ-007), fail-closed like the committed keys.

    An absent key returns `None` — no default value is invented for it (U-1). The checks and the
    `dedup.<name>` message shapes are the same as `_validated_int()`: reject a bool or a non-int,
    then reject a value outside the inclusive bounds.
    """
    if name not in dedup:
        return None
    raw = dedup[name]
    if isinstance(raw, bool) or not isinstance(raw, int):
        raise ConfigParseError(filename, ValueError(f"dedup.{name} must be an integer"))
    if not low <= raw <= high:
        raise ConfigParseError(
            filename,
            ValueError(f"dedup.{name} out of range {low}..{high}: {raw}"),
        )
    return int(raw)


def _validated_hold_states(filename: str, dedup: Mapping[str, Any]) -> tuple[str, ...]:
    """Validate the optional `legal_hold_states` list (REQ-003).

    Absent or empty means no hold. A list is fail-closed: every name must be a string and a
    stored row state (`LEGAL_HOLD_STATES`), so the list cannot name anything the store does not
    hold.
    """
    raw = dedup.get("legal_hold_states")
    if raw is None:
        return ()
    if not isinstance(raw, list):
        raise ConfigParseError(
            filename,
            ValueError("dedup.legal_hold_states must be a list of state names"),
        )
    for state in raw:
        if not isinstance(state, str) or state not in LEGAL_HOLD_STATES:
            raise ConfigParseError(
                filename,
                ValueError(
                    f"dedup.legal_hold_states names a state that is not a stored row state: "
                    f"{state}"
                ),
            )
    return tuple(raw)


def load_dedup_section(
    section: Mapping[str, Any] | None, filename: str
) -> DedupStoreConfig:
    """Validate an already-loaded `[dedup]` mapping into a typed config.

    Pure function (REQ-003): no path resolution, no filesystem access, no
    cache. `section` is the `["dedup"]` table of an already-parsed config file
    and `filename` names that file in every typed error message. A missing
    table raises `ConfigMissingError`; invalid types, booleans-as-integers,
    unknown keys, out-of-range integers, and a `db_path` that is not the
    canonical store path (`dedup_db_dir() / mcp_dedup.sqlite`) raise
    `ConfigParseError` with `dedup.<key>`-prefixed messages (REQ-006). The optional capacity
    keys and `legal_hold_states` (REQ-003, REQ-007) are validated by the same contract: absent
    means unset, and nothing here invents a threshold value (U-1).
    """
    if section is None:
        raise ConfigMissingError(f"{filename} carries no [dedup] table")
    if not isinstance(section, Mapping):
        raise ConfigParseError(filename, ValueError("[dedup] section must be a table"))

    db_path = section.get("db_path", str(dedup_db_dir() / Path(DEFAULT_DB_PATH).name))
    if not isinstance(db_path, str) or not db_path:
        raise ConfigParseError(
            filename, ValueError("dedup.db_path must be a non-empty string")
        )
    db = Path(db_path)
    if not db.is_absolute():
        raise ConfigParseError(
            filename, ValueError(f"dedup.db_path must be an absolute path: {db_path}")
        )
    expected = dedup_db_dir() / Path(DEFAULT_DB_PATH).name
    if db != expected:
        raise ConfigParseError(
            filename,
            ValueError(
                f"dedup.db_path {db_path} is not the canonical dedup store path "
                f"{expected} (the installation marker is scoped to the directory)"
            ),
        )

    unknown_keys = sorted(
        set(section)
        - {"db_path"}
        - set(_DEDUP_INT_KEYS)
        - set(DEDUP_OPTIONAL_INT_KEYS)
        - {"legal_hold_states"}
    )
    if unknown_keys:
        raise ConfigParseError(
            filename, ValueError(f"unknown dedup keys: {', '.join(unknown_keys)}")
        )

    values = {
        name: _validated_int(filename, section, name, spec[0], spec[1], spec[2])
        for name, spec in _DEDUP_INT_KEYS.items()
    }
    optional = {
        name: _validated_optional_int(filename, section, name, spec[0], spec[1])
        for name, spec in DEDUP_OPTIONAL_INT_KEYS.items()
    }
    return DedupStoreConfig(
        db_path=db_path,
        retention_days=values["retention_days"],
        pending_timeout_minutes=values["pending_timeout_minutes"],
        lease_seconds=values["lease_seconds"],
        max_attempts=values["max_attempts"],
        max_dedup_rows=optional["max_dedup_rows"],
        max_dedup_growth_per_hour=optional["max_dedup_growth_per_hour"],
        max_dedup_wal_mb=optional["max_dedup_wal_mb"],
        legal_hold_states=_validated_hold_states(filename, section),
    )
