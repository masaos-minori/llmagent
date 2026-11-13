## Goal

Remove the unverifiable-corpus-generation fatal class from the RAG consistency check
(`REQ-007`).

## Scope
**Release unit**: corpus-meta-removal

## Assumptions
- `_corpus_meta_verifiable(db)` tolerates an absent `rag_corpus_meta` table and is called in
  `check_rag_consistency()` to build `report.corpus_meta_verified`.
- `_unverifiable_corpus_issue(report)` builds the FATAL finding from that flag; the check is
  registered last in the `_CHECKS` list.

## Design decisions
- Delete `_corpus_meta_verifiable()`, `_unverifiable_corpus_issue()`, the
  `corpus_meta_verified` assignment and report-field use, and the `_ConsistencyCheck` entry;
  drop `_check_corpus_meta` from the import.

## Alternatives considered
N/A: removal is the decided Option B; keeping a dead check would reference a removed table.

## Implementation
### Target file
`scripts/db/rag_consistency.py`
### Procedure
- Remove `_check_corpus_meta` from `from db.rag_consistency_queries import (...)` (~line 11).
- Remove `corpus_meta_verified = _corpus_meta_verifiable(db)` and the
  `corpus_meta_verified=corpus_meta_verified` argument in the `RagConsistencyReport(...)`
  call (~lines 111, 137).
- Delete `_unverifiable_corpus_issue()` (lines 374-382) and `_corpus_meta_verifiable()`
  (lines 386-399).
- Remove the `_ConsistencyCheck(lambda report: report.corpus_meta_verified,
  _unverifiable_corpus_issue)` entry from `_CHECKS` (~line 447).
### Method
Four localized deletions; confirm no remaining reference to the three symbols.
### Details
- This is the third member of the `corpus-meta-removal` unit; delete before the DDL (seq 13)
  so fixtures that seed the table change with it.

## Compatibility considerations
N/A: the check verified only the removed table; schema inconsistency stays covered by the
fingerprint gate (ADR-004). No other Fatal abort is relaxed.

## Security considerations
N/A: no security-relevant behavior change.

## Rollback considerations
Revert the commit.

## Validation plan
- `rg -n "_corpus_meta_verifiable|_unverifiable_corpus_issue|_check_corpus_meta" scripts tests`
  returns nothing (the seq 10 probe removal lands in the same cycle).
  `corpus_meta_verified` remains only until the seq 12 `models.py` field removal; the table
  name `rag_corpus_meta` remains in `schema_sql.py` and fixture seeds until phase 8 (seq 13).
- `uv run pytest tests/db` passes only after seq 10/12 and companion test rows (seq 28,
  `test_db_recovery.py`) land in the same cycle.

## Completion criteria
The unverifiable-corpus-generation class is gone; `is_consistent()` keeps every other rule;
the consistency tests pass.

## Out of Scope
The report field (`REQ-007`, seq 12), the DDL table (seq 13), and the test trimming
(standalone doc 28).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | — | 20261113 | seq10-12 cycle 20261113 |
| 2 | Add or update tests per Validation plan | Completed | — | 20261113 | seq10-12 cycle 20261113 |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | — | 20261113 | seq10-12 cycle 20261113 |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | — | 20261113 | seq10-12 cycle 20261113 |

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
- **Related target files**: `scripts/db/rag_consistency.py`