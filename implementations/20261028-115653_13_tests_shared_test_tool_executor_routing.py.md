# Procedure: construct executors with a health registry and add routing and constructor tests

## Goal

Update the five `ToolExecutor(` constructions and the `set_health_registry` tests, and add the constructor and routing-kind tests (Plan REQ-004, REQ-005).

## Scope

- Modify only `tests/shared/test_tool_executor_routing.py`.
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

`tests/shared/test_tool_executor_routing.py`

### Procedure

- Pass `health_registry=McpServerHealthRegistry()` (or the test's registry) in the five `ToolExecutor(` constructions.
- Replace the roughly twenty `ex.set_health_registry(registry)` calls with passing the registry at construction.
- Replace `test_set_health_registry_stores_registry` and `test_set_health_registry_accepts_none` with `test_executor_requires_health_registry` (new) (a `TypeError` when the keyword is omitted).
- Add `test_set_runtime_registry_rejects_none` (new) and one test per routing kind driven through `execute()` (reuse the registries built in the file).
- Keep `TestMcpServerHealthRegistry` untouched.

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
| 1 | `uv run pytest tests/shared/test_tool_executor_routing.py -q` | Pass |
| 2 | `uv run ruff format tests/shared/test_tool_executor_routing.py`; `uv run ruff check tests/shared/test_tool_executor_routing.py` | No finding |

## Completion criteria

- The constructor and routing tests pass and no `set_health_registry` remains.

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
- **Requirement ID**: REQ-004, REQ-005, REQ-007 (routing tests; constructor contract)
- **Source issue**: issues/20261027-155847_mcpexec004_make-mcp-deps-mandatory.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261028-093529_mcpexec004_make-mcp-deps-mandatory.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261028-115653
- **Related target files**: tests/shared/test_tool_executor_routing.py
