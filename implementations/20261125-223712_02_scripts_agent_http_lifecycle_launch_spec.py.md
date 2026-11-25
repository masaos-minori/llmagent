## Goal

Create the single immutable launch specification the subprocess launcher consumes: validated absolute `argv[0]`, fixed process options, and the minimal per-server environment (REQ-001 one construction site, REQ-006 minimal environment, REQ-007 audit records key names only).

## Scope
**Release unit**: R1-launch-spec

## Assumptions

- The module is agent-layer and imports only `shared.mcp_config` types, consistent with the import-layer contract (Plan Design).
- The derived token names are exactly `MCP_<KEY.upper()>_AUTH_TOKEN` and `MCP_<KEY.upper()>_CONTROL_TOKEN`; every shipped child config uses those names (Plan Design, `config/github_mcp_server.toml:56,72`).
- The parent's `PATH`, `HOME`, `USER` stay parent-controlled, as the existing protected-variable rule already treats them (Plan Assumptions).

## Design decisions

- `LaunchSpec` (new) is a frozen dataclass whose only escape into `Popen` is `popen_kwargs()` (new): `start_new_session=True`, `stdout=subprocess.DEVNULL`, the caller-supplied `stderr` handle, and `env`. `shell`, `preexec_fn`, and `cwd` are never present, so no caller can add them (REQ-001, REQ-002).
- `argv` is a `tuple[str, ...]` with `argv[0]` the path `CommandValidator.validate` returned, and the environment is stored as a `tuple[tuple[str, str], ...]` so the frozen instance holds no mutable container (REQ-001).
- `build_launch_spec` (new) is the only construction site: it takes `server_key`, the `McpServerConfig`, the validated path, the captured file identity, and the stderr handle, and it is the only place that reads `cfg.env` and `cfg.credential_env`.
- `build_child_env` (new) returns a `dict[str, str]` and never returns `None`: fixed runtime set, the server's own two derived tokens, the `credential_env` names, then the configured `env` merged with the existing `_ENV_KEY_DENYLIST` and protected-variable rules (REQ-006).
- The spec carries `expected_identity` (new) (the `(st_dev, st_ino)` pair captured at validation) and `verify_identity()` (new) re-checks it against `os.stat` immediately before the spawn, returning a `StartupFailure` reason on mismatch (REQ-003).

## Alternatives considered

Passing a `dict` of Popen kwargs through the config was rejected: it is the exact override channel REQ-002 removes. A mutable spec with a builder class was rejected: a frozen dataclass plus one function makes the single-construction-site rule checkable by reading the type.

## Implementation
### Target file
`scripts/agent/http_lifecycle_launch_spec.py` (new)
### Procedure
Write the new module: the frozen spec, the single builder, the minimal-environment builder, and the identity re-check helper.

### Method
- Define `LaunchSpec` (new) with `server_key`, `argv`, `env_items` (new), `stderr`, `expected_identity` (new), and the `popen_kwargs()` and `verify_identity()` methods.
- Define `build_launch_spec` (new): validate that `argv[0]` is absolute, that every argument is a `str`, and that `server_key` passes `validate_server_key` (row 1) before any path is derived.
- Define `build_child_env` (new): start from the fixed runtime set (`PATH`, `HOME`, `USER`, `LOGNAME`, `SHELL`, `TMPDIR`, `TMP`, `TEMP`, `LANG`, `LC_*`, `LLMAGENT_CONFIG_DIR`, `LLMAGENT_SUDACHI_DICT`) read from the parent, add the two derived tokens for `server_key`, then each name in `cfg.credential_env`, then merge `cfg.env` under the existing denylist and protected-variable rules.
- Add the launch audit log line: `logger.info` naming the server key and the sorted environment key names only.

### Details
- Import `_ENV_KEY_DENYLIST` and `validate_server_key` from `shared.mcp_config`; import `StartupFailure` from `.http_lifecycle_errors` for the identity-mismatch reason.
- `LC_*` admission keeps the current `fnmatch` semantics used by `CommandValidator.filter_env`, so locale variables behave unchanged.
- A `credential_env` name that is absent from the parent environment is simply not added; a name matching the denylist is rejected at parse time (row 1), not silently dropped here.
- No `cwd`, `shell`, or `preexec_fn` keyword is ever emitted; close_fds and text keep their subprocess defaults.

## Compatibility considerations

New module with no existing consumers; rows 3 and 4 wire it in the same release unit. `CommandValidator.filter_env` is replaced by `build_child_env` (new), so the two test files that call it (rows 9 and 11) change in the same unit.

## Security considerations

The environment is always an explicit minimal dict, so `Popen(env=None)` full-inheritance cannot occur (REQ-006, AC-3). The audit line never contains a value, which is what AC-3 asserts by log capture (REQ-007).

## Rollback considerations

N/A: revert the commit; the module has no consumer until rows 3 and 4 land.

## Validation plan

- `uv run pytest tests/agent/test_http_lifecycle_launch_spec.py`
- `uv run mypy scripts/agent/http_lifecycle_launch_spec.py`
- `uv run ruff format` and `uv run ruff check`
- `uv run bandit -r scripts/agent/http_lifecycle_launch_spec.py -c pyproject.toml`

## Completion criteria

- `LaunchSpec` (new) is frozen, cannot express `shell`, `preexec_fn`, `cwd`, `stdout`, `start_new_session=False`, or an `env` override, and `popen_kwargs()` is the only keyword source.
- `build_child_env` (new) returns a `dict` for every input, including `cfg.env is None`, and contains only the fixed runtime set plus that server's own tokens and declared `credential_env` names.
- The audit log line contains key names and no value.

## Out of Scope

- Calling `Popen` and releasing resources (row 4).
- Resolving and confining the executable (row 3).
- The `credential_env` values in `config/agent.toml` (row 6).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | Execute after the row 8 Phase 1 tests are in place (REQ-009) |
| 2 | Confirm the Phase 1 test additions from row 8 fail before this change and pass after it | Pending | — | — | Tests-first order per Plan Phase 1 |
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
- **Requirement ID**: REQ-001 (immutable launch spec with one construction site), REQ-006 (minimal per-server environment), REQ-007 (audit records key names only)
- **Source issue**: issues/20261119-145304_cliplc006_mcp-launch-spec-credentials.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261125-111909_cliplc006_mcp-launch-spec-credentials.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261125-223712
- **Related target files**: `scripts/agent/http_lifecycle_launch_spec.py`
