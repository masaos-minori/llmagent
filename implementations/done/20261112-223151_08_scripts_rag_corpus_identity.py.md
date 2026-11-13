## Goal

Delete `scripts/rag/corpus_identity.py`, the corpus identity module, with its tests
(`REQ-006`).

## Scope
**Release unit**: corpus-meta-removal

## Verification Findings (2026-11-13)
- Sole remaining importer of `rag.corpus_identity`: `tests/deploy/test_init_db_schema_gate.py`
  (import line 39, seed call 142-144). Its cleanup is gated on the seq 13 DDL cycle (see seq
  32 findings), so this deletion executes in the seq 13 cycle together with seq 09 and seq 32,
  not before.

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
- This document is the first member of the `corpus-meta-removal` release unit (seq 08, 09,
  32, 10, 11, 12, 28, 20, 13, 14, 31 plus companion rows): delete the modules before
  removing the consistency class and the DDL. All importers of this module are already
  removed by earlier phases (seq 02 pipeline, 04 server, 06 ingester, 07 maintenance), so
  the deletion is safe once seq 32 (gate-test import) and seq 21 (its test module) land in
  the same cycle.

## Compatibility considerations
N/A: the module verified only the removed table; the fingerprint gate covers schema
inconsistency.

## Security considerations
N/A: no security-relevant behavior change.

## Rollback considerations
Revert the commit: restore both files from the prior commit.

## Validation plan
- `rg -n "corpus_identity|ensure_corpus_meta|bump_index_generation|compute_identity" scripts tests tools`
  returns nothing once seq 09 (identity_gate) and seq 32 (gate test import) land in the
  same cycle. The table name `rag_corpus_meta` legitimately still appears in the phase 7/8
  files (`scripts/db/schema_sql.py`, `rag_consistency*.py`, fixture seeds) until the rest of
  the release unit lands.
- `uv run pytest tests/rag tests/deploy` passes.

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
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | — | 20261113 | seq13 lockstep cycle 20261113 |
| 2 | Add or update tests per Validation plan | Completed | — | 20261113 | Covers companion `test_corpus_identity.py` seq13 lockstep cycle 20261113 |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | — | 20261113 | seq13 lockstep cycle 20261113 |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | — | 20261113 | seq13 lockstep cycle 20261113 |

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