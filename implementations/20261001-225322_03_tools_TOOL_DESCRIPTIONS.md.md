# Implementation Procedure: Update TOOL_DESCRIPTIONS.md if behavior changes

## Goal

Update `tools/TOOL_DESCRIPTIONS.md` only if the documented behavior of `check_canonical_source_conflicts.py` changes due to the `_wrap_validation_errors` fix.

## Scope

- Read and conditionally modify `tools/TOOL_DESCRIPTIONS.md`.
- In-Scope: Checking whether the tool description documents the current (buggy) behavior; updating if the fix changes any documented behavior.
- Out-of-Scope: Fixing `_wrap_validation_errors` (REQ-001); adding regression tests (REQ-002).

## Assumptions

- `tools/TOOL_DESCRIPTIONS.md` may contain descriptions of the conflict checker's behavior, including how validation errors are attributed to entries.
- If the tool description does not mention the cross-product behavior, no update is needed.
- If the tool description documents the buggy behavior (e.g., "each validation error is attributed to every entry"), it should be corrected.

## Design decisions

- **Approach**: Read the tool description, identify any statements about how validation errors are attributed to entries, and update them if they describe the buggy behavior.
- **Decision**: Based on canon003 investigation, the tool description likely does not explicitly document the cross-product behavior. This step is conditional — only execute if the description needs correction.

## Alternatives considered

- Always update the tool description regardless of content — rejected because unnecessary changes risk introducing errors.
- Skip this step entirely — rejected because the workflow requires checking whether documentation changes.

## Implementation

### Target file

`tools/TOOL_DESCRIPTIONS.md`

### Procedure

1. Read `tools/TOOL_DESCRIPTIONS.md` and locate the section describing `check_canonical_source_conflicts.py`.
2. Check if any statement describes how validation errors are attributed to entries.
3. If the description documents the buggy behavior, update it to reflect the fixed behavior.
4. If no relevant statement exists, confirm no changes are needed.

### Method

Read `tools/TOOL_DESCRIPTIONS.md` and conditionally edit based on findings.

### Details

**Step 1: Read the tool description**

```bash
rg -n "check_canonical_source_conflicts|CANONICAL-006|validation.*error" tools/TOOL_DESCRIPTIONS.md
```

**Step 2: Check for relevant statements**

Look for any statement that describes how validation errors are attributed to entries. Examples of statements that need updating:
- "Each validation error is attributed to every Registry entry."
- "The checker reports CANONICAL-006 for all entries when a multi-source violation exists."

**Step 3: If buggy behavior is documented**

Update the statement to reflect the fixed behavior:
- "Each validation error is attributed only to the Registry entry that caused it."
- "The checker reports CANONICAL-006 only for entries with multiple source_paths where the claim type is not 'runtime-behavior'."

**Step 4: If no relevant statement exists**

Confirm no changes are needed. Document this finding in the execution status.

## Compatibility considerations

- None expected — this is a conditional step that only applies if the tool description documents the buggy behavior.

## Security considerations

N/A: documentation-only change; no runtime security surface.

## Rollback considerations

Revert the tool description changes if the fix is reverted.

## Validation plan

| Target | Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| `tools/TOOL_DESCRIPTIONS.md` | Sync check | `uv run python tools/check_tool_descriptions_sync.py` | Pass (if behavior documentation changes) |

## Completion criteria

- If the tool description documents the buggy behavior: it is updated to reflect the fixed behavior.
- If no relevant statement exists: confirmed and documented.
- No contradictory behavior description remains in the tool description.

## Out of scope

Fixing `_wrap_validation_errors` (REQ-001). Adding regression tests (REQ-002). Resolving the `eventbus.persistence-schema` violation itself (canon002). Changing severity or blocking classification of CANONICAL codes unless required by the confirmed intent. Refactoring unrelated detection functions.

## Execution Status

### Execution Status

| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Read tool description | Pending | — | — | REQ-003 |
| 2 | Check for relevant statements | Pending | — | — | REQ-003 |
| 3 | Update if buggy behavior documented | Pending | — | — | REQ-003 |
| 4 | Confirm no changes if not found | Pending | — | — | REQ-003 |

### Blocker Log

| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created

| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability

- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: REQ-003 — fix CANONICAL-006 false positives in check_canonical_source_conflicts.py validation-error wrapping
- **Source issue**: N/A: no standalone requirement document is generated
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261001-223409_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261001-225322
- **Related target files**: tools/TOOL_DESCRIPTIONS.md
