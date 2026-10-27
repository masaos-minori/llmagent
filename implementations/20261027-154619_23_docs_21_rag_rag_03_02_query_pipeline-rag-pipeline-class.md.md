# Implementation Procedure: Rename the HTTP-mode section key in the RagPipeline class page (rag_03_02)

## Goal

Rename all three key occurrences in the query-pipeline class page so the HTTP-mode section
documents the renamed key (REQ-005, AC-5).

## Scope

- Three occurrences (verified 2026-10-27): the section heading `### HTTP Mode
  (`rag_service_url`)` at L36, the delegation paragraph at L38, and the anti-loop table row
  "The MCP adapter hardcodes `rag_service_url=""` ..." at L46.
- No other section of the page changes.

## Assumptions

- Documentation-only row; churn 15 commits/30d per the Plan Affected areas: rebase immediately
  before editing.

## Design decisions

- The section heading renames with the body (heading text is part of the page's key mentions).

## Alternatives considered

- N/A: mechanical rename fixed by REQ-005.

## Implementation
### Target file

`docs/21_rag/rag_03_02_query_pipeline-rag-pipeline-class.md`

### Procedure

1. Rename the key in the L36 heading to `rag_query_service_url` (new).
2. Rename the key in the L38 delegation paragraph; `call_rag_service()`, `rag_auth_token` and
   the rest of the sentence stay byte-identical.
3. Rename the key in the L46 table row; the hardcoded `=""` value notation stays.

### Method

Three single-token renames.

### Details

- N/A: grep verified exactly three standalone occurrences on these lines.

## Compatibility considerations

- Docs only; symbols named (`call_rag_service`, `rag_auth_token`, `scripts/rag/pipeline_service.py`)
  all exist (AC-5 check gate).

## Security considerations

- N/A: docs only.

## Rollback considerations

- N/A: revert the commit.

## Validation plan

- `uv run python tools/check_docs_quality.py`, `uv run python tools/check_docs_structure.py
  docs/21_rag/rag_03_02_query_pipeline-rag-pipeline-class.md`,
  `uv run python tools/check_docs_content_policy.py`,
  `uv run python tools/check_docs_consistency.py --domain rag` — all clean.
- `grep -n "rag_service_url" docs/21_rag/rag_03_02_query_pipeline-rag-pipeline-class.md | grep
  -v "rag_pipeline_service_url"` — nothing (AC-5 for this page).

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
- **Related target files**: docs/21_rag/rag_03_02_query_pipeline-rag-pipeline-class.md
