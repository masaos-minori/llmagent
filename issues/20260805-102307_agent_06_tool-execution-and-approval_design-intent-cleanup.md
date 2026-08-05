# Reduce implementation-derived detail in docs/05_agent_06_*_tool-execution-and-approval*.md

## Priority
High

## Summary
Apply the design-doc reduction policy from `memo-doc-agent-review.md` to the tool-execution-and-approval chapter (execution, approval, concurrency-safety, canonical parts): keep approval/safety/routing judgments intact; remove field lists and call-order detail, but never at the expense of safety rationale.

## Reason for Change
This chapter covers approval, fail-closed behavior, DAG scheduling, and side-effect serialization — all safety-relevant. `memo-doc-agent-review.md` explicitly warns (§「注意」 for this chapter) that safety-relevant judgment must never be dropped even while trimming code-level detail, so this cleanup carries higher risk than purely cosmetic chapters if done carelessly.

## Implementation Intent
Keep this chapter as the canonical source for tool-execution/approval/safety design (per `memo-doc-agent-review.md` §「章間の正本ルール」: ツール実行・承認・安全制御 = `05_agent_06_tool-execution-and-approval`).

## Target Files or Areas
- `docs/05_agent_06_01_tool-execution-and-approval-execution.md`
- `docs/05_agent_06_02_tool-execution-and-approval-approval.md`
- `docs/05_agent_06_03_tool-execution-and-approval-concurrency-safety.md`
- `docs/05_agent_06_04_tool-execution-and-approval-canonical.md`

## Required Changes
- Keep: `ToolExecutor` responsibility boundary, `RuntimeToolRegistry` as routing source of truth (and that `tool_names`/`ToolRegistry` are not), why DAG scheduling is used, the meaning of `serial_tool_calls`, why side-effecting tools are serialized, the Tool-level vs. Workflow-level approval boundary, why `RepositoryGateway` is an enforced boundary, fail-closed design, plan-mode design intent, why caching is limited to successful results only, in-flight de-duplication intent.
- Remove or compress: `ToolCallResult` field lists, detailed internal call order inside `execute()`, duplicated approve/reject argument explanations, full GitHub-tool-name enumeration, preview-format tables, full audit-log field enumeration, method/helper-function detail.
- Explicitly re-verify after trimming: every safety-relevant judgment (approval, side effects, DAG, caching) still states its reasoning and operational caveat, not just the resulting behavior.

## Acceptance Criteria
- All four files follow the standard template from `memo-doc-agent-review.md` §「修正後の章構成テンプレート」.
- No `ToolCallResult` field list or full GitHub-tool-name table remains.
- Every safety-relevant judgment (fail-closed, approval boundary, DAG scheduling, cache-success-only, in-flight de-dup) is still explained with its rationale after editing — verified by re-reading the edited chapter against this checklist before closing the issue.

## Testing Expectations
Not required for code behavior (documentation-only), but review must explicitly re-check that no safety-relevant rationale was silently dropped. Run `python tools/check_agent_docs_consistency.py` after editing.

## Documentation Impact
This issue is itself a documentation-only cleanup task, but is safety-sensitive documentation (approval/fail-closed behavior) — treat removal decisions conservatively per `memo-doc-agent-review.md` §「編集時の判断ルール」.

## Out of Scope
- Other `docs/05_agent_*.md` chapters.
- Code changes to `ToolExecutor`, `RuntimeToolRegistry`, or approval logic.

## AI Implementation Instruction
Follow `memo-doc-agent-review.md` §「05_agent_06_tool-execution-and-approval」 including its 注意 note: approval/side-effect/DAG/cache reasoning and operational caveats must be kept even when trimming code detail. When in doubt about whether a detail is safety-relevant, keep it and mark it for human review rather than deleting. Mark unclear rationale as `Needs Confirmation`.

## Traceability
- Workflow phase: issue-creation
- Source: `memo-doc-agent-review.md` §「05_agent_06_tool-execution-and-approval」
- Generated at: 2026-08-05
