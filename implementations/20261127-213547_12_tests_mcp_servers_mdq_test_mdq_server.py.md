## Goal

Create the boundary tests that pin one availability function used by both discovery and dispatch, per-tool evaluation, and re-evaluation at call time (REQ-001 per-tool availability).

## Scope
**Release unit**: boundary-characterization-tests (Plan step 1 cites this row; the unit covers Phases 1, 3, 4, 5, 6)

## Assumptions
- This row keeps its own document because the test design is its own decision: it must observe the same availability result through two paths, which no code row's document defines.
- Written in Phase 1 before the production change, so the tests fail first and pin the current disagreement; they pass after seq 01.
- `tests/mcp_servers/_auth_headers.py` is the HTTP fixture reused here; it is not a target row.
- The code vocabulary `tool_disabled` comes from seq 08.

## Design decisions
- The test asserts equality of the availability result between `/v1/tools` and `call_tool` for the same tool name, not merely that both report disabled.
- Re-evaluation at call time is tested by changing the allowlist between the discovery call and the dispatch call.

## Alternatives considered
- N/A: the row is a test file; no production design decision is involved.

## Implementation
### Target file
`tests/mcp_servers/mdq/test_mdq_server.py` (new)

### Procedure
- Add a test that calls `/v1/tools` and `call_tool` for the same tool name and compares the availability result.
- Add a test that changes `allowed_dirs` between the two calls and shows dispatch re-evaluates.
- Add a per-tool test showing one tool can be disabled while another is enabled.

### Method
- Use the HTTP fixture in `tests/mcp_servers/_auth_headers.py` for the HTTP path and programmatic dispatch for the second path.

### Details
- The current code passes `""` as the tool name at `scripts/mcp_servers/mdq/mdq_server.py` line 391, so the disagreement is observable today; the test names that as the behavior being fixed.

## Compatibility considerations
- N/A: new test file.

## Security considerations
- N/A: no redaction behavior is asserted here; seq 14 and seq 15 cover it.

## Rollback considerations
- N/A: revert the commit; the file stays as the characterization record.

## Validation plan
- `uv run pytest tests/mcp_servers/mdq/test_mdq_server.py`
- Full sequence per `rules/toolchain.md`.

## Completion criteria
- A tool reported as disabled cannot be executed through HTTP or programmatic dispatch (AC-1).
- Discovery and dispatch report the same availability for the same tool name.

## Out of Scope
- The availability function implementation (seq 01) and the `config_dependent` metadata (seq 07).

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
- **Requirement ID**: REQ-001 (per-tool availability, discovery and dispatch agreement)
- **Workflow phase**: plan-to-implementation-procedure
- **Source issue**: `issues/done/20261119-142123_mdqmcp001_mdq-server-boundary.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261127-160114_mdqmcp001_mdq-server-boundary.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261127-213547
- **Related target files**: `tests/mcp_servers/mdq/test_mdq_server.py`
