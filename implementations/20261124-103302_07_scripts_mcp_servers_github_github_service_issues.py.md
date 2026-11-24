## Goal

Bring `search_issues()` inside the query-construction boundary defined by row 4 (REQ-003: search tools are scoped to `allowed_repos` when `allow_global_search` is `false`; REQ-004: caller `repo:`/`org:`/`user:` qualifiers are resolved before the API call).

## Scope
**Release unit**: boundary tests (the search-boundary cases are written in Phase 2 and fail until Phase 3 lands)

## Assumptions

- `_resolve_search_query()` (new) is defined in `scripts/mcp_servers/github/github_service_security.py` (row 4); this document calls it through the inherited `GitHubSecurityGuards` mixin.
- `list_issues` (line 40) and `get_issue` (line 53) need no change here: they obtain repositories through `_get_repo()`, which becomes the boundary in row 4.
- The write methods (`create_issue` line 64, `add_issue_comment` line 103) keep their existing explicit `_assert_allowed_repo()` calls (Plan D-2).

## Design decisions

- No post-filtering of search results (Plan D-4): the boundary is applied when the query string is built, so counts, errors, and timing reflect the scoped query.
- The existing `itertools.islice` slicing over the returned iterator stays; only the query passed to `self._gh.search_issues()` changes.

## Alternatives considered

- Keeping issues search global while scoping the other tools — rejected by REQ-003, which names all four search tools.

## Implementation
### Target file
`scripts/mcp_servers/github/github_service_issues.py`

### Procedure
1. In `search_issues()` (lines 88-95), pass `req.query` through `_resolve_search_query()` and use the returned string in `self._gh.search_issues(query=...)`.
2. No other change in this file.

### Method
- Non-keyword search terms such as `is:open` or `state:closed` are not repository or owner qualifiers and are preserved by the helper; only `repo:`, `org:`, `user:` are evaluated against `allowed_repos` (REQ-004).
- A rejected qualifier raises `GitHubAuthorizationError` inside the `_sync()` closure, before the client call.

### Details
- File size 4488 B at baseline, below the 24576 B gate.
- `issue_to_info()` conversion in `mapper.py` is untouched (Reference File).

### Companion test files
- `tests/mcp_servers/github/test_service_issues.py`
  - Procedure: add the read-path allowlist cases for `list_issues` and `get_issue` (refused before the client call) and the search-boundary cases for `search_issues` — no qualifier, an allowed `repo:` qualifier, a denied one, and a query that keeps a non-repository keyword such as `is:open`; existing cases use `org/repo` with the fixture default `allowed_repos = ["org/repo"]` at lines 54-56 and stay green.
  - Validation: `uv run pytest tests/mcp_servers/github/test_service_issues.py` (AC-1, AC-3, AC-4); the read-boundary cases are written before this row lands, per the release unit.

## Compatibility considerations

- Issues search becomes scoped for the default configuration (Plan Risks); the shipped single-entry allowlist keeps the request count at one query per call.
- Existing tests that assert query construction (no qualifier handling today) are extended, not removed.

## Security considerations

- Issue content is repository data reachable by the token; the boundary makes `allowed_repos` authoritative for this tool as REQ-011 states.

## Rollback considerations

- High: `allow_global_search = true` restores the current behavior; reverting this line restores the unscoped query.

## Validation plan

| Target | Strategy | Command | Expected outcome |
|---|---|---|---|
| `scripts/mcp_servers/github/github_service_issues.py` | Unit (query construction) | `uv run pytest tests/mcp_servers/github/test_service_issues.py` | The query sent to the client is scoped to an allowlisted repository; a denied qualifier is refused before the call |
| Same file | Quality gates | `uv run ruff check scripts/mcp_servers/github/github_service_issues.py`, `uv run mypy scripts/mcp_servers/github/github_service_issues.py`, `uv run bandit scripts/mcp_servers/github/github_service_issues.py` | No finding |

## Completion criteria

- `search_issues()` cannot issue a query that reaches a repository outside `allowed_repos` while `allow_global_search` is `false` (AC-3, AC-4).

## Out of Scope

- The qualifier grammar and the config field (rows 4, 3).
- `search_pull_requests()` (row 8).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan (companion `tests/mcp_servers/github/test_service_issues.py`) | Pending | — | — | Written in Phase 2, before this row lands |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |

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
- **Related target files**: `scripts/mcp_servers/github/github_service_issues.py`, `tests/mcp_servers/github/test_service_issues.py`
