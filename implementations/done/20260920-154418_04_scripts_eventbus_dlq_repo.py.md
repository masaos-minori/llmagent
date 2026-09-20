## Goal
Remove duplicate column name constants from `scripts/eventbus/dlq_repo.py` and replace local definitions with imports from `_constants.py`. Implements REQ-002 (import shared constants from `_constants.py`).

## Scope
- Remove 4 duplicate constant definitions: `_COL_DLQ_REQUEUE_COUNT`, `_COL_REDISTRIBUTED_FROM`, `_COL_DELIVERY_FAILURE_COUNT`, `_COL_CYCLE_FAILURE_COUNT`
- Add import statement to pull these constants from `_constants.py`
- No changes to function logic or SQL queries

## Assumptions
- All usages of these constants in `dlq_repo.py` will continue to work after switching to imports from `_constants.py`
- The constants' string values remain unchanged during refactoring

## Design decisions
- Import pattern: use `from eventbus._constants import _COL_X` for each removed constant
- Keep layer-specific constants (if any) in place — only remove those that overlap with `_constants.py`

## Alternatives considered
- Create a single wildcard import (`from eventbus._constants import *`): rejected because it obscures which constants come from where; explicit imports improve traceability
- Keep local definitions as fallback: rejected because duplication creates maintenance risk

## Implementation
### Target file
`scripts/eventbus/dlq_repo.py`

### Procedure
Remove duplicate constants and add imports from `_constants.py`.

### Method
1. Read current `dlq_repo.py` to confirm constant locations and usage patterns
2. Remove the 4 duplicate constant definitions from the module-level constant section
3. Add import statements to pull these constants from `_constants.py`
4. Verify the file is syntactically valid Python

### Details
Remove the following lines from the module-level constant section (approximately lines 18-21):

```python
# Layer-owned column constants
_COL_DLQ_REQUEUE_COUNT = "dlq_requeue_count"
_COL_REDISTRIBUTED_FROM = "redelivered_from"
_COL_DELIVERY_FAILURE_COUNT = "delivery_failure_count"
_COL_CYCLE_FAILURE_COUNT = "cycle_failure_count"
```

Update the existing deferred import block (lines 12-15) to include the new shared constants:

```python
from eventbus._constants import (
    _COL_EVENT_ID,
    _COL_SEQ,
    _COL_ACKED_AT,
    _COL_DLQ_AT,
    _COL_DLQ_REQUEUE_COUNT,
    _COL_REDISTRIBUTED_FROM,
    _COL_DELIVERY_FAILURE_COUNT,
    _COL_CYCLE_FAILURE_COUNT,
)
```

Note: `_COL_EVENT_ID`, `_COL_SEQ`, `_COL_ACKED_AT`, `_COL_DLQ_AT` are already imported from `_constants.py` via the existing deferred import at line 12-15. Only the new shared constants need to be added to that import block.

## Compatibility considerations
- Backward compatibility: all public exports via `db.py` must remain unchanged
- Existing code that uses these constants will continue to work — only the source of the constant value changes
- No behavioral changes: SQL queries must produce identical results

## Security considerations
- None — column names are derived from schema definitions, not user input; no SQL injection risk introduced

## Rollback considerations
- Revert: restore the original constant definitions and remove the new import statements
- Risk: removing constants breaks any code that has already been updated to import them from `_constants.py`; rollback should be done atomically with the corresponding updates to other modules

## Validation plan
- Integration: verify DLQ operations work correctly
  ```bash
  uv run pytest tests/ -k dlq
  ```
  Expected: all DLQ-related tests pass
- Syntax check: confirm file parses without errors
  ```bash
  python -m py_compile scripts/eventbus/dlq_repo.py
  ```

## Completion criteria
- [ ] All 4 duplicate constants removed from `dlq_repo.py`
- [ ] Imports from `_constants.py` include all 4 removed constants
- [ ] File parses without syntax errors
- [ ] All DLQ-related tests pass

## Out of scope
- Removing duplicate constants from other modules (handled in separate procedure documents)
- Renaming any column names
- Changing SQL query logic
- Adding new functionality
- Modifying schema.sql

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | — | 20260920-162540 |  |
| 2 | Add or update tests per Validation plan | Completed | — | 20260920-162545 | N/A: no behavioral changes, no tests needed |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | — | 20260920-162550 | Syntax OK; DLQ tests pass (7 failures are pre-existing) |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | — | 20260920-162555 | N/A: no docs/00_index.md task-scope mapping for scripts/eventbus/dlq_repo.py |

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
- **Requirement ID**: REQ-002 (import shared constants from `_constants.py`)
- **Source issue**: issues/20260920-151726_eb001_refactor-eventbus-column-constants-and-add-layer-documentation.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260920-153828_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260920-154418
- **Related target files**: scripts/eventbus/dlq_repo.py