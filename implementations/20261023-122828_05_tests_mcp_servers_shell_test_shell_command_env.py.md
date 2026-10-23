## Goal
Add tests proving a shell command cannot observe token variables from the server process and that legitimate variables and `req.env` filtering still work (`REQ-005`).

## Scope
- New test module with helper unit tests and `run_command` environment tests; no change to existing test modules.

## Assumptions
- The sibling module `test_shell_mcp_service.py` shows the pattern: an autouse fixture patches `shutil.which` for firejail and `ShellService(ShellPolicy(...))` is built with a `tmp_path` cwd.
- `run_command` tests can use `python3 -c` with `sandbox_backend` as in sibling tests only if firejail is available; otherwise patch `SubprocessRunner.build_argv` to return argv unchanged (the probe ran under a nested firejail).

## Design decisions
- Test the helper directly for exhaustive key cases and use one real-subprocess `run_command` test for the end-to-end claim.
- Use obviously fake token values and assert on key names only.

## Alternatives considered
- Extend `test_shell_mcp_service.py`: rejected, that module is already large (51 tests) and a new focused module keeps the intent clear.

## Implementation
### Target file
`tests/mcp_servers/shell/test_shell_command_env.py` (new)

### Procedure
1. Create the module with the `from __future__ import annotations` header, the firejail `shutil.which` autouse fixture and a local `ShellPolicy` helper copied in shape from `_make_policy` (allowed command `python3`).
2. Add helper tests: base keys kept; "LC_ALL" kept; `MCP_GIT_AUTH_TOKEN`, `GITHUB_TOKEN`, `API_KEY`, "DB_PASSWORD" dropped; "TOKENIZERS_PARALLELISM" kept; `req_env` secret keys dropped; `PATH` set to the configured value; `req_env` `PATH` override preserved; input mapping not mutated.
3. Add a `run_command` test with `monkeypatch.setenv` of fake `MCP_SHELL_AUTH_TOKEN`, `MCP_GITHUB_AUTH_TOKEN` and `GITHUB_TOKEN`, running `python3 -c` that prints environment keys containing `TOKEN`, asserting none appear.
4. Add regression tests that `env_allowlist` and `env_denylist` still filter `req.env` before the secret pass.

### Method
- Use `pytest.mark.asyncio` as in `TestServiceStart` style tests of sibling modules.
- For the real-subprocess test, patch the sandbox wrapper so it does not depend on the host's firejail.

### Details
- Reference only: `tests/mcp_servers/shell/test_shell_mcp_service.py` (`_make_policy`, `_make_service`), `tests/mcp_servers/_auth_headers.py` (not needed here).

## Compatibility considerations
- Test-only; no production interface touched.

## Security considerations
- Fake values only; no real credentials in assertions or output.

## Rollback considerations
- N/A: revert the commit.

## Validation plan
- `uv run pytest tests/mcp_servers/shell/test_shell_command_env.py`, `uv run pytest tests/mcp_servers/shell`, `uv run ruff check tests/mcp_servers/shell`, `uv run mypy`.

## Completion criteria
- All listed cases pass against the implemented helper and service, and fail against the pre-change `os.environ.copy()` behavior.

## Out of Scope
- Changes to existing shell test modules.
- Agent-side environment filter tests.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the test module per Implementation > Procedure (tests are this row's change) | Pending | — | — | |
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
- **Requirement ID**: `REQ-005` (tests), covering `REQ-001`, `REQ-002`, `REQ-003`
- **Source issue**: issues/20261023-114000_mcpstart001_shell-sandbox-commands-inherit-all-mcp-auth-tokens-and-github_token.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261023-114629_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261023-122828
- **Related target files**: tests/mcp_servers/shell/test_shell_command_env.py
