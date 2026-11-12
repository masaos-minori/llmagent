## Goal

Delete `scripts/rag/identity_gate.py`, the local corpus identity reader, with its tests
(`REQ-006`).

## Scope
**Release unit**: corpus-meta-removal

## Assumptions
- `identity_gate.py` exposes `compute_local_identity()`, read-only against the open RAG DB.
- Its only consumers were `pipeline` (seq 02, already removed) and
  `rag_pipeline_server` (seq 04, already removed); deleting the module leaves no importer.

## Design decisions
- Delete the module file and its test module outright; no replacement, no alias.

## Alternatives considered
N/A: removal is the decided Option B; keeping an empty module would contradict it.

## Implementation
### Target file
`scripts/rag/identity_gate.py`
### Procedure
- Delete `scripts/rag/identity_gate.py`.
- Delete `tests/rag/test_identity_gate.py`.
### Method
Two file deletions via `git rm`; confirm no remaining reference to `compute_local_identity`
anywhere.
### Details
- Part of the `corpus-meta-removal` release unit with seq 08 and seq 11.

## Compatibility considerations
N/A: the reader fed a fail-closed identity that no longer exists; the fingerprint gate
covers schema inconsistency.

## Security considerations
N/A: no security-relevant behavior change.

## Rollback considerations
Revert the commit: restore both files from the prior commit.

## Validation plan
- `rg -n "compute_local_identity|identity_gate" scripts tests` returns nothing (excluding
  the preserved ADR-010 text).
- `uv run pytest tests/rag` passes.

## Completion criteria
Both files are gone; no importer references the deleted names.

### Companion test files
- `tests/rag/test_identity_gate.py`
  - Procedure: delete the file alongside the reader it tests.
  - Validation: `uv run pytest tests/rag` passes; the module is gone.

## Out of Scope
The identity module (`scripts/rag/corpus_identity.py`, seq 08) and the consistency class
(`REQ-007`, seq 11).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | Covers companion `test_identity_gate.py` |
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
- **Related target files**: `scripts/rag/identity_gate.py`, `tests/rag/test_identity_gate.py`
