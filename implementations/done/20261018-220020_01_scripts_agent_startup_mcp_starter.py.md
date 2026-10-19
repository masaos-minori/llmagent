## Goal

Remove the unreachable graceful-disable path for non-required subprocess MCP servers from
`scripts/agent/startup_mcp_starter.py`, so the startup module agrees with the documented
fail-closed constraint without changing any startup runtime behavior. Specifically: remove the
`if not cfg.required:` graceful-disable branch (and its now-redundant `else`) from
`McpServerStarter.start_servers`, leaving only the fatal-raise path; delete the `disable_server`
method if it has no remaining callers.

## Scope

- **In-Scope**:
  - Remove the `if not cfg.required:` graceful-disable branch (and its now-redundant `else`) from
    `McpServerStarter.start_servers` in `scripts/agent/startup_mcp_starter.py`, leaving only the
    fatal-raise path.
  - Delete the `disable_server` method from `McpServerStarter` if it has no remaining callers.
- **Out-of-Scope**:
  - Do not change the `required=false` rejection for subprocess servers.
  - Do not alter the `required=true` fail-closed spawn behavior.
  - Do not refactor the retry helper or health-check flow.
  - No `docs/*.md` changes.

## Assumptions

- Every subprocess server is `required=true` at runtime, because `McpServerConfig` construction
  rejects `required=false` for `startup_mode=subprocess` (`_validate_startup_requirements` raises at
  `scripts/shared/mcp_config.py:169`).
- `disable_server` has no remaining callers after removing the single call site in `start_servers`
  (verified by grep before deletion: exactly one caller, line 116).
- `retry_once_with_delay` re-raises on second failure rather than returning `None`, so the `else`
  branch that consults `cfg.required` is only reachable when the retry itself returns `None` (a
  process that neither starts nor raises). Even then `cfg.required` is always `true` for subprocess
  servers, so the branch always takes the fatal-raise path.

## Design decisions

- Behavior-preserving cleanup: collapsing the two-post-retry-branch structure to a single fatal
  raise is the only behavior any real configuration can already exhibit.
- Delete `disable_server` entirely (it has no remaining callers); do not leave a stub.
- Preserve the retry-once semantics and the surrounding `except` handler unchanged.

## Alternatives considered

- Leaving the dead branch in place — rejected: it is a maintenance hazard (a future author may add
  logic depending on the graceful-disable path).
- Guarding `disable_server` with a deprecation warning instead of deleting — rejected: it has no
  callers at all; there is nothing to deprecate.

## Implementation

### Target file

`scripts/agent/startup_mcp_starter.py`

### Procedure

1. Confirm via `rg`/`grep` that `disable_server` and the `if not cfg.required:` branch have no
   callers outside the single call site (production or test). Record the result. (REQ-002)
2. In `McpServerStarter.start_servers`, replace the post-retry decision block (currently
   `scripts/agent/startup_mcp_starter.py:112-122`) with a single fatal raise:
   ```python
                       else:
                           # Subprocess start failed — fail closed (required=true always for subprocess servers)
                           raise RuntimeError(
                               f"MCP subprocess {key!r} failed to start after retry"
                           )
   ```
   Remove the `if not cfg.required:` branch, its `await self.disable_server(key, cfg)` call, the
   trailing `continue`, and the now-redundant `else`.
3. Delete the `disable_server` method (`scripts/agent/startup_mcp_starter.py:213-222`) now that its
   only caller is gone.
4. Run the affected MCP lifecycle / startup test targets, then `ruff` and `mypy` on the touched
   files, and confirm no subprocess-server startup behavior changed. (AC-001, AC-002, AC-004)

### Method

- **Collapse the branch (REQ-001).** After `retry_once_with_delay`, the only post-retry action is
  the fatal `RuntimeError`. Remove the `if not cfg.required:` / `else` split and the `continue`;
  preserve the retry-once semantics and the surrounding `except (OSError, RuntimeError, TimeoutError,
  ConnectionRefusedError, ConnectionResetError, BrokenPipeError)` handler unchanged.
- **Delete `disable_server` (REQ-002).** Its sole caller was the removed branch (`:116`). Confirm a
  single caller via grep before deleting; delete the whole method (`:213-222`), including its
  docstring and body (`cfg.startup_mode = StartupMode.NONE; cfg.tool_names = []`).
- **Preserve behavior (AC-004).** All subprocess servers remain `required=true` and fail closed on
  spawn failure; no runtime behavior changes.

### Details

- `REQ-001`: `start_servers` no longer branches on `cfg.required`; the only post-retry action is
  the fatal raise.
- `REQ-002`: `disable_server` is removed, since it has no remaining callers.
- **UNK-01:** `disable_server` is referenced by a single caller (the `required=false` branch in
  `start_servers`); `tests/shared/test_mcp_config.py::test_subprocess_non_required_rejected` confirms
  such a config is rejected at construction; no test calls `disable_server`. Not blocking.

## Compatibility considerations

Behavior-preserving cleanup. No public or runtime-facing interface change; `disable_server` was
private and had no external callers.

## Security considerations

N/A: no change to security-relevant behavior; the fail-closed spawn policy is preserved.

## Rollback considerations

N/A: revert the commit.

## Validation plan

| Target File/Module | Testing Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| `scripts/agent/startup_mcp_starter.py` | Unit — subprocess startup / health lifecycle | `uv run pytest tests/agent/test_startup_mcp_lifecycle.py` (and related startup targets) | Tests pass; no test references the removed branch or `disable_server` |
| `scripts/agent/startup_mcp_starter.py` | Static — lint and type check | `uv run ruff check` / `uv run mypy` | Clean (no new findings) |

## Completion criteria

- `start_servers` no longer branches on `cfg.required`; the only post-retry action is the fatal
  raise (AC-001).
- `disable_server` is removed (AC-002).
- No subprocess-server startup behavior changed (AC-004).

## Out of scope

Changing the `required=false` rejection for subprocess servers, altering the `required=true`
fail-closed spawn behavior, refactoring the retry helper or health-check flow, and any
`docs/*.md` change.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261019-102757 | 20261019-102757 | REQ-001/002 Removed graceful-disable branch + disable_server; existing startup tests pass |
| 2 | Add or update tests per Validation plan | Completed | 20261019-102757 | 20261019-102757 | REQ-001/002 N/A: behavior-preserving cleanup, no new tests required |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261019-102757 | 20261019-102757 | all REQs ruff/mypy clean; test_startup_mcp_lifecycle(16) + test_startup_mcp_starter(7) pass |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20261019-102757 | 20261019-102757 | N/A N/A: no docs in scope |

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
- **Requirement ID**: `REQ-001`, `REQ-002`
- **Source issue**: issues/20261018-200733_agent001_agent-startup-graceful-disable-path-for-non-required-subprocess-mcp-servers.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261018-220020_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261018-220020
- **Related target files**: scripts/agent/startup_mcp_starter.py