## Goal

Add regression coverage for the requeue contract that `scripts/eventbus/dlq_repo.py` now owns (`REQ-001`) and that `scripts/eventbus/dlq_route.py` maps from the typed result (`REQ-003`): a successful requeue returns `new_event_id` and `new_seq` together, a missing event yields 404, and an event that exists but is not in the DLQ yields 409.

## Scope

- Modify `tests/eventbus/test_eventbus_dlq.py`: extend the existing requeue endpoint test and add 404 / 409 cases.
- Do not modify `scripts/eventbus/dlq_repo.py` or `scripts/eventbus/dlq_route.py` — handled by the sibling procedures (seq-01 / seq-02).

## Assumptions

- The requeue endpoint still returns the same HTTP shape: `200` with `requeued`, `new_event_id`, `new_seq`; `404` with detail `event not found`; `409` with detail `event is not in DLQ`. Only the internal source of those values changed (`REQ-001`, `REQ-003`).
- `redeliver_event()` classifies 404 vs 409 inside the locked repository operation, so the route needs no follow-up SQL (`REQ-003`).
- The `client` fixture (`eventbus_helpers`) runs the app on port 8015 with an operator token.

## Design decisions

- **Keep the happy-path assertions, add the error paths.** The existing `test_dlq_requeue` already validates the success shape; the new cases target the classification the repository now performs.
- **Drive 404 and 409 through the HTTP endpoint**, not by calling the repository directly, so the test verifies the route's mapping of the typed result (`REQ-003`).

## Alternatives considered

- Calling `redeliver_event()` directly to assert on the typed result: rejected — the production path is HTTP, and the route's mapping is what `REQ-003` changes.

## Implementation

### Target file

`tests/eventbus/test_eventbus_dlq.py`

### Procedure

1. Extend `test_dlq_requeue` to assert `new_seq` is strictly greater than the original event's `seq` and `new_event_id` is a UUID v4 (already present) and that both come from the same response object.
2. Add `test_dlq_requeue_not_found_returns_404 (new)`: requeue an `event_id` that was never published and assert `404` with the not-found detail.
3. Add `test_dlq_requeue_existing_not_in_dlq_returns_409 (new)`: publish an event, never nack it, requeue it, and assert `409` with the not-in-DLQ detail.

### Method

```python
def test_dlq_requeue_not_found_returns_404(client: TestClient) -> None:
    # Never published, so no events row exists -> repository status not_found -> 404.
    missing_id = str(uuid.uuid4())
    resp = client.post(f"/dlq/{missing_id}/requeue")
    assert resp.status_code == 404
    assert resp.json()["detail"] == "event not found"


def test_dlq_requeue_existing_not_in_dlq_returns_409(
    client: TestClient,
) -> None:
    # Published but never nacked: the events row exists but dlq_at is NULL ->
    # repository status not_in_dlq -> 409.
    body = _event("dlq")
    resp = client.post("/publish", json=body)
    assert resp.status_code == 200

    resp = client.post(f"/dlq/{body['event_id']}/requeue")
    assert resp.status_code == 409
    assert resp.json()["detail"] == "event is not in DLQ"
```

### Details

- The success case keeps asserting `data["requeued"] is True`, a valid `new_event_id`, an integer `new_seq`, and `new_seq > body["seq"]` — proving `new_event_id` and `new_seq` describe one atomic result (`REQ-001`, `REQ-003`).
- The 404 case uses a random UUID that has no `events` row, so the conditional UPDATE affects zero rows and the existence read returns nothing.
- The 409 case uses a published-but-not-dlq'd event, so the existence read succeeds while `dlq_at` is NULL.

## Compatibility considerations

- The HTTP contract is unchanged, so the existing `test_dlq_requeue` continues to pass; the two new tests only exercise the previously-uncovered 404/409 branches (`REQ-003`).
- The route now depends on `redeliver_event()` returning the typed result from the seq-01 procedure; implement the two procedures in order.

## Security considerations

- No change: these tests exercise the authenticated operator endpoint through the same `client` fixture.

## Rollback considerations

- Remove the two new test functions and revert `test_dlq_requeue` to asserting only presence of `new_event_id`/`new_seq`.

## Validation plan

| Target File/Module | Testing Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| `tests/eventbus/test_eventbus_dlq.py` | Integration: requeue 200/404/409 classification | `uv run pytest tests/eventbus/` | Success returns matching `new_event_id`/`new_seq`; 404 for missing, 409 for not-in-DLQ |
| `scripts/eventbus/dlq_route.py` | Static: no `db.execute` remaining | `rg "db.execute" scripts/eventbus/dlq_route.py` | Zero matches |
| `scripts/eventbus/*` | Static analysis | `uv run ruff check scripts/`, `uv run mypy --no-namespace-packages scripts/`, `uv run bandit -r scripts/ -c pyproject.toml -ll`, `PYTHONPATH=scripts uv run lint-imports` | Clean |

## Completion criteria

- `test_dlq_requeue` asserts `new_seq > original seq` and a valid `new_event_id` (same atomic result).
- `test_dlq_requeue_not_found_returns_404 (new)` asserts 404 for an event with no `events` row.
- `test_dlq_requeue_existing_not_in_dlq_returns_409 (new)` asserts 409 for a published event with `dlq_at` NULL.

## Out of Scope

- Failure injection and connection-reuse coverage — handled by the sibling procedure for `test_eventbus_requeue_edge_cases.py` (`REQ-002`).
- Concurrency coverage — handled by the sibling procedure for `test_eventbus_concurrent.py` (`REQ-002`).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Done | 2026-10-26 | 2026-10-26 | `test_dlq_requeue`: captured publish `seq`, asserts `new_seq > original_seq` and `new_event_id` is UUID v4 (same atomic result). Added `test_dlq_requeue_not_found_returns_404` and `test_dlq_requeue_existing_not_in_dlq_returns_409` as specified (detail-string contract). Existing `test_requeue_unknown_event_returns_404` / `test_requeue_non_dlq_event_fails` already covered the status codes; the new tests add the `detail` assertions, which those tests lacked. |
| 2 | Add or update tests per Validation plan | Done | 2026-10-26 | 2026-10-26 | `tests/eventbus/`: 331 passed, 1 skipped (was 329 + 2 new). `rg "db.execute" scripts/eventbus/dlq_route.py`: zero matches. |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Done | 2026-10-26 | 2026-10-26 | `uv run python tools/run_validation_gates.py`: all checks Pass. |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Done | 2026-10-26 | 2026-10-26 | No docs change required (test-only procedure). |

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
- **Requirement ID**: `REQ-001` (typed result with `new_event_id`/`new_seq`), `REQ-003` (404/409 from typed result, no direct-SQL route)
- **Source issue**: `issues/20261023-154325_eventbus001_dlq-requeue-transactional.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261025-095644_eventbus001_dlq-requeue-transactional.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261025-131314
- **Related target files**: `tests/eventbus/test_eventbus_dlq.py`
