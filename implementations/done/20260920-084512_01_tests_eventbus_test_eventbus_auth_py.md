# Implementation Procedure: Fix TestPrincipalFieldValidation tests failing on MagicMock auth_token assertion

## Goal

Fix `TestPrincipalFieldValidation` unit tests that trip the fail-closed `auth_token` check via a bare `MagicMock` request, preventing these tests from exercising `_TOKEN_PRINCIPAL_MAP` lookup logic.

## Scope

- **In-Scope**: Update `TestPrincipalFieldValidation` test fixtures to supply a `request` mock whose `app.state.config.auth_token` resolves to a real string
- **Out-of-Scope**: Modifying `scripts/eventbus/auth.py` production code, weakening `get_auth_token()`'s `isinstance(token, str)` assertion, or fixing other failing test classes

## Assumptions

- The fix is purely in test fixtures — no production code changes needed
- A shared local helper function for constructing the corrected `request` mock is acceptable if it avoids repeating the same construction across 4 tests
- `MagicMock(app=MagicMock(state=MagicMock(config=MagicMock(auth_token="test-token"))))` will resolve `request.app.state.config.auth_token` to `"test-token"` without triggering any side effects

## Design decisions

- Add a static helper method inside `TestPrincipalFieldValidation` rather than a module-level fixture — keeps the change scoped to the affected class only
- Default `auth_token = "test-token"` in the helper — sufficient for the fail-closed check; no need to vary per-test since none exercise token-value semantics

## Alternatives considered

- Creating a real `EventBusConfig` instance — rejected as unnecessary complexity for a test-only concern
- Patching `get_auth_token()` in each test — rejected because it would alter what the test exercises (the fail-closed check would be bypassed entirely)

## Implementation

### Target file

`tests/eventbus/test_eventbus_auth.py`

### Procedure

1. Add `_make_request_mock()` helper method inside `TestPrincipalFieldValidation`
2. Replace `MagicMock()` calls in each of the 4 `TestPrincipalFieldValidation` tests with `self._make_request_mock()`

### Method

#### Step 1: Add test fixture helper

Add a `@staticmethod` method `_make_request_mock(auth_token: str = "test-token") -> MagicMock` inside `TestPrincipalFieldValidation`:

```python
    @staticmethod
    def _make_request_mock(auth_token: str = "test-token") -> MagicMock:
        from unittest.mock import MagicMock

        mock = MagicMock()
        mock.app.state.config.auth_token = auth_token
        return mock
```

The helper returns a `MagicMock` where `app.state.config.auth_token` resolves to a real string, satisfying `get_auth_token()`'s `assert isinstance(token, str)` at `scripts/eventbus/auth.py:159`.

#### Step 2: Update test fixtures

Replace `MagicMock()` with `self._make_request_mock()` in the `resolve_principal()` call argument in each of the 4 tests:

- `test_publisher_token_grants_only_publisher_role` (~line 705)
- `test_admin_token_grants_all_roles` (~line 734)
- `test_shared_token_grants_all_roles_for_backward_compat` (~line 764)
- `test_per_role_token_has_no_consumer_restriction` (~line 796)

Each test currently passes `MagicMock()` as the `request` parameter. Change to `self._make_request_mock()`.

### Details

**Before (each test):**
```python
principal = await resolve_principal(
    MagicMock(),
    credentials=MagicMock(credentials=token),
)
```

**After:**
```python
principal = await resolve_principal(
    self._make_request_mock(),
    credentials=MagicMock(credentials=token),
)
```

**Root cause:** `resolve_principal()` calls `get_auth_token(config)` at `scripts/eventbus/auth.py:179`, where `config = request.app.state.config`. When `request` is a bare `MagicMock()`, `request.app.state.config` auto-resolves to another `MagicMock`, and `config.auth_token` is itself a truthy `MagicMock` (not `None`), so it passes the `if not token` check but fails `assert isinstance(token, str)` with `AssertionError: Expected str, got MagicMock`.

## Compatibility considerations

- No impact on production code — only test fixtures changed
- Python 3.14 compatibility verified during adversarial verification (MagicMock attribute resolution order confirmed working)

## Security considerations

- No security implications — the `auth_token` value `"test-token"` is a test constant, not a real credential
- No raw tokens leaked into audit records (pre-existing behavior preserved)

## Rollback considerations

- Simple revert: remove `_make_request_mock()` method and restore `MagicMock()` in each test
- No downstream dependencies — the helper is private to `TestPrincipalFieldValidation`

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| tests/eventbus/test_eventbus_auth.py::TestPrincipalFieldValidation | Unit — verify all 4 tests pass after fixture fix | `uv run pytest tests/eventbus/test_eventbus_auth.py::TestPrincipalFieldValidation -q` | 0 failures |
| tests/eventbus/test_eventbus_auth.py | Integration — verify no regressions in other tests | `uv run pytest tests/eventbus/test_eventbus_auth.py -q` | 0 new failures |

## Completion criteria

- All 4 `TestPrincipalFieldValidation` tests pass individually
- Each affected test still asserts the same `Principal` field values it did before (roles, `allowed_consumer_ids`, `allowed_topics`)
- No new failures introduced in other `Test*Auth` classes within `tests/eventbus/test_eventbus_auth.py`

## Out of scope

- Fixing pre-existing failures in other test classes (`TestRequireConsumerIdentityTopicSemantics`, `TestDlqListAuth`, `TestReplayAuth`) — these are unrelated to the `auth_token` MagicMock issue
- Modifying `scripts/eventbus/auth.py` production code
- Adding new test cases beyond the existing 4

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | N/A: test-fixture fix, no docs impact |

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
- **Requirement ID**: REQ-001, REQ-002
- **Source issue**: issues/20260919-164247_ebauth01_eventbus-resolve_principal-unit-tests-pass-bare-magicmock-request,-tripping-fail-closed-auth_token-check.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/done/20260920-082541_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260920-084512
- **Related target files**: tests/eventbus/test_eventbus_auth.py
