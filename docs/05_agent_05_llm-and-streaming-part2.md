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

## Reconnect Behavior

`stream()`は`LlmSseStreamHandler.stream_once()`をリトライループでラップする:

``` text
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
- `05_agent_05_llm-and-streaming-part1.md`

## Keywords

agent
llm
streaming
response
