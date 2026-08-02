# Simplify startup/health-check command listing in docs/02_deployment-part1.md

## Priority
Low

## Summary
`docs/02_deployment-part1.md` §2.3 (~lines 133-140) lists verbatim startup commands and health-check curl commands, burying the design intent (why this order of startup verification) under command-line detail.

## Reason for Change
Verbatim command listings are runbook-level content that changes independently of design intent, and duplicating them here creates a second place to keep in sync.

## Implementation Intent
Move the verbatim commands to the operations runbook, keeping only the purpose/target of the health-check step in the main text.

## Target Files or Areas
`docs/02_deployment-part1.md` (§2.3, ~lines 133-140)

## Required Changes
- Replace the verbatim command listing with: "サービス起動後、embed-llm/agent-llmそれぞれについてヘルスチェックエンドポイントへの疎通を確認する。具体的なコマンド例は運用Runbookを参照。"
- Move the exact command examples to the operations runbook (identify or create the appropriate location).

## Acceptance Criteria
The section states the health-check purpose/target without verbatim commands; the commands themselves are relocated to the runbook.

## Testing Expectations
Not required (documentation-only).

## Documentation Impact
`docs/02_deployment-part1.md` shortened; operations runbook gains this content.

## Out of Scope
Do not change the actual startup/health-check procedure in this issue — documentation relocation only.

## AI Implementation Instruction
Identify the correct runbook destination before removing the command detail from this file, so the exact commands aren't lost.

## Traceability
- Workflow phase: issue-creation
- Source: docs_review_deployment.md §3 要約候補 item 2
- Generated at: 2026-08-02
