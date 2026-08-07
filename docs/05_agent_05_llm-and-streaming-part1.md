---
title: "Agent LLM and Streaming (Part 1)"
category: agent
tags:
  - agent
  - llm
  - streaming
  - sse
related:
  - 05_agent_00_document-guide.md
source:
  - 05_agent_05_llm-and-streaming-part1.md
---

# Agent LLM and Streaming

- ターンフロー → [05_agent_03_01_turn-processing-flow-overview.md](05_agent_03_01_turn-processing-flow-overview.md)

## Purpose

`LLMClient`と`RobustSSEParser`の責務、SSEストリーミングプロトコル、再接続の挙動、usage収集、部分補完の処理を文書化する。

## Design Intent

### LLMClient の目的

`LLMClient`はLLMエンドポイントとのすべてのHTTP通信を担う。`AgentREPL.run()`内で構築され、`ctx.services.llm`に格納される。

構成要素は以下のカテゴリに分けられる：モデル、エンドポイント、認証、ストリーミング。詳細は`shared/llm_client.py`を参照。

### ホットリロード可能な設定

`apply_config(**kwargs)`は`temperature`/`max_tokens`/`max_retries`/`retry_base_delay`/`sse_heartbeat_timeout`/`sse_malformed_retry`/`sse_reconnect_max`/`stream_retry_on_heartbeat_timeout`/`stream_retry_on_malformed_chunk`を、インスタンスを再生成せずに更新する。`None`を渡したフィールドは変更されない。

### リクエストペイロード

`build_payload()`はmessages/tools/temperature/max_tokens/streamを含むリクエストdictを構築する。ツール定義は`AgentConfig.tool.tool_definitions`から取得される。

### ストリーミングの設計意図

`LLMClient.stream()`は`LlmReconnectHandler.stream()`を呼び出し、`LlmReconnectHandler`が接続試行ごとに`LlmSseStreamHandler.stream_once()`を呼び出す。`stream_once()`は以下を行う：

1. `stream=True`でPOSTする
2. `asyncio.wait_for`(`sse_heartbeat_timeout`のタイムアウト)経由でバイト列を読み取る
3. バイト列を`RobustSSEParser.feed()`に渡す
4. テキストのデルタごとに`on_token()`コールバックを呼び出す
5. 関数呼び出しのデルタを`tool_calls_map`に累積する
6. usageチャンクが届いたら`on_usage()`を呼び出す
7. `[DONE]` SSEマーカーで返る

`RobustSSEParser`本体は`shared/sse_parser.py`に実装されている。SSEチャンクの解析ロジックは`shared/llm_sse_helpers.py`の`LlmSseHelpers`に分離されている。

### 統計属性

| Attribute | Description |
|---|---|
| `stat_retries` | `request_with_retry`のリトライ回数 |
| `stat_reconnects` | SSE再接続回数 |
| `stat_heartbeat_timeouts` | HEARTBEAT_TIMEOUTイベントの発生回数 |
| `stat_parse_errors` | 不正な形式のSSEフレーム数(スキップされたものも含む) |

> **Note:** `LLMClient`インスタンス自体には`stat_partial_completions`属性は存在しない。部分補完件数は`LlmReconnectHandler.stream()`の戻り値タプルとしてのみ返され、`LLMClient.stream()`はこの値を属性に保存せず呼び出し元へ伝播しない。

## Responsibility Boundary

### Reconnect behavior (`LlmReconnectHandler.stream`, `shared/llm_reconnect.py`)

`sse_reconnect_max`回まで`stream_once()`を再試行する。再接続の可否判定：

| kind | 再接続判定 |
|---|---|
| `HEARTBEAT_TIMEOUT` | `llm_stream_retry_on_heartbeat_timeout`フラグに従う |
| `MALFORMED_SSE_FRAME` | `llm_stream_retry_on_malformed_chunk`フラグに従う |
| その他 | `LLMTransportError.retryable`に従う |

**境界条件：** `content_parts`または`tool_calls_map`に既に部分的な内容が蓄積されている場合、または例外に`partial_text`が付与されている場合、`effective_retryable`の値に関わらず再接続せず即座に例外を送出する。これは「部分的に生成済みのアシスタント応答を、無関係な新規リクエストとしてやり直すことを避ける」ための実装意図と解釈できる。

再接続が成功して最終的にコンテンツが得られた場合、`on_token("\n")`が末尾に一度だけ呼ばれる。

### RobustSSEParser (`shared/sse_parser.py`)

接続ごとのパーサー(接続試行1回につき1インスタンス)。

パーサーの挙動：
- 空行とSSEコメントは最終イベントのタイムスタンプを更新する(keepalive)
- 不正な形式のJSONは`stat_parse_errors`をインクリメントする。`sse_malformed_retry`を超えると`MALFORMED_SSE_FRAME`を発生させる
- `[DONE]`は`is_done=True`を設定する

## Key Constraints

### 部分補完の隔離

部分補完された応答は履歴に追加しない。`session_diagnostics`にのみ保存される。

### retryable vs fatal の運用意味

HTTPステータス429/503は`retryable=True`として`HTTP_STATUS_RETRYABLE`に分類され、それ以外のステータスは`HTTP_STATUS_FATAL`(retryable=False)となる。

### usageの統計的制限

LLMエンドポイントが`usage`フィールドを含むチャンクを返した場合、`prompt_tokens`と`completion_tokens`フィールドからusageデータが抽出され、`on_usage(prompt_tokens, completion_tokens)`コールバックが呼び出される。エンドポイントが`usage`を返さない場合、統計は`None`のままとなる。`/context`は`chars // 4`による見積もりを表示する。

## Operational Notes

- `LLMClient.call()`は非ストリーミングのLLM呼び出し(圧縮、タイトル生成に使用)
- `LLMClient.request_with_retry()`は指数バックオフによるリトライ付きPOST(HTTP 429/503とRequestErrorのみ)
- `LLMTransportError`は`phase`(pre_stream/in_stream)、`url`、`status_code`、`retryable`、`partial_text`、`detail`、`stat_heartbeat_timeouts`を保持する
- `UTF8_PARTIAL_DECODE_ERROR`と`PREMATURE_EOF`は明確に区別される。`PREMATURE_EOF`はSSEストリームが期待されるcontent-lengthより前に終了した場合にraiseされる。`UTF8_PARTIAL_DECODE_ERROR`はJSONデコードエラーを別途処理する

## Known Limitations

- 不明

## Related Docs

- `05_agent_00_document-guide.md`
- `05_agent_05_llm-and-streaming-part2.md`

## Keywords

agent
llm
streaming
sse
reconnect
transport-error
llm-client
