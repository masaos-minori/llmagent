"""tests/mcp_servers/github/test_service_security.py

Characterization tests closing coverage gaps in
`mcp_servers/github/service_security.py` (GitHubSecurityGuards) found before a
refactor pass. These lock existing behavior only — no source logic is asserted
to be "correct", only that it behaves the way it currently does.

Gaps covered here (see coverage report: lines 43-44, 132, 146, 182, 194-197
of service_security.py were previously unexercised by the existing suite):

  - _clamp_per_page: both directions (below max passthrough, above max clamp)
  - _get_repo: direct delegation to the PyGithub client
  - _resolve_and_check_branch: explicit branch supplied, protected_branches
    non-empty, branch does NOT match any pattern -> silent pass (the "allow"
    direction of that branch, previously untested; only the "deny" direction
    was covered)
  - _handle_github_error: HTTP 400 / 422 -> GitHubValidationError (only
    404/403/409/500 were covered previously)
  - _run_github: success path and GithubException-to-domain-exception
    conversion path, exercised directly (previously only exercised through
    higher-level methods with `_run_github` itself mocked out)
"""

from __future__ import annotations

from http import HTTPStatus
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from github import GithubException
from mcp_servers.github.github_models import (
    CreateOrUpdateFileRequest,
    GitHubAuthorizationError,
    GitHubConfig,
    GitHubValidationError,
)
from mcp_servers.github.github_service_dispatch import GitHubService


def _make_service(cfg: dict | None = None) -> GitHubService:
    """Minimal GitHubService instance; GitHub API is never called in these tests."""
    raw = cfg or {"allowed_repos": ["org/repo"]}
    return GitHubService(gh=MagicMock(), cfg=GitHubConfig.from_dict(raw))


# ── _clamp_per_page ────────────────────────────────────────────────────────────


class TestClampPerPage:
    def test_value_below_max_passes_through_unchanged(self) -> None:
        svc = _make_service({"allowed_repos": ["org/repo"], "max_per_page": 100})
        assert svc._clamp_per_page(10) == 10

    def test_value_equal_to_max_passes_through_unchanged(self) -> None:
        svc = _make_service({"allowed_repos": ["org/repo"], "max_per_page": 50})
        assert svc._clamp_per_page(50) == 50

    def test_value_above_max_is_clamped_down(self) -> None:
        svc = _make_service({"allowed_repos": ["org/repo"], "max_per_page": 50})
        assert svc._clamp_per_page(999) == 50


# ── _get_repo ──────────────────────────────────────────────────────────────────


class TestGetRepo:
    def test_delegates_to_pygithub_client_with_owner_slash_repo(self) -> None:
        gh = MagicMock()
        svc = GitHubService(
            gh=gh, cfg=GitHubConfig.from_dict({"allowed_repos": ["org/repo"]})
        )
        sentinel = object()
        gh.get_repo.return_value = sentinel

        result = svc._get_repo("org", "repo")

        gh.get_repo.assert_called_once_with("org/repo")
        assert result is sentinel


# ── _resolve_and_check_branch: previously-uncovered "allow" direction ────────


class TestResolveAndCheckBranchExplicitBranchAllowed:
    @pytest.mark.asyncio
    async def test_explicit_branch_not_matching_protected_pattern_passes_silently(
        self,
    ) -> None:
        # protected_branches is non-empty and the supplied branch
        # does not match any pattern -> must return without raising and
        # without calling the GitHub API (no default-branch lookup needed
        # since a branch was explicitly supplied).
        svc = _make_service(
            {"allowed_repos": ["org/repo"], "protected_branches": ["main", "release/*"]}
        )
        with patch.object(svc, "_run_github", new=AsyncMock()) as mock_api:
            await svc._resolve_and_check_branch("org", "repo", "feature/x")
        mock_api.assert_not_called()

    @pytest.mark.asyncio
    async def test_explicit_branch_matching_protected_pattern_still_raises(
        self,
    ) -> None:
        # Sanity check paired with the allow-direction test above: the same
        # non-empty protected_branches config must still deny a matching branch.
        svc = _make_service(
            {"allowed_repos": ["org/repo"], "protected_branches": ["main", "release/*"]}
        )
        with patch.object(svc, "_run_github", new=AsyncMock()) as mock_api:
            with pytest.raises(GitHubAuthorizationError):
                await svc._resolve_and_check_branch("org", "repo", "release/1.0")
        mock_api.assert_not_called()


