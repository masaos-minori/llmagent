## Goal

Stop `RagIngester` from bumping the corpus index generation so the ingester write path no
longer touches the removed `rag_corpus_meta` table (`REQ-004`).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- `bump_index_generation()` is imported from `rag.corpus_identity` and called once inside
  the ingestion loop, guarded by `if total_success > 0`.
- `total_success` is still read elsewhere (the completion summary at `ingester.py:200`), so
  only the bump condition is removed, not the variable.

## Design decisions
- Delete the import and the single `bump_index_generation(db)` call; leave `total_success`
  and the rest of the loop unchanged.

## Alternatives considered
N/A: removal is the decided Option B; keeping a no-op call would import a deleted module.

## Implementation
### Target file
`scripts/rag/ingestion/ingester.py`
### Procedure
- Remove `from rag.corpus_identity import bump_index_generation` (import line, line 20).
- Remove the `if total_success > 0:` block that calls `bump_index_generation(db)` together
  with its RAGCORPUS001 comment block (~lines 175-181); keep `total_success` (line 174) and
  the result aggregation that follows (line 183 onward).
### Method
Two localized deletions; confirm no remaining reference to `bump_index_generation` or the
removed import.
### Details
- `total_success` is still summed and logged after this block, so do not delete it.
- This edit overlaps `scripts/rag/ingestion/ingester.py` with `rmcompat001` (sequencing
  dependency): that Plan edits the same file's `__del__`/`_log_ingest_failure`; apply this
  edit to a re-read of the file.

## Compatibility considerations
N/A: the ingester write path simply stops recording a generation; no compatibility key.

## Security considerations
N/A: no security-relevant behavior change.

## Rollback considerations
Revert the commit.

## Validation plan
- `rg -n "bump_index_generation|index_generation" scripts/rag/ingestion tests/rag/ingestion`
  returns nothing after `tests/rag/ingestion/test_ingester_index_generation.py` is deleted
  by seq 23 in the same cycle. (Scoped to the ingestion paths: `scripts/rag/corpus_identity.py`
  and `scripts/rag/identity_gate.py` legitimately still match until the release unit removes
  them in phase 6.)
- `uv run pytest tests/rag/ingestion` passes.

## Completion criteria
`ingester.py` imports and calls no `bump_index_generation`; `total_success` is intact; the
ingestion tests pass.

### Companion test files
- `tests/rag/ingestion/test_ingester.py` — DEFERRED to the seq 13 cycle (2026-11-13
  verification): the fixture runs `DocumentManager.check_consistency` →
  `check_rag_consistency` → `verify_schema_fingerprint`, which compares the fixture DB
  against the canonical rag DDL (`shared.schema_fingerprint`). The fixture's own
  `rag_corpus_meta` DDL copy (lines 37, 64-71) and seeded row (line 105) must therefore be
  removed in the same cycle as the canonical DDL table (seq 13), not here.

## Out of Scope
The deleted index-generation test (`tests/rag/ingestion/test_ingester_index_generation.py`,
seq 23) and the maintenance wrapper (`REQ-005`, seq 07).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261113-101936 | 20261113-102229 |  |
| 2 | Add or update tests per Validation plan | Completed | — | 20261113-102229 | Covers companion `test_ingester.py` companion test_ingester.py deferred to seq 13 cycle (fingerprint coupling) |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | — | 20261113-102229 |  |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | — | 20261113-102229 |  |

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
- **Requirement ID**: `REQ-004`
- **Source issue**: issues/20261110-170753_rmcompat003_rag-corpus-identity-decision.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261112-120011_rmcompat003_rag-corpus-identity-decision.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261112-223151
- **Related target files**: `scripts/rag/ingestion/ingester.py`, `tests/rag/ingestion/test_ingester.py`