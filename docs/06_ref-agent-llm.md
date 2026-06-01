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
    kind: LLMErrorKind                          # 失敗種別 (HTTP_STATUS_FATAL / HEARTBEAT_TIMEOUT 等)
    phase: Literal["pre_stream", "in_stream"]  # 障害発生フェーズ
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
- `_parse_line(line: str) -> tuple[str | None, bool] | None`: SSE テキスト行を 1 行解析。`None` でスキップ、`(None, True)` で `[DONE]`、`(payload_str, False)` で有効データ。malformed JSON は `stat_parse_errors` をインクリメントし、予算超過で `MALFORMED_SSE_FRAME` を raise。blank line / SSE comment (`:`) は keepalive として `_last_event_at` を更新。
- `check_heartbeat(url: str) -> None`: `_heartbeat_timeout > 0` のとき `_last_event_at` からの経過秒を確認し閾値超過で `HEARTBEAT_TIMEOUT` を raise。実際のバイト待機タイムアウトは `LLMClient._read_next_chunk()` の `asyncio.wait_for` が担当するため、`check_heartbeat()` は `_stream_once()` 内から直接は呼ばれない。
- `stat_parse_errors: int`: malformed SSE frame カウント（スキップ分含む）。`LLMClient._stream_once()` が読み取り後にリセットし `LLMClient.stat_parse_errors` へ加算する。
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
    on_token=lambda tok: print(tok, end="", flush=True),   # トークン到着ごとに呼ばれる
    on_usage=lambda pt, ct: ...,                            # (prompt_tokens, completion_tokens) で呼ばれる
    sse_heartbeat_timeout=30.0,
    sse_malformed_retry=2,
    sse_reconnect_max=1,
    llm_stream_retry_on_heartbeat_timeout=True,
    llm_stream_retry_on_malformed_chunk=False,
)
response = await client.stream(url, history, tool_defs)
```

コンストラクタ引数:

| 引数 | 型 | 説明 |
|---|---|---|
| `http` | `httpx.AsyncClient` | 共有 HTTP クライアント |
| `max_retries` | `int` | `request_with_retry` の最大試行回数 |
| `retry_base_delay` | `float` | 指数バックオフの基底秒数 (`delay = base * 2^attempt`) |
| `temperature` | `float` | LLM 生成温度 |
| `max_tokens` | `int` | 最大トークン数 |
| `on_token` | `Callable[[str], None] \| None` | SSE トークン到着時に呼ばれるコールバック |
| `on_usage` | `Callable[[int, int], None] \| None` | `(prompt_tokens, completion_tokens)` を渡すコールバック。使用量データが含まれるチャンク到着時に呼ばれる |
| `sse_heartbeat_timeout` | `float` | SSE イベント無受信の閾値秒。`0` 以下で無効 |
| `sse_malformed_retry` | `int` | malformed SSE frame を許容する最大スキップ数。超過で `MALFORMED_SSE_FRAME` を raise |
| `sse_reconnect_max` | `int` | retryable エラー時の SSE reconnect 最大回数 |
| `llm_stream_retry_on_heartbeat_timeout` | `bool` | `HEARTBEAT_TIMEOUT` 発生時に reconnect するか |
| `llm_stream_retry_on_malformed_chunk` | `bool` | `MALFORMED_SSE_FRAME` 発生時に reconnect するか |

| メソッド | 説明 |
|---|---|
| `async request_with_retry(url, payload) -> httpx.Response` | 指数バックオフリトライ付き POST。HTTP 429 / 503 と `httpx.RequestError` のみリトライ。全試行失敗時は最後の例外を raise |
| `build_payload(history, tool_defs, stream=False) -> dict[str, Any]` | `messages` / `tools` / `tool_choice="auto"` / `temperature` / `max_tokens` を含むリクエストボディを生成。`stream=True` のとき `"stream": True` を追加 |
| `async call(url, history, tool_defs) -> dict[str, Any]` | 非ストリーミング LLM 呼び出し。`request_with_retry` を内部使用し `_emit_usage()` を呼ぶ |
| `async stream(url, history, tool_defs) -> dict[str, Any]` | reconnect 対応 SSE ストリーミング。失敗時は `LLMTransportError` を raise（`partial_text` 付き） |
| `async _stream_once(url, history, tool_defs, content_parts, tool_calls_map) -> str \| None` | 1 回の SSE 接続試行。トークンと tool_call delta を `content_parts` / `tool_calls_map` に in-place で追記し、`finish_reason` を返す。失敗時は `LLMTransportError` を raise |
| `async _read_next_chunk(byte_iter, url) -> tuple[bytes, bool]` | `asyncio.wait_for` で次のバイトチャンクを取得。`sse_heartbeat_timeout` 秒以内に bytes が届かなければ `HEARTBEAT_TIMEOUT` を raise。`exhausted=True` は iterator 終端 |
| `_emit_usage(data) -> None` | SSE チャンクまたは非ストリーミングレスポンスの `usage` フィールドから `prompt_tokens` / `completion_tokens` を取り出し `on_usage` コールバックを呼ぶ |
| `_process_sse_chunk(chunk, content_parts, tool_calls_map) -> str \| None` | 解析済み SSE チャンクから delta を取り出し `content_parts` / `tool_calls_map` を更新。`finish_reason` を返す |
| `_merge_tool_call_delta(tool_calls_map, tc_delta) -> None` (static) | ストリーミング tool_call delta をインデックスキーの map に累積 |
| `_build_stream_response(content_parts, tool_calls_map, finish_reason) -> dict[str, Any]` (static) | ストリーミング終了後に `content_parts` と `tool_calls_map` から `choices[0].message` 形式のレスポンス dict を構築 |
| `extract_message(response) -> tuple[LLMMessage, str \| None]` (static) | `choices[0].message` と `finish_reason` を取り出す。フィールド欠如時は `ValueError` |

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
