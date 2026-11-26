## Goal

Declare issue scope for `github_add_issue_comment` so comments on different issues no longer
serialize against each other (REQ-001, AC-2), while `github_create_issue` stays at repository
scope.

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- `_GITHUB_ISSUE_REPO_SCOPE_TAIL` (`scripts/mcp_servers/github/tools_issues.py:63-67`) is spread
  into the read entries (90, 106) as well as the write entries (122, 156), so the write entries
  need their own tail constant; the read entries keep the repo-scoped tail (reads are out of scope
  per the Plan's Out-of-Scope).
- `github_create_issue` (entry at 109) keeps `github_repo`: `CreateIssueRequest`
  (`github_models_issues.py:52-70`) has no `issue_number`, so the resource identity does not exist
  at call time, and `validate_tool_schema_v2()` rejects a scope key that is not in
  `inputSchema.properties` (`resource_scope.py:157-161`). Owner decision 20261126.
- `github_add_issue_comment` (entry at 142) declares `issue_number` (
  `github_models_issues.py:78-88`), so the key passes the validator.
- `github_search_issues` uses `_GITHUB_ISSUE_NO_SCOPE_TAIL` (139) and is unchanged.

## Design decisions
- Add a dedicated issue-scoped tail constant next to the existing repo-scoped one, mirroring the
  head/tail split already used in this file; do not inline per-entry metadata.
- Key kinds: `owner` stays `non_escalating`, `repo` stays `repo`, `issue_number` uses the new
  `issue` key kind (procedure 02).

## Alternatives considered
- Change the shared tail for all entries: rejected — it would move the read entries to issue scope
  and `github_create_issue` would fail validation.
- Declare `github_issue` for `github_create_issue` with keys `{owner, repo}`: rejected — the
  resolved string `github_issue:<owner>/<repo>` is not the ancestor `github_repo:<owner>/<repo>`
  string, so the call would stop conflicting with repository-wide writes (REQ-005).

## Implementation
### Target file
`scripts/mcp_servers/github/tools_issues.py`

### Procedure
1. Add a `_GithubIssueScopeTail` (new) TypedDict next to `_GithubIssueRepoScopeTail` (43-49).
2. Add `_GITHUB_ISSUE_SCOPE_TAIL` (new) with `requires_serial: False`,
   `resource_scope_kind: "github_issue"`, and
   `resource_scope_keys: {"owner": "non_escalating", "repo": "repo", "issue_number": "issue"}`.
3. Spread the new tail into the `github_add_issue_comment` entry (156); keep the repo tail for
   `github_create_issue` (122) and for the read entries (90, 106).
4. Update the shared-metadata comment block to state that the repo tail covers the read entries
   and `github_create_issue`, and that the comment entry uses the issue-scoped tail.

### Method
Keep the field order (`requires_serial`, `resource_scope_kind`, `resource_scope_keys`) unchanged so
the byte-for-byte shared-field structure the comment block describes still holds within each group.

### Details
- The composed scope string is `github_issue:<owner>/<repo>/<issue_number>`, produced by
  `_COMPOSED_KIND_SEPARATORS` (procedure 01); this file only declares the kind and keys.

## Compatibility considerations
- The comment block is the record of which fields are byte-for-byte identical across entries; it
  must match the new grouping or the schema-consistency test that pins the tails (created by the
  mcpai010 procedure) will disagree with the file.
- `tests/shared/test_resource_scope.py` (target row 6) asserts the resolved scope strings.

## Security considerations
- No authorization or correctness change. A comment call whose `issue_number` is absent cannot be
  built (the field is required), so no write falls to a looser scope.

## Rollback considerations
- N/A: revert the commit (single-commit change, one file).

## Validation plan
| Check | Command | Expected |
|---|---|---|
| Unit | `uv run pytest tests/shared/test_resource_scope.py tests/mcp_servers/github/test_github_tool_schema.py -v` | `github_add_issue_comment` resolves `github_issue:<owner>/<repo>/<n>`; `github_create_issue` still resolves `github_repo:<owner>/<repo>` |
| Static | `uv run ruff format --check scripts/mcp_servers/github/tools_issues.py`, `uv run ruff check scripts/mcp_servers/github/tools_issues.py`, `uv run mypy --no-namespace-packages scripts/ tests/eventbus tools` | No new findings |
| Architecture | `PYTHONPATH=scripts uv run lint-imports` | `shared-is-leaf` kept |
| Security | `uv run bandit -r scripts/ -c pyproject.toml -ll` | No new findings |

## Completion criteria
- `github_add_issue_comment` declares `github_issue` with the `issue_number` key; `github_create_issue`
  and the read entries still declare `github_repo` (AC-2).
- The comment block describes the actual grouping.

## Out of Scope
- The scope-kind vocabulary and the ancestor rule — procedure 01.
- Test files — procedure 06.
- The pull-request declarations — procedure 05.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | N/A | — | — | N/A: documentation is covered by procedure 08 |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | N/A: no blocker recorded at procedure creation | N/A: no blocker recorded | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: `REQ-001` (finer scopes for provably independent resources)
- **Source issue**: issues/20261119-140520_mcpai013_github-resource-scope-refine.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261126-073010_mcpai013_github-resource-scope-refine.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261126-215042
- **Related target files**: `scripts/mcp_servers/github/tools_issues.py`
