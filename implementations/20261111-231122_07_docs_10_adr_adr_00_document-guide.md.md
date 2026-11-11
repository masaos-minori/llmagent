## Goal

Add ADR-017 to the document guide's ADR enumeration in `adr_00_document-guide.md` (`REQ-004`, `AC-4`).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- Line 61 states ADR-011 is unassigned and enumerates the ADR list; ADR-017 is added in number order alongside the other MCP-group ADRs.

## Design decisions
- Add one enumerated entry for ADR-017 to match the existing per-ADR entries; do not renumber or reorder.

## Alternatives considered
- Regenerating the guide from a tool: the enumeration is hand-maintained in this guide. Rejected: edit the enumeration directly.

## Implementation
### Target file
`docs/10_adr/adr_00_document-guide.md`

### Procedure
1. Add an ADR-017 entry to the ADR enumeration (after the ADR-016 entry), matching the existing entry format.

### Method
- One-line addition to the enumeration; verify with `tools/check_docs_structure.py`.

### Details
- The guide still records ADR-011 as unassigned; that fact is unchanged.

### Companion test files
N/A.

## Compatibility considerations
- N/A: guide enumeration.

## Security considerations
- N/A: documentation guide.

## Rollback considerations
Revert the commit.

## Validation plan
| Target | Strategy | Command | Expected |
|---|---|---|---|
| `adr_00_document-guide.md` | Structure | `uv run python tools/check_docs_structure.py` | Pass |

## Completion criteria
- ADR-017 is enumerated in the document guide.

## Out of Scope
- Any other document-guide change.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add the ADR-017 entry to the ADR enumeration | Pending | — | — | |
| 2 | Run `check_docs_structure.py` (`rules/toolchain.md`) | Pending | — | — | |

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
- **Requirement ID**: `REQ-004` — ADR-017 registered in the ADR document guide.
- **Source issue**: issues/20261109-113023_adrrev011_mcp-audit-auth-adr.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261111-095422_adrrev011_mcp-audit-auth-adr.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261111-231122
- **Related target files**: `docs/10_adr/adr_00_document-guide.md`
