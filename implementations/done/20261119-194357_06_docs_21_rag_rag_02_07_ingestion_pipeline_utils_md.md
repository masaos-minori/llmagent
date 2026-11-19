## Goal

Document the collaborator's ownership of the accumulation loop and the strategy inputs each path supplies in `docs/21_rag/rag_02_07_ingestion_pipeline-utils.md` (`REQ-007`). Coordinate with `ragcrv010` so both doc updates describe one design, not two.

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- This is a documentation-only row; the change is confined to one doc file with no code, persistence, or security impact, so the lightweight fill applies.
- The collaborator's shape is defined by the `chunk_utils.py` row; this doc describes that shape once implemented.
- The two rag-doc updates (`rag_02_07` here and `ragcrv010`) must describe one unified design; coordinate before finalizing wording.

## Design decisions
N/A: documentation wording only.

## Alternatives considered
N/A: documentation-only row.

## Implementation
### Target file
`docs/21_rag/rag_02_07_ingestion_pipeline-utils.md`

### Procedure
1. Describe the single accumulation collaborator's ownership of the min/max/overlap loop and the strategy inputs each path supplies (oversized-item, short-tail, separator, optional paired-companion).
2. Note that `merge_text_items`, `_merge_paragraphs_en`, and `_merge_ja_sentence_pairs` route through it while keeping their language-specific splitting.

### Method
- Update the "Utility functions" index task section to replace the "three divergent loops" description with the single-collaborator ownership and the strategy-input contract. Keep the doc's existing front matter and related-doc headings intact (run the docs checkers in `rules/toolchain.md` after editing).

### Details
- Do not reword or contradict the `ragcrv010` doc; align terminology. This procedure does not edit source or other docs.

## Compatibility considerations
- Documentation-only; no API or behavior change.

## Security considerations
N/A: documentation-only.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- Docs checkers in `rules/toolchain.md` pass for `rag_02_07_ingestion_pipeline-utils.md`.

## Completion criteria
- The doc describes the collaborator's ownership and strategy inputs; the docs checkers pass; wording is consistent with `ragcrv010`.

## Out of Scope
- Any code change to the collaborator — covered by the `chunk_utils.py` row.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Run the validation sequence (`rules/toolchain.md`) | Completed | — | 20261119-215140 | All rag docs checkers pass (quality/structure/content-policy --strict/consistency); wording aligned with ragcrv010. |
| 2 | Update documentation, if in scope per Compatibility/Out of scope | Completed | — | 20261119-215145 | Section 7.1 rewritten: single-collaborator ownership of accumulate_items loop + strategy-input contract; three routing functions documented; stale 'Japanese does not use it' claim corrected. |

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
- **Requirement ID**: `REQ-007` (document the collaborator's ownership and strategy inputs)
- **Source issue**: `issues/20261119-112017_ragcrv005_unify-chunk-merge-strategies.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261119-185003_ragcrv005_unify-chunk-merge-strategies.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261119-194357
- **Related target files**: `docs/21_rag/rag_02_07_ingestion_pipeline-utils.md`