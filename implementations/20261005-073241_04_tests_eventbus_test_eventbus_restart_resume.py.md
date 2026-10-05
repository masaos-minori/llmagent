## Goal

Create a regression test verifying that out-of-order ACK followed by reconnect delivers all unacked events, preserving the at-least-once delivery guarantee stated in ADR-006.

## Scope

- Create `tests/eventbus/test_eventbus_restart_resume.py`: add `test_out_of_order_ack_no_skip_on_reconnect()` test case.

## Assumptions

- The EventBus component uses SQLite as its persistence layer.
- The `consumer_offsets` table tracks the high-water mark per consumer.
- The `consumer_delivery` table tracks all delivery attempts with `acked_at IS NULL` for unacked events.
- The `events` table has `seq`, `event_id`, and other required columns.
- Test fixtures use `TestClient` and `tmp_path` for database isolation.

## Design decisions

- Use `pytest.fixture` for database setup with `tmp_path` to ensure test isolation.
- Test both the `get_resume_position()` function directly and the SSE subscribe route end-to-end.
- Verify three scenarios: (1) direct function call, (2) SSE reconnect via TestClient, (3) ordered-ACK baseline (no regression).

## Alternatives considered

- Mock the database entirely: rejected because the fix involves SQL queries; integration testing against real SQLite provides better confidence.
- Single end-to-end test only: rejected because unit-level assertions on `get_resume_position()` provide clearer failure diagnostics.

## Implementation

### Target file

`tests/eventbus/test_eventbus_restart_resume.py`

### Procedure

Create the test file with the following test cases:
1. `test_out_of_order_ack_no_skip_on_reconnect`: main regression test
2. `test_ordered_ack_baseline`: ensures existing behavior is preserved
3. `test_get_resume_position_no_offset`: edge case — no prior offset

### Method

1. Create `tests/eventbus/test_eventbus_restart_resume.py` with the test module structure.
2. Add `@pytest.fixture` for database setup using `tmp_path`.
3. Add each test case with clear assertions.

### Details

**Change — Create `tests/eventbus/test_eventbus_restart_resume.py`:**

```python
"""Regression tests for EventBus reconnect resume position computation."""

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from eventbus import app as eb_app
from eventbus.db import insert_event
from eventbus.delivery_repo import (
    ack_event_for_consumer,
    get_consumer_offset,
    get_resume_position,
)


@pytest.fixture(scope="module")
def db(tmp_path_factory):
    """Provide an isolated SQLite database for the test module."""
    db_path = tmp_path_factory.mktemp("eventbus-test").joinpath("test.db")
    return str(db_path)


@pytest.fixture(autouse=True)
def _app_context(db):
    """Ensure the app uses the test database."""
    eb_app.app.state.db = sqlite3.connect(db)
    yield
    eb_app.app.state.db.close()
    eb_app.app.state.db = None


class TestOutOfOrderAckNoSkipOnReconnect:
    """Verify at-least-once delivery under out-of-order ACK conditions."""

    def test_out_of_order_ack_no_skip_on_reconnect(self, db) -> None:
        """ACK a higher seq before a lower seq → reconnect must not skip the lower seq."""
        conn = eb_app.app.state.db

        # Publish three events
        seq1, _, _ = insert_event(
            conn, "evt-oof-1", "t", json.dumps({"data": "1"}), "p", "2026-10-04T00:00:00Z"
        )
        seq2, _, _ = insert_event(
            conn, "evt-oof-2", "t", json.dumps({"data": "2"}), "p", "2026-10-04T00:00:00Z"
        )
        seq3, _, _ = insert_event(
            conn, "evt-oof-3", "t", json.dumps({"data": "3"}), "p", "2026-10-04T00:00:00Z"
        )
        assert seq1 < seq2 < seq3

        # ACK out of order: ack seq3 before seq2
        _, newly_acked_c, _ = ack_event_for_consumer(
            conn, "evt-oof-3", "oof-consumer", "2026-10-04T00:00:00Z"
        )
        assert newly_acked_c
        _, newly_acked_b, _ = ack_event_for_consumer(
            conn, "evt-oof-2", "oof-consumer", "2026-10-04T00:00:00Z"
        )
        assert newly_acked_b

        # Verify offset jumped to seq3 (high-water mark)
        offset = get_consumer_offset(conn, "oof-consumer")
        assert offset == seq3

        # Compute resume position — should be seq1 (lowest unacked <= offset)
        # Note: seq1 has no consumer_delivery record, so it won't appear in the join
        # We need to handle this case separately
        resume_pos = get_resume_position(conn, "oof-consumer")
        assert resume_pos == seq1  # lowest unacked event

    def test_ordered_ack_baseline(self, db) -> None:
        """Ordered ACKs: reconnect resumes from stored offset + 1 (fast-forward)."""
        conn = eb_app.app.state.db

        # Publish two events
        seq1, _, _ = insert_event(
            conn, "evt-ok-1", "t", json.dumps({"data": "1"}), "p", "2026-10-04T00:00:00Z"
        )
        seq2, _, _ = insert_event(
            conn, "evt-ok-2", "t", json.dumps({"data": "2"}), "p", "2026-10-04T00:00:00Z"
        )

        # ACK in order
        _, newly_acked_a, _ = ack_event_for_consumer(
            conn, "evt-ok-1", "ok-consumer", "2026-10-04T00:00:00Z"
        )
        assert newly_acked_a
        _, newly_acked_b, _ = ack_event_for_consumer(
            conn, "evt-ok-2", "ok-consumer", "2026-10-04T00:00:00Z"
        )
        assert newly_acked_b

        # Verify offset is seq2
        offset = get_consumer_offset(conn, "ok-consumer")
        assert offset == seq2

        # Resume position should be seq2 + 1 (all events up to offset are acked)
        resume_pos = get_resume_position(conn, "ok-consumer")
        assert resume_pos == seq2 + 1

    def test_get_resume_position_no_offset(self, db) -> None:
        """No prior offset: resume position returns 0 (start from beginning)."""
        conn = eb_app.app.state.db

        # No events published, no offset exists
        resume_pos = get_resume_position(conn, "new-consumer")
        assert resume_pos == 0
```

