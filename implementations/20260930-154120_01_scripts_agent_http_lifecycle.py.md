## Goal

Remove the duplicated stderr-tail byte-window logic from `HttpServerLifecycleManager` by inlining the delegation into `StderrLogManager.read_tail` inside its sole caller `_cleanup_server_resources`, then delete the now-unused wrapper method `_read_stderr_tail` and module constant `_STDERR_TAIL_BYTES`, and drop the docstring bullet that lists `_read_stderr_tail`. Honors REQ-001, REQ-002, REQ-003.

## Scope

Modify `scripts/agent/http_lifecycle.py` only. Four edits total: inline the delegation call, delete the `_read_stderr_tail` method, delete the `_STDERR_TAIL_BYTES` constant, remove the docstring bullet. Reference file `scripts/agent/http_lifecycle_stderr_log_manager.py` is read-only (confirm `read_tail` semantics); not modified. The three integration-test patch sites are covered by the second implementation procedure document (`20260930-154120_02_tests_agent_test_http_lifecycle_integration_py.md`).

## Assumptions

- `_cleanup_server_resources` is the sole internal caller of `_read_stderr_tail` (confirmed via `rg` across `scripts/`).
- `_STDERR_TAIL_BYTES` is referenced only inside `_read_stderr_tail`; deleting the method makes it unreferenced repo-wide (confirmed via `rg _STDERR_TAIL_BYTES scripts/ tests/`).
- Decoding `read_tail`'s `bytes` return with `.decode(errors="replace")` reproduces the previous decode exactly.
- `read_tail` is behavior-equivalent to the old body for every reachable input: untracked key -> empty, small file -> whole content, large file -> last N bytes, `OSError` -> empty. Behavior equivalence is documented in the source plan's Design section.

## Design decisions

- Inline the delegation into `_cleanup_server_resources` rather than replacing the `_read_stderr_tail` body with a one-line delegate. Rationale: the class documents "zero pure-delegation wrappers"; `_read_stderr_tail` has exactly one caller, so removing the wrapper and inlining the call satisfies that contract cleanly.
- Decode `read_tail`'s `bytes` return at the call site with `.decode(errors="replace")` to preserve the `str` return type observed by callers.

## Alternatives considered

- Replace `_read_stderr_tail` body with `return self._stderr_log_manager.read_tail(server_key).decode(errors="replace")` and keep the wrapper. Rejected: leaves a pure-delegation wrapper that contradicts the "zero pure-delegation wrappers" contract; the Issue prefers removing it.
- Keep `_STDERR_TAIL_BYTES` as a thin alias to `StderrLogManager._DEFAULT_STDERR_TAIL_BYTES`. Rejected: still a duplicate constant serving no independent purpose; becomes dead once the method is removed.

## Implementation
### Target file
`scripts/agent/http_lifecycle.py`

### Procedure
1. In `_cleanup_server_resources`, replace `self._read_stderr_tail(server_key)` with `self._stderr_log_manager.read_tail(server_key).decode(errors="replace")` (wrapped per line-length rule below).
2. Delete the `_read_stderr_tail` method definition (currently lines 95-107: open/seek/decode body).
3. Delete the module-level constant `_STDERR_TAIL_BYTES` (currently line 53).
4. Remove the `- _read_stderr_tail: seek/read/decode implementation for stderr log tailing` bullet from the module docstring "Custom logic retained in this class" list.

### Method
Locate the four edits by symbol, not by line number (line numbers drift):
- `_cleanup_server_resources` — currently returns `self._read_stderr_tail(server_key)`.
- `_read_stderr_tail` method spanning the `open()`/`seek()`/`decode` body.
- Module-level `_STDERR_TAIL_BYTES: int = 64 * 1024` among the other module constants.
- Docstring block near the top of the file under "Custom logic retained in this class:".

