# Refactor http_lifecycle.py — separation of concerns

## Priority
Medium

## Summary
Split `scripts/agent/http_lifecycle.py`'s `HttpServerLifecycleManager` class (611 lines) into focused modules to separate its security-critical command validation from process spawning, stderr log management, health/liveness checking, process introspection, and bulk shutdown — currently combined in one class whose `start()` method alone is ~190 lines.

## Background
The module docstring states this file was "Extracted from lifecycle.py," with `_ServerLifecycleRouter` in `factory.py` delegating to `HttpServerLifecycleManager` for all HTTP subprocess operations. After that extraction, `HttpServerLifecycleManager` accumulated several independent responsibilities in one class rather than being split further. Similar splits were already completed for `scripts/agent/orchestrator.py`, `scripts/agent/repl.py`, `scripts/rag/ingestion/ingester.py`, and (pending) `scripts/rag/pipeline.py` and `scripts/agent/repl_health.py` (see `issues/done/20260829-080923_refactor_001_orchestrator_separation.md`, `_002_repl_separation.md`, `_003_ingester_separation.md`, and this session's `refactor_004`/`refactor_006` issues).

## Problem
`HttpServerLifecycleManager` exceeds the 400-line threshold defined in `skills/DESIGN.md` File Split Rule trigger condition (611 lines) and combines at least six distinct concerns:

1. **Command validation and subprocess spawn** — the first ~90 lines of `start()` (roughly lines 350-449): resolves `cfg.cmd[0]` via `shutil.which`, resolves symlinks via `os.path.realpath`, verifies the resolved path is a regular file, checks the basename against `_ALLOWED_COMMANDS`, filters environment variables against `_PROTECTED_ENV_VARS`, and calls `subprocess.Popen`. This is security-relevant validation logic mixed into the same method as process startup.
2. **Startup health-poll orchestration** — the remainder of `start()` (roughly lines 451-513): polls the `/health` endpoint until ready, exited, or timed out, racing against an optional `shutdown_event`.
3. **Stderr log management** — `_open_stderr_log`, `_read_stderr_tail`, `_rotate_log` — per-server append-mode log files with size-based rotation.
4. **Process termination** — `_wait_exited`, `_terminate_with_timeout` — polling-based exit detection (deliberately avoiding `asyncio.to_thread`, per its own docstring) and terminate-then-kill escalation via process-group signals.
5. **Health/liveness checking** — `verify_running`, `verify_running_async`, `_compute_health_check_timeout`, `_interruptible_poll_sleep` — rate-limited `/health` polling separate from the startup poll in `start()`.
6. **Process introspection** — `_snapshot_fields`, `get_process_info`, `get_process_snapshot`, `list_processes` — read-only snapshots of managed subprocess state.
7. **Bulk shutdown with signal protection** — `shutdown_all`, `_absorb_sigint_during_shutdown` — terminates all managed subprocesses while temporarily overriding `SIGINT` to prevent a user's second Ctrl-C from orphaning subprocesses mid-cleanup.

`start()` in particular threads command validation, environment filtering, subprocess spawning, `pgid` capture with its own cleanup-on-failure branch, and health-poll orchestration into a single ~190-line method, making the command-allowlist logic (a security control) impossible to unit-test without also exercising the full startup and health-poll sequence.

## Reason for Change
- The command-validation logic inside `start()` (allowlist check, symlink resolution, regular-file check) is a security control that currently cannot be tested in isolation from process spawning and health polling — increasing the risk that a future change to `start()` accidentally weakens validation without a dedicated test catching it.
- Stderr log rotation, process termination, and health-checking each have their own independent failure modes and are already partially isolated via private helper methods, but remain coupled to the same class as startup and shutdown orchestration.
- `shutdown_all()`'s `SIGINT`-absorption logic is a distinct, subtle piece of signal-handling code that would benefit from independent testing rather than being verified only as a side effect of full-manager shutdown tests.

## Implementation Intent
Extract the concerns above into separate modules/classes, following the constructor-injection / delegation pattern already used for the `orchestrator.py` and `ingester.py` splits. Suggested (not mandatory) grouping, left for the implementation planning phase to finalize:
- **Command validator** — owns the allowlist/path-resolution/regular-file checks currently inline in `start()`, returning a validated executable path or raising `HttpStartupError`.
- **Stderr log manager** — owns `_open_stderr_log`, `_read_stderr_tail`, `_rotate_log`.
- **Process terminator** — owns `_wait_exited`, `_terminate_with_timeout`.
- **Health checker** — owns `verify_running`, `verify_running_async`, `_compute_health_check_timeout`, `_interruptible_poll_sleep`, and the health-poll loop portion of `start()`.
- **Process snapshot provider** — owns `_snapshot_fields`, `get_process_info`, `get_process_snapshot`, `list_processes`.
- **Shutdown coordinator** — owns `shutdown_all`, `_absorb_sigint_during_shutdown`.

`HttpServerLifecycleManager` should become a thinner composition facade wiring these components together, preserving its public interface (`start`, `restart`, `shutdown_all`, `verify_running`, `verify_running_async`, `get_process_info`, `get_process_snapshot`, `list_processes`) exactly, since `factory.py` calls these directly.

## Target Files or Areas
- `scripts/agent/http_lifecycle.py` — primary target
- `scripts/agent/factory.py` — consumer (`_ServerLifecycleRouter` delegates to `HttpServerLifecycleManager`); must continue to work unmodified
- `scripts/agent/lifecycle_protocol.py` — defines `LifecycleManagerProtocol`; referenced, not modified (the protocol describes `_ServerLifecycleRouter`, not `HttpServerLifecycleManager`, directly)
- `scripts/agent/secrets_masker.py` — referenced by `_mask_secrets`
- `scripts/agent/services/models.py` — referenced by `ProcessInfoSnapshot`
- `tests/agent/test_http_lifecycle_integration.py`, `test_http_lifecycle_warning.py` — to be reorganized alongside the split
- Documentation: Unknown — check `docs/00_index.md`'s task-scope mapping against whichever files actually change; `docs/04_mcp_03_05_lifecycle-and-new-server.md` and `docs/04_mcp_06_05_long-running-http-operation-startup_modesubprocess.md` are the likely candidates

## Required Changes
- Extract the command-validation logic inside `start()` into its own validator, independently testable against the allowlist/symlink/regular-file rules.
- Extract stderr log management, process termination, health checking, process introspection, and bulk shutdown into separate units as described under Implementation Intent.
- Reduce `HttpServerLifecycleManager` to a thin composition facade delegating to the extracted components.
- Preserve `HttpServerLifecycleManager`'s public interface (`start`, `restart`, `shutdown_all`, `verify_running`, `verify_running_async`, `get_process_info`, `get_process_snapshot`, `list_processes`) with identical signatures, return types, and exception-raising conditions.
- Reorganize `test_http_lifecycle_integration.py`/`test_http_lifecycle_warning.py` to mirror the new module boundaries where it clarifies ownership, without losing existing coverage.

## Constraints
- Do not weaken or change the command-allowlist validation logic (`_ALLOWED_COMMANDS`, symlink resolution, regular-file check) — this is a security control; behavior must be bit-for-bit identical before and after extraction.
- Do not change the process-group-based termination strategy (`os.killpg` with `SIGTERM`→`SIGKILL` escalation) or its timeouts.
- Do not change the `SIGINT`-absorption behavior in `shutdown_all()`.
- Do not change any existing log message string.
- `factory.py`'s existing calls into `HttpServerLifecycleManager` must continue to work without modification.

## Acceptance Criteria
- Each resulting module/class addresses exactly one of the six concerns listed under Implementation Intent.
- `HttpServerLifecycleManager`'s public methods retain identical signatures, return types, and exception behavior after the refactor.
- The command-validation logic is independently unit-testable without exercising subprocess spawning or health polling.
- `scripts/agent/factory.py`'s usage of `HttpServerLifecycleManager` continues to work unmodified.
- All pre-existing tests in `test_http_lifecycle_integration.py` and `test_http_lifecycle_warning.py` pass unchanged in outcome (reorganized as needed).
- `ruff`, `mypy`, and `bandit` are clean on all new/modified files — pay particular attention to `bandit`'s `subprocess`-related findings (`B404`/`B603`) retaining their existing `# nosec` justifications.
- A full `uv run pytest` run shows no new failures compared to the pre-change baseline.

## Testing Expectations
- Run `test_http_lifecycle_integration.py` and `test_http_lifecycle_warning.py` (reorganized to match the new module layout) and confirm no behavioral regression.
- Add or confirm dedicated unit tests for the extracted command validator covering: disallowed command, command not in `PATH`, symlink-resolved path not a regular file, and an allowed command succeeding.
- Run the full `uv run pytest` suite once after implementation and compare against the pre-change baseline for new failures.
- Apply the standard validation sequence in `rules/toolchain.md` (format → lint → type → arch → security → test → coverage), with particular attention to the `bandit` security scan given this file's subprocess-execution surface.

## Documentation Impact
Unknown whether `docs/04_mcp_03_05_lifecycle-and-new-server.md` or `docs/04_mcp_06_05_long-running-http-operation-startup_modesubprocess.md` reference `HttpServerLifecycleManager`'s internal method names or class structure directly — check `docs/00_index.md`'s "Document References by Task" table against whichever files this issue's implementation actually touches, and update only the matched row(s). Do not proactively write new documentation beyond what routing directs.

## Out of Scope
- Changing the command-allowlist contents (`_ALLOWED_COMMANDS`) or the protected-env-var list (`_PROTECTED_ENV_VARS`).
- Changing the process-group termination strategy or its timeouts.
- Changing the stderr log rotation policy or its size/count limits.
- Adding new lifecycle operations beyond start/restart/shutdown.
- Modifying `scripts/agent/factory.py` or `lifecycle_protocol.py` beyond what's needed to keep imports working.
- Performance optimization of the health-poll or subprocess-spawn paths.

## Dependencies
N/A: none

## Unresolved Questions
- Exact module names and file layout for the six extracted concerns are left to the `issue-to-plan` / `plan-to-implementation-procedure` phases.
- Whether the health-poll loop inside `start()` should move entirely into the health-checker unit, or remain partially in a startup orchestrator that composes the health checker, is left to the implementer to decide and document in the resulting plan.

## AI Implementation Instruction
- Do not change observable behavior: preserve command-validation rules, process-group termination strategy, `SIGINT`-absorption behavior, log message text, and all timeout values exactly.
- Extract the six concerns into separate modules/classes; you may follow the composition/delegation pattern used in `scripts/agent/orchestrator.py`'s and `scripts/rag/ingestion/ingester.py`'s splits as a reference, but it is not mandatory.
- Prioritize making the command-validation logic independently unit-testable — this is the primary security-relevant motivation for this issue.
- Verify `scripts/agent/factory.py` still works against the refactored `HttpServerLifecycleManager` unmodified.
- Do not touch out-of-scope items (allowlist contents, termination strategy, log rotation policy, new features).
- If a required design decision (module layout, health-poll ownership) is unclear, stop and record it under Unresolved Questions rather than guessing.
