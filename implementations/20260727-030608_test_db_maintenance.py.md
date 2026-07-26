## Goal

Add three boundary value test cases for `purge_old_sessions` to catch off-by-one errors at the `max_sessions` threshold.

## Scope

**In-Scope:**
- Add 3 boundary value tests to `tests/test_db_maintenance.py::TestPurgeOldSessions`:
  1. `max_sessions - 1` sessions → 0 deletions (below boundary)
  2. `max_sessions` sessions → 0 deletions (exact boundary)
  3. `max_sessions + 1` sessions → 1 deletion (above boundary)

**Out-of-Scope:**
- Any other test changes beyond these 3 additions

## Assumptions

1. `_make_session_db()` helper creates a SQLiteHelper with pre-populated session rows
2. Existing tests use values far from the boundary (e.g., 2 sessions vs max_sessions=10)

## Unknowns

| ID | Unknown Description | Resolution Path | Blocking? (True/False) |
|---|---|---|---|
| UNK-01 | Whether `_make_session_db()` supports specifying both session IDs and creation dates for precise ordering | Read `_make_session_db()` implementation | False |

## Affected Areas & Tool Evidence

- **Affected Files:**
  - `tests/test_db_maintenance.py` — add 3 boundary value tests to `TestPurgeOldSessions`

- **Blast Radius:**
  - Very low churn — 3 new test methods only
  - Very low risk since change is purely additive

- **Deploy Impact:**
  - Existing — no deploy.sh changes needed

## Design

Based on inspection of `test_db_maintenance.py`:
```python
# Current: existing tests use values far from boundary (e.g., 2 sessions vs max_sessions=10)

# Proposed additions:
def test_boundary_below_max_sessions(self):
    # Create max_sessions - 1 sessions
    # Call purge_old_sessions(max_sessions=max_sessions)
    # Verify 0 deletions

def test_boundary_at_max_sessions(self):
    # Create max_sessions sessions
    # Call purge_old_sessions(max_sessions=max_sessions)
    # Verify 0 deletions

def test_boundary_above_max_sessions(self):
    # Create max_sessions + 1 sessions
    # Call purge_old_sessions(max_sessions=max_sessions)
    # Verify 1 deletion
```

## Implementation

### Target file
`tests/test_db_maintenance.py`

### Procedure
1. Open `tests/test_db_maintenance.py`
2. Locate `TestPurgeOldSessions` class
3. Add `test_boundary_below_max_sessions` method
4. Add `test_boundary_at_max_sessions` method
5. Add `test_boundary_above_max_sessions` method
6. Save the file

### Method
Add three new test methods with boundary values around the `max_sessions` threshold.

### Details
- Use `_make_session_db()` helper to create session rows with specific counts
- Set `created_at` timestamps appropriately to ensure correct ordering
- Verify exact deletion counts match expected values

## Compatibility considerations

N/A — test additions have no runtime effect

## Security considerations

N/A

## Rollback considerations

- Simple revert: remove the 3 new test methods

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `tests/test_db_maintenance.py` | Boundary value tests pass | `uv run pytest tests/test_db_maintenance.py::TestPurgeOldSessions -v` | All 3 new tests pass |

## Out of scope

- Any other test changes beyond these 3 additions

## Traceability

- Workflow phase: plan-to-implementation-procedure
- Source issue: N/A
- Source requirement: N/A
- Source plan: plans/20260726-163000_plan.md
- Source implementation procedure: N/A
- Generated at: 20260727-030608
- Related target files: scripts/db/maintenance.py, tests/test_db_maintenance.py
