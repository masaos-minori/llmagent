## Goal

Add the missing test for ADR-002 INV-03: each of the ten MCP servers starts with a config directory that holds only its own config file (AAL-031).

## Scope
**Release unit**: N/A: not part of a release unit

Test-only change in one existing file; the file is also edited by another Plan (compatible, a different test function). Stop and report if a server needs a production change.

## Assumptions

- The existing `test_a_server_module_executes_once_under_python_m` already asserts only the own config file is loaded, but with the repository config directory present (`tests/mcp_servers/test_config_isolation_import.py:254`, re-read in Step 3a).
- Whether a server's posture gate reads another file is unknown (Plan UNK-02): the test settles it; a failure is reported, not worked around.

## Design decisions

- A new parametrized test over `_ONCE_SERVERS` that points the config directory at a temporary directory holding only the server's own file.
- Reuse `_run` and `_ONCE_RECORD`; only the config directory differs.

## Alternatives considered

Loop over servers inside one test: rejected, a parametrized test names the failing server.

## Implementation
### Target file
`tests/mcp_servers/test_config_isolation_import.py`

### Procedure
1. Read how `isolated_subprocess_env` (`tests/conftest.py:440`) sets the config directory.
2. Copy only `config/<config_file>` for the server into `tmp_path`, point the config directory there through the fixture's env mechanism.
3. Run `_ONCE_RECORD` for each `_ONCE_SERVERS` entry; assert exit code 0, `config_loads == [config_file]`, and that the stubbed `uvicorn.Config` was reached.

### Method
- Keep the test marked as the existing one is (subprocess, no new marker unless the file already uses `integration`).
- Do not copy `agent.toml` or any sibling file.

### Details
- If a server fails, record which file it read, stop, and report the production change needed (Plan UNK-02).
- Mutation check: add a read of `agent.toml` to one server's startup temporarily, confirm failure, revert.
- Cite the new test in ADR-002's INV-03 row in procedure 08.

## Compatibility considerations

N/A: adds a test only; ten subprocess runs add some seconds, as the existing parametrized test does.

## Security considerations

N/A: no secret, permission, or input handling is touched; test fixtures use dummy tokens only.

## Rollback considerations

N/A: revert the commit.

## Validation plan

- `uv run pytest tests/mcp_servers/test_config_isolation_import.py -q`
- ruff and mypy on the file

## Completion criteria

- All ten parametrized cases pass with only the own config file present.
- The mutation makes the test fail.

## Out of Scope

- Any file other than the target file (and its companions, if any); any change under `scripts/` or `config/`.
- Approval text: no approver, date, or approval sentence is written.
- The AAL-032 invariant (INV-04), which waits for the AAL-030 wording decision.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Mutation-check the new test: break the invariant temporarily, confirm the test fails, revert the break | Pending | — | — | |
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
- **Requirement ID**: `REQ-003` (a server starts with only its own config file (ADR-002 INV-03)), `REQ-008` (no production change, every test mutation-checked)
- **Source issue**: issues/20261123-164658_gov006_restore-blocking-verification-rows.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261123-165432_gov006_restore-blocking-verification-rows.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261123-165833
- **Related target files**: `tests/mcp_servers/test_config_isolation_import.py`
