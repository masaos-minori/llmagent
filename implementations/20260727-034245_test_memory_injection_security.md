## Goal

Add guard tests for memory snippet injection security to establish behavioral baseline before refactoring.

## Scope

**In-Scope:**
- Test sensitive data filtering — verify snippet with sensitive data is filtered out
- Test snippet length enforcement — verify oversized snippet truncated to max length
- Test system message priority — verify system message has correct priority relative to user messages
- Test content truncation impact — verify no critical info lost when summary differs from content[:100]

**Out-of-Scope:**
- Changing the behavior of orchestrator or injection itself
- Any changes beyond the test

## Assumptions

1. The memory injection needs characterization tests due to manipulation risk
2. Tests should verify current behavior, not expected future behavior
3. Current behavior likely has NO sensitive data filtering

## Unknowns

| ID | Unknown Description | Resolution Path | Blocking? (True/False) |
|---|---|---|---|
| UNK-01 | Whether there's an existing test for memory injection edge cases | Search for `injection` in tests | False |

## Affected Areas & Tool Evidence

- **Affected Files:**
  - New file: `tests/test_memory_injection_security.py` — all four gaps

- **Blast Radius:**
  - Low churn — new test file only
  - Very low risk since changes are defensive

- **Deploy Impact:**
  - Existing — no deploy.sh changes needed

## Design

Based on inspection of the memory injection logic:
```python
# Key behaviors:
# - Snippets containing sensitive data should be filtered
# - Oversized snippets should be truncated to max length
# - System messages have specific priority ordering
# - Content truncation may lose critical information
```

The tests will verify all four gaps: sensitive data filtering, length enforcement, message priority, and truncation impact.

## Implementation

### Target files
- New file: `tests/test_memory_injection_security.py`

### Procedure
1. Phase 1: Verify no existing memory injection edge case tests exist
2. Phase 2: Create tests for each gap
3. Phase 3: Verify with lint and tests

### Method
Create characterization tests using real components where possible.

### Details
1. Create `tests/test_memory_injection_security.py`:
   ```python
   """Characterization tests for memory snippet injection security."""
   
   def test_sensitive_data_filtered():
       """Snippet with sensitive data should be filtered out."""
       ...
   
   def test_oversized_snippet_truncated():
       """Oversized snippet should be truncated to max length."""
       ...
   
   def test_system_message_priority_correct():
       """System message should have correct priority relative to user messages."""
       ...
   
   def test_content_truncation_no_critical_info_lost():
       """No critical info should be lost when summary differs from content[:100]."""
       ...
   ```

## Compatibility considerations

N/A — test-only change

## Security considerations

These changes improve security by documenting current behavior around memory injection risks.

## Rollback considerations

- Simple revert: delete the test file

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `tests/test_memory_injection_security.py` | Characterization tests document current behavior | `uv run pytest -k "injection" -v` | All tests pass |

## Out of scope

- Changing the behavior of orchestrator or injection itself
- Any changes beyond the test

## Traceability

- Workflow phase: plan-to-implementation-procedure
- Source issue: N/A
- Source requirement: requires/20260726-134409_require.md
- Source plan: plans/20260726-173745_plan.md
- Source implementation procedure: N/A
- Generated at: 20260727-034245
- Related target files: scripts/agent/orchestrator.py, scripts/agent/memory/injection.py
