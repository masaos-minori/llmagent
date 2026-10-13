## Goal
- Remove Known Issue MCP-001 (inventory row and entry) once the five servers verify the token; the governance inventory keeps no resolved items (REQ-007).

## Scope
- In: the MCP-001 row of the Active Items table and the `#### MCP-001` entry.
- Out: every other entry and any size-ceiling change.

## Assumptions
- Apply only after Steps 3-7 pass (rows 1-15 and 29-31 done), so the Known Issue is actually resolved.
- The only other references to MCP-001 are in `docs/10_adr/adr_02_007_http-mcp-adoption-and-stdio-non-support.md` and `docs/10_adr/adr_01_index.md` (rows 33 and 34).

## Design decisions
- Delete, do not mark resolved (the inventory states that an item is removed once resolved).

## Alternatives considered
N/A: removal is the inventory's rule.

## Implementation
### Target file
`docs/00_governance/governance_03_issue-and-uncertainty-management.md`

### Procedure
1. Delete the table row.
2. Delete the entry from its heading up to (not including) the `#### DEPLOY-001` heading.
3. Run the checkers.

### Method
- The entry spans the heading `#### MCP-001` (line 308) to the blank line before `#### DEPLOY-001` (line 328); keep exactly one blank line before `#### DEPLOY-001`.
- The file only shrinks, so its size ceiling in `tools/check_docs_structure.py` is not a concern.

### Details
Table row (Before/After):

```markdown
# Before:
| MCP-001 | The shell, github, and file MCP servers register no Bearer-token authentication middleware | open | High | MCP | implementation-bug |
# After:
```

Entry: remove these lines, beginning with `#### MCP-001` and ending with the line `- **Resolution Target**: Every MCP server verifies the Bearer token, or ADR-007 lists the exceptions explicitly.`, plus the blank line that follows it.

## Compatibility considerations
- Row and entry only; other IDs are unchanged and stay valid.

## Security considerations
N/A: documentation.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run python tools/check_issue_inventory_conformance.py`, `uv run python tools/check_known_deviation_sync.py`, `uv run python tools/check_docs_structure.py`, `uv run python tools/check_docs_quality.py`, `uv run python tools/check_needs_confirmation_inventory.py`.
- `rg "MCP-001" docs/` returns nothing after rows 32-34 are applied.

## Completion criteria
- No `MCP-001` text remains in `docs/`; the checkers pass.

## Out of scope
- Other Known Issues and the size ceiling.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Remove the MCP-001 row and entry | Pending | — | — | Plan Step 8; after Steps 3-7 |
| 2 | Run the documentation checkers named in `routing.md` | Pending | — | — |  |

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
- **Requirement ID**: `REQ-007` (documentation matches the new behavior: Known Issue MCP-001 removed)
- **Source issue**: issues/20261013-113008_mcp007_register-bearer-auth-in-shell-github-file-mcp-servers.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261013-120538_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261013-123717
- **Related target files**: docs/00_governance/governance_03_issue-and-uncertainty-management.md
