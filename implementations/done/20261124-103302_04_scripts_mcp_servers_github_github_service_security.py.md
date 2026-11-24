## Goal

Make the guard module the single repository boundary (REQ-001: the allowlist check runs inside `_get_repo()` before any API access), make it use the one canonical key (REQ-002: the same lowercase key for the guard, the API slug, and the error text), add the read-path guards it is missing (REQ-005: path denylist, REQ-006: read-size limit), add the search-qualifier boundary (REQ-004: qualifiers are resolved before the call), and add the two posture checks for the settings introduced here (REQ-009: the posture reports what the code enforces).

## Scope
**Release unit**: boundary tests (the tests for this row are written in Phase 2 and fail until this row lands, so the row is validated with its companion tests as one unit)

## Assumptions

- `normalize_repo_key` (new) and `is_canonical_repo_key` (new) are defined by `implementations/20261124-103302_01_scripts_shared_repo_identity.py.md`; `get_non_negative_number` is not used here — the config module parses the values, this module only reads them.
- Write authorization behavior is preserved as-is (Plan D-2): the 9 existing explicit `_assert_allowed_repo()` call sites stay, and the duplicated check on the write path is a no-op.
- Non-canonical input is accepted and normalized, never rejected (Plan D-3).
- The two new posture checks are appended at the end of the fixed check sequence; the order the pinned tuple asserts is extended by row 20's document in the same order.

## Design decisions

