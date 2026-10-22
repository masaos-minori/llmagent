## Goal
Remove `offsets_dir` from the `EventBusConfig(...)` construction so the fixture matches the configuration model (REQ-004: the field no longer exists).

## Scope
- In: remove the 1 `offsets_dir` reference(s) in this file (keyword argument(s) of `EventBusConfig(...)` and any directory they pointed to that nothing else uses).
- Out: every other fixture value and test.

## Assumptions
- `rg -c offsets_dir tests/eventbus/test_eventbus_consumer_authorization.py` reports 1 at planning time; re-count before editing.
- Another active plan (`plans/20261022-130338_plan.md`) also edits some EventBus test files: re-read the file before editing and keep unrelated edits.

## Design decisions
- Drop only the keyword; if a `tmp_path / "offsets"` directory was created solely for it, drop that line too.

## Alternatives considered
N/A: a mechanical fixture edit with no alternative.

## Implementation
### Target file
`tests/eventbus/test_eventbus_consumer_authorization.py`

### Procedure
1. `rg -n offsets_dir tests/eventbus/test_eventbus_consumer_authorization.py`.
2. Delete each `offsets_dir=...` keyword (and an `offsets` directory creation that nothing else reads).
3. `uv run ruff check tests/eventbus/test_eventbus_consumer_authorization.py` and drop unused imports or variables.
4. Run the file's tests.

### Method
Keyword removal.

### Details
- Apply in the Plan's order; this row can run once `scripts/eventbus/config.py` no longer defines the field (seq 02) — until then the suite fails on `unexpected keyword argument`.
- If an assertion reads the offsets directory, keep the SQLite-based assertion and drop the file-based one; report a `Plan Gap` if the test's purpose depends on the directory.

## Compatibility considerations
Test-only change.

## Security considerations
N/A: test code only.

## Rollback considerations
Revert the commit.

## Validation plan
- `uv run pytest tests/eventbus/test_eventbus_consumer_authorization.py -q`; `rg offsets_dir tests/eventbus/test_eventbus_consumer_authorization.py` returns no match.

## Completion criteria
- No `offsets_dir` remains in the file and its tests pass (REQ-004; Plan AC-4).

## Out of Scope
Every other file of the Plan (each has its own procedure document); ADR text (Plan UNK-01); deleting `/opt/llm/offsets` (Plan UNK-03); offset storage, monotonic advancement, ACK-advanced offsets, and resume computation.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Remove the `offsets_dir` keyword(s) | Completed | 20261022-134028 | 20261022-134028 | Changed: see commit |
| 2 | Run the file's tests and the validation sequence (`rules/toolchain.md`) | Completed | 20261022-134028 | 20261022-134028 | Verified: tests/eventbus 324 passed, full suite 9649 passed; ruff, mypy, lint-imports, docs checkers pass |

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
- **Requirement ID**: `REQ-004` (drop the removed key from this fixture)
- **Source issue**: `issues/20261022-124119_offhelper_remove-unused-file-offset-helpers.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261022-125806_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261022-132500
- **Related target files**: `tests/eventbus/test_eventbus_consumer_authorization.py`