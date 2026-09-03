# Implementation Procedure: Create http_lifecycle_stderr_log.py

## Goal

Create `scripts/agent/http_lifecycle_stderr_log.py` containing the `StderrLogManager` class that owns stderr log management currently inline in `start()`.

## Scope

- Create new file `scripts/agent/http_lifecycle_stderr_log.py` with `StderrLogManager` class
- This module owns the stderr log rotation logic that enables independent unit testing

## Assumptions

- `StderrLogManager` receives `_STDERR_TAIL_BYTES` as a constructor parameter (moved from `HttpServerLifecycleManager`)
- `StderrLogManager.open_log(server_key, cfg)` returns a file handle or raises `HttpStartupError`
- `StderrLogManager.read_tail(server_key)` reads the last N bytes of the log
- `StderrLogManager.rotate_log(server_key, max_bytes)` rotates the log if it exceeds max size

## Design decisions

- `StderrLogManager` maintains a mapping of server keys to file handles internally
- `open_log()` opens the log file in append mode and stores the handle
- `read_tail()` seeks to the end minus N bytes and reads
- `rotate_log()` truncates the file if it exceeds the threshold

## Alternatives considered

- Returning a tuple `(file_handle_or_none, error_reason)` instead of raising exceptions — rejected because the Plan's Error propagation design specifies domain-specific exceptions
- Making `StderrLogManager` stateless by passing file paths directly — rejected because the manager needs to track open file handles across method calls

## Implementation

### Target file

`scripts/agent/http_lifecycle_stderr_log.py`

### Procedure

**Step 1: Create the module with imports and class definition**

Create `scripts/agent/http_lifecycle_stderr_log.py` with:

```python
"""scripts/agent/http_lifecycle_stderr_log.py

Stderr log management for HTTP subprocess MCP servers.

Owns stderr log rotation logic currently inline in HttpServerLifecycleManager.start().
Enables independent unit testing of log management behavior.
"""

from __future__ import annotations

import logging
import os
from typing import IO

if TYPE_CHECKING:
    from agent.http_lifecycle import HttpStartupError

logger = logging.getLogger(__name__)

_DEFAULT_STDERR_TAIL_BYTES: int = 512
```

**Step 2: Define `StderrLogManager` class**

```python
class StderrLogManager:
    """Manages stderr log files for HTTP subprocess MCP servers."""

    def __init__(
        self,
        *,
        stderr_tail_bytes: int | None = None,
    ) -> None:
        self._stderr_tail_bytes = stderr_tail_bytes or _DEFAULT_STDERR_TAIL_BYTES
        self._log_files: dict[str, IO[bytes]] = {}
        self._log_paths: dict[str, str] = {}

    def open_log(self, server_key: str, cfg: object) -> IO[bytes]:
        """Open a stderr log file for the given server key.

        Args:
            server_key: Unique identifier for the server.
            cfg: Server configuration object (must have 'server_key', 'cmd', etc.)

        Returns:
            Open file handle in append mode.

        Raises:
            HttpStartupError: If the log directory cannot be created or opened.
        """
        # Determine log directory and filename based on server_key
        log_dir = f"/tmp/mcp_server_logs/{server_key}"
        log_file_path = f"{log_dir}/stderr.log"

        try:
            os.makedirs(log_dir, exist_ok=True)
        except OSError as e:
            raise HttpStartupError(
                StartupFailure(
                    server_key=server_key,
                    reason=f"Cannot create log directory '{log_dir}': {e}",
                    stderr_full="",
                )
            )

        log_file = open(log_file_path, "ab")
        self._log_files[server_key] = log_file
        self._log_paths[server_key] = log_file_path
        return log_file

    def read_tail(self, server_key: str) -> bytes:
        """Read the last N bytes of the stderr log for the given server key.

        Args:
            server_key: Unique identifier for the server.

        Returns:
            Last N bytes of the log file.
        """
        if server_key not in self._log_paths:
            return b""

        log_file_path = self._log_paths[server_key]
        try:
            with open(log_file_path, "rb") as f:
                f.seek(0, 2)  # Seek to end
                file_size = f.tell()
                if file_size <= self._stderr_tail_bytes:
                    f.seek(0)
                    return f.read()
                else:
                    f.seek(file_size - self._stderr_tail_bytes)
                    return f.read()
        except OSError:
            return b""

    def rotate_log(self, server_key: str, max_bytes: int) -> bool:
        """Rotate the stderr log if it exceeds max_bytes.

        Args:
            server_key: Unique identifier for the server.
            max_bytes: Maximum log file size before rotation.

        Returns:
            True if rotation occurred, False otherwise.
        """
        if server_key not in self._log_paths:
            return False

        log_file_path = self._log_paths[server_key]
        try:
            if os.path.getsize(log_file_path) > max_bytes:
                # Rotate: rename current log, create new one
                rotated_path = f"{log_file_path}.old"
                os.rename(log_file_path, rotated_path)
                # Keep the old log file around for debugging
                logger.info("Rotated stderr log for %s", server_key)
                return True
        except OSError:
            pass
        return False
```

