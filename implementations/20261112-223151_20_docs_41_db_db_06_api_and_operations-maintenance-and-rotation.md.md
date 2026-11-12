## Goal

Remove `corpus_meta_verified` from the `is_consistent` rule list in the DB operations
document (`REQ-010`).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- The field is enumerated in the `is_consistent(report)` rule list (~line 50), which lists
  every clean rule including `corpus_meta_verified`.

## Design decisions
- Drop `` `corpus_meta_verified` `` from the enumerated rule list; keep the other rules.

## Alternatives considered
N/A: removal is the decided Option B; keeping the name would describe a removed rule.

## Implementation
### Target file
`docs/41_db/db_06_api_and_operations-maintenance-and-rotation.md`
### Procedure
- Remove `, `corpus_meta_verified`` from the `is_consistent` rule list (~line 50).
### Method
Single-list-item deletion; confirm no `corpus_meta_verified` remains in the document.
### Details
- The runtime field is removed by the sibling code document (seq 12).

## Compatibility considerations
N/A: documentation-only; the report field is removed by the sibling code document.

## Security considerations
N/A: no security-relevant behavior change.

## Rollback considerations
Revert the commit.

## Validation plan
- `rg -n "corpus_meta_verified" docs` returns nothing.
- `uv run python tools/check_docs_quality.py`, `check_docs_structure.py`,
  `check_docs_content_policy.py`, `check_docs_consistency.py --domain db` report no
  findings.

## Completion criteria
The DB operations document lists no `corpus_meta_verified` rule; the DB docs checkers pass.

## Out of Scope
The report field (`REQ-007`, seq 12) and the consistency class (seq 11).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | Documentation checkers only |
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
- **Requirement ID**: `REQ-010`
- **Source issue**: issues/20261110-170753_rmcompat003_rag-corpus-identity-decision.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261112-120011_rmcompat003_rag-corpus-identity-decision.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261112-223151
- **Related target files**: `docs/41_db/db_06_api_and_operations-maintenance-and-rotation.md`
