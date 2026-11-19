## Goal
Document the Japanese chunk path's oversized-sentence rule and the guarantee that a written chunk file always carries non-empty content. Implements `REQ-007`.

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- The oversized-sentence segmentation lives in `scripts/rag/ingestion/chunk_japanese.py` (via the shared `chunk_utils._split_overlong`), documented here as the JA-path behavior.
- No ADR decision change is required; if the emission rule changes materially during implementation, note it in the ADR-009 Implementation Notes.

## Design decisions
N/A: documentation-only change.

## Alternatives considered
N/A: documentation-only change.

## Implementation
### Target file
`docs/21_rag/rag_02_03_ingestion_pipeline-chunksplitter.md`

### Procedure
Locate the Japanese chunking section of the chunksplitter doc and add two statements.

### Method
Add, near the existing description of the Japanese sentence-merge behavior:
- The oversized-sentence rule: a Japanese sentence longer than `max_chunk` is segmented into pieces each within `max_chunk` by the shared `_split_overlong` helper; no emitted Japanese chunk exceeds `max_chunk`.
- The non-empty-content guarantee: every written chunk file carries non-empty `content`; an empty buffer never produces a chunk, so `{stem}-0000.json` (the completeness sentinel) always carries real content.

### Details
- Keep the statement at the domain level (what the path guarantees), not a line-by-line code walk.
- Cross-reference the shared helper so readers know the segmentation rule is shared with the English/heading path.

## Compatibility considerations
N/A: documentation-only change; no code or config impact.

## Security considerations
N/A.

## Rollback considerations
N/A: revert the commit.

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `docs/21_rag/rag_02_03_ingestion_pipeline-chunksplitter.md` | Doc quality | `uv run python tools/check_docs_quality.py` | No findings |

## Completion criteria
- The doc states the JA oversized-sentence segmentation rule and that a written chunk file always carries non-empty content.
- `check_docs_quality.py` reports no findings.

## Out of Scope
- Documenting the English/heading path's oversized rule beyond the shared-helper cross-reference.
- ADR changes.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Document the JA oversized-sentence rule and non-empty-content guarantee | Pending | — | — | REQ-007 |

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
- **Requirement ID**: REQ-007 (documentation of the oversized rule and non-empty content)
- **Source issue**: `issues/20261119-112013_ragcrv001_ja-empty-chunk-loop.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261119-113354_ragcrv001_ja-empty-chunk-loop.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261119-114314
- **Related target files**: `docs/21_rag/rag_02_03_ingestion_pipeline-chunksplitter.md`
