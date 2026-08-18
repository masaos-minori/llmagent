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
    direction of that branch, previously untested; only the "deny" and the
    "protected_branches empty -> skip entirely" directions were covered)
  - _handle_github_error: HTTP 400 / 422 -> GitHubValidationError (only
    404/403/409/500 were covered previously)
  - _run_github: success path and GithubException-to-domain-exception
    conversion path, exercised directly (previously only exercised through
    higher-level methods with `_run_github` itself mocked out)
"""

from __future__ import annotations

from http import HTTPStatus
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from github import GithubException
from mcp_servers.github.github_models import (
    GitHubAuthorizationError,
    GitHubConfig,
    GitHubValidationError,
)
from mcp_servers.github.service_dispatch import GitHubService


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
        # protected_branches is non-empty (so the early-return skip at the top
        # of _resolve_and_check_branch does NOT apply) and the supplied branch
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
