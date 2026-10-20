## Goal

Document that the generic `/health` dependency-value model now includes a fourth
degraded value, `"unreachable"`, used by `rag-pipeline-mcp` for a configured-but
unreachable embedding endpoint. Clarify that it is distinct from `"not
configured"` and carries the same degraded response shape (HTTP 503, `ready:false`,
`liveness:true`). This keeps the protocol/health reference accurate after the code
change (REQ-004, REQ-005).

## Scope

Documentation only. Update `docs/22_mcp/mcp_02_02_startup-modes-and-health.md`
in two places:

- The **Dependency Values** paragraph (the list of degraded values).
- The **Server-Specific Health Response Fields** table row for `rag-pipeline-mcp`.

No source, test, or config change in this document.

## Assumptions

- `rag-pipeline-mcp` adds `"unreachable"` to `dependencies.embed_url` when the
  reachability probe fails while `embed_url` is configured (see
  `rag_pipeline_server.py`, seq 01; `rag_pipeline_health_probe.py`, seq 02).
- `"not configured"` remains the value when `embed_url` is absent or non-string.

## Design decisions

- Extend the existing "any non-empty value is degraded" rule by naming
  `"unreachable"` alongside the existing examples; do not introduce a new section,
  since the value participates in the same degraded-response contract as the others.

## Alternatives considered

- A dedicated subsection for the probe-derived state. Rejected: the value obeys the
  same degraded contract as the other dependency values, so it belongs in the
  shared Dependency Values description rather than a server-specific aside.

## Implementation

### Target file

`docs/22_mcp/mcp_02_02_startup-modes-and-health.md`

### Procedure

1. In the **Dependency Values** paragraph, add `"unreachable"` to the example list
   and note that it means "configured but not reachable".
2. In the **Server-Specific Health Response Fields** table, expand the
   `rag-pipeline-mcp` row to mention the unreachable probe.

### Method

Current Dependency Values paragraph:

> **Dependency Values**: Any non-empty dependency value (`"not configured"`, `"not_set"`, `"check failed"`, etc.) constitutes a degraded state — a server is not healthy until all dependencies are satisfied. These values are not just informational; they always indicate an actual missing or failed dependency.

Replace with:

> **Dependency Values**: Any non-empty dependency value (`"not configured"`, `"unreachable"`, `"not_set"`, `"check failed"`, etc.) constitutes a degraded state — a server is not healthy until all dependencies are satisfied. These values are not just informational; they always indicate an actual missing or failed dependency. `"unreachable"` (used by `rag-pipeline-mcp` for `dependencies.embed_url`) means the endpoint is configured but the reachability probe could not confirm it; it carries the same degraded response shape (HTTP 503, `ready:false`, `liveness:true`) as the other values.

Current table row:

| rag-pipeline-mcp | `dependencies` for an unconfigured embedding endpoint or a failed config check |

Replace with:

| rag-pipeline-mcp | `dependencies.embed_url` is `"not configured"` (embedding URL unset), `"unreachable"` (embedding URL configured but the reachability probe fails), or `dependencies.config` is `"check failed"` (failed config check) |

### Details

- The `"unreachable"` value is produced by the bounded probe in
  `rag_pipeline_health_probe.py` (seq 02) called from `_check_health_deps`
  (seq 01). It does not set `liveness:false`; the process is live, so the shared
  `is_degraded_but_live` treatment (HTTP 503 + `liveness:true`) still applies.
- Do not alter any other server's table row or the HTTP status-code table.

## Compatibility considerations

N/A: documentation-only update. The prose matches the shipped behavior where a
configured-but-unreachable `embed_url` yields HTTP 503.

## Security considerations

N/A.

## Rollback considerations

N/A: revert the commit.

## Validation plan

- Read `docs/22_mcp/mcp_02_02_startup-modes-and-health.md` and confirm both edits
  are present and that `"unreachable"` is distinguished from `"not configured"`.
- Confirm no other server's health description changed.

## Completion criteria

- The Dependency Values paragraph names `"unreachable"` and its meaning.
- The `rag-pipeline-mcp` table row lists `"not configured"`, `"unreachable"`, and
  `"check failed"`.

## Out of Scope

- Any source, test, or config change.
- Other MCP server health descriptions.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add `"unreachable"` to the Dependency Values paragraph and the rag-pipeline-mcp table row | Completed | 20261020-182414 | 20261020-182414 | REQ-004, REQ-005 changed: docs/22_mcp/mcp_02_02_startup-modes-and-health.md |
| 2 | Add or update tests per Validation plan | Completed | 20261020-182414 | 20261020-182414 | N/A: docs-only N/A: docs-only |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261020-182414 | 20261020-182414 | docs checkers pass; full suite not re-run: no code change since the last green run |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20261020-182414 | 20261020-182414 | REQ-004, REQ-005 REQ-004, REQ-005 |

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
- **Related target files**: docs/22_mcp/mcp_02_02_startup-modes-and-health.md