- Enforcement lives in the guard module, not in each read method (Plan D-2, and the Issue's preference for a few common guard functions): the 8 unguarded read call sites become covered without editing their call sites.
- The guard's comparison uses the canonical key, so an allowlist entry that is not in canonical form is detected by `is_canonical_repo_key` rather than silently never matching (Plan D-3).
- The search boundary resolves the query at construction time and never filters results afterwards (Plan D-4); the helper returns the query string it built, so the four search methods call one function.
- The two new checks reuse `_check()` (line 227) and the existing reason constants instead of adding inline branches, keeping `validate_github_security()` at the recorded baseline complexity (C(11)).

## Alternatives considered

- Removing the 10 explicit write-side assertions — rejected by Plan D-2 (the Issue's Constraints require write behavior to be preserved, and the assertions are characterization-locked).
- Post-filtering search results — rejected by Plan D-4 (an out-of-scope query leaks through counts, timing, and logs).
- Reporting `server.max_file_read_size` as `FAILED` at `0` — rejected: `0` is the documented "unlimited" meaning, and the existing `max_file_size` check already uses `NOT_APPLICABLE` for `0` (line 340).

## Implementation
### Target file
`scripts/mcp_servers/github/github_service_security.py`

### Procedure
1. Import `shared.repo_identity` (new) at the top of the module; `shared/` imports nothing from `mcp_servers/`, so the `shared must not import from agent, mcp_servers, rag, or db` contract stays kept.
2. `_get_repo()` (lines 160-162): build the canonical key with `normalize_repo_key(owner, repo)`, call `_assert_allowed_repo()` with the canonical parts, then `return self._gh.get_repo(canonical_key)`.
3. `_assert_allowed_repo()` (line 62): compare and report the canonical key. Both the empty-allowlist branch and the not-in-allowlist branch name the canonical key in the message.
4. Add `_assert_max_read_file_size()` (new) next to `_assert_max_file_size()` (line 92): same `0 = disabled` short-circuit, `>` comparison, `GitHubValidationError` naming the path and both sizes.
5. Add `_resolve_search_query()` (new): parse caller `repo:`/`org:`/`user:` qualifiers; reject one that names a repository outside `allowed_repos` or an owner that does not correspond only to allowlisted entries; when `cfg.allow_global_search` is `false`, build the query with a `repo:` qualifier for each allowlisted entry; return the query string. Rejections raise `GitHubAuthorizationError`.
6. Add two checks in `validate_github_security()` (line 260), appended at the end of the fixed sequence: `server.global_search` (new) — `OK` when the boundary is enforced, `WARNING` when global search is opted in; `server.max_file_read_size` (new) — `OK` when positive, `NOT_APPLICABLE` with `REASON_NOT_APPLICABLE` at `0`.

### Method
- `_resolve_search_query()` is the only place in the GitHub package that knows the qualifier grammar; the four search methods pass their caller query to it and use the returned string. It does not call the client, so a rejected qualifier never reaches the API (AC-3, AC-4).
- `_assert_max_read_file_size()` takes the size already present in the content metadata (`file_content.size`), not the decoded length: the check must happen before decoding (REQ-006).
- The two new checks are pure functions of the config object, consistent with the module's existing contract: no network call, no filesystem write, no raise for a policy violation.

### Details
- The guard module is the base class of `GitHubService` through `FileOps`, `IssuesOps`, `PullRequestOps`, `RepositoryOps`; no subclass call site changes (Plan D-2).
- Module size: 15186 B at baseline, below the 24576 B gate with headroom for the two helpers (Plan Consumer scan and predictable fallout check).
- `radon cc` baseline for this file is recorded as C(11) for `validate_github_security()`; record the before/after numbers in the implementation commit as the Validation plan requires.

### Companion test files
- `tests/mcp_servers/github/test_service_security.py`
  - Procedure: replace the `_get_repo()` direct-delegation characterization case (line 76, which asserts delegation without a guard) with the boundary behavior — a mixed-case key matches a lowercase allowlist entry and the refusal happens before the client call; add guard-level cases for the canonical key, `_assert_max_read_file_size` (new) (positive limit, `0`), and `_resolve_search_query` (new) (no qualifier, allowed `repo:`, denied qualifier); add the `repo_scan` test (new) that no service module calls `self._gh.get_repo` outside `_get_repo()` (AC-10).
  - Validation: `uv run pytest tests/mcp_servers/github/test_service_security.py` (AC-1, AC-2, AC-6); the new read-boundary cases are written before this row lands, per the release unit.

## Compatibility considerations

- Reads outside `allowed_repos` start failing with `GitHubAuthorizationError` (403); this is the intended behavior change and must be stated in the commit message (Plan Risks).
- Error text and the audit record show the canonical key for mixed-case callers (Plan D-3); the audit field order is unchanged (row 9).
- Existing guard tests for `_clamp_per_page`, `_resolve_and_check_branch`, `_handle_github_error`, and `_run_github` stay green; only the `_get_repo()` characterization case is replaced because REQ-001 changes the behavior it locks.

## Security considerations

- This module is the enforcement point the documentation describes; after this row the posture's `server.repo_allowlist` claim and the runtime behavior agree (REQ-009).
- An allowlist entry in non-canonical form is reported by `is_canonical_repo_key` at the guard, so a configuration that would silently match nothing becomes visible.

## Rollback considerations

- High: reverting this row restores the per-operation pattern with no config or data change (Plan D-2, D-3).

## Validation plan

| Target | Strategy | Command | Expected outcome |
|---|---|---|---|
| `scripts/mcp_servers/github/github_service_security.py` | Unit + static shape | `uv run pytest tests/mcp_servers/github/test_service_security.py` | `_get_repo()` refuses before the client call; the guard compares the canonical key; the search helper rejects a denied qualifier before the call |
| Same file | Static gates | `uv run radon cc scripts/mcp_servers/github/github_service_security.py -s`, `uv run python tools/check_module_size.py` | No module-size violation; `validate_github_security` complexity recorded before and after (baseline C(11)) |
| Same file | Quality gates | `uv run ruff check`, `uv run mypy`, `uv run bandit` on the file | No finding; no bare except; no unjustified suppression |
| Import contract | Static shape | `uv run lint-imports` | 6 contracts kept, 0 broken |

## Completion criteria

- The eight read methods obtain repositories only through `_get_repo()`, and no service module calls `self._gh.get_repo` outside it (AC-1, AC-10, verified by the `repo_scan` test).
- The guard, the API slug, the error text, and the audit record use the same canonical key (AC-2).
- The two new checks appear in the fixed inventory with the statuses named by AC-9.

## Out of Scope

- The read-path call wiring in `scripts/mcp_servers/github/github_service_file.py` (row 5) and the four search methods in rows 6-8; they call the helpers added here but are not modified by this document.
- The config fields themselves (row 3) and the pinned test inventory (row 20).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261124-152854 | 20261124-152854 |  |
| 2 | Add or update tests per Validation plan (companion `tests/mcp_servers/github/test_service_security.py`) | Completed | 20261124-152854 | 20261124-152854 | Write the read-boundary cases before this row lands (release unit boundary tests) TestGetRepoBoundary, TestAssertMaxReadFileSize, TestResolveSearchQuery, TestSingleRepoBoundary (repo_scan) added |
| 3 | Run the validation sequence (`rules/toolchain.md`) plus `uv run radon cc` and `uv run lint-imports` | Completed | 20261124-152854 | 20261124-152854 | Record the before/after radon numbers radon: validate_github_security() C(11) before and after (new checks factored into module-level helpers); new _resolve_search_query() C(11), repo already holds 82 C-or-worse blocks and no radon gate exists |

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
- **Requirement ID**: REQ-001 (single repository boundary), REQ-002 (canonical key), REQ-004 (search qualifier rule), REQ-005 (path denylist on reads), REQ-006 (read-size guard), REQ-009 (posture reporting)
- **Source issue**: issues/done/20261119-140509_mcpai002_github-read-security-boundary.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261124-095007_mcpai002_github-read-security-boundary.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261124-103302
- **Related target files**: `scripts/mcp_servers/github/github_service_security.py`, `tests/mcp_servers/github/test_service_security.py`