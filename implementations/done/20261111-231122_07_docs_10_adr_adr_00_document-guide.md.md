## Goal

Add ADR-017 to the document guide's ADR enumeration in `adr_00_document-guide.md` (`REQ-004`, `AC-4`).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- (Corrected during adversarial verification, 2026-11-12: the guide has no per-ADR enumeration line at line 61 and no "ADR-011 is unassigned" statement — that statement lives in `adr_01_index.md` line 61. The guide's ADR enumeration is the `Reading Order` table, lines 27-44, plus the group registry table, lines 55-63.) ADR-017 is added in number order to both tables.

## Design decisions
- Add one `Reading Order` row for ADR-017 after the ADR-012 row (number order) and extend the group registry `03 mcp` row `007, 012` to `007, 012, 017`; do not renumber or reorder.

## Alternatives considered
- Regenerating the guide from a tool: the enumeration is hand-maintained in this guide. Rejected: edit the enumeration directly.

## Implementation
### Target file
`docs/10_adr/adr_00_document-guide.md`

### Procedure
1. Add a `Reading Order` table row `| MCP Authentication | `adr_02_03_017_mcp-authentication.md` |` after the `Git MCP Server-Side Write` row (ADR-012), matching the existing row format.
2. Extend the group registry row `| 03 | mcp | 007, 012 |` to `| 03 | mcp | 007, 012, 017 |`.

### Method
- Two-line addition to the two enumeration tables; verify with `tools/check_docs_structure.py`.

### Details
- The guide carries no ADR-011 statement (the unassigned-number note is in `adr_01_index.md`); nothing to update there.

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
| 1 | Add the ADR-017 entry to the ADR enumeration | Completed | — | 20261112-050137 | Reading Order row + group registry 007, 012, 017; row appended in true number order (after ADR-016), procedure line-placement note stale |
| 2 | Run `check_docs_structure.py` (`rules/toolchain.md`) | Completed | — | 20261112-050137 | check_docs_structure green after re-recording 4 size ceilings (adr_007 25606; pre-existing adr_004 33944, adr_008 36197, deployment_01 27339) |

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