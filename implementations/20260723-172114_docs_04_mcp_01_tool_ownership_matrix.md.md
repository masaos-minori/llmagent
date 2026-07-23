## Goal

Create MCP Tool Ownership Matrix, Service Boundaries, and Capability Mapping Documentation to provide a single canonical view of which tool belongs to which MCP server.

## Scope

**In:**
- `docs/04_mcp_01_tool_ownership_matrix.md` (new): Canonical tool-to-MCP-server mapping table
- `docs/04_mcp_02_service_boundaries.md` (new): Per-server responsibility/non-responsibility definitions
- `docs/04_mcp_00_document-guide.md`: Update to link to new documents

**Out:**
- Any runtime behavior changes
- Modifying existing MCP documentation files beyond updating the index/guide

## Assumptions

1. The authoritative source for tool names is `scripts/shared/tool_constants.py` — confirmed by reading the file.
2. All 10 MCP servers listed in the requirement exist and have been validated against the tool constants.
3. Risk tiers follow existing classifications: READ_TOOLS → LOW, WRITE_TOOLS → MEDIUM, DELETE_TOOLS → HIGH, GITHUB_DANGEROUS_TOOLS → HIGH, CICD_WRITE_TOOLS → HIGH.
4. Approval requirements follow existing `cfg.approval.tool_safety_tiers` logic — high-risk tools require approval, low-risk tools do not.
5. Typical workflow stages: plan → READ_TOOLS, execute → WRITE_TOOLS, verify → READ_TOOLS.

## Design decisions

- Use markdown tables for the ownership matrix — GitHub-compatible and easy to maintain.
- Include Mermaid diagrams for visual representation of ownership and dependencies.
- Mark ambiguous or unknown tool ownership as `Unknown`, never guess.
- Follow existing MCP documentation conventions (check existing files like `04_mcp_04_01_web-search-file-read-github.md` for style consistency).

## Alternatives considered

- Single monolithic document instead of two separate ones: harder to navigate, but easier to keep in sync.
- JSON/YAML data files with generated Markdown: more structured, but harder for developers to edit directly.
- Embed ownership info in tool registry code: couples documentation to implementation, violates separation of concerns.

## Implementation

### Target file

`docs/04_mcp_01_tool_ownership_matrix.md`, `docs/04_mcp_02_service_boundaries.md`, `docs/04_mcp_00_document-guide.md`

### Procedure

1. Create `docs/04_mcp_01_tool_ownership_matrix.md` with tool ownership matrix
2. Create `docs/04_mcp_02_service_boundaries.md` with service boundary definitions
3. Update `docs/04_mcp_00_document-guide.md` to include links to new documents

### Method

Create two new documentation files and update an existing document guide.

### Details

**Phase 1: Create Tool Ownership Matrix**

Create `docs/04_mcp_01_tool_ownership_matrix.md` with:
- Markdown table with columns: Tool Name, Owning MCP Server, Capability Group, Risk Tier, Approval Required, Typical Workflow Stage, Notes
- All 60+ tools mapped to their owning MCP server using `tool_constants.py` as the authoritative source
- Mermaid diagram showing tool-to-MCP ownership relationships

**Phase 2: Create Service Boundary Definitions**

Create `docs/04_mcp_02_service_boundaries.md` with:
- For each of the 10 MCP servers: Responsibilities, Explicit non-responsibilities, Allowed operation types, Forbidden operation types, Ownership rationale
- Key boundary rules documented (local vs remote Git, file operations, RAG vs MDQ)
- Mermaid diagram showing capability-to-MCP dependencies

**Phase 3: Update Document Guide/Index**

Update `docs/04_mcp_00_document-guide.md` to include links to the new documents.

## Compatibility considerations

N/A — documentation-only task, no runtime impact.

## Security considerations

N/A — documentation-only task, no security impact.

## Rollback considerations

Simple revert of documentation additions; no data migration or config changes required.

## Validation plan

| Target File/Module | Testing Strategy | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| docs/04_mcp_01_tool_ownership_matrix.md | Manual review | Read file, verify against `tool_constants.py` | All tools mapped correctly, no ambiguities |
| docs/04_mcp_02_service_boundaries.md | Manual review | Read file, verify against `tool_constants.py` | All servers have boundaries defined |
| docs/04_mcp_00_document-guide.md | Manual review | Read file, check links | New documents linked |
| Mermaid diagrams | Render test | Paste into GitHub Markdown preview | Diagrams render correctly |

## Out of scope

- Any runtime behavior changes
- Modifying existing MCP documentation files beyond updating the index/guide

## Traceability

- Workflow phase: plan-to-implementation-procedure
- Source issue: N/A
- Source requirement: N/A
- Source plan: plans/20260723-151933_plan.md
- Source implementation procedure: N/A
- Generated at: 20260723-172114
- Related target files: docs/04_mcp_01_tool_ownership_matrix.md, docs/04_mcp_02_service_boundaries.md
