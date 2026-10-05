## Goal

Update `subscribe_route.py::subscribe()` to use the new `get_resume_position()` function instead of raw `get_consumer_offset()`, while preserving the existing `since_seq` precedence logic discovered during adversarial validation.

## Scope

- Modify `scripts/eventbus/subscribe_route.py`: replace `get_consumer_offset(db, consumer_id)` with `get_resume_position(db, consumer_id)` in the reconnect path; preserve the `since_seq` parameter precedence.

## Assumptions

- The `since_seq` parameter (from Last-Event-ID header) takes precedence over consumer offset — confirmed by source inspection at lines 123-126.
- `get_resume_position()` always returns a value >= `since_seq` when called with a consumer that has prior offsets.
- The `since_seq` parameter is already available as a Query parameter at line 34.

## Design decisions

- Apply the low-water-mark logic AFTER `since_seq` determination, not as a replacement for it. This preserves the existing SSE reconnection semantics where clients can specify their last known event.
- Import `get_resume_position` locally within the function body to avoid circular import issues.

## Alternatives considered

- Replace the entire resume position logic with `get_resume_position()`: rejected because it would ignore the `since_seq` parameter, breaking client-side reconnection semantics.
- Merge `since_seq` into `get_resume_position()`: rejected because `since_seq` is a client-specified value that must take precedence; mixing it into the database query would conflate client intent with server state.

## Implementation

### Target file

`scripts/eventbus/subscribe_route.py`

### Procedure

Replace `get_consumer_offset(db, consumer_id)` with `get_resume_position(db, consumer_id)` in the reconnect path. Preserve the `since_seq` parameter precedence logic.

### Method

1. In `subscribe_route.py::subscribe()`: replace the call to `get_consumer_offset` with `get_resume_position`.
2. Ensure the `since_seq` parameter precedence is preserved (lines 123-126).

### Details

**Change — `subscribe_route.py::subscribe()` (lines 123–126):**

Before:
```python
# REQ-004: Implement precedence: since_seq > consumer offset > Last-Event-ID
start_seq = since_seq
if consumer_id and start_seq == 0:
    start_seq = get_consumer_offset(db, consumer_id)
```

After:
```python
# REQ-004: Implement precedence: since_seq > resume position > Last-Event-ID
# get_resume_position computes max(lowest_unacked_seq, stored_offset)
# ensuring no unacked event is skipped on reconnect after out-of-order ACKs.
start_seq = since_seq
if consumer_id and start_seq == 0:
    from eventbus.delivery_repo import get_resume_position
    start_seq = get_resume_position(db, consumer_id)
```

**Important**: Per adversarial validation finding, the `since_seq` parameter must retain its precedence. The low-water-mark logic applies AFTER `since_seq` determination, not as a replacement for it. If `since_seq` is non-zero (client specified), it takes priority over both the consumer offset and the low-water-mark computation.

## Compatibility considerations

- The `since_seq` parameter precedence is preserved — no behavioral change for clients that specify a Last-Event-ID.
- For consumers without a prior offset, behavior changes: they now receive all events from seq=1 (instead of starting from the beginning with no offset).
- For consumers with a prior offset but out-of-order ACKs, behavior changes: they now receive previously skipped events on reconnect.

## Security considerations

- No security impact. The function reads from existing tables without modifying data.
- The SQL query uses parameterized queries throughout — no injection risk.

## Rollback considerations

- Revert to `get_consumer_offset(db, consumer_id)` to restore the original high-water-mark-only behavior.
- Remove the local import of `get_resume_position`.

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| scripts/eventbus/subscribe_route.py | Static: format, lint, type | `uv run ruff format` / `ruff check` / `uv run mypy` on the file | Clean; no new errors |
| tests/eventbus/test_eventbus_restart_resume.py | Integration (behavior lock + regression) | `uv run pytest tests/eventbus/test_eventbus_restart_resume.py -v` | Passes before and after the edit |
| Full suite | Regression | `uv run pytest tests/` | No new failures |
| Changed lines | Coverage | `uv run diff-cover coverage.xml --compare-branch=master --fail-under=90` | ≥ 90% on changed lines |

## Completion criteria

- [ ] `subscribe_route.py::subscribe()` calls `get_resume_position(db, consumer_id)` instead of `get_consumer_offset(db, consumer_id)`.
- [ ] The `since_seq` parameter precedence is preserved (non-zero `since_seq` takes priority).
- [ ] `ruff format` and `ruff check` pass cleanly on the modified file.
- [ ] `mypy` passes on the modified file.
- [ ] All affected integration tests pass.

## Out of scope

- Changes to `delivery_repo.py` (separate procedure document).
- Adding an index on `consumer_delivery(acked_at)` (separate procedure document).
- Documentation updates beyond function docstrings.
- Changes to the `since_seq` parameter handling (existing semantics preserved).

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
- **Requirement ID**: REQ-001
- **Source issue**: issues/20261004-095313_eventbus001_eventbus-out-of-order-ack-skips-lower-seq-events-on-resume.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261004-100000_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261005-073241
- **Related target files**: scripts/eventbus/subscribe_route.py
