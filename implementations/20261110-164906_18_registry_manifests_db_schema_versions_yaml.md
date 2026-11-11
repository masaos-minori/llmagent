## Goal

Regenerate `registry/manifests/db_schema_versions.yaml` (not hand-edited) after the generator
no longer reads a stamp (`REQ-004`).

## Scope
**Release unit**: fingerprint-cutover (Phase 2; batched with rows 02,03,04,16,23,24,26 because the suite cannot validate green with the stamp removed until this row lands)

## Assumptions
- This YAML is a generated artifact produced by `tools/generate_reference_table.py` (its row);
  eventbus's entry becomes unversioned once the stamp is removed.

## Design decisions
- Do not hand-edit; run the generator after its change and let it rewrite the file.

## Alternatives considered
- Hand-editing the eventbus row: rejected; generated artifacts must be regenerated (Plan target note).

## Implementation
### Target file
`registry/manifests/db_schema_versions.yaml`

### Procedure
1. Ensure `tools/generate_reference_table.py` no longer requires the stamp (its row).
2. Run the generator to rewrite the YAML.
3. Confirm the diff only reflects the removed stamp (eventbus entry unversioned).

### Method
- `uv run python tools/generate_reference_table.py` (or the documented generate command) writes the file; review the resulting diff.

### Details
- After generating, `uv run python tools/generate_reference_table.py --check` exits 0.

## Compatibility considerations
Only the generated eventbus version entry changes (becomes unversioned).

## Security considerations
None.

## Rollback considerations
Revert the commit; git restores the prior YAML.

## Validation plan
`uv run python tools/generate_reference_table.py --check` exits 0; diff reviewed.

## Completion criteria
`registry/manifests/db_schema_versions.yaml` is regenerated and consistent with the stamp-less generator.

## Out of Scope
Hand-editing the file.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | — | 20261111-084108 | regenerated via --manifests; diff limited to eventbus version: unversioned + hash, plus eventbus_api.yaml summary line from row 49 docstring |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — |  |

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
- **Requirement ID**: `REQ-004` — regenerate the schema-version reference
- **Source issue**: issues/20261109-112715_adrrev005_schema-fingerprint-unify.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261110-095137_adrrev005_schema-fingerprint-unify.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261110-164906
- **Related target files**: `registry/manifests/db_schema_versions.yaml`