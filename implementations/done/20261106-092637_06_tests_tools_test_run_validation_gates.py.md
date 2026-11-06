## Goal
Assert that the `tools/` size gate is mapped and that the re-exported names still import after the split (`REQ-002`, `REQ-006`).

## Scope
**Release unit**: N/A: not part of a release unit

- In scope: new test functions in this existing file.
- Out of scope: existing tests.

## Assumptions
- Verified on 2026-11-06 (Step 3a): the file imports its subjects from `tools.run_validation_gates` (names listed in the `tools/run_validation_gates.py` procedure), has `test_checker_id_matches_across_sources` over every `ROUTING_GATES` entry, and uses an injected runner; it is not a companion because two rows (`tools/run_validation_gates.py` and `tools/_validation_gate_defs.py`) name it in `Related Tests`.
- Sequencing: this Plan lands last among the `tools/` Plans; the procedures of `toolcommon001` and `toolwrite001` (archived with their procedures generated) are expected to have executed first, because they edit `run_validation_gates.py` and `manage_workitem_stage.py` before this Plan moves code from them.
- Overlap judgment: the archived `toolmypy001` and `toolcommon001` Plans touched this file earlier; this Plan only adds tests.

## Design decisions
- Add a test that `ROUTING_GATES` contains `check_module_size_tools` with a `tools/*.py` pattern and the checker id `check_module_size:tools`.
- Add a test that `Gate`, `ROUTING_GATES`, `TOOLCHAIN_GATES`, and `_checker_id_from_command` imported from `tools.run_validation_gates` are the same objects (`is`) as those in `tools._validation_gate_defs` (valid after the split).

## Alternatives considered
N/A: single-purpose edit.

## Implementation
### Target file
`tests/tools/test_run_validation_gates.py`

### Procedure
1. Add the gate-mapping test now (it passes once the gate entry lands).
2. Add the identity test with the split (it fails until `tools/_validation_gate_defs.py` exists).

### Method
- Reuse the file's existing imports; select gates with `next(g for g in ROUTING_GATES if g.name == ...)`.

### Details
- Do not patch module symbols; import and compare.

## Compatibility considerations
N/A: test-only change.

## Security considerations
N/A: no I/O beyond the checked-in files.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run pytest tests/tools/test_run_validation_gates.py -q`, then `uv run pytest tests/tools -q`.
- `uv run ruff format`/`check` and `uv run mypy --no-namespace-packages tests/tools/test_run_validation_gates.py`.

## Completion criteria
- Both tests exist and pass at the right phases; existing tests are unchanged and pass.

## Out of Scope
- Source changes.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add the gate-mapping test | Completed | 20261106-121717 | 20261106-121740 | Changed: tests/tools/test_run_validation_gates.py (gate-mapping and selection tests; the re-export identity test is added with the split) |
| 2 | Add the identity test with the split and run the file | Completed | 20261106-121740 | 20261106-121740 | 58 tests pass |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261106-121740 | 20261106-121740 | ruff, mypy clean |

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
- **Requirement ID**: `REQ-002` (gate mapped), `REQ-006` (re-exports intact)
- **Source issue**: issues/20261104-152002_toolsizegate001_apply-size-gate-to-tools.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261105-110406_toolsizegate001_apply-size-gate-to-tools.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261106-092637
- **Related target files**: `tests/tools/test_run_validation_gates.py`
