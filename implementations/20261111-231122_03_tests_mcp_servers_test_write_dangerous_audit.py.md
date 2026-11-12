## Goal

Add a new parametrized cross-server test that asserts an audit record exists for every WRITE_DANGEROUS tool on its hosting server, plus a completeness test that asserts the parametrization equals the WRITE_DANGEROUS set derived from `config/agent.toml` `[tool_safety_tiers]` (`REQ-002`, `AC-2`).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- Exactly five hosting servers expose a WRITE_DANGEROUS tool: file-delete-mcp (`delete_file`, `delete_directory`), github-mcp (six `github_*` write tools), rag-pipeline-mcp (`rag_delete_document`), cicd-mcp (`trigger_workflow`), git-mcp (`git_checkout`, `git_pull`, `git_push`). `shell_run` is `ADMIN`, not `WRITE_DANGEROUS`, so shell-mcp is excluded.
- The 13 `WRITE_DANGEROUS` tools in `config/agent.toml` are the canonical set; the completeness test reads that table rather than hard-coding the list.
- Each server's `call_tool` endpoint can be reached through a `TestClient` with services stubbed (as the existing per-server tests do).

## Design decisions
- One module `tests/mcp_servers/test_write_dangerous_audit.py` parametrizes over `(server_dir, tool)` and captures the server's `logger.info` call to assert one `mcp_tool_exec` record per call.
- The completeness test loads `[tool_safety_tiers]` from `config/agent.toml`, filters to `WRITE_DANGEROUS`, and asserts it matches the parametrized `(server, tool)` pairs — so drift in either direction fails the test.
- Reuse the existing `_auth_headers.py` helper for authenticated `TestClient` calls.

## Alternatives considered
- Per-server test files for each of the five servers: more duplication and no completeness guard across servers. Rejected in favor of one parametrized module with a completeness check.

## Implementation
### Target file
`tests/mcp_servers/test_write_dangerous_audit.py` (new)

### Procedure
1. Create `tests/mcp_servers/test_write_dangerous_audit.py`.
2. Load `[tool_safety_tiers]` from `config/agent.toml` (via `tomllib`/the repo's config loader) and build the WRITE_DANGEROUS set.
3. For each of the five hosting servers, import the server module, build a `TestClient` with the server's auth token, stub the server's external service (embedding model / GitHub / CI runner / git repo), patch the server's `logger` with a call-recording stub, and POST `/v1/call_tool` for each WRITE_DANGEROUS tool it owns.
4. Assert one `mcp_tool_exec` record was emitted with the correct `tool`, `server_key`, and `outcome`.
5. Add the completeness test: assert the parametrized `(server, tool)` set equals the `WRITE_DANGEROUS` set from the config.

### Method
- Parametrize with a mapping `{server_dir: [tools]}` covering the 13 tools across the five servers.
- Capture audit via monkeypatching the server module's `logger` (or its `_audit_log`) with an `AsyncMock`/`Mock` recording `.info` calls, then assert the recorded payload's `event == "mcp_tool_exec"` and `tool` matches.
- The completeness test compares `sorted(config_write_dangerous)` against `sorted([tool for _, tool in parametrization])`.

### Details
- Import-time side effects of five server modules are the main risk (UNK-04); if one module cannot be imported in the test process, fall back to per-server parametrization within the same module and keep the completeness test as the cross-server guard.
- `target` values differ per server; the test asserts record presence and `tool`/`server_key`, not the exact `target` string.

### Companion test files
N/A: this document is the test itself.

## Compatibility considerations
- New file under `tests/mcp_servers/` (exists); does not modify existing tests.
- `tests/tools/test_adr_authority.py` references ADR-016 but is unrelated to this test (verify no inventory breaks in Phase 3, UNK-05).

## Security considerations
- The test only asserts that an audit record is written; it never exercises a real destructive call because the server service is stubbed.

## Rollback considerations
Delete the new file.

## Validation plan
| Target | Strategy | Command | Expected |
|---|---|---|---|
| `test_write_dangerous_audit.py` | Unit (parametrized, 13 tools) | `uv run pytest tests/mcp_servers -v` | Pass |
| Format/lint | Static | `uv run ruff format`, `ruff check` | Clean |

## Completion criteria
- The parametrized test fails if any of the 13 WRITE_DANGEROUS tools lacks an audit record on its hosting server.
- The completeness test fails if the parametrized set drifts from `config/agent.toml` `[tool_safety_tiers]`.

## Out of Scope
- The rag-pipeline-mcp success/failure assertions — covered by the companion row (`test_rag_pipeline_server_endpoints.py`).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Create `tests/mcp_servers/test_write_dangerous_audit.py` with parametrization + completeness check | Completed | 20261112-122123 | 20261112-123959 | new file tests/mcp_servers/test_write_dangerous_audit.py; 14 tests (13 parametrized + completeness) passed |
| 2 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261112-123959 | 20261112-040527 | pytest tests/mcp_servers: 2619 passed, 3 skipped; ruff format/check clean |

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
- **Requirement ID**: `REQ-002` — parametrized cross-server audit coverage plus completeness against `config/agent.toml`.
- **Source issue**: issues/20261109-113023_adrrev011_mcp-audit-auth-adr.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261111-095422_adrrev011_mcp-audit-auth-adr.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261111-231122
- **Related target files**: `tests/mcp_servers/test_write_dangerous_audit.py`