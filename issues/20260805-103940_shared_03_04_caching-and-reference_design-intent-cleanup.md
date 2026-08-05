# Reduce implementation-derived detail in docs/90_shared_03_04_runtime_and_execution-caching-and-reference-part{1,2}.md

## Priority
Medium

## Summary
Apply the design-doc reduction policy from `memo-doc-shared-review.md` to the caching-and-reference chapter (both parts): keep the retry/cache/health design judgments, including the note that `ToolResultCache` is currently unused by `ToolExecutor` itself; remove method lists and dataclass definitions.

## Reason for Change
This chapter is the canonical source for cache/retry/health helper design (per `memo-doc-shared-review.md` §「章間の正本ルール」: キャッシュ・retry・health補助 = `90_shared_03_04_runtime_and_execution-caching-and-reference`). It also flags a known duplication/disorganization concern in the caching mechanism that should be preserved as a Known Issues/improvement candidate, not silently dropped.

## Implementation Intent
Keep this chapter focused on the retry-limited-to-transient-failures decision, the `ToolResultCache`-currently-unused-by-ToolExecutor note, `ToolSpec`'s role as DAG-scheduling metadata, `HealthRegistry`'s circuit-breaker-like meaning, and hot-reloadable LLM config.

## Target Files or Areas
- `docs/90_shared_03_04_runtime_and_execution-caching-and-reference-part1.md`
- `docs/90_shared_03_04_runtime_and_execution-caching-and-reference-part2.md`

## Required Changes
- Keep: the design decision that retry is limited to transient failures, that `ToolResultCache` is currently not used by `ToolExecutor` itself, that apparent duplication/disorganization in the caching mechanism should be treated as a Known Issues item or improvement candidate, that `ToolSpec` is DAG-scheduling metadata, `HealthRegistry`'s circuit-breaker-like meaning, that hot-reloadable LLM config can be changed at runtime.
- Remove or compress: `LlmRetryHandler`'s signature, `ToolResultCache`'s method list, `ToolSpec`'s dataclass definition, `HealthRegistry`'s full method list, `LlmPayloadHandler`/`LlmHotConfigHandler`'s method lists, an AI-reference table.

## Acceptance Criteria
- Both files follow the standard template from `memo-doc-shared-review.md` §「修正後の章構成テンプレート」.
- No method list or dataclass definition remains.
- The `ToolResultCache`-currently-unused note and the caching-duplication Known Issues flag remain explicit rather than silently dropped.

## Testing Expectations
Not required for behavior (documentation-only), but review must confirm the caching-duplication concern was preserved as a Known Issues note, not deleted. No dedicated shared/db docs-consistency script exists; manually check internal links.

## Documentation Impact
This issue is itself a documentation-only cleanup task. If the caching-duplication note is expanded, coordinate with `docs/90_shared_90_inconsistencies_and_known_issues.md`'s cleanup issue to avoid duplication.

## Out of Scope
- Other `docs/90_shared_*.md` chapters.
- Any code under `scripts/shared/` (including cache/retry/health infrastructure).

## AI Implementation Instruction
Follow `memo-doc-shared-review.md` §「90_shared_03_04_runtime_and_execution-caching-and-reference」. Do not edit code — the caching duplication should be flagged in documentation only, not fixed. Mark unclear rationale as `Needs Confirmation`.

## Traceability
- Workflow phase: issue-creation
- Source: `memo-doc-shared-review.md` §「90_shared_03_04_runtime_and_execution-caching-and-reference」
- Generated at: 2026-08-05
