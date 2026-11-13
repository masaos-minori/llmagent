## Goal
- Make the mdq cases of this file pass by building the child environment from the isolation variables, so the child no longer reaches the production mdq database path (`REQ-002`; `REQ-001`: state the cause).

## Scope
**Release unit**: N/A: not part of a release unit

- In scope: `_import_in_fresh_interpreter` and the tests that call it (`test_empty_token_prevents_every_server_from_importing` and `test_non_empty_tokens_let_a_server_import`).
- Not in scope: skipping or weakening any test, the production database, `config/mdq_mcp_server.toml`, other tests that build a minimal environment.

## Assumptions
- Cause (measured): the child gets only `PATH`, `HOME`, token variables, `PYTHONPATH`, and `LLMAGENT_LOG_DIR`, with no `LLMAGENT_CONFIG_DIR`, so it reads the repository `config/mdq_mcp_server.toml` whose `db_path` is the production `/opt/llm/db/mdq.sqlite`; that file holds the table chunk_summaries that the canonical schema does not define, so `shared/schema_fingerprint.py` raises before the expected message. Falsifier: a child still opens a path under `/opt/llm` after the change.
- `tests/conftest.py` provides the fixture `isolated_subprocess_env`, which forwards `PATH`, `HOME`, and the isolation variables and applies `extra` last; `tests/deploy/test_init_db_eventbus_schema.py` already uses it with a helper that takes the built environment.
- The failing case is `test_empty_token_prevents_every_server_from_importing[...mdq...]`: stderr holds the fingerprint error instead of `auth_token is empty`.

## Design decisions
- Follow the repository convention: the test builds the environment with the fixture and passes it to the helper; the per-test log directory stays through `extra`.
- Do not read the production database, and do not change it.

## Alternatives considered
N/A: skipping the mdq cases on a host with a production database is rejected (the Issue forbids skipping and the gap would remain).

## Implementation
### Target file
`tests/mcp_servers/test_require_auth_token.py`

### Procedure
1. Add a parameter `build_env` (new), a callable taking an `extra` mapping, to `_import_in_fresh_interpreter` and build the child environment as `build_env({token variables, the empty variable when given, "PYTHONPATH": str(_SCRIPTS), "LLMAGENT_LOG_DIR": str(log_dir)})`.
2. In `test_empty_token_prevents_every_server_from_importing` and `test_non_empty_tokens_let_a_server_import`, add the fixture parameter `isolated_subprocess_env` and pass it as `build_env`; import `Callable` from `collections.abc`.
3. Run `uv run pytest tests/mcp_servers/test_require_auth_token.py -p no:randomly -o addopts=""` and confirm the mdq case passes.

### Method
Replace the hand-built `env` dictionary with the fixture-built environment; the empty-token entry is applied through `extra` so it overrides the token value as today.

### Details
- Keep `assert "auth_token is empty" in result.stderr` and the return-code assertion exactly; check that the mdq case now reaches the token check rather than failing for another reason.
- Do not change the AST and config structure tests of the file.

## Compatibility considerations
N/A: test-only change; the tests read the isolated config instead of the host's production database.

## Security considerations
No test may open a production database; the session fingerprint check of `tests/conftest.py` must still pass.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run pytest tests/mcp_servers/test_require_auth_token.py -p no:randomly -o addopts=""`, serially and with `-n auto`.
- `uv run ruff check tests/mcp_servers/test_require_auth_token.py` and `uv run mypy --no-namespace-packages tests/mcp_servers/test_require_auth_token.py`.

## Completion criteria
- The mdq case passes with its original assertion; no test is skipped or weakened; the production database files are unchanged (`AC-002`).

## Out of Scope
- Other subprocess tests with a minimal environment (reported in the change record).
- Production databases and configuration.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261113-180325 | 20261113-180325 |  |
| 2 | Add or update tests per Validation plan | Completed | 20261113-180325 | 20261113-180325 |  |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261113-180325 | 20261113-180325 |  |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20261113-180325 | 20261113-180325 | N/A expected: no `docs/` change N/A: no docs/00_index.md task-scope mapping (test-only change) |

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
- **Requirement ID**: REQ-001 (record the cause), REQ-002 (fix the three failing tests)
- **Source issue**: issues/20261112-183922_testspeed004_adopt-parallel-test-execution.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261113-093804_testspeed004_adopt-parallel-test-execution.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261113-102519
- **Related target files**: `tests/mcp_servers/test_require_auth_token.py`