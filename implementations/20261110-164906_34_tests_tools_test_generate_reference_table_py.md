## Goal

Drop the `PRAGMA user_version` fixture lines from the reference-table generator test
(`REQ-004`).

## Scope
**Release unit**: fingerprint-cutover (Phase 2; batched with rows 02,03,04,16,23,24,26 because the suite cannot validate green with the stamp removed until this row lands)

## Assumptions
- `tools/generate_reference_table.py` no longer requires a `PRAGMA user_version` stamp
  when deriving the schema-version reference (its row), so the eventbus `schema.sql`
  fixtures no longer carry a stamp.

## Design decisions
- Remove the `PRAGMA user_version` fragment from the two eventbus `schema.sql` fixtures;
  keep the surrounding DDL.

## Alternatives considered
N/A: test-only row; the wording follows the Plan's settled behavior.

## Implementation
### Target file
`tests/tools/test_generate_reference_table.py`

### Procedure
1. Line 138: replace
   `"CREATE TABLE eventbus_events (id INTEGER);\nPRAGMA user_version = 5;\n"`
   with `"CREATE TABLE eventbus_events (id INTEGER);\n"` in `_DEPLOYMENT_SOURCES`.
2. Line 377: replace
   `"CREATE TABLE eventbus_events (id INTEGER);\nPRAGMA user_version = 6;\n"`
   with `"CREATE TABLE eventbus_events (id INTEGER);\n"`.
3. In the drift test that writes the line 377 fixture, drive the drift from a structural
   DDL change (a table/column difference) rather than a version change, since the
   generator no longer reads the stamp (per its row).

### Method
- Locate the fixtures with
  `rg -n 'PRAGMA user_version|check_drift|render_updated_doc|DOMAIN_DOCS' tests/tools/test_generate_reference_table.py`
  before editing.

### Details
- The `eventbus_events` base table stays in both fixtures so the reference still has an
  eventbus entry.

## Compatibility considerations
None; the generator's public helpers (`check_drift`, `render_updated_doc`) are unchanged.

## Security considerations
None.

## Rollback considerations
N/A: revert the commit.

## Validation plan
`uv run pytest tests/tools/test_generate_reference_table.py -v` passes;
`uv run python tools/generate_reference_table.py --check` exits 0.

## Completion criteria
No `PRAGMA user_version` remains in the generator fixtures; drift is driven by structural
DDL.

## Out of Scope
Changing the generator itself (`tools/generate_reference_table.py`, its row).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Drop the PRAGMA user_version fixture lines | Completed | — | 20261111-092006 | PRAGMA fixture lines dropped; drift driven by structural DDL change; 16 tests + --check pass |
| 2 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — |  |

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
- **Requirement ID**: `REQ-004` — drop the PRAGMA user_version fixture lines
- **Source issue**: issues/20261109-112715_adrrev005_schema-fingerprint-unify.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261110-095137_adrrev005_schema-fingerprint-unify.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261110-164906
- **Related target files**: `tests/tools/test_generate_reference_table.py`