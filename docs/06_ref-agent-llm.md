# llm_client.py

## 1. 機能概要

`AgentREPL` から抽出した LLM HTTP 通信レイヤー。SSE ストリーミング・指数バックオフリトライ・ペイロード構築・レスポンス整形を担当。`AgentREPL().run()` で `LLMClient` インスタンスを生成し、`self._llm` として保持。

## 2. API

```python
from llm_client import LLMClient

client = LLMClient(
    http=httpx.AsyncClient(...),
    max_retries=3,
    retry_base_delay=1.0,
    temperature=0.2,
    max_tokens=1024,
)
response = await client.stream(url, history, tool_defs)
```

| メソッド | 説明 |
|---|---|
| `request_with_retry(url, payload) -> httpx.Response` | 指数バックオフリトライ付き POST。HTTP 429 / 503 と接続エラーのみリトライ |
| `build_payload(history, tool_defs, stream=False) -> dict` | `messages` / `tools` / `temperature` / `max_tokens` を含むリクエストボディを生成 |
| `call(url, history, tool_defs) -> dict` | 非ストリーミング LLM 呼び出し。`request_with_retry` を内部使用 |
| `stream(url, history, tool_defs) -> dict` | SSE ストリーミング LLM 呼び出し。エラー時は `call()` にフォールバック |
| `extract_message(response) -> tuple[dict, str \| None]` (static) | `choices[0].message` と `finish_reason` を取り出す。フィールド欠如時は `ValueError` |

統計属性:
- `stat_retries: int` — セッション通算リトライ回数

## 3. 使用スクリプト

| スクリプト | 使用箇所 |
|---|---|
| `agent_repl.py` | `self._llm = LLMClient(...)` を `run()` で生成し、LLM 呼び出しメソッドへ委譲 |
