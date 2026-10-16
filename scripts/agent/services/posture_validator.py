"""scripts/agent/services/posture_validator.py

Agent-side Security Posture contract validation — parse_posture() reads the `security` block a server
published on /health, validate_posture() checks a posture against the shared contract, and
compare_fingerprint() reports posture drift for a server key between two probes.

Dependency direction: posture_validator → shared.security
Import from here:  from agent.services.posture_validator import parse_posture, validate_posture
"""

from __future__ import annotations

import re
import threading
from collections.abc import Mapping
from dataclasses import dataclass

from shared.security.posture_contract import (
    REQUIRED_CHECK_IDS,
    SECURITY_CONTRACT_VERSION,
    SecurityPosture,
)
from shared.security.result_dto import (
    REASON_CHECK_SET_MISMATCH,
    REASON_CONFIG_INVALID,
    REASON_CONTRACT_VERSION_MISMATCH,
    REASON_FINGERPRINT_MISMATCH,
    REASON_OK,
    REASON_POSTURE_MISSING,
    REASON_SERVER_KEY_MISMATCH,
)

_FINGERPRINT_RE = re.compile(r"\A[0-9a-f]{64}\Z")

SECURITY_BODY_KEY = "security"


@dataclass(frozen=True)
class PostureValidationResult:
    """One contract verdict the classification layer (row `18`) consumes.

    `server_key` is always the key the Agent asked about, not the key the posture claims, so a
    mismatched posture still groups under the server the Agent probed.
    """

    server_key: str
    accepted: bool
    reason_code: str
    message: str
    posture: SecurityPosture | None = None


def _rejected(
    server_key: str, reason_code: str, message: str
) -> PostureValidationResult:
    """Build a rejection.

    The message is chosen here from a fixed vocabulary so that nothing a server wrote can reach an
    Agent log through it.
    """
    return PostureValidationResult(
        server_key=server_key,
        accepted=False,
        reason_code=reason_code,
        message=message,
    )


def _accepted(
    server_key: str,
    message: str,
    posture: SecurityPosture,
) -> PostureValidationResult:
    """Build an acceptance carrying the posture the caller needs for gating."""
    return PostureValidationResult(
        server_key=server_key,
        accepted=True,
        reason_code=REASON_OK,
        message=message,
        posture=posture,
    )


def parse_posture(
    body: Mapping[str, object], server_key: str
) -> PostureValidationResult:
    """Read the `security` block out of a /health body and validate what it holds.

    Never raises. A server that publishes no posture, publishes a body that is not a posture, or
    publishes a check the contract DTO cannot represent is rejected: the Agent does not treat an
    unreadable posture as a passing one.
    """
    raw = body.get(SECURITY_BODY_KEY)
    if raw is None:
        return _rejected(
            server_key, REASON_POSTURE_MISSING, "health body carries no security block"
        )
    if not isinstance(raw, Mapping):
        return _rejected(
            server_key, REASON_CONFIG_INVALID, "security block is not a mapping"
        )
    try:
        posture = SecurityPosture.from_dict(raw)
    except (TypeError, ValueError):
        # The DTO reports which key or value it rejected, and that text came from the server, so the
        # Agent records the failure kind only.
        return _rejected(
            server_key,
            REASON_CONFIG_INVALID,
            "security block does not match the posture contract",
        )
    return validate_posture(posture, expected_server_key=server_key)


def validate_posture(
    posture: SecurityPosture,
    *,
    expected_server_key: str,
) -> PostureValidationResult:
    """Check a posture against the shared contract, in the fixed order the contract names.

    Never raises: every violation is a rejection with a reason code, because REQ-013 classifies on
    the reason and not on an exception.
    """
    if posture.server_key != expected_server_key:
        return _rejected(
            expected_server_key,
            REASON_SERVER_KEY_MISMATCH,
            "posture answers for a different server key",
        )
    if posture.contract_version != SECURITY_CONTRACT_VERSION:
        return _rejected(
            expected_server_key,
            REASON_CONTRACT_VERSION_MISMATCH,
            f"posture contract version is not the Agent's version {SECURITY_CONTRACT_VERSION}",
        )
    verdict = _check_set_verdict(posture, expected_server_key)
    if verdict is not None:
        return verdict
    if not _FINGERPRINT_RE.match(posture.fingerprint):
        return _rejected(
            expected_server_key,
            REASON_CONFIG_INVALID,
            "posture fingerprint is not 64 lowercase hex characters",
        )
    if posture.ready and not posture.validated:
        return _rejected(
            expected_server_key,
            REASON_CONFIG_INVALID,
            "posture reports ready without validation",
        )
    return _accepted(expected_server_key, "posture satisfies the contract", posture)


def _check_set_verdict(
    posture: SecurityPosture,
    expected_server_key: str,
) -> PostureValidationResult | None:
    """Reject a posture that omits a required check; extra checks are allowed.

    The names in the message come from REQUIRED_CHECK_IDS, which is the Agent's own contract, so the
    message stays free of server-supplied text.
    """
    required = REQUIRED_CHECK_IDS.get(expected_server_key)
    if not required:
        return _rejected(
            expected_server_key,
            REASON_CHECK_SET_MISMATCH,
            "the contract defines no required check set for this server key",
        )
    present = {check.check_id for check in posture.checks}
    missing = sorted(set(required) - present)
    if missing:
        return _rejected(
            expected_server_key,
            REASON_CHECK_SET_MISMATCH,
            f"posture omits required check(s): {', '.join(missing)}",
        )
    return None


_last_fingerprints: dict[str, str] = {}
_fingerprint_lock = threading.Lock()


def compare_fingerprint(
    server_key: str, posture: SecurityPosture
) -> PostureValidationResult:
    """Report whether a server's fingerprint changed since the last posture seen for that key.

    The Agent never recomputes a fingerprint: doing so means reading the server's own config file,
    which REQ-017 removes. The first posture seen for a key is accepted and remembered, so drift is
    reported from the second posture onward. Returns a verdict rather than a bool for the same reason
    the validator does: the reason code has to reach the classifier.
    """
    with _fingerprint_lock:
        previous = _last_fingerprints.get(server_key)
        _last_fingerprints[server_key] = posture.fingerprint
    if previous is not None and previous != posture.fingerprint:
        return _rejected(
            server_key,
            REASON_FINGERPRINT_MISMATCH,
            "posture fingerprint changed since the last posture seen for this server",
        )
    return _accepted(
        server_key, "posture fingerprint matches the last one seen", posture
    )


def reset_fingerprint_state() -> None:
    """Clear the process-local fingerprint map, for tests."""
    with _fingerprint_lock:
        _last_fingerprints.clear()
