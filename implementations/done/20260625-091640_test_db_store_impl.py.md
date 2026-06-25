# Implementation: tests/test_db_store_impl.py

## Goal

Update `test_db_store_impl.py` to cover `tool_call_id` round-trip in `message_save` / `message_list`. Add tests for both `tool_call_id=None` (default) and `tool_call_id` with a value.

## Scope

- Target: `tests/test_db_store_impl.py`
- Update existing `message_save`/`message_list` test(s) to confirm `tool_call_id` is preserved
- Add `test_message_save_with_tool_call_id_round_trips` for explicit `tool_call_id` value

## Assumptions

1. Existing test uses an in-memory SQLite database; the `messages` table has `tool_call_id TEXT` column.
2. The test can call `message_save(..., tool_call_id="call_abc")` and then `message_list()` to verify the value is returned.
3. Existing tests that call `message_save` without `tool_call_id` still pass because the default is `None`.

## Implementation

### Target file
`tests/test_db_store_impl.py`

### Procedure
1. In the existing `message_save`/`message_list` test: assert `MessageRow.tool_call_id is None` for the default case.
2. Add new test `test_message_save_with_tool_call_id_round_trips`.

### Method

```python
def test_message_save_with_tool_call_id_round_trips(store, session_id):
    """tool_call_id is persisted and returned via message_list."""
    store.message_save(session_id, "tool", "", None, tool_call_id="call_abc123")
    rows = store.message_list(session_id)
    assert len(rows) == 1
    assert rows[0].tool_call_id == "call_abc123"

def test_message_save_default_tool_call_id_is_none(store, session_id):
    """Omitting tool_call_id stores None and message_list returns None."""
    store.message_save(session_id, "user", "hello", None)
    rows = store.message_list(session_id)
    assert rows[0].tool_call_id is None
```

### Details
- Use whatever fixture pattern existing tests use (`store`, `session_id`, or inline setup).
- `session_id` must be an existing sessions row; check how existing tests create sessions.

## Validation plan

| Check | Command | Target |
|---|---|---|
| Tests | `uv run pytest tests/test_db_store_impl.py -q` | all pass incl. new tests |
