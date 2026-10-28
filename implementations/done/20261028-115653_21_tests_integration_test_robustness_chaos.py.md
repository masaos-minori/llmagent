# Procedure: construct the chaos-test executors with a health registry

## Goal

Pass a health registry to the six `ToolExecutor(` constructions (Plan REQ-005).

## Scope

- Modify only `tests/integration/test_robustness_chaos.py`.
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

`tests/integration/test_robustness_chaos.py`

### Procedure

- Pass `health_registry=McpServerHealthRegistry()` in each of the six `ToolExecutor(...)` constructions (the `test_3b1` (new), `test_3d2` (new), `test_3d3` (new) tests and the three `_side_effect` based tests); add the import once.

### Method

Edit the existing tests in place and reuse the file's fixtures and helpers.

### Details

- Row 4 and 5 have landed.

## Compatibility considerations

N/A: test-only change.

## Security considerations

N/A: test-only change.

## Rollback considerations

N/A: revert the commit.

## Validation plan

| Step | Command | Expected outcome |
|---|---|---|
| 1 | `uv run pytest tests/integration/test_robustness_chaos.py -m integration -q` | Pass |
| 2 | `uv run ruff format tests/integration/test_robustness_chaos.py`; `uv run ruff check tests/integration/test_robustness_chaos.py` | No finding |

## Completion criteria

- All six constructions pass a registry.

## Out of Scope

- Source files and other test files.
- Documentation.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add or update tests per Validation plan | Completed | 20261028 | 20261028-181752 | Applied health_registry to all six ToolExecutor constructions (prior state had only 1/6); import already present. Applied health_registry to all six ToolExecutor constructions; prior state had only 1/6. |
| 2 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261028 | 20261028-181752 | ruff format/check clean; pytest 14 passed (run directly; file carries no integration marker). ruff clean; pytest 14 passed (direct run). |

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
- **Related target files**: tests/integration/test_robustness_chaos.py