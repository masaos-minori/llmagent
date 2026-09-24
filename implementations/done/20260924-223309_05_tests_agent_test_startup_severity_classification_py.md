## Goal

Verify severity classification tests still pass after refactoring `McpToolDiscoveryService.discover_all()` (REQ-010).

## Scope

- Verify all existing tests in `test_startup_severity_classification.py` pass without modification
- Confirm severity classification logic remains unchanged after consolidation into `SeverityClassifier`
- No code changes expected for this row

## Assumptions

- The Plan's claim that "no change expected" for this row is accurate
- Severity classification tests validate the unified severity scheme and should remain stable after the refactoring

## Design decisions

N/A — this row requires verification only, not design decisions.

## Alternatives considered

N/A — this row requires verification only.

## Compatibility considerations

- Tests must pass without modification
- No behavioral regression should occur between before/after refactoring
- The "always FATAL for duplicates" exception must be preserved

## Security considerations

- No security implications — this is a test validation task only

## Rollback considerations

- If test failures indicate behavioral regression in severity classification, revert the refactoring and investigate the root cause

## Implementation

### Target file

`tests/agent/test_startup_severity_classification.py`

### Procedure

Read-only verification — run existing tests and confirm they pass.

### Method

1. After implementing the refactoring in `mcp_tool_discovery.py`, run the severity classification tests
2. If any test fails, investigate whether the failure is due to behavioral regression in severity escalation
3. If tests pass without modification, no changes needed for this row

### Details

**Current state verification (adversarial verification):**
- This row is classified as "Read-only" in the Plan's Implementation Target Files table
- The Plan notes: "Needs confirmation: test file exists; behavioral impact unknown"
- Severity classification tests validate the unified severity scheme and should remain stable after the refactoring
- The "always FATAL for duplicates" exception must be preserved through the refactoring

**Test execution steps:**
1. Run `uv run pytest tests/agent/test_startup_severity_classification.py -v`
2. Review any failing tests for causes related to severity classification regression
3. No modifications expected unless behavioral regression is detected

## Validation plan

| Target File/Module | Testing Strategy (Regression) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| tests/agent/test_startup_severity_classification.py | Regression: verify severity classification unchanged | `uv run pytest tests/agent/test_startup_severity_classification.py -v` | All tests pass |

## Completion criteria

- [ ] All existing tests in `test_startup_severity_classification.py` pass without modification
- [ ] No behavioral regression in severity classification detected
- [ ] "Always FATAL for duplicates" exception preserved

## Out of scope

- Writing new tests for newly extracted classes
- Modifying test infrastructure or fixtures
- Adding integration tests for the HTTP client extraction

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Read-only: verify tests still pass | Completed | — | 20260925-065316 |  |
| 2 | Add or update tests per Validation plan | Completed | — | 20260925-065316 | N/A |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | — | 20260925-065317 |  |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | — | 20260925-065317 | N/A |

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
- **Requirement ID**: REQ-010
- **Source issue**: issues/20260924-105819_refactor_001_refactor-mcp-tool-discovery-service.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260924-181019_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260924-223309
- **Related target files**: tests/agent/test_startup_severity_classification.py