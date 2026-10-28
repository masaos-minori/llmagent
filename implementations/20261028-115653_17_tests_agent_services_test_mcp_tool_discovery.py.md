# Procedure: pass allowed_servers to the registry builder calls

## Goal

Update the two direct builder calls to pass `allowed_servers` (Plan REQ-001).

## Scope

- Modify only `tests/agent/services/test_mcp_tool_discovery.py`.
- Test-only change; no source file is edited.

## Assumptions

- The code procedures of this Plan with a lower `seq` have landed.
- Sequencing: the mcpcompat001, mcpinv002 and mcpinv004 implementation procedures (`implementations/20261028-013216_*` and `implementations/20261028-004831_*`) edit `scripts/shared/tool_executor.py`, `scripts/shared/tool_transport_invoker.py` and the discovery side of the posture gate; re-read the current file before editing and keep whatever those procedures produced (UNK-01).
- Overlap (compatible): `plans/20261028-094739_rtool008_fail-closed-runtimetool-builder.md` also targets `tests/shared/test_runtime_tool_registry.py`; it only changes which builder the existing calls use.

## Design decisions

- Locate edit points by test or fixture name, never by line number.
- Assert observable behavior; use barriers or events, never sleeps.

## Alternatives considered

N/A: lightweight row; the Plan fixes the approach.

## Implementation

### Target file

`tests/agent/services/test_mcp_tool_discovery.py`

### Procedure

- In the test that calls `_build_runtime_tools(entries, frozenset({"down"}))`, pass `allowed_servers=frozenset({"srv"})`-style explicit keyword matching the servers in `entries`.
- In `test_dedupe_and_build_excludes_a_duplicated_name_and_reports_it_fatal`, change `_dedupe_and_build(entries, frozenset())` to pass `allowed_servers` explicitly.
- Add `test_empty_allowed_servers_registers_nothing` (new) and `test_build_requires_allowed_servers` (new) (a `TypeError` when the keyword is omitted).
- Locate the call sites by test name; the file was edited by the mcpcompat003 procedures and may be edited by the mcpcompat001 posture-gate procedures.

### Method

Edit the existing tests in place and reuse the file's fixtures and helpers.

### Details

- Row 1 has landed.

## Compatibility considerations

N/A: test-only change.

## Security considerations

N/A: test-only change.

## Rollback considerations

N/A: revert the commit.

## Validation plan

| Step | Command | Expected outcome |
|---|---|---|
| 1 | `uv run pytest tests/agent/services/test_mcp_tool_discovery.py -q` | Pass |
| 2 | `uv run ruff format tests/agent/services/test_mcp_tool_discovery.py`; `uv run ruff check tests/agent/services/test_mcp_tool_discovery.py` | No finding |

## Completion criteria

- Both calls pass `allowed_servers`; the empty-set and required-keyword tests pass.

## Out of Scope

- Source files and other test files.
- Documentation.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add or update tests per Validation plan | Pending | — | — | |
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
- **Requirement ID**: REQ-001 (builder requires allowed_servers)
- **Source issue**: issues/20261027-155847_mcpexec004_make-mcp-deps-mandatory.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261028-093529_mcpexec004_make-mcp-deps-mandatory.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261028-115653
- **Related target files**: tests/agent/services/test_mcp_tool_discovery.py
