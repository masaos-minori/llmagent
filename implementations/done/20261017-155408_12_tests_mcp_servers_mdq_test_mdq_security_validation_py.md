# Implementation Procedure — `tests/mcp_servers/mdq/test_mdq_security_validation.py`

## Goal

Add command-guard and postcondition regression tests for mdq (`REQ-002`, `REQ-003`).

## Scope

Modify only `tests/mcp_servers/mdq/test_mdq_security_validation.py`. Assert mdq's
path/symlink guards reject disallowed input and postcondition coverage is correct. Depends
on `mdq_security_validation.py` (this plan's row 6).

## Assumptions

- Existing mdq security test file is present; append new tests.
- `mdq_security_validation.py` is verified/extended (row 6).

## Design decisions

- Negative test: disallowed path/symlink/db-path inputs are rejected.
- Regression: allowed inputs still validate.

## Alternatives considered

- Appending to a single shared test module across servers: rejected — each
  server owns its existing test file and fixtures; keeping tests co-located
  preserves coverage locality and reuse.

## Implementation

### Target file

`tests/mcp_servers/mdq/test_mdq_security_validation.py`

### Procedure

1. Test that disallowed path/symlink inputs are rejected by `validate_mdq_security`.
2. Regression test that allowed inputs validate successfully.
3. If a postcondition check was added, assert it.

### Method

- Append test functions; reuse existing config-view helpers.

### Details

- Construct minimal `mdq_cfg` mappings as the existing tests do.

## Compatibility considerations

N/A: test-only change.

## Security considerations

N/A.

## Rollback considerations

Revert the commit to the test file.

## Validation plan

- Run mdq tests; all pass.
- Command: `uv run pytest tests/mcp_servers/mdq/ -q`.

## Completion criteria

Command-guard and postcondition regression tests exist and pass.

## Out of scope

`mdq_security_validation.py` (separate row).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the test changes in test_mdq_security_validation.py | Completed | 20261017-195349 | 20261017-195349 |  |
| 2 | Add or update tests per Validation plan | Completed | 20261017-195349 | 20261017-195349 |  |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261017-195349 | 20261017-195349 |  |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20261017-195349 | 20261017-195349 | N/A |

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
- **Requirement ID**: `REQ-002`, `REQ-003`
- **Source issue**: `issues/20261017-115004_mcp006_implement-missing-guard-layers-for-high-risk-tool-categories.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261017-133731_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261017-155408
- **Related target files**: `tests/mcp_servers/mdq/test_mdq_security_validation.py`