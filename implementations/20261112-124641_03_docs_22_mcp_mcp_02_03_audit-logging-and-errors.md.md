## Goal
Merge the two `requested_target` rows of `mcp_02_03` into one row with the complete description (`REQ-001` / `AC-1`).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- Line numbers have drifted from the Plan; locate each passage by its quoted text, and skip and report it if it is already correct (Phase 1 rule).
- The rows differ: one says `emitted by git-mcp only`, the other says `captured before canonical path resolution; emitted only when the caller supplies it, mirroring the canonical_target pattern`. Keep both facts.
- Overlap: adrrev011 edits the audit-writing server list of this file (another passage); compatible.

## Design decisions
- Keep the row position of the first occurrence and delete the second.

## Alternatives considered
N/A: the Plan fixes the approach for this row.

## Implementation
### Target file
`docs/22_mcp/mcp_02_03_audit-logging-and-errors.md`

### Procedure
1. Write one row combining both descriptions.
2. Delete the other row.

### Method
- Row text: `Redacted caller-supplied target captured before canonical path resolution; emitted only when the caller supplies it, by git-mcp only, mirroring the canonical_target pattern`, with the Required `No` and Default `Omitted` cells unchanged.

### Details
- `rg -n 'requested_target' docs/22_mcp/mcp_02_03_*.md` shows one table row afterwards (other mentions in prose are fine).

## Compatibility considerations
N/A: documentation-only change; no code, config, or schema impact.

## Security considerations
N/A: no authorization, secret, or trust-boundary change.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run python tools/check_docs_consistency.py --domain mcp` — pass.
- `uv run python tools/check_docs_quality.py`, `check_docs_structure.py`, `check_docs_content_policy.py --strict`, `check_docs_japanese.py` — pass.
- `uv run python tools/check_needs_confirmation_inventory.py` — pass.

## Completion criteria
- One `requested_target` row remains with both facts.

## Out of Scope
- Other audit field rows.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Run the documentation checkers per Validation plan | Pending | — | — | |

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
- **Requirement ID**: `REQ-001` — merge the duplicated `requested_target` row
- **Source issue**: issues/20261109-113421_adrrev019_docs-stale-statements.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261111-112439_adrrev019_docs-stale-statements.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261112-124641
- **Related target files**: `docs/22_mcp/mcp_02_03_audit-logging-and-errors.md`
