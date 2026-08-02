# Resolve cicd-mcp workflow_allowlist 2-layer warning confusion and audit other servers (docs/04_mcp_05_01)

## Priority
Medium

## Summary
`docs/04_mcp_05_01_access-control-and-allowlists.md` describes 2 distinct warning mechanisms — the Agent layer's `repl_health.py` and cicd-mcp's own `service_guards.py` — as if they were a single, unified warning, when they are confirmed to be 2 separate warnings from 2 different layers.

## Reason for Change
An operator investigating an incident who doesn't realize these are 2 separate warnings (with potentially different trigger conditions and log destinations) could look in the wrong place, or miss that both layers need checking, delaying root-cause identification.

## Implementation Intent
Split the description into 2 clearly separate items, each stating its trigger condition and output destination. Additionally, check whether other MCP servers' documentation has a similar 2-layer-warning conflation.

## Target Files or Areas
`docs/04_mcp_05_01_access-control-and-allowlists.md`; potentially other `docs/04_mcp_*.md` files describing similar Agent-layer + MCP-server-layer warning pairs

## Required Changes
- Split the cicd-mcp workflow_allowlist warning description into 2 explicit items: the Agent-layer (`repl_health.py`) warning and cicd-mcp's own (`service_guards.py`) warning, each with its trigger condition and log/output destination.
- Check other MCP server documentation for a similar conflation of Agent-layer and MCP-server-layer warnings, and note any additional instances found for follow-up.

## Acceptance Criteria
The cicd-mcp section clearly distinguishes the 2 warning layers with separate trigger conditions and destinations; a check of other servers' documentation for the same pattern has been performed and findings recorded.

## Testing Expectations
Not required (documentation-only). Manually verify both warning mechanisms' trigger conditions via `repl_health.py` and cicd-mcp's `service_guards.py` before finalizing.

## Documentation Impact
`docs/04_mcp_05_01` corrected; potentially other files flagged for follow-up if the same conflation is found.

## Out of Scope
Do not fix any additional instances found during the audit directly in this issue — file them as separate, scoped follow-up issues instead.

## AI Implementation Instruction
Verify both warning mechanisms independently via source before splitting the description — do not assume they are identical in trigger condition just because they warn about a related topic.

## Traceability
- Workflow phase: issue-creation
- Source: docs_review_mcp.md §6A (cicd-mcp workflow_allowlist警告の2レイヤー混同)
- Generated at: 2026-08-02
