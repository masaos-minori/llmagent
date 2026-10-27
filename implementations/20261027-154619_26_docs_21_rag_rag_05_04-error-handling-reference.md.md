# Implementation Procedure: Rename the failure-mode table key in the error-handling reference (rag_05_04)

## Goal

Rename the single key occurrence in the error-handling reference's failure-mode table so the
page names the renamed key (REQ-005, AC-5).

## Scope

- One occurrence (verified 2026-10-27): the table row "Failure when setting
  `rag_service_url` | Fallback to in-process pipeline" at L97.
- No other part of the page changes.

## Assumptions

- Documentation-only row; churn 8 commits/30d per the Plan Affected areas.
- This page is also touched by the rag004 Plan (ingester error-handling additions); the rows
  are disjoint (rag004 targets ingestion-side error rows); second implementer rebases.

## Design decisions

- N/A: mechanical rename fixed by REQ-005.

## Alternatives considered

- N/A.

## Implementation
### Target file

`docs/21_rag/rag_05_04-error-handling-reference.md`

### Procedure

1. Rename the key in the L97 table cell to `rag_query_service_url` (new); the fallback
   description stays byte-identical.

### Method

Single-token rename inside a table cell.

### Details

- N/A: grep verified exactly one standalone occurrence in this file.

## Compatibility considerations

- Docs only.

## Security considerations

- N/A: docs only.

## Rollback considerations

- N/A: revert the commit.

## Validation plan

- `uv run python tools/check_docs_quality.py`, `uv run python tools/check_docs_structure.py
  docs/21_rag/rag_05_04-error-handling-reference.md`,
  `uv run python tools/check_docs_content_policy.py`,
  `uv run python tools/check_docs_consistency.py --domain rag` — all clean.

## Completion criteria

- AC-5: zero standalone old-spelling mentions on this page.

## Out of Scope

- The rag004 Plan's ingestion error-handling edits (separate Plan) and all other doc pages.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | Phase 4 row; land after Phase 2-3 rows |
| 2 | Run the documentation checkers (`routing.md` Tools: docs quality/structure/content-policy/consistency --domain rag) | Pending | — | — | |

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
- **Requirement ID**: REQ-005
- **Source issue**: issues/20261027-071953_rag003_rag-url-key-ambiguity.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261027-110727_rag003_rag-url-key-ambiguity.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261027-154619
- **Related target files**: docs/21_rag/rag_05_04-error-handling-reference.md
