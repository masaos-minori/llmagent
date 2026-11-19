## Goal

- Emit the documented non-route identifier `startup` for the restart-baseline audit record instead of the route-shaped `/startup` (`REQ-007`; `AC-005`).

## Scope
**Release unit**: audit-route-vocabulary

## Assumptions

- UNK-04 plan default: `startup` is the non-route identifier for the startup baseline phase.
- Row 14 states this identifier in the operator-facing doc line that currently records `route="/startup"`.

## Design decisions

- `D-05`: a startup phase is not an HTTP route, so it emits a non-path identifier.

## Alternatives considered

- Register a `/startup` route so the value is a registered path: rejected - the record is written during application startup, before any request, and a route would add surface for no benefit.

## Implementation
### Target file
`scripts/eventbus/app.py`
### Procedure
1. Change `route="/startup"` (line 81) to `route="startup"`.

### Method
- One keyword argument in the `log_privileged_action` call inside the startup baseline block; the detail payload is unchanged.

### Details
- `app.py:235-241` registers only the seven routers; no `/startup` route exists.
- The assertion that pins the current value is in `tests/eventbus/test_authz_generation_ttl.py:306` (row 13).

## Compatibility considerations

- Row 13 updates the startup-record assertion and row 14 the operator doc, in the same commit.

## Security considerations

- N/A: the baseline record is a marker, not a security event, and carries an opaque hash.

## Rollback considerations

- N/A: revert the commit together with rows 13 and 14.

## Validation plan

- `uv run pytest tests/eventbus/test_authz_generation_ttl.py -v` — the record carries `startup` (unit: startup baseline record)
- `rg "/startup" scripts/eventbus/ docs/24_eventbus/` — no match outside archived work items (static: no phantom route)

## Completion criteria

- The baseline record carries `startup` and the operator doc names the same identifier.

## Out of Scope

- Any change to baseline generation or startup ordering.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Change the emitted identifier | Completed | 20261119-232759 | 20261119-232759 | one keyword argument emitted startup identifier is now startup; TTL and startup assertions green with rows 13, 14 |
| 2 | Run the TTL/startup assertions | Completed | 20261119-232759 | 20261119-232759 | with rows 13, 14 emitted startup identifier is now startup; TTL and startup assertions green with rows 13, 14 |

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
- **Related target files**: `scripts/eventbus/app.py`