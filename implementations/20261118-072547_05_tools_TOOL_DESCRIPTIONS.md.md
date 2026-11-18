# Procedure: tools/TOOL_DESCRIPTIONS.md - leftover rows and the helper module row

## Goal

Describe in the tool documentation that the structure checker's leftover cover now spans issues, plans, and procedures, name the rules, and register the new helper module.

## Scope
**Release unit**: N/A: not part of a release unit

- Update the two `check_workitem_structure.py` rows (the summary-table row and the detailed reference-table row) to state the plan and procedure leftover rules. (REQ-005)
- Add a Shared base row for `tools/_workitem_leftover_rules.py` in the helper-module table. (REQ-005)

## Assumptions

- The checker's command-line surface is unchanged by this Plan, so `check_tool_descriptions_sync.py` compares option text only; the edits are prose and one new table row. (Verified 20261118 against the current rows.)
- The helper-module table already carries `_workitem_*` and other `_`-prefixed shared base rows, so the new row follows the same three-column shape (`| module | Shared base | role |`). (Verified 20261118.)

## Design decisions

- State each kind's rule set explicitly in the detailed row (issues: verbatim issue-template lines; plans: whole-value `{...}` Traceability values, all-empty table rows, run-time-derived plan-fence bracket lines; procedures: the first two) and compress the same statement into the summary row, so both rows agree with the routing row written by the sibling procedure document.
- Land these edits after the checker wiring procedure (`implementations/20261118-072547_02_tools_check_workitem_structure.py.md`) and re-read both rows first: `tools/TOOL_DESCRIPTIONS.md` is edited at row level by three sibling Plans of this batch (UNK-03 ordering).

## Alternatives considered

- Describe the rules only in the detailed row. Rejected: the summary row is what a tool picker reads first, and REQ-005 names the rules for the tool description as a whole.
- Register the helper module only in `routing.md`. Rejected: `routing.md` registers checkers/commands, not shared base modules; the descriptions file's helper table is where the sibling `_workitem_*` modules are documented.

## Implementation

### Target file

`tools/TOOL_DESCRIPTIONS.md` (exists)

### Procedure

1. In the summary-table row for `check_workitem_structure.py`, replace the issue-only leftover clause with the three-kind statement and keep the `--archived-status` clause.
2. In the detailed reference-table row, replace the "for an issue it additionally reports..." sentence with the per-kind rule statements of the Design decisions, including that the plan bracket set is derived from `templates/plan.md` at run time and that archived files are not scanned by this rule.
3. Add the Shared base row for `_workitem_leftover_rules.py`: the plan and procedure leftover rules the structure checker calls (whole-value `{...}` Traceability placeholders, all-empty table rows, plan-fence bracket lines derived at run time).
4. Run the sync checker.

### Method

Targeted cell edits; read the current rows first (sibling Plans may have moved neighboring rows).

### Details

- Keep each row a single Markdown table row (no embedded newlines), matching the file's existing rows.

## Compatibility considerations

- Documentation-only; readers get corrected coverage wording. The rows must describe the shipped checker, so they land after the wiring procedure.

## Security considerations

- None beyond keeping the Markdown table structure intact for the checkers.

## Rollback considerations

- Reverting this file restores the previous rows and removes the helper row; no runtime state.

## Validation plan

- `uv run python tools/check_tool_descriptions_sync.py` reports no finding.
- `uv run python tools/check_workitem_structure.py --file <this file>` is not applicable (the descriptions file is not a work item); consistency is judged by the sync checker.

## Completion criteria

- AC-5: both checker rows state the three kinds and name the rules, the helper module row exists, and the sync checker passes.

## Out of Scope

- Rows of other tools owned by sibling Plans of this batch.
- The checker's module docstring and `--help` text (owned by the checker procedure document).

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
- **Requirement ID**: REQ-005
- **Source issue**: issues/20261117-132204_wftoolfu004_plan-leftover-detection.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261117-134334_wftoolfu004_plan-leftover-detection.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261118-072547
- **Related target files**: `tools/TOOL_DESCRIPTIONS.md`
