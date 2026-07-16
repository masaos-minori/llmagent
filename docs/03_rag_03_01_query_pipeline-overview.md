---
title: "RAG Query Pipeline"
category: rag
tags:
  - pipeline-overview
  - pipeline-stage
related:
  - 03_rag_00_document-guide.md
  - 03_rag_01_system_overview-part1.md
  - 03_rag_03_02_query_pipeline-rag-pipeline-class-part1.md
  - 03_rag_03_03_query_pipeline-context-and-diagnostics.md
  - 03_rag_03_04_query_pipeline-search-stages.md
  - 03_rag_03_05_query_pipeline-augment-stages.md
  - 03_rag_03_06_query_pipeline-helpers-and-cache-part1.md
  - 03_rag_03_07_query_pipeline-tests.md
  - 03_rag_04_05_dto-types.md
  - 03_rag_05_1-configuration-reference.md
source:
  - 03_rag_03_01_query_pipeline-overview.md
---

# RAG クエリパイプライン

- システム概要 → [03_rag_01_system_overview-part1.md](03_rag_01_system_overview-part1.md)
- 設定 → [03_rag_05_1-configuration-reference.md](03_rag_05_1-configuration-reference.md)
- 型定義 → [03_rag_04_05_dto-types.md](03_rag_04_01_dto-models_data.md)

---

## 1. パイプライン概要

`RagPipeline` は6つのステージを順に実行する（固定5つ + PluginHooks）。各ステージは
`PipelineStage` Protocolを実装し、共有される `PipelineContext` dataclassをインプレースで変更する。
PluginHooksは `PipelineStage` を実装しないため、独立したパスとして処理される。

```
RagPipeline.augment(query)
  → use_search=False? → ""を返す
  → rag_service_urlが設定されている? → call_rag_service() → 失敗時はインプロセス実行にフォールバック
  → run(query, db, history_context, hook_strict=False)
      [1] MqeStage         — クエリをN個のバリアントに展開する
      [2] SearchStage      — バリアントごとにKNN + BM25を実行する
      [3] FusionStage      — RRFによるマージ（Σ 1/(rrf_k+rank)；rrf_kは設定で変更可能、デフォルト: 60）
      [4] RerankStage      — クロスエンコーダによるスコアリング；rag_min_scoreでフィルタ；リランク後にchunk_id単位で重複排除
      [5] PluginHooks      — 登録済みのリランク後フック（エラーは分離される；strictモードでは再送出される）；PipelineStageではないため独自の実行パス
      [6] AugmentStage     — [RAG_CONTEXT_START]...[RAG_CONTEXT_END] 形式に整形する
  → use_refiner=True? → refine_context()（チャンクを圧縮；エラー時は生のチャンクにフォールバック）
  → コンテキストブロック文字列を返す
```

**呼び出し元:** `scripts/mcp_servers/rag_pipeline/service.py`（`RagPipelineMCPService`）。エージェントREPLは
`RagPipeline` を直接呼び出さない。

### augment() のフォールバックチェーン（`scripts/rag/pipeline.py`）

`augment()` は以下の順で結果を確定させる。各ステップは `None` を返した場合のみ次のステップにフォールバックする（Explicit in code）。

1. HTTPモード: `_run_http_augment()` → `str`（空文字含む）または `None`（フォールバック）
2. セマンティックキャッシュ: `semantic_cache.lookup()` がヒットすれば文字列を返す。ミス時は `None`
3. 検索パイプライン: MQE + KNN/BM25 + RRFマージ + リランク → `ctx.reranked`
4. リファイナー: `refine_context()` → 圧縮テキスト（確定）または `None`（フォールバック）
5. 生チャンク: `_format_chunks()`（`stages/augment.py` の関数）で整形（最終）

**identity vs truthiness（Explicit in code）:** HTTPおよびリファイナーの結果判定は `is not None` によるidentityチェックであり、truthinessチェックではない。そのためHTTPモードが返す `""`（空文字）は有効な結果として扱われ、明示的な `None` のときのみフォールバックする。

**DB接続失敗時（Explicit in code）:** `self._rag_db_path` からのDBオープンが `sqlite3.OperationalError` / `sqlite3.DatabaseError` を送出した場合、`augment()` は `RagPipelineError` を再送出する（キャッチしてフォールバックしない）。

### MCP サーバー呼び出しパス

```
MCP クライアント
  → scripts/mcp_servers/rag_pipeline/server.py (HTTP ルート)
    → RagPipelineMCPService.run_pipeline() (service.py)
      → RagPipeline.run() (scripts/rag/pipeline.py)
```

RagPipelineクラスの詳細 → [03_rag_03_02_query_pipeline-rag-pipeline-class-part1.md](03_rag_03_02_query_pipeline-rag-pipeline-class-part1.md)

---

## 2. PipelineStage Protocol (`scripts/rag/stage.py`)

```python
from rag.stage import PipelineStage, PipelineContext

class MyStage(PipelineStage):
    async def run(self, ctx: PipelineContext, **kwargs: object) -> None:
        ...
```

`kwargs` には `db: SQLiteHelper` などステージ固有の引数が渡される。
ステージは `ctx` をインプレースで変更し、値を返さない。

---

## Related Documents

- `03_rag_00_document-guide.md`
- `03_rag_01_system_overview-part1.md`
- `03_rag_03_02_query_pipeline-rag-pipeline-class-part1.md`
- `03_rag_03_03_query_pipeline-context-and-diagnostics.md`
- `03_rag_03_04_query_pipeline-search-stages.md`
- `03_rag_03_05_query_pipeline-augment-stages.md`
- `03_rag_03_06_query_pipeline-helpers-and-cache-part1.md`
- `03_rag_03_07_query_pipeline-tests.md`
- `03_rag_04_05_dto-types.md`
- `03_rag_05_1-configuration-reference.md`

## Keywords

pipeline-overview
pipeline-stage
rag
