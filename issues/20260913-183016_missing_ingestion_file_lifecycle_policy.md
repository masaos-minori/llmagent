# Issue: Missing Documentation for RAG Ingestion Pipeline Overview File Lifecycle

## Summary
`docs/03_rag_02_01_ingestion_pipeline-overview.md` describes the file lifecycle but doesn't document the retention/deletion policy for processed chunks moved to `rag-src/registered/`.

## Evidence
- File: `docs/03_rag_02_01_ingestion_pipeline-overview.md`, File Lifecycle section
- Text: "| `{rag_src_dir}/registered/{stem}-{idx:04d}.json` | ingester.py | Chunk → Registered |"
- This is the same issue as NC-026 in the Known Issues inventory, but it should be elevated to a Known Issue since it affects operational behavior
- No retention period, deletion trigger, or deletion owner is documented anywhere in the RAG Specification set

## Impact
- Without a documented policy, `rag-src/registered/` may grow unbounded
- Files may be deleted ad hoc without a way to trace ingestion history
- Operators cannot plan disk space requirements

## Recommended Action
Add a dedicated subsection documenting:
1. Retention period for registered chunk files
2. Deletion triggers (e.g., periodic cleanup, manual operation)
3. Deletion ownership (who is responsible — ingester, cron job, operator)
4. Any correlation with source document lifecycle
