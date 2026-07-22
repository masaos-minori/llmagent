## Goal

Update startup validation behavior document to clarify operational impact of SKIPPED discovery in local mode.

## Scope

- Update `docs/04_mcp_06_11_startup-validation-behavior-tool_definitions_strict.md` — add operational impact note for SKIPPED outcome

## Assumptions

1. The existing documentation structure and content are correct; only additions are needed
2. The "全て到達不能" row needs an operational impact note
3. A new important note below the table is needed about SKIPPED severity

## Design decisions

- Modify the existing "全て到達不能" row to include operational impact note inline
- Add a separate important note below the table for emphasis

## Alternatives considered

- Adding this as a separate section instead of modifying the existing row
- Creating a separate appendix for operational impacts

## Implementation

### Target file

- `docs/04_mcp_06_11_startup-validation-behavior-tool_definitions_strict.md`

### Procedure

#### Step 1: Locate the "全て到達不能" row

1. Open `docs/04_mcp_06_11_startup-validation-behavior-tool_definitions_strict.md`
2. Find the table containing the "全て到達不能" row

#### Step 2: Update the row

Change the existing row from:

```markdown
| **全て到達不能** — どのサーバも応答しない | 検証がスキップされる；`INFO: "All MCP servers unreachable ... skipping tool definition check"` | `RuntimeError: "Strict mode: all MCP servers unreachable — cannot validate tool definitions. Unreachable servers: [...]"` |
```

To:

```markdown
| **全て到達不能** — どのサーバも応答しない | 検証がスキップされる；`INFO: "All MCP servers unreachable ... skipping tool definition check"` — **local mode: SKIPPED outcome means all tool calls will fail for that session** | `RuntimeError: "Strict mode: all MCP servers unreachable — cannot validate tool definitions. Unreachable servers: [...]"` |
```

#### Step 3: Add important note below the table

Insert the following markdown below the table:

```markdown
**重要:** local modeでdiscoveryがSKIPPEDの場合、起動は継続するが、RuntimeToolRegistryは空または不完全なままになる。このため、LLMがツールを認識していても実行時にすべて失敗する。運用者は`mcp_tool_discovery`のSKIPPED結果をWARNINGと同様の重大度で扱う必要がある。
```

#### Step 4: Verify cross-references

If there are any cross-references to other sections in the document, ensure they still work correctly.

## Compatibility considerations

- No API changes — documentation-only update
- Existing cross-references should continue to work
- The new notes help prevent misunderstanding about SKIPPED severity

## Security considerations

- N/A — documentation-only change

## Rollback considerations

- Revert the modifications if the operational impact descriptions are incorrect

## Validation plan

| Target File/Module | Testing Strategy | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `docs/04_mcp_06_11_startup-validation-behavior-tool_definitions_strict.md` | Documentation consistency check | Manual review | Row updated correctly, note visible |

## Out of scope

- Implementing `include_disabled` query parameter for `/v1/tools`
- Implementing `disabled_code` structured field
- Any source code changes

## Traceability

- Workflow phase: plan-to-implementation-procedure
- Source issue: N/A
- Source requirement: requires/ready/20260722-124218_require.md
- Source plan: plans/20260722-145326_plan.md
- Source implementation procedure: N/A
- Generated at: 20260722-180448
- Related target files: docs/04_mcp_06_11_startup-validation-behavior-tool_definitions_strict.md
