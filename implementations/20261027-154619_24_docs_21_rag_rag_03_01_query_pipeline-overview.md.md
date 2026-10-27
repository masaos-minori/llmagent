# Implementation Procedure: Rename the flow-diagram key in the query-pipeline overview page (rag_03_01)

## Goal

Rename the single key occurrence in the pipeline flow description so the overview names the
renamed key (REQ-005, AC-5).

## Scope

- One occurrence (verified 2026-10-27): the flow line "→ rag_service_url is configured? →
  call_rag_service() → fallback to in-process execution on failure" at L36.
- No other part of the page changes.

## Assumptions

- Documentation-only row; churn 13 commits/30d per the Plan Affected areas: rebase immediately
  before editing.

## Design decisions

- N/A: mechanical rename fixed by REQ-005; flow-arrow formatting preserved byte-identically
  except the key token.

## Alternatives considered

- N/A.

## Implementation
### Target file

`docs/21_rag/rag_03_01_query_pipeline-overview.md`

### Procedure

1. Rename the key in the L36 flow line to `rag_query_service_url` (new).

### Method

Single-token rename inside the flow line.

### Details

- N/A: grep verified exactly one standalone occurrence in this file.

## Compatibility considerations

- Docs only; `call_rag_service` named by the same line exists (check gate).

## Security considerations

- N/A: docs only.

## Rollback considerations

- N/A: revert the commit.

## Validation plan

- `uv run python tools/check_docs_quality.py`, `uv run python tools/check_docs_structure.py
  docs/21_rag/rag_03_01_query_pipeline-overview.md`,
  `uv run python tools/check_docs_content_policy.py`,
  `uv run python tools/check_docs_consistency.py --domain rag` — all clean.

## Completion criteria

- AC-5: zero standalone old-spelling mentions on this page.

## Out of Scope

- All other doc pages (own procedure documents).

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
- **Related target files**: docs/21_rag/rag_03_01_query_pipeline-overview.md
