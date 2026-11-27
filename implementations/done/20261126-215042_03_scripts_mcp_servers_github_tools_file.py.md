## Goal

Declare branch scope for the three GitHub file write tools so writes to different branches no
longer serialize against each other (REQ-001, AC-2: independent resources run concurrently).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- The shared tail `_GITHUB_FILE_TOOL_METADATA_TAIL` (`scripts/mcp_servers/github/tools_file.py:56-60`)
  is spread into all 4 `TOOL_LIST` entries, including the read tool `github_get_file_contents`
  (entry at 63, tail used at 78). The read tool must keep `github_repo`, so the write entries need
  a separate tail constant; the Plan's row text assumed the tail could be changed in place.
- Write entries: `github_create_or_update_file` (81), `github_push_files` (97),
  `github_delete_file` (114). The Plan named the third tool `github_delete_repo_file` (new); the
  `TOOL_LIST` name is `github_delete_file` (Plan corrected 20261126).
- `branch` is a declared property of all three request models
  (`github_models_file.py:65`, `115`, `149`), so `resource_scope_keys` passes the
  `inputSchema.properties` check (`resource_scope.py:157-161`).
- `branch` has a default for `CreateOrUpdateFileRequest` and `DeleteRepoFileRequest`, and that default
  is the empty-string sentinel (`github_models_file.py:65-68`, `149-152`), so an omitted `branch`
  contributes no part to the composed identity. Correction from execution (20261126): such a call does
  NOT fall back to `global:write` — `resolve_resource_scopes()` returns the partial composed identity
  `github_branch:<owner>/<repo>` because `owner` and `repo` did resolve (`resource_scope.py:104-109`;
  the fallback applies only when no key resolves at all). The Plan's line 29 wording ("a file-write
  call that omits `branch` therefore lands on `global:write`") is stale. Consequence, unresolved:
  `github_branch:<owner>/<repo>` conflicts with neither `github_repo:<owner>/<repo>` (the ancestor rule
  requires the descendant identity to begin with the ancestor identity plus `/`) nor
  `github_branch:<owner>/<repo>/<name>`, so a default-branch write is not serialized against
  repository-wide scopes or against an explicit write to the same default branch. Decision (user,
  20261127): fail closed — `resolve_resource_scopes()` returns `_FALLBACK_WRITE_SCOPE` for a write
  tool whose composed GitHub identity is missing a declared key (implemented in procedure 01's target
  file, `resource_scope.py:104-116`); this procedure itself declares the kind and keys only and was
  not changed by the decision. No test pins a scope result for these tools.
- `tests/mcp_servers/github/test_github_tool_schema.py` was created by the mcpai010 procedure
  `implementations/20261126-205430_03_tests_mcp_servers_github_test_github_tool_schema.py.md` and now
  exists (confirmed 20261126). It pins the published `inputSchema` only, not the metadata tails, so it
  is a verification dependency, not a companion, and is not modified here.

## Design decisions
- Add a branch-scoped tail constant next to the existing repo-scoped one, mirroring the
  head/tail split convention already used in this file and in `tools_issues.py` /
  `tools_pull_requests.py`; do not inline per-entry metadata.
- Key kinds: `owner` stays `non_escalating`, `repo` stays `repo`, `branch` uses the existing
  `branch` key kind — no vocabulary change is needed for this row.

## Alternatives considered
- Change the shared tail for all 4 entries: rejected — it would move the read tool to branch
  scope, and reads are out of scope for this Plan (they do not enter the conflict graph).

## Implementation
### Target file
`scripts/mcp_servers/github/tools_file.py`

### Procedure
1. Add a `_GithubFileBranchScopeTail` (new) TypedDict next to `_GithubFileMetadataTail` (43-49).
2. Add `_GITHUB_FILE_BRANCH_SCOPE_TAIL` (new) with `requires_serial: False`,
   `resource_scope_kind: "github_branch"`, and
   `resource_scope_keys: {"owner": "non_escalating", "repo": "repo", "branch": "branch"}`.
3. Spread the new tail into the three write entries (81, 97, 114); leave the read entry (78) on the
   existing repo tail.
4. Update the shared-metadata comment block (24-34) to state that the tail is shared by the write
   entries only and that the read entry keeps the repo-scoped tail.

### Method
Keep key order unchanged (`requires_serial`, `resource_scope_kind`, `resource_scope_keys`) so the
byte-for-byte shared-field structure the comment block describes still holds within each group.

### Details
- The composed scope string is `github_branch:<owner>/<repo>/<branch>`, produced by
  `_COMPOSED_KIND_SEPARATORS` (procedure 01); this file only declares the kind and keys.

