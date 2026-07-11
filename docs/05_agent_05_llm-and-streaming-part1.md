---
title: "Agent LLM and Streaming (Part 1)"
category: agent
tags:
  - agent
  - llm
  - streaming
  - response
related:
  - 05_agent_00_document-guide.md
source:
  - 05_agent_05_llm-and-streaming-part1.md
---

# Agent LLM and Streaming

- ターンフロー → [05_agent_03_01_turn-processing-flow-overview.md](05_agent_03_01_turn-processing-flow-overview.md)

## Purpose

`LLMClient`と`RobustSSEParser`の責務、SSEストリーミング
プロトコル、再接続の挙動、usage収集、部分補完の処理を文書化する。

---

## LLMClient (`shared/llm_client.py`)

`LLMClient`はLLMエンドポイントとのすべてのHTTP通信を担う。`AgentREPL.run()`内で
構築され、`ctx.services.llm`に格納される。

### Constructor

```python
LLMClient(
    http: httpx.AsyncClient,
    max_retries: int = 3,
    retry_base_delay: float = 1.0,
    temperature: float = 0.2,
    max_tokens: int = 1024,
    on_token: Callable[[str], None] | None = None,     # called per SSE token
    on_usage: Callable[[int, int], None] | None = None, # (prompt_tokens, completion_tokens)
    sse_heartbeat_timeout: float = 30.0,
    sse_malformed_retry: int = 2,
    sse_reconnect_max: int = 1,
    llm_stream_retry_on_heartbeat_timeout: bool = True,
    llm_stream_retry_on_malformed_chunk: bool = False,
)
```

### Key methods

| Method | Description |
|---|---|
| `build_payload(history, tool_defs, stream=False)` | messages/tools/temperature/max_tokensを含むリクエストdictを構築する |
| `async request_with_retry(url, payload)` | 指数バックオフによるリトライ付きPOST(HTTP 429/503とRequestErrorのみ) |
| `async call(url, history, tool_defs)` | 非ストリーミングのLLM呼び出し(圧縮、タイトル生成に使用) |
| `async stream(url, history, tool_defs)` | 再接続をサポートするSSEストリーミング。失敗時は`LLMTransportError`を発生させる |

### Statistics attributes

| Attribute | Description |
|---|---|
| `stat_retries` | `request_with_retry`のリトライ回数 |
| `stat_reconnects` | SSE再接続回数 |
| `stat_heartbeat_timeouts` | HEARTBEAT_TIMEOUTイベントの発生回数 |
| `stat_partial_completions` | 保存された部分補完の件数 |
| `stat_parse_errors` | 不正な形式のSSEフレーム数(スキップされたものも含む) |

---

## Payload Construction

`build_payload()`は以下を生成する:

```json
{
  "messages": [...],
  "tools": [...],
  "tool_choice": "auto",
  "temperature": 0.2,
  "max_tokens": 1024,
  "stream": true
}
```

OpenAI互換形式である。ツール定義は`AgentConfig.tool.tool_definitions`
(`config/tools_definitions.toml`からロードされる)から取得される。

---

## SSE Streaming

`LLMClient.stream()`は`LlmSseStreamHandler.stream_once()`を呼び出す。この関数は以下を行う:
1. `stream=True`でPOSTする
2. `asyncio.wait_for`(`sse_heartbeat_timeout`のタイムアウト)経由でバイト列を読み取る
3. バイト列を`RobustSSEParser.feed()`に渡す
4. テキストのデルタごとに`on_token()`コールバックを呼び出す
5. 関数呼び出しのデルタを`tool_calls_map`に累積する
6. usageチャンクが届いたら`on_usage()`を呼び出す
7. `[DONE]` SSEマーカーで返る

### RobustSSEParser (`shared/llm_client.py`)

接続ごとのパーサー(接続試行1回につき1インスタンス)。

| Method | Description |
|---|---|
| `feed(raw: bytes) -> (list[str], bool)` | バイト列をデコードし、ペイロード文字列群とis_doneフラグを返す |
| `check_heartbeat(url: str) -> None` | アイドル状態が長すぎる場合に`HEARTBEAT_TIMEOUT`を発生させる |

パーサーの挙動:
- 空行とSSEコメント(`:`)は最終イベントのタイムスタンプを更新する(keepalive)
- 不正な形式のJSONは`stat_parse_errors`をインクリメントする。`sse_malformed_retry`を超えると`MALFORMED_SSE_FRAME`を発生させる
- `[DONE]`は`is_done=True`を設定する

---

## Related Documents

- `05_agent_00_document-guide.md`
- `05_agent_05_llm-and-streaming-part2.md`

## Keywords

agent
llm
streaming
response
