## Goal

- Regenerate `registry/manifests/db_schema_versions.yaml` with a `sources` list that names what the builder actually reads, and a stamp-less version row (`REQ-009`, `REQ-011`; `AC-006`, `AC-008`).

## Scope
**Release unit**: manifest-contract-revision

## Assumptions

- Re-measured 2026-11-19: `_db_path_entries` reads both the `scripts/db/config.py` defaults and `config/agent.toml`, and `_db_schema_version_entries` reads `scripts/eventbus/schema.sql`.

## Design decisions

- `D-07`: sources state what is read; the unread `scripts/db/schema_sql.py` entry is dropped and `config/agent.toml` is declared.

## Alternatives considered

- Keep `scripts/db/schema_sql.py` because the module exists: rejected - the manifest declares read paths, not related modules.

## Implementation
### Target file
`registry/manifests/db_schema_versions.yaml`
### Procedure
1. After rows 01 and 03 land, run `uv run python tools/generate_reference_table.py --manifests`.
2. Commit the rewritten file and confirm `sources` lists `scripts/db/config.py`, `config/agent.toml`, `scripts/eventbus/schema.sql`, and the eventbus row records `unversioned`.

### Method
- Generator write only.

### Details
- Committed file today declares `scripts/db/config.py`, `scripts/db/schema_sql.py`, `scripts/eventbus/schema.sql` and omits `config/agent.toml`.
- `ASM-03`: no `PRAGMA user_version` statement exists in either schema source, so the fallback the generator carried was dead.

## Compatibility considerations

- Row 03 restates the schema's version description in the same commit; `tools/check_compat_shims.py` must keep reporting no `WORKFLOW_SCHEMA_VERSION` leftover.

## Security considerations

- N/A: paths, kind, and content hashes only.

## Rollback considerations

- Revert the commit.

## Validation plan

- `uv run python tools/generate_reference_table.py --manifests && git diff --exit-code registry/manifests/` — committed file equals regenerated output (regeneration gate: manifest freshness)
- `uv run pytest tests/tools/test_generate_reference_table.py -v` — `sources` equals the files the builder reads (unit (T-009): source declaration)

## Completion criteria

- `AC-006`, `AC-008`: the declared sources match the builder, and no version-stamping fallback is recorded.

## Out of Scope

- Any change to schema files or the content-hash fingerprint computation.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Regenerate and commit | Completed | 20261119-232759 | 20261119-232759 | generator write regenerated with version 2; generate_reference_table --check: No drift found |
| 2 | Run the regeneration gates | Completed | 20261119-232759 | 20261119-232759 | `--manifests` then `git diff --exit-code` regenerated with version 2; generate_reference_table --check: No drift found |

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
- **Requirement ID**: `REQ-009` (every manifest's sources list names exactly the files and directories its builder reads), `REQ-011` (db_schema_versions version handling matches the current stamp-less fingerprint model)
- **Source issue**: issues/20261117-123014_adrchk014_contract-manifest-sources.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261119-181257_adrchk014_contract-manifest-sources.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261119-210556
- **Related target files**: `registry/manifests/db_schema_versions.yaml`