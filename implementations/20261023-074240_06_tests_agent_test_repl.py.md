## Goal

Add two additive cases to `tests/agent/test_repl.py` asserting that the prompt read does not use the loop executor and leaves no non-daemon thread, and that EOF/Ctrl-C at the prompt still return `None` (`plans/20261022-040200_plan.md`, REQ-006, REQ-011; AC-2, AC-5).

## Scope

Modify only `tests/agent/test_repl.py`: add `TestPromptReadDoesNotUseAnExecutor` and `TestPromptInterruptAndEofUnchanged`. Keep every existing fixture and case unchanged.

## Assumptions

- The existing tests already stub `builtins.input` (`test_repl.py:640-706`); the new cases follow the same style but additionally assert on the thread and the loop spy.
- Existing cases must pass unchanged (`AC-5`).

## Design decisions

- `TestPromptReadDoesNotUseAnExecutor` spies on the running loop's `run_in_executor` while `_read_input` performs a read on each branch and asserts the spy is never called, and asserts `threading.enumerate()` shows no non-daemon thread left behind.
- `TestPromptInterruptAndEofUnchanged` stubs `builtins.input` to raise `EOFError`/`KeyboardInterrupt` and asserts `_read_input` returns `None` and `_abort_input` runs once.

## Alternatives considered

N/A: the Plan fixes the two cases; this row adds them.

## Implementation

### Target file

`tests/agent/test_repl.py`

### Procedure

1. Add `TestPromptReadDoesNotUseAnExecutor` under the existing read-input test class.
2. Add `TestPromptInterruptAndEofUnchanged` alongside it.
3. Do not modify any existing fixture, parameterization, or case name.

### Method

- Drive the real `_read_input` through `builtins.input` stubs (existing style), spying on `loop.run_in_executor` and asserting it is never called over both `_read_input` branches.
- For the interrupt/EOF case, stub `builtins.input` to raise each exception and assert the `None` return and single `_abort_input` call.

### Details

- Keep the existing `TestReadInputShutdownRace` (`:640-706`) and `test_no_shutdown_event_fallback` (`:674-680`) untouched.

## Compatibility considerations

N/A: additive only; existing cases unchanged.

## Security considerations

N/A: tests only.

## Rollback considerations

N/A: delete the added cases.

## Validation plan

| Target File/Module | Testing Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| `scripts/agent/repl_input_loop.py` | Integration: real `_read_input` driven through `builtins.input` stubs, loop `run_in_executor` spy, `threading.enumerate()` assertion; existing race cases unchanged. | `uv run pytest tests/agent/test_repl.py -q` ; `grep -n "run_in_executor\|to_thread" scripts/agent/repl_input_loop.py` | Existing `:640-706` and `test_no_shutdown_event_fallback` pass unchanged; new cases pass; grep returns nothing (AC-2, AC-5). |

## Completion criteria

- `TestPromptReadDoesNotUseAnExecutor` and `TestPromptInterruptAndEofUnchanged` pass.
- All pre-existing cases in `test_repl.py` pass unchanged.

## Out of Scope

Changing any existing case, fixture, or case name.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add `TestPromptReadDoesNotUseAnExecutor` and `TestPromptInterruptAndEofUnchanged` to `tests/agent/test_repl.py` | In Progress | 20261023-074240 | — | REQ-006, REQ-011; AC-2, AC-5 |
| 2 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |

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
- **Requirement ID**: REQ-006, REQ-011
- **Source issue**: `issues/20261021-093421_repl002_cancelled_input_read_delays_process_exit.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261022-040200_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261023-074240
- **Related target files**: `tests/agent/test_repl.py`
