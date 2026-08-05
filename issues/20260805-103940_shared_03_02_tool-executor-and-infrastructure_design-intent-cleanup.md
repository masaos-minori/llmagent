# Reduce implementation-derived detail in docs/90_shared_03_02_runtime_and_execution-tool-executor-and-infrastructure.md

## Priority
High

## Summary
Apply the design-doc reduction policy from `memo-doc-shared-review.md` to `docs/90_shared_03_02_runtime_and_execution-tool-executor-and-infrastructure.md`: keep the `ToolExecutor`/`RuntimeToolRegistry`/`ToolRegistry` boundary as a routing source-of-truth judgment; remove constructor signatures and method-level tables.

## Reason for Change
This chapter is the canonical source for the `ToolExecutor`/`RuntimeToolRegistry`/`ToolRegistry` boundary (per `memo-doc-shared-review.md` §「章間の正本ルール」: ToolExecutor / RuntimeToolRegistry / ToolRegistry境界 = `90_shared_03_02_runtime_and_execution-tool-executor-and-infrastructure`). Per the memo's explicit 注意: this boundary is important and must be kept, but expressed as "source of truth / boundary / operational meaning," not a method-name-centric description.

## Implementation Intent
Keep this chapter focused on why `RuntimeToolRegistry` is the sole runtime-routing source of truth, why `ToolRegistry` is drift-validation seed only, why cache holds only successful results, and why side-effecting tools require care.

## Target Files or Areas
`docs/90_shared_03_02_runtime_and_execution-tool-executor-and-infrastructure.md`

## Required Changes
- Keep: `ToolExecutor`'s responsibility boundary (single-tool-call execution foundation; approval/round-control stay on the agent side), that `RuntimeToolRegistry` is the sole runtime-routing/RuntimeTool-metadata source of truth, that `ToolRegistry` is a drift-validation seed and must not be used for runtime routing, the design intent behind the tool-result cache, why only successful results are cached, why side-effecting tools require care with caching/parallelization, the purpose of `HealthRegistry` as a dispatch gate, the HALF_OPEN experimental-recovery concept, why the OTel tracer is a private provider, the design intent behind exact-vs-estimated-fallback token counting.
- Remove or compress: `ToolExecutor`'s constructor signature, the sequential internal processing steps of `execute()`, a helper-function list, `ToolRegistry`/`ToolRouteResolver` method lists, a detailed table of all `HealthRegistry` state transitions, function signatures for `token_counter`/`git_helper`/formatters, the API list for `LlmPayloadHandler`/`LlmHotConfigHandler`.

## Acceptance Criteria
- The chapter follows the standard template from `memo-doc-shared-review.md` §「修正後の章構成テンプレート」.
- No constructor signature, method list, or state-transition table remains.
- The `RuntimeToolRegistry`-as-sole-source-of-truth / `ToolRegistry`-as-seed-only distinction remains explicit and unweakened, expressed as boundary/operational-meaning rather than method names.

## Testing Expectations
Not required for behavior (documentation-only), but review must confirm the routing-source-of-truth distinction was not weakened — misrouting risk if `ToolRegistry` is mistaken for the routing source. No dedicated shared/db docs-consistency script exists; manually check internal links.

## Documentation Impact
This issue is itself a documentation-only cleanup task, but touches tool-routing-safety-relevant documentation — treat removal decisions conservatively.

## Out of Scope
- Other `docs/90_shared_*.md` chapters.
- Any code under `scripts/shared/` (including `tool_executor.py`, `runtime_tool_registry.py`, `tool_registry.py`).

## AI Implementation Instruction
Follow `memo-doc-shared-review.md` §「90_shared_03_02_runtime_and_execution-tool-executor-and-infrastructure」 including its 注意 note: express the boundary as source-of-truth/operational-meaning, not method names. Do not edit code. Mark unclear rationale as `Needs Confirmation`.

## Traceability
- Workflow phase: issue-creation
- Source: `memo-doc-shared-review.md` §「90_shared_03_02_runtime_and_execution-tool-executor-and-infrastructure」
- Generated at: 2026-08-05
