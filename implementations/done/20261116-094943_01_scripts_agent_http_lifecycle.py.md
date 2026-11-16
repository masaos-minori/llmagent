## Goal

Make `HttpServerLifecycleManager.start` never report success for a process that a failed start left tracked with its exit unconfirmed: it re-terminates that process and proceeds only on a confirmed exit, otherwise it raises the startup failure again and keeps the process tracked (`REQ-001`: no success without a health check; `REQ-002`: healthy processes still reused; `REQ-003`: `shutdown_all` still names an unconfirmed process; `REQ-004`: manager-level tests).

## Scope
**Release unit**: N/A: not part of a release unit

- In scope: `scripts/agent/http_lifecycle.py` (a failed-start record, its use in `start`, its release points) and its companion test file `tests/agent/test_http_lifecycle_integration.py`.
- Out of scope: termination timeouts and the terminator's confirmation logic, `HealthChecker.poll_until_ready`, `McpServerStarter`, the failure cooldown of `ensure_ready`/`restart`, and `restart()` launching a new process while the old one is unconfirmed (`UNK-03` of the Plan).

## Assumptions

- Source plan `plans/20261115-220300_startrev003_retry-reuses-unconfirmed-process.md` was corrected in this cycle (Step 3a): the record is bound to the leftover process object and is also released in `remove_process_entry`. Reason: `ShutdownCoordinator.shutdown_all` pops the process entry through `remove_process_entry` before terminating and keeps the pgid when the exit stays unconfirmed, and `SubprocessLauncher` pops `_http_procs` itself on a `getpgid` failure; a key-only record would survive those paths and make a later `start` re-terminate a healthy, freshly launched process.
- Overlap judgment: no other Frozen Plan targets `scripts/agent/http_lifecycle.py`. `tests/agent/test_startup_mcp_lifecycle.py` is shared with Plan `startrev002`, which is compatible and sequenced first (see document `03`).
- `_raise_startup_failure_unconfirmed` has two callers, both in `HealthChecker.poll_until_ready`; `cleanup_server_key` is called by `ShutdownCoordinator`; `start` is called by `_SubprocessLifecycleManager.start_http_subprocess` and by `ensure_ready` (re-read in Step 3a).
- `scripts/agent/http_lifecycle.py` is 15326 bytes against a 24576 byte module size limit, so the change fits without a split.
- Test file `tests/agent/test_http_lifecycle_integration.py` is a companion: it is a Plan row under `tests/`, only the `http_lifecycle.py` row names it in `Related Tests` (besides itself), and its cases are fully specified by the Plan.

## Design decisions

- Keep a per-key mapping from the server key to the leftover process object, written in `_raise_startup_failure_unconfirmed`. The reuse branch of `start` acts on the record only when the tracked process `is` the recorded object, so a record that outlived its process can never apply to a newer one.
- Release the record at every point where tracking is released: `cleanup_server_key`, `remove_process_entry`, `_raise_startup_failure`, `restart`, and a confirmed re-termination inside `start`. A fresh launch replaces the tracked process, which ends the record's effect even if a release was missed.

## Alternatives considered

