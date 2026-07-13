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

> **Current behavior**: `scripts/shared/llm_client.py`の実装では`http`/`max_retries`/`retry_base_delay`/`temperature`/`max_tokens`はデフォルト値を持たない必須引数である(デフォルト値を持つのは`sse_*`以降のみ)。上記シグネチャ例のデフォルト値表記は呼び出し側(`AgentConfig`等)が渡す値の目安であり、`LLMClient`自体の既定値ではない。(Explicit in code)

### Hot-reloadable configuration

`apply_config(**kwargs)`は`temperature`/`max_tokens`/`max_retries`/`retry_base_delay`/
`sse_heartbeat_timeout`/`sse_malformed_retry`/`sse_reconnect_max`/
`stream_retry_on_heartbeat_timeout`/`stream_retry_on_malformed_chunk`を、
インスタンスを再生成せずに更新する。`None`を渡したフィールドは変更されない
(`shared/llm_hot_config.py`の`LlmHotConfigHandler`)。(Explicit in code)

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
| `stat_parse_errors` | 不正な形式のSSEフレーム数(スキップされたものも含む) |

> **Current behavior**: `LLMClient`インスタンス自体には`stat_partial_completions`属性は存在しない。部分補完件数は`LlmReconnectHandler.stream()`の戻り値タプル(5要素目`partial_completions`)としてのみ返され、`LLMClient.stream()`はこの値を属性に保存せず呼び出し元へ伝播しない。ドキュメント旧記述との相違点。(Explicit in code)

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
(`config/agent.toml`の`[[tool_definitions]]`からロードされる)から取得される。

---

## SSE Streaming

`LLMClient.stream()`は`LlmReconnectHandler.stream()`(`shared/llm_reconnect.py`)を呼び出し、
`LlmReconnectHandler`が接続試行ごとに`LlmSseStreamHandler.stream_once()`
(`shared/llm_sse_stream.py`)を呼び出す。`stream_once()`は以下を行う:
1. `stream=True`でPOSTする
2. `asyncio.wait_for`(`sse_heartbeat_timeout`のタイムアウト)経由でバイト列を読み取る
3. バイト列を`RobustSSEParser.feed()`に渡す
4. テキストのデルタごとに`on_token()`コールバックを呼び出す
5. 関数呼び出しのデルタを`tool_calls_map`に累積する
6. usageチャンクが届いたら`on_usage()`を呼び出す
7. `[DONE]` SSEマーカーで返る

> **Current behavior**: `RobustSSEParser`本体は`shared/sse_parser.py`に実装されている
> (`shared/llm_client.py`には存在しない)。SSEチャンクの解析ロジック
> (`process_sse_payloads`/`process_sse_chunk`/`parse_usage`/`merge_tool_call_delta`)は
> `shared/llm_sse_helpers.py`の`LlmSseHelpers`に分離されている。(Explicit in code)

### Reconnect behavior (`LlmReconnectHandler.stream`, `shared/llm_reconnect.py`)

`sse_reconnect_max`回まで`stream_once()`を再試行する。再接続の可否判定:

| kind | 再接続判定 |
|---|---|
| `HEARTBEAT_TIMEOUT` | `llm_stream_retry_on_heartbeat_timeout`フラグに従う |
| `MALFORMED_SSE_FRAME` | `llm_stream_retry_on_malformed_chunk`フラグに従う |
| その他 | `LLMTransportError.retryable`に従う |

**境界条件(Boundary and ownership)**: `content_parts`または`tool_calls_map`に
既に部分的な内容が蓄積されている場合、または例外に`partial_text`が付与されている場合
(`has_partial`)、`effective_retryable`の値に関わらず再接続せず即座に例外を送出する。
これは「部分的に生成済みのアシスタント応答を、無関係な新規リクエストとして
やり直すことを避ける」ための実装意図と解釈できる(Strongly implied by code)。
再接続が成功して最終的にコンテンツが得られた場合、`on_token("\n")`が末尾に一度だけ
呼ばれる。(Explicit in code)

### RobustSSEParser (`shared/sse_parser.py`)

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

## DTOs and Error Kinds

### LLMResponse / LLMUsage (`shared/llm_types.py`)

`LLMResponse`は`message`(dict)/`finish_reason`(str|None)/`usage`(`LLMUsage`|None)を
持つ`frozen`dataclass。`LLMUsage`は`prompt_tokens`/`completion_tokens`を持つ`frozen`
dataclass。`LLMClient.call()`/`stream()`はいずれも`LLMResponse`を返す。(Explicit in code)

### LLMTransportError (`shared/llm_exceptions.py`)

`LLMErrorKind`は以下のリテラル値を取る(Explicit in code):

`HTTP_STATUS_RETRYABLE` / `HTTP_STATUS_FATAL` / `CONNECT_ERROR` / `READ_TIMEOUT` /
`HEARTBEAT_TIMEOUT` / `MALFORMED_SSE_FRAME` / `UTF8_PARTIAL_DECODE_ERROR` /
`PREMATURE_EOF` / `UNKNOWN_STREAM_ERROR`

各例外は`phase`(`pre_stream`|`in_stream`)、`url`、`status_code`、`retryable`、
`partial_text`、`detail`、`stat_heartbeat_timeouts`を保持する。HTTPステータス
429/503は`retryable=True`として`HTTP_STATUS_RETRYABLE`に分類され、それ以外の
ステータスは`HTTP_STATUS_FATAL`(`retryable=False`)となる
(`shared/llm_transport_errors.py`の`LlmTransportErrorHandler`)。

> **Needs confirmation**: `UTF8_PARTIAL_DECODE_ERROR`と`PREMATURE_EOF`は
> `LLMErrorKind`に定義されているが、`llm_sse_stream.py`/`llm_transport_errors.py`/
> `sse_parser.py`の範囲では発生箇所を確認できなかった。他モジュールから
> raiseされている可能性がある。

---

## Related Documents

- `05_agent_00_document-guide.md`
- `05_agent_05_llm-and-streaming-part2.md`

## Keywords

agent
llm
streaming
response
sse
reconnect
transport-error
llm-client
