## Goal
Add assertions that the health response surfaces the new overflow-disconnect/
duplicate-rejection counter fields (REQ-005, REQ-006; AC5).

## Scope
In scope: new test method(s) in `TestHealth`. Out of scope: `test_health_ok`,
`test_health_degraded_when_db_unavailable`, `test_health_503_when_dlq_task_stopped` —
these three existing tests continue to pass unmodified.

## Assumptions
- `test_health_ok` already asserts on the healthy-baseline JSON response shape — the
  simplest addition is extending its assertions to include the two new keys
  (`overflow_disconnects: 0`, `duplicate_connection_rejections: 0` on a clean
  baseline) rather than adding an entirely separate test, since no new scenario setup
  is needed to observe the two counters at their zero-baseline value.

## Design decisions
Extend `test_health_ok` to assert `overflow_disconnects == 0` and
`duplicate_connection_rejections == 0` on a fresh client. Add one new test that drives
an actual overflow or duplicate-rejection scenario (reusing `broker.py`'s test
patterns from row 05, at the HTTP layer) and asserts the corresponding counter
increments in the health response.

## Alternatives considered
Only extending `test_health_ok`'s baseline assertion (without a nonzero-value test)
was considered and rejected: REQ-006 explicitly calls for asserting the new counter
*fields*, and a zero-only assertion would not catch a health-route bug that reads the
wrong broker attribute (e.g. always returning 0 regardless of the actual count).

## Implementation
### Target file
`tests/eventbus/test_eventbus_health.py`

### Procedure
1. Extend `test_health_ok`'s existing assertions with the two new zero-baseline keys.
2. Add `test_health_reports_overflow_and_duplicate_counters` to `TestHealth`, driving
   one overflow scenario (or directly manipulating the broker's counters via a
   duplicate-`consumer_id` subscribe attempt) and asserting the health response
   reflects the incremented count(s).

### Method
`pytest` test methods inside the existing `TestHealth` class, matching its current
style.

### Details
```python
class TestHealth:
    def test_health_ok(self, client: TestClient) -> None:
        response = client.get("/health")
        body = response.json()
        assert body["status"] == "ok"
        ...
        assert body["overflow_disconnects"] == 0
        assert body["duplicate_connection_rejections"] == 0

    def test_health_reports_overflow_and_duplicate_counters(
        self, client: TestClient
    ) -> None:
        with client.stream(
            "GET", "/subscribe", params={"consumer_id": "dup-health"}
        ):
            second = client.get("/subscribe", params={"consumer_id": "dup-health"})
            assert second.status_code == 409
            response = client.get("/health")
            assert response.json()["duplicate_connection_rejections"] >= 1
```

## Compatibility considerations
`test_health_ok`'s extension is additive (new assertions on existing keys already
present in the response); the new test does not modify any existing test.

## Security considerations
Test-only file; no production security surface.

## Rollback considerations
Revert this file's diff; no production behavior depends on this file.

## Validation plan
`uv run pytest tests/eventbus/test_eventbus_health.py -v` — all tests pass, including
the extended `test_health_ok` and the new counter test.

## Completion criteria
`test_health_ok` asserts the two new fields at their zero baseline; the new test
confirms at least one counter increments correctly in the health response after
triggering the corresponding scenario (AC5).

## Out of scope
`test_health_degraded_when_db_unavailable`, `test_health_503_when_dlq_task_stopped` —
unmodified.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Extend `test_health_ok` with the two new zero-baseline assertions | Pending | — | — | |
| 2 | Add `test_health_reports_overflow_and_duplicate_counters` | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |

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
- **Requirement ID**: REQ-005, REQ-006
- **Source issue**: issues/20260907-125042_eb_h02_backpressure_duplicate_consumer_connection.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260909-095501_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260910-092931
- **Related target files**: tests/eventbus/test_eventbus_health.py
