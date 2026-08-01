# Confirm RuntimeError impact scope on MCP server startup failure (docs/04_mcp_06_05)

## Priority
High

## Summary
`docs/04_mcp_06_05` does not state whether a `RuntimeError` raised during a single MCP server's startup failure crashes the entire Agent process, or only disables that specific server.

## Reason for Change
This directly affects incident-response expectations: if a single misconfigured MCP server can crash the whole Agent process, that is a materially different operational risk than if it is isolated to that server alone. This is currently undetermined from the document, a production-reliability-relevant gap.

## Implementation Intent
Trace the actual exception-propagation path in the startup code and document the confirmed scope, along with the apparent fail-safe design intent (or lack thereof).

## Target Files or Areas
`docs/04_mcp_06_05`

## Required Changes
- Trace the exception-propagation path for MCP server startup failures in the relevant startup/orchestration code.
- Document the confirmed behavior: does a single server's `RuntimeError` at startup crash the whole Agent process, or is it isolated/caught and only that server is disabled?
- State the apparent design intent behind whichever behavior is confirmed (e.g. "the process crashes on any MCP startup failure by design, to force operator attention" vs. "servers are isolated for resilience").

## Acceptance Criteria
The document states, as confirmed fact (with source references), the actual blast radius of an MCP server startup `RuntimeError`.

## Testing Expectations
Not required (documentation-only) unless a reproduction (deliberately breaking one server's startup config) is performed to confirm behavior, which would strengthen the finding if feasible.

## Documentation Impact
`docs/04_mcp_06_05` gains a confirmed statement of failure-isolation behavior.

## Out of Scope
Do not change the actual startup exception-handling behavior in this issue — documentation only, unless the investigation reveals an actual bug worth filing as a separate issue.

## AI Implementation Instruction
Trace actual code (and reproduce if feasible) rather than inferring from partial code reading — this is a production-reliability-relevant fact that should not be asserted without verification.

## Traceability
- Workflow phase: issue-creation
- Source: docs_review_mcp.md §6B (起動失敗時RuntimeErrorの影響範囲)
- Generated at: 2026-08-02
