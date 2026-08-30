# Implementation Procedure: wal_checkpoint_manager.py — WAL database operations responsibility extraction

## Goal

Create `scripts/agent/wal_checkpoint_manager.py` containing a `WalCheckpointManager` class that owns WAL database operations: `_wal_checkpoint_sync`, `_is_db_path_allowed`, `_wal_backup_sync`.

## Scope

- Create new module `scripts/agent/wal_checkpoint_manager.py`.
- Extract three methods from AgentREPL into WalCheckpointManager class.
- Move constants `_WAL_CHECKPOINT_TIMEOUT_S`, `_WAL_BACKUP_TIMEOUT_S` to WalCheckpointManager as class attributes.
- WalCheckpointManager receives AgentContext via constructor injection.

## Assumptions

- The WalCheckpointManager class will be instantiated by AgentREPL.__init__ with dependencies injected.
- The `_WAL_CHECKPOINT_TIMEOUT_S` and `_WAL_BACKUP_TIMEOUT_S` constants must move to WalCheckpointManager as class attributes.
- SQLiteHelper("session") is constructed inside each method — deferred to implementation phase whether to pass as dependency (UNK-01).

## Design decisions

- Composition over inheritance: WalCheckpointManager receives dependencies via constructor injection. No inheritance hierarchy.
- Dependency injection pattern: AgentContext received only by constructor. This enables independent instantiation and testing.
- Constant scoping: `_WAL_CHECKPOINT_TIMEOUT_S`, `_WAL_BACKUP_TIMEOUT_S` moved to WalCheckpointManager as class attributes.
- Module naming convention: Use snake_case with descriptive names matching the responsibility domain.

## Alternatives considered

- Keep SQLiteHelper("session") construction inside each method: Deferred to implementation phase (UNK-01) — evaluate during Phase 2 whether to prefer constructor injection for testability.
- Pass SQLiteHelper instance as dependency to WalCheckpointManager instead of constructing inside methods: Deferred to implementation phase (UNK-01).

## Implementation

### Target file

`scripts/agent/wal_checkpoint_manager.py`

### Procedure

1. Create module docstring describing WalCheckpointManager's single responsibility.
2. Define `WalCheckpointManager` class with constructor accepting `(ctx)`.
3. Add class attributes `_WAL_CHECKPOINT_TIMEOUT_S = 30.0` and `_WAL_BACKUP_TIMEOUT_S = 10.0`.
4. Move `_wal_checkpoint_sync`, `_is_db_path_allowed`, `_wal_backup_sync` methods.
5. Adapt method references: replace `self._ctx` with `self._ctx`, etc.

### Method

Create — write new module from scratch.

### Details

