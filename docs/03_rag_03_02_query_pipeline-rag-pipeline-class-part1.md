---
title: "RAG Query Pipeline - RagPipeline Class Detail (Part 1)"
category: rag
tags:
  - rag-pipeline-class
  - http-mode
related:
  - 03_rag_00_document-guide.md
  - 03_rag_01_system_overview-part1.md
  - 03_rag_03_01_query_pipeline-overview.md
  - 03_rag_03_03_query_pipeline-context-and-diagnostics.md
  - 03_rag_03_06_query_pipeline-helpers-and-cache-part1.md
  - 03_rag_04_05_dto-types.md
  - 03_rag_05_1-configuration-reference.md
source:
  - 03_rag_03_02_query_pipeline-rag-pipeline-class-part1.md
---

# RAG クエリパイプライン

- システム概要 → [03_rag_01_system_overview-part1.md](03_rag_01_system_overview-part1.md)
- 設定 → [03_rag_05_1-configuration-reference.md](03_rag_05_1-configuration-reference.md)
- 型定義 → [03_rag_04_05_dto-types.md](03_rag_04_01_dto-models_data.md)

---

## 2. RagPipeline クラス (`scripts/rag/pipeline.py`)

```python
from rag.pipeline import RagPipeline, RagPipelineError
```

> **ドキュメントと実装の矛盾**: `fetch_full_document` は `rag/pipeline.py` からは提供されない。実体は
> `rag/repository.py` で定義されている（`from rag.repository import fetch_full_document`）。
> `sanitize_document` も同様に `rag/utils.py` の関数であり `rag.pipeline` には存在しない。
> テスト・実装コードでの実際のインポートは `from rag.pipeline import RagPipeline, RagPipelineError` のみ。
> (根拠分類: Explicit in code — `scripts/rag/pipeline.py` のimport文、`scripts/rag/repository.py:232`)

### コンストラクタ

| パラメータ | 型 | 説明 |
|---|---|---|
| `http` | `httpx.AsyncClient` | LLM/埋め込み呼び出し用のHTTPクライアント |
| `cfg` | `RagConfig` | agent.tomlから読み込まれるRAG設定 |
| `module_cfg` | `dict \| None` | 任意の設定オーバーライド；load_all() / agent.toml（エージェントプロセス経路）をバイパスする；Noneの場合は内部モジュール設定の取得にフォールバックする |
| `on_status` | `Callable[[str], None] \| None` | 進行状況コールバック；デフォルトはno-op |
| `on_clear` | `Callable[[], None] \| None` | クリーンアップコールバック；`run()`/`augment()` の `finally` ブロックで常に呼び出される |

```python
RagPipeline(
    http: httpx.AsyncClient,
    cfg: RagConfig,
    *,
    module_cfg: dict | None = None,
    on_status: Callable[[str], None] | None = None,
    on_clear: Callable[[], None] | None = None,
)
```

### 公開属性

| 属性 | 型 | 説明 |
|---|---|---|
| `last_fetch_result` | `TwoStageFetchResult \| None` | 直前の `run()`/`augment()` によるリランク済みヒット。`hits`、`min_score_applied`、`max_chunks_per_doc` を保持する |
| `last_timings` | `dict[str, float]` | 直前の `run()` の各ステージの実測秒数 |
| `last_stage_results` | `list[StageResult]` | 直前の `run()` のステージごとの結果記録（status、fallback reason、elapsed） |
| `semantic_cache` | `SemanticCache` | インメモリの最近傍キャッシュ |
| `last_search_diagnostics` | `SearchDiagnostics` | 直前の `run()` の検索診断情報；HTTPモード用に `result_source`、`http_result_kind`、`remote_status_code`、`remote_latency_ms`、`fallback_reason` を含む |
| `stat_search_embed_failed` | `int` | このインスタンス上のすべての `run()` 呼び出しにおける埋め込み失敗の累積数 |
| `stat_search_fts_errors` | `int` | このインスタンス上のすべての `run()` 呼び出しにおけるFTSエラーの累積数 |

### 公開メソッド

| メソッド | シグネチャ | 説明 |
|---|---|---|
| `run` | `async (query, db, history_context="", hook_strict=False) -> PipelineRunResult` | MQE→search→RRF→rerank+PluginHooksを実行する；`PipelineRunResult`（queries、search_results、merged、reranked、stage_results、diagnostics）を返す；**`result_source` は設定しない** — ローカルモードでは常に `None`；`hook_strict=True` の場合は最初のプラグインフック失敗を再送出する（デフォルト: 警告をログに記録しスキップ）；`finally` で常に `on_clear()` を呼び出す |
| `augment` | `async (query, debug_fn=None, history_context="") -> str` | パイプライン全体 + Augmentステージを実行する；コンテキストブロック文字列または `""` を返す；DB失敗時は `RagPipelineError` を発生させる |
| `search_queries` | `async (queries, db) -> list[list[RagHit]]` | 単独利用可能なヘルパー: 並列埋め込み + 逐次DB検索；`SearchDiagnostics` を記録するSearchStageとは異なり、**診断情報を記録しない** |
| `rerank_candidates` | `async (query, merged) -> list[RagHit]` | 単独利用可能なヘルパー: クロスエンコーダ、またはスライス+重複排除によるフォールバック + 重複排除 |
| `get_diagnostics` | `() -> dict` | 直前のパイプライン実行に関する構造化された診断情報を返す；`run()`/`augment()` の前に呼び出しても安全 — 空/ゼロ値を返す |
| `invalidate_cache` | `() -> None` | `semantic_cache`（`SemanticCache`）を全消去する；コーパスを変更する操作（例: MCPの`rag_delete_document`）の後に呼び出すことを想定；`SemanticCache.invalidate()` はスレッドセーフ (根拠分類: Explicit in code — `scripts/rag/pipeline.py:606-614` のdocstring) |

### 実装意図 (Implementation note)

- `invalidate_cache()` はこのパイプラインインスタンスが認識しているコーパス変更後にのみ呼び出される想定であり、
  呼び出し側（MCPサービス層など）がコーパス変更操作を検知して明示的に呼び出す設計になっている。パイプライン自身が
  DB変更を検知して自動的にキャッシュを無効化する仕組みは持たない (根拠分類: Strongly implied by code — docstringの
  "Call after any corpus-changing operation this pipeline instance is aware of" という記述)。

## Related Documents

- `03_rag_00_document-guide.md`
- `03_rag_01_system_overview-part1.md`
- `03_rag_03_01_query_pipeline-overview.md`
- `03_rag_03_03_query_pipeline-context-and-diagnostics.md`
- `03_rag_03_query_pipeline-stages.md`
- `03_rag_03_06_query_pipeline-helpers-and-cache-part1.md`
- `03_rag_04_05_dto-types.md`
- `03_rag_05_1-configuration-reference.md`
- `03_rag_03_02_query_pipeline-rag-pipeline-class-part2.md`

## Keywords

rag-pipeline-class
http-mode
rag
