## Goal
Make `build_execution_groups` raise on duplicate call ids instead of silently resolving multiple
raw calls to one `ToolSpec`, as defense-in-depth behind the preparation rejection (REQ-002,
REQ-004; AC-004).

## Scope
**Release unit**: N/A: not part of a release unit

Covers the `scripts/agent/tool_scheduler.py` row (seq 02) of
`plans/20261101-142610_dupcallid001_duplicate-call-id-misexecution.md`, plus its companion test
file. Executed after seq 01 (both follow the red-test-first order).

## Assumptions
- In production this guard is unreachable once seq 01 rejects duplicates in preparation; it turns
  any future bypass into a loud scheduling failure (Plan D2).
- The guard fires only on genuine duplicates, so unique-id scheduling behavior is unchanged
  (REQ-004).

## Design decisions
- Raise while walking the raw batch in `build_execution_groups` (sched:259, loop at sched:276),
  before any phase building or `force_serial` dispatch, so no partially built plan escapes.
- New exception type follows the module's existing error style (`MissingToolSpecError`), e.g.
  `DuplicateToolCallIdError` (new), raised with the offending id.

## Alternatives considered
- De-duplicate silently keeping the first occurrence: rejected — reproduces the misexecution
  hazard at a different layer.
- Guard only in `_build_forced_serial_plan`: rejected — misses the DAG path.

## Implementation
### Target file
`scripts/agent/tool_scheduler.py`

### Procedure
1. Write the red companion test (see Companion test files) and confirm it fails.
2. Add a `DuplicateToolCallIdError` (new) exception next to `MissingToolSpecError`.
3. In `build_execution_groups`, before the spec walk completes (or within it), detect a repeated
   `tc["id"]` across `tool_calls` and raise `DuplicateToolCallIdError` (new). Update the docstring
   `Raises:` section.

### Method
Explicit duplicate-id guard in the existing walk over `tool_calls`.

### Details
- The check must cover the `force_serial=True` path too (`_build_forced_serial_plan` consumes the
  same `specs_ordered`), so place the guard before the `force_serial` branch.
- Error message names the duplicated id and the tool name of the second occurrence, mirroring the
  `MissingToolSpecError` message style.
- Verification 20261103: `build_execution_groups` is radon B(9) at HEAD; the guard must be a
  single `if` inside the existing spec walk so the function stays within class B (B(10) ceiling).
- Companion test uses the file's `_tc`/`_spec` helpers: two raw calls sharing one id and a single
  `call_specs` entry for that id (the current code resolves both to one spec, so the test is red
  without the raise).

### Companion test files
- `tests/agent/test_tool_scheduler.py`
  - Procedure: add a test following the `test_unknown_tool_raises_missing_tool_spec` raise-path
    pattern: two raw calls sharing one id with a matching `call_specs` entry raise
  `DuplicateToolCallIdError` (new); also assert unique-id plans are unaffected.
  - Validation: `uv run pytest tests/agent/test_tool_scheduler.py -q` green after step 3; the new
    test fails before it.

## Compatibility considerations
- Related scheduler test files `tests/agent/test_tool_scheduler_comprehensive.py` and
  `tests/agent/test_tool_scheduler_serialization.py` must keep passing unchanged (they build
  unique-id batches).
- Callers in `tool_runner.py::_execute_with_dag` do not catch scheduler exceptions today; an
  unreachable-in-production raise propagates as a loud failure, matching Plan D2.

## Security considerations
- Second layer against id-keyed spec collapse (`tool_runner.py` L434-435).

## Rollback considerations
- Guard removal restores prior silent behavior; no data or API change to unwind.

## Validation plan
1. `uv run pytest tests/agent/test_tool_scheduler.py tests/agent/test_tool_scheduler_comprehensive.py tests/agent/test_tool_scheduler_serialization.py -q`.
2. Full validation sequence per `rules/toolchain.md` at the end of the plan's execution.

## Completion criteria
- Duplicate ids reaching the scheduler raise instead of collapsing (AC-004).
- Unique-id ordering/serialization tests unchanged and green (REQ-004).

## Out of Scope
- Preparation rejection (seq 01), round-level test (seq 06), documentation (seq 03).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Write red companion tests, then implement (Procedure 1-3) | Completed | 20261103-104234 | 20261103-104234 | Red baseline: new tests fail pre-change (ImportError for `DuplicateToolCallIdError`; collapse behavior additionally proven by the seq 06 round test on stashed code). Guard is a single `if` in the spec walk before the force_serial branch; docstring Raises updated. radon: build_execution_groups B(9) -> B(10), stays class B. |
| 2 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261103-104234 | 20261103-104234 | Scheduler + comprehensive + serialization suites green; tests/agent 4030 passed; generate_reference_table regenerated for the new public `DuplicateToolCallIdError` (manifest drift resolved). |

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
- **Requirement ID**: REQ-002, REQ-004
- **Source issue**: issues/20261101-073525_dupcallid001_duplicate-call-id-misexecution.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261101-142610_dupcallid001_duplicate-call-id-misexecution.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261103-080412
- **Related target files**: `scripts/agent/tool_scheduler.py`, `tests/agent/test_tool_scheduler.py`