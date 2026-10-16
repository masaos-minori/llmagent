"""tests/mcp_servers/git/test_git_security_validation.py

Tests for scripts/mcp_servers/git/git_security.py: validate_git_security() reports Git's own
configuration rules as posture checks before HTTP bind, and GitSecurityGuards.validate_security()
reports the installed state of the guards.
"""

from __future__ import annotations

from pathlib import Path
from typing import cast
from unittest.mock import MagicMock

from mcp_servers.git import repository_state
from mcp_servers.git.git_security import (
    GitSecurityGuards,
    validate_git_security,
)
from shared.security.posture_contract import COMMON_CHECK_IDS, REQUIRED_CHECK_IDS
from shared.security.result_dto import (
    REASON_ALLOWED_DIR_INVALID,
    REASON_ALLOWLIST_EMPTY,
    REASON_DEPENDENCY_UNREACHABLE,
    REASON_NOT_APPLICABLE,
    REASON_OK,
    SecurityCheckResult,
    SecurityCheckStatus,
)

GIT_SERVER_CHECK_IDS = (
    "server.repo_allowlist",
    "server.repo_allowlist_resolvable",
    "server.read_only_mode",
    "server.protected_branch_config",
)
# A configured root whose own text is not a canonical path: the runtime containment check
# rejects it, so the startup check must reject it too.
_NON_CANONICAL_ROOT = "/tmp/opencode/git-repo/../git-repo"


def _results(
    allowed_repo_paths: tuple[str, ...],
    read_only: bool = True,
) -> dict[str, SecurityCheckResult]:
    """Git's check results keyed by check id."""
    return {
        result.check_id: result
        for result in validate_git_security(allowed_repo_paths, read_only)
    }


class TestRepoAllowlist:
    """An empty allowlist means git-mcp denies every operation: a startup failure (REQ-006)."""

    def test_empty_allowlist_fails(self) -> None:
        result = _results(())["server.repo_allowlist"]
        assert result.status is SecurityCheckStatus.FAILED
        assert result.reason_code == REASON_ALLOWLIST_EMPTY

    def test_non_empty_allowlist_is_ok(self, tmp_path: Path) -> None:
        result = _results((str(tmp_path),))["server.repo_allowlist"]
        assert result.status is SecurityCheckStatus.OK
        assert result.reason_code == REASON_OK

    def test_resolvable_is_not_applicable_when_nothing_is_configured(self) -> None:
        result = _results(())["server.repo_allowlist_resolvable"]
        assert result.status is SecurityCheckStatus.NOT_APPLICABLE
        assert result.reason_code == REASON_NOT_APPLICABLE


class TestRepoAllowlistResolvable:
    """A configured root must resolve and be contained in the allowlist it belongs to."""

    def test_canonical_root_is_ok(self, tmp_path: Path) -> None:
        result = _results((str(tmp_path),))["server.repo_allowlist_resolvable"]
        assert result.status is SecurityCheckStatus.OK
        assert result.reason_code == REASON_OK

    def test_empty_root_entry_fails(self, tmp_path: Path) -> None:
        results = _results((str(tmp_path), ""))
        result = results["server.repo_allowlist_resolvable"]
        assert result.status is SecurityCheckStatus.FAILED
        assert result.reason_code == REASON_ALLOWED_DIR_INVALID

    def test_non_canonical_root_fails(self) -> None:
        result = _results((_NON_CANONICAL_ROOT,))["server.repo_allowlist_resolvable"]
        assert result.status is SecurityCheckStatus.FAILED
        assert result.reason_code == REASON_ALLOWED_DIR_INVALID

    def test_failure_reports_the_count_and_not_the_roots(self, tmp_path: Path) -> None:
        roots = (str(tmp_path), "", _NON_CANONICAL_ROOT)
        result = _results(roots)["server.repo_allowlist_resolvable"]
        assert "2 of 3" in result.message
        for root in roots:
            if root:
                assert root not in result.message


class TestReadOnlyMode:
    """The write guard is reported explicitly instead of being skipped (Plan Design)."""

    def test_read_only_true_is_not_applicable(self, tmp_path: Path) -> None:
        result = _results((str(tmp_path),), read_only=True)["server.read_only_mode"]
        assert result.status is SecurityCheckStatus.NOT_APPLICABLE
        assert result.reason_code == REASON_NOT_APPLICABLE

    def test_read_only_false_is_ok(self, tmp_path: Path) -> None:
        result = _results((str(tmp_path),), read_only=False)["server.read_only_mode"]
        assert result.status is SecurityCheckStatus.OK
        assert result.reason_code == REASON_OK


class TestProtectedBranchConfig:
    """The config-only view reports the rule as installed; state absence is the guards' view."""

    def test_config_view_is_ok(self, tmp_path: Path) -> None:
        result = _results((str(tmp_path),))["server.protected_branch_config"]
        assert result.status is SecurityCheckStatus.OK
        assert result.reason_code == REASON_OK


class TestCheckSet:
    """The check set is identical for every configuration so row 05 can compare it."""

    def test_ids_match_the_frozen_contract(self) -> None:
        expected = tuple(
            check_id
            for check_id in REQUIRED_CHECK_IDS["git"]
            if check_id not in COMMON_CHECK_IDS
        )
        assert expected == GIT_SERVER_CHECK_IDS

    def test_order_is_fixed(self) -> None:
        assert [result.check_id for result in validate_git_security((), True)] == list(
            GIT_SERVER_CHECK_IDS
        )

    def test_check_set_is_identical_across_configurations(self, tmp_path: Path) -> None:
        configurations = (
            ((), True),
            ((str(tmp_path),), True),
            ((str(tmp_path),), False),
            ((str(tmp_path), ""), False),
        )
        for allowed_repo_paths, read_only in configurations:
            produced = validate_git_security(allowed_repo_paths, read_only)
            assert [result.check_id for result in produced] == list(
                GIT_SERVER_CHECK_IDS
            )
            assert len(produced) == len(GIT_SERVER_CHECK_IDS)

    def test_never_raises_for_a_policy_violation(self) -> None:
        produced = validate_git_security((), True)
        assert all(isinstance(result, SecurityCheckResult) for result in produced)


class TestGuardsValidateSecurity:
    """The instance view reports what the installed guards can actually prove."""

    def test_installed_guards_report_the_same_check_ids(self, tmp_path: Path) -> None:
        guards = GitSecurityGuards(
            repo_state=MagicMock(spec=repository_state.RepositoryState),
            read_only=True,
        )
        guards._allowed_repo_paths = (str(tmp_path),)
        produced = guards.validate_security()
        assert [result.check_id for result in produced] == list(GIT_SERVER_CHECK_IDS)
        assert all(
            result.status is not SecurityCheckStatus.FAILED for result in produced
        )

    def test_missing_repository_state_fails_the_protected_branch_check(self) -> None:
        guards = GitSecurityGuards(
            repo_state=cast(repository_state.RepositoryState, None),
            read_only=True,
        )
        result = {check.check_id: check for check in guards.validate_security()}[
            "server.protected_branch_config"
        ]
        assert result.status is SecurityCheckStatus.FAILED
        assert result.reason_code == REASON_DEPENDENCY_UNREACHABLE

    def test_uninstalled_allowlist_is_fail_closed(self) -> None:
        guards = GitSecurityGuards(
            repo_state=MagicMock(spec=repository_state.RepositoryState),
            read_only=True,
        )
        result = {check.check_id: check for check in guards.validate_security()}[
            "server.repo_allowlist"
        ]
        assert result.status is SecurityCheckStatus.FAILED
        assert result.reason_code == REASON_ALLOWLIST_EMPTY
