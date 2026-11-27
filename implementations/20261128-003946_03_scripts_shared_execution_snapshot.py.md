# Implementation Procedure — scripts/shared/execution_snapshot.py

## Goal

Add the mdq schema identity as an execution-snapshot component so replay equality can see an mdq
schema change (REQ-004).

## Scope
**Release unit**: N/A: not part of a release unit (the Plan lists no release units)

Requirements: REQ-004 (the snapshot gains the mdq identity). Acceptance criterion: AC-3.

## Assumptions
- Full form: this is a shared-module contract change; snapshot equality consumers read the component
  map, so the component set is a public contract.
- The identity is read from `scripts/shared/mdq_schema.py` (new), which keeps `shared` a leaf; no
  sqlite3 connection is opened here (the shared boundary rule stated at lines 13-15).
- `mdq.sqlite` is not added to `_DB_PATH_KEYS` (lines 57-66): the component value comes from the
  canonical text, not from the file header, so there is no path to resolve.
- No consumer asserts a fixed component count; the pinned component set is the companion test.

## Design decisions
- The component key is `mdq_schema` (new) and its value is the identity hash, matching the existing
  `dedup` component pattern of a read-only identity lookup.
- The value is never `absent` for a configured build: the canonical text is always available, so the
  component is always present, unlike the header-based `schema_versions`.

## Alternatives considered
- Read the identity from the live database header: rejected, because ADR-008 forbids version
  stamping and the shared boundary rule forbids opening a connection in this layer.

## Implementation
### Target file
`scripts/shared/execution_snapshot.py`

### Procedure
- Add `mdq_schema` (new) to `COMPONENT_KEYS` (lines 44-50).
- Add `_mdq_component` (new) that returns the identity from `scripts/shared/mdq_schema.py` (new) and
  is called by `build_execution_snapshot` (line 169).
- Extend the module docstring component list (lines 7-21) with the new component.

### Method
- The helper performs no config discovery and no store open, consistent with `_dedup_component`
  (line 146); a failure to read the canonical text yields `absent` rather than raising, because every
  reader here is tolerant and never raises.

### Details
- `mismatching_components` (line 211) names the new component automatically, so an audit row can
  distinguish an mdq schema change from a config-only change (AC-3).

### Companion test files
- `tests/shared/test_execution_snapshot.py`
  - Procedure: the component-set assertion at line 103 gains `mdq_schema` (new); add a case that
    changes the canonical DDL text and shows the component value and the mismatch naming change.
  - Validation: `uv run pytest tests/shared/test_execution_snapshot.py` — the mdq identity is a named
    component and equality changes when the identity changes.

## Compatibility considerations
- Consumers are the companion test and the audit writers that name mismatching components; existing
  audit rows recorded before the change carry five components, so a comparison against a new snapshot
  reports the mdq component as added — the intended behavior (Plan Risk).

## Security considerations
- N/A: the component value is a hash of canonical DDL text; no path, secret, or row content is
  published.

## Rollback considerations
- Reverting removes the component; snapshots built while it was present cannot be compared with
  snapshots built after the revert, so rollback is a code revert only.

## Validation plan
- `uv run pytest tests/shared/test_execution_snapshot.py`
- `uv run lint-imports` — `shared-is-leaf` stays KEPT.
- `uv run python tools/run_validation_gates.py`, then `uv run pytest`.

## Completion criteria
- The snapshot map contains the mdq component and its value changes only when the canonical shape
  changes (AC-3).

## Out of Scope
- The canonical DDL text and the hash computation (row 19); the health publication of the identity
  (row 4).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | Phase 3 |
| 2 | Add or update tests per Validation plan | Pending | — | — | Companion `tests/shared/test_execution_snapshot.py` |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | `uv run lint-imports` included |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | `docs/41_db/db_09_mcp_dedup_and_execution_snapshot.md` (row 18) |

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
- **Requirement ID**: REQ-004 (execution snapshots include the mdq schema identity)
- **Source issue**: `issues/20261119-142128_mdqmcp006_mdq-fts5-schema-identity.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261127-172305_mdqmcp006_mdq-fts5-schema-identity.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261128-003946
- **Related target files**: `scripts/shared/execution_snapshot.py`, `tests/shared/test_execution_snapshot.py`
