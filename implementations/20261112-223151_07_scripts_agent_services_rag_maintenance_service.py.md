## Goal

Remove `RagMaintenanceService`'s `corpus_identity()` wrapper so the maintenance service no
longer wraps `ensure_corpus_meta()` (`REQ-005`).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- The wrapper is a thin method over `rag.corpus_identity.ensure_corpus_meta`, imported at
  the top of the module alongside `CorpusIdentity`.
- No other maintenance method calls `corpus_identity()`.

## Design decisions
- Delete the `corpus_identity()` method, the `NOTE (RAGCORPUS001...)` comment above it, and
  the `ensure_corpus_meta` name from the multi-line import; keep `CorpusIdentity` if still
  referenced, otherwise drop it too.

## Alternatives considered
N/A: removal is the decided Option B; a stub would keep a dead wrapper.

## Implementation
### Target file
`scripts/agent/services/rag_maintenance_service.py`
### Procedure
- Delete the `# NOTE (RAGCORPUS001, doc 06): ...` comment block above the method (~lines
  60-67).
- Delete the `def corpus_identity(self, *, embedding_model_id, schema_version) -> ...`
  method (~lines 68-83).
- Remove `ensure_corpus_meta` from the `from rag.corpus_identity import (CorpusIdentity,
  ensure_corpus_meta)` import (~line 16); drop `CorpusIdentity` as well if it is now unused.
### Method
Method plus comment plus import-name deletions; confirm no remaining reference to
`corpus_identity` or `ensure_corpus_meta`.
### Details
- Re-check whether `CorpusIdentity` is still used after removing the method; if not, remove
  it from the import too so `lint-imports` stays clean.

## Compatibility considerations
N/A: internal maintenance method removal; no external contract.

## Security considerations
N/A: no security-relevant behavior change.

## Rollback considerations
Revert the commit.

## Validation plan
- `rg -n "corpus_identity|ensure_corpus_meta" scripts/agent/services/rag_maintenance_service.py`
  returns nothing.
- `uv run pytest tests/agent/services/test_rag_index_integrity.py` passes.

## Completion criteria
`RagMaintenanceService` has no `corpus_identity()` method and imports no
`ensure_corpus_meta`; the integrity tests pass.

### Companion test files
- `tests/agent/services/test_rag_index_integrity.py`
  - Procedure: remove the `corpus_identity()` tests and the extra DDL created for the table
    (imports at lines 12-13, DDL at lines 79-83, and the two fixture references at lines
    555, 574).
  - Validation: `uv run pytest tests/agent/services/test_rag_index_integrity.py` passes.

## Out of Scope
The identity module deletion (`REQ-006`, seq 08/09) and the maintenance-wrapper consumer in
other services.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | Covers companion `test_rag_index_integrity.py` |
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
- **Requirement ID**: `REQ-005`
- **Source issue**: issues/20261110-170753_rmcompat003_rag-corpus-identity-decision.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261112-120011_rmcompat003_rag-corpus-identity-decision.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261112-223151
- **Related target files**: `scripts/agent/services/rag_maintenance_service.py`, `tests/agent/services/test_rag_index_integrity.py`
