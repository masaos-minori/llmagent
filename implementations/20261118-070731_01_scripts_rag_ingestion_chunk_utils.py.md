## Goal

Add a fail-fast guard to `_split_overlong` in `chunk_utils.py` so a non-positive `max_chunk` raises instead of entering an infinite loop, converting a misconfigured `chunk_splitter.toml` into a clear error (REQ-001).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- `_split_overlong(item, sep, max_chunk)` is a module-level pure function (line 20); `max_chunk` has the right type (`int`) but may be an inappropriate value (`<= 0`).
- The guard fires only for `max_chunk <= 0`; all positive-`max_chunk` paths are untouched, so the exact-reproduction invariant holds.

## Design decisions
- Raise `ValueError` at the top of `_split_overlong`, before the `while start < end` loop (line 30). `ValueError` is idiomatic for a right-type/wrong-value argument to a pure utility and avoids coupling `chunk_utils.py` to the rag-layer exception hierarchy.

## Alternatives considered
- Raising `PipelineValidationError` (the configured config-error type) in the util: rejected as over-coupling the language-independent util to the rag exception layer; reserve `PipelineValidationError` for the load site (`ChunkSplitter.__init__`, REQ-002).

## Implementation
### Target file
`scripts/rag/ingestion/chunk_utils.py`

### Procedure
1. Add `if max_chunk <= 0: raise ValueError(f"max_chunk must be positive, got {max_chunk}")` at the top of `_split_overlong`, before the `while` loop (before line 30); leave the algorithm, `merge_text_items`, and `start_next_buf` untouched (REQ-001).

### Method
- Insert the guard immediately after the docstring and the `chunks: list[str] = []` / `start = 0` / `end = len(item)` setup, before `while start < end:`. Do not alter the splitting logic for positive `max_chunk`.

### Details
- The current loop (lines 30-39): when `max_chunk <= 0`, `window_end = min(start + max_chunk, end)` evaluates to `start`, the `window_end == end` early-break never fires, and `start = cut` leaves `start` unchanged, so `while start < end` loops forever. The guard prevents this.

## Compatibility considerations
- Positive-`max_chunk` behavior and the concatenation-invariant are byte-for-byte unchanged. Production always supplies a positive `max_chunk` from config; a non-positive config now errors instead of hanging.

## Security considerations
- Converts an indefinite ingestion hang (denial-of-service via misconfiguration) into a bounded, clear error. Do not weaken the guard.

## Rollback considerations
- Revert the commit; the guard is a single added line outside the splitting loop.

## Validation plan
| Target File/Module | Testing Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| `scripts/rag/ingestion/chunk_utils.py` + `tests/rag/ingestion/test_chunk_utils.py` | Unit | `uv run pytest tests/rag/ingestion` | green; `_split_overlong` raises on `max_chunk <= 0`; positive-`max_chunk` correctness + invariant preserved; existing tests pass unmodified |
| Full suite | Integration | `uv run pytest` | no regression anywhere |
| Changed files | Lint / type | `uv run ruff check` + `uv run mypy` on `chunk_utils.py` | clean |

## Completion criteria
- `_split_overlong` raises on `max_chunk = 0` and `max_chunk = -1`; for `max_chunk >= 1` output is byte-identical to the pre-change algorithm (concatenation reproduces the input) (AC-001).

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
- **Requirement ID**: `REQ-001` (fail-fast guard in `_split_overlong` on non-positive `max_chunk`)
- **Source issue**: issues/20261118-025816_chunkov001_split-overlong-nonpositive-maxchunk.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261118-043200_chunkov001_split-overlong-nonpositive-maxchunk.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261118-070731
- **Related target files**: `scripts/rag/ingestion/chunk_utils.py`
