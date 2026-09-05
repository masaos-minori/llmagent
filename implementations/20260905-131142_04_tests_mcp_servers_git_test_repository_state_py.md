# Implementation Procedure: Add Unit Tests for Fixed Authorization Logic

## Goal

Add unit tests for the fixed `_is_protected_branch()`, `ref_valid` validation, and the new Stage 3 call in `WriteProtectionPipeline.run()` — closing the gap found by this Plan's investigation that no existing test exercises these specific behaviors on the live path.

## Scope

Only changes required for Requirements REQ-001, REQ-002, REQ-004 in `tests/mcp_servers/git/test_repository_state.py`. Specifically: adding unit tests that assert the fixed protected-branch detection, ref validation, and Stage 3 authorization call — separate from REQ-010's HTTP-level regression tests.

## Assumptions

- The existing `RepositoryState.snapshot()` fixture pattern (passing `working_repo`/`bare_repo`) remains valid for constructing test subjects.
- `GitConfig.protected_branches` values (`["main", "master", "release"]`) are the policy to enforce; this Plan does not change what is configured, only makes the configured value take effect.
- `WriteProtectionPipeline.run()` will invoke `verify_authorization()` as Stage 3 before Stage 5 (preconditions), per REQ-001.
- `_is_protected_branch()` will accept `protected_branches: list[str]` parameter (default `[]`), per REQ-002.
- `ref_valid` will reject option-like (leading `-`), malformed, or empty-where-invalid refs, per REQ-004.

## Design decisions

- Use parametrized tests over branch/ref combinations to minimize duplication while covering AC-1, AC-2, AC-5.
- Separate test classes for each requirement (REQ-001, REQ-002, REQ-004) to keep failure messages clear and traceability explicit.
- Use spy/mock on the operation callable inside `WriteProtectionPipeline.run()` to prove Stage 3 rejects before Stage 6 executes — this is the critical invariant for REQ-001.

## Alternatives considered

- Adding a single parametrized test class with all three requirements: rejected because it would produce unreadable failure output when one requirement fails; separate test methods per requirement provide clearer diagnostics and easier traceability mapping.
- Using `pytest.mark.parametrize` across all axes (branch × tool × expectation): rejected because it would create a combinatorial explosion of test cases; separate test methods per scenario provide clearer intent and failure isolation.

## Implementation

### Target file

`tests/mcp_servers/git/test_repository_state.py`

### Procedure

##### Method: Add unit tests for fixed `_is_protected_branch()` (REQ-002)

**REQ-002**: Replace the placeholder module function `_is_protected_branch(repo)` (always `False`) with logic that checks the resolved branch/ref against injected `protected_branches`.

```python
import pytest
from mcp_servers.git.repository_state import _is_protected_branch
```

Tests needed:

1. **`test_is_protected_branch_main_when_main_in_list`** — `_is_protected_branch(main, ["main"])` → expect `True`.
2. **`test_is_protected_branch_main_when_master_in_list`** — `_is_protected_branch(main, ["master"])` → expect `False`.
3. **`test_is_protected_branch_refs_heads_main_normalized`** — `_is_protected_branch("refs/heads/main", ["main"])` → expect `True` (normalization must occur).
4. **`test_is_protected_branch_empty_list_always_false`** — `_is_protected_branch("main", [])` → expect `False` (empty list = no protection).
5. **`test_is_protected_branch_default_param_unchanged_behavior`** — `_is_protected_branch("main")` (no second arg) → expect `False` (default `[]`).

##### Method: Add unit tests for fixed `ref_valid` validation (REQ-004)

**REQ-004**: Replace the hard-coded `ref_valid=True` with real validation: reject option-like (leading `-`), malformed, or empty-where-invalid refs.

```python
import pytest
from mcp_servers.git.repository_state import RepositoryState
```

Tests needed:

