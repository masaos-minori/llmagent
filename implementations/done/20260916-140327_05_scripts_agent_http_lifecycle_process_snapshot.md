## Goal

Rename `ProcessInfoSnapshot` to `RawProcessSnapshot` to resolve its name collision with `agent.services.models.ProcessInfoSnapshot`, and add an optional keyword-only `fields` parameter to `ProcessSnapshotProvider.from_proc_pid()` and `get_info()`.

## Scope

- Rename `http_lifecycle_process_snapshot.ProcessInfoSnapshot` to `RawProcessSnapshot` (all internal references updated).
- Add `fields: frozenset[str] | None = None` parameter to `ProcessSnapshotProvider.from_proc_pid()` and `get_info()`, defaulting to full-fetch behavior for backward compatibility.
- Do NOT change `_build_snapshot()` or route it through `ProcessSnapshotProvider.get_info()`.

## Assumptions

- `ProcessInfoSnapshot` (23 fields) and `agent.services.models.ProcessInfoSnapshot` (7 fields) are genuinely incompatible dataclasses — their shapes differ, so unification is not feasible.
- `ProcessSnapshotProvider`'s methods have zero external callers — confirmed by `rg` — but implementing REQ-008 for completeness/acceptance-criteria compliance.
- The `fields` parameter only optimizes a currently-uncalled code path — delivers no runtime value until UNK-02 is separately resolved.

## Design decisions

- Rename only the un-consumed dataclass — do not attempt to unify `_build_snapshot()` with `ProcessSnapshotProvider.get_info()` since their return types are genuinely incompatible.
- Use `frozenset[str] | None` for the `fields` parameter type — immutable set type for clarity that field selection is read-only.
- Default `None` means "fetch all fields" — backward compatible with current behavior.

## Alternatives considered

- Renaming `agent.services.models.ProcessInfoSnapshot` instead — rejected because it is actively used by `HttpServerLifecycleManager._build_snapshot()` and its callers (`get_process_info()`, `get_process_snapshot()`, `list_processes()`), while `http_lifecycle_process_snapshot.ProcessInfoSnapshot` has zero external callers.
- Using a list instead of frozenset for `fields` — rejected because frozenset conveys immutability intent.

## Implementation
### Target file

`scripts/agent/http_lifecycle_process_snapshot.py`

### Procedure

1. Rename `ProcessInfoSnapshot` class to `RawProcessSnapshot` throughout the file.
2. Update all references to `ProcessInfoSnapshot` within the file (including `from_proc_pid` return type annotation, `get_info`/`get_snapshot` return types, `list_processes` return type).
3. Add `fields: frozenset[str] | None = None` parameter to `from_proc_pid()` and `get_info()`.
4. When `fields` is provided, only fetch the specified fields from `/proc/[pid]` filesystem.

### Method

**Step 1: Rename the dataclass**

Replace all occurrences of `ProcessInfoSnapshot` with `RawProcessSnapshot`:
- Class definition: `@dataclass(frozen=True)\nclass RawProcessSnapshot:`
- `from_proc_pid` return type: `def from_proc_pid(cls, pid: int, *, fields: frozenset[str] | None = None) -> RawProcessSnapshot:`
- `cls(...)` call inside `from_proc_pid` — update field names accordingly
- `get_info` return type: `-> RawProcessSnapshot | None`
- `get_snapshot` return type: `-> dict | None` (unchanged — returns asdict result)
- `list_processes` return type: `-> list[RawProcessSnapshot]`

**Step 2: Implement `fields` parameter in `from_proc_pid()`**

Current `from_proc_pid()` reads all 23 fields unconditionally. With `fields` parameter:

```python
@classmethod
def from_proc_pid(cls, pid: int, *, fields: frozenset[str] | None = None) -> RawProcessSnapshot:
    """Create snapshot from /proc/[pid] filesystem.

    Args:
        pid: Process ID to inspect.
        fields: Optional frozenset of field names to fetch. If None, fetches all fields.

    Returns:
        RawProcessSnapshot instance.

    Raises:
        FileNotFoundError: If /proc/[pid] does not exist.
    """
    proc_dir = f"/proc/{pid}"

    if not os.path.exists(proc_dir):
        raise FileNotFoundError(f"/proc/{pid} does not exist")

    # Determine which fields to fetch
    if fields is None:
        fields = frozenset({
            "name", "cmdline", "cwd", "status", "open_files", "connections",
            "memory_info", "io_counters", "num_threads", "create_time",
            "cpu_times", "env_vars", "maps", "cgroups", "oom_score",
            "oom_score_adj", "sched_stat", "numa_maps", "syscall_info",
            "stack_trace", "limits", "fd_list",
        })
        include_pid = True
    else:
        include_pid = "pid" in fields

    # Build partial kwargs
    kwargs: dict[str, object] = {}
    if include_pid:
        kwargs["pid"] = pid

    # Fetch requested fields
    field_readers: dict[str, tuple[int, ...]] = {
        "name": (pid,),
        "cmdline": (pid,),
        "cwd": (pid,),
        "status": (pid,),
        "open_files": (pid,),
        "connections": (pid,),
        "memory_info": (pid,),
        "io_counters": (pid,),
        "num_threads": (pid,),
        "create_time": (pid,),
        "cpu_times": (pid,),
        "env_vars": (pid,),
        "maps": (pid,),
        "cgroups": (pid,),
        "oom_score": (pid,),
        "oom_score_adj": (pid,),
        "sched_stat": (pid,),
        "numa_maps": (pid,),
        "syscall_info": (pid,),
        "stack_trace": (pid,),
        "limits": (pid,),
        "fd_list": (pid,),
    }

    for field_name in fields:
        if field_name == "pid":
            continue  # already handled above
        reader = getattr(cls, f"_read_{field_name}", None)
        if reader is not None:
            try:
                kwargs[field_name] = reader(pid)
            except Exception:
                logger.debug("Failed to read %s for pid=%d", field_name, pid)
                kwargs[field_name] = None  # fallback for missing fields
        else:
            logger.warning("Unknown field: %s", field_name)

    return cls(**kwargs)
```

