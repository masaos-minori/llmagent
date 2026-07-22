## Goal

Add startup validation severity descriptions to the startup validation behavior document.

## Scope

- Update `docs/04_mcp_06_11_startup-validation-behavior-tool_definitions_strict.md` — add severity descriptions

## Assumptions

1. The existing documentation structure and content are correct; only additions are needed
2. The three severity levels (WARNING, FATAL, SKIPPED) need explicit documentation

## Design decisions

- Add a dedicated subsection titled "Startup validation statuses" with three sub-subsections
- Include clear descriptions and examples for each severity level
- Document the display method and prefix for each severity

## Alternatives considered

- Adding inline notes within existing sections instead of creating a new subsection
- Creating a separate appendix for severity descriptions

## Implementation

### Target file

- `docs/04_mcp_06_11_startup-validation-behavior-tool_definitions_strict.md`

### Procedure

#### Step 1: Locate insertion point

1. Open `docs/04_mcp_06_11_startup-validation-behavior-tool_definitions_strict.md`
2. Find an appropriate location for the severity descriptions (likely near the beginning of the document)
3. Identify where the new section should be inserted

#### Step 2: Add severity descriptions

Insert the following markdown:

```markdown
### Startup validation statuses

#### WARNING
A non-critical issue. The system continues operating but the operator should be aware.
Example: optional server discovery failed.
Displayed via `write_warning()` with `[warn]` prefix.

#### FATAL
A critical issue that prevents normal operation. The system may be partially functional.
Displayed via `write_fatal()` with `[fatal]` prefix for visual distinction.
Example: required server discovery failed.

#### SKIPPED
Discovery was skipped entirely. In local mode, this may indicate a full-session tool-call outage.
Displayed via `write_warning()` with `[SKIPPED]` prefix.
Example: MCP discovery skipped due to missing configuration.
```

#### Step 3: Cross-reference the severity descriptions

If there are any references to severity levels elsewhere in the document, ensure they point to the new section.

## Compatibility considerations

- No API changes — documentation-only update
- Existing cross-references should continue to work
- The new section helps prevent misunderstanding about severity levels

## Security considerations

- N/A — documentation-only change

## Rollback considerations

- Revert the added section if the severity descriptions are incorrect

## Validation plan

| Target File/Module | Testing Strategy | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `docs/04_mcp_06_11_startup-validation-behavior-tool_definitions_strict.md` | Documentation consistency check | Manual review | Section added correctly |

## Out of scope

- Implementing `include_disabled` query parameter for `/v1/tools`
- Implementing `disabled_code` structured field
- Any source code changes

## Traceability

- Workflow phase: plan-to-implementation-procedure
- Source issue: N/A
- Source requirement: requires/ready/20260722-124328_require.md
- Source plan: plans/20260722-164224_plan.md
- Source implementation procedure: N/A
- Generated at: 20260722-180703
- Related target files: docs/04_mcp_06_11_startup-validation-behavior-tool_definitions_strict.md
