## Goal

Bring the two search methods in this module inside the boundary defined by row 4: scope the query at construction time (REQ-003: `allow_global_search` default `false` scopes the search tools to `allowed_repos`) and resolve caller qualifiers before the API call (REQ-004: a qualifier outside the boundary is rejected, no result is filtered afterwards).

## Scope
**Release unit**: boundary tests (the search-boundary cases are written in Phase 2 and fail until Phase 3 lands)

## Assumptions

- `_resolve_search_query()` (new) and the canonical key are defined in `scripts/mcp_servers/github/github_service_security.py` (row 4); this document calls them through the inherited `GitHubSecurityGuards` mixin and defines no helper of its own.
- The three read methods in this module (`list_branches` line 71, `list_commits` line 115, `get_commit` line 138) need no change: they obtain repositories through `_get_repo()`, which becomes the boundary in row 4.
- `_clamp_per_page()` behavior is unchanged; per-page clamping is not part of the boundary.

## Design decisions

- Query construction happens once, in the guard helper, so the two search methods here and the two in rows 7-8 share one rule (Plan D-4). No post-filtering of results.
- The existing per-search result slicing (`itertools.islice` / list comprehension over the returned iterator) stays as it is; only the query string passed to the client changes.

## Alternatives considered

- Requiring the caller to pass an in-boundary `repo:` qualifier — rejected by Plan D-4 as a caller-facing contract change.
- Leaving `search_repositories` global while scoping only `search_code` — rejected: REQ-003 covers all four search tools.

## Implementation
### Target file
`scripts/mcp_servers/github/github_service_repository.py`

### Procedure
1. In `search_repositories()` (line 45), pass `req.query` through `_resolve_search_query()` and use the returned string in `self._gh.search_repositories(query=...)`.
2. In `search_code()` (line 158), the same: build the query through `_resolve_search_query()` before the client call.
3. No other change in this file: the read methods, the result conversion, and the clamping stay as they are.

### Method
- When `cfg.allow_global_search` is `false` the returned query carries a `repo:` qualifier for every allowlisted entry; when it is `true` the helper returns the caller query unchanged (AC-3).
- A `repo:` qualifier naming a repository outside `allowed_repos`, or an `org:`/`user:` value that does not correspond only to allowlisted entries, raises `GitHubAuthorizationError` before the client call, so the mock client records no request.

### Details
- The helper is called inside the existing `_sync()` closure, before the client call, so the rejection happens on the worker thread through the same `_run_github()` path as the other domain errors.
- File size 6766 B at baseline, below the 24576 B gate.

### Companion test files
- `tests/mcp_servers/github/test_service_repository.py`
  - Procedure: add the read-path allowlist cases for `list_branches`, `list_commits`, `get_commit` (refused before the client call) and the search-boundary cases for `search_repositories`/`search_code` with no qualifier, an allowed `repo:` qualifier, and a denied one; keep the existing cases, which use `org/repo` and the fixture default `allowed_repos = ["org/repo"]` at lines 67-69, green.
  - Validation: `uv run pytest tests/mcp_servers/github/test_service_repository.py` (AC-1, AC-3, AC-4); the read-boundary cases are written before this row lands, per the release unit.

## Compatibility considerations

- Search behavior changes from global to scoped for the default configuration (Plan Risks). The shipped config has one allowlisted entry, so request count is unchanged; only the query becomes scoped.
- The response models and `mapper.py` are untouched (Reference Files), so result shapes do not change.

## Security considerations

- Search results are repository data reachable by the token; scoping at query construction is what makes `allowed_repos` a real boundary for the search tools, and the postures' claim about it becomes true (REQ-009, REQ-011).

## Rollback considerations

- High: `allow_global_search = true` restores the current global-search behavior explicitly (Plan D-4); reverting this row restores the unscoped query construction.

## Validation plan

| Target | Strategy | Command | Expected outcome |
|---|---|---|---|
| `scripts/mcp_servers/github/github_service_repository.py` | Unit (query construction) | `uv run pytest tests/mcp_servers/github/test_service_repository.py` | The query sent to the client is scoped to an allowlisted repository; a denied qualifier is refused before the call |
| Same file | Quality gates | `uv run ruff check scripts/mcp_servers/github/github_service_repository.py`, `uv run mypy scripts/mcp_servers/github/github_service_repository.py`, `uv run bandit scripts/mcp_servers/github/github_service_repository.py` | No finding |

## Completion criteria

- Both search methods cannot issue a query that reaches a repository outside `allowed_repos` while `allow_global_search` is `false`, and the refusal is recorded before any client call (AC-3, AC-4).

## Out of Scope

- Defining the qualifier grammar (row 4) and the `allow_global_search` field (row 3).
- `search_issues` (row 7) and `search_pull_requests` (row 8).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261124-152854 | 20261124-152854 |  |
| 2 | Add or update tests per Validation plan (companion `tests/mcp_servers/github/test_service_repository.py`) | Completed | 20261124-152854 | 20261124-152854 | Written in Phase 2, before this row lands |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261124-152854 | 20261124-152854 |  |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: REQ-003 (search tools scoped at query-construction time), REQ-004 (caller qualifier rule)
- **Source issue**: issues/done/20261119-140509_mcpai002_github-read-security-boundary.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261124-095007_mcpai002_github-read-security-boundary.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261124-103302
- **Related target files**: `scripts/mcp_servers/github/github_service_repository.py`, `tests/mcp_servers/github/test_service_repository.py`