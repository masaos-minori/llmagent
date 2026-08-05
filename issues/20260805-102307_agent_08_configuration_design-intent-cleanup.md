# Reduce implementation-derived detail in docs/05_agent_08_*_configuration*.md

## Priority
Medium

## Summary
Apply the design-doc reduction policy from `memo-doc-agent-review.md` to the configuration chapter (agent-config parts 1-2, llm-rag, tools-memory, mcp-approval-obs): keep ownership and hot-reload/restart-required judgments; remove full field/default-value tables and dataclass-structure explanations.

## Reason for Change
This chapter is the canonical source for config ownership and reload-boundary judgment, but currently also carries exhaustive field/default-value tables that duplicate `config/agent.toml` and its dataclass definitions, adding drift risk without operational value.

## Implementation Intent
Keep this chapter as the canonical source for configuration ownership and reload boundaries (per `memo-doc-agent-review.md` §「章間の正本ルール」: 設定所有権とreload境界 = `05_agent_08_configuration`).

## Target Files or Areas
- `docs/05_agent_08_01_configuration-loading-agent-config-part1.md`
- `docs/05_agent_08_01_configuration-loading-agent-config-part2.md`
- `docs/05_agent_08_02_configuration-llm-rag.md`
- `docs/05_agent_08_03_configuration-tools-memory.md`
- `docs/05_agent_08_04_configuration-mcp-approval-obs.md`

## Required Changes
- Keep: which files own which settings, the Hot-reloadable / Restart-required / Startup-only judgment criteria, strict-mode settings required in production, the danger of an empty `allowed_tools` list, the operational meaning of `tool_safety_tiers`, the config-drift detection approach, and what operators must do after a config change.
- Remove or compress: full mechanical field lists per config, exhaustive default-value tables, dataclass-structure explanations, plain "this field is this type" statements.

## Acceptance Criteria
- All five files follow the standard template from `memo-doc-agent-review.md` §「修正後の章構成テンプレート」.
- No exhaustive field/default-value table remains; readers are pointed to `config/agent.toml` / the relevant dataclass for exact values.
- Hot-reloadable vs. Restart-required vs. Startup-only classification is stated as a judgment criterion, not just a per-field label table.

## Testing Expectations
Not required for behavior (documentation-only). Run `python tools/check_agent_docs_consistency.py` after editing.

## Documentation Impact
This issue is itself a documentation-only cleanup task.

## Out of Scope
- Other `docs/05_agent_*.md` chapters.
- `config/agent.toml` itself and its dataclass definitions (code/config, not documentation).

## AI Implementation Instruction
Follow `memo-doc-agent-review.md` §「05_agent_08_configuration」. Where exact default values are needed, point to `config/agent.toml` rather than transcribing a table that will go stale. Mark unclear rationale as `Needs Confirmation`.

## Traceability
- Workflow phase: issue-creation
- Source: `memo-doc-agent-review.md` §「05_agent_08_configuration」
- Generated at: 2026-08-05
