## Goal
Reject every occurrence of a duplicated tool-call id in `prepare_tool_calls` with a distinct
`duplicate_id` (new) failure kind before the approval gate, so no call can run with another call's
arguments (REQ-001, REQ-005; AC-001, AC-002).

## Scope
**Release unit**: N/A: not part of a release unit

Covers the `scripts/agent/tool_preparation.py` row (seq 01) of
`plans/20261101-142610_dupcallid001_duplicate-call-id-misexecution.md`, plus its companion test
file. Execution order for the whole plan: this document and seq 02 write their red tests first,
then the code; seq 06 (round-level test) runs after both code changes; seq 03 (docs) last.

## Assumptions
- A duplicated id within a round is always ambiguous and unsafe to resolve by "last wins"; the
  safe default is to reject (Plan Assumptions).
- `error_type` values are free-form identifiers, so the `duplicate_id` (new) kind needs no schema
  change.
- Duplicate detection is batch-level (cross-call), so it lives in `prepare_tool_calls`, not in
  `_prepare_one` (per-call checks stay untouched).

## Design decisions
- Detect duplicates after `_prepare_one` returns, on the batch results: every `PreparedToolCall`
  whose `call_id` occurs more than once in the batch moves to `failures` via `_reject` with kind
  `duplicate_id` (new) and a reason naming the id and its occurrence count. A call already
  rejected for another reason is not re-rejected as a duplicate.
- The count is over `prepared` entries only (Plan D1 mechanism): a prepared call whose id also
  appears on an occurrence already rejected for another reason is not flagged — the misexecution
  hazard requires two same-id calls in `prepared` (verification 20261103).
- Empty/missing ids are already rejected per call by `_prepare_one` ("tool call is missing an
  id"); they never reach the duplicate check as prepared entries, so the existing missing-id
  tests stay untouched (REQ-005).

## Alternatives considered
- Reject inside `_prepare_one` with a seen-set threaded through the loop: rejected — it entangles
  the per-call contract with batch state; the Plan's row mandates batch-level detection.
- Keep the last occurrence and reject only the earlier ones: rejected — "last wins" is the exact
  misexecution hazard this Plan removes.

## Implementation
### Target file
`scripts/agent/tool_preparation.py`

### Procedure
1. Write the red companion tests (see Companion test files) and confirm they fail against the
   current implementation.
2. In `prepare_tool_calls` (prep:149), after the per-call loop: collect `call_id` counts of the
   `PreparedToolCall` results; for every prepared call whose id count exceeds 1, remove it from
   `prepared` and append a failure tuple built by `_reject` called with the new `duplicate_id` (new)
   kind and reason "duplicate tool call id '<id>' appears N times in this round", in
   original relative order. Verification 20261103: implement the post-pass as a private helper
   `_move_duplicate_ids` (new) called from `prepare_tool_calls` — `prepare_tool_calls` is
   radon A(3) and the inline counting/filtering would push it to B; the helper keeps both
   functions in class A.
3. Update the `_reject` docstring (prep:51) to list the `duplicate_id` (new) kind among the
   failure kinds.

### Method
Batch post-pass over prepared results; no change to `_prepare_one` semantics.

### Details
- Use a single counting pass (dict of id -> count) then one ordered filter pass; keep `prepared`
  and `failures` in original relative order per the function docstring contract.
- The failure tuple shape is identical to the other rejection kinds so `_merge_in_declared_order`
  consumes one row per declared occurrence (REQ-003/D4 semantics unchanged).

### Companion test files
- `tests/agent/test_tool_preparation.py`
  - Procedure: add a `TestPrepareToolCallsDuplicateId` (new) class: two calls sharing one id —
    both land in `failures` and `prepared` is empty. Assert the rejection through the failure
    reason text (`duplicate tool call id ... appears N times in this round`): the flat failure
    tuple carries no `error_type` (the `duplicate_id` kind lives only in `_reject`'s internal
    `ToolCallResult` and log line), matching the existing per-kind tests' text assertions
    (verification 20261103). Add a three-call case where the duplicate pair is rejected but a
    unique-id call stays prepared, with both lists in original relative order.
  - Validation: `uv run pytest tests/agent/test_tool_preparation.py -q` green after step 2; the
    new tests fail before it.

## Compatibility considerations
- Existing rejection kinds (configuration/validation/schema) and their tests are untouched.
- Callers of `prepare_tool_calls` already destructure `(prepared, failures)`; no signature change.

## Security considerations
- Closes a misexecution hazard: without this check a later call silently inherits an approved
  call's `ToolSpec` via the id-keyed dicts in `tool_runner.py` L434-435.

## Rollback considerations
- Single-file change plus tests; revert the commit restores prior behavior. No config or schema
  change to unwind.

## Validation plan
1. `uv run pytest tests/agent/test_tool_preparation.py -q` (red before code step, green after).
2. Full validation sequence per `rules/toolchain.md` at the end of the plan's execution.

## Completion criteria
- Duplicate-id calls never reach the approval gate and never execute (AC-001, AC-002).
- Existing missing-id rejection tests still pass (REQ-005).

## Out of Scope
- Scheduler guard (seq 02), round-level test (seq 06), documentation (seq 03).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Write red companion tests, then implement (Procedure 1-3) | Completed | 20261103-104234 | 20261103-104234 | Red baseline: 3 failed in TestPrepareToolCallsDuplicateId (new). Implemented `_move_duplicate_ids` (new) post-pass + `prepare_tool_calls` wiring + `_reject` docstring kind list. radon: helper A(4), prepare_tool_calls A(3), _prepare_one C(12) unchanged. |
| 2 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261103-104234 | 20261103-104234 | ruff/mypy/lint-imports/bandit clean; full suite 11393 passed / 0 failed; diff-cover 100%; pre-commit all hooks passed. |

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
- **Requirement ID**: REQ-001, REQ-005
- **Source issue**: issues/20261101-073525_dupcallid001_duplicate-call-id-misexecution.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261101-142610_dupcallid001_duplicate-call-id-misexecution.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261103-080412
- **Related target files**: `scripts/agent/tool_preparation.py`, `tests/agent/test_tool_preparation.py`