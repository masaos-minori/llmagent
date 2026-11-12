## Goal

Delete `scripts/rag/corpus_identity.py`, the corpus identity module, with its tests
(`REQ-006`).

## Scope
**Release unit**: corpus-meta-removal

## Assumptions
- `corpus_identity.py` exposes `compute_identity()` and `ensure_corpus_meta()`; it is
  imported by `pipeline` (via `identity_gate`), `ingester` (seq 06, `bump_index_generation`),
  `rag_maintenance_service` (seq 07, `ensure_corpus_meta`), and
  `tests/deploy/test_init_db_schema_gate.py`.
- Every importer is a target row of this Plan, so deleting the module leaves no dangling
  import once its siblings land.

## Design decisions
- Delete the module file and its test module outright; no replacement, no alias.

## Alternatives considered
N/A: removal is the decided Option B; keeping an empty module would contradict it.

## Implementation
### Target file
`scripts/rag/corpus_identity.py`
### Procedure
- Delete `scripts/rag/corpus_identity.py`.
- Delete `tests/rag/test_corpus_identity.py`.
### Method
Two file deletions via `git rm`; confirm no remaining reference to the module's public
names (`compute_identity`, `ensure_corpus_meta`, `bump_index_generation`) anywhere.
### Details
- This is one release unit with seq 11 (consistency class) and seq 13 (DDL): delete the
  modules before removing the consistency class and the DDL so the last three form the
  `corpus-meta-removal` unit.

## Compatibility considerations
N/A: the module verified only the removed table; the fingerprint gate covers schema
inconsistency.

## Security considerations
N/A: no security-relevant behavior change.

## Rollback considerations
Revert the commit: restore both files from the prior commit.

## Validation plan
- `rg -n "corpus_identity|rag_corpus_meta|bump_index_generation" scripts tests` returns
  nothing (excluding the preserved ADR-010 text).
- `uv run pytest tests/rag` passes.

## Completion criteria
Both files are gone; no importer references the deleted names.

### Companion test files
- `tests/rag/test_corpus_identity.py`
  - Procedure: delete the file alongside the module it tests.
  - Validation: `uv run pytest tests/rag` passes; the module is gone.

## Out of Scope
The identity-gate reader (`scripts/rag/identity_gate.py`, seq 09) and the consistency class
(`REQ-007`, seq 11).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | Covers companion `test_corpus_identity.py` |
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
- **Requirement ID**: `REQ-006`
- **Source issue**: issues/20261110-170753_rmcompat003_rag-corpus-identity-decision.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261112-120011_rmcompat003_rag-corpus-identity-decision.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261112-223151
- **Related target files**: `scripts/rag/corpus_identity.py`, `tests/rag/test_corpus_identity.py`
