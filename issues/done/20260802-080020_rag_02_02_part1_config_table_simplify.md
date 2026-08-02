# Simplify docs/03_rag_02_02-part1: remove method/utility tables, dedupe config-parameter table with 05_1

## Priority
Medium

## Summary
`docs/03_rag_02_02_ingestion_pipeline-crawler-part1.md` contains verbatim "public methods" and "module-level utility" tables (mechanical signature listings), and a 9-item configuration-parameter table that duplicates the canonical `docs/03_rag_05_1-configuration-reference.md`, without distinguishing code-fallback values from operational config values.

## Reason for Change
The method/utility tables are code-derived detail with no unique design value. The config-parameter table's duplication with `05_1` doubles maintenance effort, and the missing code-vs-operational-value distinction (a stated domain-wide concern in this review) risks readers citing the wrong value.

## Implementation Intent
Remove the method/utility tables, keeping the one-line BFS-strategy/concurrency-control design summary. Reduce the config-parameter table to only the items directly relevant to understanding this module's responsibility (`max_depth`, `max_pages`, `skip_nofollow`), explicitly distinguishing code-fallback vs. operational values, and defer the full parameter list to `05_1`.

## Target Files or Areas
`docs/03_rag_02_02_ingestion_pipeline-crawler-part1.md`

## Required Changes
- Remove the "public methods" and "module-level utility" tables; keep the BFS-strategy/concurrency-control one-line design summary.
- Reduce the configuration-parameter table to `max_depth`, `max_pages`, `skip_nofollow`, each explicitly labeled with its code-fallback value vs. its operational value in `config/crawler.toml`.
- Add a reference to `docs/03_rag_05_1-configuration-reference.md` for the full parameter list.

## Acceptance Criteria
No verbatim method/utility table remains; the config-parameter table is reduced to the 3 responsibility-relevant items with code-vs-operational values explicitly distinguished, referencing `05_1` for the rest.

## Testing Expectations
Not required (documentation-only). Manually re-verify the 3 kept parameters' code-fallback and operational values against source/config before finalizing.

## Documentation Impact
`docs/03_rag_02_02_ingestion_pipeline-crawler-part1.md` shortened and corrected.

## Out of Scope
Do not edit `docs/03_rag_05_1-configuration-reference.md` in this issue (its own fixes are tracked separately).

## AI Implementation Instruction
Verify code-fallback vs. operational values directly against source/config before writing the distinction — do not assume the values stated in this review are still current.

## Traceability
- Workflow phase: issue-creation
- Source: docs_review_rag.md §2 削除候補 item 1, §3 要約候補 item 3
- Generated at: 2026-08-02
