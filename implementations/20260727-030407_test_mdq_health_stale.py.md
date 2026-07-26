## Goal

Remove 3 skipped test methods from `tests/test_mdq_health_stale.py` that reference deleted classes and patterns no longer present in the codebase.

## Scope

**In-Scope:**
- Delete 3 skipped test methods from `tests/test_mdq_health_stale.py` (lines 101-123)

**Out-of-Scope:**
- Any other test changes beyond these 3 deletions

## Assumptions

1. Replacement tests for mdq health stale coverage exist as `TestStaleDocumentCountNewSchema` class
2. The deleted tests are no longer relevant to the current codebase

## Unknowns

| ID | Unknown Description | Resolution Path | Blocking? (True/False) |
|---|---|---|---|
| UNK-01 | Whether any other tests depend on the deleted tests indirectly | Search test files for DbRagOps references | False |

## Affected Areas & Tool Evidence

- **Affected Files:**
  - `tests/test_mdq_health_stale.py:101-123` — delete 3 skipped test methods

- **Blast Radius:**
  - Very low churn — 3 test method deletions
  - Very low risk since change is purely test removal

- **Deploy Impact:**
  - Existing — no deploy.sh changes needed

## Design

Based on inspection of `test_mdq_health_stale.py`:
```python
# Lines 101-123: Delete these 3 skipped tests
@pytest.mark.skip(reason="...")
def test_something_old_1(): ...

@pytest.mark.skip(reason="...")
def test_something_old_2(): ...

@pytest.mark.skip(reason="...")
def test_something_old_3(): ...
```

## Implementation

### Target file
`tests/test_mdq_health_stale.py`

### Procedure
1. Open `tests/test_mdq_health_stale.py`
2. Locate lines 101-123 containing the 3 skipped test methods
3. Delete these 3 test methods entirely
4. Save the file

### Method
Direct deletion of the 3 skipped test methods.

### Details
- Line 101-123: Delete all 3 skipped test methods
- Verify `TestStaleDocumentCountNewSchema` class exists and covers equivalent scenarios before deletion

## Compatibility considerations

N/A — test deletion has no runtime effect

## Security considerations

N/A

## Rollback considerations

- Simple revert: restore the 3 skipped test methods from git history

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `tests/test_mdq_health_stale.py` | Verify remaining tests still pass | `uv run pytest tests/test_mdq_health_stale.py -v` | Tests pass |

## Out of scope

- Any other test changes beyond these 3 deletions

## Traceability

- Workflow phase: plan-to-implementation-procedure
- Source issue: N/A
- Source requirement: N/A
- Source plan: plans/20260726-162802_plan.md
- Source implementation procedure: N/A
- Generated at: 20260727-030407
- Related target files: tests/test_mdq_health_stale.py
