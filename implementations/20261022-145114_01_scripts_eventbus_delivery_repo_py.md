## Goal

Replace `NackResult`'s `-1` / `-2` sentinel fields (`delivery_failure_count`, `cycle_failure_count`) with an explicit `status` (`ok`, `not_found`, `invalid_state`) plus `consumer_failure_count`, and stop `nack_event()` from reading the events-level counters that the per-consumer model left inert (REQ-002).

## Scope

- Modify `scripts/eventbus/delivery_repo.py` only.
- `NackResult`, `nack_event()`, and their re-exported names via `scripts/eventbus/db.py` (names unchanged).

## Assumptions

- `scripts/eventbus/db.py` re-exports `NackResult` / `nack_event`; the public names stay.
- `scripts/eventbus/ack_route.py` is the only production caller and maps the new status (see its own procedure document).
- An idempotent repeat NACK (matching `last_nack_attempt`) must keep reporting `ok` with the stored per-consumer count.

## Design decisions

- Model the three outcomes with a single `status: Literal["ok", "not_found", "invalid_state"]`; drop the two sentinel ints that doubled as both a returned value and the route's status signal.
- Keep `consumer_failure_count: int | None` unchanged: `ok` carries it when a `consumer_id` was given, `not_found` / `invalid_state` carry `None`.

## Alternatives considered

- Keeping the two sentinels and adding a separate status field: rejected — the sentinels are exactly the ambiguity being removed.
- A boolean "found" flag instead of a three-valued status: rejected — three outcomes map cleanly to one literal.

## Implementation

### Target file

`scripts/eventbus/delivery_repo.py`

### Procedure

1. Rewrite `NackResult`: replace `delivery_failure_count: int | Literal[-1]` and `cycle_failure_count: int | Literal[-2]` with `status: Literal["ok", "not_found", "invalid_state"]`; keep `consumer_failure_count: int | None = None`. Update the class docstring to describe the status outcomes.
2. Rewrite every `nack_event()` return site:
   - event not found → `NackResult("not_found")`
   - event already DLQ'd (`existing[_COL_DLQ_AT] is not None`) → `NackResult("invalid_state")`
   - consumer already ACKed → `NackResult("invalid_state")`
   - idempotent repeat (matching `last_nack_attempt`) → `NackResult("ok", consumer_failure_count=<current consumer count>)`
   - success with `consumer_id` → after the `consumer_delivery` increment, `NackResult("ok", consumer_failure_count=<new count>)`
   - success without `consumer_id` → `NackResult("ok")`
3. Delete the reads of `_COL_DELIVERY_FAILURE_COUNT` / `_COL_CYCLE_FAILURE_COUNT`: the idempotent branch's `SELECT {_COL_DELIVERY_FAILURE_COUNT} FROM events` (and the `dfc` derivation) and the final read-back `SELECT {_COL_DELIVERY_FAILURE_COUNT}, {_COL_CYCLE_FAILURE_COUNT} FROM events`. Neither feeds a field any more.
4. Remove the now-unused `_COL_DELIVERY_FAILURE_COUNT` / `_COL_CYCLE_FAILURE_COUNT` imports from `_constants` in this module.
5. Update `nack_event()`'s docstring to list the status outcomes instead of the two legacy counts.

### Method

The `-1` / `-2` sentinels and the events-level column reads were the sole users of those columns in this module. Removing them makes the columns inert here without touching the authoritative `consumer_delivery` path (read/increment), which stays.

### Details

- Current return sites: not-found `NackResult(-1, -1)` (lines 74, 114, 156); DLQ/already-ACKed `NackResult(-2, -2)` (lines 76, 86); idempotent `NackResult(dfc, -2, consumer)` (lines 111-113, with `dfc` read at lines 106-110); success `NackResult(int(dfc), int(cfc))` (lines 138-141) and with consumer `NackResult(..., consumer)` (lines 150-154).
- Idempotent branch: delete lines 106-110 and return `NackResult("ok", consumer_failure_count=int(consumer_row[_COL_CONSUMER_DELIVERY_FAILURE_COUNT]))`.
- Final read-back (lines 133-155): select nothing from `events`; return `NackResult("ok")` or `NackResult("ok", consumer_failure_count=...)` when a consumer_id was provided.

## Compatibility considerations

- `scripts/eventbus/ack_route.py` currently reads `nack_result.delivery_failure_count` as its status signal; its procedure renames that to `nack_result.status`. Make the two edits together so the caller and producer stay consistent.
- `scripts/eventbus/db.py` re-exports the names; no change needed.

## Security considerations

- No authorization or path change; the parameterized SQL and its `# nosec B608` comments on column-name f-strings remain valid.

## Rollback considerations

- revert the commit.

## Validation plan

- `uv run pytest tests/eventbus/test_eventbus_ack_nack.py -q` with assertions rewritten to the status model.
- `uv run ruff check scripts/`, `uv run mypy --no-namespace-packages scripts/`, `PYTHONPATH=scripts uv run lint-imports`, `uv run python tools/check_db_separation.py`.

## Completion criteria

- `NackResult` has no `delivery_failure_count` / `cycle_failure_count` fields; `nack_event()` returns only `status` plus an optional `consumer_failure_count`; `rg -P "(?<!consumer_)delivery_failure_count|cycle_failure_count" scripts/eventbus/delivery_repo.py` returns no match.

## Out of Scope

- The route status mapping, the DLQ record/listing/promotion, redelivery, the `events` DDL, the shared constants, and the four documents (each its own document).

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
- **Requirement ID**: REQ-002
- **Source issue**: `issues/20261022-124142_evcounter_decide-event-level-failure-counters.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261022-130338_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261022-145114
- **Related target files**: `scripts/eventbus/delivery_repo.py`
