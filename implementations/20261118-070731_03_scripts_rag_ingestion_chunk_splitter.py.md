## Goal

Optionally validate `max_chunk > 0` at load time in `ChunkSplitter.__init__` so a non-positive `max_chunk` raises the configured config-error type at startup instead of hanging on the first overlong item (REQ-002, OPTIONAL).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- **This is an OPTIONAL change** (plan Out-of-Scope / flagged). Implement it only if the author wants startup-surfaced validation; otherwise skip and rely on the required `_split_overlong` guard (doc 01).
- `ChunkSplitter.__init__` already raises on missing keys via `cfg[...]`, so a non-positive value is the only new case to catch (line 76: `self._max_chunk: int = int(cfg["max_chunk"])`).
- Error type: `PipelineValidationError` (the configured config-error type in `scripts/rag/exceptions.py`) is the layer-appropriate choice here, distinct from the `ValueError` used in the util (doc 01). If both layers raise, they may use different types; unify only if the author prefers.
- Whether nc034 (unvalidated chunk-size bounds) resolves to a specific config-error type should be coordinated; otherwise proceed with this choice.

## Design decisions
- After `self._max_chunk = int(cfg["max_chunk"])`, add `if self._max_chunk <= 0: raise PipelineValidationError(f"max_chunk must be positive, got {self._max_chunk}")`.

## Alternatives considered
- Raising `ValueError` here: acceptable but less layer-appropriate than `PipelineValidationError`; reserve the latter for the loader since it is the rag-layer config boundary.

## Implementation
### Target file
`scripts/rag/ingestion/chunk_splitter.py`

### Procedure
1. After `self._max_chunk: int = int(cfg["max_chunk"])` (line 76), add a `if self._max_chunk <= 0: raise <config-error-type>(...)` guard (REQ-002).
2. Import the configured config-error type (`PipelineValidationError` from `scripts/rag/exceptions.py`) if not already imported.

### Method
- Insert the guard immediately after line 76. Do not change the splitting algorithm or `merge_text_items`.

### Details
- Optional: skip entirely if the author prefers guard-only (the required `_split_overlong` guard already converts the hang to an error at chunk time). If both layers raise, using `PipelineValidationError` here and `ValueError` in the util is acceptable.

## Compatibility considerations
- Only adds a startup validation for an already-invalid (non-positive) config; no valid config is affected. Verify no config/test sets `max_chunk <= 0`.

## Security considerations
- Surfaces a misconfiguration at startup (fail-fast) rather than hanging mid-ingestion. Do not weaken.

## Rollback considerations
- Revert the commit; single added check.

## Validation plan
| Target File/Module | Testing Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| `scripts/rag/ingestion/chunk_splitter.py` | Unit | `uv run pytest tests/rag/ingestion` | green; non-positive `max_chunk` raises the configured config-error type at construction |

## Completion criteria
- `ChunkSplitter` raises the configured config-error type on a non-positive `max_chunk` at construction (AC-002, OPTIONAL).

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
- **Requirement ID**: `REQ-002` (OPTIONAL) — load-time `max_chunk > 0` validation in `ChunkSplitter.__init__`
- **Source issue**: issues/20261118-025816_chunkov001_split-overlong-nonpositive-maxchunk.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261118-043200_chunkov001_split-overlong-nonpositive-maxchunk.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261118-070731
- **Related target files**: `scripts/rag/ingestion/chunk_splitter.py`
