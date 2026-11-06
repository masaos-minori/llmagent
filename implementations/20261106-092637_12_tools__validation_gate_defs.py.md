## Goal
Finish the new private module that holds the gate type, its helpers, and the gate tables moved out of `tools/run_validation_gates.py` (`REQ-006`).

## Scope
**Release unit**: N/A: not part of a release unit

- In scope: the module header and import block after the `extract` run performed by the `tools/run_validation_gates.py` procedure (Part B).
- Out of scope: running `extract`, changing any gate.

## Assumptions
- Verified on 2026-11-06 (Step 3a): the file does not exist; the moved set is `Gate`, `_checker_id_from_command`, the constants `SOURCE_TOOLCHAIN`, `SOURCE_ROUTING`, `MODE_FAST`, `MODE_FULL`, `_TOOL_PY_RE`, `_VALUE_FLAG_RE`, `_PLACEHOLDER_TOKEN_RE`, `_BARE_EXCEPT_RULE`, and the tables `TOOLCHAIN_GATES` and `ROUTING_GATES` (Plan correction: the helpers and regexes move with `Gate` to avoid a cycle).
- Sequencing: this Plan lands last among the `tools/` Plans; the procedures of `toolcommon001` and `toolwrite001` (archived with their procedures generated) are expected to have executed first, because they edit `run_validation_gates.py` and `manage_workitem_stage.py` before this Plan moves code from them.
- The `extract` run creates this file in the earlier-`seq` procedure for `tools/run_validation_gates.py`; this document completes it. The test file `tests/tools/test_run_validation_gates.py` is named by two rows and has its own procedure.

## Design decisions
- Standard library plus `dataclasses` only; the module never imports `tools.run_validation_gates`.
- Docstring states that the entry module re-exports these names.

## Alternatives considered
N/A: single-purpose edit.

## Implementation
### Target file
`tools/_validation_gate_defs.py` (new)

### Procedure
1. Add the module docstring in the repository's header format.
2. Complete the import block (`re`, `dataclasses`, `Path` if used) and remove unused imports.
3. Confirm with `rg "run_validation_gates" tools/_validation_gate_defs.py` that no import of the entry module exists.

### Method
- Moved code is not edited.

### Details
- `_SELF_CHECKER_ID` stays in the entry module (it uses the entry's own file name).

## Compatibility considerations
- Names stay importable from `tools.run_validation_gates`; the identity test in `tests/tools/test_run_validation_gates.py` proves it.

## Security considerations
N/A: verbatim move.

## Rollback considerations
- Revert together with the entry procedure's commit.

## Validation plan
- `uv run ruff format`/`check`, `uv run mypy --no-namespace-packages tools/_validation_gate_defs.py`, `uv run bandit tools/_validation_gate_defs.py`, `uv run python tools/check_docstrings.py`.
- `uv run pytest tests/tools/test_run_validation_gates.py -q`.
- `uv run python tools/run_validation_gates.py drift`.

## Completion criteria
- The module has a docstring, a clean import block, no import of the entry module, and the tests and `drift` pass.

## Out of Scope
- Gate changes.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Complete the docstring and import block after the extract | Pending | — | — | |
| 2 | Run the validation sequence (`rules/toolchain.md`), the tests, and `drift` | Pending | — | — | |
| 3 | N/A: documentation is the `tools/TOOL_DESCRIPTIONS.md` procedure of this Plan | Pending | — | — | |

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
- **Requirement ID**: `REQ-006` (moved gate definitions)
- **Source issue**: issues/20261104-152002_toolsizegate001_apply-size-gate-to-tools.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261105-110406_toolsizegate001_apply-size-gate-to-tools.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261106-092637
- **Related target files**: `tools/_validation_gate_defs.py`
