# Issue: Missing Documentation for RAG WebCrawler Local File Injection Responsibility Boundaries

## Summary
`docs/03_rag_02_02_ingestion_pipeline-crawler.md` describes local file injection but doesn't clearly separate responsibilities between `WebCrawler.crawl_file()` and `DocumentManager._is_file_unchanged()`.

## Evidence
- File: `docs/03_rag_02_02_ingestion_pipeline-crawler.md`, section 2.1.2
- Text: "`crawl_file()` only calculates the mtime (ISO string) and SHA-256 hash of the file content and stores them in the `last_modified` and `etag` fields of the crawl payload; it does not perform any skip/decision logic."
- The decision on whether to skip or re-ingest is made by `DocumentManager._is_file_unchanged()`/`_handle_existing_file()` in `scripts/rag/ingestion/document_manager.py`
- This responsibility boundary is important but buried in a note rather than prominently documented

## Impact
- Developers modifying either component must understand the shared contract
- The boundary between calculation and decision is critical for correct behavior
- Future developers may assume `crawl_file()` makes decisions when it doesn't

## Recommended Action
Add a dedicated subsection titled "Responsibility Boundary: Calculation vs Decision" that explicitly documents:
1. What `crawl_file()` does (calculation only)
2. What `DocumentManager` does (decision making)
3. The contract between them (SHA-256 hash comparison)
4. Why this separation exists (separation of concerns, testability)
