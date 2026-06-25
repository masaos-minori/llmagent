# Implementation: tests/test_eventbus_dlq.py — update for delivery_failure_count (req #28)

## Goal

Update existing DLQ tests to use `delivery_failure_count` instead of `retry_count` for simulating DLQ-eligible events, after the schema migration.

## Scope

- Replace all `UPDATE events SET retry_count = 2` with `UPDATE events SET delivery_failure_count = 2`
- Update `test_requeue_increments_retry_count` to check `dlq_requeue_count` instead of `retry_count`
- All other test logic remains unchanged

## Assumptions

- req #28 schema.sql is applied (both columns exist)
- `promote_to_dlq()` now uses `delivery_failure_count >= max_retry` (req #24/28 change)
- `retry_count` column still exists (deprecated) but is no longer used in tests

## Implementation

### Target file

`tests/test_eventbus_dlq.py`

### Procedure

1. Replace all `SET retry_count = 2` with `SET delivery_failure_count = 2` (appears 4 times)
2. In `test_requeue_increments_retry_count`: update assertion from `retry_count == 3` to `dlq_requeue_count == 1`
3. Rename `test_requeue_increments_retry_count` to `test_requeue_increments_dlq_requeue_count`

### Method

Edit existing test file with targeted replacements.

### Details

**Lines to replace (pattern: `SET retry_count = 2`):**

In `test_dlq_promotion_when_retry_exhausted` (line ~52):
```python
# before
db.execute("UPDATE events SET retry_count = 2 WHERE event_id = ?", (ev["event_id"],))
# after
db.execute("UPDATE events SET delivery_failure_count = 2 WHERE event_id = ?", (ev["event_id"],))
```

Same replacement needed in `test_dlq_list` (line ~73), `test_dlq_requeue` (line ~93), and `test_requeue_increments_retry_count` (line ~113).

In `test_requeue_increments_retry_count` (rename + update assertion):
```python
def test_requeue_increments_dlq_requeue_count(client: TestClient, tmp_path: Path) -> None:
    ...
    # before
    assert row["retry_count"] == 3
    # after
    assert row["dlq_requeue_count"] == 1
    assert row["dlq_at"] is None
```

Also update the `SET retry_count = 2` near the end of that test (line ~130) to `SET delivery_failure_count = 2`.

Note: `test_dlq_promotion_when_retry_exhausted` passes `max_retry=2` to `promote_to_dlq()` directly; this still works because the function now uses `delivery_failure_count >= max_retry`.

## Validation plan

| Check | Command | Target |
|---|---|---|
| No old field references | `grep "retry_count" tests/test_eventbus_dlq.py` | 0 results |
| Tests pass | `uv run pytest tests/test_eventbus_dlq.py -v` | all pass |
| Lint | `ruff check tests/test_eventbus_dlq.py` | 0 errors |
| Type check | `mypy tests/test_eventbus_dlq.py` | no errors |
