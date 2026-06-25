"""
tests/test_github_mcp_service.py
Unit tests for GitHubService guard methods:
  - _assert_allowed_repo: fail_open / fail_closed modes
  - _assert_allowed_path: path_denylist glob matching
  - _assert_max_file_size: per-file size limit
  - _write_github_audit_log: audit record format and OSError suppression
"""

from __future__ import annotations

from contextlib import contextmanager
from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from mcp.github.models import (
    DeleteRepoFileRequest,
    GitHubAuditError,
    GitHubAuthorizationError,
    GitHubConfig,
    GitHubNotFoundError,
    GitHubValidationError,
    PushFile,
    PushFilesRequest,
)
from mcp.github.service import GitHubService

# ── Fixtures ──────────────────────────────────────────────────────────────────


def _make_service(cfg: dict | None = None) -> GitHubService:
    """Minimal GitHubService instance; GitHub API is never called in these tests."""
    raw = cfg or {"allowed_repos_mode": "fail_open"}
    return GitHubService(gh=MagicMock(), cfg=GitHubConfig.from_dict(raw))


@contextmanager
def _patch_cfg(cfg: dict):
    """Yield a GitHubService with the given config dict applied."""
    yield _make_service(cfg)


def _svc_with_cfg(cfg: dict) -> GitHubService:
    """Create a service with the given config dict."""
    return _make_service(cfg)


# ── _assert_allowed_repo ──────────────────────────────────────────────────────


class TestAssertAllowedRepo:
    def test_fail_open_empty_list_allows_all(self) -> None:
        svc = _make_service({"allowed_repos": [], "allowed_repos_mode": "fail_open"})
        svc._assert_allowed_repo("org", "repo")  # must not raise

    def test_fail_closed_is_default_when_mode_absent(self) -> None:
        # Default changed from fail_open to fail_closed; empty list now denies all.
        cfg: dict[str, Any] = {"allowed_repos": []}
        with _patch_cfg(cfg) as svc:
            with pytest.raises(GitHubAuthorizationError):
                svc._assert_allowed_repo("org", "repo")

    def test_fail_closed_empty_list_denies_all(self) -> None:
        svc = _make_service({"allowed_repos": [], "allowed_repos_mode": "fail_closed"})
        with pytest.raises(GitHubAuthorizationError):
            svc._assert_allowed_repo("org", "repo")

    def test_repo_in_allowlist_passes(self) -> None:
        svc = _make_service(
            {"allowed_repos": ["myorg/myrepo"], "allowed_repos_mode": "fail_open"}
        )
        svc._assert_allowed_repo("myorg", "myrepo")  # must not raise

    def test_repo_not_in_allowlist_denied(self) -> None:
        svc = _make_service(
            {"allowed_repos": ["myorg/myrepo"], "allowed_repos_mode": "fail_open"}
        )
        with pytest.raises(GitHubAuthorizationError):
            svc._assert_allowed_repo("myorg", "other")

    def test_fail_closed_nonempty_list_allows_listed_repo(self) -> None:
        svc = _make_service(
            {"allowed_repos": ["myorg/safe"], "allowed_repos_mode": "fail_closed"}
        )
        svc._assert_allowed_repo("myorg", "safe")  # must not raise

    def test_fail_closed_nonempty_list_denies_unlisted_repo(self) -> None:
        svc = _make_service(
            {"allowed_repos": ["myorg/safe"], "allowed_repos_mode": "fail_closed"}
        )
        with pytest.raises(GitHubAuthorizationError):
            svc._assert_allowed_repo("myorg", "other")

    def test_empty_owner_is_denied(self) -> None:
        svc = _make_service(
            {"allowed_repos": ["myorg/myrepo"], "allowed_repos_mode": "fail_open"}
        )
        with pytest.raises(GitHubAuthorizationError):
            svc._assert_allowed_repo("", "myrepo")

    def test_empty_repo_is_denied(self) -> None:
        svc = _make_service(
            {"allowed_repos": ["myorg/myrepo"], "allowed_repos_mode": "fail_open"}
        )
        with pytest.raises(GitHubAuthorizationError):
            svc._assert_allowed_repo("myorg", "")

    def test_slash_only_slug_is_denied(self) -> None:
        svc = _make_service(
            {"allowed_repos": ["myorg/myrepo"], "allowed_repos_mode": "fail_open"}
        )
        with pytest.raises(GitHubAuthorizationError):
            svc._assert_allowed_repo("", "")

    def test_owner_with_slash_multiple_parts_is_denied(self) -> None:
        svc = _make_service(
            {"allowed_repos": ["myorg/myrepo"], "allowed_repos_mode": "fail_open"}
        )
        with pytest.raises(GitHubAuthorizationError):
            svc._assert_allowed_repo("org/sub", "repo")


