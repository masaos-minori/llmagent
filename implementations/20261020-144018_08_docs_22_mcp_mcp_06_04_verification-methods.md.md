## Goal

Document how to verify the new `rag-pipeline-mcp` `/health` `"unreachable"` state
via the existing verification methods (HTTP probe, `/v1/tools`, Agent REPL). Keep
the Verification Methods reference accurate after the code change (REQ-004,
REQ-005).

## Scope

Documentation only. Update `docs/22_mcp/mcp_06_04_verification-methods.md`:

- The **Health probes** base-response-shape line (note the new value).
- The **Degraded responses** section (add the unreachable example).

No source, test, or config change in this document.

## Assumptions

- `rag-pipeline-mcp` adds `"unreachable"` to `dependencies.embed_url` when the
  reachability probe fails while `embed_url` is configured (see
  `rag_pipeline_server.py`, seq 01; `rag_pipeline_health_probe.py`, seq 02).
- `"not configured"` remains the value when `embed_url` is absent or non-string.

## Design decisions

- Extend the shared base-response and degraded-response descriptions with the
  `"unreachable"` example; do not add a server-specific verification subsection,
  since the state is verified through the same HTTP probe as every other server.

## Alternatives considered

- A dedicated verification subsection for embed outages. Rejected: the state is
  verified by the standard `/health` probe like every other dependency failure, so
  it belongs in the shared Health probes / Degraded responses descriptions.

## Implementation

### Target file

`docs/22_mcp/mcp_06_04_verification-methods.md`

### Procedure

1. In the **Health probes** base-response-shape line, note that a configured-but
   unreachable `embed_url` appears as `"unreachable"` in `dependencies`.
2. In the **Degraded responses** section, add the `"unreachable"` example.

### Method

Current base-response-shape line:

> Base response shape: `{"status":"ok","ready":bool,"liveness":true,"restart_recommended":false,"operator_action_required":false,"dependencies":{},"details":{}}`. Server-specific unmet conditions appear in `dependencies` (for example `shell`, `github_token`, `embed_url`, `db_file`, `git`, `filesystem`) and server-specific state in `details`.

Replace with:

> Base response shape: `{"status":"ok","ready":bool,"liveness":true,"restart_recommended":false,"operator_action_required":false,"dependencies":{},"details":{}}`. Server-specific unmet conditions appear in `dependencies` (for example `shell`, `github_token`, `embed_url`, `db_file`, `git`, `filesystem`) and server-specific state in `details`. For `rag-pipeline-mcp`, `dependencies.embed_url` is `"not configured"` when no embedding URL is set, or `"unreachable"` when the URL is set but the embedding server cannot be reached.

Current Degraded responses paragraph:

> A degraded server returns HTTP 503 with `status="degraded"`, `ready=false`, and a server-specific unmet condition in `dependencies` (for example `{"shell": "sh not found in PATH"}` for shell-mcp). The mcp subcommand's `status` action reflects it in `health_reason` as `operator_action_required` (display only; no automatic restart occurs).

Replace with:

> A degraded server returns HTTP 503 with `status="degraded"`, `ready=false`, and a server-specific unmet condition in `dependencies` (for example `{"shell": "sh not found in PATH"}` for shell-mcp, or `{"embed_url": "unreachable"}` for rag-pipeline-mcp when the embedding URL is configured but unreachable). The mcp subcommand's `status` action reflects it in `health_reason` as `operator_action_required` (display only; no automatic restart occurs).

### Details

- The `"unreachable"` value carries `liveness:true` (process is live), so the
  standard HTTP 503 interpretation applies unchanged.
- Leave the `/v1/tools`, Agent REPL, and Standalone Launch sections untouched.

## Compatibility considerations

N/A: documentation-only update. The prose matches the shipped behavior where a
configured-but-unreachable `embed_url` yields HTTP 503.

## Security considerations

N/A.

## Rollback considerations

N/A: revert the commit.

## Validation plan

- Read the Health probes and Degraded responses sections and confirm both edits
  are present and that `"unreachable"` is distinguished from `"not configured"`.
- Confirm the `/v1/tools`, Agent REPL, and Standalone Launch sections are unchanged.

## Completion criteria

- The base-response-shape line names the `"unreachable"` `embed_url` value.
- The Degraded responses section includes the `{"embed_url": "unreachable"}` example.

## Out of Scope

- Any source, test, or config change.
- Other sections of this document.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add the `"unreachable"` value to the health-probe and degraded-response descriptions | Pending | — | — | REQ-004, REQ-005 |
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
- **Related target files**: docs/22_mcp/mcp_06_04_verification-methods.md