## Compatibility considerations
- The comment block at 24-34 is the record of which fields are byte-for-byte identical across
  entries; it must match the new grouping or the schema-consistency test that pins the tails
  (created by the mcpai010 procedure) will disagree with the file.
- `tests/shared/test_resource_scope.py` (target row 6) is the test that asserts the resolved scope
  strings for these tools.

## Security considerations
- No authorization or correctness change. A write whose keys do not resolve keeps the fail-closed
  `global:write` scope, so no write becomes freely parallelizable.

## Rollback considerations
- N/A: revert the commit (single-commit change, one file).

## Validation plan
| Check | Command | Expected |
|---|---|---|
| Unit | `uv run pytest tests/shared/test_resource_scope.py tests/mcp_servers/github/test_github_tool_schema.py -v` | Write tools resolve to `github_branch:<owner>/<repo>/<branch>`; the read tool still resolves `github_repo:<owner>/<repo>` |
| Static | `uv run ruff format --check scripts/mcp_servers/github/tools_file.py`, `uv run ruff check scripts/mcp_servers/github/tools_file.py`, `uv run mypy --no-namespace-packages scripts/ tests/eventbus tools` | No new findings |
| Architecture | `PYTHONPATH=scripts uv run lint-imports` | `shared-is-leaf` kept |
| Security | `uv run bandit -r scripts/ -c pyproject.toml -ll` | No new findings |

## Completion criteria
- The three write entries declare `github_branch` with the `branch` key; the read entry still
  declares `github_repo` (AC-2).
- The comment block describes the actual grouping.

## Out of Scope
- The scope-kind vocabulary and the ancestor rule — procedure 01.
- Test files — procedure 06; the mcpai010 schema test is a verification dependency only.
- The issue and pull-request declarations — procedures 04, 05.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261127-092247 | 20261127-092247 | Verified against current source: comment block 24-34, _GithubFileMetadataTail 43-49, repo tail constant 56-60, read entry 63 (tail used at 78), write entries 81/97/114, branch properties at github_models_file.py:65/115/149 - all confirmed. File clean at cycle start. Added _GithubFileBranchScopeTail and _GITHUB_FILE_BRANCH_SCOPE_TAIL (requires_serial False, github_branch, owner/repo/branch keys), spread into the three write entries, read entry left on the repo tail, comment block rewritten to state the grouping per group rather than across all 4. Key order preserved. Changed file: scripts/mcp_servers/github/tools_file.py. Finding: the fail-closed assumption is stale - an omitted branch yields the partial identity github_branch:<owner>/<repo>, not global:write; reported to the user, no code change. |
| 2 | Add or update tests per Validation plan | Completed | 20261127-092247 | 20261127-092247 | No tests added in this cycle: the resolved-scope assertions are delivered by procedure 06 (tests/shared/test_resource_scope.py), this procedure's Out of Scope. tests/mcp_servers/github/test_github_tool_schema.py is a verification dependency and was not modified. |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261127-092247 | 20261127-092247 | ruff format --check and ruff check: pass. mypy on the changed file: no issues. bandit on the changed file: no findings. check_module_size.py: OK, no new violations. lint-imports: 6 kept / 0 broken, shared-is-leaf kept. Targeted tests: 50 passed (tests/shared/test_resource_scope.py + tests/mcp_servers/github/test_github_tool_schema.py). Ad-hoc check: the three write entries now declare github_branch and resolve to github_branch:acme/app/main when branch is supplied. Full suite and diff-cover deferred to the end of batch 3. |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20261127-092247 | 20261127-092247 | N/A: documentation is covered by procedure 08 |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| 3 | End-of-batch full suite reports 2 new failures caused by declaring a `branch` key kind on the GitHub file write tools: `tests/agent/test_tool_approval_risk.py::TestClassifyRisk::test_github_tools_have_no_declared_branch_keys` (pins REQ-008 as "no shipped github tool declares a branch-kind key") and `tests/agent/test_tool_approval_preflight.py::TestCheckApprovalDryRun::test_github_tool_triggers_dry_run` (HIGH risk now requires the full word "yes" because `main` is in `approval_high_risk_branches`, so the patched "y" answer no longer approves). Both files are outside the Plan's frozen Implementation Target Files table, so they were not modified. Reported to the user for a decision. Resolution (owner decision 20261127, plan amendment class `scope`): both tests updated to the new behavior — the risk test now pins the declared branch-key set plus HIGH escalation on `main` and non-escalation on `feature/x`; the preflight test uses a non-high-risk branch so the tier base stays `medium`. Plan rows added for both files (amendment 2026-11-27). | Resolved | 20261127 |

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
- **Related target files**: `scripts/mcp_servers/github/tools_file.py`