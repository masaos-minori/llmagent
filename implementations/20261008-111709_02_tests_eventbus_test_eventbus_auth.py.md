## Goal
Add tests that exercise the production application's wiring for the publish and health routes, and a guard that every API route has a role dependency (REQ-002, REQ-003 of the Plan).

## Scope
- Add one new test class to the EventBus auth test module using the shared client helper; do not change existing tests.

## Assumptions
- The shared helper builds a client for the production app with a default shared-token header; per-role principals can be added to the principal map for the duration of a test.

## Design decisions
- Use the production app object, not the local fixture app, so a missing dependency fails a test.
- Add per-role principals through monkeypatching the token map so the global map is restored after each test.

## Alternatives considered
- Editing the local fixture app: rejected; it is the reason the gap went unnoticed.

## Implementation
### Target file
tests/eventbus/test_eventbus_auth.py

### Procedure
1. Read the helper and the existing test module header to match imports and style.
2. Append a class with: a guard test enumerating the production app's API routes and asserting each has the role-check dependency; and for each of health and publish, tests for no token (401), a wrong-role token (403), the matching per-role token (200), and the shared token (200).
3. Run the new tests, then the EventBus suite, then the full suite once.

### Method
Use the shared client helper, remove the default authorization header for the no-token cases, register per-role principals with monkeypatched dictionary items, and call the client cleanup in a fixture teardown.

### Details
Guard: iterate the production app's routes of the API-route type and inspect the dependency tree for the role-check callable (its qualified name contains the role-check marker). Behavior: use a valid event envelope (same shape as in the publish tests) for the publish success cases; health success asserts a 200 or the service's documented degraded status code is not 401/403.

## Compatibility considerations
- No production behavior change in this file; tests rely only on public app routes and the principal map.

## Security considerations
- Tests use fake tokens only.

## Rollback considerations
- Revert the commit.

## Validation plan
- `uv run ruff format` and `ruff check` on the file, `uv run mypy` if the file is in scope, `uv run pytest tests/eventbus/test_eventbus_auth.py -q`, `uv run pytest tests/eventbus -q`, then the full suite once.

## Completion criteria
- New tests fail before the route change and pass after; the whole EventBus suite and the full suite pass (REQ-002, REQ-003).

## Out of scope
- Changes to other test files unless an additional target discovery is reported (Plan UNK-02).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add the guard and production-wiring tests | Completed | 20261008-114513 | 20261008-114513 |  |
| 2 | Run auth tests, EventBus suite, and the full suite | Completed | 20261008-114513 | 20261008-114513 |  |

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
- **Requirement ID**: REQ-002 (production-wiring tests), REQ-003 (suite still passes)
- **Source issue**: issues/20261008-110449_ebroutes01_add-role-dependencies-to-the-eventbus-health-and-publish-routes.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261008-111323_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261008-111709
- **Related target files**: tests/eventbus/test_eventbus_auth.py