## Goal
Update the "Prompt injection sanitization" bullets of the shared-utilities document so they describe the changed contract: `sanitize_document()` and `sanitize_document_full()` also neutralize the context-block boundary markers, and a single-line field sanitizer exists for untrusted header fields (`REQ-006`).

## Scope
**Release unit**: N/A: not part of a release unit

- In scope: the sanitization bullets in `docs/21_rag/rag_02_09_ingestion_pipeline-shared-utilities.md`.
- Runs after the code procedures of this Plan so the described behavior exists.

## Assumptions
- Overlap judgments (`tools/check_plan_target_overlaps.py`, Step 2): this file is not shared with another Frozen Plan.
- Documentation states intent and boundary only, in English, without signatures, counts, or concrete values (`skills/DESIGN.md` Docs content policy).
- The marker neutralization uses the same `[REMOVED]` placeholder as the injection phrases (the resolution of Plan UNK-02, recorded in the `scripts/rag/utils.py` procedure).

## Design decisions
- Keep the two existing bullets and extend their wording; add one bullet for the field sanitizer, so the section keeps its shape.

## Alternatives considered
N/A: docs-only row.

## Implementation
### Target file
`docs/21_rag/rag_02_09_ingestion_pipeline-shared-utilities.md`

### Procedure
1. `sanitize_document()` bullet: add that it also replaces the boundary marker strings of the RAG context block (case-insensitive, optional whitespace inside the brackets) with the `[REMOVED]` placeholder, so retrieved text cannot close or reopen the block.
2. `sanitize_document_full()` bullet: keep "does the same", and state that a marker match counts as sanitization in its audit trail.
3. Add one bullet for `sanitize_field()`: the variant for single-line fields such as a chunk title or url, which collapses line breaks and control characters before applying the same sanitization.

### Method
- Edit within the "Prompt injection sanitization" list only.

### Details
- State that the phrase blocklist is best-effort and the marker handling is the structural control, in one clause, consistent with the AugmentStage document; no code detail.
- The backticked `sanitize_field()` must exist when the docs checkers run, which holds once the `scripts/rag/utils.py` change has landed.

## Compatibility considerations
N/A: documentation only; no rename or move, so no link or `related:` entry changes.

## Security considerations
The text must not overstate the guarantee: the blocklist is best-effort. No secret or concrete configuration value is added.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run python tools/check_docs_quality.py`, `uv run python tools/check_docs_structure.py docs/21_rag/rag_02_09_ingestion_pipeline-shared-utilities.md`, `uv run python tools/check_docs_content_policy.py`, `uv run python tools/check_docs_consistency.py --domain rag`, `uv run python tools/check_docs_japanese.py`

## Completion criteria
- The section describes marker neutralization in both content sanitizers and the field sanitizer, without counts or code detail.
- All five documentation checkers report no findings.

## Out of Scope
- Other sections of this file; the AugmentStage document (separate procedure); code and tests.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Update the sanitization bullets and add the field sanitizer bullet | Pending | — | — | |
| 2 | Run the documentation checkers named in `routing.md` Tools "When to run which tool" | Pending | — | — | |

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
- **Requirement ID**: `REQ-006` (docs state best-effort blocklist versus structural boundary)
- **Source issue**: issues/20261108-131004_ragrev002_rag-context-boundary-injection.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261108-164455_ragrev002_rag-context-boundary-injection.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261109-104558
- **Related target files**: `docs/21_rag/rag_02_09_ingestion_pipeline-shared-utilities.md`
