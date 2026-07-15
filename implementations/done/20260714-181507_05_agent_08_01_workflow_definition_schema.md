# Implementation Procedure: Create Missing Workflow Definition Schema Section

## Goal

Create a complete "Workflow Definition Schema" section in the agent configuration loading documentation to fix a broken cross-reference and document the workflow-level approval gate mechanism.

## Scope

- `docs/05_agent_08_01_configuration-loading-agent-config-part1.md` only (new section after line 127)
- New content creation; no existing content modification

## Assumptions

1. The requirement `requires/20260714_02_require.md` is the canonical specification for this task.
2. The anchor referenced in `05_agent_06_04` L48 pointed to a non-existent section in `05_agent_08_01`.
3. The workflow definition schema includes fields for controlling approval gates.

## Implementation

### Target file

`docs/05_agent_08_01_configuration-loading-agent-config-part1.md`

### Procedure

1. **Identify insertion point**: After line 127 in the document.
2. **Create new section**: Add a "Workflow Definition Schema" section with complete field reference.
3. **Fix broken link**: Update the cross-reference in `05_agent_06_04` to point to the new section.

### Method

- Section creation via file insert.
- Cross-reference update via file edit.

### Details

- After line 127: Insert a new section titled "Workflow Definition Schema" containing:
  - Complete field reference for the workflow definition structure
  - Validation rules for each field
  - Description of approval gate behavior based on `require_approval` field
  - Example workflow definition JSON snippet showing `require_approval` usage
- Fix the broken link in `05_agent_06_04` to point to `05_agent_08_01#workflow-definition-schema`

## Validation plan

1. Verify the new section contains all required fields and validation rules.
2. Verify the cross-reference in `05_agent_06_04` resolves correctly.
3. Confirm the example JSON snippet is syntactically valid.
4. Run `pre-commit run --all-files` if markdown linting is configured.