### Details
Recommended replacement body for `_cleanup_server_resources` (ruff-formatted, stays within 88 chars):
```python
    def _cleanup_server_resources(self, server_key: str) -> str:
        """Read stderr tail, close stderr file handle, and remove tracking data for a server."""
        stderr_content = self._stderr_log_manager.read_tail(server_key).decode(
            errors="replace"
        )
        self._clear_server_tracking_data(server_key)
        return stderr_content
```
Do NOT relax the line-length rule. If the expression must be collapsed to one line, shorten the local name (e.g. `tail`) so the line stays <= 88 chars:
```python
        tail = self._stderr_log_manager.read_tail(server_key).decode(errors="replace")
```
After deleting `_read_stderr_tail`, confirm no remaining reference to it exists anywhere in `scripts/` (only the docstring bullet and the `_cleanup_server_resources` call site referenced it; both are handled here).
After deleting `_STDERR_TAIL_BYTES`, run `rg _STDERR_TAIL_BYTES scripts/ tests/` and confirm zero matches before finishing (AC-002 / T-004).
The docstring edit removes only the `_read_stderr_tail` bullet; keep the `_wait_exited` and `MCPSERVER_HEALTH_TIMEOUT` bullets intact.

## Compatibility considerations

- Callers of `_cleanup_server_resources` (`_health_poll_until_ready`) expect a `str`; `.decode(errors="replace")` preserves that contract. No external API or observable behavior changes.
- Behavior equivalence: untracked key -> `""`, `OSError` -> `""`, otherwise the decoded last-N-bytes window. Identical output to the previous implementation.

## Security considerations

- No new injection or secret-exposure surface. The returned text is already masked by `_mask_secrets` at the call site; decoding does not change masking.
- No subprocess/shell/config-value handling introduced.

## Rollback considerations

- Behavior-preserving refactor. To revert, restore the `_read_stderr_tail` method, the `_STDERR_TAIL_BYTES` constant, the original `_cleanup_server_resources` body, and the docstring bullet from the prior commit. No schema/data/migration impact.

## Validation plan

- Static: `uv run ruff check scripts/agent/http_lifecycle.py tests/agent/test_http_lifecycle_integration.py` clean; `uv run mypy scripts/agent/http_lifecycle.py` clean; `uv run bandit scripts/agent/http_lifecycle.py` clean (T-003).
- Dead symbol: `rg _STDERR_TAIL_BYTES scripts/ tests/` returns no matches (T-004 / AC-002).
- No byte-window logic: `rg` for `open()`/`seek()` inside `scripts/agent/http_lifecycle.py` finds none outside pre-existing unrelated paths (AC-001).
- Tests: `uv run pytest tests/agent/test_http_lifecycle_integration.py tests/agent/test_http_lifecycle_stderr_log_manager.py tests/agent/test_lifecycle.py`; expect 127 passed, 3 skipped, 0 failed (T-001 / AC-004).

## Completion criteria

- `_read_stderr_tail` no longer exists in `scripts/agent/http_lifecycle.py`; no `open()`/`seek()` byte-window logic remains in `HttpServerLifecycleManager` (AC-001).
- `_STDERR_TAIL_BYTES` absent from the file and unreferenced repo-wide (AC-002).
- Module docstring "Custom logic retained in this class" no longer lists `_read_stderr_tail` (AC-003).
- Full affected suites pass at baseline counts (AC-004); ruff/mypy/bandit clean (T-003).

## Out of scope

- Any change to `StderrLogManager.read_tail` semantics, rotation, or configuration.
- Updating the three integration-test patch sites (covered by the second implementation procedure document).
- Refactoring other `_read_*` helpers, `_wait_exited`, or process-management methods.
- Consolidating other duplicate constants.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | Covered by second implementation procedure document |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | Only in-code module docstring (REQ-003) |

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
- **Requirement ID**: REQ-001, REQ-002, REQ-003
- **Source issue**: issues/20260930-134555_refactor_001_remove-duplicated-stderr-tail-logic-in-httpserverlifecyclemanager-by-delegating-to-stderrlogmanager.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260930-144038_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260930-154120
- **Related target files**: scripts/agent/http_lifecycle.py
