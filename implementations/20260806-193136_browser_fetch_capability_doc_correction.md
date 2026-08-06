## Goal

Correct the documentation to reflect that `browser_fetch` does not actually use the `capabilities` field in production, despite claims in the current document.

## Scope

- **In-Scope**:
  - Modify "具体例" (Examples) section in `docs/04_mcp_08_tool_capability_naming_convention.md`.
  - Modify "ステータス" (Status) section in `docs/04_mcp_08_tool_capability_naming_convention.md`.
- **Out-of-Scope**:
  - Modifying source code or test files.
  - Changes to any other documentation files.

## Assumptions

1. The literal string `"web_fetch"` in the doc refers to the test fixture in `tests/test_runtime_tool_routing_integration.py`, not a production feature.
2. No MCP server currently sets a `capabilities` key following this naming convention in production.

## Design decisions

- Use targeted section edits rather than rewriting the entire document — minimizes change surface and avoids cascading rewrites.
- Clearly distinguish between test fixtures and production behavior in the correction.

## Alternatives considered

- Delete the entire "具体例" section: rejected because readers lose useful context about how the convention was tested.
- Add a footnote to existing sections: rejected because the claim itself is incorrect and needs direct replacement.

## Compatibility considerations

- Readers who previously assumed `browser_fetch` had a `capabilities` key in production will see the correction.
- No API contract changes — this is purely a documentation correction.

## Security considerations

N/A — documentation-only changes.

## Rollback considerations

- If the test fixture `tests/test_runtime_tool_routing_integration.py` is later removed or renamed, the cross-reference in the correction will break.
- If a production MCP server later adopts the `capabilities` key, the status section should be updated accordingly.

## Implementation

### Target file

`docs/04_mcp_08_tool_capability_naming_convention.md`

### Procedure

**Step 1: Modify "具体例" (Examples) section**

1. Locate the sub-heading "**現在採用しているツール:**" and its subsequent bullet point.
2. Replace them with a note stating that `("web_fetch",)` is used only in `tests/test_runtime_tool_routing_integration.py` and is not present in any production MCP server.

### Method

Direct file edit using sed or manual editing.

### Details

- Find the "**現在採用しているツール:**" sub-heading.
- Replace the bullet point claiming `browser_fetch` has `capabilities=("web_fetch",)` with:
  > `("web_fetch",)` is used only in `tests/test_runtime_tool_routing_integration.py` as a test fixture. It is not present in any production MCP server.

**Step 2: Modify "ステータス" (Status) section**

Rewrite the sentence claiming the convention was first adopted via `web_search-mcp`'s `browser_fetch`.

### Method

Direct file edit.

### Details

- Find the sentence claiming the convention was first adopted via `web_search-mcp`'s `browser_fetch`.
- Replace with prose such as:
  > The `capabilities` naming convention remains unadopted in production. No MCP server currently sets a `capabilities` key following this scheme.

## Verification

- Verify that the literal string `"web_fetch"` no longer appears as an adopted production value in `docs/04_mcp_08_tool_capability_naming_convention.md`.
- Confirm that the text correctly identifies the existence of `("web_fetch",)` as a test-only fixture.
- Ensure no changes were made to source code or test files.

```bash
# Verify no false production claim remains
grep -n '"web_fetch"' docs/04_mcp_08_tool_capability_naming_convention.md

# Verify the test-only clarification exists
grep -n "test_runtime_tool_routing_integration" docs/04_mcp_08_tool_capability_naming_convention.md

# Verify no source code was modified
git diff --name-only scripts/ tests/
```

## Out of scope

- Source code modifications (`scripts/`).
- Test file modifications (`tests/`).
- Changes to other documentation not listed above.

## Traceability

- Workflow phase: plan-to-implementation-procedure
- Source issue: N/A
- Source requirement: requires/20260802-145428_require.md
- Source plan: plans/20260804-123000_plan.md
- Source implementation procedure: N/A
- Generated at: 20260806-193136
- Related target files: docs/04_mcp_08_tool_capability_naming_convention.md
