## Goal

Add the recovery-drill runbook to the DB recovery document: procedure, frequency placeholder, and artifact retention location (`REQ-007`, drills with retained audit artifacts).

## Scope

- Modify only `docs/41_db/db_07_api_and_operations-recovery-and-reference.md`.

## Assumptions

- Verified (Step 3a): section 9 covers corruption recovery, section 11 the recreation procedure, 11a how to identify a schema, section 12 a verification plan. The new runbook is a new subsection under section 9 or after section 11; RPO/RTO values, schedule, and retention owner stay explicit open items (UNK-01). Write in English; state intent, boundaries, constraints, and failure behavior only, not implementation detail (`skills/DESIGN.md` Docs content policy). Edit only the sections named below (`docs/00_index.md` task scope: DB layer spec and the ADR index).
- Names that `tools/stale_detector.py` flags in this document are created by other rows of this Plan (the framework row 01 and the domain, drill, and schema rows it names) and exist when `code-implementation` executes the rows in Plan phase order.

## Design decisions

- Add one subsection; do not renumber existing sections.

## Alternatives considered

- N/A: documentation row.

## Implementation

### Target file

`docs/41_db/db_07_api_and_operations-recovery-and-reference.md`

### Procedure

1. Add a drill subsection: purpose, preconditions (outside heavy writes, because archiving reads all four databases), procedure at the intent level (run the drill command, read the artifact), measured outputs (restore time, data-loss window), artifact location (archive directory), and a marked placeholder for frequency and ownership.
2. Update section 11 so recreation points to the migration path first (registered upgrades migrate; recreation only for unregistered or older-than-baseline databases).

### Method

- Register any new Needs-confirmation marker in the governance inventory (`tools/check_needs_confirmation_inventory.py`) if one is added for the open RPO/RTO owner.

### Details

- Describe the artifact fields by meaning only, not by JSON key.

## Compatibility considerations

- N/A: documentation.

## Security considerations

- N/A: documentation.

## Rollback considerations

- N/A: revert the commit.

## Validation plan

- `uv run python tools/check_docs_quality.py`
- `uv run python tools/check_docs_structure.py`
- `uv run python tools/check_docs_content_policy.py`
- `uv run python tools/check_docs_japanese.py`
- `uv run python tools/check_docs_consistency.py --domain deployment`
- `uv run python tools/check_docs_consistency.py --domain db`
- `uv run python tools/check_needs_confirmation_inventory.py`

## Completion criteria

- The runbook subsection exists with the placeholder for frequency and ownership, section 11 points to the migration path, and the checkers pass.

## Out of Scope

- Choosing RPO/RTO targets or the schedule.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Edit the document per Procedure | Pending | — | — | Plan Phase 6; after row 11 |
| 2 | Run the documentation checkers (`routing.md` Tools) | Pending | — | — |  |

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
- **Requirement ID**: REQ-007
- **Source issue**: issues/20261029-104500_dbmig001_forward-only-db-migrations.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261029-214108_dbmig001_forward-only-db-migrations.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261030-151746
- **Related target files**: docs/41_db/db_07_api_and_operations-recovery-and-reference.md
