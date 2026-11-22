## Goal

Make `CLIView` render-only by removing the multiline reader, its protocol, its timeout constant, and its reader dependency (REQ-003).

## Scope
**Release unit**: input-controller-cutover

In scope: `scripts/agent/cli_view.py` and its companion test. Multiline policy moves to the controller row.

## Assumptions

- Verified: `read_multiline` callers are `repl_input_loop.py`, `tests/test_cli_view.py`, and `tests/agent/test_repl.py` (Plan Design, consumer scan); the loop row switches the production caller in the same release unit.

## Design decisions

- Delete `Reader`, `CLIView.read_multiline`, `_INPUT_TIMEOUT_S`, the `get_stdin_reader` import, and `self._stdin_reader`; drop `Protocol`/`runtime_checkable` imports if unused.
- Keep `WriterBase`, readline setup, spinner, and every delegated write method unchanged.

## Alternatives considered

N/A: the removal is the Issue's stated requirement.

## Implementation
### Target file
`scripts/agent/cli_view.py`

### Procedure
1. Remove the symbols listed in Design decisions and update the module docstring so it no longer mentions multiline continuation input.
2. Confirm no other module imports `Reader` from this file (`rg` over `scripts/` and `tests/`).

### Method
Pure deletion plus docstring edit; no new code.

### Details
- `asyncio` stays imported for the spinner; `logging` stays for the history file messages.

### Companion test files
- `tests/test_cli_view.py`
  - Procedure: Replace `TestReadMultilineTimeout` (line 151) with a test that `CLIView` has no `read_multiline` attribute and holds no reader; the timeout behavior is covered in the controller tests.
  - Validation: `uv run pytest tests/test_cli_view.py -q`

## Compatibility considerations

Breaking for any external caller of `CLIView.read_multiline`; none exists outside the loop and tests (consumer scan).

## Security considerations

N/A: no security-relevant behavior; it removes a second path that read stdin.

## Rollback considerations

N/A: revert the commit (release unit `input-controller-cutover`).

## Validation plan

- `uv run pytest tests/test_cli_view.py -q`
- `uv run ruff check scripts/agent/cli_view.py && uv run mypy scripts/agent/cli_view.py`

## Completion criteria

- `scripts/agent/cli_view.py` has no stdin read, no timeout constant, and no `Reader` protocol; tests and type check pass.

## Out of Scope

Controller multiline implementation, loop wiring, CLIView docs.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan (companion test files included) | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |

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
- **Requirement ID**: `REQ-003` (CLIView renders only; no input-state policy)
- **Source issue**: issues/20261119-145259_cliplc001_repl-input-controller.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261122-210208_cliplc001_repl-input-controller.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261122-210644
- **Related target files**: `scripts/agent/cli_view.py`, `tests/test_cli_view.py`
