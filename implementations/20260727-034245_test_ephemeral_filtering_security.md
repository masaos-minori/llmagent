## Goal

Add guard tests for ephemeral message filtering hardening to establish behavioral baseline before refactoring.

## Scope

**In-Scope:**
- Test fake ephemeral key injection — verify message with fake `_ephemeral` key is filtered out
- Test message structure validation — verify malformed message caught by validation
- Test ephemeral-only-from-trusted-sources — verify rejection from non-command handlers
- Test filtering preserves persistent messages — verify message without ephemeral keys is preserved

**Out-of-Scope:**
- Changing the behavior of orchestrator or cmd_skill itself
- Any changes beyond the test

## Assumptions

1. The ephemeral filtering needs characterization tests due to manipulation risk
2. Tests should verify current behavior, not expected future behavior
3. Current behavior likely has NO message structure validation

## Unknowns

| ID | Unknown Description | Resolution Path | Blocking? (True/False) |
|---|---|---|---|
| UNK-01 | Whether there's an existing test for ephemeral filtering edge cases | Search for `ephemeral` in tests | False |

## Affected Areas & Tool Evidence

- **Affected Files:**
  - New file: `tests/test_ephemeral_filtering_security.py` — all four gaps

- **Blast Radius:**
  - Low churn — new test file only
  - Very low risk since changes are defensive

- **Deploy Impact:**
  - Existing — no deploy.sh changes needed

## Design

Based on inspection of the ephemeral filtering logic:
```python
# Key behaviors:
# - Messages with _ephemeral key should be filtered unless from trusted sources
# - Message structure validation may not exist currently
# - Ephemeral messages should only come from command handlers
# - Persistent messages (without _ephemeral key) should be preserved
```

The tests will verify all four gaps: fake key injection, message validation, trusted source enforcement, and persistent message preservation.

## Implementation

### Target files
- New file: `tests/test_ephemeral_filtering_security.py`

### Procedure
1. Phase 1: Verify no existing ephemeral filtering edge case tests exist
2. Phase 2: Create tests for each gap
3. Phase 3: Verify with lint and tests

### Method
Create characterization tests using real components where possible.

### Details
1. Create `tests/test_ephemeral_filtering_security.py`:
   ```python
   """Characterization tests for ephemeral message filtering hardening."""
   
   def test_fake_ephemeral_key_injection_filtered():
       """Message with fake _ephemeral key should be filtered out."""
       ...
   
   def test_malformed_message_caught_by_validation():
       """Malformed messages should be caught by validation."""
       ...
   
   def test_ephemeral_only_from_trusted_sources():
       """Ephemeral messages from non-command handlers should be rejected."""
       ...
   
   def test_persistent_messages_preserved():
       """Messages without ephemeral keys should be preserved."""
       ...
   ```

## Compatibility considerations

N/A — test-only change

## Security considerations

These changes improve security by documenting current behavior around ephemeral message filtering.

## Rollback considerations

- Simple revert: delete the test file

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `tests/test_ephemeral_filtering_security.py` | Characterization tests document current behavior | `uv run pytest -k "ephemeral" -v` | All tests pass |

## Out of scope

- Changing the behavior of orchestrator or cmd_skill itself
- Any changes beyond the test

## Traceability

- Workflow phase: plan-to-implementation-procedure
- Source issue: N/A
- Source requirement: requires/20260726-134315_require.md
- Source plan: plans/20260726-173650_plan.md
- Source implementation procedure: N/A
- Generated at: 20260727-034245
- Related target files: scripts/agent/orchestrator.py, scripts/agent/commands/cmd_skill.py
