---
title: "LLMストリーミング例外時のツールループガードクリーンアップ欠如"
created: 2026-07-31
severity: high
area: scripts/agent/orchestrator.py
status: open
---

## 概要

`orchestrator.py` の `stream_response()` でLLMストリーミング中に例外が発生した場合、`tool_loop_guard` が `running_tool` をロックしたままになる可能性がある。`finally` ブロックでのクリーンアップがないため、以降のツール呼び出しがブロックされる。

## 証拠

```python
# scripts/agent/orchestrator.py

try:
    async for chunk in response:
        yield chunk
except Exception as e:
    # エラー発生時にストリームが中断されるが、
    # ツールループガードの状態がクリーンアップされない可能性
```

## 影響

- ストリーミング例外発生後、次のターンでツール呼び出しが無限待機またはタイムアウト
- エージェントREPLがハングする
- 再起動しない限り復旧しない

## 再現手順

1. LLMストリーミング中にネットワーク障害やタイムアウトをシミュレート
2. 例外が発生しストリームが中断される
3. 次のツール呼び出しを試みる
4. `running_tool` がロックされたままになり、ツール呼び出しがブロックされる

## 修正案

```python
try:
    async for chunk in response:
        yield chunk
except Exception as e:
    raise
finally:
    # ツールループガードの状態をクリーンアップ
    if hasattr(self, 'guard') and self.guard:
        self.guard.reset_running_tool()
```

または、`stream_response()` の呼び出し元で `finally` ブロックを追加し、`tool_loop_guard` の状態をリセットする。

## 関連ファイル

- `scripts/agent/orchestrator.py`: stream_response()
- `scripts/agent/tool_loop_guard.py`: running_tool ロック/アンロック
