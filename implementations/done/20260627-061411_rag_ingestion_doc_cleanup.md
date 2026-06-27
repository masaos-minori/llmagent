## Goal

Clean up duplicated and stale sections in `03_rag_02_ingestion_pipeline.md` by removing duplicate ChunkSplitter class overview, fixing broken output format headings, replacing stale `.txt` sentinel references with `.json`, updating `source_file` examples to `.json`, and aligning section numbering.

## Scope

**In-Scope**:
- Merge duplicated ChunkSplitter class overview sections (lines 252-264 and 273-285)
- Fix broken output format headings
- Replace `{stem}-0000.txt` with `{stem}-0000.json` (line 337)
- Update `source_file` examples from `.txt` to `.json` (lines 318, 329)
- Align section numbering (section 5 appears twice — Chunk English Mixin and Chunk Utils)

**Out-of-Scope**:
- Runtime behavior changes unless needed to align with documented `.json` behavior
- Changes to other RAG documentation files

## Assumptions

1. The first ChunkSplitter class overview (lines 252-264) is the correct one; the duplicate (lines 273-285) should be removed
2. Section numbering should be sequential — section 5 should be split into 5 and 6, with existing sections 6+ shifted accordingly

## Implementation

### Target file: docs/03_rag_02_ingestion_pipeline.md

**Procedure**: Remove duplicate ChunkSplitter class overview, replace stale `.txt` references, fix section numbering.

**Method**: Modify the ingestion pipeline documentation.

**Details**:
1. Remove duplicate ChunkSplitter class overview (lines 273-285)
   - Keep lines 252-264 (first ChunkSplitter class overview)
   - Delete lines 273-285 (second ChunkSplitter class overview)
2. Replace stale `.txt` references with `.json`:
   - Line 318: Change `source_file` example from `.txt` to `.json`
   - Line 329: Update descriptive text from "original `.txt` extension" to "original `.json` filename"
   - Line 337: Change `{stem}-0000.txt` to `{stem}-0000.json`
3. Fix section numbering:
   - Renumber sections sequentially (Chunk English Mixin = 5, Chunk Utils = 6, Chunk Japanese Mixin = 7, Pipeline Utils = 8, Shared Utilities = 9, FTS5 Implementation Notes = 10)

## Validation plan

| Target File/Module | Testing Strategy | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| 03_rag_02_ingestion_pipeline.md | Verify no duplicate ChunkSplitter overview remains | Check section 3 | Single ChunkSplitter class overview present |
| 03_rag_02_ingestion_pipeline.md | Verify all `.txt` references replaced with `.json` | Search for `.txt` in document | Zero `.txt` references (except in historical context) |
| 03_rag_02_ingestion_pipeline.md | Verify section numbering is sequential | Check all ## headings | No duplicate section numbers |

## Risks

- **Risk**: Removing duplicate section may inadvertently remove important content if sections differ | **Likelihood**: Low | **Mitigation**: Compare both sections before removing; if they differ, merge rather than delete | False
