## Goal

Bring `search_pull_requests()` inside the query-construction boundary defined by row 4 (REQ-003: search tools are scoped to `allowed_repos` when `allow_global_search` is `false`; REQ-004: caller `repo:`/`org:`/`user:` qualifiers are resolved before the API call) while keeping the `is:pr` behavior this method already has.

## Scope
**Release unit**: boundary tests (the search-boundary cases are written in Phase 2 and fail until Phase 3 lands)

## Assumptions

- `_resolve_search_query()` (new) is defined in `scripts/mcp_servers/github/github_service_security.py` (row 4); this document calls it through the inherited `GitHubSecurityGuards` mixin.
- `list_pull_requests` (line 44) and `get_pull_request` (line 60) need no change here: they obtain repositories through `_get_repo()`, which becomes the boundary in row 4.
- The write methods keep their existing explicit `_assert_allowed_repo()` calls (Plan D-2).
- `is:` is a search keyword, not a repository or owner qualifier, so the boundary helper does not evaluate it against `allowed_repos`.

## Design decisions

- Resolve the caller query through the boundary first, then append `is:pr` if it is absent: the current construction (`query if "is:pr" in query else f"{query} is:pr"`, line 111) stays behaviorally identical for in-boundary queries, and the scoped query is the one sent.
- No post-filtering of results (Plan D-4).

## Alternatives considered

- Appending `is:pr` before the boundary check — rejected: the helper would then receive a query it must parse as a whole, and the `is:` keyword handling would have to be duplicated in the helper.
- Leaving PR search global — rejected by REQ-003.

## Implementation
### Target file
`scripts/mcp_servers/github/github_service_pull_requests.py`

### Procedure
1. In `search_pull_requests()` (lines 103-120), pass `req.query` through `_resolve_search_query()`, then keep the existing `is:pr` append on the returned string and use it in `self._gh.search_issues(query=...)`.
2. No other change in this file.

### Method
- A `repo:` qualifier naming a repository outside `allowed_repos`, or an `org:`/`user:` value that does not correspond only to allowlisted entries, raises `GitHubAuthorizationError` inside the `_sync()` closure before the client call.
- When `cfg.allow_global_search` is `true`, the helper returns the caller query unchanged and `is:pr` is appended as it is today (AC-3).

### Details
- File size 7290 B at baseline, below the 24576 B gate.
- The `issue_to_info()` conversion path is untouched (Reference File `mapper.py`).

### Companion test files
- `tests/mcp_servers/github/test_service_pull_requests.py`
  - Procedure: add the read-path allowlist cases for `list_pull_requests` and `get_pull_request` (refused before the client call) and the search-boundary cases for `search_pull_requests` — no qualifier, an allowed `repo:` qualifier, a denied one — asserting that the query sent is the scoped one with `is:pr` preserved; existing cases use `org/repo` with the fixture default `allowed_repos = ["org/repo"]` and stay green.
  - Validation: `uv run pytest tests/mcp_servers/github/test_service_pull_requests.py` (AC-1, AC-3, AC-4); the read-boundary cases are written before this row lands, per the release unit.

## Compatibility considerations

- PR search becomes scoped for the default configuration (Plan Risks); the shipped single-entry allowlist keeps the request count at one query per call.
- Callers that pass `is:pr` explicitly keep the same query string; only out-of-boundary qualifiers change outcome (from results to a 403 refusal).

## Security considerations

- PR metadata is repository data reachable by the token; the boundary makes `allowed_repos` authoritative for this tool as REQ-011 states.

## Rollback considerations

- High: `allow_global_search = true` restores the current behavior; reverting this line restores the unscoped query.

## Validation plan

| Target | Strategy | Command | Expected outcome |
|---|---|---|---|
| `scripts/mcp_servers/github/github_service_pull_requests.py` | Unit (query construction) | `uv run pytest tests/mcp_servers/github/test_service_pull_requests.py` | The query sent to the client is scoped to an allowlisted repository; a denied qualifier is refused before the call; `is:pr` is preserved |
| Same file | Quality gates | `uv run ruff check scripts/mcp_servers/github/github_service_pull_requests.py`, `uv run mypy scripts/mcp_servers/github/github_service_pull_requests.py`, `uv run bandit scripts/mcp_servers/github/github_service_pull_requests.py` | No finding |

## Completion criteria

- `search_pull_requests()` cannot issue a query that reaches a repository outside `allowed_repos` while `allow_global_search` is `false` (AC-3, AC-4).

## Out of Scope

- The qualifier grammar and the config field (rows 4, 3).
- Retry and rate-limit behavior (mcpai006).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan (companion `tests/mcp_servers/github/test_service_pull_requests.py`) | Pending | — | — | Written in Phase 2, before this row lands |
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
- **Related target files**: `scripts/mcp_servers/github/github_service_pull_requests.py`, `tests/mcp_servers/github/test_service_pull_requests.py`
