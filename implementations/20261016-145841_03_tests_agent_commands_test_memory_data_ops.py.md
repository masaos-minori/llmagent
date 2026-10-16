## Goal
- Cover the new `list`, `delete`, and `prune` behavior against the real `MemoryDataOps`, and update the tests that assert the removed forms.

## Scope
- `tests/agent/commands/test_memory_data_ops.py` only. `tests/agent/commands/test_agent_cmd_memory.py` re-implements the handlers in stubs and is not changed.

## Assumptions
- The file's existing helpers build `MemoryDataOps` with mock services and a mock output port; new tests reuse that pattern.
- `builtins.input` is patched to drive the confirmation; EOF is simulated with `side_effect=EOFError`.
- The prune tests patch the database layer the way the current prune-event test does (a patched `SQLiteHelper` and `db.maintenance.prune_old_memories`), with `SQLiteMemoryDeleteStore.collect_prunable_ids` patched to return ids.

## Design decisions
- Add test classes per behavior (`list` options, `delete` confirmation, `prune` options and confirmation); keep assertions on the output port writes.
- Update the existing tests that call `memory_prune(..., ["14"])` and the list tests that depend on the old limit or full IDs.

## Alternatives considered
N/A: a stub copy of the handler, as `test_agent_cmd_memory.py` does, was rejected because it does not exercise the real code.

## Implementation
### Target file
`tests/agent/commands/test_memory_data_ops.py`

### Procedure
- `TestMemoryListOptions` (new): default limit is 20; `n` of 0, 201, and `abc` are validation errors and list nothing; `--type semantic` and `--type bogus`; `--pinned` keeps only pinned entries even when more entries than `n` exist; `--query foo bar` calls the retriever with `foo bar`; `--source RULE` and `--branch main` are rejected as unknown options; output shows 8-character IDs.
- `TestMemoryDeleteConfirmation` (new): `y` and `YES` delete once; `n`, an empty answer, and `EOFError` do not call the delete function and write the cancellation message; an unknown or ambiguous id still reports M-03 or M-04 without prompting.
- `TestMemoryPruneOptions` (new): `--days 14` uses 14; no argument uses `memory_retention_days`; `--days`, `--days abc`, `--days 0`, `--days -3`, and the old positional `14` are validation errors that do not touch the database; zero prunable ids reports nothing to prune without prompting; a positive count prompts with the count and, on `n`, does not call `prune_old_memories`; on `y` it calls it once and emits one delete event per id; `--dry-run` still reports the count without prompting.
- Update `test_prune_appends_delete_event_per_id` and `test_prune_no_pruned_ids_emits_no_events` to the new argument form and to patch the confirmation answer.

### Method
- Patch `builtins.input` with `unittest.mock.patch`; use `MagicMock` for the output port and assert on `write`, `write_success`, and `write_validation_error` calls.
- Do not open a real database; patch `SQLiteHelper`, `collect_prunable_ids`, and `prune_old_memories` at the names `memory_data_ops` imports.

### Details
- Name tests only in this Procedure section; refer to them elsewhere by description.
- Run the new tests against the unmodified handlers first and record which fail (the confirmation, option, and short-ID tests are expected to fail; short-ID and existing-resolution tests that already hold pass).
- Respect `tools/check_mock_patch_targets.py`: patch where the code under test looks the name up.

## Compatibility considerations
N/A: tests only; the updated tests change because the contract changed (Plan REQ-001 to REQ-003).

## Security considerations
N/A: no real database or process is touched.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run pytest tests/agent/commands/test_memory_data_ops.py -v` (new tests fail before the handler change and pass after)
- `uv run ruff format tests/agent/commands/test_memory_data_ops.py`, `uv run ruff check tests/agent/commands/test_memory_data_ops.py`, `uv run mypy --no-namespace-packages tests/agent/commands/test_memory_data_ops.py` (compare with the baseline error count)
- `uv run python tools/check_mock_patch_targets.py`
- `uv run coverage run -m pytest tests/agent/commands`, `uv run coverage xml`, `uv run diff-cover coverage.xml --compare-branch=master --fail-under=90`

## Completion criteria
- The new classes exist and pass after the handler change; the tests tied to the new contract fail beforehand.
- No test depends on a real database; mypy has no new error in the file; diff coverage of `memory_data_ops.py` is at least 90% or the gap is recorded.

## Out of scope
- `tests/agent/commands/test_agent_cmd_memory.py`, the handler source, the registry, and docs.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Update the tests that assert the removed forms | Pending | — | — | |
| 2 | Add the list, delete, and prune test classes | Pending | — | — | |
| 3 | Run the new tests against the unmodified handlers and record the result | Pending | — | — | |
| 4 | Run the validation sequence (`rules/toolchain.md`) after the code change | Pending | — | — | |

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
- **Requirement ID**: REQ-001, REQ-002, REQ-003 (handler tests)
- **Source issue**: issues/20261014-155503_mem001_implement-memory-command-spec.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261016-143248_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261016-145841
- **Related target files**: tests/agent/commands/test_memory_data_ops.py
