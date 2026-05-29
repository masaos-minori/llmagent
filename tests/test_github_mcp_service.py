"""
tests/test_github_mcp_service.py
Unit tests for GitHubService guard methods:
  - _assert_allowed_repo: fail_open / fail_closed modes
  - _assert_allowed_path: path_denylist glob matching
  - _assert_max_file_size: per-file size limit
  - _write_github_audit_log: audit record format and OSError suppression
"""

from __future__ import annotations

from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException
from mcp.github.models import DeleteRepoFileRequest, PushFile, PushFilesRequest
from mcp.github.service import GitHubService

# ── Fixtures ──────────────────────────────────────────────────────────────────


def _make_service() -> GitHubService:
    """Minimal GitHubService instance; GitHub API is never called in these tests."""
    return GitHubService(gh=MagicMock(), default_per_page=10, max_per_page=100)


def _patch_cfg(cfg: dict) -> Any:
    """Context manager that patches _get_cfg in github_mcp_service."""
    return patch("mcp.github.service._get_cfg", return_value=cfg)


# ── _assert_allowed_repo ──────────────────────────────────────────────────────


class TestAssertAllowedRepo:
    def test_fail_open_empty_list_allows_all(self) -> None:
        svc = _make_service()
        cfg = {"allowed_repos": [], "allowed_repos_mode": "fail_open"}
        with _patch_cfg(cfg):
            svc._assert_allowed_repo("org", "repo")  # must not raise

    def test_fail_open_is_default_when_mode_absent(self) -> None:
        svc = _make_service()
        cfg: dict[str, Any] = {"allowed_repos": []}
        with _patch_cfg(cfg):
            svc._assert_allowed_repo("org", "repo")  # must not raise

    def test_fail_closed_empty_list_denies_all(self) -> None:
        svc = _make_service()
        cfg = {"allowed_repos": [], "allowed_repos_mode": "fail_closed"}
        with _patch_cfg(cfg):
            with pytest.raises(HTTPException) as exc_info:
                svc._assert_allowed_repo("org", "repo")
            assert exc_info.value.status_code == 403
            assert "fail_closed" in exc_info.value.detail

    def test_repo_in_allowlist_passes(self) -> None:
        svc = _make_service()
        cfg = {"allowed_repos": ["myorg/myrepo"], "allowed_repos_mode": "fail_open"}
        with _patch_cfg(cfg):
            svc._assert_allowed_repo("myorg", "myrepo")  # must not raise

    def test_repo_not_in_allowlist_denied(self) -> None:
        svc = _make_service()
        cfg = {"allowed_repos": ["myorg/myrepo"], "allowed_repos_mode": "fail_open"}
        with _patch_cfg(cfg):
            with pytest.raises(HTTPException) as exc_info:
                svc._assert_allowed_repo("myorg", "other")
            assert exc_info.value.status_code == 403
            assert "myorg/other" in exc_info.value.detail

    def test_fail_closed_nonempty_list_allows_listed_repo(self) -> None:
        svc = _make_service()
        cfg = {"allowed_repos": ["myorg/safe"], "allowed_repos_mode": "fail_closed"}
        with _patch_cfg(cfg):
            svc._assert_allowed_repo("myorg", "safe")  # must not raise

    def test_fail_closed_nonempty_list_denies_unlisted_repo(self) -> None:
        svc = _make_service()
        cfg = {"allowed_repos": ["myorg/safe"], "allowed_repos_mode": "fail_closed"}
        with _patch_cfg(cfg):
            with pytest.raises(HTTPException) as exc_info:
                svc._assert_allowed_repo("myorg", "other")
            assert exc_info.value.status_code == 403


# ── _assert_allowed_path ──────────────────────────────────────────────────────


