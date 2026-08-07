## Goal

Update `docs/04_mcp_05_04_mdq-rag-boundary.md` to accurately describe how "override mode" works and how tool execution failures are handled, removing the implication that a dedicated "override mode" availability check exists.

## Scope

- **In-Scope**: Modifying `docs/04_mcp_05_04_mdq-rag-boundary.md` to correct the description of "override mode" and tool-call failure behavior in the "ルーティング方針" (Routing Policy) section.
- **Out-of-Scope**:
  - Modifying any source code (`scripts/`).
  - Adding new `.importlinter` contracts.

## Assumptions

1. The correction will replace the misleading row in the availability-fallback table.
2. The updated text will clearly distinguish between prompt-level routing hints and actual tool-execution error handling.

## Design decisions

- Treat additions as insert-only — do not modify existing text outside the target section.
- Use grep-based verification rather than Markdown AST parsing since we only need string-level comparison.

## Alternatives considered

- Rewrite the entire mdq-rag-boundary doc: rejected because scope is limited to correcting one row.
- Create a separate document for override mode: rejected because scope is limited to this doc.

## Compatibility considerations

- Added sentences must use existing Japanese terminology conventions.
- Cross-references must use existing Markdown conventions within the document.

## Security considerations

N/A — documentation-only changes.

## Rollback considerations

- If added sentences cause formatting issues, revert to git history before edit.

## Implementation

### Target file

`docs/04_mcp_05_04_mdq-rag-boundary.md`

### Procedure

1. Verify existence of the target file.
2. Locate the "ルーティング方針" (Routing Policy) section in the document.
3. Find the availability-fallback table.
4. Revise the third row (currently describing "override mode forced-server unavailable") to reflect:
   - "Override mode" (`config_mode` set to `mdq` or `rag`) only injects a routing hint into the system prompt via `scripts/agent/mdq_rag_classifier.py:resolve_mode()` and `scripts/agent/mode_classification.py:classify_and_inject_mode()`.
   - It does not force or wrap actual tool execution.
   - Any tool call failure (including `rag-pipeline-mcp`) returns an error to the caller via `scripts/shared/tool_transport_invoker.py` with no fallback to another mode/server.
5. Ensure citations to the relevant code (as specified in the requirement) are included.

### Method

Direct file edit using sed or manual editing.

### Details

```bash
# Find the routing policy section
grep -n "ルーティング方針\|Routing.*Policy" docs/04_mcp_05_04_mdq-rag-boundary.md

# Find the availability-fallback table
grep -n "availability.*fallback\|フォールバック.*Table" docs/04_mcp_05_04_mdq-rag-boundary.md

# Find the override mode mention
grep -n "override.*mode\|オーバーライド.*モード" docs/04_mcp_05_04_mdq-rag-boundary.md

# Verify resolve_mode location
grep -rn "def resolve_mode" scripts/agent/mdq_rag_classifier.py

# Verify classify_and_inject_mode location
grep -rn "def classify_and_inject_mode" scripts/agent/mode_classification.py

# Verify tool_transport_invoker location
grep -rn "class ToolTransportInvoker\|is_error" scripts/shared/tool_transport_invoker.py
```

Insertion pattern:
- Replace the third row of the availability-fallback table with:
  ```markdown
  | Override mode (`config_mode` = `mdq` or `rag`) | System prompt routing hint (`mdq_rag_classifier.py:resolve_mode()`, `mode_classification.py:classify_and_inject_mode()`) | No fallback; tool call failure returns error via `tool_transport_invoker.py` |
  ```

### Target file

Verification

### Procedure

1. Manually verify the corrected information against the requirements.
2. Check for broken formatting or structure in the table.
3. Run lint check on modified file.

### Method

Manual verification + tool execution.

### Details

```bash
# Verify override mode correction present
grep -c "override.*mode\|オーバーライド.*モード" docs/04_mcp_05_04_mdq-rag-boundary.md

# Verify no fallback statement present
grep -c "no.*fallback\|フォールバック.*しない" docs/04_mcp_05_04_mdq-rag-boundary.md

# Verify tool_transport_invoker reference present
grep -c "tool_transport_invoker" docs/04_mcp_05_04_mdq-rag-boundary.md

# Verify table structure intact
sed -n '/availability.*fallback/,/^$/p' docs/04_mcp_05_04_mdq-rag-boundary.md

# Run lint check
ruff check docs/04_mcp_05_04_mdq-rag-boundary.md
```

Expected outcomes:
- Third row of availability-fallback table corrected to reflect override mode behavior
- No implication of dedicated override mode availability check
- Clear distinction between prompt-level routing hints and tool-execution error handling
- Zero lint errors on the file
- Table structure preserved (no accidental restructuring)

## Validation plan

| Check | Tool | Target | Expected Outcome |
|---|---|---|---|
| Lint | `ruff check docs/04_mcp_05_*.md` | Docs files | 0 errors |
| Manual | Visual/Grep | Table content | Accurate description of override mode and error propagation |

## Out of scope

- Modifications to `scripts/rag/pipeline.py`, `scripts/mcp_servers/rag_pipeline/`.
- Modifications to any other documentation files.
- Adding new `.importlinter` contracts.

## Traceability

- Workflow phase: plan-to-implementation-procedure
- Source issue: N/A
- Source requirement: requires/20260802-153207_require.md
- Source plan: plans/20260805-123030_plan.md
- Source implementation procedure: N/A
- Generated at: 20260806-214227
- Related target files: docs/04_mcp_05_04_mdq-rag-boundary.md
