## Goal
Use the new helper in `ShellService.run_command()` so a command no longer inherits the server's environment (`REQ-001`, `REQ-002`).

## Scope
- Replace the environment construction at `shell_service.py:269-270` and update the import from `shell_service_static_helpers`.
- No change to `_filter_env`, argv checking, cwd resolution, limits or audit logging.

## Assumptions
- `run_command()` still builds `filtered_env = self._filter_env(req.env)` first; verified in the current source (lines 269-270).
- The file is 13523 bytes, so a two-line change stays under the 16384-byte module-size gate.

## Design decisions
- Call `build_command_env(os.environ, self._path, filtered_env)`; the helper owns the allowlist so the service keeps no environment policy.

## Alternatives considered
- Inline the allowlist in `run_command()`: rejected, it would grow a size-gated module and duplicate logic that needs its own unit tests.

## Implementation
### Target file
`scripts/mcp_servers/shell/shell_service.py`

### Procedure
1. Import `build_command_env` (new) from `.shell_service_static_helpers` in the existing import block (`from .shell_service_static_helpers import (...)`).
2. In `run_command()` replace `env = os.environ.copy() | {"PATH": self._path} | filtered_env` with `env = build_command_env(os.environ, self._path, filtered_env)`.
3. Update the comment above it ("inherit current env") to describe the allowlisted environment.

### Method
- Keep `filtered_env = self._filter_env(req.env)` unchanged so `env_allowlist` / `env_denylist` semantics are preserved.
- Keep the `os` import: it is still used for `os.environ`.

### Details
- Evidence: `shell_service.py:269-270`; probe showed `GITHUB_TOKEN`, `MCP_GITHUB_AUTH_TOKEN`, `MCP_SHELL_AUTH_TOKEN` visible to a `python3` command.
- Reference only: `subprocess_runner.py` builds argv and does not scrub the environment.

## Compatibility considerations
- Command environments shrink to the documented base keys plus filtered `req.env`; no request or response schema changes.

## Security considerations
- Core purpose of the change: stop MCP Bearer tokens and `GITHUB_TOKEN` reaching model-chosen commands; no secret value may be logged or asserted in tests (use obviously fake values).

## Rollback considerations
- N/A: revert the commit (single-function change).

## Validation plan
- `run_command` regression tests in `tests/mcp_servers/shell/test_shell_command_env.py` and the existing `tests/mcp_servers/shell/test_shell_mcp_service.py` (51 tests).
- `uv run pytest tests/mcp_servers/shell`, `uv run ruff check scripts/mcp_servers/shell`, `uv run mypy`, `uv run bandit -r scripts/mcp_servers/shell`, `uv run python tools/check_module_size.py`.

## Completion criteria
- With token variables set in the server process, a `python3` command printing environment keys shows none of them.
- All existing shell tests pass; module-size gate passes.

## Out of Scope
- Helper implementation (separate row)
- Deployment: binaries are rebuilt in the deploy step of the Plan, not here.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the import and the `run_command()` change per Implementation > Procedure/Method/Details | Completed | 20261023-125403 | 20261023-125403 | implemented and validated per plan batch (targeted shell tests, full suite 9713 passed) |
| 2 | Add or update tests per Validation plan (`tests/mcp_servers/shell/test_shell_command_env.py`, tracked in its own document) | Completed | 20261023-125403 | 20261023-125403 |  |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261023-125403 | 20261023-125403 |  |

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
- **Requirement ID**: `REQ-001` (no wholesale `os.environ` copy), `REQ-002` (secrets never reach the command), `REQ-003` (filtering unchanged)
- **Source issue**: issues/20261023-114000_mcpstart001_shell-sandbox-commands-inherit-all-mcp-auth-tokens-and-github_token.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261023-114629_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261023-122828
- **Related target files**: scripts/mcp_servers/shell/shell_service.py