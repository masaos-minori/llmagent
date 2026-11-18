## Goal

Regenerate `registry/manifests/db_schema_versions.yaml` so the `workflow_db_path` entry
flips from `in_agent_toml: false` to `true` after the key lands in `config/agent.toml`.
(`REQ-006` generated artifacts regenerated, never hand-edited)

## Scope
**Release unit**: WORKFLOW-CONFIG

## Assumptions

- The manifest is a generated file: the only allowed change is running the generator
  (`tools/generate_reference_table.py --manifests`); hand-editing is prohibited (issue
  constraint).
- Runs after procedures 03/04 land in the working tree (generator reads the live
  config/code).

## Design decisions

- Run the generator, then `--check` to prove no drift; commit the regenerated output.

## Alternatives considered

- N/A: regeneration is the only permitted shape for a generated manifest.

## Implementation
### Target file
`registry/manifests/db_schema_versions.yaml`

### Procedure
1. Run `uv run python tools/generate_reference_table.py --manifests`.
2. Confirm the `workflow_db_path` entry (`:10-13`) now shows `in_agent_toml: true`.

### Method
Generator-only edit; verify the diff touches only the affected entry (no unrelated
manifest churn — if unrelated rows change, stop and report, they indicate a tree state
problem).

### Details
The same generator run also feeds the deployment guarded table (procedure 13); they
can be produced by one invocation pass but are committed as the same unit.

## Compatibility considerations

- `tools/generate_reference_table.py --check` gate and CI compare against this file;
  stale content fails them.

## Security considerations

- N/A: generated registry artifact.

## Rollback considerations

- N/A: revert the commit.

## Validation plan

- `uv run python tools/generate_reference_table.py --check` — "No drift" (AC-2).

## Completion criteria

- Manifest shows `in_agent_toml: true` for `workflow_db_path`; `--check` clean (AC-2).

## Out of Scope

- Any hand-edit of the manifest or other registry files.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Regenerate the manifest with the generator | Pending | — | — | |
| 2 | Run `generate_reference_table.py --check` | Pending | — | — | |

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
- **Requirement ID**: `REQ-006` (manifest regenerated to reflect the new key)
- **Source issue**: issues/done/20261117-123019_adrchk019_mdq-workflow-db-settings.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261118-155712_adrchk019_mdq-workflow-db-settings.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261118-162732
- **Related target files**: `registry/manifests/db_schema_versions.yaml`
