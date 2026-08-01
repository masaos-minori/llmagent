# Fix crawl depth/page-count numbers and dedupe query-pipeline stage/MCP-responsibility tables in docs/03_rag_01_system_overview-part2.md

## Priority
High

## Summary
`docs/03_rag_01_system_overview-part2.md` states crawl depth is "up to 6 hops" and page count is "up to 500 pages," but the actual `config/crawler.toml` values are `max_depth = 3` and `max_pages = 200` — and even the sibling detail file `docs/03_rag_02_02_ingestion_pipeline-crawler-part1.md` (3 hops) already contradicts this file's "6 hops" claim. Separately, this file's "query pipeline stage table" and "MCP server responsibility table" duplicate content from the canonical `docs/03_rag_03_01_query_pipeline-overview.md`, down to class names and the `rrf_k` default value.

## Reason for Change
The depth/page numbers are a confirmed factual error that would cause an operator to misjudge expected crawl load or coverage. The stage-table duplication doubles maintenance effort against the canonical `03_01` document.

## Implementation Intent
Correct the crawl depth/page numbers to match `config/crawler.toml`, explicitly distinguishing code-fallback values from operational config values. Compress the query-pipeline stage table and MCP-responsibility table to a stage-name-plus-one-line-summary, deferring detail to `03_01` and the relevant `03_02`-`03_05` detail files.

## Target Files or Areas
`docs/03_rag_01_system_overview-part2.md`

## Required Changes
- Replace "最大6ホップ" with: "クロール深度: config/crawler.tomlの運用値は3(max_depth=3)。コード側フォールバック値は別途存在するため、参照時は運用設定ファイルの値を優先する。"
- Replace "最大500ページ" with: "クロールページ数上限: 運用値は200(max_pages=200、config/crawler.toml)。500はコードのフォールバック値であり運用値ではない。"
- Compress the query-pipeline stage table to stage names + one-line descriptions, e.g. "MQE→検索→融合→リランク→補強の5ステージ。各ステージの詳細はdocs/03_rag_03_02〜03_05を参照。"
- Compress the MCP server responsibility table similarly, deferring detail to `docs/03_rag_03_01_query_pipeline-overview.md`.

## Acceptance Criteria
Crawl depth/page numbers match `config/crawler.toml` and are consistent with `docs/03_rag_02_02_ingestion_pipeline-crawler-part1.md`; the stage/responsibility tables are compressed with detail deferred to `03_01` and the relevant detail files.

## Testing Expectations
Not required (documentation-only). Manually re-verify current values in `config/crawler.toml` before finalizing, since they may have changed further since this review.

## Documentation Impact
`docs/03_rag_01_system_overview-part2.md` corrected and shortened.

## Out of Scope
Do not change `config/crawler.toml` values in this issue — documentation only. Do not edit `docs/03_rag_03_01_query_pipeline-overview.md` in this issue (it remains canonical as-is).

## AI Implementation Instruction
This is a confirmed factual error (depth/page numbers) — apply directly after re-verifying against current `config/crawler.toml`.

## Traceability
- Workflow phase: issue-creation
- Source: docs_review_rag.md §1 (横断的な確定済み誤り item 5), §3 要約候補 item 1, §5 例5, §6A (クロール深度・ページ数上限の食い違い)
- Generated at: 2026-08-02
