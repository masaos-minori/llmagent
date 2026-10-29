## Goal

Release the inherited stderr handle and drop its tracking entry on the empty-command
failure path in `create_and_validate_proc` (`scripts/agent/http_lifecycle_subprocess_launcher.py`),
so it matches every other failure branch and stops leaking the handle and a dangling
registry entry (REQ-001).

## Scope

Modify only `create_and_validate_proc` in `scripts/agent/http_lifecycle_subprocess_launcher.py`.
No other file.

## Assumptions

- `close_stderr_log(server_key, stderr_fh)` closes the handle, pops
  `self._stderr_files[server_key]`, and calls `forget(server_key)`.
- Calling `forget` on the empty-command path is safe: it performs
  `self._log_paths.pop(server_key, None)`, a no-op when the key was never registered.
- `self._stderr_files` is a shared per-server tracking dict; only this server's key
  must be dropped, not the whole dict.

## Design decisions

- Call the existing `self.close_stderr_log(server_key, stderr_fh)` helper immediately
  before the empty-command `raise HttpStartupError(...)`, mirroring the value-error
  and `Popen`-exception branches exactly.
- Use `close_stderr_log` rather than `stderr_fh.close()` plus a registry mutation: it
  also calls `forget` (keeps the log-path registry consistent) and pops only this
  server's key (`.clear()` would wipe every server's entries).

## Alternatives considered

N/A: single-statement Path A change; inlining `.close()` + `.clear()` would skip
`forget` and over-wipe the shared registry, so the shared helper is the correct
primitive.

## Implementation
### Target file

`scripts/agent/http_lifecycle_subprocess_launcher.py`

### Procedure

Inside `create_and_validate_proc`, insert `self.close_stderr_log(server_key, stderr_fh)`
as the first statement inside the empty-command guard, before the `raise HttpStartupError(...)`.

### Method

The guard currently reads:

```python
        if not cfg.cmd or not cfg.cmd[0]:
            raise HttpStartupError(
                StartupFailure(
                    server_key=server_key,
                    reason="Empty command configuration",
                    stderr_full="",
                )
            )
```

Add the cleanup call between the `if` and the `raise`, matching the value-error and
`Popen`-exception branches' indentation and argument order.

### Details

Result:

```python
        if not cfg.cmd or not cfg.cmd[0]:
            self.close_stderr_log(server_key, stderr_fh)
            raise HttpStartupError(
                StartupFailure(
                    server_key=server_key,
                    reason="Empty command configuration",
                    stderr_full="",
                )
            )
```

## Compatibility considerations

None: the success path, the value-error branch, the `Popen`-exception branch, and the
`getpgid`-failure branch are untouched. The empty-command message
(`"Empty command configuration"`) is unchanged.

## Security considerations

N/A: no auth, secret, or input-handling change.

## Rollback considerations

N/A: revert the commit.

## Validation plan

| Target File/Module | Testing Strategy (Unit) | Tool / Command | Expected Outcome |
|---|---|---|---|
| `create_and_validate_proc` empty-command path | Regression via `test_empty_command_raises_before_spawn`: handle closed once, registry entry removed | `uv run pytest tests/agent/test_http_lifecycle.py` | `stderr_fh.close` called once; `"test" not in mgr._stderr_files`; short-circuit assertions still hold |

## Completion criteria

- Raising `HttpStartupError` on an empty command closes the inherited stderr handle.
- Raising `HttpStartupError` on an empty command drops `self._stderr_files[server_key]`.
- The other failure branches and the success path are unchanged.

## Out of Scope

The success path (handle stays open for the process lifetime); the non-empty
value-error path and `Popen`-failure cleanup; `Popen` construction, pipe setup, or
`getpgid` handling.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |

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
- **Requirement ID**: `REQ-001` (release the inherited stderr handle and drop the registry entry on the empty-command path via `close_stderr_log`)
- **Source issue**: issues/20261029-220634_lifecyc001_empty-cmd-stderr-leak.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261030-001217_lifecyc001_empty-cmd-stderr-leak.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261030-072145
- **Related target files**: scripts/agent/http_lifecycle_subprocess_launcher.py
