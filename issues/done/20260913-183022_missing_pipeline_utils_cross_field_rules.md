# Issue: Missing Documentation for RAG Pipeline Utils Canonical Artifact-Field Contract

## Summary
`docs/03_rag_02_03_ingestion_pipeline-chunksplitter.md` describes the canonical artifact-field contract but doesn't document the cross-field validation rules clearly.

## Evidence
- File: `docs/03_rag_02_03_ingestion_pipeline-chunksplitter.md`, section 3.4a
- Text: "Crawl artifacts do not carry `normalized_content` / `chunk_index` / `source_file` / `chunk_type` / `chunking_strategy` as input keys — `read_crawl_json()` sets these internally rather than reading them"
- The distinction between what's read from JSON vs set internally is important but buried in a note
- Cross-field rules (e.g., `content` empty only allowed when `code_blocks` non-empty) aren't prominently documented

## Impact
- Developers adding new fields must understand both required/nullable/conditional classification AND cross-field rules
- The internal field-setting logic is undocumented outside this section
- Future changes could break cross-field validation without awareness

## Recommended Action
Add a dedicated subsection titled "Cross-Field Validation Rules" that explicitly documents:
1. All cross-field dependencies between fields
2. When internal fields are set vs read from JSON
3. The rationale for each cross-field rule
4. Examples of valid/invalid payloads for each rule
