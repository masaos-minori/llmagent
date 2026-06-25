# tests/test_diagnostic_store.py — add tests for new convenience methods

**Plan:** `plans/20260625-094407_plan.md` (req #65)
**Target:** `tests/test_diagnostic_store.py`

## What to add

Add a new test class after existing tests. The pattern follows `save_serialization_event`
tests already in the file.

```python
class TestConvenienceMethods:
    def test_save_partial_completion(self, store, session_id) -> None:
        store.save_partial_completion(
            session_id=session_id,
            turn=3,
            reason="timeout",
            content_length=1024,
        )
        rows = store.fetch_by_kind(session_id, "partial_completion")
        assert len(rows) == 1
        payload = orjson.loads(rows[0]["content"])
        assert payload["turn"] == 3
        assert payload["reason"] == "timeout"
        assert payload["content_length"] == 1024

    def test_save_transport_failure(self, store, session_id) -> None:
        store.save_transport_failure(
            session_id=session_id,
            tool_name="read_text_file",
            server_key="file_read",
            error_msg="Connection refused",
        )
        rows = store.fetch_by_kind(session_id, "transport_failure")
        assert len(rows) == 1
        payload = orjson.loads(rows[0]["content"])
        assert payload["tool_name"] == "read_text_file"
        assert payload["server_key"] == "file_read"

    def test_save_loop_guard_hint(self, store, session_id) -> None:
        store.save_loop_guard_hint(
            session_id=session_id,
            reason="cycle_detected",
            turn_count=7,
        )
        rows = store.fetch_by_kind(session_id, "loop_guard_hint")
        assert len(rows) == 1
        payload = orjson.loads(rows[0]["content"])
        assert payload["reason"] == "cycle_detected"
        assert payload["turn_count"] == 7

    def test_fetch_by_kind_returns_empty_for_unknown_kind(self, store, session_id) -> None:
        rows = store.fetch_by_kind(session_id, "nonexistent_kind")
        assert rows == []

    def test_fetch_by_kind_filters_by_kind(self, store, session_id) -> None:
        store.save_partial_completion(session_id=session_id, turn=1, reason="t", content_length=10)
        store.save_transport_failure(session_id=session_id, tool_name="t", server_key="s", error_msg="e")
        partial_rows = store.fetch_by_kind(session_id, "partial_completion")
        transport_rows = store.fetch_by_kind(session_id, "transport_failure")
        assert len(partial_rows) == 1
        assert len(transport_rows) == 1
```

Note: Verify the `store` and `session_id` fixture names match the existing test file pattern.
If the existing fixtures are named differently, adapt accordingly.

## Validation

```
uv run pytest tests/test_diagnostic_store.py -v
```
