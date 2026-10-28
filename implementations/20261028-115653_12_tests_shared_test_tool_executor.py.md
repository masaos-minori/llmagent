# Procedure: construct executors with a health registry and add routing result tests

## Goal

Pass `health_registry` at construction and cover the four routing result kinds (Plan REQ-004, REQ-005).

## Scope

- Modify only `tests/shared/test_tool_executor.py`.
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

`tests/shared/test_tool_executor.py`

### Procedure

- Give `_make_executor`, `_make_executor_with_mock_lifecycle` and `_equivalent_executor` a `health_registry` parameter defaulting to `McpServerHealthRegistry()` and pass it to `ToolExecutor(...)`.
- Replace each `ex.set_health_registry(registry)` call (about nine, in the HTTP classification tests) with passing `health_registry=registry` to the helper; replace `executor.set_health_registry(mock_registry)` the same way.
- Add `test_execute_returns_routing_not_ready_result_before_wiring` (new), `test_execute_returns_routing_unknown_tool_result` (new), `test_execute_returns_routing_posture_excluded_result` (new) and `test_execute_returns_routing_server_unavailable_result` (new): assert `is_error`, `error_type == "routing"`, the `routing:<kind>:` prefix and that no HTTP request was made.
- Keep the `UNAVAILABLE` and `HALF_OPEN` tests' assertions unchanged.

### Method

Edit the existing tests in place and reuse the file's fixtures and helpers.

### Details

- Rows 3-5 have landed.

## Compatibility considerations

N/A: test-only change.

## Security considerations

N/A: test-only change.

## Rollback considerations

N/A: revert the commit.

## Validation plan

| Step | Command | Expected outcome |
|---|---|---|
| 1 | `uv run pytest tests/shared/test_tool_executor.py -q` | Pass |
| 2 | `uv run ruff format tests/shared/test_tool_executor.py`; `uv run ruff check tests/shared/test_tool_executor.py` | No finding |

## Completion criteria

- No `set_health_registry` call remains; the routing result tests pass.

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
- **Requirement ID**: REQ-004, REQ-005, REQ-007 (executor construction and result contract)
- **Source issue**: issues/20261027-155847_mcpexec004_make-mcp-deps-mandatory.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261028-093529_mcpexec004_make-mcp-deps-mandatory.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261028-115653
- **Related target files**: tests/shared/test_tool_executor.py
