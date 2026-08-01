# Clarify shell-mcp sandbox enforcement responsibility (docs/04_mcp_04_02)

## Priority
High

## Summary
`docs/04_mcp_04_02_file-write-file-delete-shell.md` correctly documents that shell-mcp's sandbox is disabled by default (confirmed against code), but does not state that production-environment enforcement is actually performed by the Agent-side `repl_health.py`, not shell-mcp itself — leaving the responsibility boundary unclear.

## Reason for Change
This is a security-relevant responsibility boundary: an implementer who believes shell-mcp is responsible for its own sandbox enforcement might reasonably (but incorrectly) assume that running shell-mcp directly, without the Agent-side check, is safe in production — when in fact the enforcement lives in a different layer entirely.

## Implementation Intent
Add an explicit statement that production sandbox enforcement is performed by the Agent layer (`repl_health.py`), while shell-mcp itself simply follows its own configuration without enforcing a safe default.

## Target Files or Areas
`docs/04_mcp_04_02_file-write-file-delete-shell.md`

## Required Changes
- Add: "shell-mcp itself does not enforce sandboxing by default. Production-environment enforcement is performed by the Agent-side `repl_health.py`; shell-mcp only follows its own configuration (responsibility split: enforcement logic lives in the Agent layer, execution in the MCP server layer)."
- Verify this responsibility split against current `repl_health.py` and shell-mcp source before finalizing wording.

## Acceptance Criteria
The file explicitly states which layer (Agent vs. shell-mcp) is responsible for production sandbox enforcement.

## Testing Expectations
Not required (documentation-only). Manually verify via reading `scripts/agent/repl_health.py` (or equivalent) and shell-mcp's own sandbox-related code before finalizing.

## Documentation Impact
`docs/04_mcp_04_02` gains a security-relevant responsibility-boundary clarification.

## Out of Scope
Do not change the actual sandbox enforcement implementation in this issue — documentation only.

## AI Implementation Instruction
Verify the responsibility split directly against source before writing — this is security-relevant content and must not be asserted without confirmation.

## Traceability
- Workflow phase: issue-creation
- Source: docs_review_mcp.md §4 強化候補 (shell-mcpサンドボックス強制の責務所在)
- Generated at: 2026-08-02
