# on_turn_start/on_turn_end/on_llm_wait_start/on_llm_wait_end callbacks are stored but never invoked

## Priority
Medium

## Summary
`Orchestrator`, `AuditEventEmitter`, and `LlmTurnExecutor` all accept and store
`on_turn_start`, `on_turn_end`, `on_llm_wait_start`, and `on_llm_wait_end`
callbacks in their constructors, but none of them actually invoke these
callbacks anywhere in the current code. `LlmTurnExecutor` even defines
`call_on_turn_end()`/`call_on_llm_wait_end()` helper methods for exactly this
purpose, but those helpers are themselves never called from anywhere.

## Background
While fixing `tests/agent/test_orchestrator.py::TestHandleLlmTurnOptionalCallbacks`
(3 tests, explicitly documented in their own docstring as "characterization
tests... these callbacks previously had no test coverage at all"), I found
that `on_error` had the exact same problem (stored via `LlmTurnExecutor.
call_on_error()`, never called) and fixed it by invoking
`self.call_on_error(result.exception)` inside `LlmTurnExecutor.handle_llm_turn()`
right after getting the `TurnResult` from `runner.run()` — a safe, unambiguous
fix since there is exactly one place an LLMTransportError becomes visible
(`result.exception`) and exactly one existing helper built to consume it.

The `on_turn_start`/`on_turn_end`/`on_llm_wait_start`/`on_llm_wait_end` case is
different: these callbacks are declared on THREE separate classes
(`Orchestrator.__init__`, `AuditEventEmitter.__init__`,
`LlmTurnExecutor.__init__`), and `AuditEventEmitter` already has its own
`emit_turn_start()`/`emit_turn_end()` methods that are called from
`Orchestrator._execute_turn()` for a DIFFERENT purpose (writing audit log
events) — it's not obvious whether the user-facing `on_turn_start`/`on_turn_end`
callbacks were meant to piggyback on those same call sites, or whether
`on_llm_wait_start`/`on_llm_wait_end` specifically should wrap just the LLM
streaming call inside `LLMTurnRunner.run()`/`_stream_llm()` (bracketing exactly
the network wait, not the whole turn). Given three classes independently
declare the same callback parameters, guessing the intended call site
unilaterally risks wiring it into the wrong layer or duplicating the audit-log
call sites' timing semantics incorrectly.

## Problem
No user of `Orchestrator(..., on_turn_start=..., on_turn_end=...,
on_llm_wait_start=..., on_llm_wait_end=...)` currently receives any of these
callback invocations, regardless of turn outcome (success or error).

## Reason for Change
`tests/agent/test_orchestrator.py::TestHandleLlmTurnOptionalCallbacks` (3
tests) fail because they assert these callbacks are invoked, matching what
the constructor parameters and stored callback fields imply should happen.

## Implementation Intent
Decide, for each callback, exactly where it should fire:
- `on_llm_wait_start`/`on_llm_wait_end`: most likely should bracket the actual
  LLM network call inside `LLMTurnRunner._stream_llm()` or
  `LlmTurnExecutor.handle_llm_turn()`, notifying a UI/REPL layer that the
  agent is waiting on the LLM.
- `on_turn_start`/`on_turn_end`: most likely should fire alongside (or instead
  of overloading) `AuditEventEmitter.emit_turn_start()`/`emit_turn_end()`,
  since those already bracket one whole turn — but confirm this doesn't
  double up with the audit-logger-specific behavior those methods also
  perform.
Once decided, wire the calls in and un-skip the 3 tests in
`TestHandleLlmTurnOptionalCallbacks`, adjusting them only if the exact
call site changes their expected call counts (e.g. if a callback should fire
per-tool-round instead of per-turn).

## Target Files or Areas
- `scripts/agent/llm_turn_executor.py` (`call_on_turn_end`, `call_on_llm_wait_end` helpers already exist)
- `scripts/agent/llm_turn_runner.py` (`_stream_llm`, `run`)
- `scripts/agent/audit_event_emitter.py` (`emit_turn_start`, `emit_turn_end`)
- `scripts/agent/orchestrator.py` (`_execute_turn`, `__init__`)
- `tests/agent/test_orchestrator.py::TestHandleLlmTurnOptionalCallbacks`

## Required Changes
- Wire `on_llm_wait_start`/`on_llm_wait_end` around the actual LLM stream call.
- Wire `on_turn_start`/`on_turn_end` at the appropriate turn-boundary call site.
- Remove or repurpose whichever now-redundant callback storage (three classes
  currently duplicate these same constructor parameters) once the real call
  site is settled.
- Un-skip `TestHandleLlmTurnOptionalCallbacks`'s 3 tests.

## Constraints
N/A: covered by Implementation Intent — the constraint is picking one
consistent call site per callback, not a technical limitation.

## Acceptance Criteria
- `uv run pytest tests/agent/test_orchestrator.py::TestHandleLlmTurnOptionalCallbacks -q` passes with the skip removed.
- No other currently-passing test in `tests/agent/test_orchestrator.py` or
  `tests/integration/test_orchestrator_integration.py` regresses.

## Testing Expectations
Full `tests/agent/test_orchestrator.py` and
`tests/integration/test_orchestrator_integration.py` regression run after the
change.

## Documentation Impact
N/A: covered by Summary — no user-facing docs currently describe these
callbacks' invocation semantics to update.

## Out of Scope
Do not change `on_error` wiring — already fixed and verified in this session
(see `LlmTurnExecutor.handle_llm_turn()`'s call to `self.call_on_error(...)`).

## Dependencies
N/A: none

## Unresolved Questions
- Should `on_turn_start`/`on_turn_end` fire from the same call sites as
  `AuditEventEmitter.emit_turn_start()`/`emit_turn_end()`, or independently?
- Should `on_llm_wait_start`'s return value (if any) be threaded through to
  `on_llm_wait_end`, given its type hint is `Callable[[], Any]` rather than
  `Callable[[], None]`?

## AI Implementation Instruction
Do not guess the call site unilaterally — confirm the intended semantics
(especially whether `on_turn_start`/`on_turn_end` should be layered onto the
existing audit-emitter call sites or fire independently) before wiring this
in, since three separate classes currently duplicate these same constructor
parameters without any of them being the obvious single source of truth.

## Traceability
- **Workflow phase**: N/A: manually filed
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20260911-150000
- **Related target files**: scripts/agent/llm_turn_executor.py, scripts/agent/llm_turn_runner.py, scripts/agent/audit_event_emitter.py, scripts/agent/orchestrator.py, tests/agent/test_orchestrator.py
