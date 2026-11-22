## Goal

Replace the shared-`mcp_dedup.toml` ownership description with the per-server `[dedup]` ownership map, and document the `identity_mismatch` refusal state and its config-correction recovery (REQ-010).

## Scope
**Release unit**: N/A: not part of a release unit (Phase 5 documentation row)

## Assumptions
- The code-side changes (seqs 01-26) define the documented contract; docs describe the post-Phase-4 state, not a migration window.

## Design decisions
- One ownership statement per bullet: each `*_mcp_server.toml` owns its `[dedup]` table; the store remains one shared database; the `[retry_class]` mirror is removed and `retry_policy` tool metadata is the sole retry-class authority.
- Recovery note for `identity_mismatch`: adjust the server's `[dedup]` values (never the store); archive-and-recreate via `resolve_store` stays the last resort.

## Alternatives considered
- N/A: documentation-only row.

## Implementation
### Target file
`docs/41_db/db_03_07_mcp-dedup-and-execution-snapshot.md`
### Procedure
1. Update every reference listed under Goal to the post-change contract; preserve surrounding structure, tone, and English language per `skills/DESIGN.md` Output language.
### Method
In-place text edits; no generated-block hand edits (per docs governance).
### Details
- Exact mention sites are found by `rg 'mcp_dedup'` within the file at implementation time.

## Compatibility considerations
- Stale-doc risk is covered by the consumption checker below; no code coupling.

## Security considerations
- N/A: documentation only.

## Rollback considerations
- N/A: revert the commit.

## Validation plan
- `uv run python tools/check_docs_links.py` and `uv run python tools/check_docs_consumption.py` (per `rules/tool-gates.md` for `docs/` edits).

## Completion criteria
- No stale claim about the shared file or the `[retry_class]` mirror remains in `db_03_07_mcp-dedup-and-execution-snapshot.md`; checkers exit 0.

## Out of Scope
- Status/approval statements in ADRs (issue Constraint); other documents' content (sibling rows).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Update the document per Implementation | Pending | — | — | |
| 2 | Run the documentation checkers (`tools/check_docs_links.py`, `tools/check_docs_consumption.py`) | Pending | — | — | |

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
- **Requirement ID**: REQ-010; AC-007
- **Source issue**: issues/20261120-115842_mcpdl003_dedup-config-isolation.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261121-172154_mcpdl003_dedup-config-isolation.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261122-192909
- **Related target files**: `docs/41_db/db_03_07_mcp-dedup-and-execution-snapshot.md`
