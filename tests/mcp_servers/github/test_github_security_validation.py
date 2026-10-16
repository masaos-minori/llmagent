"""tests/mcp_servers/github/test_github_security_validation.py

Tests for scripts/mcp_servers/github/github_service_security.py: validate_github_security()
reports GitHub's own policy as posture checks before HTTP bind, keeps warning-only settings
non-fatal, and never names a repository identifier or a denylist pattern.
"""

from __future__ import annotations

from pathlib import Path

from mcp_servers.github.github_models_config import GitHubConfig
from mcp_servers.github.github_service_security import validate_github_security
from shared.security.posture_contract import COMMON_CHECK_IDS, REQUIRED_CHECK_IDS
from shared.security.result_dto import (
    REASON_ALLOWLIST_EMPTY,
    REASON_CONFIG_INVALID,
    REASON_DEPENDENCY_UNREACHABLE,
    REASON_DESTRUCTIVE_GUARD_MISSING,
    REASON_FORCE_PUSH_ENABLED,
    REASON_NOT_APPLICABLE,
    REASON_OK,
    SecurityCheckResult,
    SecurityCheckStatus,
)

GITHUB_SERVER_CHECK_IDS = (
    "server.repo_allowlist",
    "server.force_push_policy",
    "server.pr_review_required",
    "server.protected_branches",
    "server.path_denylist",
    "server.max_file_size",
    "server.audit_log_writable",
    "server.per_page_bounds",
)
_REPO = "octocat/hello-world"
_DENY_PATTERN = ".github/workflows/*"


def _results(cfg: GitHubConfig) -> dict[str, SecurityCheckResult]:
    """GitHub's check results keyed by check id."""
    return {result.check_id: result for result in validate_github_security(cfg)}


def _safe_cfg(**overrides: object) -> GitHubConfig:
    """A config whose every check passes, with the named settings changed."""
    cfg = GitHubConfig(
        allowed_repos=[_REPO],
        path_denylist=[_DENY_PATTERN],
        protected_branches=["main"],
        max_file_size_kb=512,
        default_per_page=10,
        max_per_page=100,
    )
    for name, value in overrides.items():
        setattr(cfg, name, value)
    return cfg


class TestRepoAllowlist:
    """An empty allowed_repos denies every repository: a startup failure (REQ-007)."""

    def test_empty_allowlist_fails(self) -> None:
        result = _results(_safe_cfg(allowed_repos=[]))["server.repo_allowlist"]
        assert result.status is SecurityCheckStatus.FAILED
        assert result.reason_code == REASON_ALLOWLIST_EMPTY

    def test_non_empty_allowlist_is_ok(self) -> None:
        result = _results(_safe_cfg())["server.repo_allowlist"]
        assert result.status is SecurityCheckStatus.OK
        assert result.reason_code == REASON_OK


class TestWarningPolicySettings:
    """Warning-only settings stay startable, exactly as the removed audit left them."""

    def test_force_push_enabled_is_warning(self) -> None:
        result = _results(_safe_cfg(allow_force_push=True))["server.force_push_policy"]
        assert result.status is SecurityCheckStatus.WARNING
        assert result.reason_code == REASON_FORCE_PUSH_ENABLED

    def test_missing_pr_review_guard_is_warning(self) -> None:
        result = _results(_safe_cfg(require_pr_review=False))[
            "server.pr_review_required"
        ]
        assert result.status is SecurityCheckStatus.WARNING
        assert result.reason_code == REASON_DESTRUCTIVE_GUARD_MISSING

    def test_warnings_alone_leave_no_failed_check(self) -> None:
        cfg = _safe_cfg(
            allow_force_push=True, require_pr_review=False, audit_log_path=""
        )
        produced = validate_github_security(cfg)
        assert all(
            result.status is not SecurityCheckStatus.FAILED for result in produced
        )
        assert any(result.status is SecurityCheckStatus.WARNING for result in produced)


class TestInapplicableChecks:
    """A rule that is switched off is reported not_applicable instead of omitted."""

    def test_empty_protected_branches(self) -> None:
        result = _results(_safe_cfg(protected_branches=[]))["server.protected_branches"]
        assert result.status is SecurityCheckStatus.NOT_APPLICABLE
        assert result.reason_code == REASON_NOT_APPLICABLE

    def test_empty_path_denylist(self) -> None:
        result = _results(_safe_cfg(path_denylist=[]))["server.path_denylist"]
        assert result.status is SecurityCheckStatus.NOT_APPLICABLE
        assert result.reason_code == REASON_NOT_APPLICABLE

    def test_zero_max_file_size(self) -> None:
        result = _results(_safe_cfg(max_file_size_kb=0))["server.max_file_size"]
        assert result.status is SecurityCheckStatus.NOT_APPLICABLE
        assert result.reason_code == REASON_NOT_APPLICABLE

    def test_empty_audit_log_path(self) -> None:
        result = _results(_safe_cfg(audit_log_path=""))["server.audit_log_writable"]
        assert result.status is SecurityCheckStatus.NOT_APPLICABLE
        assert result.reason_code == REASON_NOT_APPLICABLE

    def test_configured_rules_are_ok(self) -> None:
        results = _results(_safe_cfg())
        for check_id in (
            "server.protected_branches",
            "server.path_denylist",
            "server.max_file_size",
        ):
            assert results[check_id].status is SecurityCheckStatus.OK


