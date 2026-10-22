## Goal
Delete the test that imports the removed helpers and drop `offsets_dir` from the fixture (REQ-002 and REQ-004).

## Scope
- In: delete `test_offset_read_write` (about line 76) and remove `offsets_dir` from the `EventBusConfig(...)` construction.
- Out: every other test.

## Assumptions
- The test body only exercises `read_offset` and `write_offset` on a temporary directory (verified).

## Design decisions
- Delete the whole function; keep neighboring tests.

## Alternatives considered
N/A: the test has no remaining subject.

## Implementation
### Target file
`tests/eventbus/test_eventbus_replay_subscribe.py`

### Procedure
1. Delete `test_offset_read_write`.
2. Remove the `offsets_dir=...` keyword from the fixture's `EventBusConfig(...)`.
3. `uv run ruff check` the file and drop unused imports.

### Method
Deletion plus keyword removal.

### Details
- Keep the blank-line layout (two blank lines between top-level functions).

## Compatibility considerations
Test-only change.

## Security considerations
N/A: test code only.

## Rollback considerations
Revert the commit.

## Validation plan
- `uv run pytest tests/eventbus/test_eventbus_replay_subscribe.py -q`; `rg "offsets" tests/eventbus/test_eventbus_replay_subscribe.py` returns no match.

## Completion criteria
- The helper test and the key are gone and the remaining tests pass (REQ-002, REQ-004; Plan AC-1, AC-4).

## Out of Scope
Every other file of the Plan (each has its own procedure document); ADR text (Plan UNK-01); deleting `/opt/llm/offsets` (Plan UNK-03); offset storage, monotonic advancement, ACK-advanced offsets, and resume computation.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Delete the helper test and the fixture keyword | Completed | 20261022-134018 | 20261022-134018 | Changed: see commit |
| 2 | Run the file's tests and the validation sequence (`rules/toolchain.md`) | Completed | 20261022-134018 | 20261022-134018 | Verified: tests/eventbus 324 passed, full suite 9649 passed; ruff, mypy, lint-imports, docs checkers pass |

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
- **Requirement ID**: `REQ-002` (remove the helper test), `REQ-004` (drop the key from fixtures)
- **Source issue**: `issues/20261022-124119_offhelper_remove-unused-file-offset-helpers.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261022-125806_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261022-132500
- **Related target files**: `tests/eventbus/test_eventbus_replay_subscribe.py`