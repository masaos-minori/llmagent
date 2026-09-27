## Goal

Fix `tests/integration/test_mcp_transport_crash.py::test_d05_http_timeout_races_lifecycle_termination`'s reference to `HttpServerLifecycleManager`'s removed `_terminate_with_timeout` wrapper method, redirecting it to the current component-delegated target (`self._process_terminator.terminate_with_timeout`) (REQ-002).

## Scope

In scope: the 1 call site (line ~201) and the docstring mention (line ~151) in this file. Out of scope: `scripts/agent/http_lifecycle.py` and its extracted component modules (confirmed already correct; the refactor removing `_terminate_with_timeout` is intentional and complete).

## Assumptions

- No other assumption beyond `agent002`'s Plan-level evidence (this is the same fix pattern as `tests/agent/test_lifecycle.py`'s implementation procedure document, applied to a single call site here).

## Design decisions

- Follow the exact fix pattern already applied to `tests/agent/test_http_lifecycle_warning.py` in commit `d98dda9a`: `mgr._terminate_with_timeout(proc, key, timeout=1.0)` → `mgr._process_terminator.terminate_with_timeout(proc, key, timeout=1.0)`.

## Alternatives considered

- N/A: a single call site with one unambiguous fix; no alternative approach considered.

## Implementation

### Target file

`tests/integration/test_mcp_transport_crash.py`

### Procedure

1. Re-confirm the call site's exact current line/form via `rg -n "_terminate_with_timeout" tests/integration/test_mcp_transport_crash.py`.
2. Replace `mgr._terminate_with_timeout(proc, "d05_server", timeout=1.0)` with `mgr._process_terminator.terminate_with_timeout(proc, "d05_server", timeout=1.0)`.
3. Update the docstring mention (line ~151, "a concurrent `HttpServerLifecycleManager._terminate_with_timeout()` call") to reference the current method path (`HttpServerLifecycleManager._process_terminator.terminate_with_timeout()`) for accuracy.

### Method

Direct call-site and docstring-text replacement — no test logic change.

### Details

- Before: `terminate_task = asyncio.create_task(mgr._terminate_with_timeout(proc, "d05_server", timeout=1.0))`
- After: `terminate_task = asyncio.create_task(mgr._process_terminator.terminate_with_timeout(proc, "d05_server", timeout=1.0))`
- `ProcessTerminator.terminate_with_timeout(self, proc: object, server_key: str, timeout: float = 5.0) -> None` (`scripts/agent/http_lifecycle_process_terminator.py:71-73`) is the confirmed replacement target.

## Compatibility considerations

- No production code changes; test-only fix.

## Security considerations

N/A: test-only fix.

## Rollback considerations

- `git revert` the commit, or manually restore the prior call site and docstring text.

## Validation plan

| Target | Strategy | Command | Expected |
|---|---|---|---|
| `tests/integration/test_mcp_transport_crash.py` | Integration | `uv run pytest tests/integration/test_mcp_transport_crash.py -q` | All tests pass |

## Completion criteria

- `uv run pytest tests/integration/test_mcp_transport_crash.py::test_d05_http_timeout_races_lifecycle_termination -q` passes.
- `uv run pytest tests/integration/test_mcp_transport_crash.py -q` (full file) passes with no regression.

## Out of scope

- `tests/agent/test_lifecycle.py` (covered by its own implementation procedure document from this same Plan).
- `scripts/agent/http_lifecycle.py` and its component modules (confirmed already correct).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | — | — | Replaced `_terminate_with_timeout` with `_process_terminator.terminate_with_timeout` at 1 call site + docstring |
| 2 | Add or update tests per Validation plan | Completed | — | — | N/A: no new test needed |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | — | — | All 5 tests pass |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | — | — | N/A: no docs/00_index.md task-scope mapping |

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
- **Requirement ID**: REQ-002: fix the `_terminate_with_timeout` reference in `tests/integration/test_mcp_transport_crash.py`
- **Source issue**: issues/20260927-075239_agent002_httpserverlifecyclemanager-missing-lifecycle-methods-tests-reference.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260927-081423_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260927-091401
- **Related target files**: tests/integration/test_mcp_transport_crash.py
