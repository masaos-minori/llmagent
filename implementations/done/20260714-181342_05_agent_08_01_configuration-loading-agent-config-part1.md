# Implementation Procedure: Remove Obsolete Direct-Execution Fallback Documentation (Configuration Loading Part 1)

## Goal

Clarify that `workflow_mode` and `workflow_require_approval` are not just "deleted" but are actively rejected as invalid config keys via `_FORBIDDEN_KEYS`.

## Scope

- `docs/05_agent_08_01_configuration-loading-agent-config-part1.md` only (line 93-96)
- Text clarification; no new content creation

## Assumptions

1. The requirement `requires/20260714_01_require.md` is the canonical specification for this task.
2. Workflow support is mandatory; no degraded workflow mode exists.
3. No source code changes are required — documentation updates only.

## Implementation

### Target file

`docs/05_agent_08_01_configuration-loading-agent-config-part1.md`

### Procedure

1. **Locate lines 93-96**: Find the section discussing `workflow_mode` and `workflow_require_approval` removal.
2. **Rewrite the section**: Replace the current description ("deleted") with clarification that these fields are actively rejected as invalid config keys via `_FORBIDDEN_KEYS`.

### Method

- Text rewrite via file edit.
- Preserve surrounding context and formatting.
- Ensure the rewritten section clearly distinguishes between "deleted" (past tense, implying removal) and "rejected" (current behavior).

### Details

- Lines 93-96: The current section likely describes `workflow_mode` and `workflow_require_approval` as having been "deleted" from the configuration. Rewrite to state: these fields are not valid config options and are actively rejected at config load time via `_FORBIDDEN_KEYS`. This distinction matters because "deleted" could be misinterpreted as a one-time cleanup rather than an ongoing enforcement mechanism.
- Example rewrite: "The `workflow_mode` and `workflow_require_approval` fields are not valid configuration options. They are actively rejected at config load time by `_FORBIDDEN_KEYS`."

## Validation plan

1. Verify the rewritten section clearly states these are not valid config options.
2. Confirm no cross-references to the old "deleted" description exist in other documents.
3. Run `pre-commit run --all-files` if markdown linting is configured.
