---
title: "Agent LLM and Streaming"
category: agent
tags:
  - agent
  - llm
  - streaming
  - response
related:
  - 05_agent_00_document-guide.md
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

## Reconnect Behavior

`stream()`は`LlmSseStreamHandler.stream_once()`をリトライループでラップする:

```
LlmSseStreamHandler.stream_once() attempt 1
  → if LLMTransportError.retryable and reconnect count < sse_reconnect_max:
       reconnect (new RobustSSEParser, new HTTP request)
       append partial_text to content_parts (preserve accumulated output)
   → else: raise LLMTransportError with full partial_text
```

再接続の条件(設定フラグで制御される):
- `HEARTBEAT_TIMEOUT` → `llm_stream_retry_on_heartbeat_timeout=True`の場合に再接続
- `MALFORMED_SSE_FRAME` → `llm_stream_retry_on_malformed_chunk=True`の場合に再接続
- `HTTP_STATUS_RETRYABLE` (429/503) → 常に再接続
- `HTTP_STATUS_FATAL` / `CONNECT_ERROR` → 再接続しない

---

## LLMTransportError

```python
class LLMTransportError(Exception):
    kind: LLMErrorKind
    phase: Literal["pre_stream", "in_stream"]
    url: str
    status_code: int | None
    retryable: bool
    partial_text: str    # non-empty = partial completion occurred
    detail: str
```

`kind`の値:

| Kind | Cause |
|---|---|
| `HTTP_STATUS_RETRYABLE` | HTTP 429 / 503 |
| `HTTP_STATUS_FATAL` | その他のHTTPエラー |
| `CONNECT_ERROR` | 接続失敗 |
| `READ_TIMEOUT` | 読み取りタイムアウト |
| `HEARTBEAT_TIMEOUT` | `sse_heartbeat_timeout`秒間SSEイベントがない |
| `MALFORMED_SSE_FRAME` | 不正な形式のフレームが多すぎる |
| `PREMATURE_EOF` | ストリームが予期せず終了した |

---

## Usage Collection

LLMエンドポイントが`usage`フィールドを含むチャンクを返した場合:
- `prompt_tokens`と`completion_tokens`フィールドからusageデータが抽出される
- `on_usage(prompt_tokens, completion_tokens)`コールバックが呼び出される
- コールバックが`ctx.stats.stat_input_tokens`と`ctx.stats.stat_output_tokens`を更新する
- `/stats`の出力に表示される

エンドポイントが`usage`を返さない場合: 統計は`None`のままとなる。`/context`は`chars // 4`による見積もりを表示する。

---

## Partial Completion Persistence

orchestratorのトランスポートエラーハンドラーによって処理される:

| Case | Action |
|---|---|
| `partial_text`が空でない場合(ストリーム中の失敗) | `[INCOMPLETE: {kind}]`のassistantメッセージを`session_diagnostics`にのみ保存する |
| `partial_text`が空の場合(ストリーム開始前の失敗) | 直前のユーザーメッセージを履歴からポップする。assistantメッセージは保存しない |
| ツール継続の失敗 | 合成された`tool`エラーメッセージを追加する。会話は継続する |

---

## LLM Generation Parameters at Runtime

| Parameter | Config field | Hot-reload via |
|---|---|---|
| Temperature | `cfg.llm.llm_temperature` | `/set temperature <f>`または`/reload` |
| Max tokens | `cfg.llm.llm_max_tokens` | `/set max_tokens <n>`または`/reload` |
| Retry count | `cfg.llm.llm_max_retries` | `/reload` |
| Heartbeat timeout | `cfg.llm.sse_heartbeat_timeout` | `/reload` |
| Reconnect max | `cfg.llm.sse_reconnect_max` | `/reload` |

圧縮処理は固定の定数を使用する: `COMPRESS_TEMPERATURE=0.3`、`COMPRESS_MAX_TOKENS=300`
(`factory.py`で定義。ホットリロード不可)。

### Per-Use-Case LLM Generation Constants

| Use case | Location | Temperature | Max tokens |
|---|---|---|---|
| 通常のLLM呼び出し | `cfg.llm.llm_temperature` / `cfg.llm.llm_max_tokens` | 0.2 (デフォルト) | 1024 (デフォルト) |
| 履歴圧縮 | `factory.py: COMPRESS_TEMPERATURE` / `COMPRESS_MAX_TOKENS` | 0.3 | 300 |
| セッションタイトル生成 | `cfg.llm.title_llm_temperature` / `cfg.llm.title_llm_max_tokens` | 0.1 | 20 |
| MQEクエリ拡張 | `scripts/rag/pipeline.py: MQE_TEMPERATURE` / `MQE_MAX_TOKENS` | 0.6 | 300 |
| クロスエンコーダーによる再ランキング | `scripts/rag/pipeline.py: RERANK_TEMPERATURE` / `RERANK_MAX_TOKENS` | 0.0 | 256 |

通常呼び出しのパラメータは`/set temperature`または`/reload`経由でホットリロード可能である。
それ以外の定数はすべてコンパイル時固定である。

## Related Documents

- `05_agent_00_document-guide.md`

## Keywords

agent
llm
streaming
response
