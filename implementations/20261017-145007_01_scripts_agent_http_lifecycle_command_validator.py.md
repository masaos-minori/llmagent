## Goal

Make `CommandValidator.filter_env` default-deny: a subprocess MCP server inherits only the
variables listed in a new `_DEFAULT_ALLOWED_ENV_VARS` allowlist plus its own configured `env`,
and a blocked protected-var override is logged by key only, never by value.

## Scope

- `scripts/agent/http_lifecycle_command_validator.py`: add the `_DEFAULT_ALLOWED_ENV_VARS`
  module constant; rewrite `filter_env` (row 1 of the Plan's `Implementation Target Files`).
- Update the `filter_env` docstring to state the model, the allowed variables, the excluded
  variables, and the server-`env` route for a variable outside the allowlist.
- Nothing else. `scripts/agent/http_lifecycle.py` (the only caller) and
  `scripts/shared/mcp_config.py` are Reference Files and stay unmodified.

## Assumptions

- `filter_env` has exactly one production caller, `scripts/agent/http_lifecycle.py:275`
  (`REQ-006` boundary). Verified 2026-10-17 by `grep -rn filter_env scripts/`.
- The shipped launch mode is `/opt/llm/bin/mcp_*` binaries; every `[mcp_servers.*]` section in
  `config/agent.toml` sets `cmd = ["/opt/llm/bin/mcp_<name>"]` (Plan `UNK-04`).
- The shared-secret model requires the child to inherit its own `MCP_<NAME>_AUTH_TOKEN`
  (Plan `UNK-01`); the allowlist therefore carries the token pattern.

## Design decisions

- Allowlist is a module-level `frozenset[str]` of `fnmatch` patterns, matching the shape of the
  imported `_ENV_KEY_DENYLIST` and the style of `_DEFAULT_ALLOWED_COMMANDS`. Patterns, not exact
  names, so a new server's token is covered without editing this file.
- Order of operations inside `filter_env`: (1) `None` passthrough; (2) build `result` from the
  parent environment keeping only allowlist-matched keys; (3) merge the server `env` applying the
  existing `_ENV_KEY_DENYLIST` block and the protected-var block, both logging key only.
  Server-configured entries are merged even when not allowlisted — they are admin-controlled.
- Excluded from the allowlist and documented in the docstring: `LLMAGENT_BINARY_DIR` and
  `LLMAGENT_STRICT_COMMAND` (parent-only controls the child never reads), unrelated parent
  credentials, proxy variables (a proxy URL can embed credentials), and interpreter toolchain
  variables (`XDG_*`, `UV_*`, `NPM_*`).

## Alternatives considered

- Per-server allowlists derived from the server key: rejected, `filter_env` receives only
  `cfg.env`, and passing `server_key` or `cfg.auth_token` would change the caller in
  `scripts/agent/http_lifecycle.py`, which `REQ-006` forbids.
- Injecting each server's resolved `cfg.auth_token` into the child env from the parent: rejected
  for the same caller-change reason; recorded in the Plan as a follow-up candidate.
- Keeping `dict(os.environ)` and only fixing the log line: rejected, it leaves the leak the
  issue is about (`REQ-001`).

## Implementation
### Target file
`scripts/agent/http_lifecycle_command_validator.py`
### Procedure
1. Add `_DEFAULT_ALLOWED_ENV_VARS: frozenset[str]` next to `_DEFAULT_PROTECTED_ENV_VARS` with the
   finalized contents recorded in the Plan's Design section: `PATH`, `HOME`, `USER`, `LOGNAME`,
   `SHELL`, `TMPDIR`, `TMP`, `TEMP`, `LANG`, `LC_*`, `MCP_*_AUTH_TOKEN`, `GITHUB_TOKEN`,
   `LLMAGENT_CONFIG_DIR`, `LLMAGENT_SUDACHI_DICT`.
2. Rewrite `filter_env` so the inherited copy is allowlist-filtered instead of a full
   `dict(os.environ)` copy; keep the denylist and protected-var handling of the server `env`.
3. Change both warning calls to log the key only.
4. Rewrite the method docstring for the default-deny contract.
### Method
Edit in place; no new module, no new public symbol other than the constant. The signature
`filter_env(self, env: dict[str, str] | None) -> dict[str, str] | None` is unchanged.
### Details
- Allowlist matching uses the same `fnmatch.fnmatch(key, pattern)` form already used for
  `_ENV_KEY_DENYLIST` in this file, so the two filters read the same way.
- A parent variable that is allowlisted but absent is simply not copied; do not insert empty
  placeholders.
- The protected-var set still blocks a server `env` from overriding `PATH`, `HOME`, `USER`,
  `PYTHONPATH`, `LD_LIBRARY_PATH`; those three are also allowlisted for inheritance, which is
  intentional (inherited from the parent, not overridable per server).

## Compatibility considerations

- Behavioral change for every subprocess server: variables outside the allowlist disappear from
  the child environment. Verified against the shipped config by the Plan's probe (10/10 servers
  import successfully) and enforced going forward by row 3's integration gate.
