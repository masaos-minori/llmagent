# shared/llm_client.py

## 1. 機能概要

`AgentREPL` から抽出した LLM HTTP 通信レイヤー。SSE ストリーミング・指数バックオフリトライ・ペイロード構築・レスポンス整形を担当。`AgentREPL().run()` で `LLMClient` インスタンスを生成し、`ctx.services.llm` として保持。

SSE 堅牢化として以下を実装:
- `RobustSSEParser`: bytes ストリームの incremental UTF-8 デコード・heartbeat 追跡・malformed frame カウンタ
- `_stream_once()`: 1 回の SSE 接続試行（heartbeat timeout / MALFORMED_SSE_FRAME / HTTP エラーを `LLMTransportError` として報告）
- `stream()`: `_stream_once()` を最大 `sse_reconnect_max` 回リトライ。partial output がある場合は `mark_incomplete` ポリシーとして `partial_text` を付与して raise

## 2. `LLMTransportError` 例外

```python
class LLMTransportError(Exception):
    kind: LLMErrorKind      # 失敗種別 (HTTP_STATUS_FATAL / HEARTBEAT_TIMEOUT 等)
    phase: str              # "pre_stream" | "in_stream"
    url: str
    status_code: int | None
    retryable: bool
    partial_text: str       # 障害前に積み上がった partial output (非空 = partial completion)
    detail: str
```

`kind` の値:
- `HTTP_STATUS_RETRYABLE` / `HTTP_STATUS_FATAL` — HTTP レスポンスエラー
- `CONNECT_ERROR` — 接続失敗
- `READ_TIMEOUT` — 読み取りタイムアウト
- `HEARTBEAT_TIMEOUT` — `sse_heartbeat_timeout` 秒間イベントなし
- `MALFORMED_SSE_FRAME` — `sse_malformed_retry` 超過
- `UTF8_PARTIAL_DECODE_ERROR` / `PREMATURE_EOF` / `UNKNOWN_STREAM_ERROR` — その他

## 3. `RobustSSEParser`

```python
parser = RobustSSEParser(malformed_retry=2, heartbeat_timeout=30.0)
payloads, is_done = parser.feed(raw_bytes)  # returns JSON payload strings
parser.check_heartbeat(url)  # raises HEARTBEAT_TIMEOUT when idle
```

- `feed(raw: bytes) -> tuple[list[str], bool]`: bytes をデコードし完成した SSE `data:` ペイロードを返す。`is_done=True` は `[DONE]` 受信。
- `_parse_line()`: `data:` / `:` (comment) / blank line を処理。malformed JSON は `stat_parse_errors` をインクリメントし、予算超過で `MALFORMED_SSE_FRAME` を raise。
- `check_heartbeat(url)`: `_heartbeat_timeout > 0` のとき最終イベントからの経過秒を確認し閾値超過で raise。
- 1 接続 1 インスタンス。reconnect 時は新規生成。

## 4. `LLMClient` API

```python
from shared.llm_client import LLMClient

client = LLMClient(
    http=httpx.AsyncClient(...),
    max_retries=3,
    retry_base_delay=1.0,
    temperature=0.2,
    max_tokens=1024,
    sse_heartbeat_timeout=30.0,
    sse_malformed_retry=2,
    sse_reconnect_max=1,
    llm_stream_retry_on_heartbeat_timeout=True,
    llm_stream_retry_on_malformed_chunk=False,
)
response = await client.stream(url, history, tool_defs)
```

| メソッド | 説明 |
|---|---|
| `request_with_retry(url, payload) -> httpx.Response` | 指数バックオフリトライ付き POST。HTTP 429 / 503 と接続エラーのみリトライ |
| `build_payload(history, tool_defs, stream=False) -> dict` | `messages` / `tools` / `temperature` / `max_tokens` を含むリクエストボディを生成 |
| `call(url, history, tool_defs) -> dict` | 非ストリーミング LLM 呼び出し。`request_with_retry` を内部使用 |
| `stream(url, history, tool_defs) -> dict` | reconnect 対応 SSE ストリーミング。失敗時は `LLMTransportError` を raise（`partial_text` 付き） |
| `_stream_once(...) -> str \| None` | 1 回の SSE 接続試行。`finish_reason` を返す |
| `extract_message(response) -> tuple[dict, str \| None]` (static) | `choices[0].message` と `finish_reason` を取り出す。フィールド欠如時は `ValueError` |

統計属性（全てセッション通算）:
- `stat_retries: int` — `request_with_retry` リトライ回数
- `stat_reconnects: int` — SSE reconnect 回数
- `stat_heartbeat_timeouts: int` — HEARTBEAT_TIMEOUT 発生回数
- `stat_partial_completions: int` — partial completion 保存回数
- `stat_parse_errors: int` — malformed SSE frame カウント（スキップ分含む）

## 5. `format_transport_error()` (tool_executor.py)

LLM / ツール両方の transport 失敗に対応する共通メタ整形ユーティリティ。`agent/orchestrator.py` がツール継続ターンの失敗時に使用。

```python
from shared.tool_executor import format_transport_error

err = format_transport_error(
    source="llm", phase="in_stream", kind="HEARTBEAT_TIMEOUT",
    url="...", status_code=None, retryable=True, partial=False,
)
# err["summary"] — ユーザー向け短文
# err["detail"]  — JSON 文字列 (audit log / ToolResult 保存用)
```

## 6. 履歴整合ルール (orchestrator.py)

`agent/orchestrator.py` が `LLMTransportError` を捕捉した際の挙動:

| ケース | 処理 |
|---|---|
| 完全成功 | 従来どおり assistant メッセージを確定 |
| partial completion (`partial_text` あり) | `[INCOMPLETE: <kind>]` 付き assistant として history / session 保存。`ctx.tool_result_store.store()` で失敗詳細を保存 (`tool_name="llm_partial_completion"`) |
| pre-stream fail (`partial_text` なし) | assistant 保存なし。直前のユーザーメッセージを pop して履歴汚染防止 |
| tool continuation fail (turn > 0) | synthetic tool error (`name="llm_transport_error"`) を history に追加して対話継続。`ctx.tool_result_store.store()` で保存 (`tool_name="llm_transport_error"`) |

`_handle_llm_turn()` は `LLMTransportError` を処理後に re-raise する。`handle_turn()` はその例外を `except LLMTransportError: pass` でキャッチして外部には伝播させない — エラー処理 (incomplete 保存・on_error コールバック) は `_handle_llm_turn()` 内で完了しているため。

`tool_result_store` に保存された LLM 失敗は `/tool show <id>` で後追い確認可能。

## 7. 使用スクリプト

| スクリプト | 使用箇所 |
|---|---|
| `agent/repl.py` | `ctx.services.llm = LLMClient(...)` を `run()` で生成 |
| `agent/orchestrator.py` | `_run_turn()` で `ctx.services.llm.stream()` を呼び出し。`LLMTransportError` を捕捉して pre_stream / partial completion / tool continuation fail に分岐。`ctx.tool_result_store` に LLM 失敗を保存 |
