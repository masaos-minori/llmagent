## Goal

- Assert that the requeue audit record names the registered route path, so the unregistered `/dlq/requeue` value can never come back (`REQ-007`; `AC-005`).

## Scope
**Release unit**: audit-route-vocabulary

## Assumptions

- Row 06 changes the emitted value in the same commit; this file only moves the assertion.

## Design decisions

- `D-04`, `D-05`: the assertion pins the registered path template rather than a handler-local label.

## Alternatives considered

- Drop the route assertion and assert only `target` and `actor`: rejected - the emitted vocabulary is the contract this row protects.

## Implementation
### Target file
`tests/eventbus/test_eventbus_dlq.py`
### Procedure
1. Update the pinned assertion at line 1301 from `kwargs["route"] == "/dlq/requeue"` to the registered path `/dlq/{event_id}/requeue`.
2. Name the case `T-012` `test_requeue_audit_record_uses_registered_route` (new) so the Plan's Tests section resolves to it.

### Method
- Assertion edit inside the existing requeue audit test; the client call, headers, and fixtures are unchanged.

### Details
- Current assertion at `tests/eventbus/test_eventbus_dlq.py:1301`; the surrounding case asserts one audit call, `target`, and the actor fingerprint.
- Row 19's manifest entry for the same route carries `POST`, `/dlq/{event_id}/requeue`, `OPERATOR`, so log and manifest are asserted against one vocabulary from two directions.

## Compatibility considerations

- Depends on row 06 landing in the same commit.

## Security considerations

- N/A: test-only change.

## Rollback considerations

- N/A: revert the commit together with row 06.

## Validation plan

- `uv run pytest tests/eventbus/test_eventbus_dlq.py -v` — passes against the registered path (unit (T-012): requeue audit vocabulary)

## Completion criteria

- The dlq suite asserts the registered path and no assertion in the file pins a phantom route.

## Out of Scope

- Any other dlq behavior assertion.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Update the pinned route assertion | Completed | 20261119-232759 | 20261119-232759 | one assertion requeue audit assertion pinned to /dlq/{event_id}/requeue (T-012); uv run pytest tests/eventbus/test_eventbus_dlq.py tests/eventbus/test_authz_generation_ttl.py -q green |
| 2 | Run `uv run pytest tests/eventbus/test_eventbus_dlq.py tests/eventbus/test_authz_generation_ttl.py -v` | Completed | 20261119-232759 | 20261119-232759 | Phase 4 acceptance command requeue audit assertion pinned to /dlq/{event_id}/requeue (T-012); uv run pytest tests/eventbus/test_eventbus_dlq.py tests/eventbus/test_authz_generation_ttl.py -q green |

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
- **Requirement ID**: `REQ-007` (audit records, docstrings, and the operator-facing documentation name either a registered route path or an identifier explicitly documented as a non-route internal loop)
- **Source issue**: issues/20261117-123014_adrchk014_contract-manifest-sources.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261119-181257_adrchk014_contract-manifest-sources.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261119-210556
- **Related target files**: `tests/eventbus/test_eventbus_dlq.py`