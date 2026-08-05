---
title: "RAG Query Pipeline - Helpers and Cache (Part 2)"
category: rag
tags:
  - semantic-cache
  - rag-repository
  - rag-scorer
  - rag-llm
related:
  - 03_rag_00_document-guide.md
  - 03_rag_01_system_overview-part1.md
  - 03_rag_03_01_query_pipeline-overview.md
  - 03_rag_03_03_query_pipeline-context-and-diagnostics.md
  - 03_rag_04_05_dto-types.md
  - 03_rag_05_1-configuration-reference.md
source:
  - 03_rag_03_06_query_pipeline-helpers-and-cache-part1.md
---

# RAG クエリパイプライン

- システム概要 → [03_rag_01_system_overview-part1.md](03_rag_01_system_overview-part1.md)
- 設定 → [03_rag_05_1-configuration-reference.md](03_rag_05_1-configuration-reference.md)
- 型定義 → [03_rag_04_05_dto-types.md](03_rag_04_01_dto-models_data.md)

---

## 7. ヘルパークラス

### 7.1 RagRepository (`scripts/rag/repository.py`)

全てのSQLを管理する。可観測性のため、呼び出しごとに query / fts_query / top_k / elapsed_ms をログに記録する。詳細な実装とシグネチャについては scripts/rag/repository.py を参照してください。

**日本語FTS5のトークン化:**

FTS5クエリのトークン数上限は 20 であり、日本語トークンとしては Sudachi の品詞カテゴリ（`{"名詞", "動詞", "形容詞"}`）が使用されます。詳細は `scripts/rag/repository.py` を参照してください。
**Sudachiの遅延ロード:**

Sudachiは初回使用時にロードされる。辞書: `core`、SplitMode: `C`。`tokenize_pos_filter(text, keep_pos)` は `part_of_speech()[0]` が `keep_pos` に含まれるトークンについて `normalized_form()` を返し、トークナイズ失敗時は `RuntimeError` を発生させる。詳細は `scripts/rag/repository.py` を参照してください。

**公開メソッド:**

詳細は `scripts/rag/repository.py` を参照してください。

- `vector_search`: `sqlite-vec` による KNN 実装。
- `fts_search`: FTS5 による BM25 実装。FTS構文エラー時は `sqlite3.OperationalError` を発生させる（呼び出し元が処理する）。

**モジュールレベルの単独ラッパー:**
- `vector_search(embedding, top_k, db)` → `RagRepository(db).vector_search()` に委譲する
- `fts_search(query, top_k, db)` → `RagRepository(db).fts_search()` に委譲する
- `fetch_full_document(chunk_id, db, window=None)` → 同一ドキュメントのチャンクを`chunk_index`昇順で取得する；`window=N` → ±N
- `deduplicate_chunks(hits, max_per_doc)` → 同一URLのヒット数を制限する；入力は降順にソートされている必要がある
- `cosine_sim(a, b) -> float` → コサイン類似度；ゼロベクトルの場合は `0.0` を返す

### 7.2 RagScorer (`scripts/rag/repository.py`)

`rrf_merge`（静的メソッド）により、複数の検索結果リストを RRF（Reciprocal Rank Fusion）を用いてマージします。詳細は `scripts/rag/repository.py` を参照してください。

### 7.3 RagLLM (`scripts/rag/llm_client.py`)

実装は以下にある。

- `scripts/rag/llm_client.py` — `RagLLM` クラス、`get_embedding()`、`summarize_tool_result()`
- `scripts/rag/llm_prompts.py` — プロンプトテンプレート、`RagExpansionError`、`RagRerankError`、`MqeParseError`

```python
from rag.llm_client import RagLLM
llm = RagLLM(client=http_client, llm_url="http://127.0.0.1:8080/v1/chat/completions")
```

**訂正（Explicit in code）:** `logger = logging.getLogger(__name__)` の重複は解消済みである。現在は `scripts/rag/llm_client.py` に1箇所のみ存在する。

`RagLLM` は、MQE によるクエリ展開 (`expand_queries`)、クロスエンコーダによる再ランキング (`cross_encoder_rerank`)、ツール出力の要約 (`summarize_tool_result`)、およびコンテキストのリファイニング (`refine_context`) を提供します。詳細なシグネチャについては `scripts/rag/llm_client.py` を参照してください。

また、`get_embedding` や `summarize_tool_result` といったモジュールレベルの関数も提供されています。これらについても `scripts/rag/llm_client.py` を参照してください。

### 7.4 PipelineRunResult (`scripts/rag/types.py`)

```python
@dataclass
class PipelineRunResult:
    queries: list[str]
    search_results: list[list[RawHit]]
    merged: list[RagHit]
    reranked: list[RagHit]
    stage_results: list[StageResult]
    diagnostics: SearchDiagnostics
```

`RagPipeline.run()` が返す。

**混同注意:** 名前が同じ `result_source` でも型が異なる2つのフィールドが存在する。
- `SearchDiagnostics.result_source: ResultSource`（`rag/models_result.py`）— `ResultSource.LOCAL`（既定）/ `REMOTE` / `FALLBACK` を取り、HTTP augment実行時に `dataclasses.replace()` で更新する

---

## Related Documents

- `03_rag_00_document-guide.md`
- `03_rag_01_system_overview-part1.md`
- `03_rag_03_01_query_pipeline-overview.md`
- `03_rag_03_03_query_pipeline-context-and-diagnostics.md`
- `03_rag_03_04_query_pipeline-search-stages.md`
- `03_rag_03_05_query_pipeline-augment-stages.md`
- `03_rag_04_05_dto-types.md`
- `03_rag_05_1-configuration-reference.md`
- `03_rag_03_06_query_pipeline-helpers-and-cache-part1.md`

## Keywords

semantic-cache
rag-repository
rag-scorer
rag-llm
rag
