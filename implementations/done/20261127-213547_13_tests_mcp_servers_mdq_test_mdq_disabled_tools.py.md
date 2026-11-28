## Goal

Create the disabled-tool and stale-discovery tests that pin the current disagreement between discovery and dispatch, including `grep_docs` configured off (REQ-001 disabled-tool enforcement).

## Scope
**Release unit**: boundary-characterization-tests (Plan step 1 cites this row; the unit covers Phases 1, 3, 4, 5, 6)

## Assumptions
- This row keeps its own document because the stale-discovery scenario is a test-design decision of its own: it requires a discovery call, a configuration change, and a dispatch call in that order.
- Written in Phase 1 before the production change; the tests fail first and pin the disagreement.
- `grep_docs` is gated only inside `MdqService.grep_docs()` today, so no existing test can show discovery and execution agreeing.
- `tests/mcp_servers/_auth_headers.py` is the HTTP fixture reused here; it is not a target row.

## Design decisions
- The stale-discovery test changes configuration between the discovery call and the dispatch call, so the assertion is about re-evaluation, not about a cached flag.
- The refusal assertion is on the response code `tool_disabled` from seq 08, not on an exception class name.

## Alternatives considered
- N/A: the row is a test file.

## Implementation
### Target file
`tests/mcp_servers/mdq/test_mdq_disabled_tools.py` (new)

### Procedure
- Add a test that reports a tool as disabled and then attempts execution through HTTP and through programmatic dispatch.
- Add the stale-discovery test: discovery reports enabled, configuration changes, dispatch refuses.
- Add the `grep_docs` configured-off case through both paths.

### Method
- Both paths must reach the same availability function in `scripts/mcp_servers/mdq/mdq_server.py` (seq 01).
- Step 3b correction (20261128): the programmatic path is `_dispatch_mdq_tool()` called in-process, so the gate must sit inside that entry, not only inside `call_tool()`. seq 01's Procedure places the refusal in `call_tool()`, which covers the HTTP path only; AC-1 names programmatic dispatch, so the check has to be on the entry both paths reach. Recorded as an implementation constraint on seq 01.
- Step 3b correction: the handler is recorded through `patch.dict(mdq_server._DISPATCH_TABLE, ...)`, because the table holds the function object bound at import and patching the module attribute would not change the entry.

### Details
- The refusal must happen before the handler runs, so the test asserts no handler call and no audit record for the refused call.
- Step 3b correction (20261128): "no audit record for the refused call" contradicts AC-3 and `docs/22_mcp/mcp_02_03_audit-logging-and-errors.md` line 58, which counts a disabled tool as one of the paths that produce exactly one record (`outcome` `rejected`, `error_type` `tool_disabled`). The assertion is therefore no handler call plus exactly one record from the single boundary, not zero records.
- Step 3b correction: `CallToolResponse` has no code field (`scripts/mcp_servers/models.py:56`), so the code `tool_disabled` is asserted on the audit record's `error_type`; the response side is asserted on the documented refusal text `Tool disabled: <reason>`.
- Step 3b correction: `grep_docs` is gated only inside `MdqService.grep_docs()` (`mdq_service.py` line 379), which raises `MdqValidationError`, so the record carries the exception-class name today. The gate must refuse before the handler, which is what the test pins.
- Step 3b correction (20261128): the four tests fail against current source as intended — the handler runs on both paths for a tool reported disabled, `grep_docs` is not reported disabled by discovery, and dispatch does not re-evaluate after the configuration change. Recorded as the pinned disagreement; they pass after seq 01 lands.

## Compatibility considerations
- N/A: new test file.

## Security considerations
- N/A: no redaction assertion here.

## Rollback considerations
- N/A: revert the commit; the file stays as the characterization record.

## Validation plan
- `uv run pytest tests/mcp_servers/mdq/test_mdq_disabled_tools.py`
- Full sequence per `rules/toolchain.md`.

## Completion criteria
- A tool reported as disabled cannot be executed through HTTP or programmatic dispatch (AC-1).
- `grep_docs` is disabled consistently when configured off.

## Out of Scope
- The availability function implementation (seq 01) and the `config_dependent` metadata value (seq 07).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261128 | 20261128 | `tests/mcp_servers/mdq/test_mdq_disabled_tools.py` created (4 tests); each assertion names the disagreement it pins |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261128-093658 | 20261128-093658 | Targeted run 20261128: 4 failed as designed (the pinned disagreement). ruff format/check Pass. Validation completes at the end of the release unit, after seq 01 lands end-of-unit gate 20261128 as recorded in seq 01's gates row; the four failing-first assertions pass after seq 01 landed |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Requirement ID**: REQ-001 (disabled-tool enforcement and stale discovery)
- **Workflow phase**: plan-to-implementation-procedure
- **Source issue**: `issues/done/20261119-142123_mdqmcp001_mdq-server-boundary.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261127-160114_mdqmcp001_mdq-server-boundary.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261127-213547
- **Related target files**: `tests/mcp_servers/mdq/test_mdq_disabled_tools.py`