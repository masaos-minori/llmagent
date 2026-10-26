## Goal

Verify DLQ pagination returns a consistent snapshot across pages (`REQ-004`) and that the requeue timestamp is bound as a SQL parameter rather than interpolated into SQL (`REQ-005`).

## Scope

- Modify `tests/eventbus/test_eventbus_dlq_pagination.py`: extend the pagination test to assert page non-overlap and full coverage, and add a static check that no f-string `strftime(...)` timestamp interpolation remains in the requeue path.
- Do not modify `scripts/eventbus/dlq_repo.py` or `scripts/eventbus/dlq_route.py` — the timestamp binding and single-lock snapshot live there (seq-01 / seq-02).

## Assumptions

- The `/dlq` endpoint accepts `limit`/`offset` and returns `total`, `limit`, `offset`, `items` (`REQ-004`).
- Promotion seeds a `consumer_delivery` row with `consumer_delivery_failure_count = 1` and a mismatched `consumer_last_nack_attempt` so a single NACK reaches `max_retry` and promotes (the existing `_simulate_delivery` helper does exactly this).
- `redeliver_event()` binds the requeue timestamp as a `?` parameter using `now_iso()` (or the schema default); the optional explicit `now` (if ever passed) is stored as data, never interpolated (`REQ-005`, `UNK-01`).

## Design decisions

- **Assert cross-page invariants**: page 2 must not overlap page 1, and together the pages must cover the full set. A torn snapshot between the count and fetch would let pages skip or double-count events.
- **Verify REQ-005 statically**, because the requeue endpoint exposes no `now` parameter (no caller passes one) — the parameterization is an internal repository contract, best caught by confirming the f-string `strftime(...)` interpolation is gone and the timestamp is bound as a `?` parameter.

## Alternatives considered

- Adding an HTTP test that passes an explicit timestamp: rejected — the requeue endpoint has no timestamp parameter; `now` lives only on the repository function (`redeliver_event`), so REQ-005 is verified by static analysis, not an HTTP call.

## Implementation

### Target file

`tests/eventbus/test_eventbus_dlq_pagination.py`

### Procedure

1. Extend `test_dlq_pagination` to fetch page 1 (`limit=100`) and page 2 (`limit=2&offset=2`) and assert: page 2 items do not overlap page 1 items, and the union covers `min(total, ...)` events with no duplicates.
2. Add `test_dlq_pagination_no_string_timestamp_interpolation (new)` as a thin wrapper that runs the static `rg` check for the removed f-string interpolation and asserts the requeue INSERT binds a `?` parameter.

### Method

```python
def test_dlq_pagination(client: TestClient) -> None:
    events = []
    for i in range(5):
        ev = _event()
        _publish_event(client, ev)
        events.append(ev["event_id"])

    for event_id in events:
        _simulate_delivery(client, event_id, "consumer-A")

    nack_headers = {"Authorization": "Bearer consumer-token"}
    for event_id in events:
        r = client.post(
            "/nack", params={"event_id": event_id, "consumer_id": "consumer-A"},
            headers=nack_headers,
        )
        assert r.status_code == 200

    dlq_headers = {"Authorization": "Bearer operator-token"}

    r = client.get("/dlq?limit=100&offset=0", headers=dlq_headers)
    assert r.status_code == 200
    body = r.json()
    total = body["total"]
    assert total >= 5

    page1_ids = [item["event_id"] for item in body["items"]]

    r2 = client.get("/dlq?limit=2&offset=2", headers=dlq_headers)
    assert r2.status_code == 200
    body2 = r2.json()
    assert body2["limit"] == 2
    assert body2["offset"] == 2

    # Non-overlap and full coverage: one consistent snapshot across pages.
    page2_ids = [item["event_id"] for item in body2["items"]]
    assert not set(page1_ids) & set(page2_ids), "pages overlap: torn snapshot"
    assert len(set(page1_ids) | set(page2_ids)) == min(total, len(page1_ids) + len(page2_ids))


def test_dlq_pagination_no_string_timestamp_interpolation() -> None:
    import subprocess

    # REQ-005: the f-string strftime(...) interpolation is removed; the timestamp
    # is bound as a ? parameter in the requeue INSERT.
    result = subprocess.run(
        ["rg", "--no-filename", "strftime\\(", "scripts/eventbus/dlq_repo.py"],
        capture_output=True, text=True,
    )
    assert result.returncode != 0, "strftime f-string interpolation still present"
```

