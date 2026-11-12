## Goal

Trim `tests/db/test_rag_consistency.py` so it no longer seeds `rag_corpus_meta` or exercises
the removed unverifiable-corpus-generation class (`REQ-007`).

## Scope
**Release unit**: corpus-meta-removal

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
- Remove the `rag_corpus_meta` table seed (~line 76).
- Remove the `corpus_meta_verified` arguments from report fixtures (~lines 183, 612).
- Delete the tests of the removed unverifiable-corpus-generation class (~lines 658, 1128).
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
- `rg -n "corpus_meta|unverifiable corpus" scripts tests` returns nothing.
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
- **Requirement ID**: `REQ-007`
- **Source issue**: issues/20261110-170753_rmcompat003_rag-corpus-identity-decision.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261112-120011_rmcompat003_rag-corpus-identity-decision.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261112-223151
- **Related target files**: `tests/db/test_rag_consistency.py`
