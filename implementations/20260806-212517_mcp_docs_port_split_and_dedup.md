## Goal

Update MCP documentation to fix stale port numbers, correct service descriptions for split servers, and remove redundant elements.

## Scope

- **In-Scope**:
  - Update `docs/04_mcp_02_service_boundaries.md` with correct ports (aligning with `config/agent.toml`), replace `file-mcp` with three separate services (`file-read-mcp`, `file-write-mcp`, `file-delete-mcp`), and remove redundant tables by replacing them with references to `04_mcp_01_tool_ownership_matrix.md`.
  - Remove the redundant Mermaid diagram from `docs/04_mcp_01_tool_ownership_matrix.md`.
- **Out-of-Scope**:
  - Any modifications to `config/agent.toml`.
  - Modifications to application source code.

## Assumptions

1. `config/agent.toml` is the absolute source of truth for all MCP server ports.

## Design decisions

- Use reference notes for ports or corrected values consistent with the pattern used in `01_tool_ownership_matrix.md`.
- Treat the audit phase as a read-only discovery pass — no fixes during the audit.
- Use grep-based extraction for port mapping verification rather than TOML parsing.

## Alternatives considered

- Auto-generate docs from `config/agent.toml`: rejected because scope is limited to manual corrections.
- Keep Mermaid diagram but update values: rejected because plan explicitly calls for removal.

## Compatibility considerations

- Port numbers must exactly match `config/agent.toml` entries.
- Cross-references between docs must use existing Markdown conventions.

## Security considerations

N/A — documentation-only changes.

## Rollback considerations

- If port corrections are wrong, revert to git history before audit.
- If Mermaid diagram removal breaks downstream references, restore diagram section.

## Implementation

### Target file

`docs/04_mcp_02_service_boundaries.md`

### Procedure

1. Extract all port mappings from `config/agent.toml`.
2. Compare current doc content against extracted mappings.
3. Update per-server headings with correct ports or use reference notes.
4. Replace `file-mcp` section with three separate sections: `file-read-mcp`, `file-write-mcp`, `file-delete-mcp`.
5. Replace "Allowed/Forbidden operation types" subsections with a reference link to `04_mcp_01_tool_ownership_matrix.md`.

### Method

Direct file edit using sed or manual editing.

### Details

```bash
# Extract port mappings from config
grep -E '^\[.*\]|port\s*=' config/agent.toml

# Find file-mcp section boundaries
grep -n "file-mcp\|file_read\|file_write\|file_delete" docs/04_mcp_02_service_boundaries.md

# Find operation type subsections
grep -n "Allowed\|Forbidden\|operation type" docs/04_mcp_02_service_boundaries.md
```

Port correction pattern:
- For each server heading like `#### <server-name> (<port>)`, replace `<port>` with value from `config/agent.toml`.

File-mcp replacement:
- Replace single `file-mcp` section with three sections matching `01_tool_ownership_matrix.md` structure.

Operation types replacement:
- Replace entire "Allowed/Forbidden operation types" subsection with: `[See tool ownership matrix](04_mcp_01_tool_ownership_matrix.md)`

### Target file

`docs/04_mcp_01_tool_ownership_matrix.md`

### Procedure

1. Locate the Mermaid diagram section.
2. Remove the entire `## Mermaid Diagram` section including its content.

### Method

Direct file edit.

### Details

```bash
# Find Mermaid section boundaries
grep -n "Mermaid\|mermaid\|```mermaid" docs/04_mcp_01_tool_ownership_matrix.md
```

Remove section from `## Mermaid Diagram` header through end of mermaid code fence block.

### Target file

Verification

### Procedure

1. Manually verify every port number in `02_service_boundaries.md` matches its corresponding `[mcp_servers.*]` entry in `config/agent.toml`.
2. Confirm that `02_service_boundaries.md` no longer contains "Allowed/Forbidden operation types" tables but has a reference link instead.
3. Confirm that `01_tool_ownership_matrix.md` no longer contains the Mermaid diagram.

### Method

Manual verification + grep.

### Details

```bash
# Verify port corrections
grep -n "port\|Port\|PORT" docs/04_mcp_02_service_boundaries.md

# Verify file-mcp split
grep -n "file-read-mcp\|file-write-mcp\|file-delete-mcp" docs/04_mcp_02_service_boundaries.md

# Verify Mermaid diagram removed
grep -c "mermaid" docs/04_mcp_01_tool_ownership_matrix.md

# Verify cross-references exist
grep -n "04_mcp_01_tool_ownership_matrix" docs/04_mcp_02_service_boundaries.md
```

Expected outcomes:
- All port numbers in `02_service_boundaries.md` match `config/agent.toml`
- Three separate `file-*` sections present instead of single `file-mcp`
- Zero occurrences of "mermaid" in `01_tool_ownership_matrix.md`
- Cross-reference link to `04_mcp_01_tool_ownership_matrix.md` present in `02_service_boundaries.md`

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `docs/04_mcp_02_service_boundaries.md` | Manual inspection vs `config/agent.toml` | `cat` / `grep` | Correct ports, split servers, no redundant tables |
| `docs/04_mcp_01_tool_ownership_matrix.md` | Manual inspection | `cat` / `grep` | Mermaid diagram removed, table remains intact |

## Out of scope

- Modifications to `config/agent.toml`.
- Modifications to application source code.
- Changes to any other documentation not listed above.

## Traceability

- Workflow phase: plan-to-implementation-procedure
- Source issue: N/A (Requirement refers to `issues/20260802-075026_mcp_ownership_matrix_port_and_dedup.md`)
- Source requirement: requires/20260802-152611_require.md
- Source plan: N/A
- Source implementation procedure: N/A
- Generated at: 20260806-212517
- Related target files: docs/04_mcp_01_tool_ownership_matrix.md, docs/04_mcp_02_service_boundaries.md
