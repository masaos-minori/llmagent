## Goal

Remove the dead `self._spawned_subprocesses` attribute from `StartupOrchestrator`
(declared in `__init__`, assigned in `run()`) so it no longer appears anywhere in the
codebase, while keeping the `_start_servers()` call whose side effect `run()` still
needs (REQ-001).

## Scope

Modify only `scripts/agent/startup.py`: delete the field declaration in
`StartupOrchestrator.__init__` and drop the `self._spawned_subprocesses =` assignment
prefix in `run()`, keeping the `await self._start_servers()` call. No other file.

## Assumptions

- The field is dead in production: declared and assigned only in `startup.py`, never
  read by `run()`, `_rollback_servers()`, or any caller; rollback is owned by
  `lifecycle.shutdown_all()` (verified in Step 3a).
- Removing the field changes no production behavior and no return contract: `run()`
  already returns `(cmds, orchestrator)`, not the tracked list.
- `import subprocess` stays valid: after the edit it is still referenced by
  `_start_servers()`'s return annotation `list[subprocess.Popen]` (startup.py:114).

## Design decisions

- Drop only the `self._spawned_subprocesses =` prefix in `run()`, not the whole line:
  the `await self._start_servers()` call is the live side effect; deleting the entire
  line would also delete the required spawn call.
- Delete the `__init__` declaration wholesale (it is a standalone one-line
  initialization with no companion logic).

## Alternatives considered

N/A: single-attribute removal on a Path A change; keeping a replacement record would
reintroduce the misleading ownership contract this change removes.

## Implementation
### Target file

`scripts/agent/startup.py`

### Procedure

1. In `StartupOrchestrator.__init__`, delete the field declaration line.
2. In `run()`, change the assignment to a bare `await self._start_servers()`, keeping
   the call and dropping only the `self._spawned_subprocesses =` prefix.

### Method

In `__init__` (around line 60), remove the standalone assignment between
`self._orchestrator` and `self._shutdown_event`. In `run()` (around line 73), within
the `try` block, edit the RHS-bearing line in place, leaving the `await` expression
intact.

### Details

Delete this line from `__init__` (current line 60, 8-space indent):

```python
        self._spawned_subprocesses: list[subprocess.Popen] = []
```

Change this line in `run()` (current line 73, 12-space indent, inside the `try`):

```python
            self._spawned_subprocesses = await self._start_servers()
```

to:

```python
            await self._start_servers()
```

`import subprocess` is retained: `_start_servers()` still annotates its return type as
`list[subprocess.Popen]`, so the import is not left unused.

## Compatibility considerations

`test_run_returns_cmds_and_orchestrator_on_success` asserts `run()` returns exactly
`(cmds, orchestrator)`; removing the tracked list does not change that return tuple.

## Security considerations

N/A: no auth, secret, or credential-handling change.

## Rollback considerations

N/A: revert the commit.

## Validation plan

| Target File/Module | Testing Strategy (Unit) | Tool / Command | Expected Outcome |
|---|---|---|---|
| `scripts/agent/startup.py::StartupOrchestrator` | Static: field no longer declared/assigned; `run()` still calls `_start_servers()` | `rg -n "_spawned_subprocesses" scripts/agent/startup.py` (expect zero matches) | No reference to the field in `startup.py`; `run()` unchanged except the dropped assignment |

## Completion criteria

- `StartupOrchestrator.__init__` no longer declares `self._spawned_subprocesses`.
- `run()` no longer assigns `self._spawned_subprocesses`; it still calls
  `_start_servers()` and returns exactly `(cmds, orchestrator)`.
- `subprocess` remains imported and used (by `_start_servers()`'s return annotation).
- `rg -n "_spawned_subprocesses" scripts/agent/startup.py` returns no matches.

## Out of Scope

The two tests in `tests/agent/test_startup_rollback.py` that assert on the field
(Row 2); `McpServerStarter._spawned_subprocesses` (a live field on a different class);
any rollback / `lifecycle.shutdown_all()` behavior.

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
- **Requirement ID**: `REQ-001` (remove the dead `self._spawned_subprocesses` from `StartupOrchestrator` while keeping the `_start_servers()` call)
- **Source issue**: issues/20261029-220719_startorch001_dead-spawned-subprocesses.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261030-065511_startorch001_dead-spawned-subprocesses.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261030-073124
- **Related target files**: scripts/agent/startup.py
