# Fix docs/03_rag_05_1 process-separation-policy: file-name typos and refiner_max_chars_per_chunk discrepancy

## Priority
High

## Summary
`docs/03_rag_05_1-configuration-reference.md`'s "プロセス分離ポリシー" (process separation policy) section — which documents that `rag_pipeline_mcp_server.toml` and `agent.toml` are fully independent and may hold different values for same-named keys, a genuinely easy-to-misunderstand and important point — uses shortened, incorrect filenames (`server.py`/`service.py`/`models.py`) instead of the actual (`rag_pipeline_server.py`/`rag_pipeline_service.py`/`rag_pipeline_models.py`). Additionally, `refiner_max_chars_per_chunk` has a code default of 800 but an operational value of 300 in `config/rag_pipeline_mcp_server.toml` — a discrepancy noted for other parameters in this file but missing for this one.

## Reason for Change
The filename errors are confirmed factual errors that would cause a developer to misidentify or confuse the wrong files during implementation work. The missing code-vs-operational discrepancy note for `refiner_max_chars_per_chunk` breaks the file's otherwise-consistent pattern of flagging such gaps, risking a chunk-size tuning decision based on the wrong (code-default) value.

## Implementation Intent
Correct the 3 filenames to their actual full names, and add the missing code-vs-operational discrepancy note for `refiner_max_chars_per_chunk`, matching the pattern already used for other parameters in this file.

## Target Files or Areas
`docs/03_rag_05_1-configuration-reference.md`

## Required Changes
- Replace `server.py`/`service.py`/`models.py` with `rag_pipeline_server.py`/`rag_pipeline_service.py`/`rag_pipeline_models.py`.
- Add: "`refiner_max_chars_per_chunk`: コードデフォルト800 / 運用設定値300(config/rag_pipeline_mcp_server.toml)。" matching this file's existing pattern for noting code-vs-operational discrepancies.

## Acceptance Criteria
No shortened/incorrect filename remains in this section; `refiner_max_chars_per_chunk`'s code-vs-operational discrepancy is noted consistently with other parameters.

## Testing Expectations
Not required (documentation-only). Manually re-verify the 3 filenames and the `refiner_max_chars_per_chunk` values (code default and `config/rag_pipeline_mcp_server.toml` value) before finalizing.

## Documentation Impact
`docs/03_rag_05_1` corrected.

## Out of Scope
Do not change the actual `refiner_max_chars_per_chunk` code default or operational value in this issue — documentation only.

## AI Implementation Instruction
This is a confirmed factual error (filenames) — apply directly. Re-verify the `refiner_max_chars_per_chunk` values against current code and config before adding the discrepancy note, in case they have changed since this review.

## Traceability
- Workflow phase: issue-creation
- Source: docs_review_rag.md §4 強化候補 (05_1 プロセス分離ポリシー), §6A (ファイル名の誤記, refiner_max_chars_per_chunkの乖離未記載)
- Generated at: 2026-08-02