# ── _assert_allowed_path ──────────────────────────────────────────────────────


class TestAssertAllowedPath:
    def test_empty_denylist_allows_any_path(self) -> None:
        svc = _make_service({"path_denylist": []})
        svc._assert_allowed_path(".github/workflows/ci.yml")  # no raise

    def test_exact_match_denied(self) -> None:
        with _patch_cfg({"path_denylist": ["Dockerfile"]}) as svc:
            with pytest.raises(GitHubAuthorizationError):
                svc._assert_allowed_path("Dockerfile")

    def test_glob_pattern_denied(self) -> None:
        with _patch_cfg({"path_denylist": [".github/workflows/**"]}) as svc:
            with pytest.raises(GitHubAuthorizationError):
                svc._assert_allowed_path(".github/workflows/ci.yml")

    def test_wildcard_prefix_denied(self) -> None:
        with _patch_cfg({"path_denylist": ["Dockerfile*"]}) as svc:
            with pytest.raises(GitHubAuthorizationError):
                svc._assert_allowed_path("Dockerfile.prod")

    def test_non_matching_path_allowed(self) -> None:
        svc = _make_service({"path_denylist": ["Dockerfile*", ".github/**"]})
        svc._assert_allowed_path("src/main.py")  # no raise

    def test_missing_denylist_key_treated_as_empty(self) -> None:
        with _patch_cfg({}) as svc:
            svc._assert_allowed_path("any/path.txt")  # no raise


# ── _assert_max_file_size ─────────────────────────────────────────────────────


class TestAssertMaxFileSize:
    def test_zero_max_disables_check(self) -> None:
        svc = _make_service({"max_file_size_kb": 0})
        svc._assert_max_file_size("x" * 10_000_000, "big.bin")  # no raise

    def test_content_within_limit_passes(self) -> None:
        with _patch_cfg({"max_file_size_kb": 10}) as svc:
            # 5 KB of ASCII text is below 10 KB limit
            svc._assert_max_file_size("a" * 5120, "small.txt")  # no raise

    def test_content_at_limit_passes(self) -> None:
        with _patch_cfg({"max_file_size_kb": 1}) as svc:
            # Exactly 1024 bytes = 1 KB
            svc._assert_max_file_size("a" * 1024, "exact.txt")  # no raise

    def test_content_over_limit_raises(self) -> None:
        with _patch_cfg({"max_file_size_kb": 1}) as svc:
            with pytest.raises(GitHubValidationError):
                svc._assert_max_file_size("a" * 1025, "big.txt")

    def test_negative_max_disables_check(self) -> None:
        svc = _make_service({"max_file_size_kb": -1})
        svc._assert_max_file_size("x" * 10_000_000, "big.bin")  # no raise

    def test_missing_max_key_disables_check(self) -> None:
        with _patch_cfg({}) as svc:
            svc._assert_max_file_size("x" * 10_000_000, "big.bin")  # no raise


# ── _write_github_audit_log ───────────────────────────────────────────────────


