## Goal
Prove `mcp_launcher.py` discovers servers statically, `--list` imports no server module, and launching a key restricts config before importing only that server (`REQ-005`).

## Scope
- New test module only; `mcp_launcher.py` has no tests today.

## Assumptions
- `scripts/` is on `sys.path` in tests (conftest), so `import mcp_launcher` works; `--list` runs in a subprocess to inspect `sys.modules` cleanly.

## Design decisions
- Stub `importlib.import_module`, `ConfigLoader.restrict_to` and `port_is_responding` for the launch test so no server starts.

## Alternatives considered
- Start a real server: rejected, slow and port dependent.

## Implementation
### Target file
`tests/mcp_servers/test_mcp_launcher.py` (new)

### Procedure
1. Test that the static scan returns the ten expected keys (same keys as the previous import-based output) with the expected `own_config_file` and module path.
2. Subprocess test: run the launcher `--list` and assert no `mcp_servers.*_server` module is in `sys.modules` afterwards.
3. Launch test: patch `ConfigLoader.restrict_to`, `importlib.import_module` (returning a fake module with a fake class) and `port_is_responding`; assert `restrict_to` runs before `import_module`, only the chosen module is imported, and `run_http` is called once.
4. Test the `--force` guard and the unknown-key exit code 1.

### Method
- Set `sys.argv` with `monkeypatch` and call `mcp_launcher.main()`; catch `SystemExit` for the error cases.

### Details
- Reference only: `scripts/mcp_launcher.py` current CLI (`--list`, `<server_key>`, `--force`).

## Compatibility considerations
- Test-only.

## Security considerations
- No secrets.

## Rollback considerations
- N/A: revert the commit.

## Validation plan
- `uv run pytest tests/mcp_servers/test_mcp_launcher.py`, `uv run ruff check tests/mcp_servers`, `uv run mypy`.

## Completion criteria
- All launcher cases pass on the implemented change.

## Out of Scope
- Starting real servers

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
- **Requirement ID**: `REQ-005` (launcher tests), covering `REQ-004`
- **Source issue**: issues/20261023-114103_mcpstart004_server-modules-load-config-before-isolation-and-package-init-imports-sibling-servers.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261023-115449_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261023-123945
- **Related target files**: tests/mcp_servers/test_mcp_launcher.py
