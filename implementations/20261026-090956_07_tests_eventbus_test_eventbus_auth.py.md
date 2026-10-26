## Goal

Assert in `tests/eventbus/test_eventbus_auth.py` that `_populate_token_maps()` publishes
atomically (seq 02) and that a failed rebuild leaves the previous generation's principals
intact and in force.

## Scope

- Modify only `tests/eventbus/test_eventbus_auth.py`.

## Assumptions

- `_populate_token_maps(config)` builds into a fresh dict then publishes via one assignment;
  raising during build leaves the prior map unchanged.

## Design decisions

- Add two tests: (a) atomic publish (no empty-map window observed), (b) failed rebuild
  preserves the previous generation.

## Alternatives considered

- Extending an existing test vs. a new test function: new function keeps concerns separate.

## Implementation

### Target file

`tests/eventbus/test_eventbus_auth.py`

### Procedure

1. Add a test that calling `_populate_token_maps()` with a new config results in a single
   atomic swap — readers never observe an empty map mid-publish (simulate concurrency if the
   harness allows, else assert the map is fully populated after the call).
2. Add a test that forces `_populate_token_maps()` to raise after building (e.g. inject a
   config that triggers the `consumer_token` configured but `consumer_authorization` missing
   raise at auth.py:137-141) and assert the previous generation's principals remain intact
   and in force (REQ-001; Acceptance 1, 5).
3. Ensure principals are built via `_populate_token_maps()` (not direct map mutation).

### Method

Add test functions; convert any direct-map setup to the production path.

### Details

- For the failure-injection test, drive the raise via config rather than patching, where
  possible, to exercise the real code path.

## Compatibility considerations

- Preserves existing auth unit tests; additive only.

## Security considerations

- Failed-rebuild test confirms no partial-population window (supports REQ-001).

## Rollback considerations

- Revert the commit.

## Validation plan

- `uv run pytest tests/eventbus/test_eventbus_auth.py` — atomic publish + failed-rebuild
  assertions pass.
- `uv run pytest tests/eventbus/` — full suite passes.

## Completion criteria

- Atomic publish and failed-rebuild-preserved-generation are both asserted.

## Out of Scope

- Other test files (seq 08-10).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | This row IS the test update |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation if in scope | Pending | — | — | N/A |

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
- **Requirement ID**: `REQ-001`
- **Source issue**: `issues/20261023-154326_eventbus006_runtime-authorization-update-consistency.md`
- **Requirement requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261025-122243_eventbus006_runtime-authorization-update-consistency.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261026-090956
- **Related target files**: `tests/eventbus/test_eventbus_auth.py`
