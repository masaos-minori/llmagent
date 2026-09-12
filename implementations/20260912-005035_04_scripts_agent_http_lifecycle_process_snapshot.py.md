# Implementation: scripts/agent/http_lifecycle_process_snapshot.py

## Goal

Ensure full coverage of snapshot logic — verify that `ProcessSnapshotProvider.get_snapshot()` covers all behaviors previously handled by `_build_snapshot_dict()` in `HttpServerLifecycleManager`. Add any missing fields (process status, exit code, runtime duration).

## Scope

- Modify `scripts/agent/http_lifecycle_process_snapshot.py` only.
- Add missing behavioral differences from `_build_snapshot_dict()` to `ProcessSnapshotProvider.get_snapshot()`:
  1. Process status field (`running`, `exited`).
  2. Exit code field (`last_exit_code`) when process has exited.
  3. Runtime duration field (`runtime_seconds`) based on start time.

## Assumptions

- The `get_snapshot()` method already handles the core fields (pid, pgid, running).
- The missing fields can be computed using standard Python APIs (os.waitpid(), datetime.timedelta).
- The `ProcessInfoSnapshot` model should include the additional fields.

## Design decisions

- Add the missing fields to `ProcessInfoSnapshot` dataclass.
- Compute `last_exit_code` using `os.waitpid()` when available.
- Compute `runtime_seconds` using `datetime.datetime.now() - start_time`.

## Alternatives considered

- **Create a wrapper method**: Would keep `get_snapshot()` unchanged but adds indirection. Not needed since we can fix the root cause directly.
- **Add parameters to control behavior**: Would make the API more complex. Simpler to just add the missing behaviors unconditionally.

## Implementation

### Target file

`scripts/agent/http_lifecycle_process_snapshot.py`

### Procedure

1. Read `_build_snapshot_dict()` in `http_lifecycle.py` to confirm the exact behavioral differences.
2. Add missing fields to `ProcessInfoSnapshot` dataclass.
3. Update `get_snapshot()` to compute and populate the missing fields.

### Method

```python
# Step 2: Add missing fields to ProcessInfoSnapshot
# Before:
@dataclass(frozen=True)
class ProcessInfoSnapshot:
    pid: int | None
    pgid: int | None
    running: bool
    last_exit_code: int | None = None

# After:
@dataclass(frozen=True)
class ProcessInfoSnapshot:
    pid: int | None
    pgid: int | None
    running: bool
    last_exit_code: int | None = None
    runtime_seconds: float | None = None

# Step 3: Update get_snapshot() to compute missing fields
# Before (around line 100):
#     def get_snapshot(self, server_key: str, proc: subprocess.Popen[bytes] | None, pgid: int | None) -> dict | None:
#         ...
#         return {
#             "pid": proc.pid if proc else None,
#             "pgid": pgid,
#             "running": proc is not None and proc.poll() is None,
#         }

# After:
#     def get_snapshot(self, server_key: str, proc: subprocess.Popen[bytes] | None, pgid: int | None) -> dict | None:
#         ...
#         # Compute runtime_seconds
#         runtime_seconds = None
#         if proc is not None and proc.start_time is not None:
#             try:
#                 runtime_seconds = (datetime.datetime.now() - proc.start_time).total_seconds()
#             except Exception:
#                 pass
#
#         # Compute last_exit_code
#         last_exit_code = None
#         if proc is not None and proc.poll() is not None:
#             last_exit_code = proc.returncode
#
#         return {
#             "pid": proc.pid if proc else None,
#             "pgid": pgid,
#             "running": proc is not None and proc.poll() is None,
#             "last_exit_code": last_exit_code,
#             "runtime_seconds": runtime_seconds,
#         }
```

### Details

- Line numbers are approximate — verify against current source before applying changes.
- Need to carefully reconcile the behavioral differences between `_build_snapshot_dict()` and `get_snapshot()` — the plan explicitly notes these differences must be reconciled during migration.
- The `proc.start_time` attribute may not be available on all platforms; need to handle this gracefully.

## Compatibility considerations

- **Breaking change** for consumers of `get_snapshot()` that expect only `pid`, `pgid`, and `running` fields. New fields (`last_exit_code`, `runtime_seconds`) will be present in the output.
- **No breaking change** for existing callers of `get_info()` — it returns the same types (`ProcessInfoSnapshot`).

## Security considerations

- No new security surface introduced. Adding snapshot fields does not introduce new attack vectors.

## Rollback considerations

- Revert the behavioral additions to `get_snapshot()`.
- If the new fields cause unexpected behavior, remove them and investigate further.

## Validation plan

| Target | Strategy | Tool / Command | Expected Outcome |
|--------|----------|----------------|------------------|
| Snapshot output | Unit test | `uv run pytest tests/agent/test_http_lifecycle_process_snapshot.py -v` | All existing tests pass without modification |
| Behavioral equivalence | Manual verification | Compare `_build_snapshot_dict()` output with `get_snapshot()` output | Identical behavior for all edge cases |
| Type checking | Static | Type checker against modified file | No type errors |
| Lint checking | Static | Lint tool against modified file | No lint errors |

## Completion criteria

- [ ] Missing fields added to `ProcessInfoSnapshot` dataclass.
- [ ] `get_snapshot()` computes and populates missing fields.
- [ ] Existing tests pass without modification.
- [ ] No type/lint regressions.

## Out of scope

- Modifying `scripts/agent/http_lifecycle.py` — handled by a separate implementation procedure document.
- Modifying `scripts/agent/http_lifecycle_process_terminator.py` — handled by a separate implementation procedure document.
- Modifying `scripts/agent/http_lifecycle_shutdown_coordinator.py` — handled by a separate implementation procedure document.
- Modifying `scripts/agent/http_lifecycle_health_checker.py` — handled by a separate implementation procedure document.
- Modifying `scripts/agent/factory.py` — handled by a separate implementation procedure document.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Verify behavioral differences with _build_snapshot_dict() | Pending | — | — | |
| 2 | Add missing fields to ProcessInfoSnapshot | Pending | — | — | |
| 3 | Update get_snapshot() to compute missing fields | Pending | — | — | |
| 4 | Run validation sequence (rules/toolchain.md) | Pending | — | — | |

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
- **Source issue**: issues/20260911-214848_refactor_http_lifecycle_eliminate_cross_module_duplication.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260911-235117_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260912-005035
- **Related target files**: scripts/agent/http_lifecycle_process_snapshot.py
