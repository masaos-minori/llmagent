## Goal

Extend `tests/tools/test_run_validation_gates.py` with the structure-gate selection, expansion, id-reconciliation, and hook-parity coverage (REQ-003, REQ-004 / AC-4, AC-5, AC-6).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions

- The tests describe the state after the seq 02 (gate row and sentinel skip) and seq 03 (hook) documents land; writing them first (plan Phase 2/3 "fail first" order) is expected.
- Existing anchors: `_PARITY_GATES` currently excludes `check_workitem_structure`, and `test_parity_gate_triggers_mirror_hook_filters` pins gate triggers to hook filters (verified 20261117).

## Design decisions

- Pin the Decision 6 invariant directly: gate `checker_id`, `_checker_id_from_cell` of the routing Run cell, and `_hook_checker_id` of the `workitem-structure` hook must all equal `check_workitem_structure:--file`.

## Alternatives considered

- Test only `drift_report` end-to-end: rejected — an equality assertion on the three ids localizes which side drifted.

## Implementation
### Target file
`tests/tools/test_run_validation_gates.py`

### Procedure

- Add tests (new): top-level selection for `issues/i.md`, `plans/p.md`, `implementations/i.md`; non-selection for `plans/done/p.md` and the other `done/` kinds; `requires_context` false for the gate; command expansion to `--file <matched paths>` via `_expand_changed_files`; a runner-based `Fail` result when the checker exits 1 (AC-5); and the three-way id equality assertion above.
- Add `check_workitem_structure` to `_PARITY_GATES` and extend the trigger-table parametrization with the top-level paths (expected set gains the gate) and `done/` paths (expected set must not).

### Method

- Mirror the existing parametrization style of `test_parity_gate_triggers_mirror_hook_filters`; reuse the module's runner fixtures for the `Fail` test.

### Details

- `CHANGED_FILES_SENTINEL` in `tools/run_validation_gates.py` is the token the gate row carries after the seq 02 edit; the expansion test asserts it is replaced by exactly the pattern-matched changed paths.

## Compatibility considerations

- This row is named by two Plan rows (gate and hook), which is why it is a standalone document rather than a companion.
- `drift_report` errors must stay at 0 in the parity test only after seq 02/03/04 land; the id-equality tests are the local guards.

## Security considerations

N/A: test module.

## Rollback considerations

N/A: revert the commit.

## Validation plan

- `uv run pytest tests/tools/test_run_validation_gates.py -v`, then `uv run pytest tests/tools -n logical -q` (plan Validation plan rows for this file).
- `uv run python tools/run_validation_gates.py drift` reports 0 errors with all four code/config targets landed.

## Completion criteria

- AC-4, AC-5, AC-6 hold as tests; `_PARITY_GATES` includes the gate; the trigger table covers top-level and `done/` paths.

## Out of Scope

- Checker-behavior tests (companion of the seq 01 document); changes to the tested modules themselves (other documents of this plan).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add the selection, expansion, id, and parity tests | Completed | 20261117-165508 | 20261117-165508 | selection/sentinel-expansion/Fail/id-equality tests added; _PARITY_GATES + trigger table extended (top-level and done/ rows) |
| 2 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261117-165508 | 20261117-170012 | 86/86 in this file; tests/tools 2081 passed, 2 skipped; drift 0 errors; full sequence at batch end full batch validation: pytest tests/ 12591 passed 7 skipped; diff-cover no measurable lines (tools/tests/docs only); drift 0 errors; hooks pass |

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
- **Requirement ID**: `REQ-003` (gate selection and expansion tests), `REQ-004` (hook parity tests)
- **Source issue**: `issues/20261117-123330_wftool001_gate-workitem-structure.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261117-124139_wftool001_gate-workitem-structure.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261117-151927
- **Related target files**: `tests/tools/test_run_validation_gates.py`