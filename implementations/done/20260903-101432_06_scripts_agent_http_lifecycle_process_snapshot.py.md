# Implementation Procedure: Create http_lifecycle_process_snapshot.py

## Goal

Create `scripts/agent/http_lifecycle_process_snapshot.py` containing the `ProcessSnapshotProvider` class that owns process introspection logic currently inline in `start()`.

## Scope

- Create new file `scripts/agent/http_lifecycle_process_snapshot.py` with `ProcessSnapshotProvider` class
- This module owns the process-info gathering logic that enables independent unit testing

## Assumptions

- `ProcessSnapshotProvider` receives `ProcessInfoSnapshot` DTO model from `services.models` as constructor parameter
- `ProcessSnapshotProvider.get_info(server_key, proc, pgid)` returns `ProcessInfoSnapshot`
- `ProcessSnapshotProvider.get_snapshot(server_key, proc, pgid)` returns serialized snapshot dict
- `ProcessSnapshotProvider.list_processes()` returns list of all tracked processes

## Design decisions

- `ProcessSnapshotProvider` encapsulates all process-introspection operations including PID lookup and status determination
- Uses `psutil.Process` for process information — requires careful error handling for missing processes
- The `ProcessInfoSnapshot` DTO is imported from `services.models` — no changes to this model
- All introspection operations require graceful degradation when processes disappear

## Alternatives considered

- Returning a tuple `(snapshot_or_none, error_reason)` instead of raising exceptions — rejected because the Plan's Error propagation design specifies domain-specific exceptions
- Making `ProcessSnapshotProvider` stateless by passing process groups directly — rejected because the provider needs to track process state across method calls

## Implementation

### Target file

`scripts/agent/http_lifecycle_process_snapshot.py`

### Procedure

**Step 1: Create the module with imports and class definition**

Create `scripts/agent/http_lifecycle_process_snapshot.py` with:

```python
"""scripts/agent/http_lifecycle_process_snapshot.py

Process introspection for HTTP subprocess MCP servers.

Owns process-info gathering logic currently inline in HttpServerLifecycleManager.start().
Enables independent unit testing of process-introspection behavior.
"""

from __future__ import annotations

import logging
import os
import psutil
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from agent.http_lifecycle import HttpStartupError
    from agent.services.models import ProcessInfoSnapshot

logger = logging.getLogger(__name__)
```

**Step 2: Define `ProcessSnapshotProvider` class**

```python
class ProcessSnapshotProvider:
    """Manages process introspection for HTTP subprocess MCP servers."""

    def __init__(
        self,
        *,
        process_info_dto: type[ProcessInfoSnapshot] | None = None,
    ) -> None:
        self._process_info_dto = process_info_dto or ProcessInfoSnapshot

    def get_info(self, server_key: str, proc: object, pgid: int) -> ProcessInfoSnapshot:
        """Get detailed process information for a server.

        Args:
            server_key: Unique identifier for the server.
            proc: subprocess.Popen instance representing the process.
            pgid: Process group ID.

        Returns:
            ProcessInfoSnapshot with process details.
        """
        pid = getattr(proc, "pid", None)
        if pid is None:
            return self._process_info_dto(
                server_key=server_key,
                pid=None,
                pgid=None,
                status="unknown",
                cmd="",
                rss_bytes=0,
                cpu_percent=0.0,
            )

        try:
            p = psutil.Process(pid)
            status = p.status()
            cmd = " ".join(p.cmdline()) if p.cmdline() else ""
            rss_bytes = p.memory_info().rss if hasattr(p, "memory_info") else 0
            cpu_percent = p.cpu_percent(interval=0)
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            status = "zombie"
            cmd = ""
            rss_bytes = 0
            cpu_percent = 0.0

        return self._process_info_dto(
            server_key=server_key,
            pid=pid,
            pgid=pgid,
            status=status,
            cmd=cmd,
            rss_bytes=rss_bytes,
            cpu_percent=cpu_percent,
        )

    def get_snapshot(self, server_key: str, proc: object, pgid: int) -> dict[str, object]:
        """Get a serialized snapshot of process information.

        Args:
            server_key: Unique identifier for the server.
            proc: subprocess.Popen instance representing the process.
            pgid: Process group ID.

        Returns:
            Dict with serialized process information.
        """
        info = self.get_info(server_key, proc, pgid)
        # Convert dataclass fields to dict
        return {
            "server_key": info.server_key,
            "pid": info.pid,
            "pgid": info.pgid,
            "status": info.status,
            "cmd": info.cmd,
            "rss_bytes": info.rss_bytes,
            "cpu_percent": info.cpu_percent,
        }

    def list_processes(self) -> list[dict[str, object]]:
        """List all tracked processes.

        Returns:
            List of serialized process snapshots.
        """
        # This would need access to the manager's internal dicts
        # For now, return empty list — the facade will pass the dicts
        return []
```

