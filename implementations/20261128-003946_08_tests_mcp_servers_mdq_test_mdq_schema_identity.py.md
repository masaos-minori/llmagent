# Implementation Procedure — tests/mcp_servers/mdq/test_mdq_schema_identity.py

## Goal

Pin that the canonical identity is stable across formatting, changes only when the canonical shape
changes, and reaches the execution snapshot as a component (REQ-003, REQ-004, AC-3).

## Scope
**Release unit**: N/A: not part of a release unit (the Plan lists no release units)

Requirements: REQ-003 (identity from the single canonical DDL source), REQ-004 (snapshot component).
Acceptance criterion: AC-3.

## Assumptions
- Full form: this is a new test file that defines the identity-stability design, so it is not a
  companion of row 1 or row 19.
- The identity is read from `scripts/shared/mdq_schema.py` (new) (row 19); this document does not
  implement it.
- The snapshot side is asserted through `COMPONENT_KEYS` and `mismatching_components` in
  `scripts/shared/execution_snapshot.py` (row 3), whose own pins live in
  `tests/shared/test_execution_snapshot.py` (row 10, companion of row 3).

## Design decisions
- Formatting stability is asserted by comparing the identity of the canonical text with a
  whitespace-and-comment variant of the same statements, so the hash is a shape identity, not a text
  fingerprint.
- The change case adds one column to a copy of the canonical statements and asserts the identity
  differs, which is the condition AC-2 states.

## Alternatives considered
- Assert the identity against a fixed expected hash: rejected, because the canonical shape changes with
  the mdqmcp004 plan, so a literal hash would be a stale pin.

## Implementation
### Target file
`tests/mcp_servers/mdq/test_mdq_schema_identity.py` (new)

### Procedure
- Add the formatting case: the identity of the canonical statements equals the identity of a
  whitespace, comment, and line-break variant of the same statements.
- Add the change case: a copy of the canonical statements with one added column produces a different
  identity.
- Add the snapshot case: the snapshot component named `mdq_schema` (new) carries the identity, and
  `mismatching_components` names it when the identity changes.

### Method
- The cases call the shared identity function directly rather than through the mdq layer, so the pin
  covers the single source the Plan names.

### Details
- The identity is a 64-character hex string, consistent with the other hash components.

## Compatibility considerations
- N/A: new test file; the pinned component set is updated by row 10's own document.

## Security considerations
- N/A: the identity is a hash of DDL text.

## Rollback considerations
- N/A: revert the commit.

## Validation plan
- `uv run pytest tests/mcp_servers/mdq/test_mdq_schema_identity.py tests/shared/test_execution_snapshot.py`
- `uv run python tools/run_validation_gates.py`, then `uv run pytest`.

## Completion criteria
- Formatting differences do not change the identity, a shape change does, and the snapshot component
  changes with it (AC-2, AC-3).

## Out of Scope
- The identity computation itself (row 19); the health publication (row 4).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | Phase 3 |
| 2 | Add or update tests per Validation plan | Pending | — | — | This document is the test row |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | N/A: the snapshot component is documented by row 18 |

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
- **Requirement ID**: REQ-003 (canonical identity from the single DDL source), REQ-004 (snapshot
  component)
- **Source issue**: `issues/20261119-142128_mdqmcp006_mdq-fts5-schema-identity.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261127-172305_mdqmcp006_mdq-fts5-schema-identity.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261128-003946
- **Related target files**: `tests/mcp_servers/mdq/test_mdq_schema_identity.py`
