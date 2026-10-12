# Implementation Procedure: tests/rag/test_fts_japanese.py

## Goal

Add a regression test verifying that Japanese sentences with empty normalization results are kept with their original text and indexed via the COALESCE fallback.

## Scope

- `tests/rag/test_fts_japanese.py`: Add a test case for empty normalization behavior.

## Assumptions

- Punctuation-only input (e.g. "。") yields an empty normalized result from Sudachi.
- The existing `_insert_chunk` fixture accepts `normalized_content=None` and the COALESCE fallback works correctly.
- The test belongs in the existing `test_fts_japanese.py`, which already covers Japanese FTS behavior.

## Design decisions

- Add a test that feeds a Japanese sentence with empty normalization result and asserts original text is preserved and indexed.
- The test should verify both `normalized_content` is NULL (not `""`) at insert time and the FTS index contains the original text.

## Alternatives considered

1. Add the test to the existing `TestChunksAiTrigger` class — preferred because it tests the same trigger behavior.
2. Create a separate test class — rejected because the existing class already covers chunks_ai trigger behavior.

## Implementation

### Target file

`tests/rag/test_fts_japanese.py`

### Procedure

1. Add a test method to the existing `TestChunksAiTrigger` class.
2. Insert a chunk with empty-normalization content (original text present, normalized_content NULL).
3. Assert the FTS index contains the original text.
4. Assert `normalized_content` is NULL, not `""`.

### Method

Unit test — insert a chunk with empty normalized content and verify FTS indexing.

### Details

1. **Add empty normalization test (REQ-003)**:
   - Current state: `test_fts_japanese.py` exists and covers Japanese FTS behavior but does not test the empty-normalization case.
   - Add a test method (e.g., `test_empty_normalization_fallback_to_original_content`) that:
     - Inserts a chunk with `content="。"` (punctuation-only input) and `normalized_content=None`.
     - Asserts the FTS index contains the original text via COALESCE fallback.
     - Asserts `normalized_content` is NULL (not `""`) at insert time.
   - Reference: ADR-009's intent that normalization must not lose original text.
   - Evidence: `test_fts_japanese.py` exists and covers Japanese FTS behavior; punctuation-only input (e.g. `。`) yields an empty normalized result.
   - The test should also verify that the COALESCE fallback works: the FTS query should find the original text even though `normalized_content` is NULL.

## Compatibility considerations

- The test relies on the existing `_insert_chunk` fixture accepting `normalized_content=None`.
- If the schema changes (e.g., COALESCE fallback removed), the test would fail — this is expected as it validates the invariant.

## Security considerations

N/A — this is a unit test for data integrity, not a security boundary change.

## Rollback considerations

- Reverting the test removes the regression guard for empty normalization.
- No production code change — rollback is safe (just remove the test).

## Validation plan

| Target | Strategy | Tool / Command | Expected Outcome |
|--------|----------|----------------|------------------|
| test_fts_japanese.py | Unit: verify empty normalization test passes | `uv run pytest tests/rag/test_fts_japanese.py -v` | Test passes |
| test_fts_japanese.py | Lint/type: ruff, mypy | `uv run ruff check`, `uv run mypy --no-namespace-packages` | No lint/type errors |

## Completion criteria

- [ ] Test verifies empty normalization keeps original text and indexes it (REQ-003).
- [ ] Test passes when run in isolation.
- [ ] ruff and mypy pass with no errors.

## Out of scope

- Changes to the FTS schema or trigger definitions.
- Tests for other edge cases (e.g., whitespace-only input).
- Changes to non-test files.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261012-081330 | 20261012-081330 | Deviation: procedure suggested content='。' + MATCH '。', but unicode61 does not tokenize standalone punctuation (probe-verified), so that exact query would not match. Implemented splitter-level assertion (empty norm retained with NULL) + storage-level NULL-preserved-and-indexed test with indexable Japanese content instead, achieving the same RAG-002 invariant reliably. |
| 2 | Add or update tests per Validation plan | Completed | 20261012-081330 | 20261012-081330 |  |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261012-081330 | 20261012-081330 |  |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | N/A | — | — | No docs/00_index.md mapping for this file |

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
- **Requirement ID**: REQ-003
- **Source issue**: `issues/20261007-154050_regtest01_add-inv-02-regression-test-and-keep-original-japanese-text-on-empty-normalization.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261008-164920_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261011-125942
- **Related target files**: `tests/rag/test_fts_japanese.py`