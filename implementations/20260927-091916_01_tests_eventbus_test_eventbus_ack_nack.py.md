## Goal

Fix `tests/eventbus/test_eventbus_ack_nack.py::TestNackEvent`'s 4 tuple-equality assertions (3 failing tests: `test_nack_event_increments_failure_count`, `test_nack_event_increments_again`, `test_nack_event_not_found`) that compare `nack_event()`'s `NackResult` return value against a bare tuple, which fails because `NackResult` is a `@dataclass(frozen=True)`, not a `NamedTuple` (REQ-001).

## Scope

In scope: the 4 tuple-equality assertions (lines 364, 390, 393, 406) in this file only. Out of scope: `scripts/eventbus/delivery_repo.py`'s `NackResult` definition (confirmed already correct, intentional, well-documented) and this file's other, separately-tracked `eb001` failures (status-code mismatches — distinct root cause, its own Plan/implementation procedure).

## Assumptions

- No other assumption beyond the Plan's own confirmed evidence (dataclass equality semantics directly confirmed via Read of `NackResult`'s definition).

## Design decisions

- Replace each bare-tuple comparison with an equivalent `NackResult(...)`-typed comparison, preserving each test's single-assertion style (each test already separately asserts the underlying DB row's `delivery_failure_count`/`cycle_failure_count` immediately after, so the `NackResult`-level assertion mainly re-confirms the function's direct return value).

## Alternatives considered

- Using two separate field assertions (`result.delivery_failure_count == N`, `result.cycle_failure_count == M`) instead of a single `NackResult(...)` comparison: considered equally valid per the Plan; this document chooses the single-comparison form to keep the diff minimal (one assertion per current one, not two).

## Implementation

### Target file

`tests/eventbus/test_eventbus_ack_nack.py`

### Procedure

1. Re-confirm each of the 4 assertions' exact current line/form via `rg -n "assert result.* == \("  tests/eventbus/test_eventbus_ack_nack.py` (adversarial re-verification — line numbers may have shifted since the Plan was written).
2. Replace each `assert result == (N, M)` / `assert result1 == (N, M)` / `assert result2 == (N, M)` with `assert result == NackResult(delivery_failure_count=N, cycle_failure_count=M)` (substituting the correct local variable name and values per assertion).
3. Confirm `NackResult` is already imported in this file (via `from eventbus.db import nack_event` — `NackResult` may need its own import from `eventbus.delivery_repo` or wherever it's re-exported; confirm via `rg -n "^from eventbus" tests/eventbus/test_eventbus_ack_nack.py` and add the import if missing).

### Method

Direct assertion-value replacement at 4 call sites — no structural change to the tests' setup/teardown.

### Details

- Line 364 (`test_nack_event_increments_failure_count`): `assert result == (1, 1)` → `assert result == NackResult(delivery_failure_count=1, cycle_failure_count=1)`.
- Line 390 (`test_nack_event_increments_again`, first assertion): `assert result1 == (1, 1)` → `assert result1 == NackResult(delivery_failure_count=1, cycle_failure_count=1)`.
- Line 393 (`test_nack_event_increments_again`, second assertion): `assert result2 == (2, 2)` → `assert result2 == NackResult(delivery_failure_count=2, cycle_failure_count=2)`.
- Line 406 (`test_nack_event_not_found`): `assert result == (-1, -1)` → `assert result == NackResult(delivery_failure_count=-1, cycle_failure_count=-1)`.
- `NackResult`'s current definition: `@dataclass(frozen=True) class NackResult: delivery_failure_count: int | Literal[-1]; cycle_failure_count: int | Literal[-2]` (`scripts/eventbus/delivery_repo.py:23-32`).

## Compatibility considerations

- No production code changes; test-only fix.

## Security considerations

N/A: test-only fix, no security-relevant behavior change.

## Rollback considerations

- `git revert` the commit, or manually restore the prior bare-tuple assertions.

## Validation plan

| Target | Strategy | Command | Expected |
|---|---|---|---|
| `tests/eventbus/test_eventbus_ack_nack.py` | Unit | `uv run pytest tests/eventbus/test_eventbus_ack_nack.py::TestNackEvent -q` | All tests in this class pass |

## Completion criteria

- `uv run pytest tests/eventbus/test_eventbus_ack_nack.py::TestNackEvent -q` passes (all tests in this class, not only the 3 affected).
- `uv run pytest tests/eventbus/test_eventbus_ack_nack.py -q` (full file) shows no new regression (the file's other, `eb001`-tracked failures are expected to remain, tracked separately).

## Out of scope

- `eb001`'s status-code-mismatch failures in the same file (its own Plan/implementation procedure).
- `scripts/eventbus/delivery_repo.py`'s `NackResult` definition (confirmed already correct).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | N/A: fixing the existing 4 assertions is itself the fix |
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
- **Requirement ID**: REQ-001: fix the 4 tuple-equality assertions in `TestNackEvent`
- **Source issue**: issues/20260927-075242_eb002_nackresult-no-longer-supports-tuple-equality-in-nack-tests.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260927-082708_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260927-091916
- **Related target files**: tests/eventbus/test_eventbus_ack_nack.py
