---
title: "トークン使用量の急激な増加に対するループガードの脆弱性"
created: 2026-07-31
severity: high
area: scripts/agent/tool_loop_guard.py
status: open
---

## 概要

`tool_loop_guard.py` で同一ターン内で複数回のツール呼び出しがある場合、`current_tokens` が累積されるが、各ツール呼び出し間のトークン消費量が正確に追跡されていない可能性がある（特にストリーミングレスポンスの場合）。

## 証拠

```python
# scripts/agent/tool_loop_guard.py

class ToolLoopGuard:
    def __init__(self, max_tokens: int):
        self.max_tokens = max_tokens
        self.current_tokens = 0
    
    async def check_and_record(self, tool_call_id: str, response_tokens: int):
        self.current_tokens += response_tokens
        if self.current_tokens > self.max_tokens:
            raise ToolLoopError("Token limit exceeded")
```

## 影響

- ストリーミングレスポンスの場合、`response_tokens` が正確に計算されない
- トークン制限超過時にループガードが誤検出または未検出
- 高額なLLM呼び出しの制御が不十分

## 再現手順

1. トークン制限を低い値に設定（例: 1000トークン）
2. 複数回のツール呼び出しを行うターンを実行
3. ストリーミングレスポンスで `response_tokens` が過小評価される
4. トークン制限超過が検知されないまま処理が続行

## 修正案

```python
async def check_and_record(self, tool_call_id: str, response_tokens: int):
    # ストリーミングレスポンスの場合は実際のトークン使用量を記録
    actual_tokens = await self._get_actual_token_usage(tool_call_id)
    if actual_tokens is None:
        actual_tokens = response_tokens  # フォールバック
    
    self.current_tokens += actual_tokens
    if self.current_tokens > self.max_tokens:
        logger.warning(f"Token limit approaching: {self.current_tokens}/{self.max_tokens}")
        raise ToolLoopError("Token limit exceeded")
```

ストリーミング中のリアルタイムトークン監視を追加することも検討する。

## 関連ファイル

- `scripts/agent/tool_loop_guard.py`: check_and_record(), current_tokens
- `scripts/agent/orchestrator.py`: stream_response()
