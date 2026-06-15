# Implementation: Phase A3 — テストカバレッジ追加

## Goal

`cmd_session.py`、`cmd_memory.py`、`cmd_notes.py`、`cmd_db.py`、`cmd_context.py`
に characterization tests を追加し、各ファイルのカバレッジ ≥ 80% を達成する。
また `mcp/dispatch.py`、`tool_scheduler.py` の未テスト経路を補強する。

## Scope

**In**:
- `tests/test_cmd_session.py` (新規)
- `tests/test_cmd_memory.py` (新規)
- `tests/test_cmd_notes.py` (新規)
- `tests/test_cmd_db.py` (新規)
- `tests/test_cmd_context.py` (新規)
- `tests/test_mcp_dispatch.py` (既存 — tuple unpack テストの修正と追加)
- `tests/test_tool_scheduler.py` (新規)

**Out**: `tests/test_rag_stages.py` (既存)

## Assumptions

1. 既存テスト (`test_cmd_mcp.py`, `test_cmd_context_refactor.py`) のパターンを踏襲:
   - `MagicMock` による最小 `_Ctx` スタブ
   - `capsys` で stdout をキャプチャ
   - 各ミックスインクラスを直接インスタンス化
2. characterization tests は「現在の動作を記録する」テスト。
   リファクタ後に動作が変わったことを検出できれば十分。
3. `test_mcp_dispatch.py` の `TestDispatchTool` は既に
   `TypeError: cannot unpack non-iterable DispatchResult object` で失敗している。
   `DispatchResult` 属性アクセスに修正した上でカバレッジを追加する。

## Implementation

### Target files

上記7ファイル。ファイルごとに独立して作成・検証する。

### Procedure

1. `uv run coverage run -m pytest tests/ && coverage report` で現行カバレッジを測定
2. 各 cmd ファイルのソースを読み、主要パスを特定
3. スタブ + テストケースを記述
4. `uv run coverage run -m pytest tests/test_cmd_session.py && coverage report --include="*cmd_session*"` で 80% 確認
5. 他ファイルも同様に繰り返す

### Method

既存の `tests/test_cmd_mcp.py` のパターン:

```python
class _Ctx:
    def __init__(self, ...) -> None:
        self.cfg = MagicMock()
        self.services = MagicMock()
        self.session = MagicMock()
        ...

class _Session(_SessionMixin):
    def __init__(self, ctx: Any) -> None:
        self._ctx = ctx  # type: ignore[assignment]

class TestCmdSession:
    def test_list_no_sessions(self, capsys: Any) -> None:
        ctx = _Ctx(...)
        ctx.session.list_sessions.return_value = []
        s = _Session(ctx)
        s._cmd_session(" list")
        out = capsys.readouterr().out
        assert "No sessions" in out
```

### Details

**test_mcp_dispatch.py の修正**:

```python
# 変更前 (tuple unpack で TypeError)
result, is_error = await dispatch_tool(...)

# 変更後 (DispatchResult 属性アクセス)
res = await dispatch_tool(...)
assert res.output == "expected"
assert not res.is_error
```

**test_tool_scheduler.py の主要テストケース**:
- `requires_serial=True` のツールが単独グループになること
- `resource_scope` が同じ write ツールが同グループになること
- `is_write=False` のツールが parallel グループになること
- `ToolSpec` オブジェクトを使った入力（Phase 7 での変更済み）

## Validation plan

1. `uv run coverage run -m pytest tests/test_cmd_session.py -v` → all pass
2. `uv run coverage report --include="*cmd_session*"` → ≥ 80%
3. 他ファイルも同様に繰り返す
4. `uv run pytest tests/test_mcp_dispatch.py -v` → TypeError なし
