#!/usr/bin/env python3
"""scripts/shared/security/result_dto.py — Security Validation result DTO and reason codes."""

from __future__ import annotations

import re
from collections.abc import Mapping
from dataclasses import dataclass
from enum import StrEnum

# Starting version values; posture_contract.py publishes the authoritative contract version.
DEFAULT_POLICY_VERSION = "1"
DEFAULT_CONTRACT_VERSION = "1"

REASON_OK = "ok"
REASON_CONFIG_MISSING = "config_missing"
REASON_CONFIG_INVALID = "config_invalid"
REASON_ALLOWLIST_EMPTY = "allowlist_empty"
REASON_ALLOWLIST_INVALID = "allowlist_invalid"
REASON_PATH_OUT_OF_BOUNDARY = "path_out_of_boundary"
REASON_SYMLINK_ESCAPE = "symlink_escape"
REASON_SANDBOX_BACKEND_MISSING = "sandbox_backend_missing"
REASON_SANDBOX_BACKEND_UNSUPPORTED = "sandbox_backend_unsupported"
REASON_AUTH_TOKEN_MISSING = "auth_token_missing"
REASON_PROTECTED_BRANCH_VIOLATION = "protected_branch_violation"
REASON_FORCE_PUSH_ENABLED = "force_push_enabled"
REASON_WILDCARD_RANGE_INVALID = "wildcard_range_invalid"
REASON_DESTRUCTIVE_GUARD_MISSING = "destructive_guard_missing"
REASON_DELETE_LIMIT_INVALID = "delete_limit_invalid"
REASON_ATOMIC_WRITE_DISABLED = "atomic_write_disabled"
REASON_DB_PATH_INVALID = "db_path_invalid"
REASON_INDEX_PATH_INVALID = "index_path_invalid"
REASON_ALLOWED_DIR_INVALID = "allowed_dir_invalid"
REASON_DEPENDENCY_UNREACHABLE = "dependency_unreachable"
REASON_DIRTY_WORKTREE = "dirty_worktree"
REASON_DETACHED_HEAD = "detached_head"
REASON_REF_GUARD_INVALID = "ref_guard_invalid"
REASON_OWN_CONFIG_VIOLATION = "own_config_violation"
REASON_NOT_APPLICABLE = "not_applicable"
REASON_POSTURE_MISSING = "posture_missing"
REASON_CONTRACT_VERSION_MISMATCH = "contract_version_mismatch"
REASON_CHECK_SET_MISMATCH = "check_set_mismatch"
REASON_FINGERPRINT_MISMATCH = "fingerprint_mismatch"
REASON_SERVER_KEY_MISMATCH = "server_key_mismatch"

# Referencing the constants here makes a mistyped name fail at import, not at comparison.
SECURITY_REASON_CODES: frozenset[str] = frozenset(
    {
        REASON_OK,
        REASON_CONFIG_MISSING,
        REASON_CONFIG_INVALID,
        REASON_ALLOWLIST_EMPTY,
        REASON_ALLOWLIST_INVALID,
        REASON_PATH_OUT_OF_BOUNDARY,
        REASON_SYMLINK_ESCAPE,
        REASON_SANDBOX_BACKEND_MISSING,
        REASON_SANDBOX_BACKEND_UNSUPPORTED,
        REASON_AUTH_TOKEN_MISSING,
        REASON_PROTECTED_BRANCH_VIOLATION,
        REASON_FORCE_PUSH_ENABLED,
        REASON_WILDCARD_RANGE_INVALID,
        REASON_DESTRUCTIVE_GUARD_MISSING,
        REASON_DELETE_LIMIT_INVALID,
        REASON_ATOMIC_WRITE_DISABLED,
        REASON_DB_PATH_INVALID,
        REASON_INDEX_PATH_INVALID,
        REASON_ALLOWED_DIR_INVALID,
        REASON_DEPENDENCY_UNREACHABLE,
        REASON_DIRTY_WORKTREE,
        REASON_DETACHED_HEAD,
        REASON_REF_GUARD_INVALID,
        REASON_OWN_CONFIG_VIOLATION,
        REASON_NOT_APPLICABLE,
        REASON_POSTURE_MISSING,
        REASON_CONTRACT_VERSION_MISMATCH,
        REASON_CHECK_SET_MISMATCH,
        REASON_FINGERPRINT_MISMATCH,
        REASON_SERVER_KEY_MISMATCH,
    }
)