Note: This approach requires careful handling of each field's read method signature. A simpler alternative is to always read all fields but only populate the requested ones in the constructor:

```python
@classmethod
def from_proc_pid(cls, pid: int, *, fields: frozenset[str] | None = None) -> RawProcessSnapshot:
    """Create snapshot from /proc/[pid] filesystem.

    Args:
        pid: Process ID to inspect.
        fields: Optional frozenset of field names to fetch. If None, fetches all fields.

    Returns:
        RawProcessSnapshot instance.

    Raises:
        FileNotFoundError: If /proc/[pid] does not exist.
    """
    proc_dir = f"/proc/{pid}"

    if not os.path.exists(proc_dir):
        raise FileNotFoundError(f"/proc/{pid} does not exist")

    # Always read all fields (for simplicity; optimization can be added later)
    name = cls._read_name(pid)
    cmdline = cls._read_cmdline(pid)
    cwd = cls._read_cwd(pid)
    status = cls._read_status(pid)
    open_files = cls._read_open_files(pid)
    connections = cls._read_connections(pid)
    memory_info = cls._read_memory_info(pid)
    io_counters = cls._read_io_counters(pid)
    num_threads = cls._read_num_threads(pid, status)
    create_time = cls._read_create_time(pid, status)
    cpu_times = cls._read_cpu_times(pid, status)
    env_vars = cls._read_env_vars(pid)
    maps = cls._read_maps(pid)
    cgroups = cls._read_cgroups(pid)
    oom_score = cls._read_oom_score(pid)
    oom_score_adj = cls._read_oom_score_adj(pid)
    sched_stat = cls._read_sched_stat(pid)
    numa_maps = cls._read_numa_maps(pid)
    syscall_info = cls._read_syscall_info(pid)
    stack_trace = cls._read_stack_trace(pid)
    limits = cls._read_limits(pid)
    fd_list = cls._read_fd_list(pid)

    # Filter to requested fields if specified
    if fields is not None:
        filtered_kwargs = {"pid": pid}
        field_map = {
            "name": name, "cmdline": cmdline, "cwd": cwd, "status": status,
            "open_files": open_files, "connections": connections,
            "memory_info": memory_info, "io_counters": io_counters,
            "num_threads": num_threads, "create_time": create_time,
            "cpu_times": cpu_times, "env_vars": env_vars, "maps": maps,
            "cgroups": cgroups, "oom_score": oom_score, "oom_score_adj": oom_score_adj,
            "sched_stat": sched_stat, "numa_maps": numa_maps,
            "syscall_info": syscall_info, "stack_trace": stack_trace,
            "limits": limits, "fd_list": fd_list,
        }
        for field_name in fields:
            if field_name != "pid":
                filtered_kwargs[field_name] = field_map.get(field_name)
        return cls(**filtered_kwargs)

    return cls(
        pid=pid, name=name, cmdline=cmdline, cwd=cwd, status=status,
        open_files=open_files, connections=connections, memory_info=memory_info,
        io_counters=io_counters, num_threads=num_threads, create_time=create_time,
        cpu_times=cpu_times, env_vars=env_vars, maps=maps, cgroups=cgroups,
        oom_score=oom_score, oom_score_adj=oom_score_adj, sched_stat=sched_stat,
        numa_maps=numa_maps, syscall_info=syscall_info, stack_trace=stack_trace,
        limits=limits, fd_list=fd_list,
    )
```

**Step 3: Update `get_info()` signature**

