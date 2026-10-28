# Procedure: construct the integration executor with a health registry

## Goal

Pass a health registry in `_make_http_executor` and drop `executor.set_health_registry(health)` (Plan REQ-005).

## Scope

- Modify only `tests/integration/test_agent_mcp_integration.py`.
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

`tests/integration/test_agent_mcp_integration.py`

### Procedure

- Give `_make_http_executor` a `health_registry` parameter (default `McpServerHealthRegistry()`) and pass it to `ToolExecutor(...)`.
- In `test_a10_health_check_unavailable_rejects_call`, build the executor with the test's `health` registry instead of calling `set_health_registry`.

### Method

Edit the existing tests in place and reuse the file's fixtures and helpers.

### Details

- Row 4 and 5 have landed. The file imports `McpServerHealthRegistry` from `shared.mcp_config`; keep whatever import path the mcpcompat001 procedures leave.

## Compatibility considerations

N/A: test-only change.

## Security considerations

N/A: test-only change.

## Rollback considerations

N/A: revert the commit.

## Validation plan

| Step | Command | Expected outcome |
|---|---|---|
| 1 | `uv run pytest tests/integration/test_agent_mcp_integration.py -m integration -q` | Pass |
| 2 | `uv run ruff format tests/integration/test_agent_mcp_integration.py`; `uv run ruff check tests/integration/test_agent_mcp_integration.py` | No finding |

## Completion criteria

- The file constructs executors with a health registry.

## Out of Scope

- Source files and other test files.
- Documentation.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add or update tests per Validation plan | Completed | — | 20261028-180946 | Changes were NOT previously landed; applied here. _make_http_executor now takes health_registry param (default None -> fresh McpServerHealthRegistry()) and passes it to ToolExecutor; test_a10 builds executor with its own health registry instead of set_health_registry. ruff clean; 12 tests pass (ran directly -m integration deselects all 12: file lacks the marker). |
| 2 | Run the validation sequence (`rules/toolchain.md`) | Completed | — | 20261028-180952 | ruff format+check clean; 12 tests pass (run directly). |

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
- **Requirement ID**: REQ-005 (integration executor construction)
- **Source issue**: issues/20261027-155847_mcpexec004_make-mcp-deps-mandatory.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261028-093529_mcpexec004_make-mcp-deps-mandatory.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261028-115653
- **Related target files**: tests/integration/test_agent_mcp_integration.py