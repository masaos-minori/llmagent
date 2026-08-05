# Reduce implementation-derived detail in docs/05_agent_03_*_turn-processing-flow*.md

## Priority
Medium

## Summary
Apply the design-doc reduction policy from `memo-doc-agent-review.md` to the turn-processing-flow chapter (overview, LLM/tool loop, workflow-engine parts 1-2): keep the per-turn conceptual model and operational guidance on approval/partial-completion; remove sequential call-detail and dataclass field dumps.

## Reason for Change
This chapter is a primary source for correlation-ID, approval-wait, partial-completion, and workflow-state concepts that matter for operations and audit — but currently also carries step-by-step function-call sequences, private method names, and dataclass field lists that are better left to code.

## Implementation Intent
Keep this chapter as the canonical source for turn-processing design intent (per `memo-doc-agent-review.md` §「章間の正本ルール」: ターン処理の設計意図 = `05_agent_03_turn-processing-flow`). Explicitly preserve correlation-ID / approval-wait / partial-completion / workflow-state concepts as operational and audit-relevant, described by intent rather than field enumeration.

## Target Files or Areas
- `docs/05_agent_03_01_turn-processing-flow-overview.md`
- `docs/05_agent_03_02_turn-processing-flow-llm-tool-loop.md`
- `docs/05_agent_03_03_turn-processing-flow-workflow-engine-part1.md`
- `docs/05_agent_03_03_turn-processing-flow-workflow-engine-part2.md`

## Required Changes
- Keep: the conceptual model of a single turn, why WorkflowEngine is mandatory, the meaning of plan/execute/verify, operational notes for approval-wait/background-failure/pause states, ToolLoopGuard's role and design intent, the reason partial completions are separated from conversation history.
- Remove or compress: sequential function-call walkthroughs, private method names, dataclass field lists, guard public-method enumerations, verbatim constant-string quotes, mechanical state-transition tables like `current_turn_id`.
- Preserve as intent (not as field lists): correlation ID, approval-wait, partial completion, workflow state — explain their operational/audit meaning.

## Acceptance Criteria
- All four files follow the standard template from `memo-doc-agent-review.md` §「修正後の章構成テンプレート」.
- No private-method-name list or dataclass field dump remains.
- Approval-wait / partial-completion / workflow-state concepts remain, framed as operational judgment rather than field enumeration.

## Testing Expectations
Not required for behavior (documentation-only). Run `python tools/check_agent_docs_consistency.py` after editing.

## Documentation Impact
This issue is itself a documentation-only cleanup task.

## Out of Scope
- Other `docs/05_agent_*.md` chapters.
- Code changes to `ToolLoopGuard` or workflow-engine implementation.

## AI Implementation Instruction
Follow `memo-doc-agent-review.md` §「05_agent_03_turn-processing-flow」 including its 注意 note: do not strip correlation-ID/approval/partial-completion/workflow-state concepts, only their field-level description. Mark unclear rationale as `Needs Confirmation`.

## Traceability
- Workflow phase: issue-creation
- Source: `memo-doc-agent-review.md` §「05_agent_03_turn-processing-flow」
- Generated at: 2026-08-05