```python
@staticmethod
def get_info(
    server_key: str,
    proc: subprocess.Popen[bytes],
    pgid: int | None,
    *,
    fields: frozenset[str] | None = None,
) -> RawProcessSnapshot | None:
    """Return a ``RawProcessSnapshot`` for *server_key* or ``None``.

    Falls back to the parent PID when the child has already exited.
    """
    pid = getattr(proc, "pid", None)
    if pid is None:
        logger.debug("%s: no PID available on proc object", server_key)
        return None
    try:
        return RawProcessSnapshot.from_proc_pid(pid, fields=fields)
    except FileNotFoundError:
        if pgid is not None:
            try:
                return RawProcessSnapshot.from_proc_pid(pgid, fields=fields)
            except FileNotFoundError:
                pass
        logger.debug("%s: /proc/%d does not exist", server_key, pid)
        return None
```

**Step 4: Update `list_processes()` return type**

```python
@staticmethod
def list_processes(
    manager: HttpServerLifecycleManager,
) -> list[RawProcessSnapshot]:
    """Return snapshots for every managed server whose process is alive."""
    results: list[RawProcessSnapshot] = []
    for server_key, proc in manager._http_procs.items():
        if proc is None:
            continue
        pgid = manager._http_pgids.get(server_key)
        if pgid is None:
            try:
                pgid = os.getpgid(proc.pid)
            except OSError:
                pass
        snapshot = ProcessSnapshotProvider.get_info(server_key, proc, pgid)
        if snapshot is not None:
            results.append(snapshot)
    return results
```

### Details

After renaming, the dataclass will be:
```python
@dataclass(frozen=True)
class RawProcessSnapshot:
    """Immutable snapshot of process information."""
    pid: int
    name: str
    cmdline: list[str]
    cwd: str | None
    status: dict[str, str]
    open_files: list[str]
    connections: list[tuple[str, str, str]]
    memory_info: dict[str, int]
    io_counters: dict[str, int]
    num_threads: int
    create_time: float | None
    cpu_times: dict[str, float]
    env_vars: dict[str, str]
    maps: list[tuple[str, str, str, str, str]]
    cgroups: list[tuple[int, str, str]]
    oom_score: int
    oom_score_adj: int
    sched_stat: tuple[int, int, int]
    numa_maps: dict[str, dict[str, int]]
    syscall_info: dict[str, int]
    stack_trace: list[tuple[str, str]]
    limits: list[tuple[str, str, str, str]]
    fd_list: list[tuple[int, str]]
```

## Compatibility considerations

- The rename resolves the name collision with `agent.services.models.ProcessInfoSnapshot` — this was a real risk for any future import combining both.
- `_build_snapshot()` in `http_lifecycle.py` continues to use `agent.services.models.ProcessInfoSnapshot` — unchanged.
- The `fields` parameter is additive and backward-compatible — existing callers without the parameter get full-fetch behavior.
- `ProcessSnapshotProvider.list_processes()` still returns `list[ProcessInfoSnapshot]` type annotation — update to `list[RawProcessSnapshot]`.

## Security considerations

- No security impact — renaming a class and adding an optional parameter do not introduce vulnerabilities.
- The `/proc` filesystem access patterns remain unchanged.

## Rollback considerations

- If the rename causes issues, revert the class name back to `ProcessInfoSnapshot` and restore all references.
- The `fields` parameter can be safely removed by dropping the parameter and its conditional logic.

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `http_lifecycle_process_snapshot.py` | Static analysis | `uv run ruff check scripts/agent/http_lifecycle_process_snapshot.py` | Clean |
| `http_lifecycle_process_snapshot.py` | Type check | `uv run mypy scripts/agent/http_lifecycle_process_snapshot.py` | Pass (no new regressions) |
| `test_http_lifecycle_process_snapshot.py` | Unit (new test file) | `uv run pytest tests/agent/test_http_lifecycle_process_snapshot.py -q` | Rename complete; `fields` parameter narrows fetched fields |

## Completion criteria

- `http_lifecycle_process_snapshot.RawProcessSnapshot` no longer shares a name with `agent.services.models.ProcessInfoSnapshot`; `_build_snapshot()` is unchanged.
- `from_proc_pid()` and `get_info()` accept optional keyword-only `fields` parameter.
- `uv run ruff check scripts/agent/http_lifecycle_process_snapshot.py` passes clean.
- `uv run mypy scripts/agent/http_lifecycle_process_snapshot.py` passes (no new regressions vs pre-existing errors).

## Out of scope

- Unifying `_build_snapshot()` with `ProcessSnapshotProvider.get_info()` — their return types are genuinely incompatible (7-field vs 23-field shapes).
- Deciding whether `ProcessSnapshotProvider` should gain a real caller or be deleted as dead code — tracked as UNK-02, out of scope.
- Adding unit tests for this file — handled in the next procedure document.

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
- **Requirement ID**: REQ-004, REQ-008
- **Source issue**: issues/20260915-102515_refactor_http_lifecycle_module_split.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260916-140327_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260916-140327
- **Related target files**: scripts/agent/http_lifecycle_process_snapshot.py
