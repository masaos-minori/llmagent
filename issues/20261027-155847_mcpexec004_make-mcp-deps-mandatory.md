# Make the MCP runtime registry and health registry mandatory and normalize routing failures

## Priority
Medium

## Summary
Remove the optional post-construction wiring of the MCP execution path (runtime registry and health registry settable to `None`), make the posture allowlist an explicit required input of registry construction, and expose one documented error contract for routing failures. The Health re-export and the `posture_gates=None` default are handled by an existing issue and are out of scope here.

## Background
Source: `memo-issue.md` Issue 04, re-verified against current source on 2026-10-27. The Health type re-export and the optional `posture_gates` default of `McpToolDiscoveryService` are already filed as `issues/done/20261027-104222_mcpcompat001_remove-mcp-compat-paths.md` (plan: `plans/20261027-115908_mcpcompat001_remove-mcp-compat-paths.md`). This issue covers the remainder.

- `scripts/agent/services/mcp_tool_discovery_registry.py`: the registry builder takes `allowed_servers: frozenset[str] | None = None`; its docstring states that `None` registers every tool without posture filtering. `Explicit in code`.
- `scripts/shared/route_resolver.py`: `set_runtime_registry(registry: RuntimeToolRegistry | None)` accepts `None`; an unresolved tool raises `ValueError` (`Unknown tool: ...`) and its module docstring states the resolver modes differ only in error-message wording. `Explicit in code`.
- `scripts/shared/tool_transport_invoker.py`: `set_health_registry(registry: McpServerHealthRegistry | None)` accepts `None`. `Explicit in code`.
- `scripts/shared/tool_executor.py`: `set_runtime_registry()` is called later from `scripts/agent/startup_validation.py`; `scripts/agent/factory.py` calls `tools.set_health_registry(registry)`. `Explicit in code`.
- Whether `ToolExecutor.execute()` converts a resolver `ValueError` into a `ToolCallResult` or lets it propagate: `Needs confirmation` (execute body not read in this verification).

## Problem
Correctness of the MCP stack depends on call order: between construction and the later setter calls the executor is usable without a runtime registry or health tracking, and passing `None` silently disables posture filtering or dynamic health gating. Routing failures may surface as exceptions while transport and health failures return `ToolCallResult`.

## Reason for Change
The optional states exist only as a leftover of staged wiring. They make security-relevant gating a matter of startup order. Production currently wires them correctly (mcpcompat001 notes the production caller passes real gates), so severity is Medium (ambiguous contract, no demonstrated bypass).

## Implementation Intent
An executable stack must be fully initialized: construct the executor with its registries (or fail fast when a call arrives before wiring is complete), reject `None` in production paths, and make the routing-failure result one documented contract that distinguishes registry-not-ready, unknown tool, posture-excluded and dynamically unavailable. Keep an empty allowlist as fail-closed (register nothing).

## Target Files or Areas
- `scripts/agent/services/mcp_tool_discovery_registry.py`
- `scripts/shared/route_resolver.py`
- `scripts/shared/tool_executor.py`
- `scripts/shared/tool_transport_invoker.py`
- `scripts/agent/factory.py`, `scripts/agent/startup_validation.py`
- MCP routing, executor and health tests under `tests/`
- `docs/10_adr/` ADR-003 and ADR-004 and MCP docs under `docs/22_mcp/` (only where they describe optional wiring)

## Required Changes
- Make the posture allowlist a required argument of registry construction while keeping the empty set fail-closed (coordinate with mcpcompat001 for the discovery-service side).
- Reject `None` for the runtime registry and the health registry in production wiring, or restrict `None` to an explicit test-only construction path.
- Convert routing failures (registry not ready, unknown tool, posture-excluded, unavailable) to a normalized `ToolCallResult`, if they currently propagate as exceptions.
- Remove or redesign resolver modes whose only difference is error-message wording.
- Update ADR and MCP docs that describe the staged wiring or the live-discovery routing source.

## Constraints
- Preserve dynamic `UNAVAILABLE` and `HALF_OPEN` handling, including release of a cancelled HALF_OPEN trial.
- Do not change the public tool-call result fields beyond adding documented error kinds.
- ADR edits must pass `tools/check_adr_preservation.py`.

## Acceptance Criteria
- No production path can execute a tool without a runtime registry, posture allowlist and health registry.
- A tool call before registry initialization returns a defined error result.
- Unknown and posture-excluded tools return normalized `ToolCallResult` values and cannot execute.
- An empty allowlist registers no tools.

## Testing Expectations
- Unit tests for each routing failure kind and for the not-ready state.
- Regression tests for `UNAVAILABLE`, `HALF_OPEN` and cancelled HALF_OPEN trials.
- `uv run pytest` for MCP discovery, registry, routing, health and executor tests; mypy, ruff, `PYTHONPATH=scripts uv run lint-imports`.

## Documentation Impact
Yes. Describe the mandatory wiring order and the routing error contract in the MCP/ADR docs; remove text that presents optional wiring as current behavior.

## Out of Scope
- The Health type re-export and `posture_gates=None` removal (mcpcompat001).
- Legacy `resource_scope` handling (mcpcompat003).
- Per-server concurrency defaults (mcpinv004) and the dead startup-mode guard (mcpinv002).

## Dependencies
- Depends on `plans/20261027-115908_mcpcompat001_remove-mcp-compat-paths.md`: implement mcpcompat001 first so the discovery-side `posture_gates` requirement is not duplicated.
- Same-file overlap with `plans/20261027-103047_mcpinv002_remove-dead-check-startup-mode-guard.md` and `plans/20261027-104612_mcpinv004_unbounded-per-server-concurrency-default.md` (both touch `scripts/shared/tool_executor.py`); implement after them or rebase carefully.

## Unresolved Questions
- Does `ToolExecutor.execute()` already normalize resolver `ValueError` into `ToolCallResult`? `Needs confirmation`.
- Are there test or fixture callers that rely on `set_runtime_registry(None)` or `set_health_registry(None)`? `Needs confirmation` (search `tests/` before removing).

## AI Implementation Instruction
Keep the change limited to wiring and the error contract. Do not touch the files and behaviors listed under Out of Scope. Search all callers before making an argument required, and stop and report if a caller needs a different design.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261027-155847
- **Related target files**: `scripts/agent/services/mcp_tool_discovery_registry.py`, `scripts/shared/route_resolver.py`, `scripts/shared/tool_executor.py`, `scripts/shared/tool_transport_invoker.py`, `scripts/agent/factory.py`, `scripts/agent/startup_validation.py`, `docs/22_mcp/`
