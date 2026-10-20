## Goal

Document that the `rag-pipeline-mcp` `/health` check reports a third
`embed_url` state: `"unreachable"` (embedding URL configured but the reachability
probe fails), distinct from `"not configured"` (URL unset). Keep the Prerequisites
health-check and troubleshooting prose accurate after the code change
(REQ-004, REQ-005).

## Scope

Documentation only. Update `docs/21_rag/rag_01_system_overview.md` in the
Prerequisites section:

- The "RAG pipeline MCP server health check" paragraph.
- The troubleshooting bullets under Troubleshooting.

No source, test, or config change in this document.

## Assumptions

- `rag-pipeline-mcp` adds `"unreachable"` to `dependencies.embed_url` when the
  reachability probe fails while `embed_url` is configured (see
  `rag_pipeline_server.py`, seq 01; `rag_pipeline_health_probe.py`, seq 02).
- `"not configured"` remains the value when `embed_url` is absent or non-string.

## Design decisions

- Extend the existing health-check sentence and add one troubleshooting bullet; do
  not restructure the Prerequisites section.

## Alternatives considered

- A new subsection for embed outages. Rejected: the state fits the existing
  "RAG pipeline MCP server health check" paragraph and troubleshooting list.

## Implementation

### Target file

`docs/21_rag/rag_01_system_overview.md`

### Procedure

1. In the "RAG pipeline MCP server health check" paragraph, add the
   `"unreachable"` state next to `"not configured"`.
2. Add a troubleshooting bullet for the `"unreachable"` case.

### Method

Current health-check paragraph:

> **RAG pipeline MCP server health check:** The `rag-pipeline-mcp` server answers `/health` with the common MCP health response, in which `liveness` is a boolean, `ready` is true only when no dependency check fails, and HTTP 503 is returned when it is not ready (`dependencies.embed_url` is `"not configured"` when no embedding URL is configured). For the response format see [mcp_02_02 Startup Modes and Health](../22_mcp/mcp_02_02_startup-modes-and-health.md) and [mcp_04_03](../22_mcp/mcp_04_03_rag-pipeline-and-cicd.md).

Replace the parenthetical with:

> ...and HTTP 503 is returned when it is not ready (`dependencies.embed_url` is `"not configured"` when no embedding URL is configured, or `"unreachable"` when the embedding URL is configured but the reachability probe cannot confirm it). For the response format see [mcp_02_02 Startup Modes and Health](../22_mcp/mcp_02_02_startup-modes-and-health.md) and [mcp_04_03](../22_mcp/mcp_04_03_rag-pipeline-and-cicd.md).

Current troubleshooting bullet:

- If the `rag-pipeline-mcp` `/health` reports `status` `"degraded"` with `dependencies.embed_url` `"not configured"`: verify the embedding server URL is set in the configuration

Add after it:

- If the `rag-pipeline-mcp` `/health` reports `status` `"degraded"` with `dependencies.embed_url` `"unreachable"`: the embedding server URL is set but the server is not reachable (down, wrong port, or network-blocked); verify the embedding server is running and reachable at the configured address. The `/health` probe is bounded by a timeout, so a hung server still returns within that bound.

### Details

- `"unreachable"` does not set `liveness:false`; the process is live, so HTTP 503
  with `liveness:true` is the expected body. Do not imply a crash or restart need.
- Leave the embedding-server (`embed-llm`) curl check and the sqlite-vec rows
  unchanged.

## Compatibility considerations

N/A: documentation-only update. The prose matches the shipped behavior where a
configured-but-unreachable `embed_url` yields HTTP 503.

## Security considerations

N/A.

## Rollback considerations

N/A: revert the commit.

## Validation plan

- Read the Prerequisites section and confirm both edits are present and that
  `"unreachable"` is distinguished from `"not configured"`.
- Confirm the embedding-server curl check and other prerequisite rows are unchanged.

## Completion criteria

- The health-check paragraph names `"not configured"` and `"unreachable"`.
- A troubleshooting bullet covers the `"unreachable"` case and its cause.

## Out of Scope

- Any source, test, or config change.
- Other sections of this document.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add the `"unreachable"` state to the health-check paragraph and a troubleshooting bullet | Completed | 20261020-182439 | 20261020-182439 | REQ-004, REQ-005 changed: docs/21_rag/rag_01_system_overview.md |
| 2 | Add or update tests per Validation plan | Completed | 20261020-182439 | 20261020-182439 | N/A: docs-only N/A: docs-only |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261020-182439 | 20261020-182439 | docs checkers pass; full suite not re-run: no code change since the last green run |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20261020-182439 | 20261020-182439 | REQ-004, REQ-005 REQ-004, REQ-005 |

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
- **Requirement ID**: REQ-004, REQ-005
- **Source issue**: issues/20261019-214637_ragobs003_rag_pipeline_health_misses_embed_outage.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261020-132416_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261020-144018
- **Related target files**: docs/21_rag/rag_01_system_overview.md