class TestAssertAllowedPath:
    def test_empty_denylist_allows_any_path(self) -> None:
        with _patch_cfg({"path_denylist": []}):
            GitHubService._assert_allowed_path(".github/workflows/ci.yml")  # no raise

    def test_exact_match_denied(self) -> None:
        with _patch_cfg({"path_denylist": ["Dockerfile"]}):
            with pytest.raises(HTTPException) as exc_info:
                GitHubService._assert_allowed_path("Dockerfile")
            assert exc_info.value.status_code == 403
            assert "Dockerfile" in exc_info.value.detail

    def test_glob_pattern_denied(self) -> None:
        with _patch_cfg({"path_denylist": [".github/workflows/**"]}):
            with pytest.raises(HTTPException) as exc_info:
                GitHubService._assert_allowed_path(".github/workflows/ci.yml")
            assert exc_info.value.status_code == 403

    def test_wildcard_prefix_denied(self) -> None:
        with _patch_cfg({"path_denylist": ["Dockerfile*"]}):
            with pytest.raises(HTTPException):
                GitHubService._assert_allowed_path("Dockerfile.prod")

    def test_non_matching_path_allowed(self) -> None:
        with _patch_cfg({"path_denylist": ["Dockerfile*", ".github/**"]}):
            GitHubService._assert_allowed_path("src/main.py")  # no raise

    def test_missing_denylist_key_treated_as_empty(self) -> None:
        with _patch_cfg({}):
            GitHubService._assert_allowed_path("any/path.txt")  # no raise


# ── _assert_max_file_size ─────────────────────────────────────────────────────


class TestAssertMaxFileSize:
    def test_zero_max_disables_check(self) -> None:
        with _patch_cfg({"max_file_size_kb": 0}):
            GitHubService._assert_max_file_size("x" * 10_000_000, "big.bin")  # no raise

    def test_content_within_limit_passes(self) -> None:
        with _patch_cfg({"max_file_size_kb": 10}):
            # 5 KB of ASCII text is below 10 KB limit
            GitHubService._assert_max_file_size("a" * 5120, "small.txt")  # no raise

    def test_content_at_limit_passes(self) -> None:
        with _patch_cfg({"max_file_size_kb": 1}):
            # Exactly 1024 bytes = 1 KB
            GitHubService._assert_max_file_size("a" * 1024, "exact.txt")  # no raise

    def test_content_over_limit_raises(self) -> None:
        with _patch_cfg({"max_file_size_kb": 1}):
            with pytest.raises(HTTPException) as exc_info:
                GitHubService._assert_max_file_size("a" * 1025, "big.txt")
            assert exc_info.value.status_code == 400
            assert "big.txt" in exc_info.value.detail
            assert "max_file_size_kb" in exc_info.value.detail

    def test_negative_max_disables_check(self) -> None:
        with _patch_cfg({"max_file_size_kb": -1}):
            GitHubService._assert_max_file_size("x" * 10_000_000, "big.bin")  # no raise

    def test_missing_max_key_disables_check(self) -> None:
        with _patch_cfg({}):
            GitHubService._assert_max_file_size("x" * 10_000_000, "big.bin")  # no raise


# ── _write_github_audit_log ───────────────────────────────────────────────────


class TestWriteGithubAuditLog:
    def test_empty_audit_path_skips_write(self) -> None:
        with _patch_cfg({"audit_log_path": ""}):
            # Must not raise even without a real file
            GitHubService._write_github_audit_log("push_files", repo="a/b")

    def test_record_written_to_file(self, tmp_path: Path) -> None:
        log_file = tmp_path / "github_audit.log"
        with _patch_cfg({"audit_log_path": str(log_file)}):
            GitHubService._write_github_audit_log(
                "push_files", repo="org/repo", branch="main", commit="abc12345"
            )
        content = log_file.read_text()
        assert "op=push_files" in content
        assert "repo='org/repo'" in content
        assert "branch='main'" in content
        assert "commit='abc12345'" in content

    def test_multiple_calls_append_to_file(self, tmp_path: Path) -> None:
        log_file = tmp_path / "audit.log"
        with _patch_cfg({"audit_log_path": str(log_file)}):
            GitHubService._write_github_audit_log("create_branch", repo="a/b")
            GitHubService._write_github_audit_log("merge_pull_request", repo="a/b")
        lines = log_file.read_text().strip().splitlines()
        assert len(lines) == 2
        assert "create_branch" in lines[0]
        assert "merge_pull_request" in lines[1]

    def test_oserror_is_suppressed(self, tmp_path: Path) -> None:
        # Write to a non-existent directory; OSError must be caught, not raised
        bad_path = str(tmp_path / "nonexistent" / "audit.log")
        with _patch_cfg({"audit_log_path": bad_path}):
            # Should not raise
            GitHubService._write_github_audit_log("push_files", repo="x/y")

    def test_missing_audit_path_key_skips_write(self) -> None:
        with _patch_cfg({}):
            GitHubService._write_github_audit_log("push_files", repo="a/b")  # no raise


