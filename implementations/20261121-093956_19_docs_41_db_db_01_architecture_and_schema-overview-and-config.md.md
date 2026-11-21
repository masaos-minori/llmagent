## Goal

Update the disposable-store paragraph in `docs/41_db/db_01_architecture_and_schema-overview-and-config.md` so the dedup ledger description matches the new table name, lease/identity columns, and recreation semantics (REQ-012; AC-11).

## Scope
**Release unit**: docs-sync

## Assumptions
- Rows 01/17 have landed; this paragraph is the overview-level summary and must agree with db_03_07 (canonical) and db_08 (runbook).
- Current text (verified 2026-11-21, :36): "the dispatcher's `tool_call_state` dedup ledger ... recreated after loss" — stale on the table name and on the unconditional-recreation wording.

## Design decisions
- Recreation wording becomes identity-gated: a pre-change or replaced store is refused and archived by the operator, not silently recreated.

## Alternatives considered
- N/A: documentation reconciliation of frozen contract text.

## Implementation
### Target file
`docs/41_db/db_01_architecture_and_schema-overview-and-config.md`
### Procedure
Edit the :36 paragraph in place.
### Method
- Name `dedup_call_state` (+ `store_meta`, `call_attempt_history`), mention lease columns and the identity stamp, and replace "recreated after loss" with the refused-then-operator-recreated semantics.
### Details
- Keep the mdq sentence and the surrounding structure untouched.

## Compatibility considerations
- Overview links to db_03_07/db_08 stay valid (docs structure checker validates).

## Security considerations
- N/A: prose.

## Rollback considerations
- N/A: revert the commit.

## Validation plan
- `uv run python tools/check_docs_quality.py` and `uv run python tools/check_docs_structure.py` (routing.md docs gate).

## Completion criteria
- AC-11: the overview paragraph matches the implemented table name and identity-gated recreation semantics.

## Out of Scope
- Other paragraphs of db_01, other docs rows.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Update the doc per Implementation > Method | Pending | — | — | |
| 2 | Run the docs checkers (routing.md Tools) | Pending | — | — | |

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
- **Requirement ID**: REQ-012
- **Source issue**: issues/20261120-115841_mcpdl002_store-identity-continuity.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261121-083728_mcpdl002_store-identity-continuity.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261121-093956
- **Related target files**: `docs/41_db/db_01_architecture_and_schema-overview-and-config.md`
