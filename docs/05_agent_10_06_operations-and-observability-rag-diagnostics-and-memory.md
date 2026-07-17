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
  - 05_agent_10_04_operations-and-observability-validation-and-troubleshooting-part1.md
  - 05_agent_10_05_operations-and-observability-monitoring.md
source:
  - 05_agent_10_01_operations-and-observability-startup-and-health.md
---

# Agent Operations and Observability

- 設定 → [05_agent_08_04_configuration-mcp-approval-obs.md](05_agent_08_04_configuration-mcp-approval-obs.md)

## RAG パイプライン診断

### RAGデバッグトレースの出力(現状未到達)

以下の構造化デバッグトレースは`CLIView.write_debug_rag(data)`(`agent/cli_view.py`)として
定義されているが、現行コードにこのメソッドの呼び出し箇所は存在しない。スラッシュコマンドとして
`/rag`は登録されておらず、`/debug`がトグルする`ctx.conv.debug_mode`もRAGパイプライン側
(`scripts/rag/`)のどこからも参照されていない — `/stats`出力での表示のみに使われる
(`agent/commands/cmd_config_stats.py`)。したがって、この出力形式は現状どの操作からも
到達不能である。(Explicit in code — 2026-07-17時点で直接確認済み)

以下は`write_debug_rag()`が受け取るデータ構造を示す想定出力例。

```
  [debug] RRF config: use_rrf=True rrf_k=60
  [debug] MQE queries (2):
    1: what is the retry policy
    2: retry policy configuration
  [debug] search: 2 result lists, 18 total candidates
  [debug] RRF merge: 12 unique candidates (top 5):
    chunk_id=4821 rrf=0.0312 url=file:///opt/llm/docs/config.md
    ...
  [debug] reranked top-5:
    chunk_id=4821 score=0.9241 url=file:///opt/llm/docs/config.md
    ...

  --- Stage timings ---
    MqeStage: 142.3 ms
    SearchStage: 38.1 ms
    FusionStage: 2.4 ms
    RerankStage: 95.7 ms

  --- Fallbacks / Failures ---
    RerankStage [fallback]: use_rerank=False
```

### ステージ結果の解釈

| Stage | `"success"` | `"fallback"` | `"failure"` |
|---|---|---|---|
| `MqeStage` | MQE queries generated | `use_mqe=False`; original query used | LLM call failed |
| `SearchStage` | Results returned | No matching chunks (empty result) | DB error or embedding failure |
| `FusionStage` | RRF merge applied | `use_rrf=False`; raw results used | Merge error |
| `RerankStage` | Cross-encoder rerank applied | `use_rerank=False`; RRF scores used | LLM call failed |
| `HttpAugment` | Remote RAG service returned result | `http_result_kind`: `"remote_nonempty"` (success) / `"remote_empty"` (valid empty) / `"in_process_fallback"` (failure) | HTTP error / no context |
| `Refiner` | Refiner compressed chunks | `"refiner_returned_empty"` (empty output) or `"refiner_exception: {e}"` (LLM error) | LLM call failed |

### StageResult のフィールド

各パイプライン実行は `pipeline.last_stage_results`（`StageResult` の dict のリスト）を生成する。

| Field | Type | Description |
|---|---|---|
| `stage_name` | str | ステージのクラス名（例: `"MqeStage"`） |
| `status` | str | `"success"`、`"fallback"`、または `"failure"` |
| `elapsed_seconds` | float | このステージの実時間（秒） |
| `fallback_reason` | str or None | status が `"fallback"` または `"failure"` の場合の理由文字列 |

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

スタンドアロンの RAG 取り込みパイプライン（`scripts/rag/ingestion/crawler.py`）は、URL ごとの進捗とサマリー行を出力する。

```
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

---

## メモリステータス（`/memory status`）

出力例。

```
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

---

## グレースフルシャットダウン

- `SIGTERM` → `agent.py` によって `SystemExit(0)` に変換される
- シャットダウンフラグが立つ → `AgentREPL._read_input()` は、ブロッキングする `input()` 呼び出しと
  `_shutdown_event.wait()`（`asyncio.wait(FIRST_COMPLETED)`）を競合させる。シャットダウン
  イベントが先に完了した場合、`_read_input()` は次のキー入力を待たずに即座に `None` を返す。
  取り残された `input()` の executor スレッドは中断されず、プロセス終了時に
  終了する。
- `finally` ブロック:
  - セッション診断の永続化 → `DiagnosticStore.save(kind="session_summary")` 経由で `session_diagnostics` テーブルにランタイムサマリーを書き込む
  - `memory.on_session_stop()` → メモリの抽出と永続化
  - リソースのクリーンアップ → readline history の保存、`lifecycle.shutdown_all()`、HTTP クライアントのクローズ
- `shutdown_all()` は実行中、追加の `SIGINT`(2回目のCtrl-C等)を一時的に吸収し、全MCPサブプロセスの終了処理が中断されずに完了することを保証する(完了後は通常の割り込み処理に戻る)

## Related Documents

- `05_agent_00_document-guide.md`
- `05_agent_10_01_operations-and-observability-startup-and-health.md`
- `05_agent_10_02_operations-and-observability-audit-and-otel.md`
- `05_agent_10_03_operations-and-observability-workflow-observability.md`
- `05_agent_10_04_operations-and-observability-validation-and-troubleshooting-part1.md`
- `05_agent_10_05_operations-and-observability-monitoring.md`

## Keywords

RAG pipeline diagnostics
stage result interpretation
memory status
graceful shutdown
