## Goal
Consolidate all shared column name constants into `scripts/eventbus/_constants.py` so it becomes the single source of truth for column names used across eventbus repo modules. Implements REQ-001 (shared constants consolidation) and REQ-002 (import from `_constants.py`).

## Scope
- Add 8 shared column constants to `_constants.py`: `_COL_DELIVERY_FAILURE_COUNT`, `_COL_CYCLE_FAILURE_COUNT`, `_COL_DLQ_REQUEUE_COUNT`, `_COL_REDISTRIBUTED_FROM`, `_COL_CONSUMER_DELIVERY_FAILURE_COUNT`, `_COL_CONSUMER_ID`, `_COL_OFFSET`
- Update `_constants.py` `__all__` to export these new constants
- No changes to constant values — only additions

## Assumptions
- Column name string values will not change during this refactoring
- All existing imports of these constants will be updated to import from `_constants.py` instead of local definitions
- Layer-specific constants remain in their original modules (not moved to `_constants.py`)

## Design decisions
- Consolidation strategy: move all shared constants to `_constants.py`, keep layer-specific ones in place
- Import pattern: use `from eventbus._constants import _COL_X` instead of local definitions
- `_constants.py` already has 4 constants (`_COL_EVENT_ID`, `_COL_SEQ`, `_COL_ACKED_AT`, `_COL_DLQ_AT`); adding 8 more brings the total to 12

## Alternatives considered
- Keep constants distributed across modules: rejected because duplication creates maintenance risk (renaming a column requires updating multiple files)
- Create a separate `column_names.py` module: rejected because `_constants.py` already serves as the shared constants module and adding to it avoids introducing a new module boundary

## Implementation
### Target file
`scripts/eventbus/_constants.py`

### Procedure
Add shared column constants and update exports.

### Method
1. Read current `_constants.py` to confirm existing constants and `__all__`
2. Append the 8 shared column constants after the existing `_COL_DLQ_AT` definition
3. Update `__all__` to include the new constants
4. Verify the file is syntactically valid Python

### Details
Append the following constants after the existing `_COL_DLQ_AT = "dlq_at"` line (line 11):

```python
# Shared column constants — used by all layers
_COL_DELIVERY_FAILURE_COUNT = "delivery_failure_count"
_COL_CYCLE_FAILURE_COUNT = "cycle_failure_count"
_COL_DLQ_REQUEUE_COUNT = "dlq_requeue_count"
_COL_REDISTRIBUTED_FROM = "redelivered_from"
_COL_CONSUMER_DELIVERY_FAILURE_COUNT = "consumer_delivery_failure_count"
_COL_CONSUMER_ID = "consumer_id"
_COL_OFFSET = "offset"
```

Update `__all__` to include the new constants:

```python
__all__ = [
    "_COL_EVENT_ID",
    "_COL_SEQ",
    "_COL_ACKED_AT",
    "_COL_DLQ_AT",
    "_COL_DELIVERY_FAILURE_COUNT",
    "_COL_CYCLE_FAILURE_COUNT",
    "_COL_DLQ_REQUEUE_COUNT",
    "_COL_REDISTRIBUTED_FROM",
    "_COL_CONSUMER_DELIVERY_FAILURE_COUNT",
    "_COL_CONSUMER_ID",
    "_COL_OFFSET",
]
```

## Compatibility considerations
- Backward compatibility: all public exports via `db.py` must remain unchanged
- Existing code that imports from `_constants.py` will gain access to additional constants without breaking
- Code that defines its own copy of these constants (currently in `delivery_repo.py`, `event_repo.py`, `dlq_repo.py`, `schema.py`) will need to be updated to import from `_constants.py` instead

## Security considerations
- None — column names are derived from schema definitions, not user input; no SQL injection risk introduced

## Rollback considerations
- Revert: remove the 8 added constants and restore the original `__all__` list
- Risk: removing constants breaks any code that has already been updated to import them from `_constants.py`; rollback should be done atomically with the corresponding updates to other modules

## Validation plan
- Unit: verify all shared constants exported correctly
  ```bash
  python -c "import eventbus._constants; print(eventbus._constants.__all__)"
  ```
  Expected: all 12 constants listed in `__all__`
- Syntax check: confirm file parses without errors
  ```bash
  python -m py_compile scripts/eventbus/_constants.py
  ```

## Completion criteria
- [ ] All 8 shared column constants defined in `_constants.py`
- [ ] `__all__` includes all 12 constants
- [ ] File parses without syntax errors
- [ ] No duplicate constant definitions remain in other modules (verified separately)

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
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | — | 20260920-160129 |  |
| 2 | Add or update tests per Validation plan | Completed | — | 20260920-160151 | N/A: no behavioral changes, no tests needed |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | — | 20260920-160159 | N/A: syntax check passed, no lint/type issues |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | — | 20260920-160207 | N/A: no docs/00_index.md task-scope mapping for scripts/eventbus/_constants.py |

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
- **Requirement ID**: REQ-001 (consolidate shared constants), REQ-002 (import from `_constants.py`)
- **Source issue**: issues/20260920-151726_eb001_refactor-eventbus-column-constants-and-add-layer-documentation.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260920-153828_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260920-154418
- **Related target files**: scripts/eventbus/_constants.py