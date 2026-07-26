## Goal

Add guard tests for tool argument injection prevention to establish behavioral baseline before refactoring.

## Scope

**In-Scope:**
- Test unexpected field injection — verify tool call with unexpected fields is rejected
- Test schema validation — verify tool call violating schema caught by validation
- Test whitelist filtering — verify only whitelisted fields pass through
- Test malicious argument blocking — verify known malicious argument patterns blocked

**Out-of-Scope:**
- Changing the behavior of tool_runner or tool_executor itself
- Any changes beyond the test

## Assumptions

1. The tool argument handling needs characterization tests due to injection risk
2. Tests should verify current behavior, not expected future behavior
3. Current behavior likely has NO unexpected field rejection or schema validation

## Unknowns

| ID | Unknown Description | Resolution Path | Blocking? (True/False) |
|---|---|---|---|
| UNK-01 | Whether there's an existing test for tool argument edge cases | Search for `tool_runner` in tests | False |

## Affected Areas & Tool Evidence

- **Affected Files:**
  - New file: `tests/test_tool_argument_injection_security.py` — all four gaps

- **Blast Radius:**
  - Low churn — new test file only
  - Very low risk since changes are defensive

- **Deploy Impact:**
  - Existing — no deploy.sh changes needed

## Design

Based on inspection of the tool argument handling logic:
```python
# Key behaviors:
# - Unexpected fields in tool calls may not be rejected
# - Schema validation may not exist currently
# - Whitelist filtering may not enforce strict field lists
# - Malicious argument patterns may not be blocked
```

The tests will verify all four gaps: unexpected field rejection, schema validation, whitelist enforcement, and malicious pattern blocking.

## Implementation

### Target files
- New file: `tests/test_tool_argument_injection_security.py`

### Procedure
1. Phase 1: Verify no existing tool argument edge case tests exist
2. Phase 2: Create tests for each gap
3. Phase 3: Verify with lint and tests

### Method
Create characterization tests using real components where possible.

### Details
1. Create `tests/test_tool_argument_injection_security.py`:
   ```python
   """Characterization tests for tool argument injection prevention."""
   
   def test_unexpected_field_rejected():
       """Tool call with unexpected fields should be rejected."""
       ...
   
   def test_schema_validation_catches_violations():
       """Tool call violating schema should be caught by validation."""
       ...
   
   def test_whitelist_filtering_enforced():
       """Only whitelisted fields should pass through."""
       ...
   
   def test_malicious_argument_patterns_blocked():
       """Known malicious argument patterns should be blocked."""
       ...
   ```

## Compatibility considerations

N/A — test-only change

## Security considerations

These changes improve security by documenting current behavior around tool argument injection risks.

## Rollback considerations

- Simple revert: delete the test file

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `tests/test_tool_argument_injection_security.py` | Characterization tests document current behavior | `uv run pytest -k "tool" -v` | All tests pass |

## Out of scope

- Changing the behavior of tool_runner or tool_executor itself
- Any changes beyond the test

## Traceability

- Workflow phase: plan-to-implementation-procedure
- Source issue: N/A
- Source requirement: requires/20260726-134600_require.md
- Source plan: plans/20260726-173936_plan.md
- Source implementation procedure: N/A
- Generated at: 20260727-034245
- Related target files: scripts/agent/tool_runner.py, scripts/shared/tool_executor.py
