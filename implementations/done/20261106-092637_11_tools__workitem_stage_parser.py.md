## Goal
Finish the new private module that holds `build_parser` moved out of `tools/manage_workitem_stage.py`, taking the command handlers as an argument (`REQ-005`).

## Scope
**Release unit**: N/A: not part of a release unit

- In scope: the module header, the handler-argument signature, and the import block of the new file after the `extract` run performed by the entry procedure.
- Out of scope: running `extract`, changing subcommand definitions.

## Assumptions
- Verified on 2026-11-06 (Step 3a): the file does not exist; `build_parser` spans about 208 lines and registers every subcommand with `func=` handlers (the `cmd_*` functions defined in the entry module) and uses validator functions such as `_valid_status_type` as `type=`; the tests call `build_parser()` with no argument through the entry module's wrapper.
- Sequencing: this Plan lands last among the `tools/` Plans; the procedures of `toolcommon001` and `toolwrite001` (archived with their procedures generated) are expected to have executed first, because they edit `run_validation_gates.py` and `manage_workitem_stage.py` before this Plan moves code from them.
- The `extract` run creates this file in the earlier-`seq` entry procedure; this document completes it.
- Correction (code-implementation Step 3b, 2026-11-06): `build_parser` does not reference any `cmd_*` handler (the entry module's `main` dispatches on `args.subcommand`), so the parser module keeps a zero-argument `build_parser()` and the entry module imports and re-exports it directly; no handler argument and no wrapper are needed. `_valid_status_type` moved with `build_parser`, and `_normalize_status` lives in the status-table module that the parser imports.

## Design decisions
- The builder takes a mapping of handler names to callables (or the module of handlers) so it never imports the entry module; the validators it needs move with it.
- The entry module's wrapper supplies the handlers.

## Alternatives considered
- Import the handlers from the entry module inside the builder: rejected, it creates a circular import (Plan Risks).

## Implementation
### Target file
`tools/_workitem_stage_parser.py` (new)

### Procedure
1. Add the module docstring in the repository's header format.
2. Change the extracted function's signature to receive the handlers and replace each direct `cmd_*` reference by the argument (the only edit to moved code; list each replaced reference in the commit).
3. Complete the import block and check that nothing imports the entry module.

### Method
- Each `set_defaults(func=cmd_x)` becomes `set_defaults(func=handlers["x"])` (or an equivalent attribute lookup); argument definitions stay verbatim.

### Details
- Confirm the parsed `--help` output of every subcommand is byte-identical before and after: `uv run python tools/manage_workitem_stage.py <cmd> --help`.

## Compatibility considerations
- `tools.manage_workitem_stage.build_parser()` keeps its zero-argument signature through the wrapper.

## Security considerations
N/A: parser construction only.

## Rollback considerations
- Revert together with the entry procedure's commit.

## Validation plan
- `uv run ruff format`/`check`, `uv run mypy --no-namespace-packages tools/_workitem_stage_parser.py`, `uv run bandit tools/_workitem_stage_parser.py`, `uv run python tools/check_docstrings.py`.
- `uv run pytest tests/tools/test_manage_workitem_stage.py tests/tools/test_manage_workitem_stage_new.py -q`.
- Compare `--help` output of every subcommand before and after.

## Completion criteria
- The module has a docstring, receives handlers as an argument, imports no entry module, and every subcommand's `--help` output and the tests are unchanged.

## Out of Scope
- Subcommand definitions beyond the handler references.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Complete the docstring, signature, and import block after the extract | Completed | 20261106-121750 | 20261106-121942 | Changed: tools/_workitem_stage_parser.py (new, created by extract; docstring and imports completed; zero-argument build_parser kept) |
| 2 | Compare every subcommand's `--help` and run the existing tests | Completed | 20261106-121942 | 20261106-121942 | existing tests pass |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261106-121942 | 20261106-121942 | ruff, mypy, bandit clean; help output of every subcommand identical |
| 4 | N/A: documentation is the `tools/TOOL_DESCRIPTIONS.md` procedure of this Plan | Completed | 20261106-121942 | 20261106-121942 | N/A: documentation is another procedure of this Plan |

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
- **Requirement ID**: `REQ-005` (moved parser construction)
- **Source issue**: issues/20261104-152002_toolsizegate001_apply-size-gate-to-tools.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261105-110406_toolsizegate001_apply-size-gate-to-tools.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261106-092637
- **Related target files**: `tools/_workitem_stage_parser.py`
