## Goal

Remove duplicate section headers and redundant content from `docs/03_rag_03_02_query_pipeline-rag-pipeline-class.md` while preserving all unique information across the three overlapping sections, per REQ-001 through REQ-005.

## Scope

- In-Scope: Removing duplicate content from `docs/03_rag_03_02_query_pipeline-rag-pipeline-class.md`; consolidating the three "RagPipeline Class" sections into a single coherent section
- Out-of-Scope: Modifying any source code files; modifying other documentation files; changing the actual RagPipeline implementation

## Assumptions

- The "## 2." numbering convention should be preserved for consistency with related documents
- The HTTP mode subsections under "## 2b." are intended to be part of the RagPipeline Class documentation and should be retained
- The "Documentation vs. Implementation Mismatch" notes across the three sections convey the same factual claim and can be consolidated into a single note

## Design decisions

1. Consolidate the three overlapping sections into one coherent section rather than deleting content outright.
2. Preserve the "## 2." numbering convention for consistency with related documents.
3. Keep the "Documentation vs. Implementation Mismatch" note as a single authoritative statement.
4. Maintain the logical flow: basic class info → HTTP mode → diagnostics.

Evidence grounding:
- `pipeline.py:34`: Actual import statement confirms `from rag.pipeline import RagPipeline, RagPipelineError`
- `repository.py`: Contains `fetch_full_document` function — supports the mismatch note
- `utils.py`: Contains `sanitize_document` function — supports the mismatch note
- `pipeline_service.py:136-146`: `call_rag_service()` function signature matches section 2b documentation
- `shared/types.py`: Contains `RagConfig` Protocol with `rag_service_url` and `rag_auth_token` fields

## Alternatives considered

- **Delete section 2a entirely without integration**: Rejected because the Plan's intent is to consolidate into a single coherent section, not just delete duplicates.
- **Keep all three sections but add cross-references**: Rejected because it would maintain the duplication and confusion the Issue describes.
- **Merge sections 2a and 2b into section 2 only**: Rejected because section 2b contains unique HTTP mode documentation that should be retained.

## Implementation
### Target file
`docs/03_rag_03_02_query_pipeline-rag-pipeline-class.md`

### Procedure
1. Verify current state of overlapping sections
2. Remove the duplicate "## 2a. RagPipeline Class" section
3. Rename "## 2b. RagPipeline Class" to "## 2. RagPipeline Class" and integrate its content
4. Consolidate the "Documentation vs. Implementation Mismatch" note
5. Consolidate the "Related Documents" list
6. Consolidate the "Keywords" list
7. Run validation sequence

### Method
Inline text consolidation within the existing documentation file.

### Details
1. **Phase 1: Preparation — Confirm current state**
   a. Locate the three overlapping sections in `docs/03_rag_03_02_query_pipeline-rag-pipeline-class.md` (lines 23-196 contain three overlapping "RagPipeline Class" sections; lines 31-65 and 67-104 are near-duplicates)
   b. Read `scripts/rag/pipeline.py` to confirm the actual RagPipeline class definition and public API
   c. Read `scripts/rag/pipeline_service.py` to verify `call_rag_service()` function signature and behavior
   d. Read `shared/types.py` to verify `RagConfig` Protocol fields
   e. Read `scripts/rag/repository.py` to verify `fetch_full_document` location
   f. Read `scripts/rag/utils.py` to verify `sanitize_document` location
   g. Read `docs/03_rag_03_03_query_pipeline-context-and-diagnostics.md` to verify cross-references to `http_result_kind` diagnostics
   
2. **Phase 2: Core Implementation**
   a. Remove the duplicate "## 2a. RagPipeline Class" section (lines 67-104):
      - Delete the entire section including header, body, and any trailing blank lines
      - Ensure the remaining content flows naturally from section 2 to section 2b
   
   b. Rename "## 2b. RagPipeline Class" to "## 2. RagPipeline Class" and integrate its content:
      ```markdown
      <!-- Before: -->
      ## 2b. RagPipeline Class
      
      <!-- After: -->
      ## 2. RagPipeline Class
      ```
   
   c. Consolidate the "Documentation vs. Implementation Mismatch" note into a single authoritative statement:
      - Compare the two instances carefully before merging (see Risks)
      - If they convey the same factual claim, keep one instance
      - If they have slightly different claims, merge them into a single comprehensive note
   
   d. Consolidate the "Related Documents" list into a single list:
      - Merge the lists from sections 2 and 2b
      - Deduplicate entries
      - Place the consolidated list at the end of the unified section
   
   e. Consolidate the "Keywords" list into a single list:
      - Merge the keyword lists from sections 2 and 2b
      - Deduplicate entries
      - Place the consolidated list at the end of the unified section

3. **Phase 3: Verification**
   a. Confirm the consolidated documentation accurately reflects the source code evidence
   b. Confirm no unintended modifications were made to other files

## Compatibility considerations

- Removing section 2a may break existing cross-references if other documents link to specific section anchors — mitigated by checking for external references before removing; updating any found
- Consolidating the mismatch note may lose nuance if the two instances had slightly different claims — mitigated by comparing the two notes carefully before merging
- Renumbering sections may affect navigation within the document — mitigated by ensuring internal links use relative references where possible

## Security considerations

N/A: Documentation update only, no security impact.

## Rollback considerations

Simple revert of the text consolidation changes — no data migration or state rollback needed.

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| docs/03_rag_03_02_query_pipeline-rag-pipeline-class.md | Manual review against source code evidence | Read target files + compare | Consolidated documentation matches actual behavior |

## Completion criteria

- [ ] Duplicate "## 2a. RagPipeline Class" section removed
- [ ] HTTP mode documentation integrated into the main section
- [ ] "Documentation vs. Implementation Mismatch" note preserved with updated cross-reference
- [ ] All cross-references and related-document links remain valid after consolidation
- [ ] Consolidated section maintains logical flow from basic class → HTTP mode → diagnostics
- [ ] No source code files are modified
- [ ] No other documentation files are modified except docs/03_rag_03_02_query_pipeline-rag-pipeline-class.md

## Out of scope

- Modifying `scripts/rag/pipeline.py` (reference file only)
- Modifying `scripts/rag/pipeline_service.py` (reference file only)
- Modifying `shared/types.py` (reference file only)
- Modifying `scripts/rag/repository.py` (reference file only)
- Modifying `scripts/rag/utils.py` (reference file only)
- Modifying `docs/03_rag_03_03_query_pipeline-context-and-diagnostics.md` (reference file only)
- Modifying other documentation files
- Changing the actual RagPipeline implementation

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Verify existing overlapping sections at lines 23-196 | Completed | — | — | Record exact wording |
| 2 | Remove duplicate ## 2a. RagPipeline Class section | Completed | — | — | Lines 67-104 |
| 3 | Rename ## 2b. RagPipeline Class to ## 2. RagPipeline Class | Completed | — | — | Integrate content |
| 4 | Consolidate Documentation vs. Implementation Mismatch note | Completed | — | — | Single authoritative statement |
| 5 | Consolidate Related Documents list | Completed | — | — | Merge and deduplicate |
| 6 | Consolidate Keywords list | Completed | — | — | Merge and deduplicate |
| 7 | Manual review of accuracy against source code | Completed | — | — | Verify all claims |

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
- **Requirement ID**: REQ-001 through REQ-005 — remove duplicate RagPipeline Class documentation sections
- **Source issue**: issues/20260913-183001_duplicate_section_headers_rag_pipeline_class.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260913-202039_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260913-220756
- **Related target files**: docs/03_rag_03_02_query_pipeline-rag-pipeline-class.md
