# Refactor eventbus column constants and add layer documentation

## Priority
High

## Summary
Consolidate duplicated column name constants across eventbus repo modules into `_constants.py` and create a README documenting the layer boundaries referenced by `db.py`'s stub header comment.

## Background
`scripts/eventbus/db.py` is a stub module whose docstring says: "Do not add new functions here. Add them to the appropriate layer module and re-export from this stub. See scripts/eventbus/README.md for layer boundaries." However, `scripts/eventbus/README.md` does not exist, and the layer boundary concept is never explained anywhere.

Each repo module (`event_repo.py`, `delivery_repo.py`, `dlq_repo.py`) and the schema layer (`schema.py`) define its own set of `_COL_*` column constants, even though many of these columns are shared across layers. For example:

- `_COL_DELIVERY_FAILURE_COUNT` appears in `delivery_repo.py`, `event_repo.py`, `dlq_repo.py`, and `schema.py` (4 places)
- `_COL_CYCLE_FAILURE_COUNT` appears in `delivery_repo.py`, `event_repo.py`, `dlq_repo.py`, and `schema.py` (4 places)
- `_COL_DLQ_AT` appears in both `_constants.py` and `delivery_repo.py`
- `_COL_CONSUMER_DELIVERY_FAILURE_COUNT` appears in both `delivery_repo.py` and `event_repo.py`
- `_COL_DLQ_REQUEUE_COUNT` appears in `dlq_repo.py`, `event_repo.py`, and `schema.py` (3 places)
- `_COL_REDISTRIBUTED_FROM` appears in `dlq_repo.py`, `event_repo.py`, and `schema.py` (3 places)
- `_COL_CONSUMER_ID` appears in `delivery_repo.py`, `event_repo.py`, and `schema.py` (3 places)
- `_COL_OFFSET` appears in `delivery_repo.py`, `event_repo.py`, and `schema.py` (3 places)

This duplication creates maintenance risk: renaming a column requires updating multiple files, and typos in column names can cause silent SQL errors.

## Problem
Column name constants are defined in four places (`_constants.py`, `delivery_repo.py`, `event_repo.py`, `dlq_repo.py`, `schema.py`) with overlapping sets. There is no single source of truth for column names, making refactoring error-prone and increasing the chance of subtle bugs from inconsistent naming.

Additionally, the layer boundary documentation referenced by `db.py`'s stub header does not exist, leaving developers without guidance on which module owns which responsibility.

## Reason for Change
Without consolidation, future changes to column names require updates across multiple files. A typo in one copy of a constant would pass linting but fail at runtime. The missing README means new contributors have no understanding of the architectural intent behind the stub module pattern.

## Implementation Intent
1. Audit all `_COL_*` constants across the five modules (`_constants.py`, `delivery_repo.py`, `event_repo.py`, `dlq_repo.py`, `schema.py`) and identify which columns are truly shared vs. layer-specific.
2. Move all shared column constants into `_constants.py`. Keep layer-specific constants in their respective modules.
3. Update all imports in `delivery_repo.py`, `event_repo.py`, `dlq_repo.py`, and `schema.py` to import shared constants from `_constants.py` instead of defining duplicates.
4. Create `scripts/eventbus/README.md` documenting: the layer architecture (connection layer, event repo, delivery repo, DLQ repo), the stub module pattern (`db.py` re-exports), and the rule about adding new functions to the appropriate layer module.

## Target Files or Areas
- `scripts/eventbus/_constants.py`
- `scripts/eventbus/delivery_repo.py`
- `scripts/eventbus/event_repo.py`
- `scripts/eventbus/dlq_repo.py`
- `scripts/eventbus/schema.py`
- `scripts/eventbus/db.py` (existing docstring)
- New file: `scripts/eventbus/README.md`

## Required Changes
- Consolidate shared column constants into `_constants.py`
- Update imports in `delivery_repo.py`, `event_repo.py`, `dlq_repo.py`, and `schema.py` to import from `_constants.py`
- Remove duplicate `_COL_*` definitions from repo modules
- Create `scripts/eventbus/README.md` with layer architecture documentation
- Verify all references to removed constants are updated

