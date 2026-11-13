## Goal

Remove the `ensure_corpus_meta` import and its seed from the fingerprint-gate tests
(`REQ-006`).

## Scope
**Release unit**: corpus-meta-removal

## Verification Findings (2026-11-13)
- Execution coupling (proven 2026-11-13): applying this document while the seq 10 probe and
  the seq 13 DDL still exist makes `test_recovery_drill_runs_under_flag_and_leaves_fixtures_untouched`
  fail FATAL — the provisioned fixture has the table but no meta row, and the drill's
  logical layer treats that as fatal. The import removal is likewise bound to the seq 08
  module deletion. Therefore this whole document executes in the seq 13 cycle (modules 08/09
  deleted, seed dropped together with the table). An early attempt was applied and reverted
  (`git checkout tests/deploy/test_init_db_schema_gate.py`).
- Import: line 39 `from rag.corpus_identity import ensure_corpus_meta`.
- Docstring mention: `_provision_canonical_vec_db` docstring (lines 121-122) names the seeded
  `rag_corpus_meta` corpus identity — reword it along with the seed deletion.
- Seed: the actual seed is the `ensure_corpus_meta(helper, embedding_model_id="test-model",
  schema_version="1")` call at lines 142-144 inside `if name == "rag":`; the documents/chunks/
  chunks_vec inserts that follow stay.

## Assumptions
- `tests/deploy/test_init_db_schema_gate.py` imports `ensure_corpus_meta` and seeds the
  `rag_corpus_meta` table to exercise the fingerprint gate (lines 39, 122).

## Design decisions
- Drop the import and the seed; keep every other fingerprint-gate test unchanged.

## Alternatives considered
N/A: removal is the decided Option B; the seed references a table the DDL no longer creates.

## Implementation
### Target file
`tests/deploy/test_init_db_schema_gate.py`
### Procedure
- Remove the `ensure_corpus_meta` import (line 39).
- Remove the `ensure_corpus_meta(...)` seed call (lines 142-144), keeping the `if name ==
  "rag":` branch and its remaining inserts.
- Reword the `_provision_canonical_vec_db` docstring (lines 121-122) to drop the
  `rag_corpus_meta` sentence.
### Method
Import plus seed deletion; confirm no remaining reference to `ensure_corpus_meta`.
### Details
- The module `rag.corpus_identity` is deleted by seq 08; delete together so the module
  imports cleanly.

## Compatibility considerations
N/A: test-only; the table is dropped from the canonical DDL by the sibling code document.

## Security considerations
N/A: no security-relevant behavior change.

## Rollback considerations
Revert the commit.

## Validation plan
- Scoped: `rg -n "corpus_meta|ensure_corpus_meta" tests/deploy/test_init_db_schema_gate.py`
  returns nothing. The cross-file search over `scripts tests` only passes at release-unit end
  (fixtures in other unit members still hold those names mid-unit).
- `uv run pytest tests/deploy` passes.

## Completion criteria
The import and seed are gone; the fingerprint-gate tests pass.

## Out of Scope
The identity module (`REQ-006`, seq 08) and the DDL table (seq 13).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | — | 20261113 | seq13 lockstep cycle 20261113 |
| 2 | Add or update tests per Validation plan | Completed | — | 20261113 | seq13 lockstep cycle 20261113 |
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
- **Related target files**: `tests/deploy/test_init_db_schema_gate.py`