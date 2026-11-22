## Goal

Replace the tests that prove `build_db_config()` reads `agent.toml` with tests that prove it returns the values from the supplied mapping (REQ-003, REQ-004; AC-004).

## Scope
**Release unit**: RU-2

## Assumptions
- This row is not a companion: `tests/db/test_db_config.py` is named by two rows (`scripts/db/config.py` and `config/agent.toml`), so it keeps its own document.
- `tests/conftest.py` is a separate target row (Plan row 20), so the shared fixture is not changed here.

## Design decisions
- The assertion target changes from "reads the repository file" to "maps the supplied mapping to the typed result"; the fail-closed `ValueError` cases (`sqlite_vec_so` empty, empty paths) keep their coverage.
- `test_single_default_literal` stays: it guards the single `workflow_db_path` default literal, which is unaffected by the signature change.

## Alternatives considered
- Keep the file-reading test as documentation of the old behaviour: rejected by AC-004, which makes the behaviour itself gone.

## Implementation
### Target file
`tests/db/test_db_config.py`
### Procedure
- Replace `test_build_db_config_reads_workflow_path_from_agent_toml` with a case that passes a mapping and asserts the typed result fields.
- Keep the type-rejection and empty-value cases, evaluated on the supplied mapping.
- Remove the `ConfigLoader` import once no test in this file loads the file.
### Method
- Plain dict inputs; no fixture, no filesystem read.
### Details
- Verified 2026-11-21: the current test reads `config/agent.toml` with `ConfigLoader()` and compares it to the loaded value, so it is the direct evidence the Plan cites; the value equality assertions are what carry over.
- Finding (2026-11-22, execution): the `ConfigLoader` import was removed as the Procedure required, but the Completion criterion "no test in this file loads `agent.toml`" is not literally satisfied. `test_repo_config_carries_the_workflow_path_key` still reads the shipped file with `tomllib`; that test is the key-presence guard for the keys Plan row 19 keeps, so it is a deliberate exception to the Method's "no filesystem read", which holds only for the mapping-to-typed-result cases.
- Finding (2026-11-22, execution): the "empty paths" case named by the Design decision cannot be asserted through `build_db_config()`. `DbConfig.__post_init__` rejects an empty path, and the test fixture redirects the `/opt/llm/db/` defaults to the isolation root, so an empty path cannot arrive from a supplied mapping here. Only the `sqlite_vec_so` empty/absent cases stay in this file; the empty-path behaviour is covered in `tests/db/test_sqlite_helper.py` through `helper._db_path = ""`.

## Compatibility considerations
- `tests/db/test_schema_validation_per_database.py` patches `db.helper.build_db_config`; patch targets stay valid through Design D3, and that test is run as an affected test.

## Security considerations
- N/A: test-only change.

## Rollback considerations
- N/A: revert the commit within release unit RU-2.

## Validation plan
- `uv run pytest tests/db/test_db_config.py -v`
- `uv run pytest tests/db/ -v` (affected tests)
- `uv run python tools/check_mock_patch_targets.py`
- `uv run ruff check tests/db/test_db_config.py`, `uv run mypy tests/db/test_db_config.py`

## Completion criteria
- The file proves the mapping-to-typed-result contract for every field, including the rejection paths; no test in this file loads `agent.toml`.

## Out of Scope
- The builder implementation (Plan row 8), the fixture change (Plan row 20).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|---|---|---|---|---|---|
| 1 | Implement the change described in Implementation > Procedure/Method | Completed | 2026-11-22 | 2026-11-22 | Implemented under the gate: the tests assert the mapping-supplied typed configuration and the key-naming ValueError messages. |
| 2 | Add or update tests per Validation plan | Completed | 2026-11-22 | 2026-11-22 | File is green. |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 2026-11-22 | 2026-11-22 | $V |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 2026-11-22 | 2026-11-22 | Documentation landed with Plan row 30. |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|---|---|---|---|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---|---|---|---|---|---|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: REQ-003, REQ-004 (injected-configuration contract for `build_db_config()`)
- **Source issue**: issues/20261120-114212_agentcfg004_config-ownership-split.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261121-140444_agentcfg004_config-ownership-split.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261121-144837
- **Related target files**: `tests/db/test_db_config.py`
