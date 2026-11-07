## Goal

- Stop `tools/generate_reference_table.py` from scraping the deleted `WORKFLOW_SCHEMA_VERSION` constant: the `db_schema_versions` manifest keeps only the EventBus `PRAGMA user_version` entry, and the committed manifest regenerates without the workflow row (amended plan row: REQ-002 / REQ-008 fallout — CI runs `--check` against the regenerated manifest).

## Scope
**Release unit**: current-schema-only-cutover

- Manifest-builder edit in this file plus regeneration of `registry/manifests/db_schema_versions.yaml` and the companion test expectations; the DDL sources are rewritten by siblings 08 (workflow) and 09 (eventbus).

## Assumptions

- `_db_path_entries()` (the `db_paths` manifest entries this builder prepends) and the EventBus entry (`_PRAGMA_USER_VERSION_RE` over `scripts/eventbus/schema.sql`) stay — `PRAGMA user_version = 6` survives the cutover (Plan Design: `user_version` stays EventBus-only).
- CI gates on `generate_reference_table.py --check` (`.github/workflows/ci.yml`), so the regenerated manifest must land in the same commit as the builder edit (verified 2026-11-07).

## Design decisions

- Remove the workflow entry entirely instead of deriving a workflow "version" from DDL shape: there is no workflow version identifier after the cutover (REQ-002), and a shape hash belongs to the fingerprint concept, not this version manifest (REQ-008 fingerprints are EventBus-side).

## Alternatives considered

- Keeping the manifest row with an empty version: rejected — `--check` compares content hashes of source files; a row pinned to a file that no longer defines the constant raises `ManifestError` in `_db_schema_version_entries` (line 568) the moment sibling document 08 lands.

## Implementation
### Target file
`tools/generate_reference_table.py`

### Procedure
1. Phase 3 commit: rewrite the companion test expectations first (RED), then apply the builder edit, then regenerate the manifest (Plan Phase 3, amended fallout row).

### Method
- Delete `_WORKFLOW_VERSION_RE = re.compile(r'^WORKFLOW_SCHEMA_VERSION = "([^"]+)"', re.MULTILINE)` (line 75).
- In `_db_schema_version_entries` (lines 560-578): delete the `workflow_text = DB_SCHEMA_SQL_SRC.read_text(...)` read, the `workflow_match = _WORKFLOW_VERSION_RE.search(workflow_text)` search with its `ManifestError("schema_sql.py does not define WORKFLOW_SCHEMA_VERSION")` branch (lines 566-568), and the `entries.append(_schema_version_row("workflow", DB_SCHEMA_SQL_SRC, workflow_match.group(1)))` block (lines 574-576); keep the EventBus entry append, the `_db_path_entries()` base, and the `entries.sort(...)` line byte-identical.
- Check whether `DB_SCHEMA_SQL_SRC` has remaining users in the file (`grep -n "DB_SCHEMA_SQL_SRC" tools/generate_reference_table.py`); if the only remaining use is a `--check` source-hash listing, keep the constant; otherwise remove its definition too.
- Regenerate the committed manifest: `uv run python tools/generate_reference_table.py --manifests` — `registry/manifests/db_schema_versions.yaml` loses its `("schema", "workflow")`-style entry (line 27 region at HEAD) and must be committed in the same change.

### Companion test files
- `tests/tools/test_generate_reference_table.py`
  - Procedure: update the `scripts/db/schema_sql.py` fixture stub `'WORKFLOW_SCHEMA_VERSION = "1.1.0"\n'` (line 136) — the stub file content may stay (the builder no longer parses it) but must not be required; remove the expected `("schema", "workflow")` tuple from the `db_schema_versions` entry-kind assertion (line 317) and any assertion that a missing constant raises `ManifestError`; keep the stale/missing-manifest cases (lines 366-444 region) — they exercise the regenerated manifest.
  - Validation: `uv run pytest tests/tools/test_generate_reference_table.py` — RED after the fixture/expectation rewrite, green after the Method; then `uv run python tools/generate_reference_table.py --check` exits 0 against the regenerated manifest.

## Compatibility considerations

- Downstream manifest consumers (docs reference tables rendered from `deployment` → `db_schema_versions`) see one fewer row; no machine contract pins the workflow row count (docs rows 26/28 are rewritten by siblings 26/28).

## Security considerations

- N/A: manifest scraping removal only reduces source-file reads.

## Rollback considerations

- Revert the commit restores the regex, the workflow entry, and the committed manifest row (single-commit change within the release unit).

## Validation plan

- `uv run pytest tests/tools/test_generate_reference_table.py` — green (amended Plan Validation row).
- `uv run python tools/generate_reference_table.py --check` — exit 0 (CI gate, `.github/workflows/ci.yml`).
- Whole-unit gates run in Plan Phase 5 per `rules/toolchain.md`.

## Completion criteria

- The builder references neither `WORKFLOW_SCHEMA_VERSION` nor `_WORKFLOW_VERSION_RE`, the committed `db_schema_versions` manifest contains only EventBus schema-version entries plus the db-path rows, and `--check` passes in CI (AC-002, AC-003).

## Out of Scope

- `schema_sql.py` constant removal — sibling document 08.
- `setup_services.sh` gate removal — sibling document 30.
- Docs rendering wording — siblings 26, 28.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Rewrite companion test expectations; confirm RED (Plan Phase 3) | Completed | — | 20261107-131044 | Release unit "current-schema-only-cutover" assertion rewrite RED confirmed |
| 2 | Remove regex + workflow entry from `_db_schema_version_entries`; regenerate manifest with `--manifests` (Plan Phase 3) | Completed | — | 20261107-131044 | Manifest file lands in the same commit regex+workflow entry+DB_SCHEMA_SQL_SRC removed; db_schema_versions.yaml and eventbus_api.yaml regenerated (16 passed) |
| 3 | Run `uv run pytest tests/tools/test_generate_reference_table.py` and `--check` green | Completed | — | 20261107-131044 | pytest green; --check exits 'No drift found' |
| 4 | Run the validation sequence (`rules/toolchain.md`) in the Phase 5 unit pass | Completed | — | 20261107-134719 | generate_reference_table --check: No drift found (manifests and reference docs regenerated in cycle) |

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
- **Requirement ID**: REQ-002 (constant removed from the schema layer must not be scraped), REQ-008 (manifests regenerate from canonical sources)
- **Source issue**: issues/20261106-125142_compatrm001_remove-db-migration-and-enforce-current-schema-startup.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261107-061846_compatrm001_remove-db-migration-and-enforce-current-schema-startup.md (amended 2026-11-07, fallout row)
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261107-113303
- **Related target files**: `tools/generate_reference_table.py`, `tests/tools/test_generate_reference_table.py` (the regenerated manifests and reference-table doc are tool output artifacts of this target, not separately edited body targets; corrected 2026-11-07 to match the body)