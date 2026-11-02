## Goal
- Register `plan_dependency_order.py` in `tools/TOOL_DESCRIPTIONS.md` and note the `list --plan --order` option (`REQ-007`).

## Scope
- In scope: one row in the tool-list table near `check_plan_target_overlaps.py`, one row in the detail table, and the `list` description in the `manage_workitem_stage.py` subcommand reference.
- Out of scope: other tools' rows (edited by flowimp001, flowimp007, flowimp008, flowimp010, flowimp011).

## Assumptions
- Plan A6 and A9. Step 3a verified (2026-11-02): the file has a summary table (`check_plan_target_overlaps.py` at line 46) and a detail table (line 172) plus `### manage_workitem_stage.py subcommands` (line 176); `check_tool_descriptions_sync.py` requires a row for every `tools/*.py`.
- Overlap (Step 2): `flowimp001`, `flowimp007`, `flowimp008`, `flowimp010`, and `flowimp011` also add or change rows in this file. Judged compatible: row-additive edits in different rows. Sequencing note: the sync check passes only once row 01 exists, which `seq` order guarantees.
- Rows 01 and 03 create `tools/plan_dependency_order.py` and the `--plan`/`--order` options before this document runs.

## Design decisions
- Place the new rows adjacent to `check_plan_target_overlaps.py` rows so related tools sit together.

## Alternatives considered
- N/A: the registration format is fixed by the existing tables.

## Implementation
### Target file
`tools/TOOL_DESCRIPTIONS.md`

### Procedure
- Summary table: add `| `plan_dependency_order.py` | Work item | Compute Plan dependency order and ready or gated state of open Plans (read-only; recommends, the owner decides) |`.
- Detail table: add a row with inputs `plans/*.md` (excluding `plans/done/`), `issues/`, the dependency line grammar, the outputs (order, `ready`/`gated`, cycles, overlap notes, warnings), `--plan`, `--format`, and that it is read-only with exit 0 on a completed run.
- `manage_workitem_stage.py` subcommands: extend the `list` entry with `--plan <path> --order`.

### Method
- Copy the column layout of the adjacent rows exactly; do not reflow other rows.

### Details
- The detail row states the structured line grammar once, by reference to `templates/plan.md`.

## Compatibility considerations
- Row-additive; no existing row changes except the `list` entry's option text.

## Security considerations
- N/A: documentation.

## Rollback considerations
- N/A: revert the commit.

## Validation plan
- `uv run python tools/check_tool_descriptions_sync.py`.

## Completion criteria
- The tool has both rows and the `list` entry mentions the order view; the sync check passes.

## Out of Scope
- `routing.md` (row 10) and the gate mapping (row 11).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — |  |
| 2 | Run the documentation checkers named in `routing.md` Tools "When to run which tool" | Pending | — | — | `check_tool_descriptions_sync.py` |

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
- **Requirement ID**: REQ-007 (register the tool and the new `list` option)
- **Source issue**: issues/20261030-191144_flowimp003_plan-dependency-gate.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261102-080134_flowimp003_plan-dependency-gate.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261102-085056
- **Related target files**: tools/TOOL_DESCRIPTIONS.md
