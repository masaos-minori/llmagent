# Refactor repl.py — separation of concerns (2/3)

## Priority
Medium

## Summary
Split `scripts/agent/repl.py` (869 lines) into focused modules to reduce cyclomatic complexity, improve testability, and clarify responsibility boundaries between REPL input loop, session persistence, WAL database operations, resource shutdown, and startup orchestration.

## Background
AgentREPL is the interactive REPL entry point imported by `agent.py`. It was designed as a thin coordinator over AgentContext components (LLMClient, ToolExecutor, HistoryManager, CommandRegistry, CLIView, Orchestrator), but accumulated many responsibilities through incremental additions: session diagnostics persistence, WAL checkpoint/backup during shutdown, signal handling, multiline input, and graceful shutdown timeouts.

## Problem
The AgentREPL class violates the Single Responsibility Principle by combining at least seven distinct concerns into one class:

1. **REPL input loop** — `_repl_loop`, `_read_input`, `_should_exit`, `_dispatch_line`, `_abort_input`
2. **Session persistence** — `_persist_session_memories`, `_persist_session_diagnostics`
3. **WAL database operations** — `_wal_checkpoint_sync`, `_is_db_path_allowed`, `_wal_backup_sync`
4. **Resource shutdown/cleanup** — `_close_resources`, `_log_graceful_shutdown_timeout`
5. **Startup/banner display** — `_print_startup_banner`, `_get_chunk_count`, `_get_workflow_status`
6. **Signal handling** — `run()` method's SIGTERM/SIGINT handler registration
7. **DI wiring / lifecycle** — `__init__`, `_run_repl_loop`, `run()`

This makes the class hard to understand, test in isolation, and modify without unintended side effects. Specifically:

- `_close_resources` has 10+ conditional branches across task cancellation, WAL checkpoint, WAL backup, and service shutdown paths
- `_wal_checkpoint_sync` has 5+ nested exception handlers and retry loops
- `_read_input` handles EOF, KeyboardInterrupt, shutdown event race, and multiline continuation all in one method
- Session diagnostics persistence (`_persist_session_diagnostics`) has 15+ fields extracted from disparate sources (stats, LLM stats, workflow store, diagnostic store)
- Signal handling in `run()` mixes platform-specific logic (Unix signal handlers vs Windows console control handlers)
- The class has grown beyond the 400-line threshold defined in `skills/DESIGN.md` File Split Rule trigger condition

## Reason for Change
- Cyclomatic complexity of `_close_resources`, `_wal_checkpoint_sync`, `_read_input`, and `_persist_session_diagnostics` exceeds maintainable levels
- New features require modifying this class even though they touch unrelated concerns (e.g., adding a new diagnostic metric would touch session persistence, but adding a new shutdown path would touch resource cleanup)
- Test isolation is poor — mocking the entire AgentREPL is required for most unit tests because all concerns are tightly coupled
- Platform-specific signal handling logic (Unix vs Windows) is mixed into the core REPL flow
- Session diagnostics extraction has 15+ fields from 4+ different sources, making it fragile when source schemas change

## Implementation Intent
Extract each concern into its own class/module while preserving AgentREPL as a thin facade that composes these components:

1. **ReplInputLoop** — REPL input/dispatch loop. Owns `_repl_loop`, `_read_input`, `_should_exit`, `_dispatch_line`, `_abort_input`. Handles readline, multiline continuation, shutdown event racing, and command routing.
2. **SessionPersister** — Session state persistence before shutdown. Owns `_persist_session_memories`, `_persist_session_diagnostics`. Extracts memories from history, builds diagnostics summary from stats/workflow/diagnostic stores, persists via DiagnosticStore.
3. **WalCheckpointManager** — SQLite WAL checkpoint and backup. Owns `_wal_checkpoint_sync`, `_is_db_path_allowed`, `_wal_backup_sync`. Handles PASSIVE/TRUNCATE checkpoint fallback, WAL file backup with path validation.
4. **ResourceShutdownCoordinator** — Graceful resource shutdown. Owns `_close_resources`, `_log_graceful_shutdown_timeout`. Coordinates task cancellation, WAL checkpoint, service lifecycle shutdown, HTTP client close.
5. **StartupBanner** — Startup display and status. Owns `_print_startup_banner`, `_get_chunk_count`, `_get_workflow_status`. Displays DB chunks, tool count, workflow status, memory mode.
6. **SignalHandler** — Cross-platform signal handling. Owns the `_sigterm_handler` closure and platform-specific signal registration logic (Unix `add_signal_handler` vs Windows `win32api.SetConsoleCtrlHandler`).

AgentREPL.__init__ wires these components via dependency injection. AgentREPL.run() delegates to SignalHandler for signal setup, calls StartupOrchestrator for component init, then hands off to ReplInputLoop for the main loop.