1. **`test_ref_valid_rejects_option_like`** — `ref_valid="-f"` → expect `False`.
2. **`test_ref_valid_rejects_malformed`** — `ref_valid="refs/heads/"` (trailing slash = malformed) → expect `False`.
3. **`test_ref_valid_accepts_valid_branch`** — `ref_valid="develop"` → expect `True`.
4. **`test_ref_valid_accepts_valid_fq_ref`** — `ref_valid="refs/heads/main"` → expect `True`.
5. **`test_ref_valid_rejects_empty_for_checkout`** — `ref_valid=""` for checkout → expect `False`.
6. **`test_ref_valid_accepts_empty_for_pull_with_tracking`** — `ref_valid=""` for pull with tracking branch → expect `True` (pull can resolve from tracking).

##### Method: Add unit tests for Stage 3 call in `WriteProtectionPipeline.run()` (REQ-001)

**REQ-001**: Add the missing Stage 3 (`RepositoryState.verify_authorization()`) call to `WriteProtectionPipeline.run()`, before Stage 5.

```python
import pytest
from unittest.mock import MagicMock, patch
from mcp_servers.git.repository_state import RepositoryState, WriteProtectionPipeline
```

Tests needed:

1. **`test_run_invokes_verify_authorization_before_stage_5`** — Spy on `verify_authorization`; assert it was called before any precondition check.
2. **`test_run_rejects_on_failed_authorization`** — Mock `verify_authorization` to return `(False, "denied")`; assert `run()` returns early without executing Stage 6.
3. **`test_run_continues_on_successful_authorization`** — Mock `verify_authorization` to return `(True, "")`; assert Stage 6 executes normally.
4. **`test_run_spy_proves_operation_not_called_when_auth_denied`** — Spy on the operation callable inside `run()`; assert it was never called when authorization fails.

##### Method: Add parametrized test for AC-2 (ref normalization)

**AC-2**: `main` and `refs/heads/main` are evaluated consistently as the same protected branch.

```python
class TestRefNormalizationUnit:
    """Verify main and refs/heads/main evaluate consistently as the same protected branch."""
    
    @pytest.mark.parametrize("branch", ["main", "refs/heads/main"])
    def test_normalized_refs_both_deny_when_main_protected(
        self, branch: str, working_repo: str
    ) -> None:
        state = RepositoryState.snapshot(working_repo, protected_branches=["main"])
        ok, err = state.validate_protected(branch)
        assert ok is False, f"Expected denial for {branch}"
```

### Details

Key additions to the file:

1. **Imports**: Add `from unittest.mock import MagicMock, patch` and `from mcp_servers.git.repository_state import _is_protected_branch`.

2. **New test class `TestProtectedBranchDetection`**:
   ```python
   class TestProtectedBranchDetection:
       """Unit tests for the fixed _is_protected_branch() function."""
       
       # ... test methods as described above
   ```

3. **New test class `TestRefValidation`**:
   ```python
   class TestRefValidation:
       """Unit tests for the fixed ref_valid validation."""
       
       # ... test methods as described above
   ```

4. **New test class `TestStage3Authorization`**:
   ```python
   class TestStage3Authorization:
       """Unit tests for the new Stage 3 call in WriteProtectionPipeline.run()."""
       
       # ... test methods as described above
   ```

5. **New test class `TestRefNormalizationUnit`**:
   ```python
   class TestRefNormalizationUnit:
       """Verify main and refs/heads/main evaluate consistently as the same protected branch."""
       
       @pytest.mark.parametrize("branch", ["main", "refs/heads/main"])
       def test_normalized_refs_both_deny_when_main_protected(
           self, branch: str, working_repo: str
       ) -> None:
           # ... as described above
   ```

6. **Pre-change baseline verification**: Before the fix, confirm:
   - `TestProtectedBranchDetection` tests FAIL (protected branches currently succeed via `_is_protected_branch` returning `False`).
   - `TestRefValidation` tests FAIL (option-like refs currently pass via `ref_valid=True`).
   - `TestStage3Authorization` tests FAIL (Stage 3 currently absent from `run()`).

