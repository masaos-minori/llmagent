## Goal
Update the AugmentStage section of the RAG augment-stages document so it states the sanitizer's guarantee boundary: the context block's markers are neutralized in every untrusted field, title and url are single-line sanitized, the phrase blocklist is best-effort, and the structural boundary is the control (`REQ-006`).

## Scope
**Release unit**: N/A: not part of a release unit

- In scope: the AugmentStage bullets, the `sanitize_document()` Contract paragraph, and the Limitations paragraph in `docs/21_rag/rag_03_05_query_pipeline-augment-stages.md`.
- Runs after the code procedures of this Plan so the described behavior exists.

## Assumptions
- Overlap judgments (`tools/check_plan_target_overlaps.py`, Step 2): `plans/20261108-165604_ragrev009_dead-pipeline-stage-runner.md` also edits this file, only the "Exception Catching Location" paragraph in the section before AugmentStage; this procedure edits other paragraphs: compatible, any order.
- Documentation states intent and boundary only, in English, without signatures or file-location mappings beyond what the section already has, and without new counts or concrete values (`skills/DESIGN.md` Docs content policy, No implementation counts).
- The existing statement that every query-time path sanitizes chunk content with `sanitize_document` stays accurate and is not rewritten; `docs/21_rag/rag_03_06_query_pipeline-helpers-and-cache.md` repeats it and needs no edit (checked in Step 3a).

## Design decisions
- Describe the guarantee, then the limit: markers and header fields are handled structurally; the blocklist is best-effort and not semantic.
- Replace the sentence that lists five pattern categories with a description that does not state a count, because the contract now also covers marker neutralization.

## Alternatives considered
N/A: docs-only row.

## Implementation
### Target file
`docs/21_rag/rag_03_05_query_pipeline-augment-stages.md`

### Procedure
1. AugmentStage bullets: change the per-chunk format bullet to say that title and url pass through a single-line field sanitizer (markers neutralized, injection phrases replaced, line breaks and control characters collapsed to spaces) and that the url stands in when the sanitized title is empty.
2. `sanitize_document()` Contract paragraph: state that, besides the injection phrase categories (named, not counted), the function replaces the boundary marker strings (case-insensitive, optional whitespace inside the brackets) with the same `[REMOVED]` placeholder, so retrieved text cannot close or reopen the context block.
3. Limitations paragraph: state that phrase matching is best-effort and not semantic, that the structural boundary (neutralized markers and single-line header fields) is the control, and that look-alike or zero-width characters are not normalized.

### Method
- Edit the existing sentences in place; keep the surrounding structure, headings, and the Content-only Invariance Rule untouched.

### Details
- Keep the marker strings and `[REMOVED]` as literals where the doc already uses them; do not add a signature table or a file-by-file call-site list.
- The helper's name may be written once as `sanitize_field()`; `tools/check_docs_consistency.py --domain rag` verifies that a backticked function reference exists, which holds once the `scripts/rag/utils.py` change has landed.

## Compatibility considerations
N/A: documentation only; no document is renamed or moved, so no link or `related:` entry changes.

## Security considerations
The text states a guarantee boundary. It must not overstate: the blocklist is best-effort and look-alike characters are not normalized. No secret or concrete configuration value is added.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run python tools/check_docs_quality.py`, `uv run python tools/check_docs_structure.py docs/21_rag/rag_03_05_query_pipeline-augment-stages.md`, `uv run python tools/check_docs_content_policy.py`, `uv run python tools/check_docs_consistency.py --domain rag`, `uv run python tools/check_docs_japanese.py`

## Completion criteria
- The section names the best-effort blocklist versus the structural boundary, the header-field handling, and the marker neutralization, without new counts or code detail.
- All five documentation checkers report no findings.

## Out of Scope
- Other paragraphs of this file (including the ragrev009 catch-location sentence); `docs/21_rag/rag_03_06_query_pipeline-helpers-and-cache.md`; code and tests.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Update the AugmentStage bullets, the `sanitize_document()` Contract paragraph, and the Limitations paragraph | Pending | — | — | |
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
- **Related target files**: `docs/21_rag/rag_03_05_query_pipeline-augment-stages.md`
