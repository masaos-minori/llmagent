## Goal
- Create the test that loads every real shipped `[dedup]` table through the typed validator and asserts the explicit keys and the default fingerprint (REQ-003, REQ-005).

## Scope
**Release unit**: N/A: not part of a release unit

- In scope: the new file `tests/mcp_servers/test_shipped_dedup_config.py`.
- Out of scope: the configuration edits (seq 06 to 15) and the validator.

## Assumptions
- This file is named by ten code rows (the ten shipped configuration rows), so it keeps its own document and is not a companion.
- It is written first, before the configuration edits (the Plan's AI instruction); the explicit-key assertion is expected to fail until seq 06 to 15 land.
- Verified in Step 3a: no test reads the real shipped tables (`rg load_dedup_section tests` shows only inline and temp-file uses); the validator requires `db_path` to equal `dedup_db_dir() / mcp_dedup.sqlite`, which is `/opt/llm/db/mcp_dedup.sqlite` when `LLMAGENT_DB_DIR` is unset; ten files carry `[dedup]` (`rg -l "^\[dedup\]" config`).

## Design decisions
- Discover the shipped files with a glob over `config/*_mcp_server.toml` and keep those carrying a `[dedup]` table, so a new server config is covered automatically; assert the discovered set is the expected ten at creation time to catch an accidental deletion.

## Alternatives considered
- Hard-code the ten names only: rejected, a new shipped table would escape the test.

## Implementation
### Target file
`tests/mcp_servers/test_shipped_dedup_config.py` (new)

### Procedure
1. Create the test module with a docstring in the repository test style.
2. Add a fixture that unsets `LLMAGENT_DB_DIR` through `monkeypatch.delenv` and resolves the repository `config/` directory from the test file location.
3. Parametrize over the discovered files: parse with `tomllib`, assert the `[dedup]` table has `pending_timeout_minutes`, call `load_dedup_section` and assert it returns a config whose fingerprint equals the fingerprint of the default config.
4. Add a case that copies one table and adds an unknown key and asserts `ConfigParseError` ("unknown dedup keys").
5. Add one case asserting the discovered set equals the ten expected file names.

### Method
- Use `_config_fingerprint` and `DedupStoreConfig` from `shared.mcp_dedup_config`; read files only, never write under `config/`.

### Details
- The test must pass on a host where `LLMAGENT_DB_DIR` is set, hence the `delenv`.

## Compatibility considerations
- Test-only.

## Security considerations
- Reads only repository configuration files; no secret values are asserted or printed.

## Rollback considerations
- N/A: revert the commit.

## Validation plan
- `uv run pytest tests/mcp_servers/test_shipped_dedup_config.py` (fails on the explicit-key case before seq 06 to 15, passes after); `uv run ruff format` and `uv run ruff check` on the file; `uv run mypy`; then the sequence in `rules/toolchain.md`.

## Completion criteria
- All ten tables load, carry the explicit key, and match the default fingerprint; the unknown-key case is rejected; the expected-set case passes; all validation commands pass.

## Out of Scope
- Configuration edits, validator changes, and other config sections.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Create the test module described in Implementation > Procedure | Pending | — | — | |
| 2 | Confirm the explicit-key case fails before the config edits and passes after | Pending | — | — | |
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
- **Requirement ID**: `REQ-003` (explicit key verified), `REQ-005` (real-file load and unknown-key rejection)
- **Source issue**: issues/20261119-141105_mcpdd001_dedup-keyless-config-gate.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261126-113156_mcpdd001_dedup-keyless-config-gate.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261126-124822
- **Related target files**: `tests/mcp_servers/test_shipped_dedup_config.py`
