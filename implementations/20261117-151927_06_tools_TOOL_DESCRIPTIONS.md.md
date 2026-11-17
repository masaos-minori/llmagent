## Goal

Update the `check_workitem_structure.py` entries of `tools/TOOL_DESCRIPTIONS.md` to describe the multi-path `--file` and the issue template-leftover check (REQ-006 / AC-8).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions

- The tool appears in two table sections of the file (verified 20261117, near lines 113 and 184); both entries must be updated in one pass because `tools/check_tool_descriptions_sync.py` compares them against the tool.
- Five sibling Plans of the batch also target this file (row-level edits, highest-churn file of the plan); the batch runs one Plan at a time and this edit touches only the two `check_workitem_structure.py` rows.

## Design decisions

N/A: documentation rows; wording follows the REQ-001 and REQ-002 contracts without restating the Plan text.

## Alternatives considered

N/A: single documented location; there is no second description file to keep in sync.

## Implementation
### Target file
`tools/TOOL_DESCRIPTIONS.md`

### Procedure

- In both table rows for `check_workitem_structure.py`, state that `--file` accepts one or more paths and that issue documents are additionally checked for verbatim `templates/issue.md` leftovers reported as `template-leftover`; keep the existing `--archived-status` wording untouched.

### Method

N/A: two row edits in place.

### Details

- Land after the seq 01 document so the described behavior exists.

## Compatibility considerations

N/A: documentation rows; the sync checker reads them.

## Security considerations

N/A: documentation rows.

## Rollback considerations

N/A: revert the commit.

## Validation plan

- `uv run python tools/check_tool_descriptions_sync.py` reports no finding (AC-8).

## Completion criteria

- AC-8: the sync check passes and both entries name the multi-path `--file` and the leftover check.

## Out of Scope

- Rows of other tools; the checker code, gate, hook, routing row (other documents of this plan).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Update the two table rows | Pending | — | — | |
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
- **Requirement ID**: `REQ-006` (tool description names the changed flag and the new check)
- **Source issue**: `issues/20261117-123330_wftool001_gate-workitem-structure.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261117-124139_wftool001_gate-workitem-structure.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261117-151927
- **Related target files**: `tools/TOOL_DESCRIPTIONS.md`
