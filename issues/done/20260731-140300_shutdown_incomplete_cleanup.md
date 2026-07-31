---
title: "システム終了時の不完全なクリーンアップ"
created: 2026-07-31
severity: medium
area: scripts/agent/repl.py
status: open
---

## 概要

`repl.py` の `_cleanup()` でシステム終了時に実行中のターンやストリーミングが中断されるが、`turn_state` や `conversation_state` のクリーンアップがない。メモリリークやDB接続リークの可能性がある。

## 証拠

```python
# scripts/agent/repl.py

def _cleanup(self):
    # MCPサーバー切断のみ
    await self._disconnect_mcp_servers()
```

## 影響

- メモリリーク（実行中のストリーム、非同期タスク）
- DB接続のリーク（未コミット/ロールバック）
- ファイルディスクリプターのリーク
- SIGINT/SIGTERMで強制終了した場合に不整合状態が残る

## 再現手順

1. エージェントREPLで長い処理を実行中
2. Ctrl+C（SIGINT）を送信
3. `_cleanup()` が呼ばれるが、MCPサーバー切断のみ
4. 残りのリソースが解放されないままプロセスが終了

## 修正案

```python
async def _cleanup(self):
    try:
        # 実行中のターンをキャンセル
        if hasattr(self, 'current_turn') and self.current_turn:
            self.current_turn.cancel()
        
        # ストリーミングを閉じる
        if hasattr(self, '_stream_response_task') and self._stream_response_task:
            self._stream_response_task.cancel()
            try:
                await self._stream_response_task
            except asyncio.CancelledError:
                pass
        
        # DBセッションをコミット/ロールバック
        if hasattr(self, 'db_session') and self.db_session:
            try:
                await self.db_session.commit()
            except Exception:
                await self.db_session.rollback()
        
        # MCPサーバー切断
        await self._disconnect_mcp_servers()
    finally:
        # 最後のクリーンアップ
        await super()._cleanup()
```

## 関連ファイル

- `scripts/agent/repl.py`: _cleanup()
- `scripts/agent/lifecycle.py`: AgentLifecycle
