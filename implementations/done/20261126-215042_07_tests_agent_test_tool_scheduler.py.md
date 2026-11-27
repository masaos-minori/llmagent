## Goal

Add conflict-graph tests for the finer GitHub scopes: same-resource writes stay sequential and
independent resources run concurrently (REQ-003, REQ-005, AC-1, AC-2, AC-3).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- `TestResourceScopeGrouping` is at `tests/agent/test_tool_scheduler.py:157` and groups by exact
  scope overlap only today (re-verified 20261126, Step 3a).
- The file is 22949 B. Correction from execution (20261127): the 24576 B module-size gate applies to
  `scripts/` only (`rules/tool-gates.md`, and the pre-commit hook is scoped to `scripts/`), so the test
  file is outside the gate; the added tests took it to 29558 B without a violation. No split was needed.
- Tests use the existing helpers `_tc`, `_spec`, `_ids` (17-40) and construct `ToolSpec` directly, so
  they exercise the predicate through the scheduler without importing the GitHub tool declarations.
- `group.reason` values are `resource_write_write_conflict` and `resource_read_write_conflict`
  (`scripts/agent/tool_scheduler.py:125-137`); the new tests assert the write/write reason.

## Design decisions
- New tests are added inside `TestResourceScopeGrouping` rather than a new class, so the grouping
  tests stay in one place.
- Scope strings in the tests are written as the resolved composed identities
  (`github_repo:org/name`, `github_branch:org/name/main`, `github_issue:org/name/42`,
  `github_pull_request:org/name/7`) so the test states the contract the predicate must honor, not an
  implementation detail.

## Alternatives considered
- End-to-end test through `RuntimeToolRegistry.tool_spec_for_call()`: rejected — that path is covered
  by `tests/shared/test_runtime_tool_registry.py` and would couple this file to the GitHub tool
  declarations (procedures 03-05).

## Implementation
### Target file
`tests/agent/test_tool_scheduler.py`

### Procedure
1. Add `test_same_branch_writes_are_grouped_and_sequential` (new): two writes with
   `github_branch:org/name/main` → one sequential group, reason `resource_write_write_conflict`.
2. Add `test_writes_to_different_branches_of_one_repository_are_concurrent` (new).
3. Add `test_two_comments_on_the_same_issue_are_grouped_and_sequential` (new): two writes with
   `github_issue:org/name/42`. Deviation recorded at execution (20261127): the procedure named this
   test `test_same_issue_comment_and_update_are_grouped_and_sequential`, but `github_update_issue` does
   not exist in the GitHub tool list (`scripts/mcp_servers/github/tools_issues.py` has list, get,
   create, search, add_comment), so the second write on the same issue is another comment call.
4. Add `test_writes_to_different_issues_of_one_repository_are_concurrent` (new).
5. Add `test_pr_update_and_merge_of_the_same_pr_are_grouped_and_sequential` (new): update at
   `github_pull_request:org/name/7`, merge at `github_repo:org/name` → one sequential group via the
   ancestor rule (AC-1, AC-3).
6. Add `test_repository_wide_write_conflicts_with_a_finer_scope` (new): a `github_repo:org/name`
   write and a `github_branch:org/name/main` write form one sequential group (AC-3).
7. Add `test_finer_scopes_of_different_repositories_are_concurrent` (new).
8. Add `test_read_tool_on_a_finer_scope_conflicts_with_a_write_on_the_repository_scope` (new):
   reason `resource_read_write_conflict` (REQ-003).

### Method
Assert `len(plan.batches) == 1`, the group's `sequential` flag, `group.reason`, and `_ids(group)` —
the same assertion shape as the existing tests in this class.

### Details
- The read/write test needs one read spec with a scope and one write spec with the ancestor scope;
  reads alone remain concurrent (existing test at 191).

## Compatibility considerations
- Reference tests `tests/agent/test_tool_scheduler_comprehensive.py` and
  `tests/agent/test_tool_scheduler_serialization.py` execute the same builder and must keep passing
  unchanged; the change adds conflicts only, so existing grouping results are preserved
  monotonically (Plan Risk).

## Security considerations
- N/A: test-only change.

## Rollback considerations
- N/A: revert the commit. Tests land before the implementation per the Plan's Phase 3 ordering.

## Validation plan
| Check | Command | Expected |
|---|---|---|
| Unit | `uv run pytest tests/agent/test_tool_scheduler.py tests/agent/test_tool_scheduler_comprehensive.py tests/agent/test_tool_scheduler_serialization.py -v` | New tests pass after procedure 01; reference tests unchanged |
| Static | `uv run ruff format --check tests/agent/test_tool_scheduler.py`, `uv run ruff check tests/agent/test_tool_scheduler.py`, `uv run mypy --no-namespace-packages scripts/ tests/eventbus tools` | No new findings |
| Coverage | `uv run diff-cover coverage.xml --compare-branch=master` | >= 90% on changed lines |

## Completion criteria
- Same-resource writes are sequential; independent branches, issues, and PRs are concurrent (AC-1,
  AC-2).
- A repository-wide write conflicts with a finer scope of the same repository (AC-3).

## Out of Scope
- `scripts/agent/tool_scheduler.py` — reference row, no modification.
- The predicate implementation — procedure 01.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261127-092247 | 20261127-092247 | Verified against current source: TestResourceScopeGrouping at tests/agent/test_tool_scheduler.py:157, helpers _tc/_spec/_ids at 17-40, reason values resource_write_write_conflict and resource_read_write_conflict in scripts/agent/tool_scheduler.py:125-137 - all confirmed. File clean at cycle start (22949 B). Added the 8 tests inside the existing class. Deviation: the procedure's test 3 named github_update_issue, which does not exist in the tool list, so it is two comment calls on the same issue. Changed file: tests/agent/test_tool_scheduler.py (29705 B; the 24576 B gate covers scripts/ only, so no violation). |
| 2 | Add or update tests per Validation plan | Completed | 20261127-092247 | 20261127-092247 | This cycle is the test cycle. Test-first ordering could not be observed in the batch because procedure 01 landed earlier in seq order; the ancestor-rule tests are satisfied only by the new predicate branch, so they lock AC-3. |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261127-092247 | 20261127-092247 | ruff format --check and ruff check: pass. mypy: tests/agent is outside the mypy scope (scripts/, tests/eventbus, tools) - no new findings. Targeted tests: 70 passed (test_tool_scheduler.py + test_tool_scheduler_comprehensive.py + test_tool_scheduler_serialization.py); the reference tests were not modified and still pass. Full suite and diff-cover deferred to the end of batch 3. |
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
- **Requirement ID**: `REQ-003` (same-resource writes remain sequential, independent resources concurrent)
- **Source issue**: issues/20261119-140520_mcpai013_github-resource-scope-refine.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261126-073010_mcpai013_github-resource-scope-refine.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261126-215042
- **Related target files**: `tests/agent/test_tool_scheduler.py`