class TestWriteGithubAuditLog:
    def test_empty_audit_path_skips_write(self) -> None:
        with _patch_cfg({"audit_log_path": ""}) as svc:
            # Must not raise even without a real file
            svc._write_github_audit_log("push_files", repo="a/b")

    def test_record_written_to_file(self, tmp_path: Path) -> None:
        log_file = tmp_path / "github_audit.log"
        svc = _make_service({"audit_log_path": str(log_file)})
        svc._write_github_audit_log(
            "push_files", repo="org/repo", branch="main", commit="abc12345"
        )
        content = log_file.read_text()
        assert "op=push_files" in content
        assert "repo='org/repo'" in content
        assert "branch='main'" in content
        assert "commit='abc12345'" in content

    def test_multiple_calls_append_to_file(self, tmp_path: Path) -> None:
        log_file = tmp_path / "audit.log"
        svc = _make_service({"audit_log_path": str(log_file)})
        svc._write_github_audit_log("create_branch", repo="a/b")
        svc._write_github_audit_log("merge_pull_request", repo="a/b")
        lines = log_file.read_text().strip().splitlines()
        assert len(lines) == 2
        assert "create_branch" in lines[0]
        assert "merge_pull_request" in lines[1]

    def test_oserror_raises_audit_error(self, tmp_path: Path) -> None:
        # Write to a non-existent directory; GitHubAuditError is raised (fail-fast)
        bad_path = str(tmp_path / "nonexistent" / "audit.log")
        with _patch_cfg({"audit_log_path": bad_path}) as svc:
            with pytest.raises(GitHubAuditError, match="Audit log write failed"):
                svc._write_github_audit_log("push_files", repo="x/y")

    def test_missing_audit_path_key_skips_write(self) -> None:
        with _patch_cfg({}) as svc:
            svc._write_github_audit_log("push_files", repo="a/b")  # no raise


# ── Pre-flight checks in async write methods (no GitHub API required) ─────────


@pytest.mark.asyncio
async def test_create_or_update_file_denies_path_in_denylist() -> None:
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
    with _patch_cfg(cfg) as svc:
        with pytest.raises(GitHubAuthorizationError):
            await svc.create_or_update_file(req)


@pytest.mark.asyncio
async def test_create_or_update_file_denies_oversized_content() -> None:
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
    with _patch_cfg(cfg) as svc:
        with pytest.raises(GitHubValidationError):
            await svc.create_or_update_file(req)


@pytest.mark.asyncio
async def test_push_files_denies_file_with_denied_path() -> None:
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
    with _patch_cfg(cfg) as svc:
        with pytest.raises(GitHubAuthorizationError):
            await svc.push_files(req)


@pytest.mark.asyncio
async def test_delete_repo_file_denies_protected_path() -> None:
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
    with _patch_cfg(cfg) as svc:
        with pytest.raises(GitHubAuthorizationError):
            await svc.delete_repo_file(req)


# ── _resolve_and_check_branch ─────────────────────────────────────────────────


class TestResolveAndCheckBranch:
    """Tests for _resolve_and_check_branch: branch="" bypass fix.

    branch="" は「ブランチ未指定 = デフォルトブランチを使う」を意味する。
    """

    @pytest.mark.asyncio
    async def test_empty_protected_branches_skips_check_with_explicit_branch(
        self,
    ) -> None:
        # protected_branches=[] → branch が何であれチェックをスキップ
        svc = _make_service()
        with patch.object(svc, "_run_github", new=AsyncMock()) as mock_api:
            await svc._resolve_and_check_branch("org", "repo", "main")
        mock_api.assert_not_called()

    @pytest.mark.asyncio
    async def test_empty_protected_branches_skips_check_with_empty_branch(self) -> None:
        # protected_branches=[] かつ branch="" → API 呼び出しなし
        svc = _make_service()
        with patch.object(svc, "_run_github", new=AsyncMock()) as mock_api:
            await svc._resolve_and_check_branch("org", "repo", "")
        mock_api.assert_not_called()

    @pytest.mark.asyncio
    async def test_explicit_branch_in_protected_raises(self) -> None:
        # branch="main" は protected_branches に含まれる
        svc = _make_service({"protected_branches": ["main"]})
        with patch.object(svc, "_run_github", new=AsyncMock()) as mock_api:
            with pytest.raises(GitHubAuthorizationError):
                await svc._resolve_and_check_branch("org", "repo", "main")

        mock_api.assert_not_called()

    @pytest.mark.asyncio
    async def test_explicit_branch_not_in_protected_passes(self) -> None:
        # branch="feature" は protected_branches に含まれない → 通過
        svc = _make_service()
        with patch.object(svc, "_run_github", new=AsyncMock()) as mock_api:
            await svc._resolve_and_check_branch("org", "repo", "feature")
        mock_api.assert_not_called()

    @pytest.mark.asyncio
    async def test_empty_branch_default_is_protected_raises(self) -> None:
        # branch="" → デフォルトブランチ "main" が protected_branches にある
        svc = _make_service({"protected_branches": ["main"]})
        with patch.object(svc, "_run_github", new=AsyncMock(return_value="main")):
            with pytest.raises(GitHubAuthorizationError):
                await svc._resolve_and_check_branch("org", "repo", "")

    @pytest.mark.asyncio
    async def test_empty_branch_default_not_protected_passes(self) -> None:
        # branch="" → デフォルトブランチ "develop" が protected_branches にない → 通過
        svc = _make_service()
        with patch.object(svc, "_run_github", new=AsyncMock(return_value="develop")):
            await svc._resolve_and_check_branch("org", "repo", "")


