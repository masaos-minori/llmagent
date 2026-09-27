## Goal

Add the missing `orch = _make_orchestrator(ctx)` construction line to `test_handle_turn_invokes_workflow_engine_run` in `tests/integration/test_orchestrator_integration.py`, fixing `NameError: name 'orch' is not defined` (REQ-001).

## Scope

In scope: this one test's missing construction line. Out of scope: the test's own mock-engine-injection technique (`orch._workflow_adapter._workflow_engine = mock_engine_instance`) — confirmed to be the *correct* pattern (direct attribute replacement after construction), not to be changed; `agent001`'s `TestToolCallFlow` fixes in this same file (already applied via a separate implementation procedure document from a different Plan) — distinct scope, do not re-touch.

## Assumptions

- `_make_orchestrator(ctx)` (no additional kwargs) is the correct construction call, matching the plain `_make_ctx()` this test already uses with no special `on_error`/`pause_on_critical_failure` needs evident from the test body.

## Design decisions

- Add the single missing line at the natural position (immediately after `ctx = _make_ctx()`), rather than restructuring the test further — the rest of the test body already correctly references `orch` in all 3 places (lines 863, 866, 870) once it exists.

## Alternatives considered

- N/A: a single missing-line omission with one obvious fix; no alternative approach considered.

## Implementation

### Target file

`tests/integration/test_orchestrator_integration.py`

### Procedure

1. Re-confirm via Read that `test_handle_turn_invokes_workflow_engine_run` (lines 847-873) still has `ctx = _make_ctx()` at line 850 with no `orch = ...` assignment before line 863's first use (adversarial re-verification).
2. Add `orch = _make_orchestrator(ctx)` immediately after `ctx = _make_ctx()` (line 850).

### Method

Single-line addition — no other change to the test body.

### Details

- Before: `ctx = _make_ctx()` (line 850), followed directly by `captured_calls: list[int] = []` and the rest of the test body, with no `orch` assignment.
- After: `ctx = _make_ctx()` followed by `orch = _make_orchestrator(ctx)`, then the existing body unchanged.
- Confirm `_make_orchestrator` is already defined in this file (line 106, per this session's earlier investigation) — no new import or helper needed.

## Compatibility considerations

- No production code changes; test-only fix.

## Security considerations

N/A: test-only fix, no security-relevant behavior change.

## Rollback considerations

- `git revert` the commit, or manually remove the added line.

## Validation plan

| Target | Strategy | Command | Expected |
|---|---|---|---|
| `tests/integration/test_orchestrator_integration.py` | Integration | `uv run pytest tests/integration/test_orchestrator_integration.py -q` | All tests pass except `agent001`'s separately-tracked failures (if not yet applied in the same working tree) |

## Completion criteria

- `uv run pytest tests/integration/test_orchestrator_integration.py::TestApprovalWorkflowWithRealDB::test_handle_turn_invokes_workflow_engine_run -q` passes.

## Out of scope

- `agent001`'s `TestToolCallFlow` fixes in this same file (separate Plan/implementation procedure).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | N/A: adding the missing line is itself the fix |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | N/A: no docs/00_index.md task-scope mapping for this test file |

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
- **Requirement ID**: REQ-001: add the missing `orch` construction line
- **Source issue**: issues/20260927-075300_int001_orchestrator_integration-nameerror-orch-not-defined.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260927-085738_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260927-093458
- **Related target files**: tests/integration/test_orchestrator_integration.py