_FINGERPRINT_RE = re.compile(r"\A[0-9a-f]{64}\Z")
# A path of at least two segments: a sensitive path must never travel inside a result.
_ABSOLUTE_PATH_RE = re.compile(r"/[A-Za-z0-9._-]+/[A-Za-z0-9._\-/]*")
# Assignment-shaped secrets and known token prefixes. REASON_AUTH_TOKEN_MISSING names a
# field without carrying a value, so it is not a match.
_SECRET_ASSIGN_RE = re.compile(
    r"(?i)\b(?:token|secret|password|passwd|api[_-]?key|authorization)\s*[:=]\s*\S"
)
_SECRET_PREFIX_RE = re.compile(
    r"\b(?:sk|ghp|xox[baprs])-[A-Za-z0-9_-]{8,}|\bBearer\s+\S"
)
_TOML_SECTION_RE = re.compile(r"(?m)^\s*\[[A-Za-z0-9_.-]+\]\s*$")
_MAX_PLAIN_TEXT_LEN = 120


class SecurityCheckStatus(StrEnum):
    """Outcome of one Security Validation check. Only FAILED blocks Ready."""

    OK = "ok"
    WARNING = "warning"
    FAILED = "failed"
    NOT_APPLICABLE = "not_applicable"


def assert_non_secret(value: str, field_name: str) -> None:
    """Reject a value carrying a Secret, a sensitive path, or a config body.

    Raises:
        ValueError: the value is longer than a non-secret summary may be, contains a
            two-segment absolute path, a credential-shaped value, or a config section
            header. The offending value is never echoed into the message.
    """
    if len(value) > _MAX_PLAIN_TEXT_LEN:
        raise ValueError(f"{field_name} is longer than a non-secret summary may be")
    if _ABSOLUTE_PATH_RE.search(value):
        raise ValueError(f"{field_name} contains an absolute path")
    if _SECRET_ASSIGN_RE.search(value) or _SECRET_PREFIX_RE.search(value):
        raise ValueError(f"{field_name} contains a credential-shaped value")
    if _TOML_SECTION_RE.search(value):
        raise ValueError(f"{field_name} contains a config section header")


@dataclass(frozen=True)
class SecurityCheckResult:
    """One Security Validation result: the only type a server returns and the Agent reads."""

    check_id: str
    status: SecurityCheckStatus
    reason_code: str
    message: str
    policy_version: str = DEFAULT_POLICY_VERSION
    contract_version: str = DEFAULT_CONTRACT_VERSION
    ready: bool = True
    fingerprint: str = ""

    def __post_init__(self) -> None:
        """Fail closed at construction rather than at consumption."""
        if not self.check_id:
            raise ValueError("check_id must not be empty")
        if self.reason_code not in SECURITY_REASON_CODES:
            raise ValueError(f"unknown reason_code for check_id {self.check_id}")
        if self.status is SecurityCheckStatus.OK and self.reason_code != REASON_OK:
            raise ValueError(f"status OK requires reason ok: check_id {self.check_id}")
        if self.status is SecurityCheckStatus.WARNING and self.reason_code == REASON_OK:
            raise ValueError(
                f"status WARNING must name a reason: check_id {self.check_id}"
            )
        assert_non_secret(self.check_id, "check_id")
        assert_non_secret(self.message, "message")
        if self.fingerprint and not _FINGERPRINT_RE.match(self.fingerprint):
            raise ValueError("fingerprint must be 64 lowercase hex characters")

    def to_dict(self) -> dict[str, str]:
        """JSON-safe form for the /health security block; versions ride at posture level."""
        return {
            "id": self.check_id,
            "status": str(self.status),
            "reason_code": self.reason_code,
            "message": self.message,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, object]) -> SecurityCheckResult:
        """Rebuild a check result from the to_dict() form a server published."""
        missing = {"id", "status", "reason_code", "message"} - set(data)
        if missing:
            raise ValueError(f"check result is missing keys: {sorted(missing)}")
        return cls(
            check_id=str(data["id"]),
            status=SecurityCheckStatus(str(data["status"])),
            reason_code=str(data["reason_code"]),
            message=str(data["message"]),
        )
