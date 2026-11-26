## Goal

Add the tests that lock the new GitHub scope kinds and the repository-versus-finer ancestor rule
(REQ-002, REQ-003, REQ-005, AC-2, AC-3), written before the implementation per the Plan's Phase 1
ordering.

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- Existing coverage is `github_repo` composition (`tests/shared/test_resource_scope.py:86-93`) and
  `filesystem:` ancestry (40-50) only; nothing pins the finer GitHub kinds (re-verified 20261126,
  Step 3a).
- The file is 12846 B, below the 24576 B module-size gate, so added tests stay inside the gate.
- The tests use the existing helpers: `_tool(**overrides)` (22-27) and
  `build_fixture_runtime_tool` (19).
- The closed-set pin for `RESOURCE_KEY_KIND_VALUES` is in `tests/shared/test_tool_metadata.py`
  (procedure 02's companion), not here; this file adds the resolution and conflict tests only.

## Design decisions
- Tests are added to the existing classes rather than a new class, so the file's existing grouping
  (resolution / conflict / validator) stays the organizing structure.
- Each test asserts one behavior so a failure names the requirement directly: resolution shape
  (AC-2), ancestor conflict (AC-3), independent non-conflict (AC-2), unchanged fallback (AC-5).

## Alternatives considered
- Parametrize the three finer kinds in one test: rejected — the ancestor rule needs directional
  cases per kind, and a parametrized single assertion would hide which kind failed.

## Implementation
### Target file
`tests/shared/test_resource_scope.py`

### Procedure
1. In `TestResolveResourceScopes` (30), add `test_github_branch_scope_composes_owner_repo_branch` (new)
   (new): asserts `("github_branch:org/name/main",)` for keys
   `{owner: non_escalating, repo: repo, branch: branch}`.
2. Add `test_github_issue_scope_composes_owner_repo_issue` (new): asserts
   `("github_issue:org/name/42",)` with the `issue` key kind.
3. Add `test_github_pull_request_scope_composes_owner_repo_pr` (new): asserts
   `("github_pull_request:org/name/7",)` with the `pull_request` key kind.
4. In `TestScopesConflict` (156), add `test_github_repo_scope_conflicts_with_finer_github_scopes` (new)
   (new): repository scope conflicts with each of the three finer scopes of the same repository,
   checked in both argument orders (mirrors the filesystem ancestor test at 163).
5. Add `test_github_finer_scopes_of_different_repositories_do_not_conflict` (new).
6. Add `test_github_finer_scopes_of_different_resources_do_not_conflict` (new): two branches, two
   issues, two PRs of the same repository are independent.
7. Add `test_github_repo_scope_does_not_conflict_with_a_different_kind` (new): keeps the existing
   cross-kind rule (160) intact for the new kinds.
8. Keep `test_known_write_tool_with_unresolvable_scope_falls_back_to_global_write` (142) unchanged
   as the AC-5 regression lock, and add
   `test_github_write_tool_with_unresolved_branch_falls_back_to_global_write` (new) so the fallback
   is asserted for a GitHub write, not only for a filesystem write.

### Method
Assert the exact resolved tuple for resolution tests and a boolean for conflict tests; do not import
the tool declaration modules — the tests exercise `resolve_resource_scopes()` and `_scopes_conflict()`
directly through fixture tools.

### Details
- The ancestor rule is identity-prefix based (`<owner>/<repo>` plus `/`), so the tests must use
  identities that are not filesystem paths; this is what distinguishes them from the filesystem
  ancestry tests.

## Compatibility considerations
- `tests/agent/test_tool_scheduler.py` (target row 7) covers the scheduler-level grouping; the
  reference tests listed in the Plan's Predictable fallout section pin no scope-kind set and are not
  affected.

## Security considerations
- N/A: test-only change.

## Rollback considerations
- N/A: revert the commit. Tests land before the implementation, so a revert of the implementation
  leaves failing tests that must be reverted together.

## Validation plan
| Check | Command | Expected |
|---|---|---|
| Unit | `uv run pytest tests/shared/test_resource_scope.py -v` | New tests pass after procedures 01 and 02; they fail before the implementation (test-first ordering) |
| Static | `uv run ruff format --check tests/shared/test_resource_scope.py`, `uv run ruff check tests/shared/test_resource_scope.py`, `uv run mypy --no-namespace-packages scripts/ tests/eventbus tools` | No new findings |
| Coverage | `uv run diff-cover coverage.xml --compare-branch=master` | >= 90% on changed lines |

## Completion criteria
- Resolution tests assert one composed scope string per finer kind (AC-2).
- Conflict tests assert repository-versus-finer conflict in both directions and non-conflict for
  independent resources (AC-2, AC-3).
- The fail-closed fallback tests still pass (AC-5).

## Out of Scope
- The implementation — procedures 01 and 02.
- Scheduler grouping tests — procedure 07.
- The closed key-kind set pin — `tests/shared/test_tool_metadata.py` (procedure 02's companion).

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
- **Requirement ID**: `REQ-002` (ancestor semantics in the conflict predicate)
- **Source issue**: issues/20261119-140520_mcpai013_github-resource-scope-refine.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261126-073010_mcpai013_github-resource-scope-refine.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261126-215042
- **Related target files**: `tests/shared/test_resource_scope.py`
