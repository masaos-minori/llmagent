## Goal

Remove pure delegation wrapper methods (`_open_stderr_log`, `_terminate_with_timeout`, `_close_and_forget_stderr`) from HttpServerLifecycleManager, retain `shutil` import for test patching, preserve custom methods (`_read_stderr_tail`, `_wait_existed`), and document `MCPSERVER_HEALTH_TIMEOUT` constant usage.

## Scope

- **In-Scope**: Remove 3 pure delegation wrapper methods; update call sites to use direct component invocations; retain `shutil` import; preserve `_read_stderr_tail` and `_wait_existed`; document `MCPSERVER_HEALTH_TIMEOUT` constant usage; update module docstring
- **Out-of-Scope**: Modifying McpServerConfig schema; changing subprocess launch arguments or security model; removing `_read_stderr_tail` or `_wait_existed`; removing `shutil` import

## Assumptions
- Callers of the removed wrapper methods exist only within http_lifecycle.py itself (verified via grep)
- The `shutil` import on line 23 is confirmed needed for test patching (CommandValidator has its own `import shutil`)
- `_read_stderr_tail` and `_wait_existed` contain custom logic beyond simple delegation

## Design decisions
- Only pure delegation wrappers are removed; methods with custom logic are preserved because they perform inline seek/read/decode and proc.poll() polling respectively
- `shutil` import retained in http_lifecycle.py because tests patch `agent.http_lifecycle.shutil.which` — CommandValidator has its own `import shutil` so this is not a functional dependency but a test infrastructure dependency

## Alternatives considered
- Removing ALL wrapper methods including `_read_stderr_tail` and `_wait_existed`: rejected because they contain non-trivial custom logic
- Removing `shutil` import: rejected because it breaks test patching infrastructure

## Implementation
### Target file
scripts/agent/http_lifecycle.py
### Procedure

1. Verify all call sites of the three wrapper methods within http_lifecycle.py
2. Replace each call site with direct component invocation
3. Delete the three wrapper method definitions
4. Retain `shutil` import with noqa comment
5. Preserve `_read_stderr_tail` and `_wait_existed` method definitions
6. Document `MCPSERVER_HEALTH_TIMEOUT` constant usage
7. Update module docstring to reflect final delegation design

### Method
Inline replacement pattern — for each removed wrapper method, find every call site in http_lifecycle.py and replace with the equivalent direct component invocation:

- `_open_stderr_log(server_key, cfg)` → `self._stderr_log_manager.open_log(server_key, cfg)`
- `_terminate_with_timeout(proc, server_key, timeout=X)` → `await self._process_terminator.terminate_with_timeout(proc, server_key, timeout=X)`
- `_close_and_forget_stderr(server_key, stderr_fh)` → inline operations: `stderr_fh.close(); self._stderr_files.pop(server_key, None); self._stderr_log_manager.forget(server_key)`

### Details
**Step 1: Identify call sites (already verified)**
- `_open_stderr_log`: called at line 258 in `_create_and_validate_proc`
- `_terminate_with_timeout`: called at lines 309, 404, 469
- `_close_and_forget_stderr`: called at lines 273, 298, 322

**Step 2: Replace call sites**
- Line 258: `self._open_stderr_log(server_key, cfg)` → `self._stderr_log_manager.open_log(server_key, cfg)`
- Line 309: `await self._terminate_with_timeout(proc, server_key, timeout=TERMINATE_TIMEOUT_SEC)` → `await self._process_terminator.terminate_with_timeout(proc, server_key, timeout=TERMINATE_TIMEOUT_SEC)`
- Line 404: `await self._terminate_with_timeout(proc, server_key, timeout=TERMINATE_TIMEOUT_SEC)` → `await self._process_terminator.terminate_with_timeout(proc, server_key, timeout=TERMINATE_TIMEOUT_SEC)`
- Line 469: `await self._terminate_with_timeout(proc, server_key)` → `await self._process_terminator.terminate_with_timeout(proc, server_key)`
- Lines 273, 298, 322: Replace `_close_and_forget_stderr(server_key, stderr_fh)` with inline: `stderr_fh.close(); self._stderr_files.pop(server_key, None); self._stderr_log_manager.forget(server_key)`

