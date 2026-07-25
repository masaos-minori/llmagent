# Ephemeral メッセージのフィルタリングが2回実行される

## Priority

Low

## Summary

`_clear_previous_turn_ephemeral_messages()` と `_handle_history_compression()` の両方で `_ephemeral` / `_memory_injected` メッセージのフィルタリングが実行される。冗長だが機能的には問題ない。

## Problem

`orchestrator.py:526-537` (turn start):

```python
def _clear_previous_turn_ephemeral_messages(self) -> None:
    ctx = self._ctx
    ctx.conv.history = [
        m for m in ctx.conv.history
        if not m.get("_ephemeral") and not m.get("_memory_injected")
    ]
```

`orchestrator.py:396-402` (history compression):

```python
ctx.session.replace_messages([
    m for m in ctx.conv.history
    if not m.get("_ephemeral") and not m.get("_memory_injected")
])
```

両方とも同じ条件で同じメッセージをフィルタリングしている。

## Root Cause

`_clear_previous_turn_ephemeral_messages()` は turn 開始時に前回の ephemeral メッセージを削除するため。`_handle_history_compression()` は圧縮後のメッセージを保存する際にフィルタリングするため。

## Fix Direction

`_handle_history_compression()` のフィルタリングを削除し、`_clear_previous_turn_ephemeral_messages()` のみを信頼するようにする。または、フィルタリングロジックを共通関数に抽出する。

## Acceptance Criteria

- [ ] ephemeral メッセージのフィルタリングが1回の実行になる
- [ ] 両方のパスで同じ結果になる
- [ ] 冗長なフィルタリングが削除される
