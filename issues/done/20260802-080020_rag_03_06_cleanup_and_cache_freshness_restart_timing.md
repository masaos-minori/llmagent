# Simplify docs/03_rag_03_06 (parts 1+2) method/SQL tables; document CLI-ingest cache-freshness restart requirement

## Priority
High

## Summary
`docs/03_rag_03_06_query_pipeline-helpers-and-cache-part1.md` and `-part2.md` transcribe `SemanticCache`/`RagRepository` methods and SQL queries verbatim. Separately, the "CLIインジェスト後のキャッシュ鮮度" (cache freshness after CLI ingest) section identifies a genuinely important operational pitfall — a process-boundary state-management issue — but doesn't specify exactly when a restart is required (i.e., that after a CLI re-ingest, a running query process's `SemanticCache` is not automatically invalidated).

## Reason for Change
The method/SQL tables are mechanical code transcription. The cache-freshness gap is explicitly flagged by this review as "運用上の最重要注意点" (the most important operational caution point) — an operator who doesn't know a running query process must be restarted (or explicitly invalidated) after a CLI re-ingest could serve stale search results indefinitely without realizing it.

## Implementation Intent
Remove the mechanical tables, keeping each class's one-sentence responsibility plus the most important design judgments (cache freshness, `result_source` confusion risk — tracked in a separate issue). Add the specific restart/invalidation timing detail to the cache-freshness section.

## Target Files or Areas
`docs/03_rag_03_06_query_pipeline-helpers-and-cache-part1.md`, `docs/03_rag_03_06_query_pipeline-helpers-and-cache-part2.md`

## Required Changes
- Remove verbatim method/SQL-query tables in both parts; keep each class's one-sentence responsibility summary (e.g. "RagRepository: DBアクセスを集約するヘルパー層") and pointer to source/Reference API for exact signatures.
- Add to the cache-freshness section: "CLIでの再インジェクション後、稼働中のクエリプロセスのSemanticCacheは自動的には無効化されない。反映させるにはプロセス再起動または明示的な`invalidate()`呼び出しが必要。" — verify this claim against actual `SemanticCache` implementation before finalizing.

## Acceptance Criteria
No verbatim method/SQL table remains; the cache-freshness section states the exact restart/invalidation requirement, verified against source.

## Testing Expectations
Not required (documentation-only). Manually verify `SemanticCache`'s invalidation behavior (or lack thereof) against source before finalizing.

## Documentation Impact
Both parts of `docs/03_rag_03_06` corrected and shortened.

## Out of Scope
Do not resolve the `result_source` dual-definition question in this issue — tracked separately. Do not implement automatic cache invalidation in this issue — documentation only, reflecting current reality.

## AI Implementation Instruction
Verify the cache-invalidation claim directly against `SemanticCache`'s source before finalizing — this is flagged as the domain's most important operational caution and must not be asserted without confirmation.

## Traceability
- Workflow phase: issue-creation
- Source: docs_review_rag.md §3 要約候補 item 7, §4 強化候補 (03_06-part1 キャッシュ鮮度)
- Generated at: 2026-08-02
