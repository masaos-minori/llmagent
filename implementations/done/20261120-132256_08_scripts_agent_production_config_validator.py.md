## Goal

Remove the blanket `allowed_tools=[]` rejection so an empty list is no longer fatal unconditionally; emptiness is now valid in `discovered` mode and owned by the mode-aware typed validators (`REQ-003`).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- The mode-aware typed validators (`config_validators.py`) enforce the mode/list mismatch, including that an empty `allowed_tools` is fatal in `explicit_allowlist` mode (AC-02).
- `ProductionConfigValidator` still validates the other `allowed_tools` shape rules it already owns.

## Design decisions
- Delete the `allowed_tools` visibility block (lines 278-282) that records `allowed_tools=[]` as an error unconditionally.
- Do not add a mode-aware replacement here: the plan assigns that rule to the mode-aware typed validators, and `ProductionConfigValidator` has no reliable mode signal at this point.

## Alternatives considered
- Replacing the blanket check with `if mode == explicit_allowlist and empty: error`: rejected because the plan centralizes the mode-dependent rule in the typed validators and keeps this validator shape-only.

## Implementation
### Target file
`scripts/agent/production_config_validator.py`

### Procedure
Delete the `allowed_tools` visibility block at lines 278-282 (the `config.get("allowed_tools")` empty-list record).

### Method
Remove the four-line block and its comment; leave the surrounding `allowed_root` block untouched.

### Details
- Remove lines 278-282 (`# allowed_tools visibility` through the `_record(...)` call).

## Compatibility considerations
An empty `allowed_tools` is now accepted at production validation in `discovered` mode; in `explicit_allowlist` mode it is rejected by the typed validators at startup/reload.

## Security considerations
Removing the blanket check cannot widen visibility: an empty list in `discovered` mode denies every tool anyway (fail-closed at runtime), and `explicit_allowlist` still rejects it via the typed validators.

## Rollback considerations
N/A: revert the commit.

## Validation plan
`uv run pytest tests/agent/test_production_config_validator.py` confirms the unconditional empty rejection is gone and other shape checks remain.

## Completion criteria
`ProductionConfigValidator` no longer records `allowed_tools=[]` unconditionally; the production-validator test passes.

## Out of Scope
Mode-aware empty enforcement (`config_validators.py`) and runtime denial.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261120-184608 | 20261120-184608 | Deleted the unconditional `allowed_tools=[]` visibility block (was lines 278-282) from `production_config_validator.py`; surrounding `allowed_root` block untouched. ruff+mypy clean. |
| 2 | Add or update tests per Validation plan | Completed | 20261120-184608 | 20261120-184608 | `test_production_config_validator.py`: replaced `test_allowed_tools_empty_produces_error_in_production` (unconditional-reject assertion) with `test_allowed_tools_empty_no_production_error` (asserts NO error recorded). `test_production_security_regression.py::test_strict_configuration_validation_via_real_startup`: dropped the now-absent `allowed_tools=[]` assertion + config entry. `_config_test_defaults.py` comment corrected. |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261120-184608 | 20261120-184608 | ruff format+check clean; mypy clean; 4621 passed / 3 skipped across tests/agent/ + tests/integration/ (no regression from removing the blanket check). |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

### Companion test files
- `tests/agent/test_production_config_validator.py`
  - Procedure: remove/adjust the assertion that `allowed_tools=[]` is rejected unconditionally; keep other shape checks.
  - Validation: `uv run pytest tests/agent/test_production_config_validator.py` passes.

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: `REQ-003`
- **Source issue**: `issues/20261120-114209_agentcfg001_tool-policy-mode.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261120-123941_agentcfg001_tool-policy-mode.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261120-132256
- **Related target files**: `scripts/agent/production_config_validator.py`, `tests/agent/test_production_config_validator.py`