### Details

- The non-overlap assertion (`set(page1_ids) & set(page2_ids)` empty) is the direct test of REQ-004's one-snapshot guarantee: a count taken at a different instant than the fetch would produce pages that skip or repeat events.
- The REQ-005 static check greps `scripts/eventbus/dlq_repo.py` for any remaining `strftime(` interpolation; a clean requeue binds `now_iso()` (or the schema default) as a `?` parameter instead.

## Compatibility considerations

- Extends existing pagination tests; the new static test imports `subprocess` locally. Requires the seq-01/seq-02 changes to exist.

## Security considerations

- No change: pagination uses the operator token; the static check reads source only.

## Rollback considerations

- Remove the extended assertions and `test_dlq_pagination_no_string_timestamp_interpolation (new)`.

## Validation plan

| Target File/Module | Testing Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| `scripts/eventbus/dlq_route.py` | Integration: pagination snapshot consistency | `uv run pytest tests/eventbus/` | Pages non-overlapping, full coverage, `total`/`items` one snapshot |
| `scripts/eventbus/dlq_repo.py` | Static: no f-string `strftime(` interpolation; timestamp bound as `?` | `rg "strftime\\(" scripts/eventbus/dlq_repo.py` | Zero matches |
| `scripts/eventbus/*` | Static analysis | `uv run ruff check scripts/`, `uv run mypy --no-namespace-packages scripts/`, `uv run bandit -r scripts/ -c pyproject.toml -ll`, `PYTHONPATH=scripts uv run lint-imports` | Clean |

## Completion criteria

- `test_dlq_pagination` asserts page 2 does not overlap page 1 and the union covers the full set.
- `test_dlq_pagination_no_string_timestamp_interpolation (new)` confirms no `strftime(` interpolation remains (`REQ-005`).

## Out of Scope

- Requeue transaction/rollback and concurrency — sibling procedures.
- Promotion-during-listing snapshot — handled by the sibling procedure for `test_eventbus_dlq_promotion.py` (`REQ-004`).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Done | 2026-10-26 | 2026-10-26 | Extended `test_dlq_pagination` with cross-page non-overlap/coverage assertions and added `test_dlq_pagination_no_string_timestamp_interpolation`. Two deviations from the doc snippet: (a) its non-overlap check compares the `limit=100` page against the `offset=2` page, which trivially overlaps; final version compares two disjoint windows (`offset=0,limit=2` vs `offset=2,limit=2`) against `min(total, 4)`. (b) the static check reads `dlq_repo.py` via `pathlib` instead of shelling out to `rg` (no tool dependency in tests); it asserts no `strftime(` anywhere in the module and that `now_iso` binding is present. `strftime(` in `scripts/eventbus/schema.sql` DEFAULT is a different file, out of scope per the seq-07 caveat. |
| 2 | Add or update tests per Validation plan | Done | 2026-10-26 | 2026-10-26 | `rg "strftime\\(" scripts/eventbus/dlq_repo.py`: zero matches (exit 1). Full suite: 337 passed, 1 skipped. |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Done | 2026-10-26 | 2026-10-26 | ruff clean; `run_validation_gates.py`: all 10 checks Pass, zero Fail. |
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
- **Requirement ID**: `REQ-004` (pagination snapshot consistency), `REQ-005` (timestamp bound as parameter)
- **Source issue**: `issues/20261023-154325_eventbus001_dlq-requeue-transactional.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261025-095644_eventbus001_dlq-requeue-transactional.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261025-131314
- **Related target files**: `tests/eventbus/test_eventbus_dlq_pagination.py`
