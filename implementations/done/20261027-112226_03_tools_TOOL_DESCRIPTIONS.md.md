## Goal

Update the two `check_adr_invariant_matrix.py` entries of `tools/TOOL_DESCRIPTIONS.md` to describe the new rules (`REQ-006`: catalog update, sync check passes).

## Scope

- Edit the summary-table row and the detail-table row of `check_adr_invariant_matrix.py` only; leave every other row, including the `check_compat_shims.py` rows that `plans/20261027-110516_mcpcompat001_remove-mcp-compat-paths.md` edits.

## Assumptions

- Row 01 is applied first so the description matches the implemented rules and severity.
- Step 3a evidence: the summary row reads "Verify that test node IDs in the ADR Invariant Verification Matrix exist"; the detail row describes only the index `Verification Status` column.
- Overlap with `plans/20261027-110516_mcpcompat001_remove-mcp-compat-paths.md` (same file, different rows): compatible; rebase in turn and re-run the sync check after any sync.
- Plan overlap check for the other two target files: none.

## Design decisions

- Keep the summary row to one clause and put the rule details (empty body cell, body/index disagreement, `WARNING` severity) in the detail row.

## Alternatives considered

N/A: documentation-only catalog edit.

## Implementation
### Target file

`tools/TOOL_DESCRIPTIONS.md`

### Procedure

1. Locate both rows (`rg -n "check_adr_invariant_matrix" tools/TOOL_DESCRIPTIONS.md`).
2. Extend the summary row to say it also reports empty ADR body evidence cells and body/index disagreements.
3. Extend the detail row with the two rules, that both report `WARNING` (exit code unchanged), and that the existing index-path rule stays an `ERROR`.

### Method

Exact-string edits on the two rows; keep the table column structure.

### Details

- Describe behavior only, with no line numbers and no counts of findings.

## Compatibility considerations

N/A: documentation only.

## Security considerations

N/A: no secret or credential is involved.

## Rollback considerations

N/A: revert the commit.

## Validation plan

- `uv run python tools/check_tool_descriptions_sync.py` (`routing.md` "When to run which tool").

## Completion criteria

- Both rows describe the new rules and their severity, and `check_tool_descriptions_sync.py` passes.

## Out of Scope

- Any other catalog row; any change to the tool itself (row 01).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Update the two catalog rows | Completed | 20261027-123411 | 20261027-123429 | After row 01 Changed: tools/TOOL_DESCRIPTIONS.md (summary row and detail row of check_adr_invariant_matrix.py). Stale detector clean. |
| 2 | Run `check_tool_descriptions_sync.py` | Completed | 20261027-123429 | 20261027-123429 | check_tool_descriptions_sync.py: No issues found. |

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
- **Requirement ID**: `REQ-006` (catalog entries updated)
- **Source issue**: issues/20261027-102002_govrev005_adr-matrix-checker-extension.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261027-105004_govrev005_adr-matrix-checker-extension.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261027-112226
- **Related target files**: tools/TOOL_DESCRIPTIONS.md