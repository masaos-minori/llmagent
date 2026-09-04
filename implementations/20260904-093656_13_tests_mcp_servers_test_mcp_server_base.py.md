## Goal
Confirm existing `TestAttachAuthMiddleware` Bearer-token tests (401/200
behavior) still pass unaffected by this Plan's changes, and add a
regression test confirming empty-token accept-all is not exercised by any
change this Plan introduces.

## Scope
- **In-Scope**: `TestAttachAuthMiddleware` (verified 2026-09-04, lines
  107-152, containing `test_no_token_allows_any_request`,
  `test_no_token_response_contains_request_id`, `test_correct_token_returns_200`,
  `test_missing_token_returns_401`, `test_wrong_token_returns_401`,
  `test_request_id_present_on_auth_failure`,
  `test_request_id_uuid4_format_on_success`, `test_each_request_gets_unique_id`).
- **Out-of-Scope**: `TestListTools`, `TestHealth`, `TestTruncateWithMeta`,
  `TestAuditLog`, `TestAppModuleImportability` — confirmed by direct read to
  be unrelated to Bearer-token authentication; also out of scope is
  `plans/done/20260903-091921_plan.md`'s own row 5 for this same file
  (bind-address-validation tests, a different concern, different test
  class).

## Assumptions
- **Corrected 2026-09-04** (`plan-to-implementation-procedure` Step 2/3
  revalidation): this Plan's original row for REQ-007's Bearer-token test
  coverage, `tests/mcp_servers/mdq/test_auth.py`, was found (by direct read)
  to contain zero `Bearer`/`auth_token`/`Authorization`-header references —
  its `TestAuthorizePathAllowlist`/`TestAuthorizePathExceptionHandling`
  classes test filesystem path-allowlist authorization for the `mdq`
  server, an unrelated security concern. The actual Bearer-token test
  coverage for `attach_auth_middleware()`/`_is_authorized()` (row 4's
  target) lives in this file's `TestAttachAuthMiddleware` class. This row
  replaces the stale `tests/mdq/test_auth.py` row.
- Row 4's edit to `scripts/mcp_servers/server.py` is docstring-only (REQ-003
  is confirm-only, no logic change) — this row's existing
  `TestAttachAuthMiddleware` tests require no modification to keep passing;
  this row's own work is limited to adding one new regression test.
- This file is also a target of `plans/done/20260903-091921_plan.md`'s own
  row 5 (bind-address-validation tests, a new `TestBindAddressValidation`
  class) — both Plans add independent new test classes/tests to this file;
  no overlap or conflict, but both should land before a final full-suite
  run of this file.

## Design decisions
- Add one new test, `test_empty_token_accept_all_is_not_a_supported_mode()`
  (or similar), documenting via an inline comment that this behavior is
  retained at the middleware level (per row 4's docstring update) but is
  unreachable in a real Agent-managed startup because
  `scripts/agent/startup_validation.py` (row 3) rejects any configuration
  with an empty token before `attach_auth_middleware()` would ever be
  called with one — this test exercises the same accept-all code path as
  the existing `test_no_token_allows_any_request()` (confirming it still
  works, since REQ-003 does not remove it) while documenting *why* it is
  safe for this file's own unit test to exercise a state real startup
  never reaches.

## Alternatives considered
- Modifying `test_no_token_allows_any_request()` itself to add this
  clarifying comment: rejected — that test already exists and passes;
  adding a new, separately-named test keeps the distinction between
  "existing behavior-lock test" and "new regression test documenting this
  Plan's reasoning" clear for future readers.

## Implementation
### Target file
`tests/mcp_servers/test_mcp_server_base.py`

### Procedure
1. Re-run `uv run pytest tests/mcp_servers/test_mcp_server_base.py::TestAttachAuthMiddleware -v`
   to confirm all 8 existing tests pass unmodified (expected, since row 4 is
   docstring-only).
2. Add `test_empty_token_accept_all_is_not_a_supported_mode()` per Design
   decisions.

### Method
Direct test addition within `TestAttachAuthMiddleware`.

### Details
Existing pattern to mirror (verified 2026-09-04, representative structure
from `TestAttachAuthMiddleware`, exact bodies not fully re-read in this
document's investigation — re-read at execution time via
`sed -n '107,152p' tests/mcp_servers/test_mcp_server_base.py`):
```python
class TestAttachAuthMiddleware:
    def test_no_token_allows_any_request(self) -> None:
        ...

    def test_correct_token_returns_200(self) -> None:
        ...

    def test_missing_token_returns_401(self) -> None:
        ...
```
New test (illustrative; exact `_make_test_app()`-style fixture usage to be
confirmed against this class's existing helper at execution time):
```python
class TestAttachAuthMiddleware:
    ...

    def test_empty_token_accept_all_is_not_a_supported_mode(self) -> None:
        """Empty-token accept-all (test_no_token_allows_any_request) is
        retained at this middleware level for unit testability, but is
        unreachable in a real Agent-managed startup: startup_validation.py
        rejects any MCP server configuration with an empty auth_token
        before attach_auth_middleware() would ever run with one."""
        client = _make_test_app(token="")
        response = client.get("/ping")
        assert response.status_code == 200
```

## Compatibility considerations
Coordinate with `plans/done/20260903-091921_plan.md`'s own row 5 for this
same file (independent new test class, no overlap).

## Security considerations
This row's new test documents (does not change) the interaction between
this file's middleware-level accept-all behavior and row 3's startup-time
enforcement.

## Rollback considerations
Single-test addition under version control; revert via `git revert` if
needed.

## Validation plan
| Target File/Module | Testing Strategy | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `tests/mcp_servers/test_mcp_server_base.py` | Unit | `uv run pytest tests/mcp_servers/test_mcp_server_base.py -v` | All existing `TestAttachAuthMiddleware` tests pass unchanged; new test documents the empty-token-accept-all/startup-rejection relationship |

## Completion criteria
`TestAttachAuthMiddleware`'s existing 8 tests pass unmodified; a new test
documents the empty-token accept-all behavior's relationship to row 3's
startup-time rejection.

## Out of scope
`TestListTools`, `TestHealth`, `TestTruncateWithMeta`, `TestAuditLog`,
`TestAppModuleImportability`, and `plans/done/20260903-091921_plan.md`'s own
`TestBindAddressValidation` addition to this file.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | Confirm existing tests pass unmodified (row 4 is docstring-only) |
| 2 | Add or update tests per Validation plan | Pending | — | — | This row's target file is itself the test file |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
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
- **Requirement ID**: REQ-007
- **Source issue**: issues/20260902-143335_mcpauth_preserve_mandatory_mcp_authentication_under_loopback.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260903-092407_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260904-093656
- **Related target files**: tests/mcp_servers/test_mcp_server_base.py
