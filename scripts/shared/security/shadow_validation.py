#!/usr/bin/env python3
"""scripts/shared/security/shadow_validation.py — compare the old Agent audit with new self-validation."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from enum import StrEnum

from shared.security.posture_contract import SECURITY_CONTRACT_VERSION, SecurityPosture
from shared.security.result_dto import SecurityCheckStatus, assert_non_secret

# The old audit's only signal is a warning, so a server check counts as flagged when it is FAILED
# or WARNING; comparing flagged sets is what makes the two sides comparable.
_FLAGGED_STATUSES = (SecurityCheckStatus.FAILED, SecurityCheckStatus.WARNING)

# A posture whose own server key cannot be named in a report is reported under this placeholder.
_UNNAMED_SERVER = "unknown"


class ShadowOutcome(StrEnum):
    """The six comparison outcomes the Plan fixes for Shadow Validation (REQ-016)."""

    MATCH_PASS = "match_pass"
    MATCH_FAIL = "match_fail"
    AGENT_ONLY_FAIL = "agent_only_fail"
    SERVER_ONLY_FAIL = "server_only_fail"
    CHECKSET_MISMATCH = "checkset_mismatch"
    CONTRACT_ERROR = "contract_error"


@dataclass(frozen=True)
class ShadowComparison:
    """One server's Shadow Validation result: the check sets in scope and where they disagree.

    Every id list is stored sorted, because the Plan compares two comparisons directly.
    """

    outcome: ShadowOutcome
    server_key: str
    matched_check_ids: tuple[str, ...] = ()
    agent_only_check_ids: tuple[str, ...] = ()
    server_only_check_ids: tuple[str, ...] = ()
    status_conflicts: tuple[str, ...] = ()


def _contract_error(server_key: str) -> ShadowComparison:
    """A comparison that cannot be trusted because one side broke the contract."""
    return ShadowComparison(outcome=ShadowOutcome.CONTRACT_ERROR, server_key=server_key)


def _posture_is_wellformed(posture: SecurityPosture) -> bool:
    """Confirm the posture carries one contract version and no duplicate check id."""
    if posture.contract_version != SECURITY_CONTRACT_VERSION:
        return False
    if not all(
        check.contract_version == posture.contract_version
        and check.policy_version == posture.policy_version
        for check in posture.checks
    ):
        return False
    return len({check.check_id for check in posture.checks}) == len(posture.checks)


def compare_shadow_results(
    audit_warnings: Iterable[str],
    posture: SecurityPosture,
    audit_check_ids: Mapping[str, str],
) -> ShadowComparison:
    """Compare one old-audit outcome list with one server posture (REQ-016).

    `audit_check_ids` maps each old-audit warning text to the check id the new side uses for the
    same rule. The mapping lives in the driving test and is retired together with the audit.
    """
    warnings = tuple(audit_warnings)
    try:
        assert_non_secret(posture.server_key, "server_key")
    except ValueError:
        return _contract_error(_UNNAMED_SERVER)
    server_key = posture.server_key
    if not _posture_is_wellformed(posture):
        return _contract_error(server_key)

    agent_ids: set[str] = set()
    flagged_agent: set[str] = set()
    for warning_text, check_id in audit_check_ids.items():
        try:
            assert_non_secret(check_id, "audit_check_id")
        except ValueError:
            return _contract_error(server_key)
        agent_ids.add(check_id)
        if warning_text in warnings:
            flagged_agent.add(check_id)

    server_ids = {check.check_id for check in posture.checks}
    flagged_server = {
        check.check_id for check in posture.checks if check.status in _FLAGGED_STATUSES
    }

    agent_only = agent_ids - server_ids
    server_only = server_ids - agent_ids
    conflicts = flagged_agent ^ flagged_server
    if agent_only or server_only:
        outcome = ShadowOutcome.CHECKSET_MISMATCH
    elif flagged_agent == flagged_server:
        outcome = (
            ShadowOutcome.MATCH_FAIL if flagged_agent else ShadowOutcome.MATCH_PASS
        )
    elif flagged_agent - flagged_server:
        outcome = ShadowOutcome.AGENT_ONLY_FAIL
    else:
        outcome = ShadowOutcome.SERVER_ONLY_FAIL
    return ShadowComparison(
        outcome=outcome,
        server_key=server_key,
        matched_check_ids=tuple(sorted(agent_ids & server_ids)),
        agent_only_check_ids=tuple(sorted(agent_only)),
        server_only_check_ids=tuple(sorted(server_only)),
        status_conflicts=tuple(sorted(conflicts)),
    )


def format_shadow_report(comparison: ShadowComparison) -> str:
    """One non-secret log line per server: outcome and sorted check ids, never message text."""
    return (
        f"shadow {comparison.server_key}: outcome={comparison.outcome}"
        f" matched={','.join(comparison.matched_check_ids)}"
        f" agent_only={','.join(comparison.agent_only_check_ids)}"
        f" server_only={','.join(comparison.server_only_check_ids)}"
        f" conflicts={','.join(comparison.status_conflicts)}"
    )
