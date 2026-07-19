---
title: "HttpTransport, McpServerHealthRegistry, and Tracing Correlation Keys (Part 1)"
category: mcp
tags:
  - mcp
  - transport
  - health-registry
related:
  - 04_mcp_00_document-guide.md
  - 04_mcp_03_01_dispatch-and-routing.md
  - 04_mcp_03_02_tool-registry.md
  - 04_mcp_03_04_tool-call-tracing-and-watchdog.md
  - 04_mcp_03_05_lifecycle-and-new-server.md
source:
  - 04_mcp_03_03_transport-and-health-part1.md
---

# HttpTransport、McpServerHealthRegistry、追跡の相関キー(Part 1)

## HttpTransport (`shared/http_transport.py`)

**矛盾点（要修正の記録）:** 本節の見出しは従来 `shared/tool_executor.py` としていたが、`HttpTransport` クラスの実体は `shared/http_transport.py` に定義されている（Explicit in code）。インスタンス化と保持は `shared/tool_transport_invoker.py` が行い、`shared/tool_executor.py` は `TransportError` 例外型のみを同モジュールからインポートしている。`shared/tool_executor.py` のモジュール docstring には "Provides HttpTransport implementation for POST /v1/call_tool over httpx." とあるが、実装本体は同ファイルには存在しない（Explicit in code）。

```python
HttpTransport(http, base_url, server_key, cfg=McpServerConfig)
result = await transport.call("tool_name", {"arg": "val"})
```

- `cfg.auth_token` が空でない場合、`Authorization: Bearer <token>` を追加する
- 全てのトランスポートレベルの障害（タイムアウト、HTTP 非 2xx、不正な形式のレスポンス、リトライ消尽）で `TransportError` を発生させる; `is_error=True` を直接返すことはない
- トランスポートエラーハンドラーが `TransportError` を捕捉し、`ToolCallResult(error_type="transport")` に変換する
- `set_session_id(session_id)` はリクエストごとに `X-Session-Id` ヘッダーを注入する（`ToolTransportInvoker` 経由）
- **リトライ:** HTTP 429/502/503/504 でリトライを行う。最大3回の試行で、遅延時間は減少していく: 試行0回目は4秒待機、試行1回目は2秒待機、試行2回目は1秒待機した後、最終的な消尽エラーとなる。計算式: 2^(RETRY_MAX - attempt - 1)。これは指数バックオフではない（試行ごとに遅延が減少する）。HealthRegistry に記録されるのは最終結果のみ（成功、または全リトライ消尽後の TransportError）。
- **リトライ不可のエラー:** HTTP タイムアウト（`httpx.TimeoutException`）と、429/502/503/504 以外のステータスコードによる HTTPStatusError は、リトライなしで即時に伝播する。
- **ツールレベルエラー vs トランスポートレベルエラー:** ツールレベルのエラー（`error_type == "tool"`）はトランスポート呼び出しの成功として扱われ、`record_success()` と `stat_tool_errors` カウンターのインクリメントをトリガーする。トランスポートレベルのエラーは `record_failure()` と `stat_transport_errors` カウンターのインクリメントをトリガーする。両カウンターは独立して追跡される。
- **レスポンスパース:** `_handle_call_tool_response()` メソッド内で `parse_http_json(resp)` を使用して httpx.Response から JSON データをデコードする。`parse_http_json` は `shared/json_utils.py` で定義され、`resp.json()` のラッパーとして機能する。旧版では `orjson.loads(resp.content)` を直接使用していた。

---

## McpServerHealthRegistry (`shared/mcp_health.py`)

**注記:** クラス実体は `shared/mcp_health.py` に定義されている。`shared/mcp_config.py` はこれを `# noqa: F401` 付きで re-export しているのみである（Explicit in code）。両モジュールから同名でインポート可能なため実害はないが、正典モジュールは `shared/mcp_health.py` である。

