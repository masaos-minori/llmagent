## Goal

Add unit tests asserting `_split_overlong` raises on `max_chunk = 0` and `max_chunk = -1`, and still splits correctly for `max_chunk >= 1` (REQ-003); include the optional `ChunkSplitter` load-time assertion if Phase 2 lands (REQ-002).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- `_split_overlong` is a module-level function in `chunk_utils.py` and can be imported alongside `merge_text_items` / `start_next_buf` (current imports, line 9).
- The optional `ChunkSplitter` load-time validation (REQ-002) is gated on an author decision; add its assertion only if that phase lands.

## Design decisions
- Import `_split_overlong` and add a parametrized test for the failure case plus a positive-`max_chunk` correctness + concatenation-invariant assertion.

## Alternatives considered
- Testing via `ChunkSplitter`/`merge_text_items` only: insufficient — the guard is at `_split_overlong`, so it is exercised directly for a precise, fast assertion.

## Implementation
### Target file
`tests/rag/ingestion/test_chunk_utils.py`

### Procedure
1. Add `_split_overlong` to the import from `rag.ingestion.chunk_utils` (line 9) (REQ-003).
2. Add a parametrized test asserting `_split_overlong` raises on `max_chunk = 0` and `max_chunk = -1` (REQ-001/REQ-003).
3. Add a test asserting a small positive `max_chunk` still splits and concatenates back to the input (REQ-003).
4. If Phase 2 (REQ-002) lands, construct `ChunkSplitter` with a non-positive `max_chunk` config and assert the configured config-error type is raised (REQ-002).

### Method
- Use `pytest.raises(ValueError)` for the `_split_overlong` failure cases. For the invariant, split a long item with `max_chunk >= 1` and assert `"".join(chunks) == item`.

### Details
- Assert on `ValueError` for the util guard (do not assert a rag-layer type here — that belongs to the `ChunkSplitter` load site). Keep existing `TestStartNextBuf` tests unmodified.

## Compatibility considerations
- New assertions; existing `test_chunk_utils.py` tests pass unmodified. No existing test exercises `max_chunk <= 0`.

## Security considerations
- Verifies the misconfiguration-hang is converted to a bounded error. Do not relax these assertions.

## Rollback considerations
- Delete the added tests; self-contained.

## Validation plan
| Target File/Module | Testing Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| `tests/rag/ingestion/test_chunk_utils.py` | Unit | `uv run pytest tests/rag/ingestion` | green; `_split_overlong` raises on `max_chunk <= 0`; positive-`max_chunk` correctness + invariant preserved; existing tests pass unmodified |

## Completion criteria
- The new failure case is covered by a green test; existing `test_chunk_utils.py` tests pass unmodified (AC-003).

## Out of Scope

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | |

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
- **Requirement ID**: `REQ-003` (unit test for `_split_overlong` non-positive raise + positive correctness)
- **Source issue**: issues/20261118-025816_chunkov001_split-overlong-nonpositive-maxchunk.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261118-043200_chunkov001_split-overlong-nonpositive-maxchunk.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261118-070731
- **Related target files**: `tests/rag/ingestion/test_chunk_utils.py`
