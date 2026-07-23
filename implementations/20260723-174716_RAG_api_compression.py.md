## Goal

Compress implementation-derived API signatures, public method tables, DTO field listings, TypedDict listings, dataclass listings, and JSON examples in 16 RAG design documents into concise Japanese design summaries while preserving caller-visible behavior, responsibility boundaries, failure behavior, data ownership, persistence semantics, search-quality-sensitive fields, compatibility-sensitive fields, security-sensitive fields, and important invariants.

## Scope

**In**:
- Compress exhaustive API and data model reference details in 16 RAG documents
- Replace with Japanese design summaries under suggested section headings (`## 主要入口`, `## 呼び出し側に影響する挙動`, `## 責務境界`, `## 失敗時の挙動`, `## 実装詳細の参照先`, `## データ構造の目的`, `## 設計上重要なフィールド`, `## 永続化・検索・互換性に関わる制約`, `## 使用してはいけない境界`)
- Preserve specific RAG design constraints (e.g., `RagPipeline.augment()`, `None` vs empty string behavior, database failure handling, cache invalidation, `content` vs `normalized_content`, deletion order)

**Out**:
- Modifying source code
- Creating ADR documents
- Modifying `00_index.md`
- Resolving any individual NC items
- Removing design intent, responsibility boundaries, invariants, failure behavior, or operational constraints

## Assumptions

1. All sixteen target RAG documents exist at their expected paths.
2. The existing API/data model listings can be safely compressed without losing design-relevant information.

## Design decisions

- Group DTOs by purpose rather than listing each field individually.
- Use exact Japanese section headings as specified in the requirement where they improve clarity.
- Preserve all design-relevant content including: caller-visible behavior, responsibility boundaries, failure behavior, data ownership, persistence semantics, search-quality-sensitive fields, compatibility-sensitive fields, security-sensitive fields, and important invariants.
- Keep implementation notes that describe design rationale; only compress field-level detail.

## Alternatives considered

- Delete API/data model details entirely: loses caller-visible contract information.
- Create separate API reference documents: fragments documentation unnecessarily.
- Keep full listings but add navigation links: doesn't reduce cognitive load.

## Implementation

### Target file

16 RAG documents: `docs/03_rag_02_01_ingestion_pipeline-overview.md`, `docs/03_rag_02_02_ingestion_pipeline-crawler-part1.md`, `docs/03_rag_02_02_ingestion_pipeline-crawler-part2.md`, `docs/03_rag_02_03_ingestion_pipeline-chunksplitter-part1.md`, `docs/03_rag_02_03_ingestion_pipeline-chunksplitter-part2.md`, `docs/03_rag_02_04_ingestion_pipeline-ingester-part1.md`, `docs/03_rag_02_04_ingestion_pipeline-ingester-part2.md`, `docs/03_rag_02_05_ingestion_pipeline-document-manager.md`, `docs/03_rag_03_02_query_pipeline-rag-pipeline-class-part1.md`, `docs/03_rag_03_02_query_pipeline-rag-pipeline-class-part2.md`, `docs/03_rag_03_03_query_pipeline-context-and-diagnostics.md`, `docs/03_rag_04_01_dto-models_data.md`, `docs/03_rag_04_02_dto-models_result.md`, `docs/03_rag_04_03_dto-models_audit.md`, `docs/03_rag_04_04_dto-models_config.md`, `docs/03_rag_04_05_dto-types.md`

### Procedure

1. Verify all sixteen target documents exist at expected paths
2. For each document:
   a. Read the document and identify the API/data model detail sections
   b. Classify each candidate before editing: design-relevant vs implementation-derived
   c. Compress implementation-derived details into Japanese design summaries
   d. Apply suggested section headings where appropriate
   e. Add source references where appropriate
3. Verify preservation of specific RAG design constraints listed in scope

### Method

Replace detailed field-by-field tables with responsibility-oriented groupings.

### Details

For `03_rag_04_01_dto-models_data.md`, replace the detailed field tables with:

```markdown
# 6.1 models_data.py (`scripts/rag/models_data.py`)

## データ構造の目的

このファイルはRAGパイプライン全体で共有されるデータモデルを定義する。
すべてのDTOは `@dataclass(frozen=True)` として定義されており、生成後の書き換えを禁止する。

## 設計上重要なフィールド

### EmbeddingResponse — 埋め込みAPIからのレスポンス
- `embedding`: 埋め込みベクトル（必須）
- `model`: モデル名（省略可）

### CrawlTarget — WebCrawlerのクロール対象
- `url`: クロール対象URL（必須）
- `lang`: 言語ヒント（`LanguageCode` enum、`"en"`/`"ja"`）

### ChunkDocument — パイプラインステージ間で受け渡されるチャンクデータ
- `url`, `title`, `lang`, `content`: 必須フィールド
- `etag`, `last_modified`: 更新検知用
- `normalized_content`: Sudachi正規化済みテキスト（日本語のみ）
- `chunking_strategy`, `source_file`, `chunk_type`: 処理メタデータ

### ChunkRecord — 埋め込みベクトル付きチャンク（クエリパイプライン使用）
- `chunk_id`, `url`, `title`, `lang`, `content`: 必須フィールド
- `embedding`: 埋め込みベクトル

### CacheEntry — セマンティックキャッシュエントリ
- `embedding`, `context_str`: 必須フィールド
- `history_context`: 関連会話履歴
- `generation`: キャッシュ無効化用世代カウンタ

### TwoStageFetchResult — HTTP RAGサービス呼び出し結果
- `hits`: インプロセス時は `RagHit`、HTTPモード時は `dict`（型が異なる）
- `min_score_applied`, `max_chunks_per_doc`: フィルタリングパラメータ

## 永続化・検索・互換性に関わる制約

- `ChunkDocument.normalized_content` は日本語のみ有効
- `TwoStageFetchResult.hits` の要素型は呼び出しモードによって異なる（`RagHit` / `dict`）
- `CrawlTarget.lang` は `LanguageCode` enum、他DTOの `lang` は素の `str`（型不統一に注意）
```

Apply similar compression to remaining fifteen documents following the same pattern, adapting section headings based on which are relevant for each document.

## Compatibility considerations

None — documentation-only change; no behavioral impact.

## Security considerations

N/A — documentation-only change.

## Rollback considerations

Restore original API/data model details from git history; no data migration or config changes required.

## Validation plan

| Check | Tool | Target |
|---|---|---|
| Markdown rendering | Manual review | Correct rendering |
| Content preservation | Manual review | No design-relevant content loss |
| Listing reduction | Manual review | Significant reduction achieved |
| RAG constraint verification | Manual review | All specific RAG design constraints preserved |

## Out of scope

- Modifying source code
- Creating ADR documents
- Modifying `00_index.md`
- Resolving any individual NC items
- Removing design intent, responsibility boundaries, invariants, failure behavior, or operational constraints

## Traceability

- Workflow phase: plan-to-implementation-procedure
- Source issue: N/A
- Source requirement: N/A
- Source plan: plans/20260723-165723_plan.md
- Source implementation procedure: N/A
- Generated at: 20260723-174716
- Related target files: Implementation-dependent — RAG design documents
