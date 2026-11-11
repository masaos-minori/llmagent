## Goal

Replace the marker-table finding in the recovery-drill harness with the generalized
fingerprint finding for each domain (`REQ-003`, `REQ-004`).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- `scripts/db/recovery_drill.py` now fingerprints each domain instead of detecting the
  legacy marker tables (`REQ-004`; its row).
- The seeded marker tables (`schema_migrations`, `workflow_schema_version`) are extra
  tables under exact matching, so they fail the fingerprint.

## Design decisions
- The drill's identity+integrity checks for rag/session stay; only the marker-table
  expectation changes to a fingerprint-refusal expectation.

## Alternatives considered
N/A: test-only row; the wording follows the Plan's settled behavior.

## Implementation
### Target file
`tests/db/test_recovery_drill.py`

### Procedure
1. Lines 203-222 seed `schema_migrations` / `workflow_schema_version` marker DDL; keep
   the fixtures but reframe their purpose: they now represent an extra legacy table that
   fails the fingerprint, not a marker-table finding.
2. In `_build_workflow` (lines 244-250) the marker injection stays; the asserted drill
   outcome changes from "marker-table finding" to "refuse with the archive-and-recreate
   error".
3. Drop any assertion that reads a marker-table result out of the drill output.

### Method
- Locate the marker fixtures and drill assertions with
  `rg -n 'schema_migrations|workflow_schema_version|marker|run_drill|DOMAINS' tests/db/test_recovery_drill.py`
  before editing.

### Details
- The rag/session baselines still fall back to plain schemas when sqlite-vec is absent
  (existing comment lines 28-37); unchanged.

## Compatibility considerations
The `db.recovery_drill.DOMAINS` / `run_drill` imports at lines 24-25 stay.

## Security considerations
None.

## Rollback considerations
N/A: revert the commit.

## Validation plan
`uv run pytest tests/db/test_recovery_drill.py -v` — marker-table fixtures now drive a
fingerprint refusal with the explicit error.

## Completion criteria
The drill's marker-table expectation is replaced by a fingerprint refusal per domain;
clean baselines pass.

## Out of Scope
Changing the drill itself (`scripts/db/recovery_drill.py`, its row).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Replace the marker-table finding with the fingerprint finding | Completed | — | 20261111-110545 | canonical-derived fixtures via _fallback_from_canonical; marker test renamed to fingerprint finding |
| 2 | Run the validation sequence (`rules/toolchain.md`) | Completed | — | 20261111-110545 | 13 tests pass |

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
- **Requirement ID**: `REQ-003` / `REQ-004` — marker-table finding replaced by fingerprint
- **Source issue**: issues/20261109-112715_adrrev005_schema-fingerprint-unify.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261110-095137_adrrev005_schema-fingerprint-unify.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261110-164906
- **Related target files**: `tests/db/test_recovery_drill.py`