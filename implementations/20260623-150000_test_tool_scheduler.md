# Implementation: test_tool_scheduler.py — ToolSpec デフォルト値・スケジューリング動作テスト

**Plan:** `plans/20260623-104755_plan.md` (Step 3)
**Target:** `tests/test_tool_scheduler.py`

---

## 追加箇所

ファイル末尾 (L295 以降) に新規クラス `TestToolRunnerDefaultSpec` を追加する。

---

## 追加内容

```python
class TestToolRunnerDefaultSpec:
    """Verify ToolSpec defaults applied in _execute_with_dag().

    These tests replicate the ToolSpec construction logic in tool_runner.py
    to ensure the defaulting rules produce correct scheduling buckets.
    """

    def test_write_file_gets_resource_scope_from_constant(self) -> None:
        from shared.tool_constants import DELETE_TOOLS, SHELL_TOOLS, WRITE_TOOLS

        fn: dict = {"name": "write_file"}
        name = fn.get("name", "")
        _is_write = name in WRITE_TOOLS or name in DELETE_TOOLS
        _default_scope = name if _is_write else ""
        spec = ToolSpec(
            call_id="",
            name=name,
            resource_scope=fn.get("resource_scope", _default_scope),
            requires_serial=fn.get("requires_serial", False) or name in SHELL_TOOLS,
            is_write=_is_write,
        )
        assert spec.resource_scope == "write_file"
        assert spec.is_write is True
        assert spec.requires_serial is False

    def test_shell_run_gets_requires_serial(self) -> None:
        from shared.tool_constants import DELETE_TOOLS, SHELL_TOOLS, WRITE_TOOLS

        fn: dict = {"name": "shell_run"}
        name = fn.get("name", "")
        _is_write = name in WRITE_TOOLS or name in DELETE_TOOLS
        _default_scope = name if _is_write else ""
        spec = ToolSpec(
            call_id="",
            name=name,
            resource_scope=fn.get("resource_scope", _default_scope),
            requires_serial=fn.get("requires_serial", False) or name in SHELL_TOOLS,
            is_write=_is_write,
        )
        assert spec.requires_serial is True
        assert spec.is_write is False
        assert spec.resource_scope == ""

    def test_write_and_read_in_same_concurrent_batch(self) -> None:
        """With resource_scope set, write_file and read_text_file share concurrent_batch."""
        tool_meta = {
            "write_file": _meta(name="write_file", resource_scope="write_file", is_write=True),
            "read_text_file": _meta(name="read_text_file"),
        }
        calls = [
            _tc("write_file"),
            _tc("read_text_file"),
        ]
        _groups, metadata = build_execution_groups(calls, tool_meta)
        # write_first must be empty: both groups end up in the same concurrent batch
        assert len(metadata.concurrent_groups) == 1
        # one group for write_file scope, one for the parallel read
        assert len(metadata.concurrent_groups[0]) == 2
```

---

## 前提確認事項

- `_tc()`, `_meta()`, `build_execution_groups`, `ToolSpec` は既存の import / ヘルパーをそのまま利用
- `TestToolRunnerDefaultSpec` は `TestConcurrentGroups` クラスの直後 (L295) に追加
- `from shared.tool_constants import ...` は各テストメソッド内で import (テストの独立性を保つ)

---

## 完了条件

```bash
uv run pytest tests/test_tool_scheduler.py::TestToolRunnerDefaultSpec -v
# → 3件 PASSED

uv run pytest tests/test_tool_scheduler.py -v
# → 全件通過 (既存テスト含む)
```
