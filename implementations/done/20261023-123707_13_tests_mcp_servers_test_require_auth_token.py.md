## Goal
Prove the helper behaves as specified and that all ten server modules refuse an empty token at import (`REQ-006`).

## Scope
- New test module only.

## Assumptions
- A fresh interpreter is needed per module because server modules attach middleware at import and are cached in `sys.modules`.
- `shell` fails earlier on hosts without the `firejail` binary, so that case is skipped when `shutil.which("firejail")` is missing.

## Design decisions
- Use `subprocess.run([sys.executable, "-c", "import <module>"])` with a minimal environment: all ten token variables set to `test-token` except the one under test, `PYTHONPATH` set to `scripts`, and `LLMAGENT_LOG_DIR` set to `tmp_path`.

## Alternatives considered
- `importlib.reload` in-process: rejected, it leaks module state and config restrictions into other tests.

## Implementation
### Target file
`tests/mcp_servers/test_require_auth_token.py` (new)

### Procedure
1. Unit tests for `require_auth_token()` (new): raises `RuntimeError` for `""` and `None`; returns a non-empty token unchanged; message contains the label and variable name.
2. Parametrized subprocess test over the ten (module, variable) pairs asserting a non-zero exit and `auth_token is empty` in stderr.
3. Positive control: the same subprocess import with all variables non-empty exits 0 for one server.

### Method
- Mark the shell case with `pytest.mark.skipif` on `shutil.which("firejail") is None`.

### Details
- Reference only: `tests/conftest.py` (token and firejail setup for in-process tests), `tests/mcp_servers/shell/test_shell_server_auth.py` (subprocess pattern, lines 53-60).

## Compatibility considerations
- Test-only.

## Security considerations
- Fake token values only; assert on messages that contain variable names, never values.

## Rollback considerations
- N/A: revert the commit.

## Validation plan
- `uv run pytest tests/mcp_servers/test_require_auth_token.py`, `uv run ruff check tests/mcp_servers`, `uv run mypy`.

## Completion criteria
- All ten refusal cases and the helper tests pass with the implemented change and the refusal cases fail on the pre-change code for the four target servers.

## Out of Scope
- Replacing the six existing inline checks

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the test module per Implementation > Procedure (tests are this row's change) | Completed | 20261023-130219 | 20261023-130219 | implemented; tests/mcp_servers 2468 passed; one additional test file discovered and added to the Plan (row 25); full suite run at the end of the batch |
| 2 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261023-130219 | 20261023-130219 |  |

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
- **Requirement ID**: `REQ-006` (helper test and all-ten refusal test), covering `REQ-001`, `REQ-002`
- **Source issue**: issues/20261023-114044_mcpstart003_four-mcp-servers-start-without-authentication-when-auth_token-is-empty.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261023-115211_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261023-123707
- **Related target files**: tests/mcp_servers/test_require_auth_token.py