## Constraints
- Must preserve backward compatibility: all public exports via `db.py` must remain unchanged
- Column names themselves must not change — only move constants between files
- No behavioral changes: SQL queries must produce identical results
- The `__all__` exports in `db.py` must remain stable

## Acceptance Criteria
- [ ] All shared column constants live in `_constants.py`; no duplicates in repo modules or schema.py
- [ ] Each repo module and schema.py imports shared constants from `_constants.py` instead of defining them locally
- [ ] Layer-specific constants remain in their original modules
- [ ] `scripts/eventbus/README.md` exists and documents layer boundaries
- [ ] All existing tests pass after changes
- [ ] No new lint/type errors introduced

## Testing Expectations
- Run existing test suite: `uv run pytest tests/` (or eventbus-specific tests if available)
- Confirm no regressions in ack/nack/DLQ operations
- Type check: `uv run mypy scripts/eventbus/`

## Documentation Impact
New file `scripts/eventbus/README.md` required. Documents:
- Layer architecture (connection, event repo, delivery repo, DLQ repo)
- Stub module pattern (`db.py` re-exports)
- Rule: "Do not add new functions here. Add them to the appropriate layer module and re-export from this stub."

## Out of Scope
- Renaming any column names
- Changing SQL query logic
- Adding new functionality
- Modifying schema.sql
- Refactoring other parts of the eventbus module

## Dependencies
N/A: none

## Unresolved Questions
- None — resolved during adversarial verification:
  - `_COL_DELIVERY_FAILURE_COUNT` and `_COL_CYCLE_FAILURE_COUNT`: duplicated in 4 files each — must be moved to `_constants.py`
  - `_COL_DLQ_AT`: already in `_constants.py` but also defined in `delivery_repo.py` — remove from `delivery_repo.py`
  - `_COL_DLQ_REQUEUE_COUNT`, `_COL_REDISTRIBUTED_FROM`: duplicated in 3 files each — move to `_constants.py`
  - `_COL_CONSUMER_DELIVERY_FAILURE_COUNT`, `_COL_CONSUMER_ID`, `_COL_OFFSET`: duplicated in 3 files each — move to `_constants.py`
  - `schema.py` was missing from target files — it's part of the duplication problem

## AI Implementation Instruction
1. Read all five modules (`_constants.py`, `delivery_repo.py`, `event_repo.py`, `dlq_repo.py`, `schema.py`) to map current constant locations.
2. Identify which constants are used by multiple modules — those go to `_constants.py`.
3. Move shared constants to `_constants.py`, update its `__all__`.
4. Update imports in each module to import from `_constants.py`.
5. Remove duplicate definitions from all modules.
6. Create `scripts/eventbus/README.md` with layer documentation.
7. Do NOT rename any column values — only move constant assignments.
8. Do NOT change any SQL query logic.
9. Verify all tests pass after changes.

## Adversarial Verification
### Claims verified against source code
- db.py docstring references README.md: **CONFIRMED** (line 2)
- README.md does not exist: **CONFIRMED** (file not found)
- Column constant duplication: **CONFIRMED**, worse than stated originally
  - `_COL_DELIVERY_FAILURE_COUNT`: 4 places (not 3 as claimed)
  - `_COL_CYCLE_FAILURE_COUNT`: 4 places (not 3 as claimed)
  - `_COL_DLQ_AT`: 2 places (confirmed)
  - `_COL_CONSUMER_DELIVERY_FAILURE_COUNT`: 2 places (confirmed)
  - `_COL_DLQ_REQUEUE_COUNT`: 3 places (new finding)
  - `_COL_REDISTRIBUTED_FROM`: 3 places (new finding)
  - `_COL_CONSUMER_ID`: 3 places (new finding)
  - `_COL_OFFSET`: 3 places (new finding)
### Corrections made during verification
1. Priority raised from Medium → High (duplication affects 4+ files per constant)
2. Added `schema.py` to target files (was missing; defines 8 overlapping constants)
3. Updated Problem section to mention 4 places instead of 3
4. Updated Implementation Intent to include `schema.py` in audit scope
5. Updated Required Changes to include `schema.py` in import updates
6. Updated Acceptance Criteria to check for duplicates in schema.py
7. Resolved Unresolved Questions with specific guidance from grep evidence
