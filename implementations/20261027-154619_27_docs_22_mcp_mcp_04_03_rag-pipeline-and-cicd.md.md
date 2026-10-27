# Implementation Procedure: Rename the anti-loop key in the rag-pipeline MCP server page (mcp_04_03)

## Goal

Rename the single key occurrence in the RAG-pipeline MCP page's anti-loop note so the MCP docs
name the renamed key (REQ-005, AC-5).

## Scope

- One occurrence (verified 2026-10-27): "To prevent HTTP loops, `rag_service_url = \"\"` is
  fixed in `build_rag_cfg_adapter()`" at L41.
- No other part of the page changes.

## Assumptions

- Documentation-only row; churn 16 commits/30d (Plan Risks high-churn list): rebase immediately
  before editing.

## Design decisions

- N/A: mechanical rename fixed by REQ-005.

## Alternatives considered

- N/A.

## Implementation
### Target file

`docs/22_mcp/mcp_04_03_rag-pipeline-and-cicd.md`

### Procedure

1. Rename the key at L41 (verified) to `rag_query_service_url` (new); the `= ""` notation and
   the `build_rag_cfg_adapter()` reference stay unchanged.

### Method

Single-token rename.

### Details

- N/A: grep verified exactly one standalone occurrence in this file.

## Compatibility considerations

- Docs only; `build_rag_cfg_adapter` exists in `scripts/mcp_servers/rag_pipeline/rag_pipeline_models.py`
  (consistency check gate).

## Security considerations

- N/A: docs only.

## Rollback considerations

- N/A: revert the commit.

## Validation plan

- `uv run python tools/check_docs_quality.py`, `uv run python tools/check_docs_structure.py
  docs/22_mcp/mcp_04_03_rag-pipeline-and-cicd.md`,
  `uv run python tools/check_docs_content_policy.py`,
  `uv run python tools/check_docs_consistency.py --domain mcp` — all clean.

## Completion criteria

- AC-5: zero standalone old-spelling mentions on this page.

## Out of Scope

- All other doc pages (own procedure documents).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | Phase 4 row; land after Phase 2-3 rows |
| 2 | Run the documentation checkers (`routing.md` Tools: docs quality/structure/content-policy/consistency --domain mcp) | Pending | — | — | |

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
- **Related target files**: docs/22_mcp/mcp_04_03_rag-pipeline-and-cicd.md
