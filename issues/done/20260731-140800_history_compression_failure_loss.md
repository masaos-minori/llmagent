---
title: "LLMベースの会話圧縮失敗時のメッセージ損失"
created: 2026-07-31
severity: high
area: scripts/agent/history.py
status: open
---

## 概要

`history.py` でLLMによる会話履歴圧縮が失敗した場合、元のメッセージが失われる。`_generate_summary()` の戻り値のNoneハンドリングがない。

## 証拠

```python
# scripts/agent/history.py

async def compress_history(self):
    summary = await self._generate_summary(messages)
    compressed = [summary] + recent_messages[-window_size:]
```

## 影響

- LLM呼び出し失敗時に会話履歴が完全に消失
- ユーザーの入力とエージェントの応答が失われる
- 回復不能なデータ損失

## 再現手順

1. 長い会話を開始
2. LLM呼び出し中にネットワーク障害やタイムアウトが発生
3. `_generate_summary()` がNoneまたは例外を返す
4. 元のメッセージが失われ、圧縮後の状態が空になる

## 修正案

```python
async def compress_history(self):
    try:
        summary = await self._generate_summary(messages)
        
        if summary is None:
            # 圧縮失敗時は元のメッセージを保持
            logger.warning("History compression failed, keeping original messages")
            return
        
        compressed = [summary] + recent_messages[-window_size:]
        return compressed
    
    except Exception as e:
        # 圧縮失敗時は元のメッセージを保持
        logger.error(f"History compression error: {e}")
        return messages
```

圧縮失敗時は元のメッセージを保持し、データ損失を防ぐ。また、圧縮成功時のみDBに保存するようにする。

## 関連ファイル

- `scripts/agent/history.py`: compress_history(), _generate_summary()
- SQLite: 会話履歴永続化
