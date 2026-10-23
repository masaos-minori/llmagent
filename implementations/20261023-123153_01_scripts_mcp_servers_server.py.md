## Goal
Enforce each server module's posture gate inside `MCPServer.run_http()` so every launch path refuses to bind on a FAILED posture (`REQ-001`, `REQ-002`).

## Scope
- Add a gate step to `run_http()` after the loopback and config-isolation checks and before the uvicorn server is built.
- No change to `attach_auth_middleware`, health, tool-list helpers or the per-module gate functions.

## Assumptions
- All ten server modules define `_enforce_posture_gate()` (verified by grep) and every test fake uses an `app_module` outside the `mcp_servers.` namespace (verified: `test:app`, `empty:app`, `public:app`, `noconfig:app`, and similar).
- The module is 12937 bytes, so about 700 bytes of additions stay under the 16384-byte module-size gate; `mcpstart003` also adds a helper here, so the total must still fit.

## Design decisions
- Resolve the gate from the module named in `app_module` with `importlib`, so no per-server override or launcher change is needed and existing per-module gates stay the single source of failure logging.
- Gate only the `mcp_servers.` namespace: fake servers in tests are not gated, while a real server module without the function raises (fail closed).

## Alternatives considered
- Per-class hook overridden in ten server modules: rejected, `mdq_server.py` is size-baselined at 17987 bytes and cannot grow, and ten edits repeat the same logic.
- Gate in each launcher: rejected, that is the bug; launchers would drift again.

## Implementation
### Target file
`scripts/mcp_servers/server.py`

### Procedure
1. Add `import importlib` to the imports of `scripts/mcp_servers/server.py` (module-level, keep alphabetical order with the existing imports).
2. Add method `_enforce_startup_posture_gate(self) -> None` (new) to `MCPServer`: take `module_name = self.app_module.partition(":")[0]`; return when it does not start with `mcp_servers.`; import the module with `importlib.import_module`; read `_enforce_posture_gate` with `getattr(module, "_enforce_posture_gate", None)`; raise `RuntimeError` naming the module when it is missing; otherwise call it.
3. In `run_http()` call `self._enforce_startup_posture_gate()` after the `restrict_to` block (the `if self.own_config_file: ... else: raise ConfigPermissionError` section) and before `class _LoopbackVerifyingServer`.
4. Update the `run_http()` docstring to mention the posture gate.

### Method
- The gate raises `SystemExit(1)` itself, so `run_http()` does not catch it; the exit propagates before `uvicorn.Config` is created.
- Importing the module inside the gate returns the cached module for launchers and `python -m` (already imported), so no second config load happens.

### Details
- Evidence: `server.py:232-286` (`run_http`); per-module gates, for example `shell_server.py` `_enforce_posture_gate` (logs check ids and reason codes only).
- Reference only: `scripts/mcp_servers/mdq/mdq_server.py` (not edited; baselined at 17987 bytes), `scripts/mcp_launcher.py` (becomes gated without a change).

## Compatibility considerations
- A server that previously bound with a FAILED posture now exits 1 at start; this matches the documented behavior and the Agent's own treatment of the same failure.
- Test fakes with non-`mcp_servers.` modules are unaffected.

## Security considerations
- Closes the documented fail-closed bypass; logs remain limited to check ids and reason codes (existing gate behavior).
- Fail closed when the gate function is missing for a real server module.

## Rollback considerations
- N/A: revert the commit; behavior returns to the `__main__`-only gate.

## Validation plan
- `tests/mcp_servers/test_posture_gate_start_path.py` (tracked in its own document) and the existing `tests/mcp_servers/test_mcp_server_base.py`, `test_config_isolation_fail_closed.py`.
- `uv run pytest tests/mcp_servers tests/agent/test_startup.py tests/agent/test_config_permission_cross_server.py`, `uv run ruff check`, `uv run mypy`, `uv run bandit -r scripts/mcp_servers`, `uv run python tools/check_module_size.py`, `uv run python tools/check_docstrings.py`, `lint-imports`.

## Completion criteria
- `Class().run_http()` with a FAILED posture raises `SystemExit(1)` before `uvicorn.Config` for every real server class.
- Existing `run_http()` tests pass; module-size and docstring gates pass.

## Out of Scope
- Changing which posture checks are FAILED
- Request-handler posture checks (plan UNK-01)
- Removing per-module `__main__` gate calls (plan UNK-02)

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the import, `_enforce_startup_posture_gate()` (new) and the `run_http()` call per Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan (`tests/mcp_servers/test_posture_gate_start_path.py`, tracked in its own document) | Pending | — | — | |
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
- **Requirement ID**: `REQ-001` (gate in `run_http()`), `REQ-002` (missing gate fails closed)
- **Source issue**: issues/20261023-114021_mcpstart002_posture-gate-bypassed-by-launchers-and-mdq-main.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261023-114842_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261023-123153
- **Related target files**: scripts/mcp_servers/server.py
