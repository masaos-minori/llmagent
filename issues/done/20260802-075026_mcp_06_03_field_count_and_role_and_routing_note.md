# Fix docs/04_mcp_06_03 agent.toml field count, confirm role-field usage, and add tool_names-not-routing-input clarification

## Priority
High

## Summary
`docs/04_mcp_06_03` states `[mcp_servers.*]` has "4 fields only," but the current config actually has 10 fields (including `tool_names`, `auth_token`, `role`, `call_timeout_sec`, `startup_timeout_sec`). Separately, this file is missing a fact present in `docs/04_mcp_03_01`: that `tool_names` is not used as a routing input (observation-only). The `role` field's actual usage is also unconfirmed — it exists in config but has zero reference sites found in code.

## Reason for Change
The field-count claim is a confirmed factual error; readers relying on this file would underestimate configurable options and could miss the `role` field entirely. The missing tool_names-routing clarification creates a cross-file inconsistency that could lead readers of this file specifically to a wrong routing-behavior assumption. The `role` field's undocumented, seemingly-unused status is a genuine open question that should be tracked rather than silently ignored.

## Implementation Intent
Replace the field-count claim with an accurate, complete field table (or explicitly state "showing only the primary fields" if intentional). Add the tool_names-not-routing-input fact for cross-file consistency. Investigate `role`'s actual usage and either document it or register it as a Needs Confirmation item.

## Target Files or Areas
`docs/04_mcp_06_03`

## Required Changes
- Replace "4 fields only" with an accurate table of all 10 current fields (or explicitly scope the claim if only listing "primary" fields is intentional).
- Add: "`tool_names` is not used as a routing input — it is observation/validation-only." (matching `04_mcp_03_01`'s existing statement).
- Investigate whether `role` is referenced anywhere in code; if genuinely unused, register a Needs Confirmation item asking whether it is a reserved-for-future field or a deprecated one, rather than silently describing it as if it has an active purpose.

## Acceptance Criteria
The field table matches the current `[mcp_servers.*]` schema (or explicitly scopes itself); the tool_names-not-routing-input fact is present; `role`'s usage status is either documented or explicitly tracked as Needs Confirmation.

## Testing Expectations
Not required (documentation-only). Manually verify the current field count/names via the `MCPServerConfig`-equivalent dataclass or config schema, and grep for `role` usage before finalizing.

## Documentation Impact
`docs/04_mcp_06_03` corrected and clarified.

## Out of Scope
Do not add or remove actual config fields in this issue — documentation only.

## AI Implementation Instruction
Verify the current field count directly against the config-loading code (not just this review's stated number of 10, in case it has changed again). Do not assert a purpose for `role` without confirming a reference site in code.

## Traceability
- Workflow phase: issue-creation
- Source: docs_review_mcp.md §1 (全体評価 item 6), §4 強化候補 (RuntimeToolRegistry区別, tool_names欠落), §6A (agent.tomlフィールド数), §6B (roleフィールドの用途)
- Generated at: 2026-08-02
