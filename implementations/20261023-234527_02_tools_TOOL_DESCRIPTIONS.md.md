## Goal

Register the new `run_validation_gates.py` tool in `tools/TOOL_DESCRIPTIONS.md` so the tool stays in the `tools/` inventory and `check_tool_descriptions_sync.py` passes. (`REQ-008`)

## Scope

- **In-Scope**: add a row documenting `run_validation_gates.py` to `tools/TOOL_DESCRIPTIONS.md` only.
- **Out-of-Scope**: implementing the tool (seq 01 of the plan's sibling row), adding the `routing.md` pointer (seq 03), or adding the `rules/toolchain.md` pointer (seq 04).

## Assumptions

- `check_tool_descriptions_sync.py` requires every `tools/<name>.py` to appear backticked as `` `<name>.py` `` somewhere in the doc; the row must therefore contain `` `run_validation_gates.py` ``.
- The doc already documents the other `tools/` scripts in category tables; the new entry belongs in the table whose category best fits an on-demand validation-gate orchestrator (the "Work Items" orchestration table is the natural home alongside `manage_workitem_stage.py`).

## Design decisions

- **Add one row to an existing category table**, keeping that table's column shape (`File | Target | Description`), rather than introducing a new table — the doc already has a table for orchestration/lifecycle tools.

## Alternatives considered

- Adding a brand-new top-level `##` section for validation orchestrators: rejected — the doc already categorizes orchestration tools; a new section would fragment the inventory.

## Implementation

### Target file

`tools/TOOL_DESCRIPTIONS.md` (modify)

### Procedure

Add one row for `run_validation_gates.py` to the appropriate category table (the "Work Items" orchestration table, `| File | Target | Description |`).

### Method

1. Locate the table that best fits an on-demand validation-gate orchestrator (the "Work Items" table listing `manage_workitem_stage.py`).
2. Insert a row: `run_validation_gates.py` | pre-commit/validation-gate selection | runs the gates a diff needs (chosen from changed files) and prints one `Pass`/`Fail`/`Partial`/`Not available`/`Blocked` summary; fast/full modes; drift check against `routing.md`.
3. Ensure `` `run_validation_gates.py` `` appears backticked (the row does).
4. Run `uv run python tools/check_tool_descriptions_sync.py` to confirm the tool is registered and no config reference dangles.

### Details

- Keep the description at the same level of detail as neighboring rows (what it does + key flags), without restating the full two-source mapping.
- If the chosen table's column headers differ, match that table's columns exactly.

## Compatibility considerations

Docs-only, additive row. No existing description is altered, so no drift in the documented behavior of the other tools.

## Security considerations

N/A: documentation change only.

## Rollback considerations

Revert the commit that adds the row, or delete the added line. Single-row, additive change.

## Validation plan

- `uv run python tools/check_tool_descriptions_sync.py` passes after the edit.
- `uv run python tools/check_workitem_structure.py` passes on this generated procedure document.

## Completion criteria

- `run_validation_gates.py` appears as a documented row in `TOOL_DESCRIPTIONS.md` with its selection/summary/drift behavior.
- `check_tool_descriptions_sync.py` passes.

## Out of Scope

Implementing the tool, the `routing.md` and `rules/toolchain.md` pointers, and the test file.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | REQ-008; tools/TOOL_DESCRIPTIONS.md |
| 2 | Add or update tests per Validation plan | Pending | — | — | N/A: docs-only |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | check_tool_descriptions_sync.py |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | this change |

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
- **Requirement ID**: `REQ-008`
- **Source issue**: `issues/20261023-173529_gate001_one-entry-point-for-the-pre-commit-validation-gates.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261023-231525_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261023-234527
- **Related target files**: `tools/TOOL_DESCRIPTIONS.md`
