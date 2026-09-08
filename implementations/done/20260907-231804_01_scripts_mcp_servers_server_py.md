## Goal

Fail closed when `MCPServer.run_http()` has a falsy `own_config_file` — raise an error at startup instead of silently skipping Config Isolation restriction (REQ-003).

## Scope

Modify exactly one file: `scripts/mcp_servers/server.py::MCPServer.run_http()`. Add an `else` branch after the existing `if self.own_config_file:` guard on line 226.

## Assumptions

- The fail-closed behavior for falsy `own_config_file` should use `ConfigPermissionError` (the existing Config Isolation violation exception in `scripts/shared/config_errors.py`) rather than the proposed `ConfigIsolationError` which does not exist in the codebase.
- No other call sites or dependencies depend on the silent-skip behavior of a falsy `own_config_file`.

## Design decisions

- Use `ConfigPermissionError` as the exception type for the fail-closed path, matching existing Config Isolation violation handling in `config_errors.py`. This avoids introducing a new exception class that would require cross-cutting changes (imports, except clauses) throughout the codebase.
- Raise immediately before the uvicorn server class definition, consistent with the existing loopback address validation above it (line 220-224).

## Alternatives considered

- Defining a new `ConfigIsolationError` class in `config_errors.py`: rejected because no existing code catches this type; would require updating all `except ConfigPermissionError` handlers plus adding new imports everywhere `ConfigLoader.restrict_to()` is called.
- Logging a warning and continuing: rejected because it contradicts ADR-002 Decision #9 ("共通Config Loaderの利用は許可するが、プロセスごとに許可ファイルを限定し、許可外ファイルの読込をRuntime Errorとする") and Fail-Fast Conditions.

## Implementation
### Target file
`scripts/mcp_servers/server.py`

### Procedure
Add an `else` branch after the existing `if self.own_config_file:` guard in `MCPServer.run_http()` (line 226).

### Method
In `MCPServer.run_http()`, locate the block starting at line 226:
```python
        if self.own_config_file:
            from shared.config_loader import ConfigLoader

            ConfigLoader.restrict_to(self.own_config_file)
```
Insert an `else` clause immediately after this block (before the `_LoopbackVerifyingServer` class definition on line 231):
```python
        else:
            from shared.config_errors import ConfigPermissionError
            raise ConfigPermissionError(
                "Config Isolation: own_config_file is falsy — cannot start without config isolation"
            )
```

### Details
1. Open `scripts/mcp_servers/server.py`.
2. Locate line 226: `if self.own_config_file:`.
3. After the `restrict_to()` call on line 229, add an `else` clause indented to match the `if`.
4. Inside the `else` clause, import `ConfigPermissionError` from `shared.config_errors` and raise it with a clear message.
5. Ensure the indentation matches the surrounding code (8 spaces for method body level).

## Compatibility considerations

- Existing tests that mock or set `own_config_file` to a truthy value are unaffected.
- Tests that expect the process to start without Config Isolation when `own_config_file` is falsy will now fail — this is the intended behavior change.
- Any external caller passing `own_config_file=""` or `None` will now receive a startup failure instead of unrestricted operation.

## Security considerations

This change closes a security-relevant gap: a falsy `own_config_file` previously allowed the MCP server to run without Config Isolation restriction, violating ADR-002 Decision #9. The fail-closed behavior ensures that Config Isolation can never be silently bypassed.

## Rollback considerations

Reverting this change means removing the `else` clause and restoring the silent-skip behavior. If the change causes unexpected failures in deployment, the rollback is a single-line removal of the `else` block. However, reverting re-introduces the Config Isolation bypass vulnerability.

## Validation plan

| Target | Testing Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| `scripts/mcp_servers/server.py` | Unit: verify falsy `own_config_file` raises `ConfigPermissionError` | `pytest -xvs` on new test | `ConfigPermissionError` raised |
| `scripts/mcp_servers/server.py` | Unit: verify truthy `own_config_file` still calls `restrict_to()` | `pytest -xvs` on existing test | No regression |

## Completion criteria

- [ ] `MCPServer.run_http()` with a falsy `own_config_file` raises `ConfigPermissionError` at startup instead of running unrestricted
- [ ] `MCPServer.run_http()` with a truthy `own_config_file` continues to call `ConfigLoader.restrict_to()` normally
- [ ] New unit test exists asserting the falsy `own_config_file` fail-closed path
- [ ] Existing tests pass without modification

## Out of scope

- Adding `ConfigIsolationError` as a new exception class (rejected per design decision above).
- Modifying any other file in the codebase.
- Changing `ConfigLoader.restrict_to()` behavior.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the fail-closed branch in MCPServer.run_http() | Pending | — | — | |
| 2 | Add unit test for falsy own_config_file fail-closed path | Pending | — | — | |
| 3 | Run the validation sequence (rules/toolchain.md) | Pending | — | — | |
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
- **Requirement ID**: REQ-003
- **Source issue**: issues/done/20260902-101452_h02_config_loader_fail_closed_gap.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260907-203653_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 2026-09-07T23:18:04Z
- **Related target files**: scripts/mcp_servers/server.py
