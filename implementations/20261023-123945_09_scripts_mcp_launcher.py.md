## Goal
Make the development launcher resolve a server key without importing any server module, then restrict config and import only the chosen server (`REQ-004`).

## Scope
- Replace `discover_servers()` (lines 27-65) with a static, `ast`-based scan; update `main()` accordingly.
- Keep `port_is_responding()` and the `--force` guard.

## Assumptions
- Server classes declare `server_name`, `own_config_file`, `app_module` (and for mdq `server_key`) as string literals (verified for all ten).
- Keys stay identical to today: `server_key` if present, else `server_name` without the `-mcp` suffix.
- `tools/check_docstrings_baseline.txt` grandfathers this file's module docstring as "missing separator"; leave the docstring format unchanged.

## Design decisions
- Scan `scripts/mcp_servers/**/*_server.py` with `ast` for classes whose base is `MCPServer`, reading class-level string assignments with `ast.literal_eval`.
- Apply `ConfigLoader.restrict_to(meta.own_config_file)` before `importlib.import_module(meta.module)`, so only the chosen server's config can be read in that process.

## Alternatives considered
- Keep import-based discovery and only warn: rejected, `--list` would still run every module's import-time side effects (log files, database probes).

## Implementation
### Target file
`scripts/mcp_launcher.py`

### Procedure
1. Add a frozen dataclass `ServerMeta` (new) with `key`, `module`, `class_name`, `own_config_file`, `http_port` and a function `discover_server_metadata()` (new) returning `dict[str, ServerMeta]` from the static scan (module path derived from the file path relative to `scripts/`).
2. `--list` prints the sorted keys from the static scan and imports no server module.
3. Launch path: look up the key, build `ServerMeta` (new), call `ConfigLoader.restrict_to(meta.own_config_file)`, import the module with `importlib.import_module`, get the class with `getattr`, instantiate, run the existing port-collision guard with `instance.http_port`, then `instance.run_http()`.
4. Remove the now unused `inspect` and `pkgutil` imports; import `MCPServer` only under `TYPE_CHECKING` if still needed for annotations.

### Method
- Resolve the scripts directory from `Path(__file__).resolve().parent`.
- Skip files that fail to parse with a warning on stderr instead of aborting discovery.

### Details
- Evidence: `scripts/mcp_launcher.py:27-65` imports every `mcp_servers.*` module (including for `--list`); no test exists for the launcher today.

## Compatibility considerations
- Command-line interface and keys are unchanged; `--list` becomes side-effect free.

## Security considerations
- Strengthens ADR-002 config isolation: a server process can no longer read another server's configuration, including its token and policy settings, through package imports or ahead of the restriction.

## Rollback considerations
- N/A: revert the commit.

## Validation plan
- `tests/mcp_servers/test_mcp_launcher.py` (tracked in its own document), `uv run pytest tests/mcp_servers tests/agent tests/tools`, `uv run ruff check`, `uv run mypy`, `uv run bandit -r scripts/mcp_servers`, `uv run python tools/check_docstrings.py`, `uv run python tools/check_module_size.py`, `lint-imports`.

## Completion criteria
- `--list` imports no server module, the ten keys match the previous output, and launching a key restricts config before importing only that module.

## Out of Scope
- Changing how binaries are built
- Server module contents

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the static discovery and launch path per Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan (`tests/mcp_servers/test_mcp_launcher.py`, tracked in its own document) | Pending | — | — | |
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
- **Requirement ID**: `REQ-004` (static discovery; import and restrict only the chosen server)
- **Source issue**: issues/20261023-114103_mcpstart004_server-modules-load-config-before-isolation-and-package-init-imports-sibling-servers.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261023-115449_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261023-123945
- **Related target files**: scripts/mcp_launcher.py
