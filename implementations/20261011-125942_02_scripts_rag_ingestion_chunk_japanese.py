# Implementation Procedure: scripts/rag/ingestion/chunk_japanese.py

## Goal

Fix empty normalization in `_split_into_ja_sentences()` so Japanese sentences whose normalized result is empty are kept with their original text instead of being discarded.

## Scope

- `scripts/rag/ingestion/chunk_japanese.py`: Modify `_split_into_ja_sentences()` to unconditionally append pairs and convert empty normalized results to NULL.

## Assumptions

- Empty normalization can be triggered by inputs like punctuation-only strings (e.g. "。").
- The COALESCE rule for `normalized_content` → `content` fallback already exists in the RAG schema (`schema_sql.py:65`).
- `store_impl.py:147-160` accepts `normalized: str | None = None` — NULL is valid.

## Design decisions

- Change `if normalized:` to append the pair unconditionally in `_split_into_ja_sentences()`.
- Convert an empty normalized result to NULL (not `""`) before it reaches `chunk_insert`, so the FTS trigger's `COALESCE(new.normalized_content, new.content)` falls back to the original text.

## Alternatives considered

1. Keep the `if normalized:` filter but also append the original text separately — rejected because it would require duplicating the original text in both `content` and `normalized_content`, violating the schema contract.
2. Return early from `_normalize_ja_sentence()` with NULL — rejected because the function returns `str`, not `str | None`; changing the return type would cascade through all callers.
3. Convert empty string to NULL in `_merge_ja_sentence_pairs()` — rejected because the merge step operates on already-filtered pairs; the fix must happen at the source (split step).

## Implementation

### Target file

`scripts/rag/ingestion/chunk_japanese.py`

### Procedure

1. Modify `_split_into_ja_sentences()` to unconditionally append (original, normalized) pairs.
2. In the normalization path, convert empty normalized results to NULL before they reach `chunk_insert`.

### Method

Code modification — change the conditional append logic in `_split_into_ja_sentences()`.

### Details

1. **Fix empty normalization (REQ-002)**:
   - Current code (line 54): `if normalized:` discards empty pairs (original kept, normalized dropped).
   - Fix: Remove the `if normalized:` condition and append unconditionally.
   - However, since `_normalize_ja_sentence()` returns `str` (not `str | None`), an empty normalized result is `""`, not `None`.
   - The FTS trigger uses `COALESCE(new.normalized_content, new.content)` — only NULL falls back to original `content`, while `""` indexes empty.
   - Therefore, after appending unconditionally, we must ensure the normalized value passed to `chunk_insert` is NULL (not `""`) when normalization yields empty.
   - Two approaches:
     a. Change `_normalize_ja_sentence()` to return `str | None` and return `None` for empty results — cascading change.
     b. Handle the conversion in `_split_into_ja_sentences()` after calling `_normalize_ja_sentence()`: if the result is empty string, treat it as NULL.
   - Approach (b) is preferred to minimize cascading changes.
   - Implementation:
     ```python
     # Before (line 54):
     if normalized:
         pairs.append((original, normalized))
     
     # After:
     normalized_value = normalized if normalized else None  # Convert "" to None
     pairs.append((original, normalized_value))
     ```
   - Evidence: `chunk_japanese.py:54` `if normalized:` discards empty pairs; `schema_sql.py:65` COALESCE requires NULL; `store_impl.py:154` accepts NULL.

## Compatibility considerations

- Changing `_split_into_ja_sentences()` behavior affects downstream consumers that rely on the current filtering behavior.
- The `normalized_content` column will now receive NULL instead of `""` for empty-normalization cases, which is consistent with the COALESCE fallback semantics.
- Existing tests in `test_fts_japanese.py` cover the COALESCE behavior but do not test the empty-normalization case (REQ-003).

## Security considerations

N/A — this is a data integrity fix, not a security boundary change.

## Rollback considerations

- Reverting the change restores the original behavior where empty-normalization sentences are silently dropped.
- This contradicts ADR-009's intent that normalization must not lose original text.
- Rollback is safe (revert the two-line change in `_split_into_ja_sentences()`).

## Validation plan

| Target | Strategy | Tool / Command | Expected Outcome |
|--------|----------|----------------|------------------|
| chunk_japanese.py | Unit: verify empty normalization keeps original text | `uv run pytest tests/rag/test_fts_japanese.py -v` | Empty norm test passes |
| chunk_japanese.py | Lint/type: ruff, mypy | `uv run ruff check`, `uv run mypy --no-namespace-packages` | No lint/type errors |

## Completion criteria

- [ ] Japanese sentence with empty normalization is stored with original text in `content` and NULL in `normalized_content` (REQ-002).
- [ ] FTS indexes the original text via COALESCE fallback.
- [ ] ruff and mypy pass with no errors.

## Out of scope

- Changes to non-empty normalization results.
- Other chunking behavior changes.
- Changes to `_normalize_ja_sentence()` return type (kept as `str`).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
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
- **Requirement ID**: REQ-002
- **Source issue**: `issues/20261007-154050_regtest01_add-inv-02-regression-test-and-keep-original-japanese-text-on-empty-normalization.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261008-164920_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261011-125942
- **Related target files**: `scripts/rag/ingestion/chunk_japanese.py`
