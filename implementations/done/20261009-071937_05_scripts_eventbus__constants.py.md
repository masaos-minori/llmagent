## Goal

Add the shared per-consumer NACK-attempt column-name constant
`_COL_LAST_NACK_ATTEMPT` to `scripts/eventbus/_constants.py` so that
`delivery_repo.nack_event()` can key NACK idempotency on the delivery attempt without
hardcoding the column string (`REQ-001`).

## Scope

Modifies `scripts/eventbus/_constants.py` only. This constant is consumed by
`scripts/eventbus/delivery_repo.py` (the `nack_event()` idempotency change) and must
match the `last_nack_attempt` column added to `consumer_delivery` in the `schema.sql`
and `schema_sql.py` rows. See Design decisions for the relationship to
`_COL_CONSUMER_DELIVERY_FAILURE_COUNT`.

## Assumptions

- All eventbus column references go through these constants; callers must not inline
  the raw string.
- The constant is a plain `TEXT` column name; nullability/lifecycle is owned by the
  schema rows.
- `_COL_ACKED_AT` ("acked_at") remains valid: it now refers to
  `consumer_delivery.acked_at` (per-consumer), since `events.acked_at` is dropped by
  `REQ-004`. Do not remove it here.

## Design decisions

- Name the constant `_COL_LAST_NACK_ATTEMPT` and value `"last_nack_attempt"` to match
  the column added to `consumer_delivery` in the schema rows.
- Place it with the other per-consumer constants near
  `_COL_CONSUMER_DELIVERY_FAILURE_COUNT` / `_COL_CONSUMER_ID`.
- Register it in `__all__` so `from eventbus._constants import _COL_LAST_NACK_ATTEMPT`
  works like the other constants.
- Keep `_COL_CONSUMER_DELIVERY_FAILURE_COUNT` as-is in this row; its placement on the
  `events` table vs `consumer_delivery` is decided by the `REQ-002` / ADR-006 decision.

## Alternatives considered

- Hardcoding `"last_nack_attempt"` in `delivery_repo.py` — rejected: violates the
  single-source-of-truth contract of this module and would drift from the schema.

## Implementation

### Target file

`scripts/eventbus/_constants.py`

### Procedure

1. Add `_COL_LAST_NACK_ATTEMPT = "last_nack_attempt"` in the per-consumer constant
   block (near `_COL_CONSUMER_DELIVERY_FAILURE_COUNT`, line 18).
2. Append `"_COL_LAST_NACK_ATTEMPT"` to the `__all__` list (after
   `"_COL_CONSUMER_DELIVERY_FAILURE_COUNT"`, line 31).

### Method

- Open `scripts/eventbus/_constants.py`; insert the constant at line 18 and the
  export at line 31, preserving alphabetical-ish grouping and existing style.
- Confirm no other constant already owns the `"last_nack_attempt"` string.
- Lint and test: `ruff`, `mypy --no-namespace-packages`, `bandit`, `lint-imports`.

### Details

- The value MUST exactly equal the column name added to `consumer_delivery` in the
  `schema.sql` / `schema_sql.py` rows; mismatch breaks the migration and the repo.
- Do not touch `_COL_ACKED_AT` — it still backs `consumer_delivery.acked_at`.

## Compatibility considerations

- Purely additive; no existing symbol changes. Downstream `delivery_repo.py` is the
  first consumer (added by its row).

## Security considerations

- Constant definitions carry no injection surface.

## Rollback considerations

- Remove the constant and its `__all__` entry to revert.

## Validation plan

- Import check: `python -c "from eventbus._constants import _COL_LAST_NACK_ATTEMPT; print(_COL_LAST_NACK_ATTEMPT)"` prints `last_nack_attempt`.
- `ruff`, `mypy --no-namespace-packages`, `bandit`, `lint-imports`.

## Completion criteria

- `_COL_LAST_NACK_ATTEMPT == "last_nack_attempt"` defined and exported.
- Value matches the `consumer_delivery.last_nack_attempt` column in the schema rows.

## Out of scope

- Adding the `last_nack_attempt` column DDL (`schema.sql` / `schema_sql.py` rows).
- Using the constant in `nack_event()` (`delivery_repo.py` row).
- Removing `_COL_ACKED_AT` (`REQ-004` — still needed for `consumer_delivery.acked_at`).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add `_COL_LAST_NACK_ATTEMPT` constant to _constants.py | Completed | 20261009-182622 | 20261009-182622 |  |
| 2 | Add or update tests per Validation plan | Completed | 20261009-182622 | 20261009-182622 |  |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261009-182622 | 20261009-182622 |  |
| 4 | Update documentation | N/A | — | — | Docs handled by REQ-006 rows |

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
- **Requirement ID**: `REQ-001`
- **Source issue**: `issues/done/20261007-154016_ebnack01_fix-eventbus-ack-and-nack-state-management.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261008-160952_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261009-071937
- **Related target files**: `scripts/eventbus/_constants.py`