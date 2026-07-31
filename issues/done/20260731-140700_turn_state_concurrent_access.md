---
title: "TurnStateの同時アクセスによる競合条件"
created: 2026-07-31
severity: medium
area: scripts/agent/context.py
status: open
---

## 概要

`context.py` の `TurnState` で複数のターンが同時に読み書きする場合、`tool_calls` リストへの同時アクセスで競合が発生する可能性がある。

## 証拠

```python
# scripts/agent/context.py

class TurnState:
    def __init__(self):
        self.turn_count = 0
        self.tool_calls = []
    
    def add_tool_call(self, call_id: str):
        self.tool_calls.append(call_id)  # 非アトミックな操作
```

## 影響

- 複数スレッドからの同時アクセスで `tool_calls` が壊れる可能性
- データ損失（一部の変更が反映されない）
- 予期せぬエラー（リスト操作の競合）

## 再現手順

1. 複数のスレッドが同時に `add_tool_call()` を呼び出す
2. リストへの追加が同時に実行される
3. 一部の変更が上書きされてデータ損失が発生

## 修正案

```python
import asyncio

class TurnState:
    def __init__(self):
        self.turn_count = 0
        self.tool_calls = []
        self._lock = asyncio.Lock()
    
    async def add_tool_call(self, call_id: str):
        async with self._lock:
            self.tool_calls.append(call_id)
    
    async def get_tool_calls(self) -> List[str]:
        async with self._lock:
            return list(self.tool_calls)  # コピーを返す
```

または、アトミックなデータ構造（`queue.Queue`など）を使用する。

## 関連ファイル

- `scripts/agent/context.py`: TurnState, tool_calls
- Python asyncio.Lock
