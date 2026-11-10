## Goal

Stop requiring a `PRAGMA user_version` stamp when generating the schema-version reference in
`tools/generate_reference_table.py` (`REQ-004`).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- The generator reads a `PRAGMA user_version` stamp from `schema.sql` to populate
  `registry/manifests/db_schema_versions.yaml` (lines 73, 562); eventbus no longer stamps it.
- The generator must not hard-fail when a domain's `schema.sql` has no stamp.

## Design decisions
- Remove the hard requirement that every `schema.sql` carries a `PRAGMA user_version`; derive the version from whatever is present and record "unversioned"/null otherwise.

## Alternatives considered
- Keeping the requirement and only special-casing eventbus: rejected; one mechanism, no stamp anywhere (REQ-004).

## Implementation
### Target file
`tools/generate_reference_table.py`

### Procedure
1. Remove the assertion/parse that a `PRAGMA user_version` stamp exists (line 562 area).
2. Relax line 73's usage so a missing stamp yields a null/unversioned entry instead of an error.
3. Regenerate `registry/manifests/db_schema_versions.yaml` (its row) after the change.

### Method
- Locate the stamp-read branch and replace it with a graceful "no stamp" path; keep the rest of the reference generation unchanged.

### Details
- After regenerating, `uv run python tools/generate_reference_table.py --check` must exit 0.

## Compatibility considerations
The reference file keeps its structure; eventbus's entry becomes unversioned.

## Security considerations
None.

## Rollback considerations
Revert the commit and the regenerated YAML.

## Validation plan
`uv run pytest tools/tools/test_generate_reference_table.py -v` (that row drops the `user_version` fixture lines); `uv run python tools/generate_reference_table.py --check` exits 0.

## Completion criteria
`tools/generate_reference_table.py` does not require a `PRAGMA user_version` stamp; the regenerated reference is clean under `--check`.

## Out of Scope
Changing the reference file schema.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |

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
- **Requirement ID**: `REQ-004` — generator no longer requires a version stamp
- **Source issue**: issues/20261109-112715_adrrev005_schema-fingerprint-unify.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261110-095137_adrrev005_schema-fingerprint-unify.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261110-164906
- **Related target files**: `tools/generate_reference_table.py`
