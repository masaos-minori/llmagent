## Goal

- Regenerate `registry/manifests/eventbus_route_roles.yaml` from the route modules so it holds exactly the 9 registered routes with method, path and role (`REQ-004`, `REQ-005`; `AC-003`).

## Scope
**Release unit**: route-role-source

## Assumptions

- Rows 01 and 04 land in the same commit: the derivation exists and the old constant is gone.

## Design decisions

- `D-03`, `D-04`: the manifest keys become the registered path templates, each with its HTTP method and role.

## Alternatives considered

- Keep the 10-key file and mark the phantoms: rejected - phantom keys are the defect, and no tolerant fallback is permitted.

## Implementation
### Target file
`registry/manifests/eventbus_route_roles.yaml`
### Procedure
1. After rows 01, 03, 04 land, run `uv run python tools/generate_reference_table.py --manifests`.
2. Commit the rewritten file and confirm the four phantom keys (`/ack`, `/dlq/requeue`, `/events`, `/admin/*`) are gone.

### Method
- Generator write only.

### Details
- Committed file today: 10 entries, `sources: [scripts/eventbus/auth.py]`, no `method` field.
- Expected output: 9 entries with `method` and `roles`, matching `EXPECTED_ROUTES` (`tests/eventbus/test_eventbus_route_registry.py:25-35`); `sources` names the seven route modules after row 01.

## Compatibility considerations

- Row 11 asserts parity against the running app, so a stale manifest fails CI.
- `deploy/deploy.sh` syncs `registry/`.

## Security considerations

- The manifest now states which role gates each registered route, derived from the enforcing code rather than from a parallel constant.

## Rollback considerations

- Revert the commit.

## Validation plan

- `uv run python tools/generate_reference_table.py --manifests && git diff --exit-code registry/manifests/` — committed file equals regenerated output (regeneration gate: manifest freshness)
- `uv run pytest tests/eventbus/test_eventbus_route_registry.py -v` — registered routes and manifest entries are identical sets (integration: route parity)

## Completion criteria

- `AC-003`: exactly 9 entries with method, path (including `{event_id}`) and role; no phantom key.

## Out of Scope

- Any route registration or role-enforcement change.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Regenerate and commit | Completed | 20261119-232759 | 20261119-232759 | generator write regenerated with version 2: 9 registered routes with method and derived roles, four phantom keys dropped; asserted by tests/eventbus/test_eventbus_route_registry.py |
| 2 | Run the parity test | Completed | 20261119-232759 | 20261119-232759 | row 11 asserts it regenerated with version 2: 9 registered routes with method and derived roles, four phantom keys dropped; asserted by tests/eventbus/test_eventbus_route_registry.py |

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
- **Requirement ID**: `REQ-004` (eventbus_route_roles entries are derived from the registered FastAPI routes and the require_role dependency of each route function), `REQ-005` (the schema route pattern accepts registered parameterized paths such as /dlq/{event_id}/requeue)
- **Source issue**: issues/20261117-123014_adrchk014_contract-manifest-sources.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261119-181257_adrchk014_contract-manifest-sources.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261119-210556
- **Related target files**: `registry/manifests/eventbus_route_roles.yaml`