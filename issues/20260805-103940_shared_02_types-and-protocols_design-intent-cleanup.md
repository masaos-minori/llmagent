# Reduce implementation-derived detail in docs/90_shared_02_*_types_and_protocols*.md

## Priority
Medium

## Summary
Apply the design-doc reduction policy from `memo-doc-shared-review.md` to the types-and-protocols chapter (core-types, tool-and-execution-dto parts 1-2, reference): keep why each type lives in shared/ and which boundary it protects; remove full field lists, DTO signatures, and Protocol/TypedDict/dataclass comparison tables.

## Reason for Change
This chapter is the canonical source for the design intent behind shared types and Protocols (per `memo-doc-shared-review.md` §「章間の正本ルール」: 共通型とProtocolの設計意図 = `90_shared_02_types_and_protocols`). Per the memo's explicit 注意 for this chapter: what matters is not the shape of the type, but why it lives in shared/ and which boundary it protects.

## Implementation Intent
Keep this chapter focused on: why common types live in shared/, why LLM DTOs are separated so they can be imported without `LLMClient`, the Protocol/TypedDict/dataclass usage policy, why `RagConfig` is a structural Protocol rather than `AgentConfig`, that `ArtifactEvent` is a data definition only (not an event bus), that `ShellPolicy` separates policy values from the shell MCP implementation, the design intent behind `RuntimeTool`/`RuntimeToolRegistry` heading toward being the canonical runtime metadata source, and the shared-is-leaf constraint (shared/ must not import agent's enums/config classes).

## Target Files or Areas
- `docs/90_shared_02_01_types_and_protocols-core-types.md`
- `docs/90_shared_02_02_types_and_protocols-tool-and-execution-dto-part1.md`
- `docs/90_shared_02_02_types_and_protocols-tool-and-execution-dto-part2.md`
- `docs/90_shared_02_03_types_and_protocols-reference.md`

## Required Changes
- Remove or compress: the full field definition of `LLMMessage`, full field lists for DTOs like `ToolCallResult`, signatures for `ActionResult`/`ToolSpec`/`CacheEntry`, dataclass definitions for `RawHit`/`MergedHit`/`RankedHit`, `ToolCallFunction`-family TypedDict listings, the full field list of `ShellPolicy`, a full tool-frozenset name enumeration, Pydantic definitions for `CallToolRequest`/`Response`, a textbook-style Protocol/TypedDict/dataclass comparison table.
- Keep the reasoning listed above intact even where the surrounding field-level detail is trimmed.

## Acceptance Criteria
- All four files follow the standard template from `memo-doc-shared-review.md` §「修正後の章構成テンプレート」.
- No full DTO/dataclass/Protocol field list or textbook-style type-comparison table remains.
- Each type's "why it's in shared/, what boundary it protects" rationale remains explicit.

## Testing Expectations
Not required for behavior (documentation-only). No dedicated shared/db docs-consistency script exists; manually check internal links.

## Documentation Impact
This issue is itself a documentation-only cleanup task.

## Out of Scope
- Other `docs/90_shared_*.md` chapters.
- `scripts/shared/types.py` itself and other type-defining modules (code, not documentation).

## AI Implementation Instruction
Follow `memo-doc-shared-review.md` §「90_shared_02_types_and_protocols」 including its 注意 note: describe why a type exists in shared/ and what boundary it protects, not its field shape. Do not edit code. Mark unclear rationale as `Needs Confirmation`.

## Traceability
- Workflow phase: issue-creation
- Source: `memo-doc-shared-review.md` §「90_shared_02_types_and_protocols」
- Generated at: 2026-08-05
