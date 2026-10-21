# Session persistence is skipped when startup fails, because it is reached only through the input loop

## Priority
Medium

## Summary
Make session persistence run on every exit path of `AgentREPL.run()`, in the same bracket as resource
shutdown, instead of only when the input loop was entered.

## Background
`AgentREPL._persist_after_loop()` persists session memories and diagnostics
(`scripts/agent/repl.py:105-108`). It is passed as the second argument of `ReplInputLoop.run()`
(`repl.py:157-160`, parameter `persister_callback` at `scripts/agent/repl_input_loop.py:76-82`), and that
method invokes it in its own `finally` (`repl_input_loop.py:111-115`). `AgentREPL.run()` wraps the whole
session in one `try:` (`repl.py:127`) whose only `finally` calls `close_resources()`
(`repl.py:161-162`), with the deliberate comment at `:124-126` that cleanup must run "on every exit path
(startup failure or interrupt, normal exit) but never ahead of the input loop".

## Problem
When `startup.run()` raises — a configuration error, an MCP startup failure, or `StartupInterrupted` — the
input loop is never entered (`repl.py:144` is not reached), so its `finally` never runs and neither
`persist_session_memories()` nor `persist_session_diagnostics()` is called. Resource shutdown still runs.
The asymmetry is visible in this environment: recent startup attempts ended with a FATAL
`mcp_tool_discovery` result before the REPL was reached, so whatever the startup path had already written to
in-memory session state was never persisted. Two related gaps:
- `_persist_after_loop` is invoked from a bare `finally` with no `except`, so a persistence failure on the
  normal path propagates out of the loop call. Needs-confirmation resolved: `SessionPersister` contains
  `(OSError, sqlite3.Error)` and `(RuntimeError, sqlite3.Error)` internally, but not the exception classes a
  malformed payload can raise (see Verification).
- Whether startup work (for example memory ingestion during startup) is expected to be persisted on a failed
  startup is not stated anywhere in code or docs.

### Verification (re-read at HEAD `c610780db`, 2026-10-22)

Confirmed against the current tree:

- `AgentREPL.run()` returns `None` and does **not** convert a startup failure into a status code:
  `except StartupInterrupted` (`repl.py:134-139`) and `except Exception` (`:140-142`) both write a message
  and `raise`, so the exception escapes the `finally` at `:161-162` and out of
  `asyncio.run(AgentREPL().run())` (`repl.py:172`). The only cleanup that runs on that path is
  `close_resources()`.
- `self._input_loop.bind(self._cmds, self._orchestrator)` (`repl.py:144`) is the only place
  `ReplInputLoop._cmds` / `_orchestrator` are assigned (`repl_input_loop.py`), so on a startup failure the
  input loop could not have run even if it had been entered.
- The only value ever passed as `persister_callback` is the bound method at `repl.py:159`. `grep -rn
  "persister_callback" scripts/` → `repl_input_loop.py:79`, `:112`, `:113` only; `grep -rn
  "_persist_after_loop" tests/` → no match. `tests/agent/test_repl.py` passes a bare `AsyncMock()` 18 times
  (`:150`, `:159`, …, `:435`) and asserts on it zero times.
- What the persist step actually writes is two things and nothing else: a `kind="session_summary"` row
  (`session_persister.py:111-149`) and `memory.on_session_stop(...)` (`:174-178`). Per-event diagnostics
  (`transport_failure`, `serialization_event`, `partial_completion`, `guard_hint`, `llm_transport_error`) are
  inserted inline at their own call sites (`llm_turn_runner.py:154`, `:161`, `:170`; `tool_runner.py:132`;
  `tool_run_recorder.py:108`; `tool_loop_guard.py:141`; `session.py:94`) and never deferred to this step.
- Nothing that the persist step reads can exist without a started session. `ctx.session` is a bare
  `AgentSession()` (`context.py:332`); `session_id` is assigned only at `session.py:148`, reached only from
  `repl_input_loop.py:88`; `AgentSession.replace_messages` (`session.py:80-84`) and
  `AgentSession.save_diagnostic` (`session.py:89-93`) already skip silently in exactly that state;
  `MemoryIngestionService.on_session_stop` returns at `memory/ingestion.py:87-89` when history yields no
  entries, and history is empty on a startup-failure path.
- Ungated persistence is not harmless. `DiagnosticStore.save(session_id=None, …)` **does** insert a row:
  measured with a real temporary `session_diagnostics` table (`/tmp/opencode/shutdown002_probe2.py`), the row
  landed as `(1, None, 'session_summary')`. `session_diagnostics.session_id` is a nullable FK
  (`scripts/db/schema_sql.py:140-147`), so nothing in the schema rejects it. The live `/opt/llm/db/
  session.sqlite` holds 6 `session_summary` rows and none with a null `session_id` — because in practice
  `session.start()` fails when the whole schema is missing, which is the other case: with no table the
  `INSERT` raises `sqlite3.OperationalError`, is caught at `session_persister.py:150`, and writes a third
  operator-facing line (`:152`).
