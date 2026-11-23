## Goal

Add the Agent recovery service: for a stale dispatched call, ask the owning server's control API for the call state, map it through the shared table, and report the mapped state and result class without ever re-executing a handler.

## Scope
**Release unit**: N/A: not part of a release unit

In scope: the new module. `tool_runner.py` stays untouched (mcpdl001 AC-6: post-send failures stay `dispatched` there). Only read calls are made by the resolver path.

## Assumptions

- Verified: `ToolCallState` carries `tool` but no server key, so the service resolves it through an injected `server_for_tool` (new) callable (wired from `ctx.runtime_tools.resolve` in row 37).
- Verified: `classify_stale_pending` applies the resulting state with its own WHERE-guarded UPDATE, so the service returns the mapped state string and does not write to `tool_call_state` itself.

## Design decisions

- `McpCallRecoveryService(server_configs, server_for_tool, client_factory=ControlClient, timeout_sec=3.0, max_lookups=8)`; `resolve_state(row)` returns one of `AGENT_RECOVERY_STATES` or `None`.
- `resolve(row)` returns a frozen `RecoveryResolution` (new) (`agent_state`, `result_class`, `external_ref`, `error_code`) for callers that need the result class; secure reference or preview facts come from the control payload only.
- Unknown server, empty `control_auth_token`, control failure, `unknown_key`, or an out-of-vocabulary payload gives `None` (row stays `outcome_unknown`); at most `max_lookups` (new) control calls run per instance pass so turn entry stays bounded.
- `reconcile(row)` calls `request_reconcile` (new) for an operator-triggered path; the resolver never calls it.

## Alternatives considered

Rejected: finalizing through `ToolCallRecorder.finalize_tool_call` from the service (the engine path already holds the guarded UPDATE; a second writer would race it).

## Implementation
### Target file
`scripts/agent/mcp_call_recovery.py` (new)

### Procedure
1. Create the module with `RecoveryResolution` (new) and the service class.
2. Validate every payload field against the contract vocabularies before using it; discard anything else.
3. Add the lookup bound and log only server key, call-id prefix, and fixed labels.

### Method
Build one `ControlClient` per server key lazily from `McpServerConfig.url` and `control_auth_token`; call `get_call_state(row.idempotency_key)`; map `payload['agent_state']` after checking it against the vocabulary and that it agrees with `agent_state_for(ledger_status, lease_live)`.

### Details
- No code path in this module imports or calls a tool handler or `HttpTransport.call`.
- A `completed` mapping returns the result class; `replay_unavailable` is reported as is and never triggers re-execution.

## Compatibility considerations

New module, inert until rows 12, 13, and 37 consult it.

## Security considerations

Only structured control evidence is read; the control token is used only through `ControlClient`; nothing is logged beyond fixed labels.

## Rollback considerations

N/A: revert the commit.

## Validation plan

- `uv run pytest tests/agent/test_mcp_call_recovery.py`
- `uv run mypy scripts/` and `uv run lint-imports`

## Completion criteria

- The service maps completed, in_progress, reconciliation_required, failed, and unknown states correctly, degrades to `None` on any control problem, and never re-executes a handler.

## Out of Scope

Stale classification (row 12), engine and orchestrator wiring (rows 13, 37, 47), and per-tool reconcilers.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |

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
- **Requirement ID**: `REQ-005` (ledger-state to Agent-state mapping and Agent recovery)
- **Source issue**: issues/20261120-115843_mcpdl004_call-state-control-api.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261123-090353_mcpdl004_call-state-control-api.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261123-113815
- **Related target files**: `scripts/agent/mcp_call_recovery.py`
