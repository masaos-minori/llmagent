## Goal
Document the new unverifiable-result findings (`REQ-007`: every finding appears with severity and `repair_action`) so the table and the startup text match `scripts/db/rag_consistency.py` after procedure 02.

## Scope
**Release unit**: N/A: not part of a release unit
- In scope: the `Repair Decision Flow` table, the closing `repair_action` paragraph, and the `Startup Warnings` bullets.
- Scope amendment against the Issue's Target Files, decided by the maintainer for this Plan.

## Assumptions
- Procedure 02 sets the values: severity Degraded, `repair_action` `rerun_check`, five rules (checked against the plan).
- The fallback FATAL entry of procedure 04 is described in the Startup Warnings text.

## Design decisions
- Group the five rules into three table rows: diagnostic errors, failed read smoke test, and unverified FK/embedding-dimension/schema probes.
- Place the new rows after `URL-level inconsistency` (the Degraded rows) and before the Fatal rows.

## Alternatives considered
N/A: documentation follows the code.

## Implementation
### Target file
`docs/21_rag/rag_05_07-rag-index-consistency-checks.md`

### Procedure
1. Add the three table rows (Severity `Degraded`, `repair_action` `rerun_check`, Fix: re-run the consistency check after the database error or unreadable table is resolved).
2. In `Startup Warnings`, extend the Degraded bullet with the unverifiable results and add one sentence: an inconsistent result that carries no finding is recorded as a fatal `rag_consistency` entry.
3. In the closing paragraph, say `rerun_check` findings need the check to be run again after the cause is fixed.

### Method
- Copy the column order of the existing rows.
- Keep the sentence "ADR-004 classifies these results as availability failures of the RAG derived indexes" true for the new rows.

### Details
- The file is 6510 bytes; the limit is 32768.
- Do not edit the example console block.

## Compatibility considerations
N/A: documentation only.

## Security considerations
N/A: documentation only.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run python tools/check_docs_structure.py` and the other checkers `routing.md` Tools lists for a `docs/` edit.

## Completion criteria
- The table lists each new finding with the code's severity and `repair_action`; the startup text mentions unverifiable results and the fallback fatal entry.

## Out of Scope
- Code (procedures 02 and 04), ADR text.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Edit the table, the Startup Warnings bullets, and the closing paragraph (Implementation > Procedure) | Completed | 20261118-140956 | 20261118-140956 | Changed: docs/21_rag/rag_05_07-rag-index-consistency-checks.md. Docs checkers pass. |
| 2 | Run the documentation checkers (Validation plan) | Completed | 20261118-140956 | 20261118-140956 | — |

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
- **Requirement ID**: REQ-007
- **Source issue**: issues/20261117-123005_adrchk005_startup-fail-closed.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261118-134945_adrchk005_startup-fail-closed.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261118-135645
- **Related target files**: `docs/21_rag/rag_05_07-rag-index-consistency-checks.md`
