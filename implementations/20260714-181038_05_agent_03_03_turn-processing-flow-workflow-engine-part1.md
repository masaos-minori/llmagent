# Implementation Procedure: Remove Obsolete Direct-Execution Fallback Documentation (Turn Processing Flow Part 1)

## Goal

Remove all references to direct-execution fallback in the workflow engine part1 documentation and simplify workflow mode/tracking field descriptions to reflect that workflow is always required.

## Scope

- `docs/05_agent_03_03_turn-processing-flow-workflow-engine-part1.md` only
- Removal of stale content; no new content creation

## Assumptions

1. The requirement `requires/20260714_01_require.md` is the canonical specification for this task.
2. Workflow support is mandatory; no degraded workflow mode exists.
3. No source code changes are required — documentation updates only.

## Implementation

### Target file

`docs/05_agent_03_03_turn-processing-flow-workflow-engine-part1.md`

### Procedure

1. **Remove lines 71-72**: Delete the entire paragraph describing direct-execution fallback ("フォールバック: `config/workflows/default.json`が存在しない、またはworkflow DBが利用不可の場合、従来の直接実行フローが使用される。").

2. **Simplify `mode` field description (line 84)**: Change from `"auto" | "required" | "disabled"` to `"required"` only.

3. **Simplify `tracking` field description (line 85)**: Change from `"enabled" | "not_loaded"` to `"enabled"` only.

### Method

- Direct text removal and simplification via file edit.
- Preserve surrounding context and formatting.
- Ensure no orphaned cross-references remain after removal.

### Details

- Line 71-72: Complete paragraph deletion. This describes a fallback path that no longer exists in the codebase.
- Line 84: The `mode` enum values must be simplified because workflow is never optional. Only `"required"` remains valid.
- Line 85: The `tracking` field's `"not_loaded"` state implied a disabled scenario that cannot occur in production. Only `"enabled"` remains valid.

## Validation plan

1. Verify no remaining references to `"auto"`, `"disabled"`, or `"not_loaded"` in the document.
2. Confirm the removed fallback paragraph does not break any cross-references from other documents.
3. Run `pre-commit run --all-files` if markdown linting is configured.
