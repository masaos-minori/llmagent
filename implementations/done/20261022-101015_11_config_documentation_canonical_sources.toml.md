## Goal
Delete the `eventbus.persistence-schema.incremental-migration` entry from the Canonical Source Registry and keep the registry valid (REQ-007).

## Scope
- Remove that one `[[canonical_sources]]` table; all other entries unchanged.

## Assumptions
- The entry describes the mechanism being removed (`source_paths = ["scripts/eventbus/db.py"]`, claim type `operational-procedure`) and has a single citation, in `db_02`, removed by its own procedure (verified by search).
- `tools/check_canonical_source_registry.py` validates schema, existing source paths, and single-normative-source-per-claim-type; removing an entry cannot violate those rules.
- `config/documentation_canonical_sources.toml` is read only by documentation tools and is not a runtime configuration (verified: no `deploy/` reference).

## Design decisions
- Remove the whole table including its `notes`; do not leave a comment about the removal.

## Alternatives considered
- Repointing the entry to the new create-only description: rejected, the Plan retires the decision target because no incremental mechanism exists to be canonical for.

## Implementation
### Target file
`config/documentation_canonical_sources.toml`

### Procedure
1. Delete the `[[canonical_sources]]` table whose `decision_target` is `eventbus.persistence-schema.incremental-migration`.

### Method
- Delete by decision target string; keep blank-line separation between the remaining tables.

### Details
- Order with the `db_02` procedure: remove the citation in `db_02` first or in the same change so no document cites a missing target.

## Compatibility considerations
Only documentation tools read the file; run the registry and prose checkers to confirm.

## Security considerations
N/A: documentation metadata.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run python tools/check_canonical_source_registry.py`, `uv run pytest tests/tools/test_check_canonical_source_registry.py -q`, `uv run python tools/check_canonical_document_prose.py`.
- `rg "persistence-schema.incremental-migration" docs config tools tests` returns no match.

## Completion criteria
- The entry is gone, the registry checker passes, and nothing cites the removed target.

## Out of Scope
- Other registry entries and registry schema changes.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Delete the registry entry | Done | 20261022-101015 | 20261022-101015 | Deleted the `eventbus.persistence-schema.incremental-migration` table; kept one blank-line separator between the remaining tables. |
| 2 | Run the registry checkers and tests | Done | 20261022-101015 | 20261022-101015 | check_canonical_source_registry passes; test_check_canonical_source_registry 25 passed; `rg "persistence-schema.incremental-migration" docs config tools tests` returns no match. |

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
- **Requirement ID**: `REQ-007` (retire the incremental-migration decision target)
- **Source issue**: `issues/20261021-102130_rmebmig_remove-the-eventbus.sqlite-schema-migrations.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261022-093935_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261022-101015
- **Related target files**: config/documentation_canonical_sources.toml