# ── Pre-flight checks in async write methods (no GitHub API required) ─────────


@pytest.mark.asyncio
async def test_create_or_update_file_denies_path_in_denylist() -> None:
    svc = _make_service()
    cfg = {
        "allowed_repos": [],
        "allowed_repos_mode": "fail_open",
        "protected_branches": [],
        "path_denylist": [".github/**"],
        "max_file_size_kb": 0,
    }
    from mcp.github.models import CreateOrUpdateFileRequest

    req = CreateOrUpdateFileRequest(
        owner="a",
        repo="b",
        path=".github/workflows/ci.yml",
        content="x",
        message="m",
    )
    with _patch_cfg(cfg):
        with pytest.raises(HTTPException) as exc_info:
            await svc.create_or_update_file(req)
    assert exc_info.value.status_code == 403


@pytest.mark.asyncio
async def test_create_or_update_file_denies_oversized_content() -> None:
    svc = _make_service()
    cfg = {
        "allowed_repos": [],
        "allowed_repos_mode": "fail_open",
        "protected_branches": [],
        "path_denylist": [],
        "max_file_size_kb": 1,
    }
    from mcp.github.models import CreateOrUpdateFileRequest

    req = CreateOrUpdateFileRequest(
        owner="a",
        repo="b",
        path="large.txt",
        content="x" * 1025,
        message="m",  # > 1 KB
    )
    with _patch_cfg(cfg):
        with pytest.raises(HTTPException) as exc_info:
            await svc.create_or_update_file(req)
    assert exc_info.value.status_code == 400


@pytest.mark.asyncio
async def test_push_files_denies_file_with_denied_path() -> None:
    svc = _make_service()
    cfg = {
        "allowed_repos": [],
        "allowed_repos_mode": "fail_open",
        "protected_branches": [],
        "path_denylist": ["Dockerfile*"],
        "max_file_size_kb": 0,
    }
    req = PushFilesRequest(
        owner="a",
        repo="b",
        branch="feature",
        files=[PushFile(path="Dockerfile", content="FROM scratch")],
        message="add Dockerfile",
    )
    with _patch_cfg(cfg):
        with pytest.raises(HTTPException) as exc_info:
            await svc.push_files(req)
    assert exc_info.value.status_code == 403


@pytest.mark.asyncio
async def test_delete_repo_file_denies_protected_path() -> None:
    svc = _make_service()
    cfg = {
        "allowed_repos": [],
        "allowed_repos_mode": "fail_open",
        "protected_branches": [],
        "path_denylist": [".github/**"],
        "max_file_size_kb": 0,
    }
    req = DeleteRepoFileRequest(
        owner="a",
        repo="b",
        path=".github/workflows/ci.yml",
        message="remove ci",
        sha="abc123",
    )
    with _patch_cfg(cfg):
        with pytest.raises(HTTPException) as exc_info:
            await svc.delete_repo_file(req)
    assert exc_info.value.status_code == 403


@pytest.mark.asyncio
async def test_push_files_writes_audit_log_on_success(tmp_path: Path) -> None:
    svc = _make_service()
    log_file = tmp_path / "audit.log"
    cfg = {
        "allowed_repos": [],
        "allowed_repos_mode": "fail_open",
        "protected_branches": [],
        "path_denylist": [],
        "max_file_size_kb": 0,
        "audit_log_path": str(log_file),
    }
    mock_result = MagicMock()
    mock_result.branch = "main"
    mock_result.commit_sha = "abc1234567890"
    mock_result.files_pushed = 1

    req = PushFilesRequest(
        owner="a",
        repo="b",
        branch="main",
        files=[PushFile(path="file.py", content="x")],
        message="test",
    )
    with _patch_cfg(cfg):
        with patch.object(svc, "_run_github", new=AsyncMock(return_value=mock_result)):
            await svc.push_files(req)

    content = log_file.read_text()
    assert "op='push_files'" not in content or "push_files" in content
    assert "a/b" in content
