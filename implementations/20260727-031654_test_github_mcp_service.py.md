## Goal

Extend `tests/test_github_mcp_service.py` with unit tests for GitHub MCP service layer business logic methods to raise coverage from 21-47% to ≥70%.

## Scope

**In-Scope:**
- Add tests for each service module's public methods:
  - `service_file.py`: get_file_contents, create_or_update_file, push_files, delete_repo_file
  - `service_issues.py`: list_issues, get_issue, create_issue, search_issues, add_issue_comment
  - `service_pull_requests.py`: list_pull_requests, get_pull_request, create_pull_request, search_pull_requests, update_pull_request, merge_pull_request
  - `service_repository.py`: search_repositories, list_branches, create_branch, list_commits, get_commit, search_code
- For each method: success path + error path (4xx/5xx)

**Out-of-Scope:**
- Modifying production code or existing tests beyond what's needed for coverage
- Integration/E2E tests — unit-level mocking only

## Assumptions

1. The existing `_make_service(cfg)` fixture is sufficient as a base; new tests will extend it with mocked GitHub API responses
2. The `gh` parameter passed to GitHubService is a PyGithub `Github` instance whose methods return controlled objects when mocked
3. Error paths use `GithubException` which can be raised by mocking the underlying HTTP client

## Unknowns

| ID | Unknown Description | Resolution Path | Blocking? (True/False) |
|---|---|---|---|
| UNK-01 | How PyGithub methods are called internally (method signatures, return types) | Read service_*.py source files to identify PyGithub calls | False |
| UNK-02 | Whether error responses come from PyGithub exceptions or HTTP status codes | Check exception_handlers.py and _handle_github_error() | False |
| UNK-03 | What request model classes are required for each method | Check models_config.py for request/response types | False |

## Affected Areas & Tool Evidence

- **Affected Files:**
  - `tests/test_github_mcp_service.py` — extend with ~20+ new test methods across 4 service modules
  - `scripts/mcp_servers/github/service_file.py` — reference for understanding PyGithub calls
  - `scripts/mcp_servers/github/service_issues.py` — reference for understanding PyGithub calls
  - `scripts/mcp_servers/github/service_pull_requests.py` — reference for understanding PyGithub calls
  - `scripts/mcp_servers/github/service_repository.py` — reference for understanding PyGithub calls

- **Blast Radius:**
  - Very low churn — new test methods only
  - Very low risk since change is purely additive

- **Deploy Impact:**
  - Existing — no deploy.sh changes needed

## Design

Based on inspection of `service_file.py`:
```python
# Each service method follows this pattern:
async def get_file_contents(self, req: GetFileContentsRequest) -> GetFileContentsResponse:
    def _sync() -> GetFileContentsResponse:
        repo = self._get_repo(req.owner, req.repo)
        file_content = repo.get_contents(req.path, **kwargs)
        # ... process result
        return GetFileContentsResponse(...)
    return await self._run_github(_sync)

# To mock: patch repo.get_contents() to return a MagicMock with .decoded_content, .sha, .size attributes
```

Test structure:
```python
class TestServiceFile:
    @pytest.mark.asyncio
    async def test_get_file_contents_success(self) -> None:
        # Mock repo.get_contents() to return file content
        # Verify response contains expected fields

    @pytest.mark.asyncio
    async def test_get_file_contents_not_found(self) -> None:
        # Mock repo.get_contents() to raise GithubException(404)
        # Verify GitHubNotFoundError is raised

    # ... similar for create_or_update_file, push_files, delete_repo_file

class TestServiceIssues:
    # ... list_issues, get_issue, create_issue, search_issues, add_issue_comment

class TestServicePullRequests:
    # ... list_pull_requests, get_pull_request, create_pull_request, search_pull_requests, update_pull_request, merge_pull_request

class TestServiceRepository:
    # ... search_repositories, list_branches, create_branch, list_commits, get_commit, search_code
```

## Implementation

### Target file
`tests/test_github_mcp_service.py`

### Procedure
1. Open `tests/test_github_mcp_service.py`
2. Add imports for request model classes from `mcp_servers.github.github_models`
3. Add `TestServiceFile` class with tests for get_file_contents, create_or_update_file, push_files, delete_repo_file (success + error paths)
4. Add `TestServiceIssues` class with tests for list_issues, get_issue, create_issue, search_issues, add_issue_comment (success + error paths)
5. Add `TestServicePullRequests` class with tests for list_pull_requests, get_pull_request, create_pull_request, search_pull_requests, update_pull_request, merge_pull_request (success + error paths)
6. Add `TestServiceRepository` class with tests for search_repositories, list_branches, create_branch, list_commits, get_commit, search_code (success + error paths)
7. Save the file

### Method
Add test classes following the existing pattern in the file, using MagicMock for PyGithub objects.

### Details
For each service method:
- Success path: mock PyGithub objects to return controlled values, verify response fields
- Error path: mock PyGithub objects to raise `GithubException(status=4xx/5xx)`, verify appropriate error handling

Key mocking patterns:
- `repo.get_contents(path)` → return MagicMock with `.decoded_content`, `.sha`, `.size` attributes
- `repo.get_issue(number)` → return MagicMock with `.title`, `.body`, `.state` attributes
- `repo.get_pull(pull_number)` → return MagicMock with `.title`, `.body`, `.state` attributes
- `repo.search_code(query)` → return MagicMock with `.total_count`, `.items` attributes

## Compatibility considerations

N/A — test additions have no runtime effect

## Security considerations

N/A

## Rollback considerations

- Simple revert: remove the added test classes

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `tests/test_github_mcp_service.py` | All new tests pass individually | `uv run pytest tests/test_github_mcp_service.py -v` | All tests pass |
| Coverage verification | Each target file reaches ≥70% coverage | `uv run pytest tests/test_github_mcp_service.py --cov=mcp_servers/github --cov-report=term-missing` | Coverage ≥70% per file |

## Out of scope

- Modifying production code or existing tests beyond what's needed for coverage
- Integration/E2E tests — unit-level mocking only

## Traceability

- Workflow phase: plan-to-implementation-procedure
- Source issue: N/A
- Source requirement: N/A
- Source plan: plans/20260726-163642_plan.md
- Source implementation procedure: N/A
- Generated at: 20260727-031654
- Related target files: scripts/mcp_servers/github/service_file.py, scripts/mcp_servers/github/service_issues.py, scripts/mcp_servers/github/service_pull_requests.py, scripts/mcp_servers/github/service_repository.py
