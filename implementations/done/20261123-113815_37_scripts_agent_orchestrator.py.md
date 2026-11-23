## Goal

Construct the Agent recovery service from the configured MCP servers and hand its resolver to the `WorkflowEngine` the orchestrator builds.

## Scope
**Release unit**: N/A: not part of a release unit

In scope: the `WorkflowEngine(...)` construction block only. An injected `workflow_engine` argument still wins.

## Assumptions

- Corrected by verification: `AgentContext` has no `runtime_tools` attribute; the registry is reached through `ctx.services.runtime_tools`, and `services` may be None before `build_agent_context()` completes. The lazy lookup answers `None` in that case.
- Corrected by verification: `AgentConfig` holds the map as `ctx.cfg.mcp.mcp_servers` (`MCPConfig`), not `ctx.cfg.mcp_servers`. The construction reads it through that path.
- Verified: `Orchestrator` builds `WorkflowEngine(self._workflow_def, self._state_store, pending_timeout_minutes=..., tracer=...)` only when no engine is injected.

## Design decisions

- Pass `call_state_resolver=McpCallRecoveryService(self._ctx.cfg.mcp.mcp_servers, server_for_tool)` where `server_for_tool` returns `None` when `self._ctx.services` or its `runtime_tools` is absent, or the tool is unknown.

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
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261123-152455 | 20261123-152455 | lazy server_for_tool closure reads self._ctx.services.runtime_tools and answers None when services are not wired; the service is built from self._ctx.cfg.mcp.mcp_servers and passed only in the non-injected path; construction performs no I/O |
| 2 | Add or update tests per Validation plan | Completed | 20261123-152455 | 20261123-152455 | tests/agent/test_orchestrator.py: new TestCallStateResolverWiring asserts the built engine carries the service, an injected engine still wins, and the lazy lookup answers None before services are wired |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261123-152455 | 20261123-152455 | ruff, mypy, lint-imports, bandit pass; tests/agent/test_orchestrator.py green |

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