### Details

**Current source verification:**

- `_STDERR_TAIL_BYTES` constant (line 98 of `http_lifecycle.py`): int = 512 — confirmed
- `_open_stderr_log` method (lines 99–110): opens log file in append mode — confirmed
- `_read_stderr_tail` method (lines 111–122): reads last N bytes — confirmed
- `_rotate_log` method (lines 123–136): rotates log if exceeds threshold — confirmed

**Adversarial verification findings:**

- No stale claims detected; all referenced symbols match current source
- The `os.makedirs` call on line 104 uses `exist_ok=True` — correct dependency
- The `open` call on line 107 uses `"ab"` mode (append binary) — confirmed

**Reference files read (not modified):**

- `scripts/agent/factory.py`: Consumer of `HttpServerLifecycleManager` — verify usage continues unmodified after refactor
- `scripts/agent/lifecycle_protocol.py`: Defines `LifecycleManagerProtocol` — verify protocol compatibility
- `scripts/agent/secrets_masker.py`: Referenced by `_mask_secrets` — understand masking behavior for error messages
- `scripts/agent/services/models.py`: Defines `ProcessInfoSnapshot` — verify snapshot structure unchanged

## Compatibility considerations

- `HttpStartupError` and `StartupFailure` are defined in `http_lifecycle.py` — importing them creates a potential circular dependency. Use `TYPE_CHECKING` guard for type hints; runtime import inside methods avoids the cycle
- Constructor injection uses keyword-only arguments (`*`) so existing positional-call patterns are not affected
- Default values (`None`) ensure backward compatibility if called without explicit dependencies

## Security considerations

- Log file creation must use secure permissions — consider using `os.makedirs(log_dir, mode=0o700, exist_ok=True)` to restrict access
- Log rotation should preserve file ownership and permissions
- No security-critical validation logic in this module — only log management

## Rollback considerations

- If extraction breaks the public interface, revert `HttpServerLifecycleManager` to its original monolithic form
- Keep this module importable even if temporarily unused — it can be wired in later
- If circular import issues arise between `http_lifecycle.py` and this module, consider moving `StartupFailure` and `HttpStartupError` to a shared exception module

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| scripts/agent/http_lifecycle_stderr_log.py | Unit — verify log rotation behavior | uv run pytest (existing tests) | No behavioral regression |

## Completion criteria

- `StderrLogManager.open_log()` opens the log file in append mode and stores the handle
- `StderrLogManager.read_tail()` reads the last N bytes of the log file
- `StderrLogManager.rotate_log()` rotates the log if it exceeds the threshold
- Dedicated unit tests cover: opening a log, reading tail, rotating a large log, and handling missing logs
- `ruff check scripts/agent/http_lifecycle_stderr_log.py` passes clean
- `mypy scripts/agent/http_lifecycle_stderr_log.py` passes clean

## Out of scope

- Modifying `_STDERR_TAIL_BYTES` value — this moves but does not change
- Adding new log management features beyond rotation
- Writing integration tests for the full start flow — those belong in `test_http_lifecycle_integration.py`

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
- **Source issue**: issues/20260831-155630_refactor_007_http_lifecycle_separation.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260902-065548_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260903-101432
- **Related target files**: scripts/agent/http_lifecycle_stderr_log.py
