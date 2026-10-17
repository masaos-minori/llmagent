## Goal

Add the permanent gate that keeps the default-deny allowlist sufficient: a new integration test
file that (a) checks every `${ENV:...}` variable in the shipped config against
`_DEFAULT_ALLOWED_ENV_VARS`, and (b) starts a real child process for every configured subprocess
server using the environment `filter_env` returns.

## Scope

- `tests/agent/test_http_lifecycle_env_allowlist_integration.py` (row 3 of the Plan's
  `Implementation Target Files`) — new file; `tests/agent/` already exists.
- Reads `config/agent.toml` and `config/*_mcp_server.toml` as evidence; it does not modify them.

## Assumptions

- `tests/conftest.py` already sets all ten `MCP_*_AUTH_TOKEN` variables, so the parent environment
  inside the test suite carries them (`tests/conftest.py:38-46`).
- CI runs the whole suite (`uv run pytest -v`, `.github/workflows/ci.yml:52,55`), so an
  `@pytest.mark.integration` test is not deselected.
- `PYTHONPATH` is denylisted, so the child must resolve `mcp_servers.*` from the working directory:
  `python -c` puts cwd at `sys.path[0]`, so `cwd=scripts/` is the launch shape.
- Entry modules are the `if __name__ == "__main__":` files under `scripts/mcp_servers/`; the repo
  contains no binary-name-to-module build manifest, so the mapping is declared in this test file.

## Design decisions

- Two gates in one file: a cheap static alignment gate, and a real-child startup gate that proves
  the filtered environment is sufficient, not merely narrower.
- A negative control is mandatory: without it the startup gate could pass vacuously. It removes
  every `MCP_*_AUTH_TOKEN` from the parent and asserts the child import fails.
- The parent environment is controlled with `patch.dict(os.environ, ..., clear=True)` plus an
  explicit `PATH`/`HOME`/token set, so the gate does not depend on the developer's or CI's own
  environment beyond those two values.

## Alternatives considered

- Runtime observation on the deployment host: impossible here (`/opt/llm/bin` is empty, no MCP port
  listens), so the gate runs against the same server modules in source form (Plan `UNK-05`).
- Importing the entry modules inside the test process instead of a child: rejected, it would not
  exercise the filtered environment at all.
- Deriving the entry module from the binary name in `cmd`: rejected, the naming is not derivable
  (`file_read` -> `mcp_servers.file.read_server`), so an explicit table with a completeness guard
  is used instead.

## Implementation
### Target file
`tests/agent/test_http_lifecycle_env_allowlist_integration.py`
### Procedure
1. Module constants: `_REPO = Path(__file__).resolve().parents[2]`, `_SCRIPTS = _REPO / "scripts"`,
   `_CONFIG = _REPO / "config"`, `_ENV_REF_RE = re.compile(r"\$\{ENV:([A-Za-z_][A-Za-z0-9_]*)\}")`,
   and `_SERVER_ENTRY_MODULES` mapping every `startup_mode = "subprocess"` key in
   `config/agent.toml` to its entry module (`shell` -> `mcp_servers.shell.shell_server`,
   `git` -> `mcp_servers.git.git_server`, `web_search` -> `mcp_servers.web_search.web_search_server`,
   `file_read`/`file_write`/`file_delete` -> `mcp_servers.file.{read,write,delete}_server`,
   `github` -> `mcp_servers.github.github_server`, `cicd` -> `mcp_servers.cicd.cicd_server`,
   `rag_pipeline` -> `mcp_servers.rag_pipeline.rag_pipeline_server`,
   `mdq` -> `mcp_servers.mdq.mdq_server`).
2. `test_config_env_refs_are_all_allowlisted`: scan the raw text of `config/agent.toml` and every
   `config/*_mcp_server.toml`, collect every `${ENV:VAR}` name, and assert each is matched by
   `_DEFAULT_ALLOWED_ENV_VARS` with `fnmatch`.
3. `test_allowlist_does_not_admit_denylisted_loader_vars`: assert `PYTHONPATH`, `LD_PRELOAD`,
   `LD_LIBRARY_PATH` match no allowlist pattern.
4. `test_server_key_mapping_covers_every_subprocess_server`: assert every subprocess server key in
   `config/agent.toml` has an entry in `_SERVER_ENTRY_MODULES` (fails loudly when a server is added
   without updating this gate).
5. `test_each_subprocess_server_starts_under_filtered_env` (`@pytest.mark.integration`): for each
   server, build `env = CommandValidator().filter_env(cfg.get("env", {}))` under a controlled parent
   environment, then `subprocess.run([sys.executable, "-c", "import <entry module>"], env=env,
   cwd=_SCRIPTS, timeout=120)` and assert returncode 0.
6. `test_missing_token_breaks_the_child_import` (negative control, same marker): same run with every
   `MCP_*_AUTH_TOKEN` removed from the parent, assert a non-zero returncode and that stderr names
   the missing variable.
### Method
New file, standard-library only plus `pytest` and `agent.http_lifecycle_command_validator`.
### Details
- The controlled parent environment is `{PATH, HOME} + the ten MCP tokens`; `filter_env` copies only
  what is both present and allowlisted, so the child receives exactly the allowlist intersection.
- Keep the child timeout generous (120 s) but assert the measured cost stays small: the ten imports
  took about 4 s in total during the 2026-10-17 probe.
- Importing an entry module is side-effect-light: each server binds its port only under
  `if __name__ == "__main__":`, and each computes its security posture at import without raising.

## Compatibility considerations

- Adds real subprocess starts to CI (about 4 s measured). No production code is touched.
- If a future server is added to `config/agent.toml` without a mapping entry, test 4 fails with an
  explicit message rather than silently skipping coverage.

## Security considerations

- This file is what prevents the default-deny allowlist from silently drifting out of sync with the
  config that depends on it (`REQ-007`, `AC-006`, `AC-007`).
- The negative control proves the gate can detect a missing allowlist entry.

## Rollback considerations

N/A: revert the commit — a new test file with no production coupling.

## Validation plan

- `uv run pytest tests/agent/test_http_lifecycle_env_allowlist_integration.py -v` — all pass.
- Mutation check: remove `MCP_*_AUTH_TOKEN` from `_DEFAULT_ALLOWED_ENV_VARS` locally and confirm
  tests 2 and 5 fail, then revert.
- `uv run ruff format` / `uv run ruff check`, `uv run mypy --no-namespace-packages scripts/`
  (test files are outside the mypy target), full `uv run pytest -q -p no:randomly tests/`.

## Completion criteria

- All six tests pass in the repository's normal test run, including under CI's `uv run pytest -v`.
- The negative control fails when an allowlist entry is removed (verified locally, then reverted).
- `AC-006` and `AC-007` are satisfied by named tests, not by manual inspection.

## Out of scope

- Changing `config/agent.toml` or any `config/*_mcp_server.toml` (Reference Files).
- Changing `_DEFAULT_ALLOWED_ENV_VARS` itself (row 1) — this file only asserts against it.
- Compiled-binary (`/opt/llm/bin/mcp_*`) startup, which cannot run on this host (Plan `UNK-05`).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Create the file with constants and the config-alignment gates | Pending | — | — | |
| 2 | Add the real-child startup gate and the negative control | Pending | — | — | |
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
- **Requirement ID**: `REQ-001`, `REQ-005`, `REQ-007`
- **Source issue**: `issues/20261016-093044_mcp004_filter_env_secret_logging_env_leak.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261016-110959_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261017-145007
- **Related target files**: `tests/agent/test_http_lifecycle_env_allowlist_integration.py`
