# Implementation: tests/test_tool_loop_guard.py — ハッシュ統一・update_errors・RETRY_HINT テスト

**Plan:** `plans/20260623-230000_plan.md` (Phase 5)
**Target:** `tests/test_tool_loop_guard.py`

---

## 追加テストケース

### 1. `_canonical_key` ハッシュ統一テスト

`check_dedup` と `check_retry` が同一の `_canonical_key()` を使うことで、引数の JSON キー順序が異なっても同一キーと判定されることを検証する。

```python
class TestCanonicalKeyConsistency:
    def test_same_args_different_json_order_produce_same_key(self) -> None:
        """check_dedup and check_retry agree even when JSON key order differs."""
        from agent.tool_loop_guard import ToolLoopGuard
        key1 = ToolLoopGuard._canonical_key("write_file", '{"path": "a", "content": "b"}')
        key2 = ToolLoopGuard._canonical_key("write_file", '{"content": "b", "path": "a"}')
        assert key1 == key2

    def test_different_args_produce_different_key(self) -> None:
        from agent.tool_loop_guard import ToolLoopGuard
        key1 = ToolLoopGuard._canonical_key("write_file", '{"path": "a"}')
        key2 = ToolLoopGuard._canonical_key("write_file", '{"path": "b"}')
        assert key1 != key2

    def test_invalid_json_falls_back_to_empty_dict(self) -> None:
        from agent.tool_loop_guard import ToolLoopGuard
        from shared.tool_executor import tool_hash_key
        key = ToolLoopGuard._canonical_key("write_file", "INVALID_JSON")
        expected = tool_hash_key("write_file", {})
        assert key == expected
```

### 2. `update_errors` 部分失敗テスト

```python
class TestUpdateErrorsPartialFailure:
    def test_all_failed_increments(self) -> None:
        from agent.tool_loop_guard import ToolLoopGuard
        assert ToolLoopGuard.update_errors(2, 3, 3) == 3  # all failed → increment

    def test_all_succeeded_resets(self) -> None:
        from agent.tool_loop_guard import ToolLoopGuard
        assert ToolLoopGuard.update_errors(2, 0, 3) == 0  # all succeeded → reset

    def test_partial_failure_maintains_count(self) -> None:
        from agent.tool_loop_guard import ToolLoopGuard
        assert ToolLoopGuard.update_errors(2, 1, 3) == 2  # partial failure → maintain
```

### 3. `check_retry` RETRY_HINT テスト

```python
class TestCheckRetryHint:
    def test_check_retry_diagnostics_uses_retry_hint(self, mock_ctx) -> None:
        """check_retry stores RETRY_HINT (not DEDUP_HINT) in diagnostics."""
        from agent.tool_loop_guard import RETRY_HINT, ToolLoopGuard
        guard = ToolLoopGuard(mock_ctx)
        saved = []
        mock_ctx.diagnostics.save = lambda *a: saved.append(orjson.loads(a[2]))

        from shared.tool_executor import tool_hash_key
        key = tool_hash_key("write_file", {"path": "a"})
        failed_calls = {key}
        message: LLMMessage = {
            "role": "assistant",
            "tool_calls": [{"function": {"name": "write_file", "arguments": '{"path":"a"}'}}],
        }
        result = guard.check_retry(failed_calls, message)
        assert result is not None
        assert any(d.get("hint") == RETRY_HINT for d in saved)
```

**注意:** `mock_ctx` は既存 conftest / fixture を使用。`diagnostics.save` のシグネチャを確認してから実装する。

---

## 完了条件

```bash
uv run pytest tests/test_tool_loop_guard.py::TestCanonicalKeyConsistency -v
# → 3件 PASSED

uv run pytest tests/test_tool_loop_guard.py::TestUpdateErrorsPartialFailure -v
# → 3件 PASSED

uv run pytest tests/test_tool_loop_guard.py -v
# → 全件通過 (既存テスト含む)
```