class TestAuditLogWritable:
    """A configured audit path that cannot be written fails before the first guarded call."""

    def test_writable_path_is_ok(self, tmp_path: Path) -> None:
        cfg = _safe_cfg(audit_log_path=str(tmp_path / "audit.log"))
        result = _results(cfg)["server.audit_log_writable"]
        assert result.status is SecurityCheckStatus.OK
        assert result.reason_code == REASON_OK

    def test_missing_parent_directory_fails(self, tmp_path: Path) -> None:
        cfg = _safe_cfg(audit_log_path=str(tmp_path / "absent" / "audit.log"))
        result = _results(cfg)["server.audit_log_writable"]
        assert result.status is SecurityCheckStatus.FAILED
        assert result.reason_code == REASON_DEPENDENCY_UNREACHABLE

    def test_parent_that_is_a_file_fails(self, tmp_path: Path) -> None:
        blocker = tmp_path / "not-a-directory"
        blocker.write_text("blocker", encoding="utf-8")
        cfg = _safe_cfg(audit_log_path=str(blocker / "audit.log"))
        result = _results(cfg)["server.audit_log_writable"]
        assert result.status is SecurityCheckStatus.FAILED
        assert result.reason_code == REASON_DEPENDENCY_UNREACHABLE

    def test_audit_path_that_is_a_directory_fails(self, tmp_path: Path) -> None:
        cfg = _safe_cfg(audit_log_path=str(tmp_path))
        result = _results(cfg)["server.audit_log_writable"]
        assert result.status is SecurityCheckStatus.FAILED
        assert result.reason_code == REASON_DEPENDENCY_UNREACHABLE

    def test_failure_message_does_not_name_the_path(self, tmp_path: Path) -> None:
        cfg = _safe_cfg(audit_log_path=str(tmp_path / "absent" / "audit.log"))
        result = _results(cfg)["server.audit_log_writable"]
        assert str(tmp_path) not in result.message


class TestPerPageBounds:
    """A reversed bound is invisible today because _clamp_per_page() hides it."""

    def test_non_positive_max_fails(self) -> None:
        result = _results(_safe_cfg(max_per_page=0))["server.per_page_bounds"]
        assert result.status is SecurityCheckStatus.FAILED
        assert result.reason_code == REASON_CONFIG_INVALID

    def test_reversed_bounds_fail(self) -> None:
        result = _results(_safe_cfg(default_per_page=50, max_per_page=10))[
            "server.per_page_bounds"
        ]
        assert result.status is SecurityCheckStatus.FAILED
        assert result.reason_code == REASON_CONFIG_INVALID

    def test_valid_bounds_are_ok(self) -> None:
        result = _results(_safe_cfg())["server.per_page_bounds"]
        assert result.status is SecurityCheckStatus.OK
        assert result.reason_code == REASON_OK


class TestCheckSet:
    """The check set is identical for every configuration so row 05 can compare it."""

    def test_ids_match_the_frozen_contract(self) -> None:
        expected = tuple(
            check_id
            for check_id in REQUIRED_CHECK_IDS["github"]
            if check_id not in COMMON_CHECK_IDS
        )
        assert expected == GITHUB_SERVER_CHECK_IDS

    def test_order_is_fixed(self) -> None:
        produced = validate_github_security(GitHubConfig())
        assert [result.check_id for result in produced] == list(GITHUB_SERVER_CHECK_IDS)

    def test_check_set_is_identical_across_configurations(self, tmp_path: Path) -> None:
        configurations = (
            GitHubConfig(),
            _safe_cfg(),
            _safe_cfg(allow_force_push=True, require_pr_review=False),
            _safe_cfg(
                audit_log_path=str(tmp_path / "absent" / "audit.log"), max_per_page=0
            ),
        )
        for cfg in configurations:
            produced = validate_github_security(cfg)
            assert [result.check_id for result in produced] == list(
                GITHUB_SERVER_CHECK_IDS
            )
            assert len(produced) == len(GITHUB_SERVER_CHECK_IDS)

    def test_never_raises_for_a_policy_violation(self) -> None:
        produced = validate_github_security(GitHubConfig())
        assert all(isinstance(result, SecurityCheckResult) for result in produced)


class TestMessages:
    """Repository identifiers and denylist patterns are raw allowlist values (REQ-002)."""

    def test_no_message_names_a_repository_or_a_denylist_pattern(self) -> None:
        cfg = _safe_cfg(allowed_repos=[_REPO], path_denylist=[_DENY_PATTERN])
        for result in validate_github_security(cfg):
            assert _REPO not in result.message
            assert _DENY_PATTERN not in result.message
