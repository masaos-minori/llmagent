---
title: "MCPサーバー初期化失敗の可視性不足"
created: 2026-07-31
severity: medium
area: scripts/agent/factory.py
status: open
---

## 概要

`factory.py` の `_initialize_mcp_servers()` で `return_exceptions=True` を使用しているため、一部のMCPサーバーが失敗しても気づかない。後続のツール呼び出しで予期せぬエラーが発生する。

## 証拠

```python
# scripts/agent/factory.py

async def _initialize_mcp_servers(self):
    tasks = [self._init_single_server(server) for server in servers]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # 例外が返されてもログ出力されていない可能性
```

## 影響

- 特定のMCPサーバーが起動していないことに気づかない
- ツール呼び出しで `ConnectionRefusedError` や `TimeoutError` が発生
- デバッグが困難（どのサーバーが失敗したか不明）

## 再現手順

1. 3つのMCPサーバーを構成（A, B, C）
2. サーバーBが起動しない状態にする
3. エージェントREPLを起動
4. サーバーAとCは正常に初期化される
5. サーバーBの失敗が検知されず、ツール呼び出しでエラー発生

## 修正案

```python
async def _initialize_mcp_servers(self):
    tasks = [self._init_single_server(server) for server in servers]
    results = await asyncio.gather(*tasks, return_exceptions=False)
    
    # または、個別に処理して失敗を明示的にログ出力
    failed_servers = []
    for task in tasks:
        result = await task
        if isinstance(result, Exception):
            logger.error(f"MCP server initialization failed: {result}")
            failed_servers.append(result.server_name)
    
    if failed_servers:
        raise RuntimeError(
            f"Failed to initialize MCP servers: {failed_servers}"
        )
```

## 関連ファイル

- `scripts/agent/factory.py`: _initialize_mcp_servers(), _init_single_server()
- `scripts/agent/startup.py`: エージェント起動シーケンス
