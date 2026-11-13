## Goal

Trim `tests/db/test_rag_consistency.py` so it no longer seeds `rag_corpus_meta` or exercises
the removed unverifiable-corpus-generation class (`REQ-007`).

## Scope
**Release unit**: corpus-meta-removal

## Verification Findings (2026-11-13)
- Current references in `tests/db/test_rag_consistency.py`: the `rag_corpus_meta` INSERT seed
  at lines 76-79 (inside `_make_rag_db`), and `corpus_meta_verified=True` report-construction
  kwargs at lines 654 and 1136. The Plan's cited 183/612/658/1128 have drifted; these are the
  current numbers.
- There are no dedicated test functions for the unverifiable-corpus-generation class; class
  coverage is exactly those two kwargs (adjust any assertion that reads
  `report.corpus_meta_verified` in the same tests).
- The fixture schema is derived from the canonical DDL: `_RAG_SCHEMA =
  _fallback_from_canonical(build_rag_schema_sql(EMBED_DIMS))` (line 67). When seq 13 removes
  the table from `schema_sql.py`, this fixture follows automatically — but seq 28 must run
  in the same cycle as seq 13: removing the seed while the probe (seq 10) and the DDL
  (seq 13) still exist makes the consistency/drill logical layer report a fatal missing
  meta row (proven by the `test_init_db_schema_gate` drill failure when its seed was
  dropped early on 2026-11-13); removing it after seq 13 executes the INSERT against an
  absent table. The `corpus_meta_verified` kwargs and probe-class tests go with the
  seq 10/11/12 cycle; the seed goes with the seq 13 cycle.

## Assumptions
- The test seeds the `rag_corpus_meta` table and passes `corpus_meta_verified` to report
  fixtures, plus dedicated tests of the removed fatal class (lines 76, 183, 612, 658,
  1128).

## Design decisions
- Remove the table seed and the `corpus_meta_verified` arguments; delete the tests of the
  removed class; keep every other fatal-class and degraded-class test unchanged.

## Alternatives considered
N/A: removal is the decided Option B; the tests exercise a removed class.

## Implementation
### Target file
`tests/db/test_rag_consistency.py`
### Procedure
- Remove the `rag_corpus_meta` table seed (lines 76-79).
- Remove the `corpus_meta_verified=True` kwargs at lines 654 and 1136, and any assertion in
  those tests that reads `report.corpus_meta_verified`.
- No dedicated removed-class test functions exist; no test deletion beyond the kwarg/assertion
  removals.
### Method
Targeted deletions; confirm no remaining `rag_corpus_meta` seed or `corpus_meta_verified`
reference and no test of the removed class.
### Details
- Part of the `corpus-meta-removal` unit; the class and field it tests are removed by
  seq 11 and seq 12.

## Compatibility considerations
N/A: test-only; the verified class only covered the removed table.

## Security considerations
N/A: no security-relevant behavior change.

## Rollback considerations
Revert the commit.

## Validation plan
- Scoped: `rg -n "corpus_meta|unverifiable corpus" tests/db/test_rag_consistency.py` returns
  nothing. The cross-file search over `scripts tests` only passes at release-unit end (other
  unit members still hold those names mid-unit).
- `uv run pytest tests/db` passes; every other fatal-class and degraded-class test is
  unchanged.

## Completion criteria
The seeded table, `corpus_meta_verified` arguments, and removed-class tests are gone; the
other consistency tests pass.

## Out of Scope
The consistency class (`REQ-007`, seq 11), the report field (seq 12), and the DDL (seq 13).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261113 | 20261113 | kwargs/test trims done in seq10-12 cycle 20261113; seed deletion deferred to seq 13 cycle seq13 lockstep cycle 20261113 |
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
- **Requirement ID**: `REQ-007`
- **Source issue**: issues/20261110-170753_rmcompat003_rag-corpus-identity-decision.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261112-120011_rmcompat003_rag-corpus-identity-decision.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261112-223151
- **Related target files**: `tests/db/test_rag_consistency.py`