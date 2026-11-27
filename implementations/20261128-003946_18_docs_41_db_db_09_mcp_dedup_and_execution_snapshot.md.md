# Implementation Procedure — docs/41_db/db_09_mcp_dedup_and_execution_snapshot.md

## Goal

Document the mdq schema identity as an execution-snapshot component (REQ-004, AC-3).

## Scope
**Release unit**: N/A: not part of a release unit (the Plan lists no release units)

Requirements: REQ-004 (the snapshot gains the mdq identity). Acceptance criterion: AC-3.

Lightweight fill: documentation-only row.

## Assumptions
- Line 159 states "five component keys" and lists them without mdq; the code lists the components in the
  module docstring (lines 7-21) and `COMPONENT_KEYS` (lines 44-50), so the doc claim is the part that
  drifts.
- The component value is the identity hash from `scripts/shared/mdq_schema.py` (new) (row 19), so the doc
  points to that module as the source rather than restating the DDL.
- The component is always present for a configured build, unlike the header-based `schema_versions`, so
  the doc does not describe an `absent` case for it.
- Audit rows recorded before the change carry five components, which the Plan records as a risk; the doc
  states the comparison names the added component.

## Design decisions
- The count statement is corrected to six and the component name is added to the same sentence, so the
  doc keeps one canonical statement of the component set.
- The doc describes the component as an identity read from the canonical text, not as a store header read,
  which is what distinguishes it from `schema_versions`.

## Alternatives considered
- N/A: documentation-only change.

## Implementation
### Target file
`docs/41_db/db_09_mcp_dedup_and_execution_snapshot.md`

### Procedure
- Change the sentence at line 159 from "five component keys" to six and add the mdq component to the list.
- Add one sentence stating that the mdq component carries the identity hash of the canonical text and that
  `mismatching_components` names it when the identity changes.

### Method
- Prose only; the guarded reference-table block is checked, not edited by hand.

### Details
- The existing `dedup` component paragraph above the change keeps its wording, so the two identity
  components read as parallel entries.

## Compatibility considerations
- `uv run python tools/generate_reference_table.py --check` must stay clean for the db domain.

## Security considerations
- N/A: documentation only; the component value is a hash.

## Rollback considerations
- N/A: revert the commit.

## Validation plan
- `uv run python tools/check_docs_content_policy.py`
- `uv run python tools/check_docs_quality.py`
- `uv run python tools/check_docs_structure.py docs/41_db/db_09_mcp_dedup_and_execution_snapshot.md`
- `uv run python tools/check_docs_consistency.py --domain db`
- `uv run python tools/generate_reference_table.py --check`

## Completion criteria
- The doc states six components including the mdq identity and points to the shared module as its source;
  the docs checkers pass (AC-3).

## Out of Scope
- The component implementation (row 3); the identity computation (row 19).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Write the doc changes described in Procedure/Method/Details | Pending | — | — | Phase 4 |
| 2 | Run the documentation checkers (`rules/tool-gates.md`) | Pending | — | — | |

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
- **Related target files**: `docs/41_db/db_09_mcp_dedup_and_execution_snapshot.md`
