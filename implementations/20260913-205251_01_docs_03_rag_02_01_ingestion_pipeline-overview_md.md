## Goal

Improve the verification command documentation in `docs/03_rag_02_01_ingestion_pipeline-overview.md` so operators can reliably verify JSON artifacts without confusion about binary mode requirements or expected output format, per REQ-001 through REQ-005.

## Scope

- In-Scope: Improving the File Lifecycle section in `docs/03_rag_02_01_ingestion_pipeline-overview.md` with better verification guidance; adding concrete working example, binary mode explanation, expected output format description, orjson rationale
- Out-of-Scope: Modifying any source code files; modifying other documentation files; creating new helper scripts (deferred as optional enhancement)

## Assumptions

- The existing verification command structure (`orjson.loads()`) should be preserved rather than replaced with an alternative approach
- A concise inline improvement (approximately 5-10 sentences total) is sufficient — the goal is operator usability, not exhaustive documentation
- Helper script creation (REQ-005) is optional and should be evaluated based on whether the inline improvements alone are adequate

## Design decisions

1. Enhance the existing inline command rather than replacing it — keep the compact form for quick reference while adding a separate expanded example block.
2. Use the actual JSON key structures from `pipeline_utils.py` as the basis for the expected output format description.
3. Keep the explanation concise — approximately 5-10 sentences total — since this is a practical operational guide, not a deep dive into `orjson`.
4. Defer helper script creation (REQ-005) unless inline improvements prove insufficient.

Evidence grounding:
- `pipeline_utils.py:106`: `raw = path.read_bytes()` — confirms binary mode is necessary because `orjson.loads()` accepts `bytes` input directly
- `pipeline_utils.py:110`: `data = orjson.loads(raw)` — confirms the function signature expects bytes
- Crawl JSON keys: `url`, `content`, `title`, `lang`, `code_blocks`, `etag`, `last_modified`, `fetched_at`
- Chunk JSON keys: `url`, `content`, `title`, `lang`, `code_blocks`, `etag`, `last_modified`, `normalized_content`, `chunk_index`, `source_file`, `chunk_type`, `chunking_strategy`, `fetched_at`
- `orjson` rationale: faster serialization/deserialization, deterministic output ordering, strict JSON compliance — all confirmed by its usage pattern across the RAG module

## Alternatives considered

- **Replace `orjson.loads()` with `json.load()`**: Rejected because the Plan's design decision preserves the existing command structure — changing the library would alter the operator's mental model and require different error handling.
- **Create a dedicated helper script**: Deferred as optional (REQ-005); inline improvements should address the immediate pain points first before introducing additional tooling.
- **Add a full JSON schema dump**: Rejected because the Plan limits scope to ~5-10 sentences of explanation — the detailed schema belongs in the referenced pipeline_utils.py, not the overview doc.

## Implementation
### Target file
`docs/03_rag_02_01_ingestion_pipeline-overview.md`

### Procedure
1. Verify current state of File Lifecycle section
2. Add concrete working example with placeholder file path
3. Explain why binary mode ('rb') is required for orjson.loads()
4. Add expected output format description using representative JSON keys
5. Add brief explanation of why orjson is used instead of standard json
6. Evaluate whether a helper script is needed (REQ-005)

### Method
Inline text addition within the existing File Lifecycle section.

### Details
1. **Phase 1: Preparation — Confirm current state**
   a. Locate the File Lifecycle section in `docs/03_rag_02_01_ingestion_pipeline-overview.md` (line 77 contains only a brief inline command)
   b. Read `scripts/rag/ingestion/pipeline_utils.py` lines 100-160 to confirm binary mode usage and crawl JSON schema
   c. Read `scripts/rag/ingestion/pipeline_utils.py` lines 163-199 to confirm chunk JSON schema
   d. Review `orjson` usage patterns in `crawler.py`, `chunk_splitter.py`, `file_routing.py`, `crawl_persister.py` to confirm consistent binary-mode usage
   