After implementing the fix, confirm all new tests pass.

## Compatibility considerations

- **No change to existing tests**: This adds new test classes/methods; existing `SnapshotCapture`, `GuardDelegation`, etc. tests continue unchanged.
- **Default parameter preservation**: The new `protected_branches: list[str] = []` parameter to `RepositoryState.snapshot()` preserves every existing direct-`snapshot()` call that does not pass it, per the plan's assumptions.
- **Test isolation**: Each new test class operates independently; no shared mutable state between test methods.

## Security considerations

- **Fail-closed verification**: These tests explicitly verify that protected branches and invalid refs are DENIED — the opposite direction from the existing `SnapshotCapture` tests which verify the snapshot capture itself works. A regression here means protection is silently disabled.
- **Operation callable spy**: The critical invariant for REQ-001 is that the operation callable inside `run()` is NEVER invoked when authorization fails — this proves the fail-closed behavior.

## Rollback considerations

- **Tests-only change**: Adding tests has no production impact if rolled back — the code remains unchanged. However, losing these tests means the coverage gap reopens.
- **Pre-change baseline**: The value of these tests depends on confirming they FAIL before the fix and PASS after. Rolling back the tests loses this evidence.

## Validation plan

| Step | Action | Command | Expected Outcome |
|------|--------|---------|------------------|
| 1 | Run new tests against pre-change code | `uv run pytest tests/mcp_servers/git/test_repository_state.py::TestProtectedBranchDetection -v` | New tests FAIL (protected branches currently succeed via `_is_protected_branch` returning `False`) |
| 2 | Run new tests against post-change code | Same command after fix | All new tests PASS |
| 3 | Run full git-mcp suite | `uv run pytest tests/mcp_servers/git/ -v` | 184+ tests pass, no new failures |
| 4 | Static analysis | `uv run ruff check scripts/mcp_servers/git/`; `uv run mypy scripts/mcp_servers/git/`; `uv run bandit -r scripts/mcp_servers/git/ -c pyproject.toml`; `PYTHONPATH=scripts uv run lint-imports` | All pass with no new findings |

## Completion criteria

- [ ] `TestProtectedBranchDetection` class exists with tests for all 5 scenarios (REQ-002).
- [ ] `TestRefValidation` class exists with tests for all 6 scenarios (REQ-004).
- [ ] `TestStage3Authorization` class exists with tests for all 4 scenarios (REQ-001).
- [ ] `TestRefNormalizationUnit` class exists with parametrized test for `main` vs `refs/heads/main` (AC-2).
- [ ] Each new test fails against pre-change code (protected branches currently succeed via `_is_protected_branch` returning `False`).
- [ ] Each new test passes against post-change code.
- [ ] Full git-mcp suite passes with no new failures.
- [ ] All static analysis tools pass with no new findings.

## Out of scope

- HTTP-level regression tests for `/v1/call_tool` — Row 3 responsibility (REQ-010).
- Fixing `_is_protected_branch()` placeholder implementation — Row 1 responsibility.
- Adding Stage 3 call to `WriteProtectionPipeline.run()` — Row 1 responsibility.
- Replacing `ref_valid=True` — Row 1 responsibility.
- Operation-target resolution — Row 1 responsibility.
- Threading `protected_branches` into `snapshot()` — Row 2 responsibility.
- Documentation updates — deferred per issue's Constraint.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | |
| 3 | Run the validation sequence (rules/toolchain.md) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | |

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
- **Requirement ID**: REQ-001, REQ-002, REQ-004
- **Source issue**: issues/20260902-144907_gitauth_complete_protected_branch_and_ref_authorization.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260904-162951_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260905-131142
- **Related target files**: tests/mcp_servers/git/test_repository_state.py
