# Issue: Missing Documentation for RAG DTO Models Result Implementation Notes

## Summary
`docs/03_rag_04_02_dto-models_result.md` contains implementation notes about SearchDiagnostics fields that aren't clearly connected to the main DTO description.

## Evidence
- File: `docs/03_rag_04_02_dto-models_result.md`, Implementation Notes section
- Text: "The fields `result_source`, `http_result_kind`, `remote_status_code`, `remote_latency_ms`, and `fallback_reason` in `SearchDiagnostics` are categorized as 'Remote mode fields (new)' in the code comments (Explicit in code, `scripts/rag/models_result.py`). While `embed_ok`, `embed_failed`, and `fts_errors` are existing counters from local execution, the remote fields were added after the introduction of the HTTP RAG service."
- The distinction between local and remote mode fields is important but buried in implementation notes rather than prominently documented

## Impact
- Developers adding new diagnostic fields must know which category they belong to
- The historical context of why certain fields exist is undocumented elsewhere
- Future developers may not understand the evolution of the DTO

## Recommended Action
Move the implementation notes into the main DTO description table. Add a clear section header distinguishing "Local Execution Counters" from "Remote Mode Fields (added after HTTP introduction)". Document the migration path and rationale for the separation.