# ── Integration: create_or_update_file と delete_repo_file の branch=None 保護 ──


@pytest.mark.asyncio
async def test_create_or_update_file_empty_branch_protected_raises() -> None:
    """branch="" (省略) のとき default_branch が protected_branches にあれば 403 を返す。"""
    cfg = {
        "allowed_repos": [],
        "allowed_repos_mode": "fail_open",
        "protected_branches": ["main"],
        "path_denylist": [],
        "max_file_size_kb": 0,
    }
    from mcp.github.models import CreateOrUpdateFileRequest

    req = CreateOrUpdateFileRequest(
        owner="a",
        repo="b",
        path="README.md",
        content="hello",
        message="update",
        # branch を省略 → デフォルト ""
    )
    with _patch_cfg(cfg) as svc:
        with patch.object(svc, "_run_github", new=AsyncMock(return_value="main")):
            with pytest.raises(GitHubAuthorizationError):
                await svc.create_or_update_file(req)


@pytest.mark.asyncio
async def test_delete_repo_file_empty_branch_protected_raises() -> None:
    """branch="" (省略) のとき default_branch が protected_branches にあれば 403 を返す。"""
    cfg = {
        "allowed_repos": [],
        "allowed_repos_mode": "fail_open",
        "protected_branches": ["main"],
        "path_denylist": [],
        "max_file_size_kb": 0,
    }
    req = DeleteRepoFileRequest(
        owner="a",
        repo="b",
        path="old_file.txt",
        message="remove",
        sha="abc123",
        # branch を省略 → デフォルト ""
    )
    with _patch_cfg(cfg) as svc:
        with patch.object(svc, "_run_github", new=AsyncMock(return_value="main")):
            with pytest.raises(GitHubAuthorizationError):
                await svc.delete_repo_file(req)


@pytest.mark.asyncio
async def test_push_files_writes_audit_log_on_success(tmp_path: Path) -> None:
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
    with _patch_cfg(cfg) as svc:
        with patch.object(svc, "_run_github", new=AsyncMock(return_value=mock_result)):
            await svc.push_files(req)

    content = log_file.read_text()
    assert "op='push_files'" not in content or "push_files" in content
    assert "a/b" in content


# ── dry_run ───────────────────────────────────────────────────────────────────


