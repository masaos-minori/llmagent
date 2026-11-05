## Goal
- Make the `mypy` gate in the validation-gate table check the same scope as `pyproject.toml`, including `tools` (`REQ-002`: the gate command names the same scope).

## Scope
**Release unit**: N/A: not part of a release unit

- In scope: the command tuple of the `Gate(name="mypy", ...)` entry in the toolchain gate table of `tools/run_validation_gates.py` (lines 668-681).
- Plan: `plans/20261105-105442_toolmypy001_add-tools-to-mypy-scope.md`, Plan step 2 (Phase 2). Not listed in the source Issue; found in Plan Step 3.

## Assumptions
- The gate lists `"scripts/"` and `"tests/eventbus"` as its last two arguments and runs in full mode only (verified 2026-11-05). The drift check compares gate names with `routing.md` and the hooks, not the arguments, so the name `mypy` stays.
- `tests/tools/test_run_validation_gates.py` asserts only that the `mypy` gate exists (line 146), not its arguments, so no test changes.
- Plan overlap: the `toolcommon001` Plan edits `_git_diff_name_only` in this file and the `toolsizegate001` Plan adds a gate and later moves the gate tables; both depend on this Plan, so this is a sequencing dependency, not a conflict (the split moves the already-changed tuple).

## Design decisions
- Add `"tools",` after `"tests/eventbus",` in the tuple, one new line.

## Alternatives considered
N/A: single-tuple alignment.

## Implementation
### Target file
`tools/run_validation_gates.py`

### Procedure
1. In the `mypy` gate command tuple, add the element `"tools",` after `"tests/eventbus",`.

### Method
- One added line; no other gate or helper changes.

### Details
- Keep the `source` and `mode` fields of the gate as they are.

## Compatibility considerations
- `run_validation_gates.py --full` now type-checks `tools/` as well; the output format is unchanged.

## Security considerations
N/A: the command is a fixed argv tuple with no user input.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run pytest tests/tools/test_run_validation_gates.py -q` passes.
- `uv run python tools/run_validation_gates.py` passes, and `uv run python tools/run_validation_gates.py drift` reports parity.
- `uv run ruff format`, `uv run ruff check`, and `uv run bandit tools/run_validation_gates.py` are clean.

## Completion criteria
- The gate tuple names `scripts/`, `tests/eventbus`, and `tools`, and the drift check still passes.

## Out of Scope
- Other gates, the gate runner, and the module-size split of this file (handled by the `toolsizegate001` Plan).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add `"tools"` to the `mypy` gate tuple | Pending | — | — | |
| 2 | Run the tests, the drift check, and ruff/bandit (`rules/toolchain.md`) | Pending | — | — | |

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
- **Requirement ID**: `REQ-002` (the gate command names the same scope)
- **Source issue**: issues/20261104-152002_toolmypy001_add-tools-to-mypy-scope.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261105-105442_toolmypy001_add-tools-to-mypy-scope.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261105-133115
- **Related target files**: `tools/run_validation_gates.py`
