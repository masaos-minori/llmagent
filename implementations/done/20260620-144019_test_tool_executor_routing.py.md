# Implementation: tests/test_tool_executor_routing.py (update — cache key regression test)

## Goal

Add a regression test to `tests/test_tool_executor_routing.py` that verifies the cache
key format is plain string concatenation (`f"{tool_name}:{json_dumps(args)}"`), NOT
MD5-hashed, and that identical args always produce identical keys.

## Scope

**In:**
- Add one new test class `TestCacheKeyFormat` with test functions verifying:
  - Cache key is a plain string, not a hex digest
  - Identical args produce identical cache keys
  - Different args or tool names produce different cache keys

**Out:**
- Changing existing cache tests
- Modifying the cache key implementation

## Assumptions

- `ToolExecutor._cache_key()` (or equivalent) is the method that generates cache keys
  using `f"{tool_name}:{_json_dumps(args)}"` (plain string, no MD5)
- The existing `test_cache_hit_returns_empty_x_request_id` at line 382 provides a
  pattern for the test setup (using `_make_executor()` helper)
- `_json_dumps` is accessible via `from shared.tool_executor import _json_dumps` or
  the cache key can be reconstructed manually for assertion

## Implementation

### Target file

`tests/test_tool_executor_routing.py`

### Procedure

1. Read the file to identify the class structure and where to append the new class
2. Append `TestCacheKeyFormat` after the last existing test class
3. Test method accesses the cache key via one of:
   - Direct call to `ToolExecutor._cache_key(tool_name, args)` if it exists as a method
   - Reconstructing `f"{tool_name}:{orjson.dumps(args, option=orjson.OPT_SORT_KEYS).decode()}"` 
     and asserting it does NOT look like a hex digest (no 32-char hex string)

### Method

```python
class TestCacheKeyFormat:
    def test_cache_key_is_plain_string_not_md5(self) -> None:
        """Cache key must use plain string format, not MD5 hex digest."""
        ex = _make_executor()
        key = ex._cache_key("read_text_file", {"path": "/tmp/f.txt"})
        # Plain string contains the tool name and colon separator
        assert key.startswith("read_text_file:")
        # Must NOT be a 32-character hex digest (MD5 format)
        assert not re.fullmatch(r"[0-9a-f]{32}", key)

    def test_cache_key_identical_args_produce_identical_key(self) -> None:
        """Same tool + same args must always produce the same cache key."""
        ex = _make_executor()
        args = {"path": "/tmp/f.txt", "mode": "r"}
        key1 = ex._cache_key("read_text_file", args)
        key2 = ex._cache_key("read_text_file", args)
        assert key1 == key2

    def test_cache_key_different_tool_produces_different_key(self) -> None:
        """Different tool names must produce different cache keys for same args."""
        ex = _make_executor()
        args = {"path": "/tmp/f.txt"}
        key1 = ex._cache_key("read_text_file", args)
        key2 = ex._cache_key("write_file", args)
        assert key1 != key2

    def test_cache_key_different_args_produce_different_key(self) -> None:
        """Different args must produce different cache keys for same tool."""
        ex = _make_executor()
        key1 = ex._cache_key("read_text_file", {"path": "/tmp/a.txt"})
        key2 = ex._cache_key("read_text_file", {"path": "/tmp/b.txt"})
        assert key1 != key2
```

### Details

- If `ToolExecutor` does not expose a `_cache_key()` method, inspect the cache
  implementation in `tool_executor.py` to find the key construction site and adapt
  the test accordingly (e.g., execute a call and inspect `ex._cache.keys()`)
- `re` is already imported in the test file (check first); if not, add it
- `_make_executor()` helper already exists in the file — use it as-is
- The `re.fullmatch(r"[0-9a-f]{32}", key)` assertion guards specifically against
  MD5 hex format (32 lowercase hex chars)

## Validation plan

| Check | Command | Expected |
|---|---|---|
| New class present | `grep -n "TestCacheKeyFormat" tests/test_tool_executor_routing.py` | 1 match |
| Cache key format test passes | `uv run pytest tests/test_tool_executor_routing.py::TestCacheKeyFormat -v` | all pass |
| Existing tests unaffected | `uv run pytest tests/test_tool_executor_routing.py -x -v` | all pass |
| Lint | `uv run ruff check tests/test_tool_executor_routing.py` | 0 errors |
| Type check | `uv run mypy tests/test_tool_executor_routing.py` | 0 errors |
