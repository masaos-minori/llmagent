# MCPツールディスカバリとHTTPライフサイクルのタイムアウト引数の不一致

## 深刻度: 低〜中程度

## 概要

`McpToolDiscovery._fetch_server_tools()` で `timeout=5.0` を直接渡しているが、
`McpServerLifecycle` では `httpx.Timeout(timeout=5.0)` を使用している。
`httpx.AsyncClient` が秒数を許容するか確認が必要。

## 該当コード

`scripts/agent/services/mcp_tool_discovery.py:113`

```python
resp = await self._ctx.services_required.http.get(
    f"{cfg.url}/v1/tools", timeout=5.0
)
```

`scripts/agent/http_lifecycle.py:250`

```python
httpx.Timeout(connect=5.0, read=5.0)
```

## 問題の詳細

1. `httpx.AsyncClient.get()` の `timeout` パラメータは、`float` または `httpx.Timeout` のいずれかを許容
2. `http_lifecycle.py` では `httpx.Timeout(connect=5.0, read=5.0)` を使用しているが、
   httpxの仕様では `connect` と `read` のみを同時に指定すると `ValueError` を発生する
3. `mcp_tool_discovery.py` では `timeout=5.0` を直接渡しており、これは `httpx.Timeout` オブジェクトではなく秒数
4. httpxのドキュメントによると、`timeout=5.0` は「すべての接続/読み込み/書き込みのタイムアウト」を意味する
5. 両者のセマンティクスが異なる：
   - `timeout=5.0`: 各操作ごとに5秒
   - `httpx.Timeout(connect=5.0, read=5.0)`: 本来は不正（4つのパラメータすべてが必要）

## 影響

- `http_lifecycle.py` の `httpx.Timeout(connect=5.0, read=5.0)` は httpxのAPI要件を満たさず、
  実際には `ValueError` を発生させる可能性がある
- タイムアウトのセマンティクスがモジュール間で不統一

## 修正案

`http_lifecycle.py` の修正:

```python
# Option 1: Single parameter form
httpx.Timeout(timeout=5.0)

# Option 2: All four parameters
httpx.Timeout(connect=5.0, read=5.0, write=5.0, idle=5.0)
```

`mcp_tool_discovery.py` も統一:

```python
resp = await self._ctx.services_required.http.get(
    f"{cfg.url}/v1/tools", timeout=httpx.Timeout(timeout=5.0)
)
```
