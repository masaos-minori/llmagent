## Goal

Record the document map of the MCP design documents in the MCP document guide so that every
server issue updates the right file (REQ-007, AC-5).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- The Issue's map is taken as the assignment basis; each assignment is confirmed against the
  file's actual content during execution (Plan Assumption, Unknowns UNK-02).
- Map completeness is recorded, not proven (AC-5 covers recording only).

## Design decisions
- The map is recorded in this guide, the file-index document, not in a new file.
- Assignments are stated by file title with the responsibility each file owns, matching the
  guide's existing table style.

## Alternatives considered

N/A: the guide is the canonical file-index document for the area; no alternative location.

## Implementation
### Target file
`docs/22_mcp/mcp_00_document-guide.md`
### Procedure
- Add a document-map section that assigns each MCP design document its update responsibility
  (dispatch and routing, audit logging, per-server sections, risk tiers, MDQ boundary and
  enforcement, tracing), confirming each assignment against the file's content.
### Method
- Read the guide's existing file index, then add the map as one table: file, responsibility,
  and the server-issue scope each file owns.
### Details
- The guide currently has no document map (verified 20261126); the existing file index stays
  and the map is added without duplicating it.

## Compatibility considerations

N/A: documentation-only change; the map has no code consumers (Plan Design, Predictable fallout).

## Security considerations

N/A: no security behavior is described beyond pointing to the existing policy documents.

## Rollback considerations

N/A: revert the commit.

## Validation plan

- `uv run python tools/check_docs_quality.py`
- `uv run python tools/check_docs_structure.py` (front matter, related lists, link reachability)

## Completion criteria

- The map names every MCP design document in the Plan's target table with its update
  responsibility, and every assignment matches the file's content.

## Out of Scope

- No other `docs/` file is modified; the governance file is referenced, not edited.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261126-234310 | 20261126-234310 | Document map section added to docs/22_mcp/mcp_00_document-guide.md covering the MCP document set and its cross-links. |
| 3 | Run the docs checkers (`rules/tool-gates.md`) | Completed | 20261126-234310 | 20261126-234310 | docs checkers pass (quality, structure, content policy, consistency --domain mcp) |

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
- **Requirement ID**: `REQ-007` (record the MCP document map)
- **Source issue**: issues/20261119-140519_mcpai012_mcp-design-docs-update.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261126-072155_mcpai012_mcp-design-docs-update.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261126-212443
- **Related target files**: `docs/22_mcp/mcp_00_document-guide.md`