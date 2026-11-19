## Goal
- Make the EventBus application use the renamed request-ID middleware function (REQ-003: unambiguous name) with no change in behavior.

## Scope
**Release unit**: eventbus-api-surface

- In scope: the import entry and the single call in `scripts/eventbus/app.py`.
- Depends on the seq 01 document, which declares the new name; both land in one release unit.

## Assumptions
- `app.py` imports the old function once and calls it once on the module-level app (verified in Step 3a).
- The inline `noqa` justification comments on the import entries are not part of this change and stay as they are.

## Design decisions
- Change only the name at the two sites; keep the call position directly after the app is created, so middleware order is unchanged.

## Alternatives considered
N/A: a name-only change at two sites.

## Implementation
### Target file
`scripts/eventbus/app.py`

### Procedure
1. In the `from eventbus.auth import (...)` block, replace the entry `attach_auth_middleware` with `attach_request_id_middleware` (new).
2. Replace the call `attach_auth_middleware(app)` after `app = FastAPI(lifespan=lifespan)` with `attach_request_id_middleware(app)` (new).

### Method
- Keep the import entries in alphabetical order; the renamed entry stays first.
- Do not change the other entries, their `noqa` comments, or the router registration order.

### Details
- Apply this document together with the seq 01 document; applied alone, the import fails.
- Verify with `rg "attach_auth_middleware" scripts/eventbus`, which MUST find nothing once seq 01 and this document are applied.

## Compatibility considerations
N/A: internal import and call; the HTTP surface is unchanged.

## Security considerations
N/A: the middleware only injects X-Request-Id; authentication stays in the route dependencies.

## Rollback considerations
- Revert together with the seq 01 document's commit.

## Validation plan
- `uv run ruff format --check scripts/eventbus/app.py` and `uv run ruff check scripts/eventbus/app.py`.
- `uv run mypy --no-namespace-packages scripts/ tests/eventbus tools`.
- `uv run pytest tests/eventbus/test_eventbus_app_isolation.py tests/eventbus/test_eventbus_startup.py -q`.

## Completion criteria
- `app.py` references only `attach_request_id_middleware` (new) and the application starts with the X-Request-Id header on every response.

## Out of Scope
- Any other change in `app.py`, including lifespan, task, and noqa-comment cleanup.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Rename the import entry and the call | Completed | 20261119-100101 | 20261119-100153 | Step 2 stale check clean; app.py clean at baseline Changed: scripts/eventbus/app.py |
| 2 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261119-100153 | 20261119-102738 | ruff, mypy, lint-imports, bandit pass; 76 targeted tests pass; full suite once at end of unit End of unit: full suite 12898 passed 7 skipped (not integration/production_paths_allowed/repo_scan); diff-cover 100%; ADR-cited tests 52 passed; validation gates pass |

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
- **Requirement ID**: `REQ-003` (rename the request-ID middleware)
- **Source issue**: issues/20261117-123002_adrchk002_eventbus-authz-model.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261119-092411_adrchk002_eventbus-authz-model.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261119-094420
- **Related target files**: `scripts/eventbus/app.py`