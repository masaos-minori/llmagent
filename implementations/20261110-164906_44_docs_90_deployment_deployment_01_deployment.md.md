## Goal

Describe the generalized per-database fingerprint gate in `init_db` and `setup_services` in
`deployment_01` (`REQ-006`).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- Lines 302-307 currently describe the EventBus-specific gate importing
  scripts/shared/eventbus_schema_fingerprint.py and a PRAGMA user_version comparison; both are
  replaced by the generalized shared fingerprint gate.
- The archive-and-recreate flow (line 309) stays.

## Design decisions
- Replace the EventBus-specific gate description with the generalized per-database fingerprint gate;
  keep the marker-table rejection as one example of a fingerprint mismatch.

## Alternatives considered
N/A: documentation-only change; the wording follows the Plan's settled behavior.

## Implementation
### Target file
`docs/90_deployment/deployment_01_deployment.md`

### Procedure
1. Line 302: remove "Refuses an `eventbus.sqlite` stamped with another version or unstamped".
2. Line 304: replace "carrying the legacy migration marker tables `schema_migrations` or
   `workflow_schema_version`" with "whose shape does not match the current canonical schema by the
   shared fingerprint".
3. Line 305: keep "Verifies `eventbus.sqlite` with `eventbus.db_tools verify` (integrity and the
   shared schema fingerprint)".
4. Line 307: replace "The EventBus shape gate is the shared validator
   scripts/shared/eventbus_schema_fingerprint.py... even when PRAGMA user_version matches" with
   "The generalized gate is the shared validator `scripts/shared/schema_fingerprint`; it derives the
   canonical shape from each database's canonical DDL and `assert_matches()` raises on any mismatch,
   independent of any file-header field".

### Method
- Locate the clauses with
  `rg -n 'eventbus_schema_fingerprint|PRAGMA user_version|stamped with another version' docs/90_deployment/deployment_01_deployment.md`
  before editing.

### Details
- Line 309 (archive, delete, re-run `init_db.sh`) stays and now applies to any domain whose shape
  mismatches.

## Compatibility considerations
Cross-references to `rotate_all_dbs()`, `eventbus.db_tools rotate`, and section 11 remain valid.

## Security considerations
None beyond the existing Fail-Fast refusal narrative.

## Rollback considerations
N/A: revert the commit.

## Validation plan
`uv run python tools/check_docs_consistency.py --domain deployment` passes; no document claims a
validation mechanism other than fingerprint matching.

## Completion criteria
Lines 302-307 describe the generalized per-database fingerprint gate; the `eventbus_schema_fingerprint`
import reference and `user_version` comparison are removed.

## Out of Scope
Changing the deploy script order or the environment-variable rules.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Describe the generalized gate in init_db and setup_services | Pending | — | — | |
| 2 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 3 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | |

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
- **Requirement ID**: `REQ-006` — describe the generalized gate in init_db and setup_services
- **Source issue**: issues/20261109-112715_adrrev005_schema-fingerprint-unify.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261110-095137_adrrev005_schema-fingerprint-unify.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261110-164906
- **Related target files**: `docs/90_deployment/deployment_01_deployment.md`
