## Goal

Confirm that `scripts/eventbus/_constants.py` is consistent with REQ-001's per-consumer delivery state: `_COL_CONSUMER_DELIVERY_FAILURE_COUNT` is present and unchanged, and `_COL_CONSUMER_LAST_NACK_ATTEMPT` is defined for NACK idempotency.

## Scope

Verify `scripts/eventbus/_constants.py` only. No functional edit is required for REQ-001 unless a Plan revision directs otherwise (see Out of scope / Plan Gap). Specifically:

- Confirm `_COL_CONSUMER_DELIVERY_FAILURE_COUNT = "consumer_delivery_failure_count"` (line 17) is present and unchanged.
- Confirm `_COL_CONSUMER_LAST_NACK_ATTEMPT = "consumer_last_nack_attempt"` (line 18) is present and exported in `__all__`.

Referenced/updated by other documents (not modified here): the columns' DDL (`scripts/eventbus/schema.sql`, row 3; `scripts/db/schema_sql.py`, row 4) and the `nack_event()` / `ack_event_for_consumer()` logic that consumes these constants (`scripts/eventbus/delivery_repo.py`, row 1).

## Assumptions

- Column names are the single source of truth for both DDL and Python; the constant values must match the DDL exactly.
- `last_nack_attempt` is stored on `consumer_delivery` and keyed per `(consumer_id, event_id)`.

## Design decisions

- **New named constant**: introduce `_COL_LAST_NACK_ATTEMPT` rather than an inline string literal at call sites, matching the existing pattern (`_COL_CONSUMER_DELIVERY_FAILURE_COUNT`, `_COL_ACKED_AT`).
- **Value stability**: `_COL_CONSUMER_DELIVERY_FAILURE_COUNT` keeps its current value; only its semantic owner changes from `events` to `consumer_delivery`, so this file needs no edit to that line.

## Alternatives considered

- Inline string literals at the two call sites — rejected; the repo centralizes column names in this module to avoid drift between DDL and SQL.

## Implementation

### Target file

`scripts/eventbus/_constants.py`

### Procedure

1. **Already completed**: `_COL_CONSUMER_DELIVERY_FAILURE_COUNT = "consumer_delivery_failure_count"` is present at line 17 and unchanged.
2. **Already completed**: `_COL_CONSUMER_LAST_NACK_ATTEMPT = "consumer_last_nack_attempt"` is present at line 18 and exported in `__all__` at line 31.

### Method

- Insert the new assignment in the existing `_COL_*` block so the file stays grouped; append to `__all__` preserving alphabetical-ish order consistent with the current listing.

### Details

- **Already completed**: `_COL_CONSUMER_DELIVERY_FAILURE_COUNT` (line 17) is unchanged; its reassignment to the per-consumer column happens at the usage site (`delivery_repo.py`, row 1).
- **Already completed**: `_COL_CONSUMER_LAST_NACK_ATTEMPT` (line 18) is defined and exported.
- Keep the module docstring accurate: column names derive from the `events`/`consumer_delivery` DDL in `schema.sql`.

## Compatibility considerations

- Purely additive; existing imports and values are unchanged. No runtime impact until consumers adopt `_COL_LAST_NACK_ATTEMPT`.

## Security considerations

- Column names are not user input; injection risk does not apply (consistent with the module's existing rationale).

## Rollback considerations

- Removing the one added constant and `__all__` entry reverts this file cleanly.

## Validation plan

- `rg _COL_LAST_NACK_ATTEMPT scripts/` confirms the constant is defined and exported.
- ruff + mypy on `_constants.py`; confirm `__all__` has no duplicate entries.

## Completion criteria

- **Already met**: `_COL_CONSUMER_LAST_NACK_ATTEMPT` is defined in the shared block and present in `__all__`.
- **Already met**: `_COL_CONSUMER_DELIVERY_FAILURE_COUNT` is unchanged in value.

## Out of scope

- The `consumer_delivery` DDL / column additions (rows 3-4).
- `nack_event()` idempotency logic consuming the constant (`delivery_repo.py`, row 1).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | — | — | All steps already completed in prior cycle |
| 2 | Add or update tests per Validation plan | Completed | — | — | Tests updated in prior cycle |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | — | — | ruff/mypy passed in prior cycle |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | — | — | No doc target for this row |

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
- **Requirement ID**: `REQ-001` (per-consumer failure count + NACK idempotency — constant for `last_nack_attempt`)
- **Source issue**: `issues/done/20261007-154016_ebnack01_fix-eventbus-ack-and-nack-state-management.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261008-160952_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261009-132618
- **Related target files**: `scripts/eventbus/_constants.py`

> **Plan Gap (needs plan amendment)**: REQ-001 also adds `consumer_delivery_failure_count` and `last_nack_attempt` to the `consumer_delivery` table DDL. Those additions belong in `scripts/eventbus/schema.sql` (row 3) and `scripts/db/schema_sql.py` (row 4), which are tagged REQ-004 only. `schema.py` `_migrate` currently adds the count to `events`, not `consumer_delivery`, and `schema.py` is not a listed target file. Scope decision for a Plan revision; this document covers only the constant addition tagged for `_constants.py`.
