## Goal

Remove the `_check_corpus_meta` fatal-class probe from the RAG consistency query layer
(`REQ-007`).

## Scope
**Release unit**: corpus-meta-removal

## Assumptions
- `_check_corpus_meta(db)` is the SQL probe that counts rows in `rag_corpus_meta` and
  returns whether a single id-bearing row exists; it is imported by
  `db/rag_consistency.py` (seq 11).

## Design decisions
- Delete the `_check_corpus_meta` function and its docstring line; the module's probe
  inventory in its module docstring also lists it and should be dropped.

## Alternatives considered
N/A: removal is the decided Option B; an empty probe would import a deleted table name.

## Implementation
### Target file
`scripts/db/rag_consistency_queries.py`
### Procedure
- Delete the `_check_corpus_meta(db: SQLiteHelper) -> bool` function (~lines 283-300).
- Remove the `_check_corpus_meta` entry from the module-level probe inventory comment block
  (~line 12).
### Method
Function plus docstring-inventory deletion; confirm no remaining reference anywhere.
### Details
- The caller in `db/rag_consistency.py` (seq 11) removes the corresponding finding and the
  check entry together; do not leave a dangling call.

## Compatibility considerations
N/A: the probe verified only the removed table; the fingerprint gate covers schema
inconsistency.

## Security considerations
N/A: no security-relevant behavior change.

## Rollback considerations
Revert the commit.

## Validation plan
- `rg -n "corpus_meta|unverifiable corpus" scripts tests` returns nothing.
- `uv run pytest tests/db` passes.

## Completion criteria
`_check_corpus_meta` is gone from the query layer; no caller references it.

## Out of Scope
The finding and report field (`REQ-007`, seq 11/12) and the test trimming (standalone doc
28).

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
- **Related target files**: `scripts/db/rag_consistency_queries.py`
