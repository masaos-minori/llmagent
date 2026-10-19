## Goal
Register `manage_binaries.py` in the tool descriptions so the tool-description sync check passes (`REQ-003`).

## Scope
- One new table row in the existing tool table.

## Assumptions
- The row is placed next to related deploy or consistency tools in the existing table and follows its column format.

## Design decisions
- Use the one-sentence style of neighboring rows; do not describe options.

## Alternatives considered
N/A: one row.

## Implementation
### Target file
`tools/TOOL_DESCRIPTIONS.md`

### Procedure
1. Add the row.
2. Run the sync check.

### Method
- Row: `| manage_binaries.py | Deploy | Write build info for the Nuitka binaries, check their freshness against a source revision, swap a staged set into the bin directory with a saved previous set, roll back, and record the deployed revision |`.

### Details
- Keep the column count identical to the other rows.

## Compatibility considerations
N/A: documentation only.

## Security considerations
N/A: documentation only.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run python tools/check_tool_descriptions_sync.py`
- `uv run python tools/check_docs_quality.py`

## Completion criteria
- The row exists and `check_tool_descriptions_sync.py` passes.

## Out of scope
- Any other row
- `routing.md` (the tool is called by deploy scripts, not at an AI trigger point)

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add the table row | Pending | — | — | |
| 2 | Run `tools/check_tool_descriptions_sync.py` | Pending | — | — | |

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
- **Requirement ID**: `REQ-003` (register the tool)
- **Source issue**: issues/20261019-103807_deploybin001_binary-freshness-and-rollback-in-deploy.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261019-104249_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261019-105818
- **Related target files**: tools/TOOL_DESCRIPTIONS.md
