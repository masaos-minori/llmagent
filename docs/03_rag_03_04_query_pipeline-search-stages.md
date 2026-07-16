---
title: "RAG Query Pipeline - Search Stages"
category: rag
tags:
  - mqe-stage
  - search-stage
  - fusion-stage
related:
  - 03_rag_00_document-guide.md
  - 03_rag_01_system_overview-part1.md
  - 03_rag_03_01_query_pipeline-overview.md
  - 03_rag_03_02_query_pipeline-rag-pipeline-class-part1.md
  - 03_rag_03_05_query_pipeline-augment-stages.md
  - 03_rag_03_03_query_pipeline-context-and-diagnostics.md
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

## 5. ステージの詳細

### 5.1 MqeStage

```python
MqeStage(cfg: RagConfig, llm: RagLLM)
```

- `use_mqe=False`: `ctx.queries = [ctx.query]` を設定する（単一クエリ、展開なし）
- `use_mqe=True`: `RagLLM.expand_queries(query)` を呼び出し `ctx.queries` へ格納する（コンテキストは直接のパラメータではなく、cfgのプロンプトテンプレートを介して適用される）；LLM失敗時は `RagExpansionError` を発生させる
- `mqe_n_queries` の設定でバリアント数を制御する

### 5.2 SearchStage

```python
SearchStage(cfg: RagConfig, http: httpx.AsyncClient | None = None, embed_url: str = "")
```

- `ctx.queries` 内のすべてのクエリに対して並列に埋め込みを生成する
- DB検索は逐次実行する（競合を避けるためクエリごとに1接続）
- 各クエリは `ctx.search_results` に0〜2件の `list[RawHit]` を追加する（KNN + BM25）；埋め込み失敗またはDBエラーの場合は空
- KNN: sqlite-vecによる `vector_search(embedding, top_k)`
- BM25: FTS5による `fts_search(query, top_k)`
- `/opt/llm/logs/search.log` にログを記録: 埋め込み失敗の警告、検索の劣化警告（embed_failed件数、FTSエラー件数）
- `db=None` の場合は警告付きで空の結果を返して処理する

> **ドキュメントと実装の矛盾**: `vector_search`/`fts_search` が送出する `sqlite3.OperationalError` /
> `RuntimeError` は `SearchStage` 内部（`_search_all_queries()`）で捕捉され、クエリ単位で
> `fts_errors` カウンタに計上されるのみで、例外として呼び出し元（`RagPipeline._run_stage()`）へは
> 伝播しない。1クエリの検索失敗は残りのクエリの処理を止めない
> (根拠分類: Explicit in code — `scripts/rag/stages/search.py:56-65`)。
>
> **注記（2026-07-13）:** `RagPipeline.search_queries()` と `RagPipeline.rerank_candidates()` メソッドは
> `pipeline.py` に定義されているが、いずれも呼び出し側が存在しない（デッドコード）。
> 実際の検索・リランク処理は `SearchStage.run()` → `_search_all_queries()` および
> `RerankStage.run()` → `_rerank()` で実行される。

#### 失敗時の意図 (Failure behavior)

`_search_all_queries()` は埋め込み取得（`asyncio.gather(..., return_exceptions=True)`）とDB検索
（`try/except`）の両方で例外を個別に握りつぶし、`SearchDiagnostics` のカウンタに反映するのみで
処理を継続する。これは、MQEで複数バリアントに展開したクエリのうち一部が失敗しても、
残りのクエリの検索結果でパイプライン全体を継続させるための設計と考えられる
(根拠分類: Strongly implied by code — 各クエリのループ内で個別に例外処理し、失敗時も
`continue`/ループ継続する構造)。

### 5.3 FusionStage

```python
FusionStage(rrf_k: int = 60, use_rrf: bool = True)
```

- Reciprocal Rank Fusionを用いて `ctx.search_results` をマージする: score = Σ 1/(rrf_k + rank)
- `rrf_k` のデフォルト: 60；`cfg.rrf_k` で変更可能（RagConfig Protocolに `rrf_k` フィールドが含まれる）
- 各 `MergedHit` に `rrf_score` を割り当て、`ctx.merged` に格納する

> `use_rrf=False` は重複排除のみのフォールバックを発動させる（すべて `rrf_score=0.0`）。`pipeline.py:294` がRRF設定フラグを `FusionStage` に渡す。

#### 検索品質のトレードオフ: `use_rrf=False` と `use_rrf=True`

> **警告:** `use_rrf=False` は無害なフォールバックではなく、**大幅な品質低下**を意味する。
> ランク信号は完全に無効化される: MQEによる複数クエリ展開は追加的なランキング効果を持たなくなる。
> 診断目的、またはレイテンシを最小化する必要があり検索品質を犠牲にできる場合にのみ使用すること。

| モード | 仕組み | 品質への影響 |
|---|---|---|
| `use_rrf=True`（デフォルト） | RRF: 各ヒットを全結果リストにわたって `Σ 1/(rrf_k + rank)` でスコア付けする | 複数クエリで見られたチャンクが優先される；リスト横断で堅牢なランキングを行う |
| `use_rrf=False` | 重複排除のみ: chunk_idで重複排除し、最初に出現したものが優先される；すべてのヒットは `rrf_score=0.0` になる | ランク信号なし；MQEの結果は追加的なランキング効果を持たない |

**`use_rrf=False` の場合:**
- `chunk_id` による重複排除；結果リスト全体で最初に出現したものが優先される
- マージ後のすべてのヒットが `rrf_score=0.0` になる — ランクによる重み付けスコアリングは行われない
- MQEによって生成された複数クエリの結果は**追加的なランキング効果を持たない**: 3つのクエリで
  見られたチャンクも、1つのクエリでしか見られなかったチャンクと同じスコアになる
- 推奨: 埋め込み/FTSのオーバーヘッドを最小化する必要があり検索品質を犠牲にできる場合を除き、
  `use_rrf=True`（デフォルト）を維持すること

**可観測性:**
- `/rag search --debug` は `[debug] fusion: use_rrf=False (rank signal disabled)` を表示する
- `get_diagnostics()["fusion_mode"]` は `"rrf"` または `"dedup_only"` を返す
- ログ: `INFO FusionStage: dedup-only mode (use_rrf=False) — rank signal disabled, MQE provides no ranking benefit`
- 起動時: `WARNING rag config warning: use_rrf=false degrades retrieval quality; use only for diagnostics`（パイプライン初期化時に `config_validator.py` 経由で出力される）

---

## Related Documents

- `03_rag_00_document-guide.md`
- `03_rag_01_system_overview-part1.md`
- `03_rag_03_01_query_pipeline-overview.md`
- `03_rag_03_02_query_pipeline-rag-pipeline-class-part1.md`
- `03_rag_03_05_query_pipeline-augment-stages.md`
- `03_rag_03_03_query_pipeline-context-and-diagnostics.md`
- `03_rag_04_05_dto-types.md`
- `03_rag_05_1-configuration-reference.md`

## Keywords

mqe-stage
search-stage
fusion-stage
rag
