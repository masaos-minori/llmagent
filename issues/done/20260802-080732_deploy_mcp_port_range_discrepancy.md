# Confirm MCP port-range discrepancy: docs/02_deployment-part1.md "8004-8014" vs. setup_services.sh comment "8004-8016"

## Priority
Low

## Summary
`docs/02_deployment-part1.md` §2.3 states the MCP server port range is 8004-8014, matching the actual ports used in `config/agent.toml`'s MCP server sections. However, `deploy/setup_services.sh`'s comment states "8004-8016," which would include Event Bus and an apparently-unused port 8016.

## Reason for Change
An operator configuring firewall rules based on either source could open or restrict the wrong port range, depending on which they trust — this discrepancy should be resolved rather than left standing.

## Implementation Intent
Confirm with the document/script author whether the wider range in the script comment reflects a planned future expansion (intentionally inclusive) or is simply an outdated/incorrect comment, then align both sources to state the same range.

## Target Files or Areas
`docs/02_deployment-part1.md` (§2.3), `deploy/setup_services.sh` (comment)

## Required Changes
- Confirm with the author whether "8004-8016" in the script comment reflects intentional future-expansion headroom or is an error.
- Align both the documentation and the script comment to state the same, confirmed-correct port range (this review's own assessment leans toward the documentation's "8004-8014" being closer to actual reality, but confirm before changing the script comment).

## Acceptance Criteria
`docs/02_deployment-part1.md` and `deploy/setup_services.sh`'s comment state a consistent port range, with the discrepancy's cause (typo vs. intentional headroom) explicitly resolved.

## Testing Expectations
Not required (documentation-only, plus one script-comment change with no behavioral effect). Verify current port assignments via `config/agent.toml` before finalizing.

## Documentation Impact
`docs/02_deployment-part1.md` and `deploy/setup_services.sh`'s comment aligned.

## Out of Scope
Do not change any actual port assignments or `setup_services.sh`'s functional behavior in this issue — comment/documentation alignment only.

## AI Implementation Instruction
Do not assume which side is correct without confirmation — if the author's intent for the wider range can't be determined, register this as an explicit open Needs Confirmation item rather than picking one value.

## Traceability
- Workflow phase: issue-creation
- Source: docs_review_deployment.md §6 (通常の確認事項: MCPポート範囲の表記ゆれ)
- Generated at: 2026-08-02
