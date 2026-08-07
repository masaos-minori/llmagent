---
title: "Agent LLM and Streaming (Part 2)"
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

ストリーミングエラーの処理、部分補完の永続化、ランタイムパラメータ生成について文書化する。

## Design Intent

### 部分補完の永続化ルール

orchestratorのトランスポートエラーハンドラーによって処理される：

| ケース | アクション |
|---|---|
| `partial_text`が空でない場合(ストリーム中の失敗) | `[INCOMPLETE: {kind}]`のassistantメッセージを`session_diagnostics`にのみ保存する |
| `partial_text`が空の場合(ストリーム開始前の失敗) | 直前のユーザーメッセージを履歴からポップする。assistantメッセージは保存しない |
| ツール継続の失敗 | 合成された`tool`エラーメッセージを追加する。会話は継続する |

### エラー種別の設計意図

`LLMTransportError`の`kind`は以下のカテゴリに分けられる：

| カテゴリ | 説明 |
|---|---|
| HTTP_STATUS_RETRYABLE | HTTP 429 / 503 |
| HTTP_STATUS_FATAL | その他のHTTPエラー |
| CONNECT_ERROR | 接続失敗 |
| READ_TIMEOUT | 読み取りタイムアウト |
| HEARTBEAT_TIMEOUT | sse_heartbeat_timeout秒間SSEイベントがない |
| MALFORMED_SSE_FRAME | 不正な形式のフレームが多すぎる |
| PREMATURE_EOF | ストリームが予期せず終了した |

### ランタイムパラメータ生成

| パラメータ | 設定フィールド | ホットリロード経由 |
|---|---|---|
| Temperature | `cfg.llm.llm_temperature` | `/set temperature <f>`または`/reload` |
| Max tokens | `cfg.llm.llm_max_tokens` | `/set max_tokens <n>`または`/reload` |
| Retry count | `cfg.llm.llm_max_retries` | `/reload` |
| Heartbeat timeout | `cfg.llm.sse_heartbeat_timeout` | `/reload` |
| Reconnect max | `cfg.llm.sse_reconnect_max` | `/reload` |

圧縮処理は固定の定数を使用する：`COMPRESS_TEMPERATURE=0.3`、`COMPRESS_MAX_TOKENS=300`（factory.pyで定義。ホットリロード不可）。

通常呼び出しのパラメータは`/set temperature`または`/reload`経由でホットリロード可能である。それ以外の定数はすべてコンパイル時固定である。

## Responsibility Boundary

### 部分補完の境界条件

`content_parts`または`tool_calls_map`に既に部分的な内容が蓄積されている場合、または例外に`partial_text`が付与されている場合、`effective_retryable`の値に関わらず再接続せず即座に例外を送出する。これは「部分的に生成済みのアシスタント応答を、無関係な新規リクエストとしてやり直すことを避ける」ための実装意図と解釈できる。

## Key Constraints

### 部分補完の隔離

部分補完された応答は履歴に追加しない。`session_diagnostics`にのみ保存される。

### retryable vs fatal の運用意味

HTTPステータス429/503は`retryable=True`として`HTTP_STATUS_RETRYABLE`に分類され、それ以外のステータスは`HTTP_STATUS_FATAL`(retryable=False)となる。

### usageの統計的制限

LLMエンドポイントが`usage`フィールドを含むチャンクを返した場合、`prompt_tokens`と`completion_tokens`フィールドからusageデータが抽出され、`on_usage(prompt_tokens, completion_tokens)`コールバックが呼び出される。エンドポイントが`usage`を返さない場合、統計は`None`のままとなる。`/context`は`chars // 4`による見積もりを表示する。

## Operational Notes

- `LLMTransportError`は`phase`(pre_stream/in_stream)、`url`、`status_code`、`retryable`、`partial_text`、`detail`、`stat_heartbeat_timeouts`を保持する
- `UTF8_PARTIAL_DECODE_ERROR`と`PREMATURE_EOF`は明確に区別される。`PREMATURE_EOF`はSSEストリームが期待されるcontent-lengthより前に終了した場合にraiseされる。`UTF8_PARTIAL_DECODE_ERROR`はJSONデコードエラーを別途処理する
- 再接続が成功して最終的にコンテンツが得られた場合、`on_token("\n")`が末尾に一度だけ呼ばれる

## Known Limitations

- 不明

## Related Docs

- `05_agent_00_document-guide.md`
- `05_agent_05_llm-and-streaming-part1.md`

## Keywords

agent
llm
streaming
response
