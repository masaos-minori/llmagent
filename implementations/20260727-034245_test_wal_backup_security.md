## Goal

Add guard tests for WAL file backup path traversal prevention to establish behavioral baseline before refactoring.

## Scope

**In-Scope:**
- Test symlink target validation — verify backup path doesn't follow symlink
- Test path normalization — verify normalized absolute path used
- Test backup directory existence — verify directory creation or graceful failure
- Test race condition prevention — verify unique backup filename generation

**Out-of-Scope:**
- Changing the behavior of repl.py itself
- Any changes beyond the test

## Assumptions

1. The WAL backup needs characterization tests due to path traversal risk
2. Tests should verify current behavior, not expected future behavior
3. Current behavior likely has NO symlink validation or path normalization

## Unknowns

| ID | Unknown Description | Resolution Path | Blocking? (True/False) |
|---|---|---|---|
| UNK-01 | Whether there's an existing test for WAL backup security | Search for `wal` in tests | False |

## Affected Areas & Tool Evidence

- **Affected Files:**
  - New file: `tests/test_wal_backup_security.py` — all four gaps

- **Blast Radius:**
  - Low churn — new test file only
  - Very low risk since changes are defensive

- **Deploy Impact:**
  - Existing — no deploy.sh changes needed

## Design

Based on inspection of the repl.py WAL backup logic:
```python
# Key behaviors:
# - Backup path construction from session_id + timestamp
# - No symlink validation currently exists
# - No path normalization before backup
# - Directory may not exist when creating backup
# - Race conditions possible with concurrent backup operations
```

The tests will verify all four gaps: symlink validation, path normalization, directory existence handling, and unique filename generation.

## Implementation

### Target files
- New file: `tests/test_wal_backup_security.py`

### Procedure
1. Phase 1: Verify no existing WAL backup security tests exist
2. Phase 2: Create tests for each gap
3. Phase 3: Verify with lint and tests

### Method
Create characterization tests using real components where possible.

### Details
1. Create `tests/test_wal_backup_security.py`:
   ```python
   """Characterization tests for WAL backup path traversal prevention."""
   
   def test_symlink_target_not_followed():
       """Backup path should not follow symlinks."""
       ...
   
   def test_path_normalized_to_absolute():
       """Backup path should use normalized absolute path."""
       ...
   
   def test_backup_directory_created_or_fails_gracefully():
       """Directory should be created if missing or fail gracefully."""
       ...
   
   def test_unique_backup_filename_generated():
       """Each backup should have a unique filename."""
       ...
   ```

## Compatibility considerations

N/A — test-only change

## Security considerations

These changes improve security by documenting current behavior around path traversal risks.

## Rollback considerations

- Simple revert: delete the test file

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `tests/test_wal_backup_security.py` | Characterization tests document current behavior | `uv run pytest -k "wal" -v` | All tests pass |

## Out of scope

- Changing the behavior of repl.py itself
- Any changes beyond the test

## Traceability

- Workflow phase: plan-to-implementation-procedure
- Source issue: N/A
- Source requirement: requires/20260726-133944_require.md
- Source plan: plans/20260726-173321_plan.md
- Source implementation procedure: N/A
- Generated at: 20260727-034245
- Related target files: scripts/agent/repl.py
