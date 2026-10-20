## Goal

Document that `rag-pipeline-mcp` `/health` reports a third dependency state for
`embed_url`: a configured-but-unreachable embedding service is reported as
`"unreachable"` (HTTP 503, `ready:false`, `liveness:true`), distinct from the
existing `"not configured"` (key absent/non-string) state. This keeps the
catalog entry accurate after the code change in `rag_pipeline_server.py`
(REQ-004, REQ-005).

## Scope

Documentation only. Update `docs/22_mcp/mcp_04_03_rag-pipeline-and-cicd.md`
(the rag-pipeline-mcp catalog entry) to reflect the new `"unreachable"` state.
No source, test, or config change in this document.

## Assumptions

- The code change adds `"unreachable"` to `dependencies.embed_url` when the
  reachability probe fails while `embed_url` is configured (see
  `rag_pipeline_server.py`, seq 01).
- `"not configured"` remains the value when `embed_url` is absent or non-string.

## Design decisions

- Keep the existing two-state sentence structure and insert the third state
  inline, so the entry stays consistent with the other servers' one-line health
  descriptions in the same catalog.

## Alternatives considered

- A separate paragraph for the probe behavior. Rejected: the catalog uses one
  compact bullet per server; a separate paragraph would break that pattern.

## Implementation

### Target file

`docs/22_mcp/mcp_04_03_rag-pipeline-and-cicd.md`

### Procedure

1. In the `rag-pipeline-mcp` > Operations bullet, extend the `/health` line to
   list the three states.
2. Leave the cicd-mcp section untouched.

### Method

Current line (rag-pipeline-mcp Operations):

- `/health`: `dependencies.embed_url` is `"not configured"` or `dependencies.config` is `"check failed"` (degraded, HTTP 503); otherwise `ok`.

Replace with:

- `/health`: `dependencies.embed_url` is `"not configured"` (embedding URL unset), `"unreachable"` (embedding URL configured but the reachability probe fails), or `dependencies.config` is `"check failed"` (degraded, HTTP 503); otherwise `ok`.

### Details

- The `"unreachable"` value is produced by the bounded probe in
  `rag_pipeline_health_probe.py` (seq 02) called from `_check_health_deps`
  (seq 01). It carries the same HTTP 503 / `ready:false` / `liveness:true` shape
  as the other degraded states, so no response-shape distinction is needed here.
- Do not change the cicd-mcp `/health` bullet or any other server's entry.

## Compatibility considerations

N/A: documentation-only update. The prose matches the shipped behavior where a
configured-but-unreachable `embed_url` yields HTTP 503.

## Security considerations

N/A.

## Rollback considerations

N/A: revert the commit.

## Validation plan

- Read `docs/22_mcp/mcp_04_03_rag-pipeline-and-cicd.md` and confirm the
  rag-pipeline-mcp `/health` bullet lists all three states and still distinguishes
  `"not configured"` from `"unreachable"`.
- Confirm the cicd-mcp section and other servers' entries are unchanged.

## Completion criteria

- The rag-pipeline-mcp `/health` bullet names `"not configured"`, `"unreachable"`,
  and `"check failed"` and maps each to its condition.

## Out of Scope

- Any source, test, or config change.
- Other MCP server catalog entries.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Update the rag-pipeline-mcp `/health` bullet to include the `"unreachable"` state | Pending | — | — | REQ-004, REQ-005 |
| 2 | Add or update tests per Validation plan | Pending | — | — | N/A: docs-only |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | REQ-004, REQ-005 |

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
- **Related target files**: docs/22_mcp/mcp_04_03_rag-pipeline-and-cicd.md
