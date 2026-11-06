## Goal
Finish the new private module that holds the Execution Status table logic moved out of `tools/manage_workitem_stage.py` (`REQ-005`).

## Scope
**Release unit**: N/A: not part of a release unit

- In scope: the module header and import block of the new file, and checking its content after the `extract` run performed by the `tools/manage_workitem_stage.py` procedure.
- Out of scope: running `extract` (that procedure does it), changing moved code.

## Assumptions
- Verified on 2026-11-06 (Step 3a): the file does not exist; the moved set is the Execution Status functions of `tools/manage_workitem_stage.py` (`parse_execution_status_rows`, `parse_execution_status_table`, `update_execution_status`, `build_table_header_line`, `build_table_separator_line`, `build_data_row_line`, `_rows_equal`) plus any private helper or constant both they and the entry need; `tools/plan_dependency_order.py` and `tools/close_procedures_batch.py` import the first and third names through the entry module.
- Sequencing: this Plan lands last among the `tools/` Plans; the procedures of `toolcommon001` and `toolwrite001` (archived with their procedures generated) are expected to have executed first, because they edit `run_validation_gates.py` and `manage_workitem_stage.py` before this Plan moves code from them.
- The `extract` run creates this file as the destination of the earlier-`seq` procedure for `tools/manage_workitem_stage.py`; this document only completes it (docstring, imports, ordering), so that procedure's file count stays one.

## Design decisions
- The module imports only the standard library and `tools._atomic_write`; it never imports the entry module or the parser module.
- Module docstring states responsibility and that the entry module re-exports the public names.

## Alternatives considered
N/A: single-purpose edit.

## Implementation
### Target file
`tools/_workitem_status_table.py` (new)

### Procedure
1. Add the module docstring in the repository's header format (`tools/check_docstrings.py` checks it).
2. Make the import block complete and ordered (ruff `I`), removing imports the extract left unused and adding those the moved code needs.
3. Confirm the dependency direction with `rg "manage_workitem_stage" tools/_workitem_status_table.py` (no match) and run the checks.

### Method
- The moved function bodies are not edited.

### Details
- Do not add behavior; `compare` in the entry procedure proves equality.

## Compatibility considerations
- Public names stay importable from `tools.manage_workitem_stage`.

## Security considerations
N/A: verbatim move.

## Rollback considerations
- Revert together with the entry procedure's commit.

## Validation plan
- `uv run ruff format`/`check`, `uv run mypy --no-namespace-packages tools/_workitem_status_table.py`, `uv run bandit tools/_workitem_status_table.py`, `uv run python tools/check_docstrings.py`.
- `uv run pytest tests/tools/test_manage_workitem_stage.py -q`.
- `uv run python tools/check_tool_descriptions_sync.py` is expected to report the new file until the documentation procedure lands (known interim result).

## Completion criteria
- The module has a docstring, a clean import block, no import of the entry or parser module, and passes lint, type, security, docstring, and test checks.

## Out of Scope
- Behavior changes.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Complete the docstring and import block after the extract | Completed | 20261106-121750 | 20261106-121941 | Changed: tools/_workitem_status_table.py (new, created by extract; docstring and imports completed) |
| 2 | Run the validation sequence (`rules/toolchain.md`) and the existing tests | Completed | 20261106-121941 | 20261106-121941 | existing tests pass |
| 3 | N/A: documentation is the `tools/TOOL_DESCRIPTIONS.md` procedure of this Plan | Completed | 20261106-121941 | 20261106-121941 | ruff, mypy, bandit clean; imports no entry or parser module |

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
- **Requirement ID**: `REQ-005` (moved status-table logic)
- **Source issue**: issues/20261104-152002_toolsizegate001_apply-size-gate-to-tools.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261105-110406_toolsizegate001_apply-size-gate-to-tools.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261106-092637
- **Related target files**: `tools/_workitem_status_table.py`
