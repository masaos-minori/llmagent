"""scripts/shared/mcp_dedup_schema.py — Canonical schema and state vocabularies.

The DDL shape of the disposable dedup store, its schema fingerprint, and the
start/acquisition state vocabularies. Split from shared/mcp_dedup.py by the
scripts/ module size gate (24576 B); re-exported through the shared.mcp_dedup
facade where consumers need them.
"""

from __future__ import annotations

import hashlib

TERMINAL_STATES = frozenset({"completed", "failed", "interrupted"})
START_STATES = frozenset(
    {
        "first_initialization",
        "healthy",
        "lost",
        "replaced",
        "legacy_or_unverified",
        "schema_mismatch",
        "identity_mismatch",
    }
)
ACQUISITION_STATES = frozenset(
    {
        "acquired",
        "replay_completed",
        "in_progress",
        "reconciliation_required",
        "outcome_unknown",
        "contract_mismatch",
        "replay_unavailable",
    }
)

# Stored-result cap: payloads over this many serialized characters are replaced
# by a truncated sentinel (preview + hash of the full payload). Tunable; raise
# if replayed results are observed to be truncated in normal operation.
RESULT_MAX_CHARS = 8000
RESULT_PREVIEW_CHARS = 1000

_USER_VERSION = 1
_INSTALL_MARKER_NAME = ".mcp_dedup_installed"

_SCHEMA = """
CREATE TABLE IF NOT EXISTS dedup_call_state (
    key TEXT PRIMARY KEY,
    tool_name TEXT NOT NULL,
    args_hash TEXT NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('pending', 'completed', 'failed', 'interrupted')),
    owner_id TEXT,
    lease_expires_epoch REAL,
    attempt_number INTEGER NOT NULL DEFAULT 1,
    snapshot_json TEXT NOT NULL,
    created_epoch REAL NOT NULL,
    updated_epoch REAL NOT NULL,
    result_json TEXT
)
"""
_STORE_META_SCHEMA = """
CREATE TABLE IF NOT EXISTS store_meta (
    store_uuid TEXT NOT NULL,
    generation INTEGER NOT NULL,
    schema_fingerprint TEXT NOT NULL,
    config_fingerprint TEXT NOT NULL,
    created_epoch REAL NOT NULL
)
"""
_ATTEMPT_HISTORY_SCHEMA = """
CREATE TABLE IF NOT EXISTS call_attempt_history (
    key TEXT NOT NULL,
    attempt_number INTEGER NOT NULL,
    owner_id TEXT,
    outcome TEXT NOT NULL,
    detail TEXT,
    recorded_epoch REAL NOT NULL
)
"""
_INDEXES = (
    "CREATE INDEX IF NOT EXISTS idx_dcs_updated ON dedup_call_state(updated_epoch)",
    "CREATE INDEX IF NOT EXISTS idx_dcs_status ON dedup_call_state(status)",
    "CREATE INDEX IF NOT EXISTS idx_cah_key ON call_attempt_history(key)",
)
# Canonical shape of this database: the fingerprint input for open-time
# validation (ADR-008; the user_version stamp records identity, it is not a
# migration mechanism).
_CANONICAL_DDL = (
    _SCHEMA.rstrip()
    + ";\n"
    + _STORE_META_SCHEMA.rstrip()
    + ";\n"
    + _ATTEMPT_HISTORY_SCHEMA.rstrip()
    + ";\n"
    + "\n".join(ddl.rstrip() + ";" for ddl in _INDEXES)
)
_SCHEMA_FINGERPRINT = hashlib.sha256(_CANONICAL_DDL.encode("utf-8")).hexdigest()
