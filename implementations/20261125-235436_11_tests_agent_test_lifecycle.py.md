## Goal

Add new-state transition-table tests, invalid-transition no-mutation tests, and shutdown-suppression typed-error tests (REQ-006, REQ-007, REQ-008, REQ-011), and retarget this module's private-dict sets and assertions to the record registry so it survives REQ-001 (REQ-001; AC-1).

## Scope
**Release unit**: N/A: not part of a release unit (Phase 1 tests are outside R3-ownership; the retargeting is Phase 3 fallout)

## Assumptions
- Phase 1 tests are written first and are expected to fail until Phases 2-4 land (Plan Phase 1, release unit R3-ownership note).
- `_records` (new) and `set_termination_outcome` (new) come from row 3 (`scripts/agent/http_lifecycle.py`); `ManagedProcessRecord` (new) from row 2.
- Two kinds of change live in one file: new defect-pinning tests (Phase 1) and a mechanical accessor swap at the existing private-dict sites (Phase 3), kept in separate test classes so intentional failures stay visible.

## Design decisions
- Keep the pinned invalid pairs (`:685-696`, `FAILED -> RUNNING` and `STOPPED -> RUNNING`) green while adding the new-state tests.

## Alternatives considered
- N/A: test row, no design decision of its own.

## Implementation
### Target file
`tests/agent/test_lifecycle.py`

### Procedure
1. Add tests for the three new states and their transitions, for `_set_state` rejection without mutation, and for `EnsureSuppressedError`/`RestartSuppressedError` raises during shutdown.
2. Retarget every private-dict set and assertion to the record registry.

### Method
Extend the existing transition-table test class and the router test class; imports already cover `LifecycleState`, `assert_valid_transition`, and the router (`:29-30`). Retarget by dict access on the new `_records` mapping so each existing assertion keeps its shape and only the value type changes.

### Details
- The no-mutation test asserts the state is unchanged after an invalid transition (AC-3); the suppression tests assert typed raises (AC-4).
- Retarget the private-dict sites to `mgr._subprocess_mgr._http_mgr._records` (or `mgr._records` where `mgr` is already an `HttpServerLifecycleManager`): the paired `_http_procs[key] = proc` and `_http_pgids[key] = pgid` sets at `:145,216,540-541,576,600,612,635,872,898-899,910,921-922,952,969,980-981,1043,1071,1100,1134,1162,1251` collapse into one `_records[key] = ManagedProcessRecord(...)` assignment; membership and emptiness assertions at `:207,475-476,505-506,568,904,915,942,975,1009,1217-1218` become `"key" in mgr._records` and `len(mgr._records) == 0` comparisons; `mock_mgr._http_procs = {}` at `:170` becomes `mock_mgr._records = {}`; the `orig_get = mgr._http_pgids.get` spy at `:545` becomes a spy on the record's `pgid` attribute.
- Update the class docstring at `:893` ("pops all _http_procs entries") to describe record removal, so the module does not document a removed structure.

## Compatibility considerations
- Test-only, but phase-coupled: the retargeting must land in the same phase as row 3, which removes the dicts. A retarget committed earlier fails against the dicts that still exist; one committed later breaks the suite.
- This file is the companion test for rows 1, 6 and 7 (`scripts/agent/lifecycle.py`, `scripts/agent/lifecycle_router.py`, `scripts/agent/lifecycle_protocol.py`); those rows' validation commands run it.

## Security considerations
- N/A.

## Rollback considerations
- Revert this row together with rows 1, 3, 6 and 8: the new tests import names those rows create, and the retargeted assertions require the registry row 3 installs.

## Validation plan
- `uv run pytest tests/agent/test_lifecycle.py` — new tests green after Phases 2-4; pinned pairs still rejected.

## Completion criteria
- AC-3 and AC-4 are pinned by green tests; the pinned invalid pairs remain green.
- No reference to `_http_procs`, `_http_pgids` or `_failed_start_procs` remains in the file.

## Out of Scope
- The implementation changes (rows 01, 06, 08).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | Tests first, expected to fail until Phases 2-4 |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | Test row: validation is the pytest run |

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
- **Requirement ID**: REQ-001, REQ-006, REQ-007, REQ-008, REQ-011 (defect-pinning tests first; private-dict fallout)
- **Source issue**: issues/20261119-145305_cliplc007_mcp-process-ownership.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261125-232847_cliplc007_mcp-process-ownership.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261125-235436
- **Related target files**: `tests/agent/test_lifecycle.py`
