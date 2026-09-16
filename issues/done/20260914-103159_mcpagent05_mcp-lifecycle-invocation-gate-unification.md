# Unify MCP lifecycle, server-state, and invocation gate behavior

## Priority
Medium

## Summary
Whether a tool call may proceed is currently decided by several independent checks spread across `ToolExecutor`, `ToolTransportInvoker`, configuration validation, and discovery (invocation APIs, startup modes, required-server behavior, failure policy, lifecycle exceptions, timeout semantics, missing configuration), risking contradictory gating between call paths; this issue defines one lifecycle matrix and one shared invocation gate chain applied consistently to every public tool execution path.

## Background
N/A: covered by Summary — this is a direct code-level finding across the MCP invocation/lifecycle path, not derived from a prior design decision document.

## Problem
More than one public invocation entry point may exist, and it is not confirmed that all of them route through the same disabled-state, health, lifecycle, transport, and concurrency checks in the same order. `LifecycleProtocol`'s permitted exceptions are not fully enumerated, so a lifecycle exception could propagate as an undocumented error rather than a normalized `ToolCallResult`. Required-field expectations differ across `NONE`, `PERSISTENT`, and `SUBPROCESS` startup modes without being explicit, and connection secrets may be required even for a fully disabled server. The meaning of a `0` value for call/health/startup timeout fields is not confirmed consistent between validation messages and actual behavior.

## Reason for Change
Invocation APIs, startup modes, required-server behavior, failure policy, lifecycle exceptions, timeout semantics, and missing server configuration all determine whether a call may proceed. Separate fixes would leave contradictory gates across `ToolExecutor`, `ToolTransportInvoker`, configuration validation, and discovery.

## Implementation Intent
Define one lifecycle matrix and one shared invocation gate chain for every public tool execution path. Disabled, unknown, unhealthy, unavailable, or unconfigured servers must be handled consistently.

## Target Files or Areas
- `scripts/shared/tool_lifecycle.py`
- `scripts/shared/tool_transport_invoker.py`
- `scripts/shared/tool_executor.py`
- `tests/shared/test_tool_executor.py`
- `scripts/shared/mcp_config.py`
- `scripts/agent/services/mcp_tool_discovery.py`
- `tests/shared/test_mcp_config.py`
- `tests/agent/services/test_mcp_tool_discovery.py`

## Required Changes
- Define one public execution entry point, or make all public paths call the same gate chain.
- Require a validated server configuration for every routed server key.
- Apply disabled-state, health, lifecycle, transport, and concurrency checks in the same order.
- Define the lifecycle exceptions permitted by `LifecycleProtocol`.
- Normalize cooldown, startup failure, OS failure, missing configuration, and missing transport into documented `ToolCallResult` errors.
- Add parity tests for all invocation APIs.
- Define required fields for `NONE`, `PERSISTENT`, and `SUBPROCESS` modes.
- Do not require connection secrets for a fully disabled server unless explicitly justified.
- Define `required` as startup criticality and `failure_policy` as a separate documented runtime behavior, or remove redundant fields.
- Specify whether zero means no timeout for call, health, and startup timeout fields.
- Correct validation messages to match the accepted numeric range.
- Add matrix tests for mode, required flag, failure policy, URL, command, token, and timeout combinations.

## Constraints
N/A: none stated in source review.

## Acceptance Criteria
- No public invocation path bypasses disabled-state or lifecycle checks.
- A routed server without validated configuration fails closed.
- Equivalent failures have the same error type and health-recording behavior across APIs.
- Lifecycle exceptions do not escape unexpectedly.
- Every valid mode has an explicit required-field set.
- Disabled servers do not require unused connection credentials.
- `required`, strict validation, and `failure_policy` have non-overlapping documented roles.
- Timeout value zero has one consistent meaning across code and documentation.

## Testing Expectations
Add or update automated tests for every modified behavior and failure path (see Acceptance Criteria and Required Changes' test items). Run unit tests, integration tests, static analysis, and type checks.

## Documentation Impact
Update ADRs and the active known-issue inventory only after executable verification is available.

## Out of Scope
- Unrelated refactoring outside the design and implementation boundary described in this issue.

## Dependencies
Shares `scripts/shared/tool_executor.py`/`tool_transport_invoker.py` with `mcpagent01` (startup publication) and `mcpagent04` (policy reload) — coordinate ordering so the shared invocation gate chain is defined once, not divergently across issues.

## Unresolved Questions
N/A: none.

## AI Implementation Instruction
Keep changes scoped to the invocation gate chain and lifecycle matrix; do not rewrite unrelated discovery or registry-publication logic beyond what one shared gate chain requires. If `mcpagent01` has already moved the startup-mode check to a shared boundary, extend that boundary here rather than creating a second one. Verify that logs and tool results do not expose credentials, payloads, raw response bodies, or sensitive configuration.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20260914-103159
- **Related target files**: scripts/shared/tool_lifecycle.py, scripts/shared/tool_transport_invoker.py, scripts/shared/tool_executor.py, tests/shared/test_tool_executor.py, scripts/shared/mcp_config.py, scripts/agent/services/mcp_tool_discovery.py, tests/shared/test_mcp_config.py, tests/agent/services/test_mcp_tool_discovery.py
