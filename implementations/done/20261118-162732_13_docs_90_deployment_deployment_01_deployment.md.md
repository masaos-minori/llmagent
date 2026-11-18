## Goal

Regenerate the guarded "DB Path Reference (auto-generated)" table in
`docs/90_deployment/deployment_01_deployment.md` so the `workflow.sqlite` row shows
"Yes" for `Set in agent.toml?` after `config/agent.toml` gains the key. (`REQ-006`
generated artifacts regenerated, never hand-edited)

## Scope
**Release unit**: WORKFLOW-CONFIG

## Assumptions

- The table lives between the `<!-- AUTO-GENERATED: generate_reference_table.py
  db-path-reference -->` guard comments (`:349-359`); regeneration is the only allowed
  edit inside them (issue constraint).
- Runs after procedures 03/04 land in the working tree (the generator reads live
  `scripts/db/config.py` and `config/agent.toml`).

## Design decisions

- Run `tools/generate_reference_table.py --type deployment`, then
  `generate_reference_table.py --check` to prove no drift; commit the regenerated output.

## Alternatives considered

- N/A: regeneration is the only permitted shape for a guarded generated block.

## Implementation
### Target file
`docs/90_deployment/deployment_01_deployment.md`

### Procedure
1. Run `uv run python tools/generate_reference_table.py --type deployment`.
2. Confirm the `workflow.sqlite` row of the guarded table now reads `Yes`.

### Method
Generator-only edit; verify the diff touches only the guarded table (no unrelated doc
churn — if other lines change, stop and report, they indicate a tree state problem).

### Details
The prose around the table (`:273-275`, `:286`) already defers to the generated table
for which keys are set and does not name `workflow_db_path` as a default-only case, so
no manual sentence edit is needed in this file.

## Compatibility considerations

- `generate_reference_table.py --check` and CI compare against the generated content;
  stale content fails them.

## Security considerations

- N/A: generated documentation block.

## Rollback considerations

- N/A: revert the commit (WORKFLOW-CONFIG unit).

## Validation plan

- `uv run python tools/generate_reference_table.py --check` — no drift.
- `uv run python tools/check_docs_consistency.py --domain deployment` (plan row
  validation) — clean.

## Completion criteria

- The guarded table shows `workflow_db_path` as set in `agent.toml` (AC-4); `--check`
  clean.

## Out of Scope

- `docs/41_db/db_01_...` (procedure 14).
- Any hand-edit of the guarded table.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Regenerate the guarded DB Path Reference table | Completed | 2026-11-18 | 2026-11-18 |  |
| 2 | Run `generate_reference_table.py --check` and the deployment docs checker | Completed | 2026-11-18 | 2026-11-18 |  |

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
- **Requirement ID**: `REQ-006` (deployment guarded table regenerated)
- **Source issue**: issues/done/20261117-123019_adrchk019_mdq-workflow-db-settings.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261118-155712_adrchk019_mdq-workflow-db-settings.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261118-162732
- **Related target files**: `docs/90_deployment/deployment_01_deployment.md`