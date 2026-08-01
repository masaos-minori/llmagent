# Fix port numbers, remove duplicate Mermaid diagram, and dedupe Allowed/Forbidden operation types (01_tool_ownership_matrix.md + 02_service_boundaries.md)

## Priority
High

## Summary
`docs/04_mcp_01_tool_ownership_matrix.md` and `docs/04_mcp_02_service_boundaries.md` both list MCP server ports, and confirmed cross-check against `config/agent.toml` shows every server except git-mcp (8014) has a wrong port number in both files. `01_tool_ownership_matrix.md` also duplicates its server/port/tool table as a Mermaid diagram (same information, separately maintained, also wrong). `02_service_boundaries.md`'s "Allowed/Forbidden operation types" section nearly duplicates the Ownership Matrix. Additionally, `file-mcp` is documented as a single server, but it is actually split into 3 servers (file-read-mcp/file-write-mcp/file-delete-mcp).

## Reason for Change
This is a confirmed factual error (verified against `config/agent.toml`), not speculation — 7 of 8 servers have wrong ports in both files, and the file-mcp split predates this documentation. An operator trusting this document would attempt to connect to the wrong port. The Mermaid diagram and the Allowed/Forbidden table are redundant maintenance burdens that doubled the drift.

## Implementation Intent
Stop hardcoding port numbers in prose; make `config/agent.toml`'s `[mcp_servers.*]` section (or `docs/01_overview-files-05-config.md`, once established as canonical per the related Overview/Architecture issue) the sole authority, with a reference note here instead of fixed values. Remove the duplicate Mermaid diagram, keeping the table as the single representation. Replace the Allowed/Forbidden operation types in `02_service_boundaries.md` with a reference to the Ownership Matrix. Update file-mcp's documented structure to reflect the actual 3-way split.

## Target Files or Areas
`docs/04_mcp_01_tool_ownership_matrix.md`, `docs/04_mcp_02_service_boundaries.md`

## Required Changes
- Remove fixed port-number values from both files' tables; replace with a note that `config/agent.toml`'s `[mcp_servers.*]` section is authoritative, and that as of the review date the previously-documented values did not match implementation for 7 of 8 servers.
- Remove the Mermaid diagram in `01_tool_ownership_matrix.md` (or, if a visual representation must be kept, annotate it as generated/do-not-hand-edit and derive it from the table).
- Replace `02_service_boundaries.md`'s "Allowed/Forbidden operation types" section with a reference link to the Ownership Matrix, keeping only the "Key Boundary Rules" section's unique design-intent content.
- Update file-mcp's description from a single server to the actual 3-server split (file-read-mcp/file-write-mcp/file-delete-mcp).

## Acceptance Criteria
Neither file contains a hardcoded port number without a canonical-source disclaimer; `01_tool_ownership_matrix.md` has no duplicate Mermaid diagram; `02_service_boundaries.md`'s Allowed/Forbidden section is a reference, not a duplicate table; file-mcp is documented as 3 servers.

## Testing Expectations
Not required (documentation-only). Manually verify current port assignments against `config/agent.toml`'s `[mcp_servers.*]` section and the actual `file-read-mcp`/`file-write-mcp`/`file-delete-mcp` server definitions before finalizing.

## Documentation Impact
Both files substantially corrected; establishes the reference pattern other MCP docs should follow for port numbers.

## Out of Scope
Do not change `config/agent.toml` in this issue. Do not consolidate MCP port documentation into `docs/01_overview-files-05-config.md` in this issue — that consolidation is tracked in the Overview/Architecture domain's own issue set.

## AI Implementation Instruction
Verify every port number against `config/agent.toml` directly before writing the replacement text — do not merely soften wording around the existing incorrect values.

## Traceability
- Workflow phase: issue-creation
- Source: docs_review_mcp.md §1 (全体評価 item 1), §2 削除候補 items 1-2, §5 例1, §6A (ポート番号)
- Generated at: 2026-08-02
