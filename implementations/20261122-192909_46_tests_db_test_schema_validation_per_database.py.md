## Goal

Regression run/adjustment for the per-database schema validation imports (`DedupStore`/`DedupStoreError` and canonical DDL at lines 42-43): keep imports resolvable against the facade after the renames (sibling seq 02) and add the `identity_mismatch` (new) state only if the file enumerates refusal states.

## Scope
**Release unit**: N/A: not part of a release unit (Phase 3 validation-only row)

## Assumptions
- The code-side contract changes come from the sibling procedures cited above; this row only follows them.

## Design decisions
- Follow the sibling procedure's contract exactly; no new fixture abstraction beyond what the sibling's Validation plan implies.

## Alternatives considered
- N/A: test-only follower row.

## Implementation
### Target file
`tests/db/test_schema_validation_per_database.py`
### Procedure
1. Apply the changes described in Goal at the sites named in Reason/Repository Evidence; remove references to deleted APIs (discovery loader, cache clear, `[retry_class]` map, `mcp_dedup.toml`).
### Method
Edit in place; keep existing fixture names where consumers depend on them.
### Details
- Evidence for each site is in the plan's Implementation Target Files row (Verified column).

## Compatibility considerations
- Keep public fixture names and test class names stable where other tests or tooling reference them.

## Security considerations
- N/A: test edit.

## Rollback considerations
- N/A: revert the commit.

## Validation plan
- `uv run pytest tests/db/test_schema_validation_per_database.py -q`; then the delivery-unit full-suite run (`uv run pytest -q`).

## Completion criteria
- Schema validation per database passes unchanged for the dedup store (behavior lock: schema and DDL untouched).

## Out of Scope
- Production code changes (owned by the sibling procedures).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Update the test file per Implementation | Pending | — | — | |
| 2 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |

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
- **Requirement ID**: REQ-008
- **Source issue**: issues/20261120-115842_mcpdl003_dedup-config-isolation.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261121-172154_mcpdl003_dedup-config-isolation.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261122-192909
- **Related target files**: `tests/db/test_schema_validation_per_database.py`