**Step 3: Delete wrapper method definitions**
- Delete `_open_stderr_log` method (lines 89-91)
- Delete `_terminate_with_timeout` method (lines 123-132)
- Delete `_close_and_forget_stderr` method (lines 235-239)

**Step 4: Retain shutil import**
- Keep line 23: `import shutil  # noqa: F401 — kept for tests patching agent.http_lifecycle.shutil.which (shared module object also used by CommandValidator)`

**Step 5: Preserve custom methods**
- Keep `_read_stderr_tail` method definition (lines 93-105)
- Keep `_wait_exited` method definition (lines 107-121)

**Step 6: Document MCPSERVER_HEALTH_TIMEOUT constant**
- Line 45: `MCPSERVER_HEALTH_TIMEOUT: float = 5.0` — define the constant (source of truth)
- Line 445: `timeout=httpx.Timeout(timeout=MCPSERVER_HEALTH_TIMEOUT)` — used in `start()` method's httpx.AsyncClient timeout
- This constant is moved out of http_lifecycle.py by the health_checker procedure (see separate implementation procedure)

**Step 7: Update module docstring**
- Update the module-level docstring to reflect that HttpServerLifecycleManager is now a true composition facade with no wrapper methods

## Compatibility considerations
- All callers of the removed methods must be updated simultaneously — no partial migration possible
- The inline replacement for `_close_and_forget_stderr` must replicate the exact same side effects: close handle, pop from dict, forget log path

## Security considerations
- No security-relevant behavior changes — only structural refactoring
- The `shutil` import retention preserves existing test patching capability for CommandValidator validation logic

## Rollback considerations
- If any call site replacement causes regressions, revert to the original wrapper method calls
- The wrapper method definitions can be restored from git history if needed
## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| scripts/agent/http_lifecycle.py | Unit: verify wrapper methods removed | `grep -c "_open_stderr_log\|_terminate_with_timeout\|_close_and_forget_stderr" scripts/agent/http_lifecycle.py` | Returns 0 |
| scripts/agent/http_lifecycle.py | Unit: verify shutil import retained | `grep -c "import shutil" scripts/agent/http_lifecycle.py` | Returns 1 |
| scripts/agent/http_lifecycle.py | Unit: verify custom methods preserved | `grep -c "_read_stderr_tail\|_wait_exited" scripts/agent/http_lifecycle.py` | Returns 2+ |
| scripts/agent/http_lifecycle.py | Unit: verify MCPSERVER_HEALTH_TIMEOUT defined | `grep -c "MCPSERVER_HEALTH_TIMEOUT" scripts/agent/http_lifecycle.py` | Returns 2+ |
| All lifecycle modules | Integration: run full test suite | `pytest tests/agent/test_http_lifecycle*.py` | All tests pass |
## Completion criteria

- Three wrapper methods (`_open_stderr_log`, `_terminate_with_timeout`, `_close_and_forget_stderr`) no longer exist as methods in HttpServerLifecycleManager class body
- All call sites replaced with direct component invocations producing identical behavior
- `shutil` import present in http_lifecycle.py with noqa comment
- `_read_stderr_tail` and `_wait_existed` methods still present and unchanged
- `MCPSERVER_HEALTH_TIMEOUT` constant defined in http_lifecycle.py with documented usage
- Module docstring updated to reflect final delegation design
- All existing unit tests pass without modification

## Out of scope
- Modifying McpServerConfig schema
- Changing subprocess launch arguments or security model
- Adding new error types or changing existing error semantics
- Performance optimization beyond what the refactoring naturally achieves

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20260920-151456 | 20260920-151456 |  |
| 2 | Add or update tests per Validation plan | Completed | 20260920-151615 | 20260920-151615 |  |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20260920-151615 | 20260920-151615 |  |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20260920-151615 | 20260920-151615 |  |

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
- **Requirement ID**: REQ-002, REQ-003, REQ-006
- **Source issue**: issues/20260920-125036_refactor_http_lifecycle_full_delegation.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260920-130856_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260920-131846
- **Related target files**: scripts/agent/http_lifecycle.py