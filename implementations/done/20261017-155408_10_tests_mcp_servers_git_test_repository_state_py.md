# Implementation Procedure — `tests/mcp_servers/git/test_repository_state.py`

## Goal

Add postcondition verification and TOCTOU re-check tests for git (`REQ-003`).

## Scope

Modify only `tests/mcp_servers/git/test_repository_state.py`. Assert the filled
postcondition fires on partial/unintended results and that the TOCTOU re-check is real
(not a no-op). Depends on `repository_state.py` (this plan's row 4).

## Assumptions

- Existing repository_state test file is present; append new tests.
- `repository_state.py` fills checkout + TOCTOU gaps (row 4).

## Design decisions

- Negative test: postcondition fails closed on drift.
- Regression: dry-run / detached-head / pull-conflict paths remain correct (plan Risk).

## Alternatives considered

- Appending to a single shared test module across servers: rejected — each
  server owns its existing test file and fixtures; keeping tests co-located
  preserves coverage locality and reuse.

## Implementation

### Target file

`tests/mcp_servers/git/test_repository_state.py`

### Procedure

1. Test that `verify_postcondition` fails closed on a genuine post-condition drift.
2. Test that the TOCTOU re-check now performs a real re-read (not a no-op) and rejects
   on drift.
3. Regression: existing dry-run and detached-head paths still pass.

### Method

- Append test functions; reuse existing repo fixtures where available.

### Details

- Use a real temporary repo fixture so the re-check has authoritative state.

## Compatibility considerations

N/A: test-only change.

## Security considerations

N/A.

## Rollback considerations

Revert the commit to the test file.

## Validation plan

- Run git tests; all pass.
- Command: `uv run pytest tests/mcp_servers/git/ -q`.

## Completion criteria

Postcondition-fails-closed and real-re-check tests exist and pass; existing paths remain
correct.

## Out of scope

`repository_state.py` (separate row).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the test changes in test_repository_state.py | Completed | 20261017-185039 | 20261017-185039 | added TestPostconditionFailClosed(verify_postcondition fails closed on git_pull unmerged blobs via MagicMock _repo swap) + TestTOCTOURecheck(4: _fresh_is_detached reads live repo not cached; no-drift op succeeds; non-checkout head drift rejects at Stage 5b after op executed; git_checkout exempt from re-check); corrected stale docstring in test_head_drift_not_rejected_with_single_snapshot(old no-op claim inaccurate post-row4); ruff format/check+mypy clean(except pre-existing line-89 frozen-dataclass error); full git suite 345 pass(+6 new)/43 fail(all pre-existing test_git_security_compliance, identical on clean tree); no regression |
| 2 | Add or update tests per Validation plan | Completed | 20261017-185039 | 20261017-185039 | added TestPostconditionFailClosed(verify_postcondition fails closed on git_pull unmerged blobs via MagicMock _repo swap) + TestTOCTOURecheck(4: _fresh_is_detached reads live repo not cached; no-drift op succeeds; non-checkout head drift rejects at Stage 5b after op executed; git_checkout exempt from re-check); corrected stale docstring in test_head_drift_not_rejected_with_single_snapshot(old no-op claim inaccurate post-row4); ruff format/check+mypy clean(except pre-existing line-89 frozen-dataclass error); full git suite 345 pass(+6 new)/43 fail(all pre-existing test_git_security_compliance, identical on clean tree); no regression |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261017-185039 | 20261017-185039 | added TestPostconditionFailClosed(verify_postcondition fails closed on git_pull unmerged blobs via MagicMock _repo swap) + TestTOCTOURecheck(4: _fresh_is_detached reads live repo not cached; no-drift op succeeds; non-checkout head drift rejects at Stage 5b after op executed; git_checkout exempt from re-check); corrected stale docstring in test_head_drift_not_rejected_with_single_snapshot(old no-op claim inaccurate post-row4); ruff format/check+mypy clean(except pre-existing line-89 frozen-dataclass error); full git suite 345 pass(+6 new)/43 fail(all pre-existing test_git_security_compliance, identical on clean tree); no regression |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20261017-185039 | 20261017-185039 | N/A added TestPostconditionFailClosed(verify_postcondition fails closed on git_pull unmerged blobs via MagicMock _repo swap) + TestTOCTOURecheck(4: _fresh_is_detached reads live repo not cached; no-drift op succeeds; non-checkout head drift rejects at Stage 5b after op executed; git_checkout exempt from re-check); corrected stale docstring in test_head_drift_not_rejected_with_single_snapshot(old no-op claim inaccurate post-row4); ruff format/check+mypy clean(except pre-existing line-89 frozen-dataclass error); full git suite 345 pass(+6 new)/43 fail(all pre-existing test_git_security_compliance, identical on clean tree); no regression |

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
- **Requirement ID**: `REQ-003`
- **Source issue**: `issues/20261017-115004_mcp006_implement-missing-guard-layers-for-high-risk-tool-categories.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261017-133731_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261017-155408
- **Related target files**: `tests/mcp_servers/git/test_repository_state.py`