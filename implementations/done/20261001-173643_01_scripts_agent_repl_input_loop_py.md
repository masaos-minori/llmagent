# Implementation Procedure: repl_input_loop.py — per-turn exception safety net

## Goal

Contain a non-`RuntimeError`, non-`TimeoutError` exception escaping a turn so that it is surfaced through the CLI view and the REPL loop remains usable for the next command, instead of propagating out of `asyncio.run()` and ending the interactive session. Implements `REQ-001` (short purpose: contain unexpected per-turn errors at the REPL layer).

## Scope

- **In scope**: Add a per-turn exception safety net around the turn-dispatch await in `ReplInputLoop._repl_loop` in `scripts/agent/repl_input_loop.py`.
- **Out of scope**: Startup `session.start()` exception translation in `run()`; input-coroutine cancellation on the shutdown-during-input path (tracked separately as `repl002`); `WorkflowEngine` internals; adapter-side containment in `WorkflowEngineAdapter.execute_turn`; shutdown racing, multiline continuation, and command routing outside the turn-dispatch path.

## Assumptions

- The CLI view exposes `write_fatal`/`write_warning` methods suitable for surfacing the error (confirmed present in the review evidence and used throughout `repl_input_loop.py`).
- `_repl_loop` is the preferred containment location because loop containment avoids masking exceptions the engine intentionally propagates; adapter-side containment is a fallback that still must preserve the documented workflow-error handling in `execute_turn`.
- `asyncio.CancelledError` must never be swallowed as a handled turn error.

## Design decisions

- **Containment location**: wrap the turn-dispatch await inside `_repl_loop` with a `try/except Exception` guard. Loop containment is preferred over `run()` or adapter-side containment because it keeps the operator-facing surface responsible for the error and does not widen the exception contract downstream.
- **Exception selection**: catch broad base `Exception`, but explicitly re-raise `asyncio.CancelledError` (a `BaseException`, not `Exception`, so this is defensive clarity, not a gap). Never catch `BaseException`.
- **Preserve existing paths**: the new handler sits alongside, and does not collapse into, the existing `TimeoutError` shutdown-race handling in `_repl_loop` and the `RuntimeError` fatal-write-and-reraise path in `run()`. `TimeoutError` keeps its existing shutdown-race behavior; `RuntimeError` keeps its existing fatal-write-and-reraise path.
- **Complexity budget**: `_repl_loop` already has cyclomatic complexity D (radon score 28). Extract a small named helper method if the added branch grows beyond a few lines rather than inlining it.

## Alternatives considered

- **Adapter-side containment in `WorkflowEngineAdapter.execute_turn`**: convert unexpected exceptions into an error response/error_kind and document that contract. Rejected as the primary approach because it risks masking exceptions the engine intentionally propagates and changes a broader cross-layer contract. Retained as the fallback design in the Plan only if implementation finds it materially cleaner for a specific recurring type, addressed as a follow-up.
- **Containment in `run()` around `_repl_loop()`**: less surgical; the existing `RuntimeError` fatal-write-and-reraise path in `run()` must remain intact, making a broad catch here riskier than scoping it to the dispatch await in `_repl_loop`.

## Implementation

### Target file

`scripts/agent/repl_input_loop.py`

### Procedure

1. Read `scripts/agent/workflow_engine_adapter.py` (`execute_turn`), `scripts/agent/repl.py` (`AgentREPL.run()` delegating to `_input_loop.run(...)` with no surrounding try/except), and `scripts/agent/orchestrator.py` (`handle_turn`/`_execute_turn`) to confirm the exact exception-propagation path from `handle_turn` to `_dispatch_line` and lock the containment decision at the loop layer.
2. In `_repl_loop`, wrap the turn-dispatch await (the `asyncio.ensure_future(self._dispatch_line(line, ctx))` site and its awaiting branches) with a `try/except Exception` guard that:
   - re-raises `asyncio.CancelledError` explicitly;
   - lets the existing `TimeoutError` shutdown-race path and the `RuntimeError` fatal-write-and-reraise path behave unchanged;
   - otherwise writes the error through the view (`write_fatal`/`write_warning`) and continues the loop when no shutdown was requested.
3. If the added branch grows beyond a few lines, extract a small named helper method (for example `_surface_turn_error(exc) -> None`) that performs the view write, keeping `_repl_loop`'s branch count flat.
4. Confirm the new handler never touches the surrounding shutdown logic (`shutdown_event`, `shutdown_requested`, graceful-timeout handling).

### Method

- Keep the change minimal and localized to the turn-dispatch await; do not alter `_read_input`, `_should_exit`, `_dispatch_line`, or the shutdown-race branches.
- Preserve the `finally` block that resets `_turn_active`/`is_processing`.
- Do not introduce blocking I/O in the async handler; the view write is synchronous and already used elsewhere in this module.

### Details

