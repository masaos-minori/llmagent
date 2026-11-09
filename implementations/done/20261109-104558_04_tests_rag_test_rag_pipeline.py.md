## Goal
Add regression tests proving that forged boundary markers cannot close or reopen the RAG context block and that title and url cannot break the `[Source: ...]` header: forged markers in content, title, and url for `_format_chunks` (`REQ-001`, `REQ-002`), marker neutralization in the rerank preview (`REQ-004`), the audit trail of `sanitize_document_full` (`REQ-001`), and the unchanged marker names (`REQ-005`).

## Scope
**Release unit**: ragrev002-core

- In scope: new tests in `tests/rag/test_rag_pipeline.py`, added to the existing classes (`TestSanitizeDocument`, `TestFormatChunks`, `TestBuildRerankPromptSanitization`).
- Depends on the production procedures of this Plan (`scripts/rag/utils.py` `seq` 01, `scripts/rag/stages/augment.py` `seq` 02): these tests fail until they land.

## Assumptions
- Overlap judgments (`tools/check_plan_target_overlaps.py`, Step 2): this file is not shared with another Frozen Plan.
- `sanitize_field`, `RAG_BLOCK_START`, `RAG_BLOCK_END`, and `sanitize_document_full` behavior come from the `seq` 01 sibling; `sanitize_field` and the two constants are resolved from it.
- The file already imports `_RAG_BLOCK_START`, `_RAG_BLOCK_END`, `_format_chunks` (as `_augment_format_chunks`), `_build_rerank_prompt`, `sanitize_document`, and `RawHit`; the existing helpers `TestFormatChunks._hit` and `TestBuildRerankPromptSanitization._make_cfg` / `_hit` are reused.
- Existing marker assertions in this file and in `tests/rag/test_rag_stages.py` must pass unmodified (`REQ-005`).

## Design decisions
- Parametrize marker variants (exact, lower case, inner whitespace, both markers, repeated) instead of one test per spelling, and assert on counts of the raw constants, not on the replacement text.
- Include a spliced-fragment case (an injection phrase placed inside a marker) to pin that phrase substitution cannot assemble a marker.

## Alternatives considered
N/A: test-only row; levels are fixed by the Plan.

## Implementation
### Target file
`tests/rag/test_rag_pipeline.py`

### Procedure
1. `TestSanitizeDocument`: parametrized test that each marker variant is absent from the sanitized text; the spliced-fragment case; idempotence (sanitizing twice equals sanitizing once); a `sanitize_document_full` test that a marker-only text reports `was_sanitized` and a non-empty `patterns_detected`, and that clean text reports neither.
2. `TestFormatChunks`: content carrying `[RAG_CONTEXT_END]` (also lower case and with inner whitespace) yields exactly one start and one end marker in the output; a title and a url carrying markers, a line break followed by a fake `[Source: ...]` header, or `ignore previous instructions` yield one header line per chunk with no raw marker; an empty and a whitespace-only title fall back to the url; the marker names imported from `rag.stages.augment` equal the constants in `rag.utils`.
3. `TestBuildRerankPromptSanitization`: a candidate whose content carries markers yields a prompt with no raw marker, and the 300-character budget per item line still holds.

### Method
- Build hits with the existing helpers; count occurrences with `str.count` on the raw constants; check header lines by splitting the output on line breaks and counting lines that start with `[Source:`.
- Do not assert the exact replacement text beyond containing `[REMOVED]`.

### Details
- Do not modify existing tests. A suppression comment, if one is needed for a stub, follows the repository justification rule (`rules/coding.md` Suppression governance).
- Comments in English; test names describe the behavior.

## Compatibility considerations
N/A: tests only.

## Security considerations
N/A: tests only; the forged strings are inert literals and no network or database is used.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run pytest tests/rag/test_rag_pipeline.py tests/rag/test_rag_stages.py -q` (new tests fail before the production changes and pass after; existing tests unmodified)
- `uv run ruff format tests/rag/test_rag_pipeline.py`, `uv run ruff check tests/rag/test_rag_pipeline.py`
- `uv run python tools/check_suppression_justification.py`

## Completion criteria
- Forged markers in content, title, and url leave exactly one start and one end marker and single-line headers.
- The rerank preview and `sanitize_document_full` cases pass; the marker-name import check passes.
- Existing tests pass unmodified; ruff is clean.

## Out of Scope
- Production code and docs; refiner prompt tests (in the `tests/rag/test_augment_refiner.py` companion of the `scripts/rag/llm_client.py` procedure).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add the sanitizer, `sanitize_document_full`, `_format_chunks`, rerank preview, and marker-name tests | Completed | 20261109-143405 | 20261109-150615 | Fails until the `seq` 01 and 02 procedures land Tests added; 12018 passed full suite, diff-cover 100% |
| 2 | Run the validation sequence (`rules/toolchain.md`) and the targeted test modules | Completed | 20261109-143405 | 20261109-150615 | Tests added; 12018 passed full suite, diff-cover 100% |

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
- **Requirement ID**: `REQ-001` (markers cannot close or reopen the block), `REQ-002` (single-line title and url), `REQ-004` (rerank previews neutralize markers), `REQ-005` (marker names unchanged)
- **Source issue**: issues/20261108-131004_ragrev002_rag-context-boundary-injection.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261108-164455_ragrev002_rag-context-boundary-injection.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261109-104558
- **Related target files**: `tests/rag/test_rag_pipeline.py`