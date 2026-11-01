# A shutdown request during startup ends the process with a traceback and exit status 1

## Priority
Medium

## Summary
When SIGTERM or SIGINT arrives during agent startup, `AgentREPL.run` prints a non-fatal warning and re-raises `StartupInterrupted`. Neither entry point catches it: `repl.main` and `__main__` both call `asyncio.run(AgentREPL().run())` directly. `StartupInterrupted` derives from `BaseException`, so `asyncio.run` propagates it, the interpreter prints a full traceback, and the process exits with status 1. A requested, clean shutdown is reported as a crash. Handle the exception at the process entry point and define the exit status for an interrupted startup.

## Background
Found during an adversarial review (`python-code-review`) of the agent startup path.
- `issues/done/20261021-220332_star002_make-startupinterrupted-distinguishable-from-ordinary-runtimeerror-in-broad-startup-handlers.md` deliberately moved `StartupInterrupted` from `RuntimeError` to `BaseException` so broad startup handlers do not swallow it. That change is correct; it is also what lets the exception reach the interpreter unhandled.
- `AgentREPL.run` was written to re-raise it after the warning, and the test `test_startup_interrupted_warns_and_reraises` in `tests/agent/test_repl.py` pins that contract for `run()` only. No test covers the process-level outcome.
- `repl.main` and `__main__` duplicate the same entry call; there is no shared place that handles startup interruption.

## Problem
Chain: a signal sets the shutdown event; a startup step raises `StartupInterrupted`; `AgentREPL.run` warns, runs its `finally` cleanup, and re-raises; the exception leaves `asyncio.run`.

Verified behavior of the interpreter (throwaway script, not committed): `asyncio.run` of a coroutine that ends with a `BaseException` subclass other than `KeyboardInterrupt`/`SystemExit` prints the traceback and exits with status 1. The full agent was not run end to end for this check, because that would start real services; the agent-level chain above is established by reading the code.

## Reason for Change
Service managers and init scripts treat a non-zero exit status as a failed run, and a traceback in the output is indistinguishable from a real crash during startup. Stopping the service while it is starting is a normal operation, so it should end quietly with a defined status.

## Implementation Intent
Catch `StartupInterrupted` in one place at the process entry (a single function used by both `repl.main` and `__main__`), after `AgentREPL.run` has completed its cleanup, and map it to a deliberate exit status without a traceback. Keep the `run()` contract (warn, clean up, re-raise) and the `BaseException` base class unchanged.

## Target Files or Areas
- `scripts/agent/repl.py` (`main`, `AgentREPL.run`)
- `scripts/agent/__main__.py`
- `scripts/agent/startup.py` (`StartupInterrupted`, read only)
- `tests/agent/test_repl.py`

## Required Changes
- Introduce one entry-point function that runs the REPL and handles `StartupInterrupted`; make `repl.main` and `__main__` use it.
- Define the exit status for an interrupted startup (see Unresolved Questions) and apply it.
- Add a test that runs the entry function with a startup that raises `StartupInterrupted` and asserts no exception escapes and the chosen status is returned.

## Constraints
- `StartupInterrupted` stays a `BaseException` subclass.
- `AgentREPL.run` must keep running its cleanup in `finally` before the exception leaves it.
- A real startup failure (any other exception) must keep its current non-zero exit and visible error.
- The compiled binary built from `repl.main` must behave the same.

## Acceptance Criteria
- Sending a shutdown request during startup ends the process without a traceback and with the defined exit status.
- A genuine startup failure still ends with a non-zero status and the fatal message.
- Both `python -m agent` and `repl.main` share the same handling.
- The new test fails on the current code and passes after the change.

## Testing Expectations
- Unit test of the entry function as described, using mocks for `AgentREPL.run` so no real services start.
- Run `tests/agent/test_repl.py`, `ruff`, and `mypy --no-namespace-packages` on the touched files.
- Manual verification (optional, on a development host only): start the agent and send SIGTERM during startup; check the exit status and absence of a traceback.

## Documentation Impact
Needs confirmation: check whether operations documentation lists agent exit statuses or shutdown behavior during startup. If it does, record the defined status for an interrupted startup.

## Out of Scope
- Changing `StartupInterrupted`'s base class or message format.
- How and when startup steps check the shutdown event.
- Changes to `AgentREPL.run`'s cleanup order.

## Dependencies
N/A: none. No open issue or in-flight plan targets the entry points for this behavior.

## Unresolved Questions
- `不明`: which exit status an interrupted startup should use (0, the conventional 128 plus signal number, or 1 without a traceback). The owner must decide.
- Whether the packaged (compiled) entry point or the init script wraps the exit status in a way that changes the requirement: not verified.

## AI Implementation Instruction
Add the entry-point handling and its test only. Do not change `StartupInterrupted`, the startup steps, or `AgentREPL.run`'s cleanup. Do not choose the exit status silently: implement the status the owner specifies, or stop and report if it is still undecided.

## Traceability
- **Workflow phase**: python-code-review -> issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261031-135544
- **Related target files**: scripts/agent/repl.py, scripts/agent/__main__.py, scripts/agent/startup.py, tests/agent/test_repl.py
