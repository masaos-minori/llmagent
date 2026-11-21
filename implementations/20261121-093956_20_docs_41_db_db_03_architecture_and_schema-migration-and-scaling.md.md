## Goal

Update the dedup rows of `docs/41_db/db_03_architecture_and_schema-migration-and-scaling.md` to the identity-gated rule: legacy/unverified stores are rejected, recreation issues a new generation (REQ-006, REQ-012; AC-11).

## Scope
**Release unit**: docs-sync

## Assumptions
- Rows 01/17/18 have landed; this file's migration-policy framing ("no automatic migration, archive and recreate") is the frame the dedup rows must join.
- Current text (verified 2026-11-21): :68 states "`mcp_dedup` is recreated empty" with no identity/legacy gate, and the per-database table rows (:76 region, :87 region) carry the same wording.

## Design decisions
- The dedup rule joins the other five databases' reject-and-archive language, with the identity/start-state classification (:68 sentence) as the dedup-specific gate.

## Alternatives considered
- N/A: documentation reconciliation of frozen contract text.

## Implementation
### Target file
`docs/41_db/db_03_architecture_and_schema-migration-and-scaling.md`
### Procedure
Rewrite the `mcp_dedup` mentions in the policy sentence and the per-database table rows.
### Method
- Replace "recreated empty" at :68 and the affected table rows with: open-time classification (`legacy_or_unverified`, `replaced`, `schema_mismatch`, `lost`) refuses the store; the operator archives and the next creation issues a new generation (identity row + stamp + marker).
- Keep the six-database framing and the ADR-008 Decision Detail #22 citation intact.
### Details
- Do not claim migration or version-upgrade paths: generation rollover is creation of a new store, not migration of the old one.

## Compatibility considerations
- Wording must agree with db_08's runbook (row 18) and init_db.sh's abort messages (row 08).

## Security considerations
- N/A: prose.

## Rollback considerations
- N/A: revert the commit.

## Validation plan
- `uv run python tools/check_docs_quality.py` and `uv run python tools/check_docs_structure.py` (routing.md docs gate).

## Completion criteria
- AC-11: no "recreated empty" wording remains; the dedup rows state the identity-gated rejection and generation rollover.

## Out of Scope
- Other domains' rows, the runbook itself (row 18).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Update the doc per Implementation > Method | Pending | — | — | |
| 2 | Run the docs checkers (routing.md Tools) | Pending | — | — | |

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
- **Requirement ID**: REQ-006, REQ-012
- **Source issue**: issues/20261120-115841_mcpdl002_store-identity-continuity.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261121-083728_mcpdl002_store-identity-continuity.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261121-093956
- **Related target files**: `docs/41_db/db_03_architecture_and_schema-migration-and-scaling.md`