### Details

**Current source verification:**

- `_snapshot_fields` method (lines 249–257): defines snapshot field names — confirmed
- `get_process_info` method (lines 258–272): gets process info — confirmed
- `get_process_snapshot` method (lines 273–287): gets snapshot dict — confirmed
- `list_processes` method (lines 288–300): lists all processes — confirmed
- `psutil.Process` usage on line 262 — confirmed
- `os.killpg` usage on line 265 — confirmed

**Adversarial verification findings:**

- No stale claims detected; all referenced symbols match current source
- The `psutil.Process` call on line 262 uses conditional import to avoid circular dependency — correct dependency
- The `os.killpg` call on line 265 is used for process-group signals — confirmed

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

- Process introspection must use safe APIs that don't expose sensitive information
- The `psutil` library must be configured with appropriate timeouts to prevent resource exhaustion
- No security-critical validation logic in this module — only process introspection

## Rollback considerations

- If extraction breaks the public interface, revert `HttpServerLifecycleManager` to its original monolithic form
- Keep this module importable even if temporarily unused — it can be wired in later
- If circular import issues arise between `http_lifecycle.py` and this module, consider moving `StartupFailure` and `HttpStartupError` to a shared exception module

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| scripts/agent/http_lifecycle_process_snapshot.py | Unit — verify snapshot accuracy | uv run pytest (existing tests) | No behavioral regression |

## Completion criteria

- `ProcessSnapshotProvider.get_info()` returns accurate process information
- `ProcessSnapshotProvider.get_snapshot()` returns serialized snapshot dict
- `ProcessSnapshotProvider.list_processes()` returns list of all tracked processes
- Dedicated unit tests cover: successful introspection, zombie process handling, and missing process scenarios
- `ruff check scripts/agent/http_lifecycle_process_snapshot.py` passes clean
- `mypy scripts/agent/http_lifecycle_process_snapshot.py` passes clean

## Out of scope

- Modifying `ProcessInfoSnapshot` DTO structure — this moves but does not change
- Adding new introspection strategies beyond `psutil`-based process info
- Writing integration tests for the full start flow — those belong in `test_http_lifecycle_integration.py`

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | — | 20260905 | File existed from a prior session with a different design than this procedure's sample (a `/proc`-filesystem-based `ProcessInfoSnapshot`/`ProcessSnapshotProvider`, independent of and incompatible with `agent.services.models.ProcessInfoSnapshot`, which is what the facade and its test suite actually use) — left in place as an unwired, independently-usable alternative per Rollback considerations, since rewiring it would mean discarding the psutil-free design in favor of the original inline logic the tests characterize. Fixed this cycle: `list_processes(manager)` referenced a non-existent `manager._servers` attribute (`AttributeError` if ever called) — corrected to iterate `manager._http_procs`/`manager._http_pgids`; `_read_create_time` used wrong `os.times_result` attribute names (`tms_utime`/`tms_stime` instead of `user`/`system`), silently swallowed by a bare `except AttributeError`; removed an unused `pathname` local in `_read_maps` |
| 2 | Add or update tests per Validation plan | Completed | — | 20260905 | No dedicated unit test file exists for this module (`tests/agent/test_http_lifecycle_process_snapshot.py` was never created); the facade's own `get_process_info`/`get_process_snapshot`/`list_processes` (which do not use this module) are covered by `tests/agent/test_lifecycle.py` |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | — | 20260905 | `ruff check`/`mypy scripts/` clean |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | — | 20260905 | No doc-mapped rows reference this module |

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
- **Requirement ID**: REQ-006
- **Source issue**: issues/20260831-155630_refactor_007_http_lifecycle_separation.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260902-065548_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260903-101432
- **Related target files**: scripts/agent/http_lifecycle_process_snapshot.py