`_build_tool_executor()`（factory.py）内で作成され、`ToolTransportInvoker`（`set_health_registry()` 経由）と
`AppServices.health_registry` の間で共有される、サーバーごとの失敗トラッカー。
両者は同一のオブジェクトを保持するため、`ToolExecutor` によって記録されたヘルス状態は
`AppServices.health_registry` を通じて即座に可視化される。

**状態遷移:**

```
HEALTHY ──(failure × threshold)──→ UNAVAILABLE
   ↑                                    │
   │                            (cooldown 30s elapsed)
   │                                    ↓
   └──(record_success)────────── HALF_OPEN (trial probe)
                                        │
                              (failure)─┘ → UNAVAILABLE (cooldown reset)
```

| 状態 | 条件 |
|---|---|
| `HEALTHY` | 失敗なし、または呼び出し成功後 |
| `DEGRADED` | 失敗回数 < しきい値（デフォルト3） |
| `UNAVAILABLE` | 失敗回数 ≥ しきい値; ディスパッチはブロックされる |
| `HALF_OPEN` | 30秒のクールダウン経過後; 1回の試行ディスパッチが許可される |

| メソッド | 説明 |
|---|---|
| `record_failure(server_key)` | 失敗回数をインクリメント; `HALF_OPEN → UNAVAILABLE`（クールダウンリセット); しきい値到達時 → `UNAVAILABLE` |
| `record_degraded(server_key, reason)` | オプションの理由文字列とともに、状態を `DEGRADED` に設定する; 到達可能だが健全とは言えないサーバーを報告するためのAPI。現在の状態が `UNAVAILABLE` または `HALF_OPEN` の場合は no-op（debug ログのみ記録し、状態・理由は変更しない）— circuit breaker のディスパッチゲーティングとシングルトライアル窓を維持するためのガード |
| `get_degraded_reason(server_key)` | 最後に記録された degraded の理由文字列を返す。設定されていない場合は `None` |
| `record_success(server_key)` | 失敗回数、unavailable タイムスタンプ、degraded の理由をリセット; `HALF_OPEN → HEALTHY` |
| `get_state(server_key)` | 現在の状態; 未知のキーの場合は `HEALTHY` を返す |
| `is_unavailable(server_key)` | `UNAVAILABLE` であり、かつクールダウンがまだ経過していない場合 `True`; 副作用として、クールダウン経過時に `HALF_OPEN` へ遷移する |

**コンストラクタ:** `McpServerHealthRegistry(failure_threshold=3, half_open_cooldown_sec=30.0)`
- `half_open_cooldown_sec`: `UNAVAILABLE` に入ってから試行ディスパッチが許可されるまでの秒数（デフォルト30秒、固定値 — 指数バックオフではない）

**共有配線:** このレジストリは一度だけ作成され、複数の場所で消費される — 書き込み側は `ToolTransportInvoker`（`record_failure`/`record_success`）、読み取り側は `/mcp status`（`McpStatusService.probe_all()`、`get_state`/`get_degraded_reason`）。`factory.py` のツールエクゼキュータビルド処理で `McpServerHealthRegistry()` が1つ生成され、`ToolTransportInvoker.set_health_registry()` 経由で `ToolTransportInvoker` に注入され、同じオブジェクトが `AppServices.health_registry` にも格納される。結果として、ディスパッチゲーティング（`is_unavailable()`）はトランスポート層の失敗記録を同期ラグなしで即座に認識する。注意: レジストリオブジェクトの置き換えや再構築（例: 将来のリファクタリングで2番目の `McpServerHealthRegistry()` を構築）は、書き込み側と読み取り側の非同期を引き起こし、ディスパッチゲーティングの一貫性を壊す — 将来の変更ではこれを制約として考慮すること。

---

## Related Documents

- `04_mcp_00_document-guide.md`
- `04_mcp_03_01_dispatch-and-routing.md`
- `04_mcp_03_02_tool-registry.md`
- `04_mcp_03_03_transport-and-health-part2.md`
- `04_mcp_03_04_tool-call-tracing-and-watchdog.md`
- `04_mcp_03_05_lifecycle-and-new-server.md`

## Keywords

mcp
HttpTransport
McpServerHealthRegistry
health state
retry
correlation keys
