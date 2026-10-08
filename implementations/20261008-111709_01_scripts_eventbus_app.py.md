## Goal
Make the production EventBus application require the Publisher role on the publish route and the Monitoring role on the health route (REQ-001 of the Plan: route dependencies).

## Scope
- Change only the signatures of the two route handlers in the application module; keep every other route and all handler bodies unchanged.

## Assumptions
- The role-dependency helper, the principal type, and the role enum are already imported in this module.
- The user confirmed no external caller calls these routes without a token, and that deployment is not part of this work.

## Design decisions
- Declare the dependency as a parameter with the dependency default, the same style the other routes use.

## Alternatives considered
- A router-level or global dependency: rejected; the other routes declare dependencies per route and the issue asks for matching style.

## Implementation
### Target file
scripts/eventbus/app.py

### Procedure
1. Re-check that the health and publish handlers still lack a dependency parameter.
2. Add the Monitoring dependency to the health handler and the Publisher dependency to the publish handler.
3. Run format, lint, type, import-boundary, and security checks.

### Method
Two signature edits using the exact route-declaration style already present for the replay and dlq routes.

### Details
Health handler gains a private dependency parameter of the principal type defaulting to the role dependency for the Monitoring role; the publish handler gains the same with the Publisher role. Handler bodies still delegate to the existing route functions and do not read the new parameter.

## Compatibility considerations
- The new parameter is underscore-prefixed and unused in the body, matching the existing routes. Callers must now present a token with the matching role (the shared token also works).

## Security considerations
- Closes unauthenticated access to publish and health; no secrets handled.

## Rollback considerations
- Revert the commit; no data or schema change.

## Validation plan
- `uv run ruff format scripts/eventbus/app.py`, `uv run ruff check scripts/eventbus/app.py`, `uv run mypy --no-namespace-packages scripts/`, `PYTHONPATH=scripts uv run lint-imports` (a pre-existing unrelated violation is expected), `uv run bandit scripts/eventbus/app.py`.
- `uv run pytest tests/eventbus -q` after the test procedure is applied.

## Completion criteria
- The publish route has the Publisher dependency and the health route the Monitoring dependency; no other declaration or handler body changed (REQ-001).

## Out of scope
- Token model, other routes, handler logic, deployment.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add the dependencies to the two handlers | Completed | 20261008-114513 | 20261008-114513 |  |
| 2 | Run format, lint, type, boundary, security checks | Completed | 20261008-114513 | 20261008-114513 |  |

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
- **Requirement ID**: REQ-001 (route dependencies)
- **Source issue**: issues/20261008-110449_ebroutes01_add-role-dependencies-to-the-eventbus-health-and-publish-routes.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261008-111323_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261008-111709
- **Related target files**: scripts/eventbus/app.py