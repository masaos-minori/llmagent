# Harden MCP server availability, discovery, and startup publication

## Priority
High

## Summary
The agent's startup path currently risks publishing a partially valid runtime tool registry — disabled servers may still be discoverable/routable, a fatal discovery finding may not halt startup, and required-tool schema validation is not guaranteed complete before the registry is published — so this issue defines one startup state machine that validates server eligibility, discovery results, required-tool schemas, and policy before publishing an atomic, safe-to-expose registry.

## Background
N/A: covered by Summary — this is a direct code-level finding across the MCP startup/discovery/registry path, not derived from a prior design decision document.

## Problem
`StartupMode.NONE` (disabled) servers are not confirmed excluded from `/v1/tools` discovery or from `RuntimeToolRegistry`/LLM-facing tool definitions, and a lower-level `invoke()` API may allow bypassing the startup-mode check. A `FATAL` startup finding is not guaranteed to convert into a startup failure before the agent begins accepting requests, and malformed required-server tool entries may not be treated as fatal. The registry may also be built and published without atomicity, risking a reader observing a partially-initialized state.

## Reason for Change
Disabled-server exclusion, fatal discovery handling, required-tool validation, and policy-before-publication are parts of one startup state machine. Implementing them separately could publish a partially valid registry, expose disabled tools, or allow the agent to accept work after a fatal discovery result.

## Implementation Intent
Build and publish a runtime tool registry only after server eligibility, discovery results, required-tool schemas, fatal findings, and active policy have been validated successfully. The agent must remain unavailable until the complete registry is safe to expose. Coordinate with `mcpagent08` (duplicate-tool ownership) since duplicate detection is one of this issue's own fatal-finding sources.

## Target Files or Areas
- `scripts/shared/mcp_config.py`
- `scripts/agent/services/mcp_tool_discovery.py`
- `scripts/shared/tool_transport_invoker.py`
- `scripts/shared/tool_executor.py`
- `tests/shared/test_tool_executor.py`
- `tests/agent/services/test_mcp_tool_discovery.py`
- `scripts/agent/startup.py` and related `scripts/agent/startup_*.py` files (Unknown: source review cited a `scripts/agent/startup/` directory, which does not exist — the startup logic is instead a flat set of `scripts/agent/startup_*.py` modules; confirm the exact file(s) to modify before implementation)
- `scripts/agent/context.py`
- `tests/agent/test_startup.py` (Unknown: source review cited `tests/test_agent_startup.py`, which does not exist anywhere under `tests/`; `tests/agent/test_startup.py` is the closest candidate among several `tests/agent/test_startup_*.py` files — confirm exact target(s) before implementation)
- `scripts/shared/runtime_tool_registry.py`

## Required Changes
- Exclude `StartupMode.NONE` servers from `/v1/tools` discovery.
- Do not create transports for disabled servers.
- Exclude disabled-server tools from `RuntimeToolRegistry` and LLM-facing tool definitions.
- Move the startup-mode check to the shared invocation boundary or make the lower-level `invoke()` API non-public.
- Define whether disabled servers participate in drift diagnostics without becoming routable.
- Add mode-matrix tests for `NONE`, `PERSISTENT`, and `SUBPROCESS`.
- Convert every `FATAL` startup finding into a startup failure before the agent begins accepting requests.
- Treat malformed required-server tool entries as fatal, or enforce strict tool-definition validation in production.
- Verify that every required tool is discovered and has a valid schema.
- Keep optional-server failures as warnings only when degraded operation is explicitly supported.
- Add startup tests for duplicate tools, unreachable required servers, malformed required tools, and optional-server degradation.
- Define the startup order as discovery, validation, policy application, executor wiring, LLM-definition publication, and request acceptance.
- Build the final registry off-path and publish it atomically.
- Prevent tool execution while registry initialization is incomplete.
- Prevent LLM-facing tool-definition generation from using an unfiltered registry.
- Add startup-order and concurrent-access regression tests.

## Constraints
N/A: none stated in source review.

## Acceptance Criteria
- No network request is sent to a disabled server during discovery or tool execution.
- No disabled-server tool appears in routing or LLM-facing definitions.
- Both name-based execution and any server-key invocation path reject disabled servers.
- Diagnostics can report disabled servers without making them executable.
- The process does not enter the ready state when any fatal finding exists.
- Duplicate tool ownership always prevents startup.
- A required server with an invalid or missing required tool prevents startup.
- Optional-server degradation is reported without exposing unavailable tools.
- No request can execute a tool before policy application completes.
- No disallowed tool is exposed to the LLM during startup or reload.
- Fatal discovery findings prevent registry publication.
- Registry replacement is atomic for readers.

## Testing Expectations
Add or update automated tests for every modified behavior and failure path (see Acceptance Criteria and Required Changes' test items). Run unit tests, integration tests, static analysis, and type checks.

## Documentation Impact
Update ADRs and the active known-issue inventory only after executable verification is available — do not update ahead of the code/test change.

## Out of Scope
- Unrelated refactoring outside the design and implementation boundary described in this issue.

## Dependencies
Coordinates with `mcpagent08` (duplicate-tool ownership detection, one of this issue's fatal-finding sources) and `mcpagent05` (MCP lifecycle/invocation gate unification, which shares the same invocation boundary this issue's startup-mode check moves to) — implement in either order but reconcile the shared invocation-gate logic if both change it.

## Unresolved Questions
Exact file(s) under `scripts/agent/startup_*.py` and the exact test file among `tests/agent/test_startup*.py` that correspond to the source review's `scripts/agent/startup/` and `tests/test_agent_startup.py` references — confirm during implementation rather than guessing. Non-blocking.

## AI Implementation Instruction
Keep changes scoped to the startup/discovery/registry-publication path; do not rewrite unrelated MCP server business logic. Confirm the exact startup and test file targets (see Unresolved Questions) before editing rather than guessing. Verify that logs and tool results do not expose credentials, payloads, raw response bodies, or sensitive configuration. Coordinate with `mcpagent05`/`mcpagent08` if implemented in the same session to avoid duplicating the invocation-gate or duplicate-detection logic.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20260914-103015
- **Related target files**: scripts/shared/mcp_config.py, scripts/agent/services/mcp_tool_discovery.py, scripts/shared/tool_transport_invoker.py, scripts/shared/tool_executor.py, tests/shared/test_tool_executor.py, tests/agent/services/test_mcp_tool_discovery.py, scripts/agent/startup.py, scripts/agent/context.py, tests/agent/test_startup.py, scripts/shared/runtime_tool_registry.py
