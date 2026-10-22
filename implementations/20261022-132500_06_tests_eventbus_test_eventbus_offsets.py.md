## Goal
Remove the file-helper tests and the startup-ignores-files test, drop `offsets_dir` from the fixture, and keep the SQLite and ACK-advanced offset tests (REQ-002 and REQ-004).

## Scope
- In: delete classes `TestConsumerIdSanitization`, `TestFileOffsetMonotonicity`, `TestFileOffsetIdentityValidation`, `TestCrashResistance`, `TestMalformedContent`, `TestStartupIgnoresOffsetFiles` and the `legacy_offset_files` fixture; remove the `offsets_dir=` argument of the `client` fixture; reword the module docstring sentence that names `write_offset`; remove now-unused imports and `tmp_path` offsets-directory use.
- Out: `TestSqliteOffsetMonotonicity`, `TestConsumerOffsetsTable`, and the module-level tests (`test_ack_writes_offset`, `test_reconnect_resume_via_consumer_id`, `test_offset_not_advanced_without_ack`, `test_consumer_id_stability`).

## Assumptions
- Class boundaries were verified at lines 212, 297, 438, 448, 571, 613, and 667; the `TestStartupIgnoresOffsetFiles` class sits between two kept classes, so delete by class, not by line range across classes.
- `test_ack_writes_offset(client, tmp_path)` takes `tmp_path`; check whether it inspects the offsets directory before editing and keep only the SQLite assertions.

## Design decisions
- Delete classes whole rather than editing tests one by one.
- After deletion, remove unused imports flagged by `ruff` instead of guessing.

## Alternatives considered
Keeping the startup-ignores-files test against a removed key was rejected: it asserts a behavior that no longer exists.

## Implementation
### Target file
`tests/eventbus/test_eventbus_offsets.py`

### Procedure
1. Delete the six classes and the `legacy_offset_files` fixture (by class boundaries).
2. Remove `offsets_dir=str(tmp_path / "offsets")` from the `client` fixture (about line 64).
3. Reword the module docstring so it no longer names `write_offset`.
4. Run `uv run ruff check tests/eventbus/test_eventbus_offsets.py` and drop unused imports.
5. Run the file's tests.

### Method
Deletion plus fixture keyword removal; no new symbol.

### Details
- Delete `TestCrashResistance` and `TestMalformedContent` bodies together with their `from eventbus.offsets import ...` imports inside the tests.
- The remaining tests exercise `ack_event_for_consumer()` and the `consumer_offsets` table and must pass unchanged.

## Compatibility considerations
Test-only change.

## Security considerations
N/A: test code only.

## Rollback considerations
Revert the commit.

## Validation plan
- `uv run pytest tests/eventbus/test_eventbus_offsets.py -q`, then `uv run pytest tests/eventbus -q`; `rg "offsets_dir|eventbus\.offsets|write_offset|read_offset" tests/eventbus/test_eventbus_offsets.py` returns no match.

## Completion criteria
- No reference to the removed helpers or key remains; the SQLite offset and ACK tests pass (REQ-002, REQ-004; Plan AC-1, AC-4).

## Out of Scope
Every other file of the Plan (each has its own procedure document); ADR text (Plan UNK-01); deleting `/opt/llm/offsets` (Plan UNK-03); offset storage, monotonic advancement, ACK-advanced offsets, and resume computation.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Delete the helper test classes, the fixture, and the startup-ignores-files test | Pending | — | — | |
| 2 | Remove `offsets_dir` from the `client` fixture and fix the docstring | Pending | — | — | |
| 3 | Run the file's tests and the validation sequence (`rules/toolchain.md`) | Pending | — | — | |

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
- **Requirement ID**: `REQ-002` (remove the helper tests), `REQ-004` (drop the key from fixtures)
- **Source issue**: `issues/20261022-124119_offhelper_remove-unused-file-offset-helpers.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261022-125806_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261022-132500
- **Related target files**: `tests/eventbus/test_eventbus_offsets.py`
