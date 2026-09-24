## Goal

Verify tests still pass after refactoring `McpToolDiscoveryService.discover_all()`. Update if `_dedupe_and_build()` return signature changes (REQ-010).

## Scope

- Verify all existing tests in `test_mcp_tool_discovery.py` pass without modification
- Update tests only if `_dedupe_and_build()` return signature changes require corresponding updates
- No new tests should be written unless the refactoring introduces new behavior that needs coverage

## Assumptions

- The Plan's claim that "_dedupe_and_build() return signature may change" is correct — this row may need test updates
- All other tests should pass without modification after the refactoring

## Design decisions

N/A — this row requires verification only, not design decisions.

## Alternatives considered

N/A — this row requires verification only.

## Compatibility considerations

- Tests must pass without modification where possible
- Test updates should be minimal and focused on the specific assertion failures caused by signature changes
- No behavioral regression should occur between before/after refactoring

## Security considerations

- No security implications — this is a test validation task only

## Rollback considerations

- If test failures indicate behavioral regression, revert the refactoring and investigate the root cause

## Implementation

### Target file

`tests/agent/services/test_mcp_tool_discovery.py`

### Procedure

Read-only verification — run existing tests and update only if `_dedupe_and_build()` return signature changes require it.

### Method

1. After implementing the refactoring in `mcp_tool_discovery.py`, run the full test suite
2. If any test fails due to `_dedupe_and_build()` return signature change, update the affected assertions
3. If tests pass without modification, no changes needed for this row

### Details

**Current state verification (adversarial verification):**
- This row is classified as "Read-only" in the Plan's Implementation Target Files table
- The Plan notes: "Needs confirmation: test file exists; _dedupe_and_build() return signature change impact unknown"
- The refactoring will change `_dedupe_and_build()` to accept `unavailable_servers` parameter and potentially change its return signature
- Test updates may be needed if the return signature changes

**Test execution steps:**
1. Run `uv run pytest tests/agent/services/test_mcp_tool_discovery.py -v`
2. Review any failing tests for causes related to:
   - `_dedupe_and_build()` return signature change
   - New class instantiation requirements (`McpToolsHttpClient`, `ToolEntryValidator`, `SeverityClassifier`)
   - Changed method signatures in `McpToolDiscoveryService`
3. Update only the minimum necessary assertions to match the new behavior

## Validation plan

| Target File/Module | Testing Strategy (Unit) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| tests/agent/services/test_mcp_tool_discovery.py | Unit: verify each extracted class independently | `uv run pytest tests/agent/services/test_mcp_tool_discovery.py -v` | All tests pass |

## Completion criteria

- [ ] All existing tests in `test_mcp_tool_discovery.py` pass without modification, OR
- [ ] Tests updated minimally to accommodate `_dedupe_and_build()` return signature change
- [ ] No behavioral regression detected

## Out of scope

- Writing new tests for newly extracted classes (covered by the primary row's validation plan)
- Modifying test infrastructure or fixtures
- Adding integration tests for the HTTP client extraction

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Read-only: verify tests still pass | Completed | — | 20260925-065230 | May need updates if _dedupe_and_build() signature changes |
| 2 | Add or update tests per Validation plan | Completed | — | 20260925-065230 |  |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | — | 20260925-065231 |  |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | — | 20260925-065231 | N/A |

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
- **Related target files**: tests/agent/services/test_mcp_tool_discovery.py