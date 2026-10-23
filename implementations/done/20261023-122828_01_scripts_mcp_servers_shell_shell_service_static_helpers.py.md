## Goal
Add a pure, stateless helper that builds a shell command's environment from an explicit key allowlist and removes secret-shaped variables (`REQ-001`, `REQ-002`).

## Scope
- Add constants for the base keys and the secret rule, `is_secret_env_key()` (new) and `build_command_env()` (new) to this module.
- No change to existing helpers (`init_sandbox`, `make_preexec`, `validate_shell_security`).

## Assumptions
- The module is 8651 bytes, so adding about 1.5 KB stays under the 16384-byte module-size gate.
- Allowlisted commands need only `HOME`, `USER`, `LOGNAME`, `SHELL`, `LANG`, `LC_*`, `TMPDIR`, `TMP`, `TEMP` and `PATH` (plan UNK-01, verified during validation).

## Design decisions
- The helper is a pure function of its arguments (base mapping, configured `PATH`, filtered `req.env`) so it is unit-testable without a subprocess; the module docstring already states its helpers have no instance state.
- Secret detection is word-segment based, not substring based, so "TOKENIZERS_PARALLELISM" is kept while `GITHUB_TOKEN` and `MCP_*` are dropped.

## Alternatives considered
- Substring match on `TOKEN`: rejected, it drops "TOKENIZERS_PARALLELISM" and similar harmless names.
- Keep `os.environ.copy()` and only denylist secrets: rejected, a denylist misses new credential names; an allowlist fails closed.

## Implementation
### Target file
`scripts/mcp_servers/shell/shell_service_static_helpers.py`

### Procedure
1. Add module-level constants `_BASE_ENV_KEYS` (new) (exact names), `_BASE_ENV_PREFIXES` (new) (`LC_`) and `_SECRET_ENV_SEGMENTS` (new) (`TOKEN`, "SECRET", `PASSWORD`, "PASSWD", "CREDENTIAL", "CREDENTIALS") (new).
2. Add `is_secret_env_key(key: str) -> bool` (new): true when the upper-cased key starts with `MCP_`, has a `_`-delimited segment in the secret set, or has segment `API` immediately followed by `KEY` (also the single segment "APIKEY").
3. Add `build_command_env(base_env: Mapping[str, str], path: str, req_env: Mapping[str, str]) -> dict[str, str]` (new): copy base keys, set `PATH`, merge `req_env`, then drop every key for which `is_secret_env_key` (new) is true.
4. Document both functions with the repository's docstring format and keep the module docstring header unchanged.

### Method
- Base copy: iterate "base_env" and keep a key when it is in `_BASE_ENV_KEYS` (new) or starts with a prefix in `_BASE_ENV_PREFIXES` (new).
- Merge order matches the current code (`base | {"PATH": path} | req_env`), so a `req.env` entry can still override `PATH` (plan UNK-03, existing behavior kept).
- Final pass removes secret-shaped keys from the merged result, so neither `req_env` nor an allowlist can re-introduce them.

### Details
- Segment split: `key.upper().split("_")`; `API`+`KEY` is checked on adjacent segments.
- Return a new `dict`; never mutate "base_env" (callers pass `os.environ`).
- Reference only: `scripts/agent/http_lifecycle_command_validator.py` `_DEFAULT_ALLOWED_ENV_VARS` lists what the server process receives; it is not modified.

## Compatibility considerations
- Public module-level names are added only; the service import list in `shell_service.py` changes in the separate service row.
- Commands lose `LLMAGENT_*` variables and `SHELL`-less environments are unchanged because `SHELL` stays in the base list.

## Security considerations
- Core purpose of the change: stop MCP Bearer tokens and `GITHUB_TOKEN` reaching model-chosen commands; no secret value may be logged or asserted in tests (use obviously fake values).

## Rollback considerations
- N/A: revert the commit; the helper is additive and unused until the service row lands.

## Validation plan
- Unit tests in `tests/mcp_servers/shell/test_shell_command_env.py` cover keys kept, secrets dropped, `LC_*`, "TOKENIZERS_PARALLELISM", and merge order.
- `uv run pytest tests/mcp_servers/shell`, `uv run ruff check scripts/mcp_servers/shell`, `uv run mypy`, `uv run bandit -r scripts/mcp_servers/shell`, `uv run python tools/check_module_size.py`.

## Completion criteria
- `build_command_env()` (new) returns only base keys, `PATH` and filtered `req_env` entries, and never a secret-shaped key.
- Module-size gate and lint, type and security checks pass.

## Out of Scope
- Wiring the helper into `ShellService.run_command()` (separate row).
- Pinning `PATH` against `req.env` override (plan UNK-03).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the constants, `is_secret_env_key()` (new) and `build_command_env()` (new) per Implementation > Procedure/Method/Details | Completed | 20261023-125402 | 20261023-125402 | implemented and validated per plan batch (targeted shell tests, full suite 9713 passed) |
| 2 | Add or update tests per Validation plan (`tests/mcp_servers/shell/test_shell_command_env.py`, tracked in its own document) | Completed | 20261023-125402 | 20261023-125402 |  |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261023-125402 | 20261023-125402 |  |

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
- **Requirement ID**: `REQ-001` (minimal base environment), `REQ-002` (drop secret-shaped keys), `REQ-003` (keep `req.env` behavior)
- **Source issue**: issues/20261023-114000_mcpstart001_shell-sandbox-commands-inherit-all-mcp-auth-tokens-and-github_token.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261023-114629_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261023-122828
- **Related target files**: scripts/mcp_servers/shell/shell_service_static_helpers.py