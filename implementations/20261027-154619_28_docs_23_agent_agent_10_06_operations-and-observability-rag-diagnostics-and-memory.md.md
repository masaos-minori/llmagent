# Implementation Procedure: Rename the diagnostics key mention in the agent RAG diagnostics page (agent_10_06)

## Goal

Rename the single key occurrence in the agent operations page's stage-diagnostics paragraph so
the agent docs name the renamed key (REQ-005, AC-5).

## Scope

- One occurrence (verified 2026-10-27): "HttpAugment (present when `rag_service_url` is
  configured) ..." at L48.
- No other part of the page changes.

## Assumptions

- Documentation-only row; churn 12 commits/30d per the Plan Affected areas.

## Design decisions

- N/A: mechanical rename fixed by REQ-005.

## Alternatives considered

- N/A.

## Implementation
### Target file

`docs/23_agent/agent_10_06_operations-and-observability-rag-diagnostics-and-memory.md`

### Procedure

1. Rename the key at L48 (verified) to `rag_query_service_url` (new); the `HttpAugment`,
   `Refiner`, `last_stage_results`, and `http_result_kind` text stays byte-identical.

### Method

Single-token rename.

### Details

- N/A: grep verified exactly one standalone occurrence in this file.

## Compatibility considerations

- Docs only; `HttpAugment` and the diagnostics symbols named by the line all exist in
  `scripts/` (consistency check gate).

## Security considerations

- N/A: docs only.

## Rollback considerations

- N/A: revert the commit.

## Validation plan

- `uv run python tools/check_docs_quality.py`, `uv run python tools/check_docs_structure.py
  docs/23_agent/agent_10_06_operations-and-observability-rag-diagnostics-and-memory.md`,
  `uv run python tools/check_docs_content_policy.py`,
  `uv run python tools/check_docs_consistency.py --domain agent` — all clean.

## Completion criteria

- AC-5: zero standalone old-spelling mentions on this page.

## Out of Scope

- All other doc pages (own procedure documents).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | Phase 4 row; land after Phase 2-3 rows |
| 2 | Run the documentation checkers (`routing.md` Tools: docs quality/structure/content-policy/consistency --domain agent) | Pending | — | — | |

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
- **Related target files**: docs/23_agent/agent_10_06_operations-and-observability-rag-diagnostics-and-memory.md
