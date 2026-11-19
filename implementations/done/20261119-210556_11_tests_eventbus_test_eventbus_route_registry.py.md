## Goal

- Add the registered-route versus committed-manifest parity test, so a route that is added, renamed, or un-gated fails CI until the manifest is regenerated (`REQ-006`; `AC-004`).

## Scope
**Release unit**: route-role-source

## Assumptions

- This file already locks the registered surface through `EXPECTED_ROUTES` (lines 25-35) and reads `app.routes`, so the new case compares that surface to the manifest.

## Design decisions

- Compare sets of `(method, path, role)` rather than counts, so a phantom key and a missing role dependency fail in the same way.
- Read the committed manifest with `tools._contract_manifests.load_manifest`, the same loader the generator's drift check uses.

## Alternatives considered

- Assert parity only inside `tests/tools/test_generate_reference_table.py`: rejected - the fact is a property of the running app, and this file already builds the production app.

## Implementation
### Target file
`tests/eventbus/test_eventbus_route_registry.py`
### Procedure
1. Add the class `TestRouteManifestParity` (new) with case `T-007` `test_registered_routes_match_manifest_entries` (new): collect `(method, path)` from the app's `APIRoute` objects and compare the set with the entries of `registry/manifests/eventbus_route_roles.yaml`, failing on a difference in either direction.
2. Add the case `T-008` `test_manifest_role_matches_require_role_dependency` (new): for each registered route, compare the manifest `roles` entry with the `Role` value in that route function's `Depends(require_role(Role.X))` dependency.
3. Compare that set with the entries of `registry/manifests/eventbus_route_roles.yaml` and fail when the two differ in either direction.
4. Keep `EXPECTED_ROUTES` as the registered-surface lock and assert the manifest holds exactly those 9 routes with their method and role.

### Method
- One new test case plus its helper for reading route dependencies; the existing authorization cases in this file stay unchanged.

### Details
- Current file: 9 registered routes are locked at lines 25-35; no manifest comparison exists today.
- After row 19 the manifest holds 9 entries with `method`; the four phantom keys are gone.

## Compatibility considerations

- Depends on rows 01, 04, 19 landing in the same commit; run order is Phase 3 then Phase 6.

## Security considerations

- N/A: the test reads the route table and the manifest, not any credential.

## Rollback considerations

- N/A: revert the commit.

## Validation plan

- `uv run pytest tests/eventbus/test_eventbus_route_registry.py -v` — passes; a deliberate phantom entry makes it fail (integration: route parity)

## Completion criteria

- `AC-004`: the parity test fails when the registered routes and the committed manifest diverge.

## Out of Scope

- Any change to authorization behavior or route registration.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add the parity test case | Completed | 20261119-232759 | 20261119-232759 | one new case TestRouteManifestParity added (T-007, T-008): 9 registered routes, roles and methods match registry/manifests/eventbus_route_roles.yaml; 9 passed with test_eventbus_auth.py |
| 2 | Run `uv run pytest tests/eventbus/test_eventbus_route_registry.py tests/eventbus/test_eventbus_auth.py -v` | Completed | 20261119-232759 | 20261119-232759 | Phase 3 acceptance command TestRouteManifestParity added (T-007, T-008): 9 registered routes, roles and methods match registry/manifests/eventbus_route_roles.yaml; 9 passed with test_eventbus_auth.py |

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
- **Requirement ID**: `REQ-006` (a test asserts that every registered EventBus route (method, path, role) matches the committed manifest, and fails when the two diverge)
- **Source issue**: issues/20261117-123014_adrchk014_contract-manifest-sources.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261119-181257_adrchk014_contract-manifest-sources.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261119-210556
- **Related target files**: `tests/eventbus/test_eventbus_route_registry.py`