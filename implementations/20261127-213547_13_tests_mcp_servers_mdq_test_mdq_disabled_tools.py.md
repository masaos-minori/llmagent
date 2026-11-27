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

### Details
- The refusal must happen before the handler runs, so the test asserts no handler call and no audit record for the refused call.

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
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
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
- **Requirement ID**: REQ-001 (disabled-tool enforcement and stale discovery)
- **Workflow phase**: plan-to-implementation-procedure
- **Source issue**: `issues/done/20261119-142123_mdqmcp001_mdq-server-boundary.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261127-160114_mdqmcp001_mdq-server-boundary.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261127-213547
- **Related target files**: `tests/mcp_servers/mdq/test_mdq_disabled_tools.py`