- Propagation path being closed: `_dispatch_line` → `Orchestrator.handle_turn` → `Orchestrator._execute_turn` → `WorkflowEngineAdapter.execute_turn`, which catches only `WorkflowPendingApprovalError` and `(WorkflowHaltError, WorkflowTimeoutError)`; any other exception currently escapes to `asyncio.run()`.
- The guard must sit around the dispatch-await branches only, not around `_read_input` or the shutdown watcher.
- Error text surfaced via the view must not leak secrets or sensitive session internals (see Security considerations).

## Compatibility considerations

- Shutdown behavior is unchanged: a shutdown request still terminates the loop, and `CancelledError` is not swallowed as a handled turn error (AC-2).
- The existing `RuntimeError` fatal-write-and-reraise path in `run()` is untouched.
- The existing `TimeoutError` shutdown-race path in `_repl_loop` is untouched.
- Existing REPL tests (`tests/agent/test_repl*.py`) must continue to pass (AC-3).

## Security considerations

- The broad `except Exception` MUST NOT swallow `asyncio.CancelledError`, `KeyboardInterrupt`, or `SystemExit` (all `BaseException`); re-raise `CancelledError` explicitly and leave the others uncaught.
- Error text written through the view must avoid dumping full tracebacks or session-internal state that could expose secrets or sensitive data; surface the exception class name and message minimally.
- Do not log sensitive context (per `skills/DESIGN.md` No secrets in output).

## Rollback considerations

- Single-file, localized change; reverting the commit restores the original `_repl_loop` behavior with no data migration or config change. `deploy.sh` impact is limited to the interactive session; no deploy/config change.

## Validation plan

| Target File/Module | Testing Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| `scripts/agent/repl_input_loop.py` | Format + lint | `uv run ruff format scripts/agent/repl_input_loop.py` then `uv run ruff check scripts/agent/repl_input_loop.py` | Clean (no diffs, no errors) |
| `scripts/agent/repl_input_loop.py` | Type check | `uv run mypy scripts/` (primary, per `rules/toolchain.md`); the single-file `uv run mypy scripts/agent/repl_input_loop.py` may report the pre-existing `tool_constants` duplicate-module-path quirk unrelated to this change | Pass (no new regressions vs pre-existing errors) |
| `scripts/agent/repl_input_loop.py` | Architecture | `PYTHONPATH=scripts uv run lint-imports` | No boundary violations |
| `scripts/agent/repl_input_loop.py` | Security lint | `uv run bandit scripts/agent/repl_input_loop.py` | No new findings |
| `scripts/agent/repl_input_loop.py` | Complexity | `uv run radon cc scripts/agent/repl_input_loop.py -s` | Complexity did not worsen beyond the existing D grade |
| `tests/agent/test_repl*.py` | Regression: non-`RuntimeError` turn exception keeps loop responsive | `uv run pytest tests/agent/test_repl*.py` | All pass; new regression test present |
| Whole affected lifecycle suite | Full regression | `uv run pytest` on affected lifecycle suites | Pass; diff-cover >= 90% on changed lines |

## Completion criteria

- A turn that raises a non-`RuntimeError` exception is contained by `_repl_loop`, reported through the view, and the loop then waits for the next input instead of terminating the session (AC-1).
- Shutdown behavior is unchanged: a shutdown request still terminates the loop, and `CancelledError` is not swallowed as a handled turn error (AC-2).
- The existing REPL tests still pass, and the new regression test passes (AC-3).

## Out of scope

- Startup `session.start()` exception translation in `run()` (tracked separately as `repl002`).
- Input-coroutine cancellation on the shutdown-during-input path.
- `WorkflowEngine` internals and adapter-side containment in `WorkflowEngineAdapter.execute_turn` (fallback only, per the Plan).
- Shutdown racing, multiline continuation, and command routing outside the turn-dispatch path.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Read reference files; confirm exception-propagation path; lock loop-layer containment | Completed | 20261001-193738 | 20261001-193738 | REQ-001 Reference files confirmed; propagation path locked to _repl_loop layer |
| 2 | Add per-turn exception safety net around the turn-dispatch await in `_repl_loop` | Completed | 20261001-193738 | 20261001-193738 | REQ-001 Added _surface_turn_error helper + except Exception handler; _repl_loop stays grade D (radon 29) |
| 3 | Run validation sequence (`rules/toolchain.md`): ruff/mypy/lint-imports/bandit/radon/pytest/diff-cover | Completed | 20261001-193738 | 20261001-193738 | REQ-001 ruff clean; mypy clean via --no-namespace-packages; bandit clean; radon D; pytest 0 new failures (6 pre-existing DB-setup); diff-cover 100% on changed lines; negative control fails vs pre-fix |

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
- **Requirement ID**: `REQ-001` — contain unexpected per-turn errors at the REPL layer
- **Source issue**: issues/20260930-231242_repl001_repl-turn-exception-not-contained-by-runtimeerror-only-handler-crashes-interactive-session.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260930-234119_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261001-173643
- **Related target files**: scripts/agent/repl_input_loop.py