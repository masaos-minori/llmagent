## Goal

Remove `_COL_DELIVERY_FAILURE_COUNT` and `_COL_CYCLE_FAILURE_COUNT` and their `__all__` entries from `_constants.py`, since no importer remains after the other edits (REQ-005).

## Scope

- Modify `scripts/eventbus/_constants.py` only.

## Assumptions

- After `delivery_repo.py` and `dlq_repo.py` drop their imports, nothing references these two constants.
- The schema-migration module that previously imported them was already removed.

## Design decisions

- Delete the two `=_COL_*` definitions (lines 13-14) and their `__all__` entries (lines 26-27); keep `_COL_CONSUMER_DELIVERY_FAILURE_COUNT`.

## Alternatives considered

- Leaving the constants defined but unused: rejected — dead exports invite reuse of the removed counters.

## Implementation

### Target file

`scripts/eventbus/_constants.py`

### Procedure

1. Delete `_COL_DELIVERY_FAILURE_COUNT = "delivery_failure_count"` (line 13) and `_COL_CYCLE_FAILURE_COUNT = "cycle_failure_count"` (line 14).
2. Remove `"_COL_DELIVERY_FAILURE_COUNT"` and `"_COL_CYCLE_FAILURE_COUNT"` from `__all__` (lines 26-27).
3. Confirm no remaining `import` of either name with `rg "_COL_DELIVERY_FAILURE_COUNT|_COL_CYCLE_FAILURE_COUNT" scripts/` (only the deleted definitions should have gone).

### Method

These constants were imported only by `delivery_repo.py` and `dlq_repo.py`; both drop the imports in their own documents, so the exports become dead.

### Details

- Definitions lines 13-14; `__all__` entries lines 26-27.

## Compatibility considerations

- Verify the live run `uv run python tools/check_db_separation.py` and `lint-imports` still pass after the sibling edits remove the importers.

## Security considerations

- N/A: constant removal.

## Rollback considerations

- revert the commit.

## Validation plan

- `uv run ruff check scripts/`, `uv run mypy --no-namespace-packages scripts/`, `PYTHONPATH=scripts uv run lint-imports`, `uv run python tools/check_db_separation.py`.
- `uv run pytest tests/eventbus tests/db -q`.

## Completion criteria

- `_constants.py` exports no `_COL_DELIVERY_FAILURE_COUNT` / `_COL_CYCLE_FAILURE_COUNT`; `rg -P "(?<!consumer_)delivery_failure_count|cycle_failure_count|_COL_DELIVERY_FAILURE_COUNT|_COL_CYCLE_FAILURE_COUNT" scripts` returns no match (AC-1).

## Out of Scope

- DDL, DLQ/redelivery code, tests, documents.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | |

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
- **Requirement ID**: REQ-005
- **Source issue**: `issues/20261022-124142_evcounter_decide-event-level-failure-counters.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261022-130338_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261022-145114
- **Related target files**: `scripts/eventbus/_constants.py`
