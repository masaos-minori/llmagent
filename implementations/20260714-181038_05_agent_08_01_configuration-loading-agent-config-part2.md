# Implementation Procedure: Remove Obsolete Direct-Execution Fallback Documentation (Configuration Loading Part 2)

## Goal

Condense the `workflow_mode` removal section in the agent configuration loading documentation to remove unnecessary elaboration on what the old modes were.

## Scope

- `docs/05_agent_08_01_configuration-loading-agent-config-part2.md` only
- Condensing existing content; no new content creation

## Assumptions

1. The requirement `requires/20260714_01_require.md` is the canonical specification for this task.
2. Workflow support is mandatory; no degraded workflow mode exists.
3. No source code changes are required — documentation updates only.

## Implementation

### Target file

`docs/05_agent_08_01_configuration-loading-agent-config-part2.md`

### Procedure

1. **Identify lines 43-49**: Locate the section about `workflow_mode` and `workflow_require_approval` fields being removed.
2. **Condense the section**: Keep only that `_FORBIDDEN_KEYS` rejects these keys. Remove the elaboration on what "auto"/"disabled" modes were.

### Method

- Text condensation via file edit.
- Replace detailed explanation with concise statement of fact.
- Preserve surrounding context and formatting.

### Details

- Lines 43-49: The current section describes both that the fields are rejected AND provides details about what the old modes were. Since those modes no longer exist and are irrelevant to understanding the current behavior, reduce to: "The `workflow_mode` and `workflow_require_approval` fields are rejected by `_FORBIDDEN_KEYS`."
- Do not add historical notes about the migration unless explicitly requested.

## Validation plan

1. Verify the condensed section still conveys the key information: the fields are rejected.
2. Confirm no cross-references to the removed elaboration exist in other documents.
3. Run `pre-commit run --all-files` if markdown linting is configured.
