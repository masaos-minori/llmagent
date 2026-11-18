## Goal
Keep the two `check_adr_structure.py` rows in sync with the new checks (fallout of REQ-009 and REQ-010).

## Scope
**Release unit**: N/A: not part of a release unit
- The two table rows that describe `check_adr_structure.py`.

## Assumptions
- Fallout file: it is outside the Issue's Target Files list and is reported to the owner as a scope amendment.
- The file has the highest churn of the targets; edit only the two rows.

## Design decisions
- Extend each row's check list with (e) Status value and (f) pending-form ledger ID, in the existing lettering style.

## Alternatives considered
N/A: single row edit.

## Implementation
### Target file
`tools/TOOL_DESCRIPTIONS.md`
### Procedure
In the short row add the Status value and pending-form checks; in the detailed row add (e) and (f) with their severities (Error).
### Method
Edit the two rows in place; leave every other row untouched.
### Details
- Find the rows by the tool name in the first column; do not rely on line numbers.

## Compatibility considerations
N/A: description-only.

## Security considerations
N/A: documentation-only change.

## Rollback considerations
N/A: revert the commit

## Validation plan
- `uv run python tools/check_tool_descriptions_sync.py`
- `uv run python tools/check_docs_quality.py`, `uv run python tools/check_docs_structure.py`, `uv run python tools/check_docs_content_policy.py`, `uv run python tools/check_docs_japanese.py`

## Completion criteria
- Both rows list the new checks and `tools/check_tool_descriptions_sync.py` reports no finding.

## Out of Scope
- Editing any other tool row.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Confirm the checker procedure (row 16) is done | Pending | — | — | Stop if not |
| 2 | Edit the two rows | Pending | — | — |  |
| 3 | Run `tools/check_tool_descriptions_sync.py` | Pending | — | — |  |

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
- **Requirement ID**: `REQ-009`: Status value check; `REQ-010`: pending-form check (description sync)
- **Source issue**: issues/20261117-123011_adrchk011_adr-approval-governance.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261118-092611_adrchk011_adr-approval-governance.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261118-093859
- **Related target files**: `tools/TOOL_DESCRIPTIONS.md`
