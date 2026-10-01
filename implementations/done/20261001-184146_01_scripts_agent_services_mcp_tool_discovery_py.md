# Implementation Procedure: mcp_tool_discovery.py — remove dead code `_fetch_server_tools()` and `_validate_and_normalize_entry()`

## Goal

Remove the unused `_fetch_server_tools()` method and its private helper `_validate_and_normalize_entry()` from `McpToolDiscoveryService` in `scripts/agent/services/mcp_tool_discovery.py`, eliminating latent divergence between two parallel tool-validation implementations. Implements `REQ-001` (short purpose: delete `_fetch_server_tools()` after confirming no caller), `REQ-002` (short purpose: delete `_validate_and_normalize_entry()` if unused).

## Scope

- **In scope**: Deletion of `_fetch_server_tools()` and `_validate_and_normalize_entry()` methods from `scripts/agent/services/mcp_tool_discovery.py`; verification that no caller remains.
- **Out of scope**: Any refactor of the live `McpToolsHttpClient.fetch_tools()` path; unifying the two validation implementations into one.

## Assumptions

- No dynamic dispatch (e.g., `getattr` calls, `__getattr__` hooks) reaches `_fetch_server_tools()` at runtime (confirmed via grep).
- No subclass overrides of `McpToolDiscoveryService` depend on these methods (confirmed: no subclasses found in `scripts/`).
- The imports used by both dead methods (`httpx`, `get_effective_health_timeout`, `MCP_TOOL_SCHEMA_VERSION`, `StartupCheckStatus`, `_warning_fetch_result`, `_warning_entry`, `validate_tool_schema_v2`, `_REQUIRED_SCHEMA_V2_FIELDS`) are all referenced by the live `fetch_tools()` / `ToolEntryValidator` paths, so deletion should leave no unused import. Still run `ruff check` to confirm.

## Design decisions

- **Delete both methods together**: since `_validate_and_normalize_entry()` is called only from `_fetch_server_tools()`, deleting the latter makes the former unreachable. Remove both in a single change to avoid leaving orphaned dead code.
- **Preserve `discover_all()` behavior**: the active path builds the registry via `McpToolsHttpClient.fetch_tools()` + `ToolEntryValidator.validate_entry()`, not these methods. Deletion must not alter this path.

## Alternatives considered

- **Delete only `_fetch_server_tools()` and leave `_validate_and_normalize_entry()`**: rejected because it would leave an orphaned dead method. REQ-002 requires removing it if unused after REQ-001.
- **Consolidate the two validation implementations**: out of scope per the Plan. This is a separate concern.

## Implementation

### Target file

`scripts/agent/services/mcp_tool_discovery.py`

### Procedure

1. Read `scripts/agent/services/mcp_tool_discovery.py` and confirm the exact locations of `_fetch_server_tools()` and `_validate_and_normalize_entry()` methods. Confirm via `tests/agent/services/test_mcp_tool_discovery.py` that no test asserts on these methods before deletion.
2. Delete the `_fetch_server_tools()` method from `McpToolDiscoveryService`.
3. Delete the `_validate_and_normalize_entry()` method from `McpToolDiscoveryService` (it becomes unreachable after step 2).
4. Verify no unused imports remain by running `ruff check` on the file.

### Method

- Keep the change minimal: only delete the two dead methods. Do not modify any other method, class, or module-level construct.
- After deletion, verify the file still parses correctly (no dangling references).
- Run `ruff check` to confirm no new lint errors (especially unused-import).

### Details

- Current code at the shutdown-done branch (lines 155-158):
  ```python
  # Cancellation handled by shutdown watcher — do not cancel here
  if shutdown_done or shutdown_coro in done:
      self._abort_input()
      return None
  ```
- New code should be:
  ```python
  if shutdown_done or shutdown_coro in done:
      input_coro.cancel()
      try:
          await input_coro
      except asyncio.CancelledError:
          pass
      self._abort_input()
      return None
  ```
- The comment must be removed or replaced with one stating that `_read_input` performs the cancellation.

## Compatibility considerations

- `discover_all()` still builds the same `RuntimeToolRegistry` and emits the same findings (AC-3).
- Existing discovery tests (`tests/agent/services/test_mcp_tool_discovery.py`) must continue to pass.
- No public interface changes — both deleted methods are private (`_` prefix).

## Security considerations

- N/A: dead code removal does not introduce security-sensitive paths.

## Rollback considerations

- Single-file change; reverting the commit restores the original methods with no data migration or config change. `deploy.sh` impact is limited to the internal service; no deploy/config change.

## Validation plan

| Target File/Module | Testing Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| `scripts/agent/services/mcp_tool_discovery.py` | Lint check | `ruff check scripts/agent/services/mcp_tool_discovery.py` | Clean (no errors) |
| `scripts/agent/services/mcp_tool_discovery.py` | Type check | `mypy scripts/agent/services/mcp_tool_discovery.py` | Clean (no type errors) |
| `tests/agent/services/test_mcp_tool_discovery.py` | Regression test | `pytest tests/agent/services/test_mcp_tool_discovery.py` | All tests pass |

## Completion criteria

- No remaining definition or call site for `_fetch_server_tools()` in the repository (AC-001 / REQ-001).
- If `_validate_and_normalize_entry()` is also unused, it is removed; otherwise left intact (AC-002 / REQ-002).
- `discover_all()` still builds the same `RuntimeToolRegistry` and emits the same findings (AC-003 / REQ-003).
- `ruff` / `mypy` clean on the file (AC-004 / REQ-004).

## Out of scope

- Any refactor of the live `McpToolsHttpClient.fetch_tools()` path.
- Unifying the two validation implementations into one.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Phase 1: Preparation / Verification — confirm no callers exist | In Progress | 20261001-184231 | — | REQ-001, REQ-002 |
| 2 | Phase 2: Core Logic Implementation — delete `_fetch_server_tools()` and `_validate_and_normalize_entry()` | Pending | — | — | REQ-001, REQ-002 |
| 3 | Phase 3: Deployment & Verification — ruff/mypy/pytest | Pending | — | — | REQ-003, REQ-004 |

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
- **Requirement ID**: `REQ-001` — delete `_fetch_server_tools()` after confirming no caller; `REQ-002` — delete `_validate_and_normalize_entry()` if unused
- **Source issue**: issues/done/20260930-161945_mcp001_mcp_tool_discovery_fetch_server_tools_dead_code.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261001-093812_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261001-184146
- **Related target files**: scripts/agent/services/mcp_tool_discovery.py