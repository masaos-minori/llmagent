## Goal

- Assert the internal-phase audit identifiers `ttl_sweep` and `startup`, so the sweep and startup records cannot emit route-shaped values (`REQ-007`; `AC-005`).

## Scope
**Release unit**: audit-route-vocabulary

## Assumptions

- Rows 07 and 08 change the emitted identifiers in the same commit.

## Design decisions

- `D-05`: the test asserts the documented non-route identifiers, which is what an operator sees in the log.

## Alternatives considered

- Assert only that the value is non-empty: rejected - it would not fail a regression back to `/ttl_sweep`.

## Implementation
### Target file
`tests/eventbus/test_authz_generation_ttl.py`
### Procedure
1. Update the sweep assertion at line 148 from `route == "/ttl_sweep"` to `route == "ttl_sweep"`, and name the case `T-013` `test_sweep_audit_record_uses_internal_identifier` (new).
2. Update the startup baseline assertion at line 306 from `record["route"] == "/startup"` to `record["route"] == "startup"`.

### Method
- Two assertion edits; generation-transition and detail assertions stay as they are.

### Details
- Current assertions: `tests/eventbus/test_authz_generation_ttl.py:148` (sweep) and `:306` (startup baseline record).
- Row 09 documents both identifiers as non-route, and row 14 states them for operators.

## Compatibility considerations

- Depends on rows 07, 08, 09 landing in the same commit.

## Security considerations

- N/A: test-only change.

## Rollback considerations

- N/A: revert the commit together with rows 07 and 08.

## Validation plan

- `uv run pytest tests/eventbus/test_authz_generation_ttl.py -v` — both assertions pass on the new identifiers (unit (T-013): sweep and startup identifiers)

## Completion criteria

- The file asserts `ttl_sweep` and `startup`, and no assertion pins a route-shaped internal identifier.

## Out of Scope

- Any change to TTL grant or generation semantics.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Update the two route assertions | Completed | 20261119-232759 | 20261119-232759 | two assertions two assertions now use the internal identifiers ttl_sweep and startup, plus test_sweep_audit_record_uses_internal_identifier (T-013); 15 passed |
| 2 | Run `uv run pytest tests/eventbus/test_eventbus_dlq.py tests/eventbus/test_authz_generation_ttl.py -v` | Completed | 20261119-232759 | 20261119-232759 | Phase 4 acceptance command two assertions now use the internal identifiers ttl_sweep and startup, plus test_sweep_audit_record_uses_internal_identifier (T-013); 15 passed |

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
- **Related target files**: `tests/eventbus/test_authz_generation_ttl.py`