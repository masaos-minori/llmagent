# Reduce implementation-derived detail in docs/05_agent_01_system-overview.md

## Priority
Medium

## Summary
Apply the design-doc reduction policy from `memo-doc-agent-review.md` to `docs/05_agent_01_system-overview.md`: keep purpose, scope boundaries, and the high-level execution model; remove mechanical entry-point call chains and full slash-command enumerations.

## Reason for Change
The chapter currently mixes design intent (why WorkflowEngine is always in the path, why RAG/MCP/Embedding are out of scope) with code-derivable detail (entry-point call sequences, class-to-file tables, exact prompt strings) that will drift from the source and adds no decision value.

## Implementation Intent
Keep this chapter as the canonical source for overall scope and the top-level execution model (per `memo-doc-agent-review.md` §「章間の正本ルール」: 全体像・対象範囲 = `05_agent_01_system-overview`). Push component-level detail to the chapters that own it.

## Target Files or Areas
`docs/05_agent_01_system-overview.md`

## Required Changes
- Keep: Agent's purpose, in-scope/out-of-scope boundaries, overall execution model, the reason WorkflowEngine is always traversed, the RAG/MCP/Embedding out-of-scope boundary, high-level responsibilities of major components.
- Remove or compress: detailed entry-point call sequences, mechanical class/file correspondence tables, prompt literal strings and history-filename details that are visible in code, exhaustive slash-command enumeration.

## Acceptance Criteria
- Chapter follows the standard template from `memo-doc-agent-review.md` §「修正後の章構成テンプレート」.
- No entry-point call-sequence walkthrough or full class/file table remains.
- Slash commands are referenced by pointer to the canonical command chapter (`05_agent_07_*`), not re-enumerated here.

## Testing Expectations
Not required for behavior (documentation-only). Run `python tools/check_agent_docs_consistency.py` after editing.

## Documentation Impact
This issue is itself a documentation-only cleanup task.

## Out of Scope
- Other `docs/05_agent_*.md` chapters.
- Slash-command detail (owned by `05_agent_07_*`, tracked separately).
- Code changes.

## AI Implementation Instruction
Follow `memo-doc-agent-review.md` §「05_agent_01_system-overview」. When content overlaps with a chapter that owns it canonically (e.g. commands), replace with a pointer rather than re-explaining. Mark unclear design rationale as `Needs Confirmation` instead of guessing.

## Traceability
- Workflow phase: issue-creation
- Source: `memo-doc-agent-review.md` §「05_agent_01_system-overview」
- Generated at: 2026-08-05
