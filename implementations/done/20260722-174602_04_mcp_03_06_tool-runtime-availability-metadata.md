## Goal

Clarify enabled/disabled_reason field mappings between /v1/tools response and RuntimeTool fields, documenting the gap where disabled_reason is not currently a first-class RuntimeTool field.

## Scope

- Update `docs/04_mcp_03_06_tool-runtime-availability-metadata.md` — clarify enabled/disabled_reason field mapping

## Assumptions

1. The existing documentation structure and content are correct; only clarifications are needed
2. The gap between /v1/tools.enabled and RuntimeTool.enabled_for_llm needs explicit documentation
3. The deferred nature of disabled_reason support needs to be documented

## Design decisions

- Add a dedicated subsection titled "Field Mapping: /v1/tools ↔ RuntimeTool" rather than modifying existing sections
- Use a table format to show the mapping clearly

## Alternatives considered

- Adding inline notes within existing sections instead of creating a new subsection
- Creating a separate appendix for field mappings

## Implementation

### Target file

- `docs/04_mcp_03_06_tool-runtime-availability-metadata.md`

### Procedure

#### Step 1: Locate insertion point

1. Open `docs/04_mcp_03_06_tool-runtime-availability-metadata.md`
2. Find the section describing /v1/tools response fields
3. Identify where the field mapping clarification should be inserted

#### Step 2: Add field mapping section

Insert the following markdown after the existing /v1/tools response field descriptions:

```markdown
## Field Mapping: /v1/tools ↔ RuntimeTool

The following table shows how /v1/tools response fields map to RuntimeTool fields:

| /v1/tools field | RuntimeTool field | Notes |
|---|---|---|
| `enabled` | `enabled_for_llm` | Both indicate LLM visibility; values should match |
| `disabled_reason` | *(not a first-class field)* | Currently not stored in RuntimeTool; deferred future task |

### Key points

- `enabled` and `enabled_for_llm` serve the same purpose: indicating whether the tool is visible to the LLM
- `disabled_reason` from /v1/tools is **not** currently a first-class RuntimeTool field
- The reason a tool is disabled is determined by the source of truth (config, health status, etc.) rather than being carried forward in RuntimeTool
- Future work will add `RuntimeTool.disabled_reason` as a first-class field to close this gap
```

#### Step 3: Update deferred tasks note

If there is an existing "Deferred Tasks" or similar section in the document, add a reference to this gap:

```markdown
- [ ] First-class `RuntimeTool.disabled_reason` field — see "Field Mapping: /v1/tools ↔ RuntimeTool" above
```

## Compatibility considerations

- No API changes — documentation-only update
- Existing cross-references should continue to work
- The deferred task note helps track future work

## Security considerations

- N/A — documentation-only change

## Rollback considerations

- Revert the added subsection if the field mapping is incorrect

## Validation plan

| Target File/Module | Testing Strategy | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `docs/04_mcp_03_06_tool-runtime-availability-metadata.md` | Documentation consistency check | Manual review | Section added correctly, mapping accurate |

## Out of scope

- Implementing `include_disabled` query parameter for `/v1/tools`
- Implementing `disabled_code` structured field
- Adding `RuntimeTool.disabled_reason` as a first-class field (deferred)
- Any source code changes

## Traceability

- Workflow phase: plan-to-implementation-procedure
- Source issue: N/A
- Source requirement: requires/ready/20260722-123620_require.md
- Source plan: plans/20260722-135916_plan.md
- Source implementation procedure: N/A
- Generated at: 20260722-174602
- Related target files: docs/04_mcp_03_06_tool-runtime-availability-metadata.md
