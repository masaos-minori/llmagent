# Implementation: tests/test_github_mcp_service.py — Abnormal Path Tests + Fixture Update

## Goal

Add 8 abnormal-path test cases covering the new fail-fast behaviors. Update existing test fixtures from `_get_cfg()` monkeypatch to direct `GitHubConfig` injection.

---

## Scope

**Target file:** `tests/test_github_mcp_service.py`

**In:**
- Add `GitHubConfig` fixture replacing `_get_cfg` monkeypatch
- Add 8 new test functions
- Update existing tests that use `_get_cfg` monkeypatch to use the new fixture
- Existing test coverage must not regress

**Out:**
- No new test files
- No changes to test logic for happy paths (only fixture update)

---

## Assumptions

1. Existing tests use `monkeypatch.setattr("mcp.github.models._get_cfg", ...)` — after Step 1, `_get_cfg` no longer exists; tests must pass `GitHubConfig` directly.
2. `GitHubService` constructor now takes `(gh: Github, cfg: GitHubConfig)` — tests create it with a mock `gh` and a `GitHubConfig(...)` instance.
3. `pytest-asyncio` is available for async tests.

---

## Implementation

### Target file
`tests/test_github_mcp_service.py`

### Procedure

**Fixture update:**
1. Add `@pytest.fixture` `github_cfg() -> GitHubConfig` that returns a permissive test config.
2. Replace all `monkeypatch.setattr("mcp.github.models._get_cfg", ...)` with constructing `GitHubService(mock_gh, github_cfg)`.

**New test cases:**

3. `test_unauthorized_repo_raises_authorization_error` — `GitHubConfig(allowed_repos=["owner/allowed"])` + call with `owner/other` → `GitHubAuthorizationError`
4. `test_fail_closed_empty_allowed_repos_raises` — `GitHubConfig(allowed_repos=[], allowed_repos_mode="fail_closed")` → `GitHubAuthorizationError`
5. `test_fail_open_empty_allowed_repos_passes` — `GitHubConfig(allowed_repos=[], allowed_repos_mode="fail_open")` → no exception
6. `test_unauthorized_path_raises_authorization_error` — `GitHubConfig(path_denylist=["*.env", ".secrets/*"])` + path=`.env` → `GitHubAuthorizationError`
7. `test_protected_branch_raises_authorization_error` — `GitHubConfig(protected_branches=["main"])` + branch=`main` → `GitHubAuthorizationError`
8. `test_github_api_404_raises_not_found_error` — mock PyGithub raises `GithubException(404, ...)` → `GitHubNotFoundError`
9. `test_github_api_403_raises_authorization_error` — mock PyGithub raises `GithubException(403, ...)` → `GitHubAuthorizationError`
10. `test_audit_failure_raises_audit_error` — `GitHubConfig(audit_log_path="/nonexistent/dir/audit.log")` + write op → `GitHubAuditError`

### Method

```python
import pytest
from unittest.mock import MagicMock, patch
from github import GithubException
from mcp.github.models import (
    GitHubConfig,
    GitHubAuthorizationError,
    GitHubNotFoundError,
    GitHubAuditError,
)
from mcp.github.service import GitHubService


@pytest.fixture
def permissive_cfg() -> GitHubConfig:
    return GitHubConfig(
        allowed_repos=[],
        allowed_repos_mode="fail_open",
        path_denylist=[],
        protected_branches=[],
        max_file_size_kb=0,
        audit_log_path="",
    )


@pytest.fixture
def mock_gh() -> MagicMock:
    return MagicMock()


def test_unauthorized_repo_raises_authorization_error(mock_gh):
    cfg = GitHubConfig(allowed_repos=["owner/allowed"], allowed_repos_mode="fail_closed")
    svc = GitHubService(mock_gh, cfg)
    with pytest.raises(GitHubAuthorizationError, match="not in allowed_repos"):
        svc._assert_allowed_repo("owner", "other")


def test_fail_closed_empty_allowed_repos_raises(mock_gh):
    cfg = GitHubConfig(allowed_repos=[], allowed_repos_mode="fail_closed")
    svc = GitHubService(mock_gh, cfg)
    with pytest.raises(GitHubAuthorizationError, match="fail_closed"):
        svc._assert_allowed_repo("any", "repo")


def test_fail_open_empty_allowed_repos_passes(mock_gh, permissive_cfg):
    svc = GitHubService(mock_gh, permissive_cfg)
    svc._assert_allowed_repo("any", "repo")  # no exception


def test_unauthorized_path_raises_authorization_error(mock_gh):
    cfg = GitHubConfig(path_denylist=["*.env", ".secrets/*"], allowed_repos_mode="fail_open")
    svc = GitHubService(mock_gh, cfg)
    with pytest.raises(GitHubAuthorizationError, match="path_denylist"):
        svc._assert_allowed_path(".env")


def test_protected_branch_raises_authorization_error(mock_gh):
    cfg = GitHubConfig(protected_branches=["main"], allowed_repos_mode="fail_open")
    svc = GitHubService(mock_gh, cfg)
    with pytest.raises(GitHubAuthorizationError, match="protected"):
        svc._assert_allowed_branch("owner", "repo", "main")


def test_github_api_404_raises_not_found_error():
    exc = GithubException(404, {"message": "Not Found"}, {})
    with pytest.raises(GitHubNotFoundError):
        GitHubService._handle_github_error(exc)


def test_github_api_403_raises_authorization_error():
    exc = GithubException(403, {"message": "Forbidden"}, {})
    with pytest.raises(GitHubAuthorizationError):
        GitHubService._handle_github_error(exc)


def test_audit_failure_raises_audit_error(mock_gh):
    cfg = GitHubConfig(
        audit_log_path="/nonexistent_dir_xyz/audit.log",
        allowed_repos_mode="fail_open",
    )
    svc = GitHubService(mock_gh, cfg)
    with pytest.raises(GitHubAuditError, match="Audit log write failed"):
        svc._write_github_audit_log("test_op", key="value")
```

### Details

- Existing tests that call `GitHubService(mock_gh, default_per_page=10, max_per_page=100)` must be updated to `GitHubService(mock_gh, permissive_cfg)` after Step 2 changes the constructor.
- `test_tool_schema_matches_request_model` (from Step 4) can be added here: assert `len(TOOL_LIST) == len(_TOOL_SPECS)` and spot-check a few field names.
- The `_assert_allowed_path` and `_assert_allowed_branch` are converted from `@staticmethod` to instance methods in Step 2 — tests must call `svc._assert_allowed_path(...)` not `GitHubService._assert_allowed_path(...)`.

---

## Validation plan

| Check | Command | Target |
|---|---|---|
| Tests | `uv run pytest tests/test_github_mcp_service.py -v` | all pass |
| Coverage | `uv run coverage run -m pytest tests/test_github_mcp_service.py && uv run diff-cover coverage.xml --compare-branch=master` | ≥ 90% on changed lines |
| Type check | `uv run mypy tests/test_github_mcp_service.py` | no errors |