2. **Phase 2: Core Implementation**
   a. Below the existing inline command, add a concrete working example with placeholder file path:
      ```markdown
      **Example:** To verify a crawl artifact:
      
      ```bash
      python -c "import orjson; print(orjson.loads(open('/path/to/crawl_<timestamp>.json', 'rb').read()))"
      ```
      
      Replace `/path/to/crawl_<timestamp>.json` with the actual file path.
      ```
   
   b. Add explanation of why binary mode ('rb') is required:
      ```markdown
      **Note:** The `'rb'` (binary read) mode is required because `orjson.loads()` accepts `bytes` input directly, unlike Python's standard `json.load()` which reads text. This matches how the ingestion pipeline writes these files — all use `orjson.dumps()` with binary write (`wb`).
      ```
   
   c. Add expected output format description using representative JSON keys:
      ```markdown
      **Expected output:** A valid JSON object. For crawl artifacts, look for keys: `url`, `content`, `title`, `lang`, `code_blocks`, `etag`, `last_modified`, `fetched_at`. For chunk artifacts, look for additional keys: `normalized_content`, `chunk_index`, `source_file`, `chunk_type`, `chunking_strategy`.
      ```
   
   d. Add brief explanation of why orjson is used:
      ```markdown
      **Why `orjson`?** The ingestion pipeline uses `orjson` (not the standard `json` module) for faster serialization/deserialization, deterministic output ordering, and strict JSON compliance. These properties ensure consistency when reading back artifacts written by the pipeline.
      ```
   
   e. Evaluate whether a helper script is needed (REQ-005):
      - If inline improvements above are deemed sufficient, skip this step
      - If a helper script is proposed, define its purpose and scope:
        - Purpose: Provide a simple CLI tool for verifying JSON artifacts without manual command construction
        - Scope: Accept a file path argument, read in binary mode, parse with orjson, display formatted output
        - Location: Would belong in `scripts/rag/ingestion/` alongside other ingestion utilities

3. **Phase 3: Verification**
   a. Confirm the improved documentation accurately reflects the source code evidence
   b. Confirm no unintended modifications were made to other files

## Compatibility considerations

- The inline summary supplements, not replaces, the existing cross-reference — operators can still navigate to the detailed document for deeper understanding
- Terminology choices ("HTTP route handling", "pipeline orchestration", "core search logic") align with the source code's own descriptions and the existing cross-referenced document
- No behavioral change — this is documentation-only

## Security considerations

N/A: Documentation update only, no security impact.

## Rollback considerations

Simple revert of the added text — no data migration or state rollback needed.

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| docs/03_rag_02_01_ingestion_pipeline-overview.md | Manual review against source code evidence | Read target files + compare | Improved documentation matches actual behavior |

## Completion criteria

- [ ] Verification command includes a concrete working example with placeholder file path
- [ ] Explanation of why binary mode ('rb') is required for orjson.loads() is present
- [ ] Expected output format description is included
- [ ] Explanation of why orjson is used instead of the standard json module is added
- [ ] If a helper script is proposed, its purpose and scope are clearly defined
- [ ] No source code files are modified
- [ ] No other documentation files are modified except docs/03_rag_02_01_ingestion_pipeline-overview.md

## Out of scope

- Modifying `scripts/rag/ingestion/pipeline_utils.py` (reference file only)
- Modifying `scripts/rag/ingestion/crawler.py` (reference file only)
- Modifying `scripts/rag/ingestion/chunk_splitter.py` (reference file only)
- Modifying `scripts/rag/ingestion/file_routing.py` (reference file only)
- Modifying `scripts/rag/ingestion/crawl_persister.py` (reference file only)
- Modifying other documentation files
- Creating new helper scripts (optional enhancement, deferred)
- Full JSON schema dump (too verbose for overview doc)

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Verify existing inline command at line 77 | Completed | 20260913-235106 | 20260913-235106 | Record exact wording |
| 2 | Add concrete working example with placeholder path | Completed | 20260913-235106 | 20260913-235106 | Example: /path/to/crawl_<timestamp>.json |
| 3 | Explain binary mode ('rb') requirement | Completed | 20260913-234918 | 20260913-234918 | orjson.loads() accepts bytes |
| 4 | Add expected output format description | Completed | 20260913-234927 | 20260913-234927 | Crawl: 8 keys; Chunk: 12 keys |
| 5 | Explain orjson vs json rationale | Completed | 20260913-234936 | 20260913-234936 | Performance, determinism, strict compliance |
| 6 | Evaluate REQ-005 helper script necessity | Completed | 20260913-235038 | 20260913-235038 | Optional, defer if inline suffices |
| 7 | Manual review of accuracy against source code | Completed | 20260913-235106 | 20260913-235106 | Verify all claims |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: REQ-001 through REQ-005 — improve RAG Ingestion Pipeline JSON parsing verification command documentation
- **Source issue**: issues/20260913-183047_missing_ingestion_pipeline_json_parsing_verification_command.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260913-193654_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260913-205251
- **Related target files**: docs/03_rag_02_01_ingestion_pipeline-overview.md