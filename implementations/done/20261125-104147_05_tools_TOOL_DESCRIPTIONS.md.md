## Goal
Update `tools/TOOL_DESCRIPTIONS.md` for the companion kinds: the two `check_workitem_structure.py` rows describe them, and a Shared-base row documents the new module so `check_tool_descriptions_sync.py` passes (`REQ-006`, `REQ-007`).

## Scope
**Release unit**: N/A: not part of a release unit

- Three edits: the overview-table row for `check_workitem_structure.py`, its detail-table row, and one new row for `tools/_workitem_companion_kinds.py`.

## Assumptions
- The two checker rows are the ones that start with `| \`check_workitem_structure.py\` |` (the overview table and the detail table, checked in Step 3a).
- The precedent for a private helper is the Shared-base rows of `_workitem_leftover_rules.py`, `_workitem_status_check.py`, and `_workitem_length_check.py`; the new row goes in that group, in alphabetical order before `_workitem_leftover_rules.py`.
- The behavior to describe is the one wired by the `seq` 02 procedure.

## Design decisions
- Overview row: add that companion documents (`issues/{timestamp}[_{seq}]_unknowns.md`, `_risks.md`) are verified for required sections against `templates/unknowns-issue.md` and `templates/risks-issue.md`.
- Detail row: add the two kinds to the template list, the `--kind` choices (`unknowns`, `risks`), and the note that `--kind issue` means ordinary Issues only.
- New row: `_workitem_companion_kinds.py`, Shared base, one sentence on the filename pattern and the template map, read by `check_workitem_structure.py`.

## Alternatives considered
N/A: documentation-only edits to existing rows.

## Implementation
### Target file
`tools/TOOL_DESCRIPTIONS.md`

### Procedure
1. Edit the overview-table row of `check_workitem_structure.py`.
2. Edit its detail-table row (kinds, `--kind` choices, companion behavior).
3. Add the Shared-base row for `_workitem_companion_kinds.py` before the `_workitem_leftover_rules.py` row.

### Method
Targeted edits of the three rows; keep the table column structure and the existing wording of unrelated sentences.

### Details
Keep the rows factual: filename forms, templates, required-section rule only, and the `--kind` change.

## Compatibility considerations
N/A: documentation only.

## Security considerations
N/A: documentation only.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run python tools/check_tool_descriptions_sync.py` (the new module needs its row) and `uv run python -m tools.run_validation_gates drift`.
- `uv run python tools/run_validation_gates.py` over the changed file.

## Completion criteria
- Both checker rows name the companion kinds and templates, the new module has a row, and the sync and drift checks pass.

## Out of Scope
- Rows of other tools; the CLI and Exit-Code Convention section.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Edit the two `check_workitem_structure.py` rows and add the module row | Completed | 20261125-105021 | 20261125-105030 | Changed: tools/TOOL_DESCRIPTIONS.md (two checker rows, new _workitem_companion_kinds.py row) |
| 2 | Run the sync and drift checks (`rules/tool-gates.md` "When to run which tool") | Completed | 20261125-105030 | 20261125-105030 | check_tool_descriptions_sync: no issues; drift: parity OK |

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
- **Requirement ID**: `REQ-006` (tool rows), `REQ-007` (sync check)
- **Source issue**: issues/20261125-091717_gate001_workitem-structure-companion-kinds.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261125-102213_gate001_workitem-structure-companion-kinds.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261125-104147
- **Related target files**: `tools/TOOL_DESCRIPTIONS.md`