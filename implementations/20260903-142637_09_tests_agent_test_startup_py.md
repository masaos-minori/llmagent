# Implementation Procedure: tests/agent/test_startup.py

## Goal

Reorganize `tests/agent/test_startup.py` to align test classes alongside their corresponding new modules/classes, matching the module layout established by the six extracted concerns.

## Scope

- Move test classes/functions in `test_startup.py` to match the new module structure
- Preserve all existing test behavior — no behavioral changes to test assertions
- Align test class names with the new module/class naming convention

## Assumptions

- The following test classes exist in `test_startup.py`:
  - `TestStartupOrchestratorStartServers` → should move to `test_startup_mcp_starter.py`
  - `TestStartupOrchestratorRecoverPendingApprovals` → should move to `test_startup_approval_recovery.py`
  - `TestStartupOrchestratorSetupPrompt` → should move to `test_startup_prompt_setup.py`
  - `TestStartupWorkflowPreflight` → should move to `test_startup_component_init.py`
  - `TestStartupRollback` → stays in `test_startup.py` (orchestrator-level rollback)
  - `TestCheckServicesSeverityClassification` → should move to `test_startup_validation_pipeline.py`
  - `TestStartupVerifyMcpHealth` → should move to `test_startup_mcp_starter.py`
  - `TestStartupMemoryFailures` → should move to `test_startup_prompt_setup.py`

## Design decisions

- **One test file per new module**: Each extracted module gets its own dedicated test file.
- **Preserve helper functions**: `_make_startup`, `_http_subprocess_cfg` stay in `test_startup.py` as shared helpers or move to appropriate files based on usage.
- **No test logic changes**: Only move code, do not modify test assertions or behavior.

## Alternatives considered

- **Keep all tests in one file**: Rejected: defeats the purpose of REQ-015 (align test structure with new module layout).
- **Rename existing test classes**: Rejected: would break test discovery and CI pipelines that reference specific class names.

## Implementation

### Target file

`tests/agent/test_startup.py`

### Procedure

Move test classes to their corresponding new test files.

### Method

File modification (move sections).

### Details

**Phase 4: Test Reorganization** (REQ-015)

1. In `test_startup.py`, remove the following test classes (they will be moved to separate files):
   - `TestStartupOrchestratorStartServers` (lines 76–231)
   - `TestStartupOrchestratorRecoverPendingApprovals` (lines 232–525)
   - `TestStartupOrchestratorSetupPrompt` (lines 526–627)
   - `TestStartupWorkflowPreflight` (lines 628–698)
   - `TestCheckServicesSeverityClassification` (lines 974–1361)
   - `TestStartupVerifyMcpHealth` (lines 1362–1509)
   - `TestStartupMemoryFailures` (lines 1510–end)

2. Keep in `test_startup.py`:
   - Helper functions (`_make_startup`, `_http_subprocess_cfg`)
   - `TestStartupRollback` class (orchestrator-level rollback tests)
   - Any imports needed by remaining tests

3. Create/move test classes to corresponding files:
   - `TestStartupOrchestratorStartServers` → `tests/agent/test_startup_mcp_starter.py`
   - `TestStartupOrchestratorRecoverPendingApprovals` → `tests/agent/test_startup_approval_recovery.py`
   - `TestStartupOrchestratorSetupPrompt` → `tests/agent/test_startup_prompt_setup.py`
   - `TestStartupWorkflowPreflight` → `tests/agent/test_startup_component_init.py`
   - `TestCheckServicesSeverityClassification` → `tests/agent/shared/test_startup_validation_pipeline.py`
   - `TestStartupVerifyMcpHealth` → `tests/agent/test_startup_mcp_starter.py`
   - `TestStartupMemoryFailures` → `tests/agent/test_startup_prompt_setup.py`

## Compatibility considerations

- **Critical**: All test assertions must remain identical. No behavioral changes to test outcomes.
- **Import paths**: After moving test classes, update imports to reference new module locations.
- **Helper function placement**: `_make_startup` may need to be duplicated or imported into moved test files depending on which tests use it.

## Security considerations

- No security-sensitive changes. Test files contain no secrets or credentials.
- `_mask_secrets` is not called in test files.
- `StartupInterrupted` exception handling in tests must remain unchanged.

## Rollback considerations

- If reorganization breaks test discovery, revert to original `test_startup.py` structure.
- Restore all removed test classes to `test_startup.py`.

## Validation plan

| Target | Strategy | Tool / Command | Expected Outcome |
|--------|----------|----------------|------------------|
| `tests/agent/test_startup.py` | Integration — verify remaining tests pass | `uv run pytest tests/agent/test_startup.py` | No new failures |
| `tests/agent/test_startup_mcp_starter.py` | Unit — MCP starter tests | `uv run pytest tests/agent/test_startup_mcp_starter.py` | All pass |
| `tests/agent/test_startup_approval_recovery.py` | Unit — approval recovery tests | `uv run pytest tests/agent/test_startup_approval_recovery.py` | All pass |
| `tests/agent/test_startup_prompt_setup.py` | Unit — prompt setup tests | `uv run pytest tests/agent/test_startup_prompt_setup.py` | All pass |
| `tests/agent/test_startup_component_init.py` | Unit — component init tests | `uv run pytest tests/agent/test_startup_component_init.py` | All pass |
| `tests/agent/shared/test_startup_validation_pipeline.py` | Integration — validation pipeline tests | `uv run pytest tests/agent/shared/test_startup_validation_pipeline.py` | No new failures |

## Completion criteria

- [ ] Test classes moved to corresponding new test files
- [ ] All test assertions preserved verbatim
- [ ] Import paths updated for moved test classes
- [ ] `ruff`, `mypy`, `bandit` clean on all modified/new test files
- [ ] All four test files pass unchanged in outcome
- [ ] No duplicate test coverage across files

## Out of scope

- Changing test assertions or adding new tests
- Modifying `repl_health.py`, `http_lifecycle.py`, or `factory.py` internals
- Performance optimization

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
- **Requirement ID**: REQ-015
- **Source issue**: issues/20260831-155933_refactor_008_startup_separation.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260902-073153_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260903-142637
- **Related target files**: tests/agent/test_startup.py
