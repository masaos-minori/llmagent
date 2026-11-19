## Goal

- Emit the documented non-route identifier `ttl_sweep` from the authorization TTL sweep instead of the route-shaped `/ttl_sweep` (`REQ-007`; `AC-005`).

## Scope
**Release unit**: audit-route-vocabulary

## Assumptions

- UNK-04 plan default: the internal-phase identifiers are `ttl_sweep` and `startup`, written without a leading slash so they cannot be mistaken for a path.
- Row 13 updates the assertion at `tests/eventbus/test_authz_generation_ttl.py:148`; row 09 states the vocabulary in the audit docstring.

## Design decisions

- `D-05`: an internal maintenance loop emits a non-path identifier, and that vocabulary is documented once in `scripts/eventbus/audit.py` and in the EventBus operations doc (row 14).

## Alternatives considered

- Keep `/ttl_sweep` and document it as an internal pseudo-route: rejected by the UNK-04 plan default - a slash-prefixed value invites a route-parity check that it can never pass.

## Implementation
### Target file
`scripts/eventbus/authz_ttl.py`
### Procedure
1. Change `route="/ttl_sweep"` (line 112) to `route="ttl_sweep"`.

### Method
- One keyword argument in the `log_authorization_change` call; generation-transition fields are unchanged.

### Details
- No `@router` decorator defines `/ttl_sweep` anywhere in `scripts/eventbus/`, which is why the value can never match a manifest entry.
- `tests/eventbus/test_authz_generation_ttl.py:148` and `:306` are the two assertions that read this vocabulary.

## Compatibility considerations

- Row 13 lands in the same commit; row 14 records the vocabulary for operators.

## Security considerations

- N/A: no credential value changes; the record still carries only counts and generation hashes.

## Rollback considerations

- N/A: revert the commit together with row 13's assertion.

## Validation plan

- `uv run pytest tests/eventbus/test_authz_generation_ttl.py -v` — the record carries `ttl_sweep` (unit (T-013): sweep audit record)
- `rg "/ttl_sweep" scripts/eventbus/ tests/eventbus/ docs/24_eventbus/` — no match outside archived work items (static: no route-shaped internal id)

## Completion criteria

- The sweep record carries `ttl_sweep`, and the docstring and operator doc describe it as non-route.

## Out of Scope

- Any change to the sweep interval, grant removal, or generation semantics.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Change the emitted identifier | Completed | 20261119-232759 | 20261119-232759 | one keyword argument emitted sweep identifier is now ttl_sweep; uv run pytest tests/eventbus/test_authz_generation_ttl.py -q 15 passed |
| 2 | Run `uv run pytest tests/eventbus/test_authz_generation_ttl.py -v` | Completed | 20261119-232759 | 20261119-232759 | with row 13 emitted sweep identifier is now ttl_sweep; uv run pytest tests/eventbus/test_authz_generation_ttl.py -q 15 passed |

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
- **Related target files**: `scripts/eventbus/authz_ttl.py`