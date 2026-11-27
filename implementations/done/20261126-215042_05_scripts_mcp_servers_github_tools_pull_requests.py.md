## Goal

Declare pull-request scope for `github_update_pull_request` so updates to different pull requests
no longer serialize against each other (REQ-001, AC-2), while `github_create_pull_request` and
`github_merge_pull_request` stay at repository scope.

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- `_GITHUB_PR_REPO_SCOPE_TAIL` (`scripts/mcp_servers/github/tools_pull_requests.py:66-70`) is spread
  into the read entries (92, 108) as well as the three write entries (124, 157, 173), so the
  affected write entry needs its own tail constant; the other entries keep the repo-scoped tail.
- `github_create_pull_request` (entry at 111) keeps `github_repo`: `CreatePullRequestRequest`
  (`github_models_pull_requests.py:50-64`) has no pull-request number, so the resource identity does
  not exist at call time and `validate_tool_schema_v2()` rejects a scope key that is not in
  `inputSchema.properties` (`resource_scope.py:157-161`). Owner decision 20261126.
- `github_update_pull_request` (entry at 144) declares `pr_number`
  (`github_models_pull_requests.py:76`) — the key name is `pr_number`, not `pull_request_number` (new), so
  `resource_scope_keys` must use `pr_number`.
- `github_merge_pull_request` (entry at 160) keeps `github_repo` per the Plan's independence
  argument (merge mutates the target branch — shared repository state).
- `github_search_pull_requests` uses `_GITHUB_PR_NO_SCOPE_TAIL` (141) and is unchanged.

## Design decisions
- Add a dedicated PR-scoped tail constant next to the existing repo-scoped one, mirroring the
  head/tail split already used in this file and in `tools_issues.py`; do not inline per-entry
  metadata.
- Key kinds: `owner` stays `non_escalating`, `repo` stays `repo`, `pr_number` uses the new
  `pull_request` key kind (procedure 02).

## Alternatives considered
- Change the shared tail for all entries: rejected — it would move the read entries to PR scope and
  `github_create_pull_request` would fail validation.
- Move `github_merge_pull_request` to PR scope: rejected — merge affects shared repository state, so
  it stays at repository scope (AC-1).

## Implementation
### Target file
`scripts/mcp_servers/github/tools_pull_requests.py`

### Procedure
1. Add a `_GithubPrScopeTail` (new) TypedDict next to `_GithubPrRepoScopeTail` (45-51).
2. Add `_GITHUB_PR_SCOPE_TAIL` (new) with `requires_serial: False`,
   `resource_scope_kind: "github_pull_request"`, and
   `resource_scope_keys: {"owner": "non_escalating", "repo": "repo", "pr_number": "pull_request"}`.
3. Spread the new tail into the `github_update_pull_request` entry (157); keep the repo tail for
   `github_create_pull_request` (124), `github_merge_pull_request` (173), and the read entries
   (92, 108).
4. Update the shared-metadata comment block (25-36) to state that the repo tail covers the read
   entries, `github_create_pull_request`, and `github_merge_pull_request`, and that
   `github_update_pull_request` uses the PR-scoped tail.

### Method
Keep the field order (`requires_serial`, `resource_scope_kind`, `resource_scope_keys`) unchanged so
the byte-for-byte shared-field structure the comment block describes still holds within each group.

### Details
- The composed scope string is `github_pull_request:<owner>/<repo>/<pr_number>`, produced by
  `_COMPOSED_KIND_SEPARATORS` (procedure 01); this file only declares the kind and keys.

## Compatibility considerations
- The comment block states "5 of the 6 entries also share an identical tail"; after this change the
  grouping is 4 entries on the repo tail (2 reads + create + merge), 1 on the PR tail (update), and 1
  unscoped (search) — not "5 on the repo tail plus 1 on the PR tail" as this section originally read
  (stale claim, corrected 20261127). The wording was updated to describe the grouping per scope group.
- `tests/shared/test_resource_scope.py` (target row 6) asserts the resolved scope strings.

## Security considerations
- No authorization or correctness change. `pr_number` is a required field, so the update call always
  resolves its scope; no write falls to a looser scope.

## Rollback considerations
- N/A: revert the commit (single-commit change, one file).

## Validation plan
| Check | Command | Expected |
|---|---|---|
| Unit | `uv run pytest tests/shared/test_resource_scope.py tests/mcp_servers/github/test_github_tool_schema.py -v` | `github_update_pull_request` resolves `github_pull_request:<owner>/<repo>/<n>`; create and merge still resolve `github_repo:<owner>/<repo>` |
| Static | `uv run ruff format --check scripts/mcp_servers/github/tools_pull_requests.py`, `uv run ruff check scripts/mcp_servers/github/tools_pull_requests.py`, `uv run mypy --no-namespace-packages scripts/ tests/eventbus tools` | No new findings |
| Architecture | `PYTHONPATH=scripts uv run lint-imports` | `shared-is-leaf` kept |
| Security | `uv run bandit -r scripts/ -c pyproject.toml -ll` | No new findings |

## Completion criteria
- `github_update_pull_request` declares `github_pull_request` with the `pr_number` key; create, merge,
  and the read entries still declare `github_repo` (AC-1, AC-2).
- The comment block describes the actual grouping.

## Out of Scope
- The scope-kind vocabulary and the ancestor rule — procedure 01.
- Test files — procedure 06.
- The issue declarations — procedure 04.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261127-092247 | 20261127-092247 | Verified against current source: comment block 26-36, _GithubPrRepoScopeTail 45-51, repo tail constant 66-70, no-scope tail used at 141, entries create at 111 (tail 124), update at 144 (tail 157), merge at 160 (tail 173), read entries at 92 and 108, pr_number required at github_models_pull_requests.py:76 - all confirmed. File clean at cycle start. Added _GithubPrScopeTail and _GITHUB_PR_SCOPE_TAIL (requires_serial False, github_pull_request, owner/repo/pr_number keys), spread into github_update_pull_request only; create, merge, and the 2 read entries keep the repo tail. Comment block rewritten to the actual grouping (4 repo + 1 PR + 1 unscoped). Field order preserved. Changed file: scripts/mcp_servers/github/tools_pull_requests.py. |
| 2 | Add or update tests per Validation plan | Completed | 20261127-092247 | 20261127-092247 | No tests added in this cycle: the resolved-scope assertions are delivered by procedure 06 (tests/shared/test_resource_scope.py), this procedure's Out of Scope. |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261127-092247 | 20261127-092247 | ruff format --check and ruff check: pass. mypy on the changed file: no issues. bandit on the changed file: no findings. check_module_size.py: OK. lint-imports: 6 kept / 0 broken, shared-is-leaf kept. Targeted tests: 58 passed (tests/shared/test_resource_scope.py + tests/mcp_servers/github/test_github_tool_schema.py + tests/shared/test_tool_metadata.py). Ad-hoc check: github_pull_request:acme/app/7 resolves as one composed string; pr_number is required so no partial identity is possible; ancestor conflict with github_repo:acme/app is True, and a PR scope does not conflict with a branch scope of the same repository (merge stays at repo scope, which is what covers the shared-branch case). Full suite and diff-cover deferred to the end of batch 3. |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20261127-092247 | 20261127-092247 | N/A: documentation is covered by procedure 08 |

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
- **Related target files**: `scripts/mcp_servers/github/tools_pull_requests.py`