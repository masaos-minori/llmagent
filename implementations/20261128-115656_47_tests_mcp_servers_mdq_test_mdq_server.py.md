# Implementation Procedure — tests/mcp_servers/mdq/test_mdq_server.py

## Goal

Classify `tests/mcp_servers/mdq/test_mdq_server.py` as `contract`: the module asserts the single availability boundary that discovery and dispatch must share (`REQ-001`, `AC-1`), and it already carries the `REQ-001` citation at line 4, so the plan's rule (`contract` when the assertions trace to a requirement source) makes it a contract module (`REQ-003`, `AC-3`).

## Scope
**Release unit**: mdq-taxonomy-gate

- One module-level `pytestmark` line is added; no assertion or fixture in the module changes.
- No citation clause is written: the `REQ-001` citation at line 4 already satisfies what `tools/check_test_taxonomy.py` requires of a `contract` module.

## Assumptions

- This row is an amendment of the Plan's frozen `Implementation Target Files` table: the module is one of the three under `tests/mcp_servers/mdq/` that the rebase introduced after the Plan was frozen, so it had no row and no procedure document before the amendment (user-approved, 20261128).
- The module has no `pytestmark` today and already imports `pytest`, so `add_import` is `false` in the records file.
- `tests/mcp_servers/mdq` is not in `CLASSIFIED_AREAS` at current HEAD (`tools/check_test_taxonomy.py:66`, `in_classified_area()` matches by prefix), so this module is judged only after the classified-area addition, which is the same release unit (`mdq-taxonomy-gate`, plan Phases 4 and 5).
- The module docstring states that its assertions fail against current source because `/v1/tools` passes `""` to the availability function and `call_tool()` has no availability check. At current HEAD the module passes (17 tests across the three modules the rebase introduced), so that docstring claim is stale. The row is a marker-only change, so the claim is reported here and not repaired.

## Design decisions

- Classify as `contract` because the assertions trace to a requirement source (`REQ-001`): one shared availability boundary used by both discovery and dispatch is a documented contract, not observed behavior with no source.

## Alternatives considered

- `N/A: one-line classification change; the plan names the marker, and the citation the plan expected to be absent is already present.`

## Implementation
### Target file
`tests/mcp_servers/mdq/test_mdq_server.py`

### Procedure
1. Add `pytestmark = pytest.mark.contract` after the module-level import block.
2. Leave the docstring and the assertions as they are.

### Method

- Applied through `tools/apply_test_taxonomy_markers.py` from the batch records JSON array; the marker line is the only change the tool makes to the module.
- The marker is placed after the import block (imports end at line 31), not in the docstring, so the citation the module already carries is not touched.

### Details

- Records record: `{"path": "tests/mcp_servers/mdq/test_mdq_server.py", "pytestmark": "contract", "add_import": false}`.

## Compatibility considerations

- `N/A: test-only change.`
- After classification the CI report step groups this module under `contract` (`AC-6`), so a failure here is a checker finding, not a report-only result.

## Security considerations

- `N/A: test-only change.` The assertions cover availability refusals at dispatch; no production path changes.

## Rollback considerations

- `N/A: revert the commit.`

## Validation plan

- `uv run python tools/check_test_taxonomy.py` — no finding for this module (`AC-3`)
- `uv run pytest tests/mcp_servers/mdq/test_mdq_server.py`
- Full sequence per `rules/toolchain.md`.

## Completion criteria

- The module carries exactly one taxonomy marker, `contract` (`AC-3`).
- The `REQ-001` citation stays in the module, so the contract citation requirement is met without a new clause (`AC-3`).

## Out of Scope

- The classified-area addition (`tools/check_test_taxonomy.py`, row 05).
- The stale docstring claim that the assertions fail against current source.
- The availability boundary itself, which is the `REQ-001` production change owned by another plan.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | Plan Phase 4, amended row |
| 2 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | The "Add or update tests" step does not apply: this row is the test module itself |

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
- **Requirement ID**: REQ-003 (machine-readable test classification), AC-3
- **Source issue**: `issues/20261119-142132_mdqmcp010_mdq-release-readiness.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/done/20261127-203046_mdqmcp010_mdq-release-readiness.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261128-115656
- **Related target files**: `tests/mcp_servers/mdq/test_mdq_server.py`
