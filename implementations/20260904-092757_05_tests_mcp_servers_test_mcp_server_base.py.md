## Goal
Add tests for `MCPServer`'s new bind-address validation (row 2), covering
private-LAN/wildcard/public rejection and `127.0.0.1`/`::1` acceptance.

## Scope
- **In-Scope**: a new test class exercising `run_http()`'s bind-address
  validation, using or extending the existing `_SimpleServer`/`_EmptyServer`
  fixtures (verified 2026-09-04, lines 19-44).
- **Out-of-Scope**: `TestListTools`, `TestHealth`, `TestAttachAuthMiddleware`,
  `TestTruncateWithMeta`, `TestAuditLog`, `TestAppModuleImportability` (lines
  46-343+) — confirmed by direct read to be unrelated to bind-address
  validation.

## Assumptions
- Must execute after row 2's `scripts/mcp_servers/server.py` edit lands —
  this row's tests exercise the new validation logic directly.
- `run_http()` calls the blocking `uvicorn.run(...)`, so a test cannot call
  it directly without actually starting a server; the validation check must
  be testable in isolation. If row 2 implements validation as a separate
  method/function (e.g. `_validate_loopback_host()`), this row's tests call
  that unit directly. If row 2 embeds the check inline in `run_http()`
  without factoring it out, this row's tests instead patch `uvicorn.run`
  (e.g. via `unittest.mock.patch`) to prevent an actual server start while
  still exercising `run_http()`'s validation path before that call —
  determine the exact test structure at execution time based on row 2's
  final implementation shape.

## Design decisions
- Add a new fixture subclass `_PublicBoundServer(MCPServer)` with
  `http_host = "192.168.1.1"` (mirroring `_SimpleServer`'s structure, lines
  19-34) for use in rejection tests, alongside the existing
  `_SimpleServer`/`_EmptyServer` fixtures which already use the safe
  `"127.0.0.1"` value and continue to serve as the acceptance case.
- Name the new test class `TestBindAddressValidation`, grouped with the
  existing `TestListTools`/`TestHealth`-style per-concern test classes in
  this file.

## Alternatives considered
- Testing bind-address validation via a full integration test that actually
  starts `run_http()` in a subprocess and inspects its exit/log output:
  rejected — this file's existing tests are all synchronous unit tests
  against `MCPServer`'s methods directly (`TestHealth`, `TestListTools`);
  a subprocess-based test would be disproportionately heavier than this
  file's established pattern and duplicate what
  `tests/eventbus/test_eventbus_startup.py`'s equivalent-purpose tests
  already establish for the parallel Event Bus case.

## Implementation
### Target file
`tests/mcp_servers/test_mcp_server_base.py`

### Procedure
1. Add `_PublicBoundServer(MCPServer)` fixture class with
   `http_host = "192.168.1.1"`, mirroring `_SimpleServer`'s structure
   (verified 2026-09-04, lines 19-34).
2. Add `TestBindAddressValidation` with:
   - `test_loopback_v4_accepted()` using `_SimpleServer` (`http_host =
     "127.0.0.1"`, already present).
   - `test_loopback_v6_accepted()` using a fixture with `http_host = "::1"`.
   - `test_private_lan_rejected()`, `test_wildcard_rejected()`,
     `test_other_public_rejected()` using `_PublicBoundServer`-style fixtures
     with `192.168.1.1`, `0.0.0.0`, and a public IP respectively.
3. Determine the exact call target for each test (row 2's validation
   function/method, or a mocked `run_http()` invocation) per Assumptions,
   based on row 2's final implementation.

### Method
Direct test addition, following this file's existing per-concern test-class
pattern (`TestHealth`, `TestListTools`, etc.).

### Details
Current fixture pattern (verified 2026-09-04, lines 19-34):
```python
class _SimpleServer(MCPServer):
    server_name = "simple"
    server_version = "1.0.0"
    http_host = "127.0.0.1"
    http_port = 9999
    app_module = "tests.mcp_servers.test_mcp_server_base:app"
    mcp_tools = [...]

    async def dispatch(self, name: str, args: dict) -> DispatchResult:
        ...
```
Illustrative new test (exact call target to be finalized per row 2's
implementation, see Assumptions):
```python
class _PublicBoundServer(MCPServer):
    server_name = "public"
    server_version = "1.0.0"
    http_host = "192.168.1.1"
    http_port = 9999
    app_module = "tests.mcp_servers.test_mcp_server_base:app"
    mcp_tools = []

    async def dispatch(self, name: str, args: dict) -> DispatchResult:
        raise NotImplementedError


class TestBindAddressValidation:
    def test_private_lan_rejected(self) -> None:
        with pytest.raises(ValueError, match="non-loopback address"):
            _PublicBoundServer().run_http()  # or the factored-out validator, per row 2
```

## Compatibility considerations
Coupled to row 2 — must land after it and must match its exact validation
error message/mechanism.

## Security considerations
This file's edits are themselves the regression coverage for row 2's
security fix.

## Rollback considerations
Test-only edit under version control; revert via `git revert` if needed,
together with row 2.

## Validation plan
| Target File/Module | Testing Strategy | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `tests/mcp_servers/test_mcp_server_base.py` | Unit | `uv run pytest tests/mcp_servers/test_mcp_server_base.py -v` | Private-LAN/wildcard/public `http_host` rejected; `127.0.0.1`/`::1` accepted |

## Completion criteria
A new test class confirms `MCPServer`'s bind-address validation rejects
every non-loopback address class and accepts `127.0.0.1`/`::1`.

## Out of scope
`TestListTools`, `TestHealth`, `TestAttachAuthMiddleware`,
`TestTruncateWithMeta`, `TestAuditLog`, `TestAppModuleImportability`.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20260904 | 20260904 | Row 2 inlined the check in `run_http()` (not factored into a separate method) — rejected-host tests call `run_http()` directly (raises before any uvicorn construction); accepted-host tests patch `uvicorn.Server.run` to a no-op (setting `started = True`) to avoid actually binding/blocking, since the validation reaches `uvicorn.Config`/`uvicorn.Server` construction for a valid host |
| 2 | Add or update tests per Validation plan | Completed | 20260904 | 20260904 | This row's target file is itself the test file |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20260904 | 20260904 | ruff clean; 33 passed |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | N/A | — | — | N/A: test-only file |

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
- **Requirement ID**: REQ-005
- **Source issue**: issues/20260902-143334_loopbackonly_enforce_loopback_only_http_remove_external_publication.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260903-091921_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260904-092757
- **Related target files**: tests/mcp_servers/test_mcp_server_base.py
