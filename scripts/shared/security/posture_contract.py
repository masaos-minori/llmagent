#!/usr/bin/env python3
"""scripts/shared/security/posture_contract.py — versioned, non-secret Security Posture contract."""

from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Mapping
from dataclasses import dataclass

from shared.security.result_dto import (
    DEFAULT_CONTRACT_VERSION,
    SecurityCheckResult,
    SecurityCheckStatus,
    assert_non_secret,
)

# One version literal, held in result_dto, so a check and its posture cannot disagree.
SECURITY_CONTRACT_VERSION = DEFAULT_CONTRACT_VERSION
# Status string a consumer may render for a validated posture; `validated` is the authority.
POSTURE_STATUS_OK = "ok"

CHECK_ID_OWN_CONFIG_ONLY = "common.own_config_only"
CHECK_ID_AUTH_TOKEN = "common.auth_token"
CHECK_ID_PUBLISHED_TOOLS = "common.published_tools"
COMMON_CHECK_IDS: tuple[str, ...] = (
    CHECK_ID_OWN_CONFIG_ONLY,
    CHECK_ID_AUTH_TOKEN,
    CHECK_ID_PUBLISHED_TOOLS,
)

# The check ids each server's posture must carry: the three common checks plus that server's
# own checks, in the order the startup flow emits them. Extra checks are allowed.
REQUIRED_CHECK_IDS: Mapping[str, tuple[str, ...]] = {
    "shell": COMMON_CHECK_IDS
    + (
        "server.sandbox_backend",
        "server.sandbox_binary",
        "server.command_allowlist",
        "server.resource_limits",
    ),
    "git": COMMON_CHECK_IDS
    + (
        "server.repo_allowlist",
        "server.repo_allowlist_resolvable",
        "server.read_only_mode",
        "server.protected_branch_config",
    ),
    "github": COMMON_CHECK_IDS
    + (
        "server.repo_allowlist",
        "server.force_push_policy",
        "server.pr_review_required",
        "server.protected_branches",
        "server.path_denylist",
        "server.max_file_size",
        "server.audit_log_writable",
        "server.per_page_bounds",
    ),
    "cicd": COMMON_CHECK_IDS
    + (
        "server.repo_allowlist",
        "server.workflow_allowlist",
        "server.workflow_pattern_valid",
        "server.backend_available",
    ),
    "file_read": COMMON_CHECK_IDS
    + (
        "server.allowed_dirs_configured",
        "server.allowed_dirs_exist",
        "server.max_read_bytes",
    ),
    "file_write": COMMON_CHECK_IDS
    + (
        "server.allowed_dirs_configured",
        "server.allowed_dirs_exist",
        "server.max_write_bytes",
        "server.write_dirs_writable",
        "server.supported_extensions",
    ),
    "file_delete": COMMON_CHECK_IDS
    + (
        "server.allowed_dirs_configured",
        "server.allowed_dirs_exist",
        "server.allowed_root_protected",
        "server.audit_log_writable",
    ),
    "rag_pipeline": COMMON_CHECK_IDS
    + (
        "server.embed_url_configured",
        "server.llm_url_configured",
        "server.rag_db_path_configured",
        "server.sqlite_vec_available",
        "server.top_k_bounds",
        "server.min_score_valid",
        "server.refiner_limits",
    ),
    "mdq": COMMON_CHECK_IDS
    + (
        "server.auth_token_configured",
        "server.allowed_dirs_configured",
        "server.allowed_dirs_exist",
        "server.db_path_valid",
        "server.schema_valid",
        "server.index_available",
    ),
    "web_search": COMMON_CHECK_IDS
    + (
        "server.results_bounds",
        "server.search_timeout_valid",
        "server.browser_timeout_valid",
        "server.browser_response_limit",
        "server.browser_allowlist",
    ),
}

_FINGERPRINT_RE = re.compile(r"\A[0-9a-f]{64}\Z")
_MAX_SCALAR_TUPLE_LEN = 8


