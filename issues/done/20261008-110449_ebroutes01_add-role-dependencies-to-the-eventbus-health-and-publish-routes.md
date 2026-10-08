# Add role dependencies to the EventBus health and publish routes

## Priority
High

## Summary
Make the production EventBus application reject unauthenticated and wrong-role requests to the health and publish routes, as the ADR and the health reference already require, and test the behavior against the production application.

## Background
Found while verifying ADR-013 (tracked as EVENTBUS-016 in the Known Issue ledger). Route introspection of the production application shows that every route except the health and publish routes carries a role dependency; these two carry none, and their handlers call no authentication helper.

## Problem
- Any local process that can reach the loopback port can publish events and read health state without a token, which violates ADR-013 INV-01 and the documented Monitoring-role requirement for the health route.
- The existing authentication tests build their own fixture application and add the role dependencies themselves, so they pass without exercising the production wiring.

## Reason for Change
Authentication is the security boundary of the EventBus; the two routes with the largest side effect (publishing) and an operational disclosure (health) are the ones left open. The documentation now records this as a Known Deviation, which should not outlive a small, well-bounded fix.

## Implementation Intent
- Attach the Publisher role dependency to the publish route and the Monitoring role dependency to the health route in the application's route registration, matching how the other routes are declared.
- Keep handler logic unchanged; keep the role map and token model unchanged.
- Replace or supplement the fixture-based tests with tests that use the production application object, so a missing dependency fails a test.

## Target Files or Areas
- `scripts/eventbus/app.py`
- `tests/eventbus/test_eventbus_auth.py`
- Known Issue ledger entry EVENTBUS-016 and the ADR-013 Known Deviations line (removed when the fix lands)

## Required Changes
- Add the two role dependencies to the route declarations.
- Add tests against the production application: no token returns 401, a wrong-role token returns 403, and the correct per-role token succeeds, for both routes.
- Check whether the health endpoint is used by internal callers (for example startup health probes) that would now need a Monitoring-capable token, and update their configuration if so.

## Constraints
- A health probe that currently runs without a token (for example from the agent or a deployment script) must keep working, which may require supplying the monitoring or shared token to it; confirm before changing the route.
- No change to token kinds, role names, or the other routes.

## Acceptance Criteria
- Requests without a token to the health and publish routes return 401 against the production application object.
- A token without the required role returns 403 on each route.
- The per-role token (and the shared token) succeed.
- All existing EventBus tests still pass.

## Testing Expectations
Unit/integration tests using the production application, plus the full EventBus test suite, ruff, mypy, and the import-boundary check per `rules/toolchain.md`.

## Documentation Impact
Yes: remove EVENTBUS-016 from the ledger and from the ADR-013 Known Deviations, and update the INV-01 Verification note once the production-wiring tests exist. Check the EventBus health reference for any statement that changes (for example how health probes authenticate).

## Out of Scope
- Redesigning the token model or removing the shared `auth_token` requirement (EVENTBUS-015).
- Consumer-identity allowlist behavior (EVENTBUS-008).

## Dependencies
- Related to the ADR-013 correction work, which registers EVENTBUS-016.

## Unresolved Questions
- Which internal callers, if any, call the health route without a token today (unknown; must be checked before the change).
- Whether any deployment places something in front of the service that already enforces authentication (unknown; the repository shows none).

## AI Implementation Instruction
Change only the two route declarations and the tests. Do not alter handler logic or the token model. Before editing, find every caller of the health route and report any that would break. Stop and ask if a caller needs a configuration decision.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/done/20261008-103440_plan.md
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261008-110449
- **Related target files**: `scripts/eventbus/app.py`, `tests/eventbus/test_eventbus_auth.py`