# ── _handle_github_error: previously-uncovered validation-error branch ───────


class TestHandleGithubErrorValidationBranch:
    def test_400_bad_request_raises_validation_error(self) -> None:
        exc = GithubException(HTTPStatus.BAD_REQUEST, {"message": "bad ref"}, {})
        with pytest.raises(GitHubValidationError, match="GitHub API validation error"):
            GitHubService._handle_github_error(exc)

    def test_422_unprocessable_entity_raises_validation_error(self) -> None:
        exc = GithubException(
            HTTPStatus.UNPROCESSABLE_ENTITY, {"message": "invalid"}, {}
        )
        with pytest.raises(GitHubValidationError, match="GitHub API validation error"):
            GitHubService._handle_github_error(exc)


# ── _run_github: direct exercise of the try/except wrapper itself ────────────


class TestRunGithubDirect:
    @pytest.mark.asyncio
    async def test_success_path_returns_callable_result(self) -> None:
        svc = _make_service()
        result = await svc._run_github(lambda: 42)
        assert result == 42

    @pytest.mark.asyncio
    async def test_github_exception_is_converted_to_domain_exception(self) -> None:
        svc = _make_service()

        def _raise() -> None:
            raise GithubException(HTTPStatus.NOT_FOUND, {"message": "missing"}, {})

        from mcp_servers.github.github_models import GitHubNotFoundError

        with pytest.raises(GitHubNotFoundError, match="Resource not found"):
            await svc._run_github(_raise)


# ── Audit before/after + correlation (REQ-004) ────────────────────────────────


class TestGithubAuditLog:
    """A successful github operation emits an audit record carrying the
    before/after target identity and an approval-correlation flag. Only
    identifiers are recorded — never issue/pr/body payloads."""

    @pytest.mark.asyncio
    async def test_create_or_update_file_emits_audit_with_before_after_and_approved(
        self, tmp_path: Path
    ) -> None:
        audit_path = tmp_path / "audit.log"
        gh = MagicMock()
        repo_mock = MagicMock()
        repo_mock.create_file.return_value = {
            "commit": MagicMock(sha="abcdef1234567890")
        }
        gh.get_repo.return_value = repo_mock
        svc = GitHubService(
            gh=gh,
            cfg=GitHubConfig.from_dict(
                {
                    "allowed_repos": ["org/repo"],
                    "audit_log_path": str(audit_path),
                    "protected_branches": ["release/*"],
                }
            ),
        )
        req = CreateOrUpdateFileRequest(
            owner="org",
            repo="repo",
            path="src/app.py",
            content="hello world",
            message="test",
            branch="main",
        )
        result = await svc.create_or_update_file(req)
        assert result.operation == "created"
        record = audit_path.read_text(encoding="utf-8")
        assert "op=create_or_update_file" in record
        assert "before=org/repo|" in record
        assert "after=org/repo|" in record
        assert "approved=true" in record


# ── Guard sufficiency (REQ-002, REQ-004) ──────────────────────────────────────


class TestGuardSufficiency:
    """Each existing guard rejects disallowed input (fail-closed); the clamp
    still bounds per_page above the configured maximum."""

    def test_assert_allowed_repo_denies_when_allowlist_empty(self) -> None:
        svc = _make_service({"allowed_repos": []})
        with pytest.raises(GitHubAuthorizationError):
            svc._assert_allowed_repo("org", "repo")

    def test_assert_allowed_repo_denies_unknown_repo(self) -> None:
        svc = _make_service({"allowed_repos": ["org/allowed"]})
        with pytest.raises(GitHubAuthorizationError):
            svc._assert_allowed_repo("org", "other")

    def test_assert_allowed_repo_allows_known_repo(self) -> None:
        svc = _make_service({"allowed_repos": ["org/allowed"]})
        svc._assert_allowed_repo("org", "allowed")

    def test_assert_allowed_path_denies_matched_glob(self) -> None:
        svc = _make_service(
            {"allowed_repos": ["org/repo"], "path_denylist": ["*.secret"]}
        )
        with pytest.raises(GitHubAuthorizationError):
            svc._assert_allowed_path("config.secret")

    def test_assert_allowed_path_allows_unmatched(self) -> None:
        svc = _make_service(
            {"allowed_repos": ["org/repo"], "path_denylist": ["*.secret"]}
        )
        svc._assert_allowed_path("src/app.py")

    def test_assert_allowed_branch_denies_protected(self) -> None:
        svc = _make_service(
            {"allowed_repos": ["org/repo"], "protected_branches": ["main"]}
        )
        with pytest.raises(GitHubAuthorizationError):
            svc._assert_allowed_branch("org", "repo", "main")

    def test_assert_allowed_branch_allows_unprotected(self) -> None:
        svc = _make_service(
            {"allowed_repos": ["org/repo"], "protected_branches": ["main"]}
        )
        svc._assert_allowed_branch("org", "repo", "feature/x")

    def test_clamp_per_page_bounds_above_max(self) -> None:
        svc = _make_service({"allowed_repos": ["org/repo"], "max_per_page": 25})
        assert svc._clamp_per_page(1000) == 25


