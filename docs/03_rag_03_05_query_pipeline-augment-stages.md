---
title: "RAG Query Pipeline - Augment Stages"
category: rag
tags:
  - rerank-stage
  - augment-stage
related:
  - 03_rag_00_document-guide.md
  - 03_rag_01_system_overview-part1.md
  - 03_rag_03_01_query_pipeline-overview.md
  - 03_rag_03_04_query_pipeline-search-stages.md
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

### 5.4 RerankStage

```python
RerankStage(cfg: RagConfig, llm: RagLLM)
```

- `use_rerank=False`: RRF順で上位 `rag_top_k` を返す（スライス） + `deduplicate_chunks`
- `use_rerank=True`: `RagLLM.cross_encoder_rerank(query, candidates, top_k, rag_min_score)`；LLM失敗時は `RagRerankError` を発生させる
- `rag_min_score` によりフィルタする；クロスエンコーダの失敗時にフォールバックはない（例外が伝播する）
- 重複排除: `deduplicate_chunks(hits, max_chunks_per_doc)` — 同一URLのヒット数を制限する；関数自体はソート済み入力を必須としないが、呼び出し元はリランク後の降順結果を渡すため、上位チャンクのみが残る；リランクの後に適用される（前ではない）

**例外の捕捉位置（Explicit in code）:** `RerankStage.run()` 自体は例外を捕捉しない。`RagPipeline` が `run()` の実行を try/except で包み、`RuntimeError`（`RagRerankError` の基底）・`sqlite3.OperationalError`・`httpx.HTTPStatusError`・`httpx.RequestError`・`TimeoutError` を捕捉して `StageResult(status="failure", fallback_reason=<例外メッセージ>)` に変換する。したがってパイプライン全体としては例外で停止せず、後続ステージ（AugmentStage）は空の `ctx.reranked` を引き継いで実行が継続する。

### 5.5 AugmentStage

コンストラクタなし（`PipelineStage` を継承）。

**訂正（Explicit in code）:** チャンク整形関数の重複は解消済みである。`scripts/rag/stages/augment.py:11` のチャンク整形関数が唯一の実装であり、`scripts/rag/pipeline.py` はこれを `_augment_format_chunks` としてimportして使う（`from rag.stages.augment import _format_chunks as _augment_format_chunks`）。AugmentStage（augment.py内）と `RagPipeline.augment()` の生チャンクフォールバック（pipeline.py 461行目付近）はいずれも同一関数を呼び出す。

- `ctx.reranked` を `[Source: {title if title else url} | {url}]\n{sanitize_document(content)}` の形式のブロックとして整形する；titleが空の場合はURLをフォールバックとして使用する
- `\n\n---\n\n` で連結し、`[RAG_CONTEXT_START]` / `[RAG_CONTEXT_END]` で囲む
- `ctx.augment_result` に格納する
- 整形前に `rag.utils` の `sanitize_document(c.content)` でコンテンツをサニタイズする
- rerankedが空の場合は `[RAG_CONTEXT_START]\n\n[RAG_CONTEXT_END]` を返す

**コンテンツのみの不変条件（DESIGN-2）:** AugmentStageは `content` のみを整形し、`normalized_content` は決して使用しない。

- `chunks.content` は元のチャンクテキストであり、LLMコンテキストとして使用される**唯一の**テキストである
- `chunks.normalized_content` はSudachiで正規化された日本語テキストで、FTS5の検索インデックス用途に**限定して**使用される；LLMコンテキストに出現してはならない
- `content` を `normalized_content` に置き換えると、LLMコンテキストの品質が低下する（Sudachi正規化されたテキストは元の可読性を失う）
- RAGコンテキストブロックには常に元の読みやすいチャンクテキストが含まれなければならない

#### RefineResult dataclass (`scripts/rag/pipeline_refiner.py`)

```python
from rag.pipeline_refiner import RefineResult
```

| フィールド | 型 | 説明 |
|---|---|---|
| `text` | `str \| None` | 要約されたコンテキストテキスト；失敗時は `None`（生のチャンクへフォールバック） |
| `reason` | `str \| None` | 失敗理由；成功時は `None`；フォールバック時は `"refiner_returned_empty"` または `"refiner_exception: ..."` |

#### リファイナーのフォールバック理由

`use_refiner=true` で要約処理が失敗した場合、`augment()` は生チャンクの
整形処理にフォールバックする。フォールバック理由は `last_stage_results` と
`get_diagnostics()["fallback_reasons"]` に記録される。

| 理由 | 条件 |
|---|---|
| `refiner_returned_empty` | LLMレスポンスの内容が `.strip()` 後に `""` または空白のみである。`if refined:` のガードがFalseと評価される。よくある原因: コンテンツポリシーによる拒否、空のLLM生成、抜き出せる要点がないプロンプト形式。 |
| `refiner_exception: {e}` | LLM呼び出し中に `httpx.HTTPStatusError`、`httpx.RequestError`、または `ValueError` が発生した。例外メッセージが理由文字列に含まれる。リトライは行われない。 |

**リトライなしの方針**: リファイナーの失敗は致命的でない品質低下として扱われる — 生チャンクを出力として許容する。失敗したLLM呼び出しをリトライしても、期待される効果は低い一方でレイテンシが増加する（一時的なエラーは稀であり、コンテンツポリシーによる拒否はリトライしても成功しない）。劣化した出力を許容できない場合は `use_refiner=false` でリファイナーを完全に無効化すること。

いずれの理由も以下で確認できる。
- アプリケーションログでINFOレベルで表示される（`augment: refiner fallback (reason=...)`）
- `/rag search` の出力で `[warn] refiner fallback: <reason>` として表示される
- `/rag search --debug` のステージ結果で `~ Refiner: fallback — <reason>` およびサマリー行 `[refiner] fallback: N time(s)` として表示される
- `pipeline.get_diagnostics()["fallback_reasons"]`、`["refiner_fallback_count"]`、`["refiner_exception_count"]` から取得可能

**`get_diagnostics()` の関連フィールド（Explicit in code、`scripts/rag/pipeline.py`）:**

| キー | 説明 |
|---|---|
| `refiner_fallback_count` | Refinerステージが `status="fallback"` になった回数 |
| `refiner_returned_empty` | 上記のうち `fallback_reason == "refiner_returned_empty"` の件数 |
| `refiner_exception_count` | 上記のうち `fallback_reason` が `"refiner_exception:"` で始まる件数 |
| `refiner_exception` | `refiner_exception_count > 0` の真偽値 |

---

## Related Documents

- `03_rag_00_document-guide.md`
- `03_rag_01_system_overview-part1.md`
- `03_rag_03_01_query_pipeline-overview.md`
- `03_rag_03_04_query_pipeline-search-stages.md`
- `03_rag_03_03_query_pipeline-context-and-diagnostics.md`
- `03_rag_04_05_dto-types.md`
- `03_rag_05_1-configuration-reference.md`
- `03_rag_03_06_query_pipeline-helpers-and-cache-part1.md`
- `03_rag_03_06_query_pipeline-helpers-and-cache-part2.md`

## Keywords

rerank-stage
augment-stage
refiner-fallback
rag
