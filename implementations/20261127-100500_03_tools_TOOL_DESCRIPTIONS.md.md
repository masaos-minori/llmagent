## Goal
- Document the new tool in `tools/TOOL_DESCRIPTIONS.md` (`REQ-005`: Index row and Work Items row) so `tools/check_tool_descriptions_sync.py` passes.

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- Run after seq 01. The `tools/finalize_procedures.py` Plan adds its own rows to the same file; add separate rows, do not edit its lines. Verified in Step 3a: the `generate_workitem.py` row near line 139 is the nearest sibling for placement.

## Design decisions
- Index row Type `Work item`; Work Items row target `plans/*.md`.

## Alternatives considered
- N/A: single placement beside `generate_workitem.py`.

## Implementation
### Target file
`tools/TOOL_DESCRIPTIONS.md`

### Procedure
1. Index row: `generate_repeated_procedures.py | Work item | Write one implementation procedure per listed Plan row from one body template with {path}, {name}, {seq}, {timestamp} placeholders; refuses rows whose Change Responsibility differs`.
2. Work Items row: usage `generate_repeated_procedures.py <plan> --rows P [P ...] --body-template F [--dry-run] [--root R]`; the refusal cases (not a Plan row, duplicate, existing output including `done/`, `## Traceability` in the template, unknown placeholder, differing Change Responsibility after path and base-name substitution), that nothing is written on a refusal, the shared pass timestamp and row-position `seq` identical to `generate_workitem.py`, the appended Traceability block, the structure check result and exit codes 0/1/2, and that `stale_detector.py` is still required.

### Method
- Match neighboring rows' style; one line per row.

### Details
- State that the tool does not merge documents: one file per row.

## Compatibility considerations
- N/A: documentation row only.

## Security considerations
- N/A: no behavior change.

## Rollback considerations
- N/A: revert the commit.

## Validation plan
- `uv run python tools/check_tool_descriptions_sync.py` exits 0.

## Completion criteria
- Both rows exist and describe seq 01's behavior; the sync check passes.

## Out of Scope
- Gate definitions, `rules/tool-gates.md`, other tools' rows.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add the Index row and the Work Items row | Pending | — | — | |
| 2 | Run `uv run python tools/check_tool_descriptions_sync.py` | Pending | — | — | |

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
- **Requirement ID**: `REQ-005` (tool inventory)
- **Source issue**: issues/20261126-151442_wfeff007_repeated-row-procedures.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261127-095809_wfeff007_repeated-row-procedures.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261127-100500
- **Related target files**: `tools/TOOL_DESCRIPTIONS.md`