- The input-loop path already double-reports the same error. `SchemaMissingError` is a `RuntimeError`
  (`session.py:19`); it is caught, printed and re-raised at `repl_input_loop.py:89-91` and then caught and
  printed **again** by the outer `except RuntimeError` at `:108-110`. Measured (
  `/tmp/opencode/shutdown002_probe.py`): the same `Session schema missing. Run: bash deploy/init_db.sh to
  initialize the database.` line is printed twice as `[fatal]`.
- A `finally` exception replaces the exception that is already propagating. Same probe: the session-start
  error that had been reported and re-raised was replaced in the traceback by `TypeError: Object of type
  MagicMock is not JSON serializable` raised from the persist `finally`, and `session.session_id` stayed
  `None` with zero `session_diagnostics` rows. In production the payload is built from `services=None`
  defaults (`session_persister.py:54`, `:56`, `:118-126`), but the guard at `:154` accepts only
  `(OSError, sqlite3.Error)`, so a payload defect is not contained.
- Existing coverage cannot express this decision: `tests/agent/test_repl.py:505-512`
  (`test_handles_none_session_id`) is the closest case and contains **no assertion**; it patches
  `agent.wal_checkpoint_manager.SQLiteHelper` (`:511`), which `SessionPersister` never calls.
  `TestRunStartupInterrupted` (`:810-873`) drives both startup-failure branches and asserts only the message
  text and `close_resources.assert_awaited()`. `TestAgentREPLRunSubprocessTermination` (`:1364-1475`) asserts
  the recorded cleanup calls are exactly `["close_resources"]` (`:1459`, `:1474`).
- Store-level intent is deliberately different and must not be narrowed by this change:
  `tests/agent/test_regression_diagnostic_persist.py:114-123` asserts that
  `DiagnosticStore.save(session_id=None, …)` is stored and retrievable. The gate therefore belongs to the
  session-level persist step, not to `DiagnosticStore`.
- Documentation claim that this issue contradicts: `docs/01_overview/overview_01_03-arch-features.md:65`
  states persistence happens "After the REPL input loop ends", which is exactly the behavior being changed.
  `docs/23_agent/agent_10_01_operations-and-observability-startup-and-health.md:76-82` documents the cleanup
  order "when the interactive session ends **or when startup fails or is interrupted**" and lists four
  steps, none of which is persistence.

## Reason for Change
The persistence step is the only place session memories and diagnostics reach the session DB. Making it
reachable from exactly one code path means any startup failure silently discards that state, while the DB
checkpoint for the same session still runs.

## Implementation Intent
Own the shutdown sequence in `AgentREPL.run()`: persist first, then close resources, on all paths, with each
step reporting its own failure.

## Target Files or Areas
- `scripts/agent/repl.py` (`run`, `_persist_after_loop` → the single exit bracket)
- `scripts/agent/repl_input_loop.py` (`run`, `persister_callback` parameter and its `finally`, the duplicate
  `except` report at `:89-91` / `:108-110`)
- `scripts/agent/session_persister.py` (the one place the "is there a session to persist for?" decision lives;
  the issue originally listed this file as reference only — verification shows the decision must be owned here)
- `tests/agent/test_repl.py` (startup-failure and ordering assertions, the 18 `persister_callback` call sites,
  `test_handles_none_session_id`)
- `tests/agent/test_session_persister.py` (new; the mirror file for the gate and containment behavior)
- `docs/23_agent/agent_10_01_operations-and-observability-startup-and-health.md` (`:76-82`)
- `docs/01_overview/overview_01_03-arch-features.md` (`:65`)

## Required Changes
- Decide explicitly whether persistence must run after a failed startup, and encode that decision in one
  place rather than through a callback that happens to be nested inside the input loop. Resolved: **no session
  state is persisted when no session was started, and that is a stated, logged skip rather than an accident.**
  The persist step is reached on every exit path; the decision to write or skip is owned by
  `SessionPersister` and keyed on `ctx.session.session_id`, because every value the step reads or writes is
  keyed to a `sessions` row that does not exist on that path (Verification).
- Move the call into `AgentREPL.run()`'s bracket before `close_resources()`, and remove the
  `persister_callback` indirection. Resolved: yes — two owners of one step is what made the behavior
  path-dependent.
