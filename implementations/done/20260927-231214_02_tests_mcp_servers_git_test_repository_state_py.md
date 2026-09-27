# Implementation Procedure — `test_repository_state.py`

## Goal

Update the `RepositoryState` test suite to reflect the refactor of
`scripts/mcp_servers/git/repository_state.py`: delete tests that exercise the removed
delegation methods and `structured_result`, rewrite guard-integration tests through the
surviving entry points, and add regression tests locking the new pipeline-stage behavior.
Drives Requirements `REQ-002`–`REQ-005` of plan `plans/done/20260927-194329_plan.md`.

## Scope

Only `tests/mcp_servers/git/test_repository_state.py`. The production change lives in a
separate implementation procedure for
`scripts/mcp_servers/git/repository_state.py`.

## Assumptions

- The four delegation methods (`check_dirty_worktree`, `check_detached_head`,
  `validate_protected`, `validate_ref`) and `structured_result` are removed from
  `RepositoryState` (see the sibling production procedure).
- `verify_preconditions` now contains the inlined dirty-worktree and detached-HEAD guards;
  `verify_authorization` still enforces the protected-branch / ref-validity check.
- `audit()` is retained, so audit-record tests remain valid.
- No other test file calls the removed members — confirmed by scanning `tests/`; other git
  test files import `RepositoryState` and use only `snapshot()` and data fields, which are
  retained.

## Design decisions

- Delete tests whose sole purpose was asserting the removed public API surface.
- Rewrite the three `TestGuardIntegration` guard tests to route through the surviving
  entry points (`verify_preconditions`, `verify_authorization`) so their type-shape
  assertions stay meaningful without referencing deleted methods.
- Add a negative-regression suite asserting the removed members are absent, preventing
  accidental reintroduction.

## Alternatives considered

- Deleting the three `TestGuardIntegration` tests wholesale: rejected — they encode
  dirty-worktree / detached-HEAD / protected-branch guard expectations worth keeping, and
  routing them through the surviving entry points preserves that coverage at near-zero cost.

## Implementation

### Target file

`tests/mcp_servers/git/test_repository_state.py`

### Procedure

1. **Delete** these nine tests (they reference removed members):
   - `TestGuardDelegation.test_check_dirty_worktree_delegates_to_state`
   - `TestGuardDelegation.test_check_detached_head_delegates_to_state`
   - `TestGuardDelegation.test_validate_protected_delegates_to_state`
   - `TestGuardDelegation.test_validate_ref_delegates_to_state`
   - `TestGuardDelegation.test_structured_result_contains_state_fields`
   - `TestGuardDelegation.test_legacy_check_dirty_worktree_delegates`
   - `TestGuardDelegation.test_legacy_check_detached_head_delegates`
   - `TestGuardDelegation.test_legacy_validate_protected_delegates`
   - `TestGuardDelegation.test_legacy_validate_ref_delegates`

2. **Keep unchanged**: `test_validate_repo_delegates_to_state` and
   `test_legacy_validate_repo_delegates` (assert `state.path` / `state.ref_valid` only);
   all `TestSnapshotCapture`, `TestVerifyPreconditionsDryRunAndDetachedHead`,
   `TestAuditLogVerification` (uses retained `audit()`), `TestPostconditionChecks`,
   `TestResolveRemoteUrl`, `TestRedactRemoteUrl`, `TestGetRepoLock`,
   `TestHeadIdentityRecheck`, `TestProtectedBranchCheck`, `TestRefValidValidation`,
   `TestStage3Authorization`. Do not touch the top-of-file import block (it imports only
   retained symbols).

3. **Rewrite** these three `TestGuardIntegration` tests to the surviving entry points:
   - `test_dirty_worktree_rejected`: replace the `state.check_dirty_worktree()` call with
     `state.verify_preconditions("checkout")` against the dirty repo; keep the
     `"dirty"/"uncommitted"` substring assertion.
   - `test_detached_head_rejected`: replace the `state.check_detached_head(...)` call with
     `state.verify_preconditions("checkout", allow_detached_head=False)`; keep the
     `isinstance(ok, bool)` / `isinstance(err, str)` assertions.
   - `test_protected_branch_rejected`: replace the `state.validate_protected("main")` call
     with `state.verify_authorization()`; keep the type-shape assertions.

