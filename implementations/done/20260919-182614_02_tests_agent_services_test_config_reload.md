## Goal

Fix pre-existing test failures related to CONFIG_FIELD_REGISTRY imports in `tests/agent/services/test_config_reload.py`.

## Scope

- **In-Scope**: Fixing 14 pre-existing test failures caused by import path changes and exception type mismatches
- **Out-of-Scope**: Changes to source code under `scripts/agent/services/`; adding new test coverage beyond fixing existing failures

## Assumptions

- The 14 pre-existing test failures are caused by two distinct issues: (a) `_diff_mcp_server_config` moved to `config_outcome_classification.py` but tests still import from `config_reload.py`; (b) validators now raise `ValueError` directly instead of `ConfigReloadValidationError` — both fixable without changing the core refactoring logic

## Design decisions

- Import path correction only — move `_diff_mcp_server_config` import from `config_reload` to `config_outcome_classification`
- Exception type correction only — replace `ConfigReloadValidationError` assertions with `ValueError` where appropriate

## Alternatives considered

- Moving `_diff_mcp_server_config` back to `config_reload.py` — rejected because it would undo the prior module split that motivated the import error
- Wrapping `ValueError` in `ConfigReloadValidationError` at the validator level — rejected because the plan states validators now raise `ValueError` directly and the fix should match current behavior

## Implementation

### Target file

tests/agent/services/test_config_reload.py

### Procedure

Fix 14 pre-existing test failures by correcting import paths and exception type expectations.

### Method

#### Step 1: Verify current failure state

Run `uv run pytest tests/agent/services/test_config_reload.py` to confirm the 14 failing tests. Categorize them into:
- 10 TestDiffMcpServerConfig failures due to ImportError (cannot import `_diff_mcp_server_config`)
- 4 TestApprovalGitopsPushBlocked failures due to ValueError mismatch (expecting `ConfigReloadValidationError` but getting `ValueError`)

#### Step 2: Fix import path for TestDiffMcpServerConfig tests

Replace imports like:
```python
from agent.services.config_reload import _diff_mcp_server_config
```
with:
```python
from agent.services.config_outcome_classification import _diff_mcp_server_config
```

#### Step 3: Fix exception type for TestApprovalGitopsPushBlocked tests

Replace assertion patterns like:
```python
with pytest.raises(ConfigReloadValidationError):
    ...
```
with:
```python
with pytest.raises(ValueError):
    ...
```

### Details

The 10 TestDiffMcpServerConfig failures stem from `_diff_mcp_server_config` being moved to `config_outcome_classification.py` during a prior refactor. The 4 TestApprovalGitopsPushBlocked failures stem from validators raising `ValueError` directly instead of wrapping it in `ConfigReloadValidationError`. Both fixes are mechanical — find-and-replace in the affected test classes.

## Compatibility considerations

- Test-only changes — no impact on production code behavior
- Import path change must match the actual location of `_diff_mcp_server_config` in `config_outcome_classification.py`
- Exception type change must match the actual exception raised by validators

## Security considerations

- No security-relevant behavior changes — test infrastructure only

## Rollback considerations

- If import path correction breaks tests further, revert to original import and investigate root cause
- If exception type correction causes false positives, verify which exceptions validators actually raise before proceeding

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| Full test suite | Regression — all config_reload tests | `uv run pytest tests/agent/services/test_config_reload.py` | All 56 tests pass |
| Type checking | Static analysis | `uv run mypy tests/agent/services/test_config_reload.py` | Clean |
| Linting | Style check | `uv run ruff check tests/agent/services/test_config_reload.py` | Clean |

## Completion criteria

- All 56 tests pass after refactoring (currently 14 fail)
- No behavioral changes — same inputs produce same outputs
- Type checker passes on modified test file
- Linter passes on modified test file

## Out of scope

- Adding new test coverage for extracted methods (covered by the companion procedure for `config_reload.py`)
- Changes to source code under `scripts/agent/services/`
- Deciding whether `ProcessSnapshotProvider` should be wired to a real caller (separate issue)

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
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
- **Requirement ID**: REQ-006
- **Source issue**: issues/done/20260919-112313_refactor_001_refactor_config_reload_service_apply_config_dict.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260919-114636_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260919-182614
- **Related target files**: tests/agent/services/test_config_reload.py
