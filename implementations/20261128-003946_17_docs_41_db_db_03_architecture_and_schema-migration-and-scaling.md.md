# Implementation Procedure — docs/41_db/db_03_architecture_and_schema-migration-and-scaling.md

## Goal

State the FTS5 definition comparison and align the mdq runbook rows with the identity and the readiness
conditions (REQ-001, REQ-007, AC-4).

## Scope
**Release unit**: N/A: not part of a release unit (the Plan lists no release units)

Requirements: REQ-001 (definition comparison), REQ-007 (the runbook rows match the behavior).
Acceptance criterion: AC-4.

Lightweight fill: documentation-only row.

## Assumptions
- Section 8e (line 66) owns the per-store archive-and-recreate table; the mdq row (line 74) has no
  re-index verification step today.
- The re-index verification step is recorded in the 8e mdq row and points to db_07 section 11, which is
  the plan default for UNK-04.
- Line 109 names the mdq schema creation source; after row 19 the canonical text is owned by
  `scripts/shared/mdq_schema.py` (new), so that line must name the shared module as the schema authority.
- This file is also a target row of the mdqmcp010 plan; the Plan's dependency bullets order this Plan
  before it, so the overlap is a compatible ordering overlap.

## Design decisions
- The comparison is stated as normalized stored-definition text, not as a name check, so the doc matches
  what the fingerprint actually compares.
- The verification step is one clause in the existing mdq row, not a new section.

## Alternatives considered
- N/A: documentation-only change.

## Implementation
### Target file
`docs/41_db/db_03_architecture_and_schema-migration-and-scaling.md`

### Procedure
- Update the section 8d paragraph (line 62) so the acceptance condition states the FTS5 definition
  comparison by normalized stored text.
- Add the re-index verification step to the mdq row of the 8e table (line 74): after recreation, the
  readiness conditions confirm the definition and the trigger synchronization before the store is
  accepted.
- Update line 109 so the mdq schema authority is `scripts/shared/mdq_schema.py` (new) with the creation
  entry point named separately.

### Method
- Prose only; the guarded reference-table block is checked, not edited by hand.

### Details
- The readiness conditions named in the row are the same names row 15 documents, so the two docs do not
  invent different vocabularies.

## Compatibility considerations
- `uv run python tools/generate_reference_table.py --check` must stay clean for the db domain.

## Security considerations
- N/A: documentation only.

## Rollback considerations
- N/A: revert the commit.

## Validation plan
- `uv run python tools/check_docs_content_policy.py`
- `uv run python tools/check_docs_quality.py`
- `uv run python tools/check_docs_structure.py docs/41_db/db_03_architecture_and_schema-migration-and-scaling.md`
- `uv run python tools/check_docs_consistency.py --domain db`
- `uv run python tools/generate_reference_table.py --check`

## Completion criteria
- The doc states the definition comparison, the mdq row carries the verification step, and the schema
  authority names the shared module; the docs checkers pass (AC-4).

## Out of Scope
- The readiness-condition mapping section, owned by row 16; the snapshot component, owned by row 18.

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
- **Requirement ID**: REQ-001, REQ-007
- **Source issue**: `issues/20261119-142128_mdqmcp006_mdq-fts5-schema-identity.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261127-172305_mdqmcp006_mdq-fts5-schema-identity.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261128-003946
- **Related target files**: `docs/41_db/db_03_architecture_and_schema-migration-and-scaling.md`
