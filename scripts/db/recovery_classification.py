#!/usr/bin/env python3
"""scripts/db/recovery_classification.py — DbCondition states and the error-to-state mapping.

Owns the states a recovery run reports and the mapping from a caught SQLite error to one
of them. The physical integrity check, the restore steps, and the RecoveryResult policy
live in db.recovery, which calls this mapping; a state here is a label, never a decision
about what to do with it.
"""

import sqlite3
from enum import StrEnum


class DbCondition(StrEnum):
    """Classification of database state/failure."""

    HEALTHY = "healthy"
    CORRUPTION = "corruption"
    LOCK_CONTENTION = "lock_contention"
    PERMISSION_FAILURE = "permission_failure"
    INVALID_FORMAT = "invalid_format"
    UNKNOWN = "unknown"
    MISSING = "missing"


# sqlite_errorcode -> condition for the failures SQLite identifies by code
# (5/6 = SQLITE_BUSY / SQLITE_LOCKED, 8 = SQLITE_READONLY).
_ERRORCODE_CONDITIONS: dict[int, DbCondition] = {
    5: DbCondition.LOCK_CONTENTION,
    6: DbCondition.LOCK_CONTENTION,
    8: DbCondition.PERMISSION_FAILURE,
}

# Message fallbacks, in priority order, for the conditions error codes do not cover.
_MESSAGE_CONDITIONS: tuple[tuple[tuple[str, ...], DbCondition], ...] = (
    (("database is locked", "busy"), DbCondition.LOCK_CONTENTION),
    (("permission denied", "readonly"), DbCondition.PERMISSION_FAILURE),
)

# Signal the SQLite C library reports when the file is not a database at all.
_INVALID_FORMAT_SIGNAL = "file is not a database"


def _classify_operational_error(e: sqlite3.OperationalError) -> DbCondition:
    """Classify an OperationalError: error code first, message substrings second."""
    errcode: int | None = getattr(e, "sqlite_errorcode", None)
    if errcode is not None and errcode in _ERRORCODE_CONDITIONS:
        return _ERRORCODE_CONDITIONS[errcode]
    msg = str(e).lower()
    for tokens, condition in _MESSAGE_CONDITIONS:
        if any(token in msg for token in tokens):
            return condition
    return DbCondition.UNKNOWN


def _classify_error(e: Exception) -> DbCondition:
    """Classify a caught exception into a DbCondition.

    Uses sqlite_errorcode where available (Python 3.14+), falling back to
    substring matching for conditions not covered by error codes.
    Priority: INVALID_FORMAT via message > lock/permission via error code >
    CORRUPTION > UNKNOWN.

    The INVALID_FORMAT signal is checked for every sqlite3 error, OperationalError
    included: SQLite raises an OperationalError when it reads the header of a file
    that is not a database, and classifying that as UNKNOWN would hide the reason
    the file cannot be opened.
    """
    if isinstance(e, (sqlite3.Error, ValueError)) and _INVALID_FORMAT_SIGNAL in str(e):
        return DbCondition.INVALID_FORMAT
    if isinstance(e, sqlite3.OperationalError):
        return _classify_operational_error(e)
    if isinstance(e, (sqlite3.DatabaseError, ValueError)):
        return DbCondition.CORRUPTION
    return DbCondition.UNKNOWN