class TestGitHubDryRun:
    @pytest.mark.asyncio
    async def test_create_branch_dry_run_returns_preview(self) -> None:
        import orjson

        svc = _make_service({"allowed_repos": [], "allowed_repos_mode": "fail_open"})
        result = await svc.fmt_create_branch(
            {
                "owner": "org",
                "repo": "repo",
                "branch_name": "feature/x",
                "dry_run": True,
            }
        )
        payload = orjson.loads(result)
        assert payload["dry_run"] is True
        assert "Would create branch" in payload["preview"]
        assert "feature/x" in payload["preview"]

    @pytest.mark.asyncio
    async def test_create_branch_dry_run_does_not_call_github_api(self) -> None:
        svc = _make_service({"allowed_repos": [], "allowed_repos_mode": "fail_open"})
        with patch.object(
            svc,
            "create_branch",
            new=AsyncMock(side_effect=RuntimeError("must not call")),
        ):
            # dry_run=True — API must not be called
            await svc.fmt_create_branch(
                {
                    "owner": "org",
                    "repo": "repo",
                    "branch_name": "feature/x",
                    "dry_run": True,
                }
            )

    @pytest.mark.asyncio
    async def test_create_branch_dry_run_shows_from_branch(self) -> None:
        import orjson

        svc = _make_service({"allowed_repos": [], "allowed_repos_mode": "fail_open"})
        result = await svc.fmt_create_branch(
            {
                "owner": "org",
                "repo": "repo",
                "branch_name": "hotfix/y",
                "from_branch": "main",
                "dry_run": True,
            }
        )
        payload = orjson.loads(result)
        assert "main" in payload["preview"]

    @pytest.mark.asyncio
    async def test_create_branch_dry_run_default_branch_label(self) -> None:
        import orjson

        svc = _make_service({"allowed_repos": [], "allowed_repos_mode": "fail_open"})
        result = await svc.fmt_create_branch(
            {
                "owner": "org",
                "repo": "repo",
                "branch_name": "hotfix/y",
                "dry_run": True,
            }
        )
        payload = orjson.loads(result)
        assert "(default branch)" in payload["preview"]

    @pytest.mark.asyncio
    async def test_fail_closed_empty_allowlist_denies_dry_run(self) -> None:
        svc = _make_service({"allowed_repos": [], "allowed_repos_mode": "fail_closed"})
        with pytest.raises(GitHubAuthorizationError):
            await svc.fmt_create_branch(
                {
                    "owner": "org",
                    "repo": "repo",
                    "branch_name": "feature/z",
                    "dry_run": True,
                }
            )

    @pytest.mark.asyncio
    async def test_create_branch_non_dry_run_calls_service(self) -> None:
        cfg = {"allowed_repos": [], "allowed_repos_mode": "fail_open"}
        mock_result = MagicMock()
        mock_result.branch_name = "feature/x"
        mock_result.sha = "abc1234567890"

        with _patch_cfg(cfg) as svc:
            with patch.object(
                svc, "create_branch", new=AsyncMock(return_value=mock_result)
            ):
                result = await svc.fmt_create_branch(
                    {"owner": "org", "repo": "repo", "branch_name": "feature/x"}
                )
        assert "feature/x" in result
        assert "abc12345" in result

    @pytest.mark.asyncio
    async def test_create_issue_non_dry_run_calls_service(self) -> None:
        cfg = {"allowed_repos": [], "allowed_repos_mode": "fail_open"}
        mock_issue = MagicMock()
        mock_issue.number = 42
        mock_issue.title = "Bug fix"
        mock_issue.url = "https://github.com/org/repo/issues/42"
        mock_result = MagicMock()
        mock_result.issue = mock_issue

        with _patch_cfg(cfg) as svc:
            with patch.object(
                svc, "create_issue", new=AsyncMock(return_value=mock_result)
            ):
                result = await svc.fmt_create_issue(
                    {"owner": "org", "repo": "repo", "title": "Bug fix"}
                )
        assert "42" in result or "Bug fix" in result

    @pytest.mark.asyncio
    async def test_create_pull_request_dry_run_all_fields(self) -> None:
        import orjson

        svc = _make_service({"allowed_repos": [], "allowed_repos_mode": "fail_open"})
        result = await svc.fmt_create_pull_request(
            {
                "owner": "org",
                "repo": "repo",
                "title": "My PR",
                "head": "feature/x",
                "base": "main",
                "dry_run": True,
            }
        )
        payload = orjson.loads(result)
        assert payload["dry_run"] is True
        assert "feature/x" in payload["preview"]
        assert "main" in payload["preview"]

    @pytest.mark.asyncio
    async def test_merge_pull_request_dry_run(self) -> None:
        import orjson

        svc = _make_service({"allowed_repos": [], "allowed_repos_mode": "fail_open"})
        result = await svc.fmt_merge_pull_request(
            {"owner": "org", "repo": "repo", "pr_number": 7, "dry_run": True}
        )
        payload = orjson.loads(result)
        assert payload["dry_run"] is True
        assert "7" in payload["preview"]

    @pytest.mark.asyncio
    async def test_create_or_update_file_dry_run_create_op(self) -> None:
        import orjson

        svc = _make_service({"allowed_repos": [], "allowed_repos_mode": "fail_open"})
        result = await svc.fmt_create_or_update_file(
            {
                "owner": "org",
                "repo": "repo",
                "path": "src/file.py",
                "content": "code",
                "message": "add file",
                "dry_run": True,
            }
        )
        payload = orjson.loads(result)
        assert payload["dry_run"] is True
        assert "create" in payload["preview"] or "Would" in payload["preview"]

    @pytest.mark.asyncio
    async def test_create_or_update_file_dry_run_update_op(self) -> None:
        import orjson

        svc = _make_service({"allowed_repos": [], "allowed_repos_mode": "fail_open"})
        result = await svc.fmt_create_or_update_file(
            {
                "owner": "org",
                "repo": "repo",
                "path": "src/file.py",
                "content": "code",
                "message": "update file",
                "sha": "abc123",
                "dry_run": True,
            }
        )
        payload = orjson.loads(result)
        assert "update" in payload["preview"]

    @pytest.mark.asyncio
    async def test_push_files_dry_run(self) -> None:
        import orjson

        svc = _make_service({"allowed_repos": [], "allowed_repos_mode": "fail_open"})
        result = await svc.fmt_push_files(
            {
                "owner": "org",
                "repo": "repo",
                "branch": "main",
                "files": [{"path": "a.py", "content": "x"}],
                "message": "push",
                "dry_run": True,
            }
        )
        payload = orjson.loads(result)
        assert payload["dry_run"] is True
        assert "a.py" in payload["preview"]

    @pytest.mark.asyncio
    async def test_delete_file_dry_run(self) -> None:
        import orjson

        svc = _make_service({"allowed_repos": [], "allowed_repos_mode": "fail_open"})
        result = await svc.fmt_delete_file(
            {
                "owner": "org",
                "repo": "repo",
                "path": "old.py",
                "sha": "abc",
                "message": "delete",
                "dry_run": True,
            }
        )
        payload = orjson.loads(result)
        assert payload["dry_run"] is True
        assert "old.py" in payload["preview"]

    @pytest.mark.asyncio
    async def test_add_issue_comment_dry_run(self) -> None:
        import orjson

        svc = _make_service({"allowed_repos": [], "allowed_repos_mode": "fail_open"})
        result = await svc.fmt_add_issue_comment(
            {
                "owner": "org",
                "repo": "repo",
                "issue_number": 3,
                "body": "comment text",
                "dry_run": True,
            }
        )
        payload = orjson.loads(result)
        assert payload["dry_run"] is True
        assert "3" in payload["preview"]

    @pytest.mark.asyncio
    async def test_update_pull_request_dry_run(self) -> None:
        import orjson

        svc = _make_service({"allowed_repos": [], "allowed_repos_mode": "fail_open"})
        result = await svc.fmt_update_pull_request(
            {
                "owner": "org",
                "repo": "repo",
                "pr_number": 5,
                "title": "New title",
                "dry_run": True,
            }
        )
        payload = orjson.loads(result)
        assert payload["dry_run"] is True
        assert "5" in payload["preview"]
        assert "New title" in payload["preview"]

    @pytest.mark.asyncio
    async def test_create_issue_dry_run_with_labels(self) -> None:
        import orjson

        svc = _make_service({"allowed_repos": [], "allowed_repos_mode": "fail_open"})
        result = await svc.fmt_create_issue(
            {
                "owner": "org",
                "repo": "repo",
                "title": "Bug",
                "labels": ["bug", "p1"],
                "dry_run": True,
            }
        )
        payload = orjson.loads(result)
        assert payload["dry_run"] is True
        assert "bug" in payload["preview"] or "Bug" in payload["preview"]

    @pytest.mark.asyncio
    async def test_add_issue_comment_non_dry_run_calls_service(self) -> None:
        cfg = {"allowed_repos": [], "allowed_repos_mode": "fail_open"}
        mock_result = MagicMock()
        mock_result.issue_number = 3
        mock_result.comment_url = "https://github.com/org/repo/issues/3#comment-1"
        with _patch_cfg(cfg) as svc:
            with patch.object(
                svc, "add_issue_comment", new=AsyncMock(return_value=mock_result)
            ):
                result = await svc.fmt_add_issue_comment(
                    {"owner": "org", "repo": "repo", "issue_number": 3, "body": "hi"}
                )
        assert "Comment posted" in result
        assert "3" in result

    @pytest.mark.asyncio
    async def test_create_pull_request_non_dry_run_calls_service(self) -> None:
        cfg = {"allowed_repos": [], "allowed_repos_mode": "fail_open"}
        mock_pr = MagicMock()
        mock_pr.number = 10
        mock_pr.title = "My PR"
        mock_pr.head_ref = "feature/x"
        mock_pr.base_ref = "main"
        mock_pr.url = "https://github.com/org/repo/pull/10"
        mock_result = MagicMock()
        mock_result.pull_request = mock_pr
        with _patch_cfg(cfg) as svc:
            with patch.object(
                svc, "create_pull_request", new=AsyncMock(return_value=mock_result)
            ):
                result = await svc.fmt_create_pull_request(
                    {
                        "owner": "org",
                        "repo": "repo",
                        "title": "My PR",
                        "head": "feature/x",
                        "base": "main",
                    }
                )
        assert "Created" in result
        assert "10" in result

    @pytest.mark.asyncio
    async def test_update_pull_request_non_dry_run_calls_service(self) -> None:
        cfg = {"allowed_repos": [], "allowed_repos_mode": "fail_open"}
        mock_pr = MagicMock()
        mock_pr.number = 5
        mock_pr.state = "open"
        mock_pr.title = "Updated title"
        mock_pr.url = "https://github.com/org/repo/pull/5"
        mock_result = MagicMock()
        mock_result.pull_request = mock_pr
        with _patch_cfg(cfg) as svc:
            with patch.object(
                svc, "update_pull_request", new=AsyncMock(return_value=mock_result)
            ):
                result = await svc.fmt_update_pull_request(
                    {
                        "owner": "org",
                        "repo": "repo",
                        "pr_number": 5,
                        "title": "Updated title",
                    }
                )
        assert "Updated" in result
        assert "5" in result

    @pytest.mark.asyncio
    async def test_merge_pull_request_non_dry_run_calls_service(self) -> None:
        cfg = {"allowed_repos": [], "allowed_repos_mode": "fail_open"}
        mock_result = MagicMock()
        mock_result.pr_number = 7
        mock_result.merged = True
        mock_result.sha = "abc1234567890"
        mock_result.message = "Merged successfully"
        with _patch_cfg(cfg) as svc:
            with patch.object(
                svc, "merge_pull_request", new=AsyncMock(return_value=mock_result)
            ):
                result = await svc.fmt_merge_pull_request(
                    {"owner": "org", "repo": "repo", "pr_number": 7}
                )
        assert "Merged" in result
        assert "7" in result


