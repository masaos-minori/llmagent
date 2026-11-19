## Goal

Confirm that `chunk_splitter.py` already produces the Shape B behavior for English and
requires no source change once `chunk_english.py` returns the unfiltered original
(`REQ-001`, `REQ-002`). Document this so the sibling `chunk_english.py` change is the
only code edit in Phase 2.

## Scope
**Release unit**: english-content-stopword-loss

## Assumptions

- Shape B drops filtering: English `normalized_content` is `NULL`, so the `content`
  triple carries the unfiltered original and the normalized slot is empty/`NULL`.
- `chunk_english.py` (sibling procedure) is the only file that changes in Phase 2; this
  document verifies that `chunk_splitter.py` passes that value through unchanged.

## Design decisions

- `N/A: no design decision is made here. Shape B is fixed by the owner decision
  (UNK-01, 20261119-130500); this document records that the current
  `chunk_splitter.py` already realizes it.`

## Alternatives considered

- `N/A: no code alternative. The `("text", c, "")` literal and `norm_content or None`
  already encode Shape B (see Procedure).`

## Implementation
### Target file
`scripts/rag/ingestion/chunk_splitter.py`

### Procedure
No source modification is required for Shape B. Verify the two existing sites realize
it:

1. `_build_text_triples` (`chunk_splitter.py:299`):
   `return [("text", c, "") for c in self._chunk_english(content)]`. After the sibling
   `chunk_english.py` change, `c` is the unfiltered original, so the `content` triple is
   the original text (`REQ-001`) and the third tuple element is `""` (Shape B).
2. `_build_chunk_payload` (`chunk_splitter.py:389`):
   `"normalized_content": norm_content or None`. With `norm_content == ""`, this stores
   `None` (`NULL`) (`REQ-002`).

Optionally add an inline comment at `chunk_splitter.py:299` noting that the `""` is the
Shape B sentinel (English/code/non-normalized text → `NULL` per ADR-009 INV-04). This is
documentation only; do not alter control flow.

### Method

Do not change the return expression at `chunk_splitter.py:299` or the payload dict at
`chunk_splitter.py:389`. Confirm they read exactly as above. If the inline comment is
added, it must not change behavior.

### Details

- No symbols, imports, or signatures are created or changed.
- The Japanese path (`chunk_splitter.py:289-292`, `_chunk_japanese`) and markdown path
  are untouched. Code triples (`_build_code_triples`) are unchanged.
- This document modifies only `chunk_splitter.py`; the actual value change originates in
  the sibling `chunk_english.py` procedure.

## Compatibility considerations

- Behavior of `chunk_splitter.py` itself does not change; only its input
  (`_chunk_english` output) changes via the sibling procedure. FTS5 indexes the now
  original `content` via `COALESCE(normalized_content, content)`; see the FTS
  regression tests.

## Security considerations

`N/A: no auth, secrets, network, or user-data handling changes.`

## Rollback considerations

Revert the single commit; `chunk_splitter.py` reverts with it (no net change to this
file).

## Validation plan

- Unit: `uv run pytest tests/rag/ingestion/test_chunk_splitter.py` — the new test asserts
  the `content` triple is the unfiltered original and `normalized_content` is `NULL`
  (`REQ-002`).
- Regression: `TestChunkPayloadKeyContract` and the Japanese chunking tests stay green.

## Completion criteria

- `_build_text_triples` (`chunk_splitter.py:299`) emits `("text", c, "")` with `c` the
  unfiltered original, and `_build_chunk_payload` (`chunk_splitter.py:389`) stores
  `NULL` for English.
- No behavioral change to `chunk_splitter.py` beyond the optional comment.

## Out of Scope

- The stored-value change itself (`chunk_english.py`, `REQ-001`) — covered by the sibling
  procedure.
- The REQ-006 test body — covered by the sibling test procedure.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 2026-11-19 | 2026-11-19 | Verified chunk_splitter.py:299/:389 already realize Shape B; no source change |
| 2 | Add or update tests per Validation plan | Completed | 2026-11-19 | 2026-11-19 | No source change; no new test from this proc |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 2026-11-19 | 2026-11-19 | pytest + 822 RAG tests pass |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 2026-11-19 | 2026-11-19 | No doc change from this proc |

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
- **Requirement ID**: `REQ-001` (unfiltered `content` passes through), `REQ-002`
  (`normalized_content` NULL, Shape B)
- **Source issue**: `issues/20261119-112014_ragcrv002_english-content-stopword-loss.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261119-123746_ragcrv002_english-content-stopword-loss.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261119-132013
- **Related target files**: `scripts/rag/ingestion/chunk_splitter.py`
