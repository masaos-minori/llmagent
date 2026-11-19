## Goal

Confirm that `ChunkSplitter._chunk_code` still drives the code path correctly after the collaborator extraction, and modify the call site only if `merge_text_items`' signature changed (`REQ-002`, `REQ-006`). Because `merge_text_items` keeps its signature (see the `chunk_utils.py` row), no change to `chunk_splitter.py` is expected. The call site lives in `_chunk_code` (`scripts/rag/ingestion/chunk_splitter.py:305-323`). The call site lives in `_chunk_code` (`scripts/rag/ingestion/chunk_splitter.py:305-323`).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- `merge_text_items` retains its exact signature and return value (thin delegating wrapper), so `chunk_splitter._chunk_code` (`scripts/rag/ingestion/chunk_splitter.py:305-323`, which calls `merge_text_items`) needs no edit.
- `chunk_index` ordering set here is unaffected by the extraction.

## Design decisions
N/A: verification-only row; no design decision unless the call site must change.

## Alternatives considered
N/A: verification-only.

## Implementation
### Target file
`scripts/rag/ingestion/chunk_splitter.py`

### Procedure
1. Verify `merge_text_items`' signature is unchanged (compare against the `chunk_utils.py` row) and that `_chunk_code`'s call still matches.
2. If and only if the signature changed, update the `_chunk_code` call site accordingly.

### Method
- Read `_chunk_code` (`scripts/rag/ingestion/chunk_splitter.py:305-323`) and confirm the `merge_text_items(items, "\n\n", min_chunk, max_chunk, chunk_overlap)` call is unchanged. Record the verification result.

### Details
- If no change is required, state so explicitly; do not introduce an unrelated edit (`AGENTS.md` Global Rule 5).

## Compatibility considerations
- No public-API or `chunk_index` change expected.

## Security considerations
N/A: verification-only.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- Regression: `uv run pytest tests/rag/ingestion/test_chunk_splitter.py` code-chunk cases produce zero diff from baseline.

## Completion criteria
- `_chunk_code`'s `merge_text_items` call is confirmed unchanged (or corrected if the signature changed), and code-chunk regression cases pass.

## Out of Scope
- Any change to `merge_text_items` itself — covered by the `chunk_utils.py` row.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Verify/adjust the `_chunk_code` call site | Pending | — | — | |
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
- **Requirement ID**: `REQ-002` (`merge_text_items` entry unchanged for `_chunk_code`) and `REQ-006` (output/order unchanged)
- **Source issue**: `issues/20261119-112017_ragcrv005_unify-chunk-merge-strategies.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261119-185003_ragcrv005_unify-chunk-merge-strategies.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261119-194357
- **Related target files**: `scripts/rag/ingestion/chunk_splitter.py`