- Always re-terminating a live tracked process in `start`: rejected, it would kill healthy servers on every idempotent `ensure_ready`/`start`.
- Dropping the process from tracking on an unconfirmed failure: rejected, `shutdown_all` would stop naming it.
- A key-only set (the Plan's first version): rejected after verification, because it can go stale through `remove_process_entry` and the launcher's failure cleanup.

## Implementation
### Target file
`scripts/agent/http_lifecycle.py`

### Procedure
1. In `__init__`, add the mapping `_failed_start_procs` (new), a `dict[str, subprocess.Popen[bytes]]`, next to the other per-key tracking dicts.
2. In `_raise_startup_failure_unconfirmed`, store the tracked process for the key in `_failed_start_procs` (new) before raising, when the tracked process exists.
3. Release the record (pop the key) in `cleanup_server_key`, `remove_process_entry`, `_raise_startup_failure` and `restart`.
4. In `start`, change the reuse branch: when `existing` is alive and `_failed_start_procs` (new) holds that same object for the key, do not return. Terminate it again with the terminator (reusing `_terminate_for_startup_failure` from `agent/http_lifecycle_health_checker.py`, which already classifies a terminator exception as unconfirmed); on a confirmed outcome release the tracking (process, pgid, record, stderr and health-check data, as the confirmed startup-failure path does) and fall through to the fresh launch; on an unconfirmed outcome call `_raise_startup_failure_unconfirmed` (stderr text from `_stderr_log_manager.read_tail`) so the tracking and the record stay. A tracked live process with no matching record is reused exactly as today.

### Method
- Add the import of `_terminate_for_startup_failure` to the existing `from .http_lifecycle_health_checker import ...` line; the module already imports from that file and `lint-imports` is unaffected. If a reviewer rejects the private-name import, the fallback is a short inline `try/except OSError` around `self._process_terminator.terminate_with_timeout(existing, server_key, timeout=TERMINATE_TIMEOUT_SEC)` returning `TerminationOutcome.EXIT_UNCONFIRMED` on failure; do not change the health checker module.
- Log the re-termination decision at INFO and an unconfirmed result through the existing error log in `_raise_startup_failure_unconfirmed`; keep the `kill -TERM -<pgid>` hint and the pid/pgid fields unchanged (`REQ-003`).
- No signature changes; `shutdown_all` and `ShutdownCoordinator` are not edited.

### Details
- `_failed_start_procs` (new) is cleared by the same code that clears `_http_procs` entries; after `shutdown_all` finishes with an unconfirmed exit it holds no entry for the key (the process entry is gone), and the pgid and stderr-log tracking that `shutdown_all` keeps are unchanged.
- Radon: `start` must stay below grade C after the added branch; move the re-termination into a small private method of the manager if it would not.

### Companion test files
- `tests/agent/test_http_lifecycle_integration.py`
  - Procedure: write these tests first, in `TestStartupFailureTerminateOrTrack` using the `mgr` fixture and a patched `terminate_with_timeout` `AsyncMock`, and confirm they fail on the current code: (a) after an unconfirmed failed start, a second `start` re-terminates, raises `HttpStartupError` while the terminator keeps returning `EXIT_UNCONFIRMED`, does not launch, and keeps process, pgid and record; (b) with the terminator returning `EXIT_UNCONFIRMED` then `EXITED`, the second `start` launches a fresh process (patch the launcher) and the record is released; (c) a tracked live process with no record is reused on repeated `start` with no terminator call; (d) a record naming an older process object than the tracked one is ignored (reused, no terminator call); (e) `shutdown_all` after an unconfirmed failure and an unconfirmed re-termination still returns the server and logs its pid and pgid; (f) the record is released by a confirmed shutdown, a confirmed failed start, `restart` and `remove_process_entry`.
  - Validation: `uv run pytest tests/agent/test_http_lifecycle_integration.py tests/agent/test_http_lifecycle.py tests/agent/test_http_lifecycle_health_check.py tests/agent/test_http_lifecycle_shutdown_coordinator.py -q`.

## Compatibility considerations

- Behavior changes only for a key that failed a start with an unconfirmed exit and whose process object is still the tracked one; every other `start`, `ensure_ready` and `restart` path is unchanged.
- No public signature changes; `HealthChecker`, `McpServerStarter` and `ShutdownCoordinator` keep their contracts.

## Security considerations

- Re-terminating signals only the process group the manager itself launched and tracked; the identity binding prevents signaling a process the record does not describe. Log lines keep their current fields and are not extended with command lines or secrets.

## Rollback considerations

- Revert the commit; the record is in-memory only, so no persisted state needs cleanup.

## Validation plan

- Run the targeted pytest command above; the unconfirmed-reuse tests fail on the pre-change code and pass after.
- `uv run ruff format`, `uv run ruff check scripts/`, `uv run mypy --no-namespace-packages scripts/`, `PYTHONPATH=scripts uv run lint-imports`.
- `uv run python tools/check_module_size.py` and `uv run python tools/generate_reference_table.py --check`.
- Diff coverage per `rules/toolchain.md` section 7.

## Completion criteria

- A second `start` after an unconfirmed failed start does not return success: it raises `HttpStartupError` while the exit stays unconfirmed (tracking and record kept), and launches a fresh process after a confirmed re-termination (`REQ-001`, AC-1, AC-2).
- A healthy tracked process without a matching record is still reused (`REQ-002`); `shutdown_all` still returns an entry for a never-confirmed process and its log line is unchanged (`REQ-003`, AC-3).
- The new tests exist and fail on the pre-change code (`REQ-004`, AC-4); AC-6 checks pass.

## Out of Scope

- `restart()` with an unconfirmed old process (`UNK-03`), health checker changes, starter changes, deployment, and the design document paragraph (document `04`).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Write the manager-level unconfirmed-reuse tests first and confirm they fail on the current code (companion `tests/agent/test_http_lifecycle_integration.py`) | Done | — | 20261116 | `TestStartupFailureTerminateOrTrack` (11 cases) added; all pass. |
| 2 | Add the identity-bound failed-start record, set it, release it at every release point, and make the reuse branch of `start` re-terminate a recorded process | Done | — | 20261116 | `_failed_start_procs` in `scripts/agent/http_lifecycle.py`; reuse branch calls `_reterminate_recorded_failed_start`. |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Done | — | 20261116 | ruff format/check, mypy (567 files), lint-imports, bandit -ll (0 high/medium), radon, module-size, reference-table, diff-cover 100%, pre-commit all pass. |

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
- **Requirement ID**: `REQ-001` (no success for an unconfirmed leftover), `REQ-002` (healthy reuse kept), `REQ-003` (`shutdown_all` still names it), `REQ-004` (manager-level tests)
- **Source issue**: issues/20261115-214903_startrev003_retry-reuses-unconfirmed-process.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261115-220300_startrev003_retry-reuses-unconfirmed-process.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261116-094943
- **Related target files**: `scripts/agent/http_lifecycle.py`, `tests/agent/test_http_lifecycle_integration.py`