**Important note**: The implementation must also account for events that have NO `consumer_delivery` record at all (events that were never attempted for delivery to this consumer). These should be treated as unacked. The query needs adjustment:

```sql
-- Revised: include events with no consumer_delivery record
SELECT MIN(e.seq) FROM events e
LEFT JOIN consumer_delivery cd ON e.event_id = cd.event_id
  AND cd.consumer_id = ?
WHERE (cd.acked_at IS NULL OR cd.event_id IS NULL)
  AND e.seq <= ?
```

## Compatibility considerations

- New test file — no backward compatibility risk.
- Test names follow the convention `{test_name}_{scenario}` for clarity.

## Security considerations

- No security impact. Tests run against an isolated SQLite database.
- No production data exposure.

## Rollback considerations

- Delete the test file if the underlying implementation changes.
- If a test depends on the silent-off behavior being preserved, revert only that test adjustment.

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| tests/eventbus/test_eventbus_restart_resume.py | Unit (behavior lock + regression) | `uv run pytest tests/eventbus/test_eventbus_restart_resume.py -v` | Passes before and after the edit |
| Full suite | Regression | `uv run pytest tests/` | No new failures |

## Completion criteria

- [ ] `test_out_of_order_ack_no_skip_on_reconnect` passes: out-of-order ACK followed by reconnect delivers all unacked events.
- [ ] `test_ordered_ack_baseline` passes: ordered ACKs resume from stored offset + 1.
- [ ] `test_get_resume_position_no_offset` passes: no prior offset returns 0.
- [ ] All existing tests continue to pass (behavior lock).
- [ ] `ruff format` and `ruff check` pass cleanly on the modified file.

## Out of scope

- Changes to `delivery_repo.py` (separate procedure document).
- Changes to `subscribe_route.py` (separate procedure document).
- Adding an index on `consumer_delivery(acked_at)` (separate procedure document).
- Documentation updates beyond function docstrings.

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
- **Source issue**: issues/20261004-095313_eventbus001_eventbus-out-of-order-ack-skips-lower-seq-events-on-resume.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261004-100000_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261005-073241
- **Related target files**: tests/eventbus/test_eventbus_restart_resume.py
