## Goal

Correct the tool counts in the "Server Catalog" table of `docs/04_mcp_01_system_overview.md` and add a note about the `web-search-mcp` update.

## Scope

- **In-Scope**: Modifying `docs/04_mcp_01_system_overview.md` to update `web-search-mcp` tool count (1 → 2) and `mdq-mcp` tool count (9 → 7), and adding a note regarding the `web-search-mcp` change.
- **Out-of-Scope**: Any modification to source code or other documentation files.

## Assumptions

1. Current tool counts in source are: `web-search-mcp` = 2, `mdq-mcp` = 7.
2. The note should be concise and placed near the relevant cell or table.

## Design decisions

- Treat additions as insert-only — do not modify existing text outside the target section.
- Use grep-based verification rather than Markdown AST parsing since we only need string-level comparison.

## Alternatives considered

- Rewrite the entire system overview doc: rejected because scope is limited to updating tool counts.
- Create a separate document for web-search-mcp update: rejected because scope is limited to this doc.

## Compatibility considerations

- Added sentences must use existing Japanese terminology conventions.
- Cross-references must use existing Markdown conventions within the document.

## Security considerations

N/A — documentation-only changes.

## Rollback considerations

- If added sentences cause formatting issues, revert to git history before edit.

## Implementation

### Target file

`docs/04_mcp_01_system_overview.md`

### Procedure

1. Verify existence of the target file.
2. Final verification of tool counts by counting `TOOL_LIST` entries in:
   - `scripts/mcp_servers/web_search/web_search_tools.py`
   - `scripts/mcp_servers/mdq/mdq_tools.py`
3. Locate the "Server Catalog" table in the document.
4. Update `web-search-mcp` tool count to `2`.
5. Update `mdq-mcp` tool count to `7`.
6. Add a note stating: "`web-search-mcp` count updated from 1 to 2 due to `browser_fetch` integration."

### Method

Direct file edit using sed or manual editing.

### Details

```bash
# Find the Server Catalog table
grep -n "Server.*Catalog\|サーバー.*カタログ" docs/04_mcp_01_system_overview.md

# Find the web-search-mcp mention
grep -n "web-search-mcp" docs/04_mcp_01_system_overview.md

# Find the mdq-mcp mention
grep -n "mdq-mcp" docs/04_mcp_01_system_overview.md

# Verify current tool counts
grep -c "TOOL_LIST" scripts/mcp_servers/web_search/web_search_tools.py
grep -c "TOOL_LIST" scripts/mcp_servers/mdq/mdq_tools.py

# Verify browser_fetch exists
grep -rn "browser_fetch" scripts/mcp_servers/web_search/
```

Insertion pattern:
- After the "Server Catalog" table, add a note:
  ```markdown
  > Note: `web-search-mcp` tool count updated from 1 to 2 due to `browser_fetch` integration.
  ```

### Target file

Verification

### Procedure

1. Manually verify the changes in the markdown file.
2. Check for any formatting issues in the table.
3. Run lint check on modified file.

### Method

Manual verification + tool execution.

### Details

```bash
# Verify web-search-mcp count updated
grep -c "web-search-mcp.*2" docs/04_mcp_01_system_overview.md

# Verify mdq-mcp count updated
grep -c "mdq-mcp.*7" docs/04_mcp_01_system_overview.md

# Verify note added
grep -c "browser_fetch.*integration\|browser_fetch.*統合" docs/04_mcp_01_system_overview.md

# Verify old counts removed
grep -c "web-search-mcp.*1\|mdq-mcp.*9" docs/04_mcp_01_system_overview.md

# Run lint check
ruff check docs/04_mcp_01_system_overview.md
```

Expected outcomes:
- `web-search-mcp` tool count updated to 2
- `mdq-mcp` tool count updated to 7
- Note about `browser_fetch` integration added
- Zero lint errors on the file
- Document structure preserved (no accidental restructuring)

## Validation plan

| Check | Tool | Target | Expected Outcome |
|---|---|---|---|
| Lint | `ruff check docs/04_mcp_01_*.md` | Docs files | 0 errors |
| Manual | Visual/Grep | Table content | Correct counts and note present |

## Out of scope

- Modifications to `scripts/rag/pipeline.py`, `scripts/mcp_servers/rag_pipeline/`.
- Modifications to any other documentation files.
- Creating new documentation files.

## Traceability

- Workflow phase: plan-to-implementation-procedure
- Source issue: N/A
- Source requirement: requires/20260802-170840_require.md
- Source plan: plans/20260805-123200_plan.md
- Source implementation procedure: N/A
- Generated at: 20260806-214644
- Related target files: docs/04_mcp_01_system_overview.md