def _scalar(key: str, value: object) -> object:
    """Return the value unchanged when it is a non-secret scalar a fingerprint may hash."""
    if value is None or isinstance(value, (bool, int, float)):
        return value
    if isinstance(value, str):
        # The same non-secret rule a check message carries: a token, a sensitive path, or
        # a config body must not reach the digest, let alone the posture.
        assert_non_secret(value, key)
        return value
    raise ValueError(f"{key} carries a value that is not a scalar")


def compute_config_fingerprint(values: Mapping[str, object]) -> str:
    """Hash a server's own normalized non-secret config view into a 64-hex digest.

    Raises:
        ValueError: a key is not a non-empty string, or a value is a Mapping, list, set,
            a tuple longer than the scalar limit, a tuple holding a non-scalar, or a
            string longer than a non-secret summary may be. The offending value is not echoed.
    """
    normalized: dict[str, object] = {}
    for key, value in values.items():
        if not isinstance(key, str) or not key:
            raise ValueError("fingerprint input must use non-empty string keys")
        if isinstance(value, tuple):
            if len(value) > _MAX_SCALAR_TUPLE_LEN:
                raise ValueError(
                    f"{key} carries a tuple longer than a fingerprint input may be"
                )
            normalized[key] = tuple(_scalar(key, item) for item in value)
        elif isinstance(value, (Mapping, list, set, frozenset)):
            raise ValueError(
                f"{key} carries a collection value; only scalars may be hashed"
            )
        else:
            normalized[key] = _scalar(key, value)
    canonical = json.dumps(
        normalized, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class SecurityPosture:
    """The versioned, non-secret security posture one MCP server publishes on /health."""

    contract_version: str
    server_key: str
    policy_version: str
    validated: bool
    ready: bool
    fingerprint: str
    checks: tuple[SecurityCheckResult, ...]

    def __post_init__(self) -> None:
        """Reject an envelope that cannot be published as a contract."""
        if not isinstance(self.checks, tuple):
            object.__setattr__(self, "checks", tuple(self.checks))
        if not self.contract_version:
            raise ValueError("contract_version must not be empty")
        if not self.server_key:
            raise ValueError("server_key must not be empty")
        if not self.policy_version:
            raise ValueError("policy_version must not be empty")
        if not self.checks:
            raise ValueError(
                f"posture for {self.server_key} must carry at least one check"
            )
        if not _FINGERPRINT_RE.match(self.fingerprint):
            raise ValueError("fingerprint must be 64 lowercase hex characters")
        if self.validated and any(
            check.status is SecurityCheckStatus.FAILED for check in self.checks
        ):
            raise ValueError(
                f"posture for {self.server_key} cannot be validated with a FAILED check"
            )
        if self.ready and not self.validated:
            raise ValueError(
                f"posture for {self.server_key} cannot be ready without validation"
            )

    def to_dict(self) -> dict[str, object]:
        """JSON-safe form published as the /health `security` block."""
        return {
            "contract_version": self.contract_version,
            "server_key": self.server_key,
            "policy_version": self.policy_version,
            "validated": self.validated,
            "ready": self.ready,
            "fingerprint": self.fingerprint,
            "checks": [check.to_dict() for check in self.checks],
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, object]) -> SecurityPosture:
        """Rebuild a posture from the `security` block another process published."""
        required = {
            "contract_version",
            "server_key",
            "policy_version",
            "validated",
            "ready",
            "fingerprint",
            "checks",
        }
        missing = required - set(data)
        if missing:
            raise ValueError(f"posture is missing keys: {sorted(missing)}")
        raw_checks = data["checks"]
        if not isinstance(raw_checks, list):
            raise ValueError("posture checks must be a list")
        checks: list[SecurityCheckResult] = []
        for entry in raw_checks:
            if not isinstance(entry, Mapping):
                raise ValueError("posture check entry must be a mapping")
            checks.append(SecurityCheckResult.from_dict(entry))
        return cls(
            contract_version=str(data["contract_version"]),
            server_key=str(data["server_key"]),
            policy_version=str(data["policy_version"]),
            validated=bool(data["validated"]),
            ready=bool(data["ready"]),
            fingerprint=str(data["fingerprint"]),
            checks=tuple(checks),
        )