# ── Fail-fast domain exception tests (added in Step 6) ───────────────────────


class TestGitHubDomainExceptions:
    """Tests for domain exception mapping (fail-fast refactor)."""

    def test_github_api_404_raises_not_found_error(self) -> None:
        from github import GithubException

        exc = GithubException(404, {"message": "Not Found"}, {})
        with pytest.raises(GitHubNotFoundError, match="Resource not found"):
            GitHubService._handle_github_error(exc)

    def test_github_api_403_raises_authorization_error(self) -> None:
        from github import GithubException

        exc = GithubException(403, {"message": "Forbidden"}, {})
        with pytest.raises(GitHubAuthorizationError, match="rate limit"):
            GitHubService._handle_github_error(exc)

    def test_github_api_409_raises_conflict_error(self) -> None:
        from github import GithubException
        from mcp.github.models import GitHubConflictError

        exc = GithubException(409, {"message": "Conflict"}, {})
        with pytest.raises(GitHubConflictError):
            GitHubService._handle_github_error(exc)

    def test_github_api_500_raises_upstream_error(self) -> None:
        from github import GithubException
        from mcp.github.models import GitHubUpstreamError

        exc = GithubException(500, {"message": "Server Error"}, {})
        with pytest.raises(GitHubUpstreamError, match="status=500"):
            GitHubService._handle_github_error(exc)

    def test_audit_failure_raises_audit_error(self, tmp_path) -> None:
        bad_path = str(tmp_path / "nonexistent" / "audit.log")
        svc = _make_service({"audit_log_path": bad_path})
        with pytest.raises(GitHubAuditError, match="Audit log write failed"):
            svc._write_github_audit_log("test_op", key="value")

    def test_github_config_from_dict(self) -> None:
        from mcp.github.models import GitHubConfig

        cfg = GitHubConfig.from_dict(
            {
                "allowed_repos": ["org/repo"],
                "allowed_repos_mode": "fail_open",
                "max_per_page": 50,
            }
        )
        assert cfg.allowed_repos == ["org/repo"]
        assert cfg.allowed_repos_mode == "fail_open"
        assert cfg.max_per_page == 50
        assert cfg.protected_branches == []

    def test_github_config_defaults(self) -> None:
        from mcp.github.models import GitHubConfig

        cfg = GitHubConfig.from_dict({})
        assert cfg.allowed_repos_mode == "fail_closed"
        assert cfg.max_per_page == 100
        assert cfg.audit_log_path == ""