## Target Files or Areas
- `scripts/agent/repl.py` — primary target
- `scripts/agent/cli_view.py` — referenced by CLIView (display)
- `scripts/agent/context.py` — referenced by AgentContext (shared state)
- `scripts/agent/orchestrator.py` — referenced by Orchestrator (turn execution)
- `scripts/agent/startup.py` — referenced by StartupOrchestrator (component init)
- `scripts/agent/memory/models.py` — referenced by HistoryMessage
- `scripts/agent/services/rag_maintenance_service.py` — referenced by RagMaintenanceService
- `scripts/agent/session.py` — referenced by SchemaMissingError
- `scripts/agent/diagnostic_store.py` — referenced by DiagnosticStore
- `db/helper.py` — referenced by SQLiteHelper

## Required Changes
- Create new module files under `scripts/agent/` for each extracted concern (5-6 new files)
- Move methods from AgentREPL into the appropriate new class
- Update AgentREPL to compose the new classes via dependency injection
- Remove inline import of `StartupOrchestrator` from `run()` — move to top-level import since it's only guarded by TYPE_CHECKING
- Extract `_WAL_CHECKPOINT_TIMEOUT_S`, `_WAL_BACKUP_TIMEOUT_S`, `_GRACEFUL_TIMEOUT_S` constants into WalCheckpointManager and ResourceShutdownCoordinator respectively
- Extract `_EPHEMERAL_KEYS` pattern usage (from orchestrator.py) is NOT relevant here — no ephemeral keys in repl.py
- Ensure all public APIs of AgentREPL remain unchanged (backward compatibility)
- Update `__init__.py` exports if needed

## Constraints
- Must preserve all existing public method signatures and return types (backward compatibility)
- Must not change any observable behavior (no behavioral regression)
- Must not break existing import paths (e.g., `from agent.repl import AgentREPL`)
- Must not introduce circular dependencies between new modules
- The `SIGTERM`/`SIGINT` signal handling must continue to work identically on both Unix and Windows
- The `_GRACEFUL_TIMEOUT_S` timeout applies to both turn completion and shutdown sequence — do not split this into two separate timeouts without explicit design decision
- The `_n_tools` property depends on `ctx.services_required.runtime_tools` — this must remain accessible after refactor
- The `SLASH_COMMANDS` cached_property depends on `completion_command_names()` — this must remain accessible after refactor

## Acceptance Criteria
- [ ] AgentREPL class reduced to fewer than 200 lines (from 869)
- [ ] Each extracted concern has its own dedicated class with clear responsibility boundary
- [ ] All existing public methods of AgentREPL work identically after refactor
- [ ] No circular imports between new modules
- [ ] Existing import paths (`from agent.repl import AgentREPL`) continue to work
- [ ] Signal handling works identically on both Unix and Windows platforms
- [ ] WAL checkpoint/backup behavior is identical (PASSIVE → TRUNCATE fallback, path validation)
- [ ] Session diagnostics summary contains identical fields/values
- [ ] `ruff` lint passes on all modified/new files
- [ ] `mypy` type check passes on all modified/new files

## Testing Expectations
- Run existing AgentREPL unit tests to confirm no behavioral regression
- Verify each extracted class can be instantiated and tested independently
- Confirm `_repl_loop` still respects both exit conditions (/exit, shutdown_requested)
- Verify WAL checkpoint produces identical log output and error handling
- Verify session diagnostics summary structure remains identical (same keys/values)
- Verify signal handler behavior is identical on both Unix and Windows
- Run `uv run pytest` for full suite validation

## Documentation Impact
Update module docstrings for each new extracted class to describe its single responsibility. Update `repl.py` module docstring to reflect its new role as a thin composition facade. No user-facing documentation changes required.

## Out of Scope
- Changing the `_GRACEFUL_TIMEOUT_S` value or making it configurable
- Modifying StartupOrchestrator internals
- Adding new diagnostic metrics or changing the session diagnostics schema
- Changing the WAL checkpoint strategy (PASSIVE → TRUNCATE fallback)
- Adding new signal types beyond SIGTERM/SIGINT
- Modifying CLIView or other display-layer components
- Changing the command dispatch mechanism (CommandRegistry)

## Dependencies
N/A: none

## Unresolved Questions
- Should `SQLiteHelper("session")` be passed as a dependency to WalCheckpointManager instead of being constructed inside each method? Currently it's created fresh in `_wal_checkpoint_sync` and `_wal_backup_sync`.
- Should the `_sigterm_handler` closure capture `self._shutdown_event` directly, or should SignalHandler accept it as a constructor argument? Currently it captures `self` which ties it to AgentREPL instance lifetime.
- Is the current 200-line target for AgentREPL reasonable, or should we aim lower given it will become a pure composition layer?
- The `_n_tools` property and `SLASH_COMMANDS` cached_property depend on AgentREPL's internal state — should these move to StartupBanner or stay as properties?

## AI Implementation Instruction
When implementing this issue:
- Do NOT rewrite unrelated files (cli_view.py, startup.py, orchestrator.py, etc.)
- Keep changes minimal per module — move methods, update references, remove inline imports where safe
- Preserve all public method signatures exactly as-is
- Verify backward compatibility by running existing tests before closing
- Stop and report open questions if requirements are unclear — do not guess about shared dependencies
- Do not implement out-of-scope items (config changes, new features, schema changes)