```python
"""scripts/agent/wal_checkpoint_manager.py

WalCheckpointManager — WAL database operations responsibility extraction.

Owns: _wal_checkpoint_sync, _is_db_path_allowed, _wal_backup_sync.
Handles: PASSIVE/TRUNCATE checkpoint fallback, WAL file backup with path validation.
"""

import asyncio
import os
import shutil
import time
import uuid
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from agent.context import AgentContext

logger = Logger(__name__, "/opt/llm/logs/agent.log")


class WalCheckpointManager:
    """Manages SQLite WAL checkpoint and backup operations.

    Owns WAL checkpoint (PASSIVE → TRUNCATE fallback), WAL file backup with
    path validation, and timeout handling for shutdown sequences.
    """

    _WAL_CHECKPOINT_TIMEOUT_S: float = 30.0
    _WAL_BACKUP_TIMEOUT_S: float = 10.0

    def __init__(self, ctx: "AgentContext") -> None:
        self._ctx = ctx

    def wal_checkpoint_sync(self) -> tuple[bool, list[tuple[str, str]]]:
        """Attempt a WAL checkpoint (PASSIVE, falling back to TRUNCATE with retries).

        Runs synchronously; intended to be invoked via `loop.run_in_executor(...)` since
        `time.sleep()` blocks. Returns `(True, [])` on PASSIVE/TRUNCATE success or when
        journal mode is not WAL; returns `(False, errors)` when TRUNCATE exhausts its
        retries.
        """
        errors: list[tuple[str, str]] = []
        with SQLiteHelper("session").open(write_mode=True) as db:
            wal_mode = db.execute("PRAGMA journal_mode").fetchone()[0]
            if wal_mode.lower() != "wal":
                logger.debug("WAL checkpoint skipped: journal mode is %r", wal_mode)
                return True, errors
            # Try PASSIVE checkpoint first (no exclusive lock required)
            _passive_start = time.monotonic()
            try:
                db.checkpoint("PASSIVE")
                elapsed = time.monotonic() - _passive_start
                if elapsed > 5:
                    logger.warning(
                        "WAL PASSIVE checkpoint took %s seconds, falling back to TRUNCATE",
                        round(elapsed, 2),
                    )
                else:
                    logger.info("WAL checkpoint completed (PASSIVE) on shutdown")
                    return True, errors
            except sqlite3.Error as passive_err:
                logger.warning(
                    "WAL PASSIVE checkpoint failed, falling back to TRUNCATE: %s",
                    passive_err,
                )
            # Retry TRUNCATE checkpoint with exponential backoff
            for attempt in range(3):
                try:
                    db.checkpoint("TRUNCATE")
                    logger.info(
                        "WAL checkpoint completed (TRUNCATE) on shutdown after %d retries",
                        attempt + 1,
                    )
                    return True, errors
                except sqlite3.Error as truncate_err:
                    if attempt < 2:
                        logger.warning(
                            "WAL TRUNCATE checkpoint attempt %d failed, retrying: %s",
                            attempt + 1,
                            truncate_err,
                        )
                        time.sleep(2**attempt)
                    else:
                        logger.error(
                            "WAL TRUNCATE checkpoint failed after 3 attempts: %s",
                            truncate_err,
                        )
                        errors.append(
                            (
                                "wal_checkpoint_truncate",
                                f"{type(truncate_err).__name__}: {truncate_err}",
                            )
                        )
            return False, errors

    def is_db_path_allowed(self, resolved_db_path: str) -> bool:
        """Return True when `resolved_db_path` is inside `cfg.approval.allowed_root`.

        Note: SQLite WAL files are always in the same directory as the DB file,
        so validating the DB path is equivalent to validating the WAL path.
        """
        allowed_root = self._ctx.cfg.approval.allowed_root
        if not allowed_root:
            return True
        resolved_root = os.path.realpath(allowed_root)
        return resolved_db_path == resolved_root or resolved_db_path.startswith(
            resolved_root + os.sep
        )

    def wal_backup_sync(self) -> tuple[str | None, list[tuple[str, str]]]:
        """Copy the WAL file to a backup location. Runs synchronously via an executor.

        Returns `(backup_path_or_None, errors)`.
        """
        errors: list[tuple[str, str]] = []
        wal_backup_path: str | None = None
        try:
            with SQLiteHelper("session").open(write_mode=True) as db:
                db_path = db.execute("PRAGMA database_list").fetchone()[2]
                if db_path:
                    resolved_db_path = os.path.realpath(db_path)
                    if not self.is_db_path_allowed(resolved_db_path):
                        logger.warning(
                            "WAL backup skipped: resolved db path %s is outside allowed_root %s",
                            resolved_db_path,
                            self._ctx.cfg.approval.allowed_root,
                        )
                        errors.append(
                            (
                                "wal_backup_path_rejected",
                                f"resolved db path {resolved_db_path} is outside allowed_root "
                                f"{self._ctx.cfg.approval.allowed_root!r}",
                            )
                        )
                        return wal_backup_path, errors
                    wal_file = f"{db_path}-wal"
                    backup_dir = os.path.dirname(db_path) or "/tmp"
                    if not os.path.isdir(backup_dir) or not os.access(
                        backup_dir, os.W_OK
                    ):
                        logger.warning(
                            "WAL backup skipped: backup directory %s is not writable",
                            backup_dir,
                        )
                        errors.append(
                            (
                                "wal_backup_dir_not_writable",
                                f"backup directory not writable: {backup_dir}",
                            )
                        )
                        return wal_backup_path, errors
                    session_id = self._ctx.session.session_id
                    session_tag = (
                        str(session_id)
                        if session_id is not None
                        else uuid.uuid4().hex[:8]
                    )
                    wal_backup_path = os.path.join(
                        backup_dir,
                        f"{os.path.basename(db_path)}-wal-backup-{session_tag}-{int(time.time())}",
                    )
                    shutil.copy2(wal_file, wal_backup_path)
                    logger.warning("WAL file backed up to %s", wal_backup_path)
        except Exception as backup_err:  # noqa: BLE001 — WAL backup is best-effort during shutdown; failure must be recorded, not raised
            logger.error("Failed to backup WAL file: %s", backup_err)
            errors.append(("wal_backup", f"{type(backup_err).__name__}: {backup_err}"))
        return wal_backup_path, errors
```

