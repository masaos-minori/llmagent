## Goal

Make `tools/generate_reference_table.py` emit a `mcp_dedup` schema-version entry (canonical DDL source + `user_version` stamp) in `registry/manifests/db_schema_versions.yaml` (REQ-008, REQ-009, AC-9).

## Scope
**Release unit**: dedup-lease-identity-rollover

## Assumptions
- Row 01 defines the canonical DDL (`_CANONICAL_DDL` over `dedup_call_state`/`store_meta`/`call_attempt_history`) and the `PRAGMA user_version = 1` stamp; this generator reads them from `scripts/shared/mcp_dedup.py` without importing `db`.
- Row 07 regenerates the manifest after this change; the generator never hand-edits the manifest.

## Design decisions
- Emit the dedup entry as a `kind: schema` entry (canonical DDL source path + `version: 1`), mirroring the existing `eventbus` entry shape but with a versioned stamp instead of `unversioned`; extend the `db_schema_versions` generator source list with `scripts/shared/mcp_dedup.py`.

## Alternatives considered
- Hand-writing the manifest entry: forbidden — the manifest is generated output (row 07 rule).

## Implementation
### Target file
`tools/generate_reference_table.py`
### Procedure
Add the dedup source to the `db_schema_versions` manifest generator and emit its entry.
### Method
1. Add `scripts/shared/mcp_dedup.py` to `_MANIFEST_SOURCES["db_schema_versions"]` (current sources: `scripts/db/config.py`, `config/agent.toml`, `scripts/eventbus/schema.sql`; verified 2026-11-21).
2. In the `db_schema_versions` generator (`_db_schema_version_entries`): build the dedup entry with `name: mcp_dedup`, `kind: schema`, `source: scripts/shared/mcp_dedup.py`, the `user_version` stamp read from the store module constant, and a content hash of `_CANONICAL_DDL` consistent with `_schema_version_row`'s existing hash usage.
3. `--check` mode must fail when the manifest drifts from the new entry.
### Details
- The dedup DB path is not an `agent.toml` key, so the entry does not carry `kind: db_path`/`in_agent_toml` (unlike rag/session/workflow); path-key coverage is enforced by `tools/check_db_separation.py` (row 05).

## Compatibility considerations
- Existing entries keep their shape; the new entry is additive. Consumers of the manifest (snapshot `schema_versions` component, docs checkers) see one more entry.

## Security considerations
- N/A: generator/manifest metadata only.

## Rollback considerations
- N/A: revert the commit; regenerate the manifest (row 07) on rollback as well.

## Validation plan
- `uv run python tools/generate_reference_table.py --check` passes with a `mcp_dedup` row after row 07 regenerates the manifest.
- `uv run pytest tests/tools/` (generator tests) shows no drift failures.

## Completion criteria
- AC-9 (second half): `--check` shows a `mcp_dedup` entry in `registry/manifests/db_schema_versions.yaml`.

## Out of Scope
- Manifest file content (row 07), table ownership registration (row 05), DDL itself (row 01).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | Generator has no new test row; existing tests/tools coverage applies |

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
- **Requirement ID**: REQ-008, REQ-009
- **Source issue**: issues/20261120-115841_mcpdl002_store-identity-continuity.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261121-083728_mcpdl002_store-identity-continuity.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261121-093956
- **Related target files**: `tools/generate_reference_table.py`
