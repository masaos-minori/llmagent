# Implementation Procedure: Update test fixtures for unified required field

## Goal

Update `tests/agent/services/test_mcp_tool_discovery.py` test fixtures to use the unified `required` field instead of `required_in_production`/`required_in_local`, and remove `failure_policy` parameter usage after FAIL_FAST-only simplification.

## Scope

- Replace `required_in_local=False` and `required_in_local=True` with `required=False` and `required=True` in test fixture calls
- Remove `failure_policy=FailurePolicy.FAIL_FAST` and `failure_policy=FailurePolicy.DEGRADED` parameters from test fixture calls
- Update any assertions that reference `failure_policy` values

## Assumptions

- After Plan 2 Step 1 completes, `McpServerConfig` will have a single `required` field replacing both `required_in_production` and `required_in_local`
- After Plan 2 Step 1 completes, `FailurePolicy` will contain only `FAIL_FAST`, making other enum values invalid
- Test fixtures currently use `required_in_local=False` and `required_in_local=True` with various `failure_policy` values (confirmed by grep)

## Design decisions

- Replace `required_in_local` with `required` directly — no migration layer needed since tests are internal
- Remove `failure_policy` parameter entirely from test fixtures since only FAIL_FAST remains valid
- Tests that previously used `failure_policy=FailurePolicy.DEGRADED` should now either assert FATAL status (since required servers always produce FATAL) or be removed if they tested degraded behavior that no longer applies

## Alternatives considered

- Could keep `failure_policy` parameter but mark it deprecated — unnecessary since the enum itself prevents invalid values at construction time
- Could add migration logic to map old `failure_policy` values to FAIL_FAST — unnecessary since tests should reflect the new model

## Implementation

### Target file

`tests/agent/services/test_mcp_tool_discovery.py`

### Procedure

**Phase 1: Replace dual required fields with unified field**

1. On lines 737, 758, replace `required_in_local=False` with `required=False`
2. On lines 779, 800, replace `required_in_local=True` with `required=True`

**Phase 2: Remove failure_policy parameter usage**

3. On lines 738, 759, 780, 801, remove `failure_policy=FailurePolicy.FAIL_FAST` and `failure_policy=FailurePolicy.DEGRADED` parameters from McpServerConfig constructor calls
4. Update any assertions that check `failure_policy` values — since only FAIL_FAST remains, assertions should verify FATAL status for required unreachable servers

**Phase 3: Update test logic**

5. Review test methods that use `failure_policy=FailurePolicy.DEGRADED` — these tests may need to be updated or removed since DEGRADED is no longer a valid policy value
6. Verify that tests using `failure_policy=FailurePolicy.FAIL_FAST` still work correctly without the explicit parameter (FAIL_FAST becomes implicit default)

### Method

Test fixture update: replace deprecated field names, remove obsolete enum comparisons, adjust test expectations.

### Details

- Use exact string matching for field removal: `required_in_local` → `required`
- Preserve test method structure and coverage intent — only modify the fixture construction and assertion logic
- Do not alter the substance of Decision, Rationale, Invariants, or Verification sections beyond section placement changes
- Record per-file outcome explicitly (nothing lost / relocated / not applicable)

## Compatibility considerations

- Breaking change for any external consumer that depends on `required_in_production` or `required_in_local` attribute names in test fixtures
- Tests that previously verified DEGRADED behavior will fail since DEGRADED is no longer valid — these tests should be updated or removed
- Default `required=True` maintains backward compatibility with current default behavior where both fields defaulted to True

## Security considerations

- None applicable; this is a configuration model alignment change, not a security fix

## Rollback considerations

- All changes are reversible via git revert if issues arise
- No data loss risk since no content is deleted without careful review

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `tests/agent/services/test_mcp_tool_discovery.py` | Unit: verify test fixtures compile with `required` field and no `failure_policy` parameter | `uv run pytest tests/agent/services/test_mcp_tool_discovery.py::TestMcpServerConfig` | All assertions pass |

## Completion criteria

- No references to `required_in_production` or `required_in_local` remain in this file
- No references to `FailurePolicy.DISABLE_TOOL` or `FailurePolicy.DEGRADED` remain in this file
- All test fixtures use the unified `required` field
- All test assertions for unreachable server handling verify FATAL status for required servers

## Out of scope

- Modifying `McpServerConfig` dataclass fields (covered by separate procedure document)
- Modifying `mcp_tool_discovery.py` caller (covered by separate procedure document)
- Modifying `startup.py` caller (covered by separate procedure document)
- Updating ADR-004 Known Issue entry (covered by separate procedure document)

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Phase 1: Replace dual required fields with unified field | Pending | — | — | |
| 2 | Phase 2: Remove failure_policy parameter usage | Pending | — | — | |
| 3 | Phase 3: Update test logic | Pending | — | — | |

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
- **Requirement ID**: REQ-005
- **Source issue**: issues/20260831-173019_adr004_01_mcp_config_failure_model_alignment.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260831-230938_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260831-230938
- **Related target files**: tests/agent/services/test_mcp_tool_discovery.py