## Compatibility considerations

- REQ-003: WalCheckpointManager owns WAL database operations (`_wal_checkpoint_sync`, `_is_db_path_allowed`, `_wal_backup_sync`).
- REQ-008: All existing public method signatures and return types preserved.
- REQ-012: WAL checkpoint/backup behavior is identical (PASSIVE → TRUNCATE fallback, path validation).
- REQ-010: Existing import paths (`from agent.repl import AgentREPL`) continue to work.

## Security considerations

- REQ-012: WAL checkpoint/backup behavior identical (PASSIVE → TRUNCATE fallback, path validation) — WalCheckpointManager preserves exact fallback logic.
- Path validation (`_is_db_path_allowed`) ensures WAL backup only occurs within allowed_root boundaries.

## Rollback considerations

- If WalCheckpointManager introduces behavioral regression, revert repl.py to original version via `git checkout`.
- The new module can be removed independently without affecting the original repl.py.

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| scripts/agent/wal_checkpoint_manager.py | Unit: verify WAL checkpoint behavior identical | Custom unit test + existing WAL tests | Identical log output and error handling |
| scripts/agent/repl.py | Integration: verify run behavior unchanged | `uv run pytest tests/agent/test_repl.py tests/agent/test_repl_error_handling.py tests/agent/test_repl_health.py tests/agent/test_repl_health_malformed.py tests/agent/test_signal_handler_race.py` | All existing tests pass |
| scripts/agent/repl.py | Static analysis: no circular imports | `python -c "import agent.repl"` | No ImportError |
| scripts/agent/repl.py | Static analysis: backward compat import paths | `python -c "from agent.repl import AgentREPL"` | Import succeeds |
| All new/modified files | Lint: ruff passes | `ruff check scripts/agent/repl_input_loop.py scripts/agent/session_persister.py scripts/agent/wal_checkpoint_manager.py scripts/agent/resource_shutdown_coordinator.py scripts/agent/startup_banner.py scripts/agent/signal_handler.py scripts/agent/repl.py` | No lint errors |
| All new/modified files | Type check: mypy passes | `mypy scripts/agent/repl_input_loop.py scripts/agent/session_persister.py scripts/agent/wal_checkpoint_manager.py scripts/agent/resource_shutdown_coordinator.py scripts/agent/startup_banner.py scripts/agent/signal_handler.py scripts/agent/repl.py` | No type errors |

## Completion criteria

- WalCheckpointManager class has its own dedicated class with clear responsibility boundary.
- Each extracted concern has its own dedicated class.
- No circular imports between new modules.
- Existing import paths (`from agent.repl import AgentREPL`) continue to work.
- `ruff` lint passes on all modified/new files.
- `mypy` type check passes on all modified/new files.

## Out of scope

- Changing the `_GRACEFUL_TIMEOUT_S` value or making it configurable.
- Modifying StartupOrchestrator internals.
- Adding new diagnostic metrics or changing the session diagnostics schema.
- Changing the WAL checkpoint strategy (PASSIVE → TRUNCATE fallback).
- Adding new signal types beyond SIGTERM/SIGINT.
- Modifying CLIView or other display-layer components.
- Changing the command dispatch mechanism (CommandRegistry).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | |

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
- **Requirement ID**: REQ-003
- **Source issue**: issues/20260829-080924_refactor_002_repl_separation.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260829-180809_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260830-083027
- **Related target files**: scripts/agent/wal_checkpoint_manager.py
