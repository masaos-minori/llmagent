---
title: "Agent Operations and Observability - RAG Diagnostics and Memory"
category: agent
tags:
  - agent
  - operations
  - rag-diagnostics
  - memory-status
  - graceful-shutdown
related:
  - 05_agent_00_document-guide.md
  - 05_agent_10_01_operations-and-observability-startup-and-health.md
  - 05_agent_10_02_operations-and-observability-audit-and-otel.md
  - 05_agent_10_03_operations-and-observability-workflow-observability.md
  - 05_agent_10_04_operations-and-observability-validation-and-troubleshooting.md
  - 05_agent_10_05_operations-and-observability-monitoring.md
source:
  - 05_agent_10_01_operations-and-observability-startup-and-health.md
---

# エージェントの運用と可観測性

- 設定 → [05_agent_08_04_configuration-mcp-approval-obs.md](05_agent_08_04_configuration-mcp-approval-obs.md)

## RAG パイプライン診断

### ステージ結果の解釈

| Stage | `"success"` | `"fallback"` | `"failure"` |
|---|---|---|---|
| `MqeStage` | MQE queries generated | `use_mqe=False`; original query used | LLM call failed |
| `SearchStage` | Results returned | No matching chunks (empty result) | DB error or embedding failure |
| `FusionStage` | RRF merge applied | `use_rrf=False`; raw results used | Merge error |
| `RerankStage` | Cross-encoder rerank applied | `use_rerank=False`; RRF scores used | LLM call failed |
| `HttpAugment` | Remote RAG service returned result | `http_result_kind`: `"remote_nonempty"` (success) / `"remote_empty"` (valid empty) / `"in_process_fallback"` (failure) | HTTP error / no context |
| `Refiner` | Refiner compressed chunks | `"refiner_returned_empty"` (empty output) or `"refiner_exception: {e}"` (LLM error) | LLM call failed |

### ステータス値

| Status | Meaning |
|---|---|
| `success` | ステージが正常に完了した |
| `fallback` | 設定フラグ（例: `use_rrf=False`）によりステージがバイパスされた |
| `failure` | ステージが例外を発生させ、パイプラインは低下した出力のまま継続した |

### Refiner と HTTP フォールバックのステージ

該当する場合、`last_stage_results` にさらに2つのエントリが現れる。

| stage_name | Appears when | fallback_reason on fallback |
|---|---|---|
| `HttpAugment` | `rag_service_url` が設定されている場合 | `http_result_kind`: `"remote_nonempty"` / `"remote_empty"` / `"in_process_fallback"` |
| `Refiner` | `use_refiner=True` の場合 | `"refiner_returned_empty"`（空の出力）または `"refiner_exception: {e}"`（LLM エラー） |

### RAG 取り込み診断

スタンドアロンの RAG 取り込みパイプラインは、URL ごとの進捗とサマリー行を出力する。

``` text
[ingest] crawling https://example.com/docs (lang=en)...
[ingest] splitting chunks...
[ingest] 12 chunks written
[ingest] ingesting to DB...
inserted 10/12 chunks: https://example.com/docs/page1
inserted 8/8 chunks: https://example.com/docs/page2
inserted 0/5 chunks: https://example.com/docs/page3  <- skipped (already registered)
=== done: 3 URLs processed (18 success, 0 failed, 1 skipped) ===
```

| Field | Description |
|---|---|
| `inserted N/M chunks: <url>` | N 個のチャンクが埋め込まれた、M はクロール JSON 内の総数。0/M は URL がスキップされたことを意味する（`--force` なしで既に DB に存在） |
| `done: X URLs processed` | この実行における全 URL グループの集計 |
| `success` | 埋め込みと保存に成功したチャンク |
| `failed` | 埋め込みまたは DB 書き込みに失敗したチャンク |
| `skipped` | URL が既に `documents` に存在するためスキップされた URL グループ（再埋め込みするには `--force` を使用） |

## メモリステータス（`/memory status`）

出力例。

``` text
Field                   Value
----------------------  --------------------------------------------------
Mode                    Hybrid mode (semantic + FTS)
Memory layer            enabled
Embedding enabled       Yes
Local-only              enabled
Circuit                 closed
Consecutive failures    0
FTS fallback count      2
Last retrieval mode     hybrid
Entries (total)         142
  semantic              89
  episodic              53
Embed skip count        8
  source:RULE           34
  source:DECISION       22
  source:FAILURE        15
  source:CONVERSATION   71
```

- **Mode** ラベル: `Hybrid mode (semantic + FTS)` | `Memory enabled, embedding disabled (FTS-only)` | `Degraded mode (circuit open, FTS fallback)` | `Memory layer disabled`
- **Local-only**: `config/agent.toml` で `memory_local_only = true` の場合に `enabled`
- **FTS fallback count**: 埋め込みが利用不可で FTS のみが使用されたセッション数
- **Embed skip count**: 埋め込みなしで保存されたエントリ数（circuit open または embed disabled による）

## グレースフルシャットダウン

- `SIGTERM` → `agent.py` によって `SystemExit(0)` に変換される
- シャットダウンフラグが立つ → REPL入力は、ブロッキングする `input()` 呼び出しと `_shutdown_event.wait()`（`asyncio.wait(FIRST_COMPLETED)`）を競合させる。シャットダウンイベントが先に完了した場合、入力は次のキー入力を待たずに即座に `None` を返す。取り残された `input()` の executor スレッドは中断されず、プロセス終了時に終了する。
- `finally` ブロック:
  - セッション診断の永続化 → `DiagnosticStore.save(kind="session_summary")` 経由で `session_diagnostics` テーブルにランタイムサマリーを書き込む
  - `memory.on_session_stop()` → メモリの抽出と永続化
  - リソースのクリーンアップ → readline history の保存、`lifecycle.shutdown_all()`、HTTP クライアントのクローズ
- `shutdown_all()` は実行中、追加の `SIGINT`(2回目のCtrl-C等)を一時的に吸収し、全MCPサブプロセスの終了処理が中断されずに完了することを保証する(完了後は通常の割り込み処理に戻る)

## 関連資料

- [05_agent_10_01_operations-and-observability-startup-and-health.md](05_agent_10_01_operations-and-observability-startup-and-health.md) — 起動とヘルスチェック
- [05_agent_10_02_operations-and-observability-audit-and-otel.md](05_agent_10_02_operations-and-observability-audit-and-otel.md) — 監査ログとOTel
- [05_agent_10_03_operations-and-observability-workflow-observability.md](05_agent_10_03_operations-and-observability-workflow-observability.md) — ワークフローの可観測性
- [05_agent_10_04_operations-and-observability-validation-and-troubleshooting.md](05_agent_10_04_operations-and-observability-validation-and-troubleshooting.md) — 追加検証とトラブルシューティング
- [05_agent_10_05_operations-and-observability-monitoring.md](05_agent_10_05_operations-and-observability-monitoring.md) — モニタリング