# ── Legitimate-call regression ────────────────────────────────────────────────


class TestLegitimateCallRegression:
    @pytest.mark.asyncio
    async def test_create_or_update_file_succeeds_and_returns_response(
        self, tmp_path: Path
    ) -> None:
        audit_path = tmp_path / "audit.log"
        gh = MagicMock()
        repo_mock = MagicMock()
        repo_mock.create_file.return_value = {
            "commit": MagicMock(sha="deadbeef00001111")
        }
        gh.get_repo.return_value = repo_mock
        svc = GitHubService(
            gh=gh,
            cfg=GitHubConfig.from_dict(
                {
                    "allowed_repos": ["org/repo"],
                    "audit_log_path": str(audit_path),
                    "protected_branches": ["release/*"],
                }
            ),
        )
        req = CreateOrUpdateFileRequest(
            owner="org",
            repo="repo",
            path="README.md",
            content="hi",
            message="init",
            branch="main",
        )
        result = await svc.create_or_update_file(req)
        assert result.path == "README.md"
        assert result.operation == "created"
        assert result.commit_sha == "deadbeef00001111"


class TestGitHubConfigLoad:
    """GitHubConfig.load() fail-closed validation (ADR-004 REQ-004)."""

    @staticmethod
    def _patch_loader(monkeypatch: pytest.MonkeyPatch, raw: dict) -> None:
        class _FakeLoader:
            def load(self, name: str) -> dict:
                return raw

        monkeypatch.setattr(
            "mcp_servers.github.github_models_config.ConfigLoader", _FakeLoader
        )

    def test_load_rejects_empty_protected_branches(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        self._patch_loader(monkeypatch, {"protected_branches": []})
        with pytest.raises(ValueError, match="protected_branches"):
            GitHubConfig.load()

    def test_load_rejects_absent_protected_branches(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        self._patch_loader(monkeypatch, {})
        with pytest.raises(ValueError, match="protected_branches"):
            GitHubConfig.load()

    def test_load_allows_empty_path_denylist(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """An empty path_denylist stays valid under the ADR-004 exception."""
        self._patch_loader(
            monkeypatch, {"protected_branches": ["main"], "path_denylist": []}
        )
        cfg = GitHubConfig.load()
        assert cfg.path_denylist == []
        assert cfg.protected_branches == ["main"]


# ── _get_repo: the single repository boundary (mcpai002 REQ-001, REQ-002) ─────


class TestGetRepoBoundary:
    """The guard, the API slug, and the error text share one canonical key."""

    def test_mixed_case_caller_reaches_the_canonical_slug(self) -> None:
        gh = MagicMock()
        svc = GitHubService(
            gh=gh, cfg=GitHubConfig.from_dict({"allowed_repos": ["org/repo"]})
        )
        svc._get_repo("Org", "REPO")
        gh.get_repo.assert_called_once_with("org/repo")

    def test_repository_outside_the_allowlist_is_refused_before_the_client_call(
        self,
    ) -> None:
        gh = MagicMock()
        svc = GitHubService(
            gh=gh, cfg=GitHubConfig.from_dict({"allowed_repos": ["org/repo"]})
        )
        with pytest.raises(GitHubAuthorizationError, match="not in allowed_repos"):
            svc._get_repo("other", "repo")
        gh.get_repo.assert_not_called()

    def test_empty_allowlist_is_refused_before_the_client_call(self) -> None:
        gh = MagicMock()
        svc = GitHubService(gh=gh, cfg=GitHubConfig.from_dict({"allowed_repos": []}))
        with pytest.raises(GitHubAuthorizationError, match="allowed_repos is empty"):
            svc._get_repo("org", "repo")
        gh.get_repo.assert_not_called()

    def test_non_canonical_allowlist_entry_is_reported_instead_of_never_matching(
        self,
    ) -> None:
        gh = MagicMock()
        svc = GitHubService(
            gh=gh, cfg=GitHubConfig.from_dict({"allowed_repos": ["Org/Repo"]})
        )
        with pytest.raises(GitHubAuthorizationError, match="cannot match a repository"):
            svc._get_repo("org", "repo")
        gh.get_repo.assert_not_called()


# ── _assert_max_read_file_size: read-size limit, 0 = unlimited (REQ-006) ──────


class TestAssertMaxReadFileSize:
    def test_content_within_the_limit_passes(self) -> None:
        svc = _make_service(
            {"allowed_repos": ["org/repo"], "max_file_read_size_kb": 10}
        )
        svc._assert_max_read_file_size(10 * 1024, "docs/a.md")

    def test_content_above_the_limit_is_refused(self) -> None:
        svc = _make_service(
            {"allowed_repos": ["org/repo"], "max_file_read_size_kb": 10}
        )
        with pytest.raises(GitHubValidationError, match="max_file_read_size_kb"):
            svc._assert_max_read_file_size(11 * 1024, "docs/a.md")

    def test_zero_is_unlimited(self) -> None:
        svc = _make_service({"allowed_repos": ["org/repo"], "max_file_read_size_kb": 0})
        svc._assert_max_read_file_size(100 * 1024 * 1024, "docs/a.md")


# ── _resolve_search_query: boundary resolved before the call (REQ-004) ────────


class TestResolveSearchQuery:
    def test_bare_query_is_scoped_to_the_allowlisted_repository(self) -> None:
        svc = _make_service()
        assert svc._resolve_search_query("lang:python") == "(lang:python) repo:org/repo"

    def test_allowed_repo_qualifier_is_kept_and_the_query_is_scoped(self) -> None:
        svc = _make_service()
        query = svc._resolve_search_query("filename:a.py repo:org/repo")
        assert query == "(filename:a.py repo:org/repo) repo:org/repo"

    def test_non_key_terms_are_preserved(self) -> None:
        svc = _make_service()
        assert svc._resolve_search_query("is:open") == "(is:open) repo:org/repo"

    def test_repo_qualifier_outside_the_allowlist_is_refused(self) -> None:
        svc = _make_service()
        with pytest.raises(GitHubAuthorizationError, match="outside allowed_repos"):
            svc._resolve_search_query("repo:other/repo term")

    def test_owner_qualifier_outside_the_allowlist_is_refused(self) -> None:
        svc = _make_service()
        with pytest.raises(
            GitHubAuthorizationError, match="owner outside allowed_repos"
        ):
            svc._resolve_search_query("org:other term")

    def test_owner_qualifier_inside_the_allowlist_passes(self) -> None:
        svc = _make_service()
        assert (
            svc._resolve_search_query("org:org term") == "(org:org term) repo:org/repo"
        )

    def test_global_search_opt_in_returns_the_query_unchanged(self) -> None:
        svc = _make_service(
            {"allowed_repos": ["org/repo"], "allow_global_search": True}
        )
        assert svc._resolve_search_query("lang:python") == "lang:python"

    def test_empty_allowlist_refuses_a_scoped_search(self) -> None:
        svc = _make_service({"allowed_repos": []})
        with pytest.raises(GitHubAuthorizationError, match="no repository scope"):
            svc._resolve_search_query("lang:python")


# ── repo_scan: one boundary point per client repository call (AC-10) ─────────


class TestSingleRepoBoundary:
    @pytest.mark.repo_scan
    def test_no_service_module_reaches_get_repo_outside_the_guard(self) -> None:
        """Only `_get_repo()` in the guard module may call the client's get_repo."""
        package = Path(__file__).resolve().parents[3] / "scripts/mcp_servers/github"
        hits: dict[str, list[int]] = {}
        for path in sorted(package.glob("*.py")):
            lines = path.read_text(encoding="utf-8").splitlines()
            found = [num for num, line in enumerate(lines, 1) if "_gh.get_repo" in line]
            if found:
                hits[path.name] = found
        assert set(hits) == {"github_service_security.py"}
        guard_lines = (
            (package / "github_service_security.py")
            .read_text(encoding="utf-8")
            .splitlines()
        )
        for num in hits["github_service_security.py"]:
            assert "normalize_repo_key" in guard_lines[num - 1]
