## Goal

Map the renamed `NackResult.status` to the existing 404 / 409 outcomes and return the per-consumer count under the new key `consumer_delivery_failure_count` in the NACK response, leaving DLQ promotion on the per-consumer count unchanged (REQ-003).

## Scope

- Modify `scripts/eventbus/ack_route.py` only.
- `_nack_and_promote()`, the post-call 404 dispatch, and the response dict.

## Assumptions

- `nack_event()` (its own document) now returns `NackResult(status, consumer_failure_count)`; `consumer_id` is mandatory for NACK, so `consumer_failure_count` is present on the `ok` path.
- `scripts/eventbus/delivery_repo.py` is edited in the same change (its procedure document).

## Design decisions

- Replace the `failure_count == -1` / `== -2` sentinel dispatch with a `status == "not_found"` / `"invalid_state"` dispatch; keep the atomic 409 checks inside the transaction for `invalid_state`.
- Rename the response key `delivery_failure_count` → `consumer_delivery_failure_count`; keep `dlq_promoted` when promoted.

## Alternatives considered

- Returning the raw `NackResult` to the endpoint handler and branching there: rejected — keep the transaction boundary in `_nack_and_promote` and only surface a small `(status, count, promoted)` tuple.
- Keeping the old key and deprecating it later: rejected — the plan renames permanently (the key already reported the per-consumer value).

## Implementation

### Target file

`scripts/eventbus/ack_route.py`

### Procedure

1. In `_nack_and_promote()`, replace `failure_count = nack_result.delivery_failure_count` with `status = nack_result.status`.
2. Replace `if failure_count == -1: return (-1, False)` with `if status == "not_found": return ("not_found", None, False)`.
3. Replace `if failure_count == -2:` block with `if status == "invalid_state":` keeping the existing atomic 409 checks (consumer-acked then `dlq_at`), still raising 409.
4. On the `ok` path, keep `consumer_failure_count = nack_result.consumer_failure_count` and the promotion gate unchanged; return `("ok", consumer_failure_count, promoted)`.
5. After `run_with_db_lock`, replace `if failure_count == -1: raise 404` with `if status == "not_found": raise 404`.
6. Rename the response key: `"delivery_failure_count": failure_count` → `"consumer_delivery_failure_count": consumer_failure_count` (the count returned on the `ok` path). Update the log line's field name accordingly.

### Method

The route used `delivery_failure_count` purely as a status signal (-1 not found, -2 invalid state) while the value it carried was already the per-consumer count; the explicit status removes the overload and the rename removes the misleading key at once.

### Details

- Current code: lines 171-174 (sentinel dispatch), 205-210 (returns `consumer_failure_count if not None else failure_count`), 212-214 (404 on `-1`), 218-221 (response dict keyed `delivery_failure_count`).
- `_nack_and_promote` now returns `tuple[str, int | None, bool]` (`status, consumer_failure_count, promoted`).

## Compatibility considerations

- Depends on `delivery_repo.py` returning the new `NackResult` shape; edit both together.
- External consumers of `POST /nack` see a renamed response key (the plan's chosen breaking change, UNK-01); announce the new key to known clients before deployment.

## Security considerations

- No change to authorization or SQL; the 409 branch still reads `consumer_delivery.acked` and `events.dlq_at` parametrically.

## Rollback considerations

- revert the commit.

## Validation plan

- `uv run pytest tests/eventbus/test_eventbus_ack_nack.py -q` asserting the 404/409/200 outcomes and the new response key.
- `uv run ruff check scripts/`, `uv run mypy --no-namespace-packages scripts/`, `PYTHONPATH=scripts uv run lint-imports`.

## Completion criteria

- The NACK route dispatches on `nack_result.status`, raises 404 for `not_found` and 409 for `invalid_state`, promotes on the per-consumer count, and the response body holds `event_id` and `consumer_delivery_failure_count` (plus `dlq_promoted` when promoted).

## Out of Scope

- The result-model change (`delivery_repo.py`), DLQ/redelivery/DDL/constants, tests, documents.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 2026-10-22 | 2026-10-22 | |
| 2 | Add or update tests per Validation plan | Completed | 2026-10-22 | 2026-10-22 | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 2026-10-22 | 2026-10-22 | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 2026-10-22 | 2026-10-22 | |

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
- **Requirement ID**: REQ-003
- **Source issue**: `issues/20261022-124142_evcounter_decide-event-level-failure-counters.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261022-130338_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261022-145114
- **Related target files**: `scripts/eventbus/ack_route.py`
