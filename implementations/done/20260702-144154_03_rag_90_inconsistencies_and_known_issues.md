# Implementation Procedure: docs/03_rag_90_inconsistencies_and_known_issues.md

## Goal

Append two open design questions to the existing inconsistencies document:
- **OPEN-01**: CLI `main()` does not pass `on_ingest_complete` — semantic cache is not
  invalidated after CLI ingestion.
- **OPEN-02**: `delete_document()` in `RagPipelineMCPService` does not invalidate the
  semantic cache — stale entries may be served after document deletion.

These entries make the known gaps discoverable without requiring readers to trace call graphs.

## Scope

**In scope:**
- Additive edits to `docs/03_rag_90_inconsistencies_and_known_issues.md` only
- Two new entries under a "Cache Invalidation" section (or the nearest appropriate section)

**Out of scope:**
- Fixing the underlying gaps (separate feature request)
- Modifying any source file
- Editing any other documentation file

## Assumptions

1. `docs/03_rag_90_inconsistencies_and_known_issues.md` already exists and has an established
   section structure (numbered entries or heading-based).
2. The two entries are **additive only** — no existing content is modified or removed.
3. The document uses Markdown with heading levels already established.
4. "Recommended action" lines are acceptable per the plan's guidance to avoid the misread
   "no action needed".

## Implementation

### Target file

`docs/03_rag_90_inconsistencies_and_known_issues.md`

### Procedure

1. Read the entire file to understand the current section structure and numbering scheme.
2. Identify the correct location to insert: either after the last existing entry, or under an
   existing "Cache" or "RAG pipeline" section if present.
3. Append the two entries below, preserving the existing numbering/heading style.

### Method

Pure document edit — no code changes. Use the Edit tool to append the new section.

### Details

Append the following block (adjust heading level and numbering to match existing style):

```markdown
## Cache Invalidation

### OPEN-01: CLI ingestion does not invalidate the semantic cache

**Status:** Open design question
**Affected code:** `scripts/rag/ingestion/ingester.py` — `main()` at line 661
**Impact:** After a CLI `rag-ingest` run, any running `RagPipeline` instance (e.g. inside
the MCP server) retains stale semantic cache entries. Subsequent queries may return cached
results that no longer reflect the updated document corpus.
**Root cause:** `main()` calls `ingester.ingest_all(args.force)` without passing an
`on_ingest_complete` callback. The callback is the only mechanism for post-ingestion cache
invalidation.
**Recommended action:** Pass `pipeline.semantic_cache.invalidate` as `on_ingest_complete`
in callers that require fresh results immediately after ingestion.

---

### OPEN-02: `delete_document()` does not invalidate the semantic cache

**Status:** Open design question
**Affected code:** `scripts/mcp/rag_pipeline/service.py` — `delete_document()`
**Impact:** After a document is deleted via `rag_delete_document` MCP tool, cached semantic
search results that referenced the deleted document remain in `SemanticCache` until the
next `invalidate()` call or process restart.
**Root cause:** `delete_document()` removes DB rows but does not call
`pipeline.semantic_cache.invalidate()`. No other invalidation path exists in the MCP service.
**Recommended action:** Call `self.pipeline.semantic_cache.invalidate()` at the end of
`delete_document()`, or document that callers must trigger cache invalidation separately.
```

## Validation plan

| Step | Command | Expected result |
|------|---------|----------------|
| File exists | `ls docs/03_rag_90_inconsistencies_and_known_issues.md` | exists |
| Content present | `grep "OPEN-01" docs/03_rag_90_inconsistencies_and_known_issues.md` | match found |
| Content present | `grep "OPEN-02" docs/03_rag_90_inconsistencies_and_known_issues.md` | match found |
| Lint | `ruff check docs/` (if applicable) | no errors |
| Pre-commit | `pre-commit run --all-files` | pass |
