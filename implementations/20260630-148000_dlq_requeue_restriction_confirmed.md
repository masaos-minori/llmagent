## Goal
- Confirm DLQ requeue restriction to events currently in DLQ is already implemented

## Findings
- `db.py::requeue_event()`: Both SELECT and UPDATE use `dlq_at IS NOT NULL` as guard ✓
- `app.py::dlq_requeue`: Follow-up SELECT distinguishes 409 (event exists, not in DLQ) vs 404 (not found) ✓
- Tests: 19 tests pass including `test_requeue_non_dlq_event_fails` (409), `test_requeue_unknown_event_returns_404` (404), and concurrent requeue test ✓
- Docs: 409 response documented at L180, L184, L207 in `06_eventbus_02_http_api_and_runtime.md` ✓

## Conclusion
No changes needed — already implemented.
