## Goal

Confirm `tests/mcp_servers/test_config_isolation_import.py` still satisfies `REQ-002` — each MCP
server reads only its own configuration file — after the multi-main build, and make only the
minimal, necessary change. The multi-main build (`deploy/build_binaries.sh`) keeps the
`ENTRIES` shape (`module:final_name:cls:cfg`) and the per-server
`ConfigLoader.restrict_to(...)` before each server import, so the existing isolation tests keep
validating the same guarantee; this row verifies that rather than rewriting the test.

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions

- The ten MCP entries stay in `deploy/build_binaries.sh` `ENTRIES` with the
  `module:final_name:cls:cfg` shape (the agent is split off but the ten MCP rows are unchanged),
  so the test's `_entries()` parser still yields exactly the ten servers.
- Each MCP launcher still runs `restrict_to("${cfg}")` before `from ${module} import ${cls}`, so
  the launcher-template assertion still holds.
- The ten servers share one built artifact (seq 01), but each launcher is still a separate
  top-level module that restricts to its own config, so per-server isolation is preserved.

## Design decisions

- **Keep the test as a guard; do not rewrite it.** The test already asserts the REQ-002
  guarantee (own-config-only load, no sibling import, entry-table mapping, launcher restriction).
  Since seq 01 preserves the data the test reads (`ENTRIES` shape) and the behavior it checks
  (restrict-before-import), adding tests would duplicate existing coverage and widen the change.

## Alternatives considered

- **Adding a multi-main-specific isolation case.** Rejected — the shared artifact does not change
  which config each launcher loads; the existing `test_a_server_module_executes_once_under_python_m`
  already asserts `config_loads == [config_file]` per server under real execution.

## Implementation
### Target file
`tests/mcp_servers/test_config_isolation_import.py`

### Procedure

1. Confirm `_SERVERS` and `_ONCE_SERVERS` still list the ten MCP servers and their config files;
   do not add or remove rows — the ten servers are unchanged by the multi-main build.
2. Confirm `_entries()` (reads `deploy/build_binaries.sh` `ENTRIES(` … `\n)\n`, splits each row on
   `:` into `module:_name:cls:cfg`, keeps rows with a `cls`) still returns the ten servers, because
   the ten MCP `ENTRIES` rows keep their shape after the agent is split off.
3. Confirm `test_entries_table_matches_the_server_classes` still holds: `len(entries) == len(_SERVERS)`
   (both ten) and each entry's class `own_config_file` equals its config file.
4. Confirm `test_launcher_template_restricts_config_before_the_server_import` still holds: in
   `deploy/build_binaries.sh`, `ConfigLoader.restrict_to("${cfg}")` appears before
   `from ${module} import ${cls}`.
5. Run the file; all cases pass. Make no structural change unless seq 01 altered the `ENTRIES`
   shape or removed the per-server `restrict_to` before import, in which case apply the smallest
   update to the affected assertion.

### Method

- Expected result: no edit. The test reads only constructs seq 01 preserves (`ENTRIES` shape,
  restrict-before-import), and it currently passes (30 cases).
- If a targeted update is required, change only the affected assertion and re-run the file.

### Details

- `test_restrict_first_import_loads_only_the_own_config` drives
  `ConfigLoader.restrict_to("<config>")` then `import <module>` in a fresh interpreter and asserts
  only the own config loads.
- `test_importing_one_file_server_does_not_import_its_siblings` imports a `file` server and
  asserts sibling `file` servers are not imported.
- `test_a_server_module_executes_once_under_python_m` runs the real `run_http()` (only
  `uvicorn.Config` stubbed) via `runpy` and asserts the target module executes once and only its
  own config loads — the strongest isolation check, still valid under a shared artifact.

## Compatibility considerations

- No change to the test API (`isolated_subprocess_env`, `firejail_on_path` fixtures) or the
  recorded-script format, so nothing that depends on this test changes.

## Security considerations

- The isolation guarantee (each server loads only its own config) is a configuration-isolation
  boundary; keeping this test green preserves the regression guard against a server loading a
  sibling's or the agent's config.

## Rollback considerations

`N/A: revert the commit`; no code change is expected.

## Validation plan

- `uv run pytest tests/mcp_servers/test_config_isolation_import.py` — all cases pass.
- `uv run ruff check tests/mcp_servers/test_config_isolation_import.py`;
  `uv run mypy tests/mcp_servers/test_config_isolation_import.py`.

## Completion criteria

- The ten MCP servers remain in `_SERVERS`/`_ONCE_SERVERS` and `_entries()` still yields ten.
- `test_entries_table_matches_the_server_classes` and
  `test_launcher_template_restricts_config_before_the_server_import` still hold.
- All cases pass; no structural change was introduced unless a specific seq 01 alteration
  required it.

## Out of Scope

- Changing which servers are listed (the ten MCP set is fixed by the build).
- The multi-main build mechanics (`deploy/build_binaries.sh`, `REQ-001`).
- The staleness/rebuild-unit model (`tools/manage_binaries.py`, `REQ-003`).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | verify existing coverage; no edit expected |
| 2 | Add or update tests per Validation plan | Pending | — | — | existing file, all cases |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | |

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
- **Requirement ID**: `REQ-002`
- **Source issue**: `issues/20261115-072739_buildperf001_mcp-multidist-binary.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261115-193516_buildperf001_mcp-multidist-binary.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261116-104919
- **Related target files**: `tests/mcp_servers/test_config_isolation_import.py`
