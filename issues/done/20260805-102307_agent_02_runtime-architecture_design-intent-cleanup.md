# Reduce implementation-derived detail in docs/05_agent_02_runtime-architecture-part{1,2}.md

## Priority
Medium

## Summary
Apply the design-doc reduction policy from `memo-doc-agent-review.md` to the runtime-architecture chapter (both parts): keep responsibility-boundary and startup-safety judgments; remove private-class/mixin/MRO detail and method-level responsibility tables.

## Reason for Change
This chapter mixes genuine architectural boundary decisions (AgentREPL as a thin UI coordinator, StartupOrchestrator's separation rationale, shared/agent dependency direction, fail-fast/rollback policy) with implementation detail that changes on every refactor (private class names, mixin counts, MRO, per-method tables), causing frequent doc/code drift.

## Implementation Intent
Keep this chapter as the canonical source for runtime responsibility boundaries (per `memo-doc-agent-review.md` §「章間の正本ルール」: ランタイム責務境界 = `05_agent_02_runtime-architecture`).

## Target Files or Areas
- `docs/05_agent_02_runtime-architecture-part1.md`
- `docs/05_agent_02_runtime-architecture-part2.md`

## Required Changes
- Keep: AgentREPL-as-thin-coordinator judgment, reason StartupOrchestrator was split out, AgentContext/AppServices responsibility boundary, Orchestrator/LLMTurnRunner/ToolExecutor/HistoryManager role split, shared-vs-agent dependency direction, startup-validation fail-fast/rollback policy.
- Remove or compress: fine-grained private class names in dependency graphs, mixin counts, MRO detail, internal implementation class names, method-level responsibility tables, `Explicit in code`-labeled implementation-confirmation notes.

## Acceptance Criteria
- Both parts follow the standard template from `memo-doc-agent-review.md` §「修正後の章構成テンプレート」.
- No mixin/MRO enumeration or method-level responsibility table remains.
- Fail-fast/rollback policy for startup validation is stated as a judgment (why), not just a mechanical description of steps.

## Testing Expectations
Not required for behavior (documentation-only). Run `python tools/check_agent_docs_consistency.py` after editing.

## Documentation Impact
This issue is itself a documentation-only cleanup task.

## Out of Scope
- Other `docs/05_agent_*.md` chapters.
- Detailed startup runbook content (owned by `05_agent_10_*`, tracked separately).
- Code changes.

## AI Implementation Instruction
Follow `memo-doc-agent-review.md` §「05_agent_02_runtime-architecture」. Preserve shared/agent dependency-direction rules verbatim in intent (this is an architectural boundary rule enforced elsewhere, e.g. `lint-imports`). Mark unclear rationale as `Needs Confirmation`.

## Traceability
- Workflow phase: issue-creation
- Source: `memo-doc-agent-review.md` §「05_agent_02_runtime-architecture」
- Generated at: 2026-08-05
