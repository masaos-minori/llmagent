## Goal

Delete `tests/test_db_consistency_detail.py` which contains 3 skipped test methods referencing deleted DbRagOps functionality no longer present in the codebase.

## Scope

**In-Scope:**
- Delete entire `tests/test_db_consistency_detail.py` file

**Out-of-Scope:**
- Any other test changes beyond this file deletion

## Assumptions

1. DbRagOps functionality has been fully replaced by other mechanisms
2. No other tests depend on this file

## Unknowns

| ID | Unknown Description | Resolution Path | Blocking? (True/False) |
|---|---|---|---|
| UNK-01 | Whether any other tests depend on this file indirectly | Search test files for DbRagOps references | False |

## Affected Areas & Tool Evidence

- **Affected Files:**
  - `tests/test_db_consistency_detail.py` — delete entire file

- **Blast Radius:**
  - Very low churn — one file deletion
  - Very low risk since change is purely test removal

- **Deploy Impact:**
  - Existing — no deploy.sh changes needed

## Design

Based on inspection of `test_db_consistency_detail.py`:
```python
# Entire file content: Delete all 3 skipped test methods
import pytest

@pytest.mark.skip(reason="DbRagOps removed")
def test_db_rag_ops_consistency(): ...

@pytest.mark.skip(reason="DbRagOps removed")
def test_db_rag_ops_schema_match(): ...

@pytest.mark.skip(reason="DbRagOps removed")
def test_db_rag_ops_migration(): ...
```

## Implementation

### Target file
`tests/test_db_consistency_detail.py`

### Procedure
1. Delete `tests/test_db_consistency_detail.py` entirely
2. Verify no other tests reference this file

### Method
Direct file deletion.

### Details
- Delete entire file: `rm tests/test_db_consistency_detail.py`
- Verify no imports or references to this file exist in other test files

## Compatibility considerations

N/A — test deletion has no runtime effect

## Security considerations

N/A

## Rollback considerations

- Simple revert: restore the file from git history

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `tests/test_db_consistency_detail.py` | Verify entire file can be safely removed | `uv run pytest -q` — pass count decreases by 3 | No errors |

## Out of scope

- Any other test changes beyond this file deletion

## Traceability

- Workflow phase: plan-to-implementation-procedure
- Source issue: N/A
- Source requirement: N/A
- Source plan: plans/20260726-162802_plan.md
- Source implementation procedure: N/A
- Generated at: 20260727-030407
- Related target files: tests/test_db_consistency_detail.py