- Report persistence failures through the CLI view with a non-fatal severity, and keep them from masking the
  original startup error. Today a persist exception replaces the propagating exception (measured), and the
  persister's outer guard does not cover payload defects.
- Do not report the same input-loop error twice (`repl_input_loop.py:89-91` then `:108-110`).
- Document the intended order (persist → checkpoint → backup → close services → close HTTP client) and why
  that order is required.

## Constraints
- Persistence must not run after `close_resources()` closes the shared HTTP client — that ordering constraint
  is the reason the current nesting exists.
- `ReplInputLoop.run(on_startup, persister_callback)` is an existing contract used by `repl.py:157-160` and by
  tests; changing it must be done together with `tests/agent/test_repl.py`.
- A startup failure must not be replaced by a secondary persistence error.
- Do not create a session row or session DB write where no session was created.

## Acceptance Criteria
- For a forced startup failure, the chosen behavior is asserted by a test and stated in a docstring and in
  `docs/`: the persist step is reached, and it performs no session DB write and no memory ingestion because no
  session exists.
- On the normal exit path, persistence still runs before `close_resources()`, in that order, asserted by a
  test that records both calls.
- A persistence failure produces a distinguishable non-fatal message and does not change the exception, exit
  status, or reported error of the path that was already failing.
- One error raised inside the input loop produces exactly one operator-facing line for that error.
- No `session_diagnostics` row is written with a null `session_id` by the session persist step, while
  `tests/agent/test_regression_diagnostic_persist.py:114-123` (store-level `session_id=None`) still passes.

## Testing Expectations
- Regression test: `AgentREPL.run()` with `startup.run()` stubbed to raise, asserting the persistence decision
  (the step is reached; `DiagnosticStore.save` and `memory.on_session_stop` are not called) — assert on the
  documented behavior, not on incidental calls.
- Ordering test: assert persist is called before `close_resources()` on the normal path.
- Unit tests in `tests/agent/test_session_persister.py`: the gate skips with a stated reason for a
  session-less context; a payload or store defect is contained and reported as non-fatal; a started session
  still persists.
- `uv run pytest tests/agent/test_repl.py tests/agent/test_session_persister.py
  tests/agent/test_repl_error_handling.py tests/agent/test_regression_diagnostic_persist.py -q` and the full
  `uv run pytest tests/agent -q`.

## Documentation Impact
State the shutdown sequence as an ordered contract (what is persisted, what is closed, in which order, on
which exit paths) in `docs/23_agent/agent_10_01_operations-and-observability-startup-and-health.md`, and
replace the false timing claim at `docs/01_overview/overview_01_03-arch-features.md:65`. A failed startup not
persisting session state is recorded as by design, with its reason, not as a Known Issue.

## Out of Scope
- The persistence content itself (what memories/diagnostics are written).
- WAL checkpoint bounds (`shutdown001`).
- Signal handling (`repl001`).

## Dependencies
- `repl001` owns the same `repl.py:110-162` region (shutdown-event ownership) and `repl_input_loop.py`'s
  mid-turn cancellation path; this issue's edits are in the same `run()` body, so the two must not be
  implemented in the same pass.
- `shutdown001` owns `close_resources()`'s body. This issue changes only the bracket that *calls* it.
- The `repl003` wiring guard is useful here but not required: the assertions in this issue are reachable
  through the existing fixtures at `tests/agent/test_repl.py:28-88`.

## Unresolved Questions
Resolved by the verification above:
- Should a failed startup persist anything at all? No. No session exists, and every value the persist step
  reads or writes is keyed to a `sessions` row. The step is still reached, and it records an explicit skip.
- Should `persister_callback` remain a parameter of `ReplInputLoop.run()`? No. The step has one owner.

Still open:
- Which handler reports an input-loop error exactly once: keep the outer `except RuntimeError`
  (`repl_input_loop.py:108-110`) as the single reporter, or make each inner handler the only reporter for its
  own class. The second is a smaller edit; the first keeps a safety net for errors raised deeper in the loop.
  Needs a decision during implementation (tracked as an unknown in the plan).
- Whether a persistence failure should be visible only as a non-fatal CLI line, or also change the process
  exit status. The current code has no status code to change (`run()` returns `None`), so the plan keeps it
  non-fatal; promoting it to a distinct exit status is a separate decision.

## AI Implementation Instruction
Make the shutdown bracket explicit in one function instead of relying on nested `finally` blocks. State the
ordering requirement in code comments that match the tests.

## Traceability
- **Workflow phase**: `python-code-review` (startup/shutdown lifecycle review), filed via `issue-creator`
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261021-093421
- **Related target files**: `scripts/agent/repl.py`, `scripts/agent/repl_input_loop.py`,
  `scripts/agent/session_persister.py`
