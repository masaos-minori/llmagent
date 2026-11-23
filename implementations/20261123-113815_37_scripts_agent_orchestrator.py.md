## Goal

Construct the Agent recovery service from the configured MCP servers and hand its resolver to the `WorkflowEngine` the orchestrator builds.

## Scope
**Release unit**: N/A: not part of a release unit

In scope: the `WorkflowEngine(...)` construction block only. An injected `workflow_engine` argument still wins.

## Assumptions

- Verified: `Orchestrator` builds `WorkflowEngine(self._workflow_def, self._state_store, pending_timeout_minutes=..., tracer=...)` only when no engine is injected, and `ctx.cfg.mcp_servers` holds the `McpServerConfig` map.
- Verified: `ctx.runtime_tools` is an optional `RuntimeToolRegistry` with `resolve(tool_name)` returning the owning server key; it may not be set yet at construction, so the lookup is a lazy callable.

## Design decisions

- Pass `call_state_resolver=McpCallRecoveryService(cfg.mcp_servers, server_for_tool)` where `server_for_tool` returns `None` when `ctx.runtime_tools` is absent or the tool is unknown.

## Alternatives considered

Rejected: building the service in `factory.py` (it would still need the engine construction site changed here).

## Implementation
### Target file
`scripts/agent/orchestrator.py`

### Procedure
1. Import the service.
2. Define the lazy `server_for_tool` closure over `self._ctx`.
3. Pass the resolver to `WorkflowEngine(...)`.

### Method
Edit only the construction expression; no change to the injected-engine path.

### Details
- Construction must not perform network I/O; the service connects lazily.

## Compatibility considerations

With no `control_auth_token` configured the resolver returns `None` for every row and behavior equals today's.

## Security considerations

The service reads only configuration already loaded; secrets are registered by the config builder.

## Rollback considerations

N/A: revert the commit.

## Validation plan

- `uv run pytest tests/agent/test_mcp_call_recovery.py tests/agent/test_orchestrator.py`

## Completion criteria

- The orchestrator-built engine carries the resolver and the injected-engine path is unchanged.

## Out of Scope

Service logic (row 11) and engine plumbing (rows 13, 47).

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
- **Related target files**: `scripts/agent/orchestrator.py`
