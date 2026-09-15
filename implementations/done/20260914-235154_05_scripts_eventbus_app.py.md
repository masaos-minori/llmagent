## Goal

Understand how config is loaded and token maps are populated at startup.

## Scope

- `scripts/eventbus/app.py`: Read-only reference. Document the startup wiring between config loading, token map population, and middleware attachment. No modifications needed.

## Assumptions

- A: The plan specifies this file as read-only — no changes are expected.

## Design decisions

- **No modifications**: This file is listed as read-only in the plan. Its purpose is to provide context for understanding how config and auth interact at startup.

## Alternatives considered

- None — this file is explicitly read-only per the plan.

## Implementation

### Target file

`scripts/eventbus/app.py`

### Procedure

No implementation steps. This file is read-only reference only.

### Method

**Startup flow (lifespan function):**

1. `load_config(get_config_path())` — loads and validates config (Phase 1 + Phase 2 validation)
2. `open_db(app.state.config.db_path)` — opens database connection
3. `_populate_token_maps(app.state.config)` — populates `_TOKEN_ROLE_MAP` from config tokens
4. `EventBroker(cfg)` — creates event broker instance
5. `attach_auth_middleware(app)` — registers auth middleware on FastAPI app

**Key interactions:**

- `app.state.config` is set before `_populate_token_maps()` is called, so the function can access all config fields including `admin_token`.
- `attach_auth_middleware()` is called after the lifespan sets up the app, which is required because Starlette freezes the middleware stack on first ASGI call.
- The `Role` enum from auth.py is used by route handlers via `Depends(require_role(Role.X))`.

## Compatibility considerations

N/A — no modifications.

## Security considerations

N/A — no modifications.

## Rollback considerations

N/A — no modifications.

## Validation plan

N/A — no modifications.

## Completion criteria

N/A — no modifications.

## Out of scope

- Modifying this file — it is read-only reference only.
- Implementing `/admin/*` route handlers — future work.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20260915-162407 | 20260915-162407 |  |
| 2 | Add or update tests per Validation plan | Completed | 20260915-162407 | 20260915-162407 |  |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20260915-162407 | 20260915-162407 |  |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20260915-162407 | 20260915-162407 |  |

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
- **Requirement ID**: REQ-004, REQ-005
- **Source issue**: issues/20260914-102535_eventbus09_config-validation-role-token-policy.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260914-175822_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260914-235154
- **Related target files**: scripts/eventbus/app.py