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
  - 03_rag_03_query_pipeline-stages.md
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

すべてのSQLを保有する。ステージから内部的に使用される。可観測性のため、呼び出しごとにquery / fts_query / top_k / elapsed_msをログに記録する。

**SQLクエリ:**

| メソッド | SQL |
|---|---|
| `vector_search` | `SELECT c.chunk_id, c.content, d.url, d.title, cv.distance FROM chunks_vec cv JOIN chunks c ON c.chunk_id = cv.chunk_id JOIN documents d ON d.doc_id = c.doc_id WHERE cv.embedding MATCH ? ORDER BY cv.distance LIMIT ?` |
| `fts_search` | `SELECT c.chunk_id, c.content, d.url, d.title, bm25(chunks_fts) AS bm25_score FROM chunks_fts JOIN chunks c ON c.chunk_id = chunks_fts.rowid JOIN documents d ON d.doc_id = c.doc_id WHERE chunks_fts MATCH ? ORDER BY bm25(chunks_fts) LIMIT ?` |

**日本語FTS5のトークン化:**

| 定数 | 値 | 説明 |
|---|---|---|
| FTS5クエリ内のトークン数上限 | 20 | |
| 日本語トークンとして保持されるSudachiの品詞カテゴリ | `{"名詞", "動詞", "形容詞"}` | |

**Sudachiの遅延ロード:**

Sudachiは初回使用時にロードされる。辞書: `core`、SplitMode: `C`。

| メソッド | シグネチャ | 説明 |
|---|---|---|
| `tokenize_pos_filter` | `(text: str, keep_pos: frozenset[str]) -> list[str]` | part_of_speech()[0]がkeep_posに含まれるトークンについて normalized_form() を返す；トークナイズ失敗時はRuntimeErrorを発生させる |

**公開メソッド:**

| メソッド | シグネチャ | 説明 |
|---|---|---|
| `vector_search` | `(embedding: list[float], top_k: int) -> list[RagHit]` | sqlite-vecによるKNN；`distance` フィールドを持つRawHitを返す；`top_k`/`hits`/`elapsed_ms` をログに記録する |
| `fts_search` | `(query: str, top_k: int) -> list[RagHit]` | FTS5によるBM25；`bm25_score` フィールドを持つRawHitを返す；FTS構文エラー時は `sqlite3.OperationalError` を発生させる（呼び出し元が処理する）；`query`/`fts_query`/`top_k`/`hits`/`elapsed_ms` をログに記録する |

**モジュールレベルの単独ラッパー:**
- `vector_search(embedding, top_k, db)` → `RagRepository(db).vector_search()` に委譲する
- `fts_search(query, top_k, db)` → `RagRepository(db).fts_search()` に委譲する
- `fetch_full_document(chunk_id, db, window=None)` → 同一ドキュメントのチャンクを`chunk_index`昇順で取得する；`window=N` → ±N
- `deduplicate_chunks(hits, max_per_doc)` → 同一URLのヒット数を制限する；入力は降順にソートされている必要がある
- `cosine_sim(a, b) -> float` → コサイン類似度；ゼロベクトルの場合は `0.0` を返す

### 7.2 RagScorer (`scripts/rag/repository.py`)

| メソッド | シグネチャ | 説明 |
|---|---|---|
| `rrf_merge`（静的メソッド） | `(results_list: list[list[RawHit]] \| list[list[RagHit]], rrf_k: int = 60) -> list[RagHit]` | RRFスコア Σ 1/(rrf_k+rank)；降順；`rrf_score` を割り当てる；RawHitまたはRagHitの結果リストを受け入れる |

### 7.3 RagLLM (`scripts/rag/llm_client.py`)

実装は以下にある。

- `scripts/rag/llm_client.py` — `RagLLM` クラス、`get_embedding()`、`summarize_tool_result()`
- `scripts/rag/llm_prompts.py` — プロンプトテンプレート、`RagExpansionError`、`RagRerankError`、`MqeParseError`

```python
from rag.llm_client import RagLLM
llm = RagLLM(client=http_client, llm_url="http://127.0.0.1:8001/v1/chat/completions")
```

**注記:** `scripts/rag/llm_client.py:48-50` には `logger = logging.getLogger(__name__)` の行が重複している — 2番目の代入が最初のものを上書きする。1つだけあれば十分である。

| メソッド | シグネチャ | 説明 |
|---|---|---|
| `expand_queries` | `async (query: str, context: str = "") -> list[str]` | MQE；HTTP失敗、接続エラー、またはパース失敗時に `RagExpansionError` を発生させる |
| `cross_encoder_rerank` | `async (query: str, candidates: list[RagHit], top_k: int, rag_min_score=0.0) -> list[RagHit]` | クロスエンコーダ；HTTP失敗、接続エラー、またはパース失敗時に `RagRerankError` を発生させる；`rag_min_score` でフィルタする |
| `summarize_tool_result` | `async (text: str, tool_name: str, args: dict[str, object]) -> str` | LLM経由でツール出力を要約する；HTTPまたはパースの失敗時に例外を発生させる — 処理方法の判断は呼び出し元に委ねられる |
| `refine_context` | `async (chunks: list[RagHit], query: str, max_tokens: int, per_chunk_chars: int, timeout: float) -> str` | 単一のLLM呼び出しでチャンクをクエリに関連する要点に圧縮する；エラー時に例外を発生させ呼び出し元がフォールバックできるようにする |

**モジュールレベルの関数:**

| 関数 | シグネチャ | 説明 |
|---|---|---|
| `get_embedding` | `async (text, client, embed_url) -> list[float]` | テキストを埋め込みベクトルに変換する；`"query: "` プレフィックスを使用する（E5の規約）；HTTP失敗または埋め込みフィールドの欠落/空の場合に例外を発生させる |
| `summarize_tool_result` | `async (text, tool_name, args, client, llm_url=None) -> str` | 単独利用可能な要約処理；`None` の場合はキャッシュされた設定から `llm_url` をロードする；LLM呼び出し失敗時に例外を発生させる |

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
    result_source: str | None = None
```

`RagPipeline.run()` が返す。**`result_source` は常に `None`** である — `run()` はこれを設定することがない。このフィールドは、HTTPモードでHTTPのaugmentハンドラが `dataclasses.replace()` により設定する場合のためだけに存在する。

---

## Related Documents

- `03_rag_00_document-guide.md`
- `03_rag_01_system_overview-part1.md`
- `03_rag_03_01_query_pipeline-overview.md`
- `03_rag_03_03_query_pipeline-context-and-diagnostics.md`
- `03_rag_03_query_pipeline-stages.md`
- `03_rag_04_05_dto-types.md`
- `03_rag_05_1-configuration-reference.md`
- `03_rag_03_06_query_pipeline-helpers-and-cache-part1.md`

## Keywords

semantic-cache
rag-repository
rag-scorer
rag-llm
rag
