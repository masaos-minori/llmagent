## Goal
Describe the Status value check, the new baseline, and the new helper module in `tools/TOOL_DESCRIPTIONS.md`, so the tool documentation matches the tool after the Plan lands.

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- UNK-03 of the Plan: several Plans of this batch edit rows of this file. Re-read the current text of the checker rows and the shared-base table before editing, and touch only the named rows.
- The checker behavior and baseline are the ones landed by `implementations/20261118-050931_03_tools_check_workitem_structure.py.md` and `implementations/20261118-050931_07_tools_check_status_value_baseline.txt.md`.

## Design decisions
- Summary table: extend the `check_workitem_structure.py` row with the `status-value` category and the archived-plan coverage, in the row's existing compressed style.
- Detail table: extend the long `check_workitem_structure.py` entry the same way — `--file` and the directory scan judge plan and procedure Status values against the vocabulary; `--archived-status` reports unfinished rows (existing baseline) and out-of-vocabulary values of archived procedures and plans (new baseline `tools/check_status_value_baseline.txt`), and its hook trigger covers `plans/done/` too.
- Shared-base table: add one row for `_workitem_status_check.py` beside the `_workitem_status_table.py` row, in the same one-line style: the Status value rule read by `check_workitem_structure.py`.

## Alternatives considered
- Documenting the helper module only inside the checker's entry: rejected by the Plan row ("add the helper module row") — the shared-base table lists every `_workitem_*` helper one row per module, and the sync checker compares rows against the tools directory.

## Implementation
### Target file
`tools/TOOL_DESCRIPTIONS.md`

### Procedure
1. Edit the summary and detail entries of `check_workitem_structure.py` per Design decisions.
2. Add the `_workitem_status_check.py` row to the shared-base table.
3. Run the sync checker and confirm the file matches the tools on disk.

### Method
Three row edits/additions; every other row stays byte-identical.

### Details
- Wording must match the landed behavior exactly (category names `status-value`, both baseline file paths, the widened hook trigger) — the sync checker proves coverage, not wording; wording accuracy is reviewed against the checker procedure's Completion criteria.

## Compatibility considerations
- The file has very high churn; row-level discipline per UNK-03 prevents clobbering other Plans' rows.

## Security considerations
Not applicable: documentation-only change.

## Rollback considerations
Restore the two checker rows and delete the helper row together.

## Validation plan
- `uv run python tools/check_tool_descriptions_sync.py` — no finding (AC-6).

## Completion criteria
- The summary row, the detail entry, and the new shared-base row exist and describe the landed behavior; the sync checker passes.

## Out of Scope
- Entries of other tools; the routing table (sibling procedure).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | |

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
- **Requirement ID**: REQ-006
- **Source issue**: issues/20261117-132201_wftoolfu001_workitem-status-vocabulary.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261117-133851_wftoolfu001_workitem-status-vocabulary.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261118-050931
- **Related target files**: `tools/TOOL_DESCRIPTIONS.md`
