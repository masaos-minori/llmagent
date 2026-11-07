# Implementation Procedure: docs/41_db/db_03_07_mcp-dedup-and-execution-snapshot.md

## Goal
Correct the provenance framing of the MCP dedup / execution snapshot tables: they are part of the
canonical schema, not the product of a workflow migration ledger or `migrations_workflow.py`.

## Scope
- Target file: `docs/41_db/db_03_07_mcp-dedup-and-execution-snapshot.md` (MODIFY).
- Release unit: `policy-finalization`.
- Related requirement / acceptance criteria: REQ-005 / AC-004 (frozen target row 11).

## Assumptions
- Anchors grep-verified: lines 46-48 and 74-78 cite the workflow migration ledger and
  `migrations_workflow.py` as the tables' provenance; an Adoption Path section (lines 134-141)
  describes adoption via migration and must be re-expressed as the current creation path.
- compatrm001 owns the deletion of the migration modules; this document edit only removes their
  live citation.

## Design decisions
- Provenance becomes: tables are defined in the canonical schema definition and created at
  database creation; any table-not-present condition is a startup error (current-only policy).
- If a historical sentence about the former ledger is needed for context, it carries `historical`
  / `removed` on the same or a preceding line (10-line window rule).

## Alternatives considered
- Deleting the whole provenance subsection: rejected — readers need to know where the tables are
  defined; only the mechanism attribution is wrong.

## Implementation

### Target file
- `docs/41_db/db_03_07_mcp-dedup-and-execution-snapshot.md` (MODIFY).

### Procedure
1. Lines 46-48: replace migration-ledger provenance sentences with canonical-schema provenance.
2. Lines 74-78: same for the execution-snapshot table's provenance passage.
3. Lines 134-141 (Adoption Path): rewrite "adopt via migration" guidance as
   create-from-canonical-schema / archive-and-recreate guidance.
4. Sweep the file for the five doc-claim phrases; mark historical mentions or remove.

### Method
- Text edits; checker doc-claim + doc-symbol pass afterwards (backticked
  `migrations_workflow.py` citations must not survive as live references).

### Details
- Table DDL descriptions themselves stay; only mechanism attribution changes.

## Compatibility considerations
- docs consistency CI must stay green.

## Security considerations
- None.

## Rollback considerations
- Single-file revert.

## Validation plan
- Checker blocking run exit 0; docs consistency CI.

## Completion criteria
- No live citation of the migration ledger or `migrations_workflow.py`; provenance states the
  canonical schema path; checker green.

## Out of Scope
- Other db docs (docs 12-13).

## Execution Status
| Step | Status | Notes |
|---|---|---|
| 1 Lines 46-48 | Pending | |
| 2 Lines 74-78 | Pending | |
| 3 Lines 134-141 | Pending | |
| 4 Sweep | Pending | |

### Blocker Log
- None.

### Work Items Created
- None.

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: REQ-005 / AC-004
- **Source issue**: issues/20261106-125145_compatrm004_finalize-no-compatibility-policy-across-ci-tests-docs.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261107-064415_compatrm004_finalize-no-compatibility-policy-across-ci-tests-docs.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261107-103000
- **Related target files**: `docs/41_db/db_03_07_mcp-dedup-and-execution-snapshot.md`