- `scripts/mcp_servers/shell/shell_service.py:270` builds the `shell_run` command environment as
  `os.environ.copy() | {"PATH": self._path} | filtered_env`; the shell server's own inherited
  environment is now the allowlist, so shell commands see only those variables plus the
  configured `PATH` and the request-supplied env. Documented in row 4.

## Security considerations

- Closes the leak: unrelated parent credentials (`AWS_*`, `OPENAI_API_KEY`, cookies, generic
  tokens) no longer reach any MCP subprocess, and no secret value is written to the log.
- Residual, accepted in the Plan: the `MCP_*_AUTH_TOKEN` wildcard and `GITHUB_TOKEN` give every
  subprocess server the other servers' tokens. Narrower than `dict(os.environ)`, not fixed here.
- Defense in depth: `LD_PRELOAD`, `LD_LIBRARY_PATH`, `PYTHONPATH` are stripped from the merged
  server `env` even though the config loader already rejects them (`AC-005`).

## Rollback considerations

Single commit, single file: `git checkout -- scripts/agent/http_lifecycle_command_validator.py`
restores default-ALLOW behavior. No persisted state and no config change are involved, so no
data rollback is needed.

## Validation plan

- `pytest tests/agent/test_http_lifecycle_command_validator.py` — unit contract for the rewrite
  (row 2).
- `pytest tests/agent/test_http_lifecycle_env_allowlist_integration.py` — allowlist sufficiency
  against the shipped config with a real child process (row 3).
- `uv run ruff format` / `uv run ruff check`, `uv run mypy --no-namespace-packages scripts/`,
  `uv run lint-imports`, full `uv run pytest -q -p no:randomly tests/`.

## Completion criteria

- `filter_env` returns only allowlisted parent variables plus the merged server `env`;
  `filter_env(None)` still returns `None` (`AC-004`).
- Neither warning emits a value (`AC-002`).
- `LD_PRELOAD`, `LD_LIBRARY_PATH`, `PYTHONPATH` never appear in the result (`AC-005`).
- Rows 2 and 3's tests pass, and the full validation sequence is green.

## Out of scope

- Command validation, subprocess launch, health polling, process termination (`REQ-006`).
- `config/agent.toml` and every `config/*_mcp_server.toml` (Reference Files).
- Per-server token isolation, and the `check_docstrings.py` findings tracked separately.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add `_DEFAULT_ALLOWED_ENV_VARS` with the finalized set | Pending | — | — | |
| 2 | Rewrite `filter_env` (default-deny, key-only logging, `None` passthrough) | Pending | — | — | |
| 3 | Update the `filter_env` docstring | Pending | — | — | |
| 4 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |

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
- **Requirement ID**: `REQ-001`, `REQ-002`, `REQ-003`, `REQ-004`, `REQ-005`
- **Source issue**: `issues/20261016-093044_mcp004_filter_env_secret_logging_env_leak.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261016-110959_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261017-145007
- **Related target files**: `scripts/agent/http_lifecycle_command_validator.py`