4. **Add** a negative-regression test class `TestRemovedMembersAbsent` asserting the
   removed members no longer exist on the class, so future edits cannot silently restore
   them:

```python
class TestRemovedMembersAbsent:
    """REQ-002: the backward-compat delegation methods and structured_result
    were removed; assert their absence to prevent reintroduction."""

    def test_removed_methods_absent(self, working_repo: str) -> None:
        state = RepositoryState.snapshot(working_repo)
        for name in (
            "check_dirty_worktree",
            "check_detached_head",
            "validate_protected",
            "validate_ref",
            "structured_result",
        ):
            assert not hasattr(state, name), f"{name} should not exist"
```

### Method

Read the target file in full. Apply surgical edits only to the tests named above. Preserve
all kept tests byte-for-byte. After edits, run `ruff format` on the file so any blank-line
gaps left by deletions conform.

### Details

- Behavior contract preserved: the rewritten `test_dirty_worktree_rejected` still asserts
  dirty-worktree rejection; the rewritten guarded tests still assert guard return shapes.
- The inlined `verify_preconditions` is the single entry point for both dirty-worktree and
  detached-HEAD guards (see the sibling production procedure's discrepancy note about why
  these guards moved there). The rewritten tests exercise that entry point directly.

## Compatibility considerations

- No other test file references the removed members (confirmed by scanning `tests/`); only
  this file needs changes.
- `MagicMock(spec=RepositoryState)` in `TestStage3Authorization._make_mock_state` auto-
  provides attributes on access; removing real methods does not affect it because those
  attributes are never accessed there.

## Security considerations

Test-only change. No authorization or validation logic changes; the guards themselves are
unchanged in behavior (only their entry point changed).

## Rollback considerations

Restore the nine deleted tests and revert the three rewrites to their original bodies. All
edits are confined to test methods; no imports, fixtures, or production code touched.

## Validation plan

Run after implementing (executed by the code-implementation phase, not here):

```bash
uv run ruff format tests/mcp_servers/git/test_repository_state.py
uv run ruff check tests/mcp_servers/git/test_repository_state.py
uv run pytest tests/mcp_servers/git/test_repository_state.py -v
```

See `plans/done/20260927-194329_plan.md` acceptance criteria AC-001–AC-003 for the full
post-implementation sequence (full suite, diff-cover ≥ 90%, pre-commit gate).

## Completion criteria

- `ruff format` / `ruff check` pass on the changed test file with no new findings.
- `pytest tests/mcp_servers/git/test_repository_state.py` passes with the nine tests
  deleted, three rewritten, and `TestRemovedMembersAbsent` added.
- Acceptance criteria AC-001–AC-003 in `plans/done/20260927-194329_plan.md` all hold.

## Out of scope

- `scripts/mcp_servers/git/repository_state.py` — separate production procedure.
- Other git test files (they use only retained `snapshot()` / data fields).
- Production validation sequence beyond this file's own ruff/pytest gate (covered by the
  sibling procedure's AC-001–AC-003).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 2026-09-28 | 2026-09-28 | Deleted 9 removed-member tests; rewrote 3 TestGuardIntegration tests via surviving entry points; added negative-regression suite |
| 2 | Add or update tests per Validation plan | Completed | 2026-09-28 | 2026-09-28 | This file IS the test change |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 2026-09-28 | 2026-09-28 | Fixed casing bug in rewritten detached-head assertion; 75/75 green |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 2026-09-28 | 2026-09-28 | None in scope |

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
- **Requirement ID**: `REQ-002` (remove dead delegation methods + update tests), `REQ-005` (regression tests exercising pipeline stages directly)
- **Source issue**: issues/done/20260927-185308_gitref001_refactor-repository_state-pipeline-separation-of-concerns.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/done/20260927-194329_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260927-231214
- **Related target files**: tests/mcp_servers/git/test_repository_state.py
