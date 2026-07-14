# Implementation Procedure: Remove Obsolete Direct-Execution Fallback Documentation (Startup and Health)

## Goal

Simplify the `_get_workflow_status()` description to remove the "not loaded" case explanation that describes a scenario which cannot occur in production.

## Scope

- `docs/05_agent_10_01_operations-and-observability-startup-and-health.md` only
- Simplifying existing content; no new content creation

## Assumptions

1. The requirement `requires/20260714_01_require.md` is the canonical specification for this task.
2. Workflow support is mandatory; no degraded workflow mode exists.
3. No source code changes are required — documentation updates only.

## Implementation

### Target file

`docs/05_agent_10_01_operations-and-observability-startup-and-health.md`

### Procedure

1. **Locate line 57**: Find the `_get_workflow_status()` function description.
2. **Remove the "not loaded" case**: Delete the explanation for when `orchestrator.workflow_status()["tracking"] == "not_loaded"` returns `"not loaded"`.
3. **Simplify the description**: Retain only the two valid cases: `self._orchestrator is None` → `"unknown"`, and `orchestrator.workflow_status()["tracking"] == "enabled"` → `"enabled"`.

### Method

- Case elimination via file edit.
- Description rewrite for brevity.
- Preserve surrounding context and formatting.

### Details

- Line 57: The current description reads "_get_workflow_status() は `self._orchestrator is None` なら `"unknown"`、`orchestrator.workflow_status()["tracking"] == "enabled"` なら `"enabled"`、それ以外は `"not loaded"` を返す。". Simplify to: "_get_workflow_status() は `self._orchestrator is None` なら `"unknown"`、`orchestrator.workflow_status()["tracking"] == "enabled"` なら `"enabled"` を返す。"
- The "not loaded" case describes a scenario where startup would fail before REPL runs, so it cannot occur in production. Removing it eliminates confusion about non-existent degraded states.

## Validation plan

1. Verify the simplified description still covers all production-valid return values.
2. Confirm no cross-references to the removed "not loaded" case exist in other documents.
3. Run `pre-commit run --all-files` if markdown linting is configured.
