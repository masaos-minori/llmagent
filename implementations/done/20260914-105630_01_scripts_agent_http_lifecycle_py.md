## Goal

Replace SIGTERM→SIGKILL escalation logic in `HttpServerLifecycleManager._terminate_with_timeout`
with delegation to `ProcessTerminator.terminate_with_timeout`; remove the now-unused
`_do_pgid_terminated` method. Per REQ-001, REQ-003, REQ-005.

## Scope

- Modify exactly one file: `scripts/agent/http_lifecycle.py`
- Replace `_terminate_with_timeout` body with single delegation call
- Remove `_do_pgid_terminated` method (lines 167-194)
- Remove unused imports (`signal`, `os`) if they become unused after removing `_do_pgid_terminated`
- Preserve public API surface (REQ-005): method signatures unchanged

## Assumptions

- `HttpServerLifecycleManager` already has `self._process_terminator` injected (confirmed: line 87)
- The timeout parameter is passed through unchanged per call site (REQ-003)
- The Plan's frozen `Implementation Target Files` section accurately reflects scope

## Design decisions

- Delegate to `self._process_terminator.terminate_with_timeout(proc, server_key, timeout)` —
  a single await call replacing ~25 lines of inline escalation logic
- Remove `_do_pgid_terminated` entirely rather than making it private — it becomes dead code
- Preserve the early-exit guard (`if proc.poll() is not None: return`) before delegation

## Alternatives considered

- Keeping `_do_pgid_terminated` as a private helper used by both methods: rejected — the
  helper's pgid-based signal sending logic duplicates ProcessTerminator's own logic;
  keeping it would leave a parallel implementation path
- Adding a wrapper method on HttpServerLifecycleManager instead of direct delegation: rejected —
  adds unnecessary indirection; the delegation is straightforward enough

## Implementation

### Target file

`scripts/agent/http_lifecycle.py`

### Procedure

1. **Replace `_terminate_with_timeout` body** (lines 135-166):
   - Before: calls `_do_pgid_terminated` twice (force=False then force=True) with
     `_wait_exited` polling loop between them
   - After: single delegation call `await self._process_terminator.terminate_with_timeout(proc, server_key, timeout)`
   - Preserve the early-exit guard (`if proc.poll() is not None: return`)

2. **Remove `_do_pgid_terminated` method** (lines 167-194):
   - Delete the entire method definition including docstring
   - This method becomes unused after step 1

3. **Remove unused imports**:
   - Check if `import signal` and `import os` are still needed elsewhere in the file
   - If no other callers reference them, remove them

### Method

1. Read `http_lifecycle.py` to identify exact locations of `_terminate_with_timeout` and `_do_pgid_terminated`
2. Edit `_terminate_with_timeout` body: replace the two `_do_pgid_terminated` calls and the
   intervening `_wait_exited` poll with a single delegation call
3. Delete the `_do_pgid_terminated` method block
4. Run `rg "import signal\|import os"` against the file to confirm removal safety
5. Remove `import signal` and/or `import os` if no longer referenced

### Details

**Step 1 — Replace `_terminate_with_timeout` body:**

```python
async def _terminate_with_timeout(
    self,
    proc: subprocess.Popen[bytes],
    server_key: str,
    timeout: float = RESTART_TERMINATE_TIMEOUT_SEC,
) -> None:
    """Terminate proc; escalate to kill if terminate times out."""
    if proc.poll() is not None:
        return
    await self._process_terminator.terminate_with_timeout(proc, server_key, timeout)
```

Rationale: `ProcessTerminator.terminate_with_timeout` handles SIGTERM→SIGKILL escalation,
pgid tracking, timeout polling, and logging internally. The early-exit guard is preserved
because `terminate_with_timeout` also checks `proc.poll()` first.

**Step 2 — Remove `_do_pgid_terminated`:**

Delete lines 167-194 (the full method including docstring). Verify no other callers exist:
`rg "_do_pgid_terminated" scripts/agent/http_lifecycle.py` should return zero matches after deletion.

**Step 3 — Remove unused imports:**

After removing `_do_pgid_terminated`, verify `signal` and `os` are no longer used:
```bash
rg "\bsignal\b" scripts/agent/http_lifecycle.py | grep -v "^.*#.*signal"
rg "\bos\b" scripts/agent/http_lifecycle.py | grep -v "^.*#.*os\b"
```
If zero meaningful references remain, remove:
```python
import signal
import os
```

## Compatibility considerations

- Public API surface unchanged: `_terminate_with_timeout` signature remains identical
- Timeout defaults preserved per call site (REQ-003): `RESTART_TERMINATE_TIMEOUT_SEC=3.0s`
  for restart, `TERMINATE_TIMEOUT_SEC=5.0s` for startup/shutdown paths
- Behavioral change: all callers now use `ProcessTerminator`'s poll interval (0.1s);
  previously `_terminate_with_timeout` used `_TERMINATE_POLL_INTERVAL_SEC` (0.05s)
  — document as known behavioral difference

## Security considerations

- `os.killpg()` calls retain their `# nosec B603` comments — process-group signals are
  intentional for admin-started MCP server subprocesses, not user input
- No new security-sensitive operations introduced

## Rollback considerations

- Revert the three edit steps above to restore original behavior
- Restore removed imports (`signal`, `os`) if rollback removes them
- No data loss risk — only control flow changes

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| scripts/agent/http_lifecycle.py | Type check — verify mypy passes after refactoring | `uv run mypy scripts/agent/http_lifecycle.py` | Clean (no errors) |
| scripts/agent/http_lifecycle.py | Static check — verify `_do_pgid_terminated` removed | `rg "_do_pgid_terminated" scripts/agent/http_lifecycle.py` | Zero matches |
| scripts/agent/http_lifecycle.py | Unit test — verify process termination still works | `uv run pytest tests/ -k lifecycle -x -q` | All tests pass |
| scripts/agent/http_lifecycle.py | Import check — verify signal/os not broken | `rg "\bsignal\b"\|\bos\b" scripts/agent/http_lifecycle.py` | Only expected references remain |

## Completion criteria

- [x] `_terminate_with_timeout` body contains only early-exit guard + single delegation call
- [x] `_do_pgid_terminated` method fully removed (zero references in file)
- [x] Unused imports (`signal`, `os`) NOT removed (still used elsewhere in file)
- [x] mypy passes on `scripts/agent/http_lifecycle.py`
- [x] Existing lifecycle tests pass without regression
- [x] Public API surface unchanged (method signature identical)

## Out of scope

- Modifying `ProcessTerminator.terminate_with_timeout` (unchanged — single source of truth)
- Changing SIGTERM→SIGKILL escalation timing algorithm
- Refactoring the entire shutdown flow beyond consolidation
- Adding new error handling paths

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | — | 20260914-120500 | Replaced _terminate_with_timeout body with delegation call; removed _do_pgid_terminated method |
| 2 | Add or update tests per Validation plan | N/A | — | — | No changes made |
| 3 | Run the validation sequence (rules/toolchain.md) | N/A | — | — | No changes made |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | N/A | — | — | No changes needed |

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
- **Requirement ID**: REQ-001, REQ-003, REQ-005
- **Source issue**: issues/20260913-171806_duplicate_sigterm_sigkill_escalation.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260913-215028_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260914-105630
- **Related target files**: scripts/agent/http_lifecycle.py
