## Goal

Rebase `StartupInterrupted` from `RuntimeError` to `BaseException` (`REQ-001`, `REQ-006`)
and add an explicit `except StartupInterrupted` rollback branch to
`StartupOrchestrator.run()` so subprocess cleanup still runs on a startup-time
interrupt (`REQ-004`).

## Scope

- **In-Scope**:
  - Change `class StartupInterrupted(RuntimeError):` → `class StartupInterrupted(BaseException):`
    in `scripts/agent/startup.py` (line 30); keep the docstring/message unchanged.
  - Add an `except StartupInterrupted` branch before `except Exception as setup_err:`
    (line 77) in `run()` that calls `lifecycle.shutdown_all()` with the existing
    shutdown-failure handling and re-raises (`REQ-004`).
- **Out-of-Scope**:
  - Any change to `scripts/agent/startup_mcp_starter.py` (the `except StartupInterrupted:
    raise` guard there is a separate procedure), `repl.py`, or retry behavior.
  - Renaming `StartupInterrupted` or changing its message / string repr (`REQ-006`).

## Assumptions

- **ASM-001**: `StartupInterrupted` is only raised in `startup_mcp_starter.py` and
  `shared/retry_helper.py`; only handlers on those call paths can intercept it.
- **ASM-002**: No caller or test asserts `isinstance(exc, RuntimeError)` for a
  `StartupInterrupted` (verified: `isinstance(..., RuntimeError)` assertions in
  `tests/` target other exceptions).
- **ASM-003**: `lifecycle.shutdown_all()` is idempotent, so preserving rollback in
  `run()` (which already double-closes today) is safe.

## Design decisions

- Rebase to `BaseException`: it is automatically excluded from every `except Exception`
  / `except RuntimeError` clause, so `retry_once_with_delay()` (line 42) and `run()`'s
  generic handler no longer intercept it (`REQ-001`, `REQ-002`).
- Add a dedicated `except StartupInterrupted` rollback branch before the generic handler
  because the rebase removes `StartupInterrupted` from `except Exception`, restoring the
  fail-closed rollback that `REQ-004` requires.

## Alternatives considered

- Removing `RuntimeError` from `start_servers()`'s first-attempt tuple: rejected — it
  would drop retry for genuine transient `RuntimeError`s (`REQ-005`). That change belongs
  to `startup_mcp_starter.py` (separate procedure), which keeps `RuntimeError` and adds an
  explicit guard instead.

## Implementation

### Target file

`scripts/agent/startup.py`

### Procedure

1. Change `class StartupInterrupted(RuntimeError):` → `class StartupInterrupted(BaseException):`
   (line 30); keep the docstring.
2. Add an `except StartupInterrupted` branch immediately before `except Exception as
   setup_err:` in `run()` that calls `lifecycle.shutdown_all()` with the existing
   shutdown-failure handling and re-raises.

### Method

Edit the class definition at line 30 and the `try/except` block in `run()` (lines 72-89).
The new branch mirrors the existing rollback body exactly (logger error + `write_fatal`
on shutdown failure) and re-raises. Place it BEFORE the generic `except Exception as
setup_err:` so it takes precedence.

### Details

Current `run()` (lines 67-94):

```python
    async def run(self) -> tuple[CommandRegistry, Orchestrator]:
        """Execute full startup sequence; return (cmds, orchestrator)."""
        self._cmds, self._orchestrator = await ComponentInitializer(
            self._ctx, self._view
        ).initialize()
        try:
            self._spawned_subprocesses = await self._start_servers()
            await self._verify_mcp_health()
            await self._check_services()
            await self._setup_prompt()
        except Exception as setup_err:
            try:
                await self._ctx.services_required.lifecycle.shutdown_all()
            except Exception as shutdown_err:  # noqa: BLE001 — rollback shutdown failure must not mask the original startup error
                logger.error(
                    "CRITICAL: Startup rollback FAILED — subprocesses may be orphaned: %s",
                    shutdown_err,
                )
                self._view.write_fatal(
                    "CRITICAL: Startup rollback FAILED — subprocesses may be orphaned"
                )
            # Termination is owned exclusively by lifecycle.shutdown_all() above; run() no longer returns the spawned-subprocess list.
            raise setup_err
```

Add immediately before `except Exception as setup_err:`:

```python
        except StartupInterrupted:
            try:
                await self._ctx.services_required.lifecycle.shutdown_all()
            except Exception as shutdown_err:  # noqa: BLE001 — rollback shutdown failure must not mask the original interrupt
                logger.error(
                    "CRITICAL: Startup rollback FAILED — subprocesses may be orphaned: %s",
                    shutdown_err,
                )
                self._view.write_fatal(
                    "CRITICAL: Startup rollback FAILED — subprocesses may be orphaned"
                )
            raise
```

`StartupInterrupted` is defined at module scope in this same file, so the branch
references the class name directly (no import needed).

## Compatibility considerations

`AgentREPL.run()` (`repl.py:131`) has an explicit `except StartupInterrupted` that catches
either base class; no change needed (`REQ-003`). Existing
`test_startup_interrupted_triggers_rollback_like_any_other_exception` still passes: the
interrupt now hits the dedicated branch instead of the generic one, but
`shutdown_all()` is still awaited once.

## Security considerations

N/A: no auth, secret, or crypto impact. The `# noqa: BLE001` on the shutdown-failure
handler is preserved verbatim.

## Rollback considerations

Revert the two edits (base-class line and the added branch) — a single logical commit.

## Validation plan

| Target | Strategy | Command | Expected |
|---|---|---|---|
| `scripts/agent/startup.py` | Static: base is `BaseException`, not `RuntimeError`; rollback preserved | `pytest`, `mypy`, `ruff`, `bandit` | AC-001, AC-004 |
| `tests/agent/test_startup_rollback.py` | Behavior: interrupt rolls back once | `pytest` | AC-004 |
| `tests/agent/` (full) | Regression | `pytest` | All green |

## Completion criteria

- `issubclass(StartupInterrupted, RuntimeError)` is `False`;
  `issubclass(StartupInterrupted, BaseException)` is `True` (AC-001).
- A `StartupInterrupted` raised from `_start_servers()` triggers exactly one
  `shutdown_all()` call and re-raises (AC-004).
- `test_startup_interrupted_triggers_rollback_like_any_other_exception` passes.

## Out of Scope

`scripts/agent/startup_mcp_starter.py` (guard is a separate procedure), `repl.py`, retry
timing, any other startup exception.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | — | 20261022-095438 |  |
| 2 | Add or update tests per Validation plan | Completed | — | 20261022-095438 |  |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | — | 20261022-095438 |  |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | — | 20261022-095438 | N/A: no docs map to `startup.py` |

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
- **Requirement ID**: REQ-001, REQ-004, REQ-006
- **Source issue**: `issues/20261021-220332_star002_make-startupinterrupted-distinguishable-from-ordinary-runtimeerror-in-broad-startup-handlers.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/done/20261021-232426_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261022-072226
- **Related target files**: `scripts/agent/startup.py`