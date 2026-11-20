## Goal

- State the new identifier rule in the two `check_known_deviation_sync.py` rows (`REQ-010`).

## Scope
**Release unit**: N/A: not part of a release unit

- Plan step 6. Fallout required by `AGENTS.md` Global Rule 9. Execute after the checker rule landed; add the scripts rule when Plan step 7 lands.

## Assumptions

- Only the rule that landed is described; the pending adrchk013 procedure edits other rows of this file (compatible overlap, Plan Assumption A1).

## Design decisions

- Extend the existing sentences of both rows; add no row.

## Alternatives considered

N/A: a text edit; the Plan fixes the change.

## Implementation
### Target file
`tools/TOOL_DESCRIPTIONS.md`
### Procedure
1. In the tool list row, add that an `UNK-` or `NC-` identifier cited in an ADR must resolve to exactly one `governance_03` heading.
2. In the detailed row, add it as a further `ERROR` check next to (c).
### Method
- Direct text edit of two rows.
### Details
- Keep the row structure, the `GV-022` mention, and the `--format json` remark.

## Compatibility considerations

N/A: documentation row; no decision text changes.

## Security considerations

N/A: documentation row.

## Rollback considerations

N/A: revert the commit.

## Validation plan

- `uv run python tools/check_tool_descriptions_sync.py`, `uv run python tools/check_docs_quality.py`.

## Completion criteria

- Both rows describe the landed rule and the sync check passes (AC-7).

## Out of Scope

- Other tools' rows.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Update the two rows (Plan step 6) | Pending | — | — | After the checker procedure |
| 2 | Run the validation sequence for this row (Validation plan) | Pending | — | — | |

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
- **Requirement ID**: `REQ-010` (tool description)
- **Source issue**: issues/20261117-123012_adrchk012_traceability-id-uniqueness.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261120-124329_adrchk012_traceability-id-uniqueness.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261120-125111
- **Related target files**: `tools/TOOL_DESCRIPTIONS.md`
