## Goal
Make the existing health test send a token that has the Monitoring role, since the health route now enforces it (REQ-007 of the Plan: additional target discovered by the full EventBus suite).

## Scope
- Change the one health test in the subscribe test module; leave the client fixture and every other test unchanged.

## Assumptions
- The module's configuration defines a shared token that grants every role; the client fixture authenticates with the consumer-only token, which is why the health call returns 403 after the route change.

## Design decisions
- Pass the shared token as a per-request header in that test rather than changing the fixture, so no other test's authentication changes.

## Alternatives considered
- Add a monitoring token to the fixture configuration: rejected; it widens the change and is unnecessary for one call.

## Implementation
### Target file
tests/eventbus/test_eventbus_subscribe.py

### Procedure
1. Confirm the test still calls the health route without a header override.
2. Add an Authorization header carrying the module's shared token to that call.
3. Run the test and the module.

### Method
A one-line edit of the request call.

### Details
The call becomes a health request with a per-request Authorization header that uses the shared token already present in the module's configuration.

## Compatibility considerations
- Test only; no production behavior change.

## Security considerations
- Fake test tokens only.

## Rollback considerations
- Revert the commit.

## Validation plan
- `uv run ruff format` and `ruff check` on the file; `uv run pytest tests/eventbus/test_eventbus_subscribe.py -q`.

## Completion criteria
- The health test passes with a Monitoring-capable token and the rest of the module is unaffected (REQ-007).

## Out of scope
- The four timing-out tests in the subscribe-transition module, which also time out without the route change (pre-existing).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Send the shared token in the health test | Completed | 20261008-114513 | 20261008-114513 |  |
| 2 | Run the test module | Completed | 20261008-114513 | 20261008-114513 |  |

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
- **Requirement ID**: REQ-007 (health test token)
- **Source issue**: issues/20261008-110449_ebroutes01_add-role-dependencies-to-the-eventbus-health-and-publish-routes.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261008-111323_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261008-111709
- **Related target files**: tests/eventbus/test_eventbus_subscribe.py