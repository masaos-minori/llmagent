## Goal

Move the Memory command tests from the flag-based approval and direct-SQLite expectations to registry approval, async handlers, service-layer routing, and verified outcomes (REQ-003, REQ-004, REQ-005, REQ-006, REQ-009; AC-3, AC-4, AC-5, AC-6, AC-9).

## Scope
**Release unit**: R3-memory-approval (Phase 3); the service-layer routing assertions are R5-memory-layering (Phase 5)

- In scope: the `--confirm` flag behavior assertions and the direct `SQLiteHelper` mock expectations.

## Assumptions

- `--confirm` and `--allow-loss` remain recorded grants, so the test asserts they are recorded on the job rather than that they authorize the run.
- The handlers become async, so the tests await them; the behavior asserted is the same.

## Design decisions

- Assert approval through the registry decision: a run with `ApprovalLevel.NONE` starts without a grant, `confirm` and `guard` are refused without the request-bound confirmation. That is the contract REQ-003 establishes, and a flag-only assertion cannot express it.

## Alternatives considered

- Keeping the flag assertions and adding a separate registry test — rejected: the flag is no longer the authority, so a flag assertion would lock behavior the requirement removes.

## Implementation
### Target file
`tests/agent/commands/test_cmd_memory.py`

### Procedure
1. Replace the flag-based approval expectations with registry approval-level expectations for the Memory maintenance subcommands.
2. Assert the handler runs as a tracked job and reports the job id and terminal state.
3. Replace the direct `SQLiteHelper` mock with the `MemoryStore` accessor path through `MemoryServices`.
4. Assert the postcondition runs before the success line, and the repair guidance names the registered `/memory reindex --fts` / `/memory reindex --vec` forms.

### Method

- Use the factory-built context so the test exercises the single registry instance rather than a locally constructed one.

### Details

- The `ValueError` case for `backup` without `allow_loss` (`scripts/agent/memory/import_ops.py:81-83`) is still asserted; the message names the job id when the run was registered.

### Companion test files

- None; this row is its own document. It is named by rows 5, 6, 7, 8.

## Compatibility considerations

- Runs with rows 5, 6, 7, 8; the pin-limit and delete-consistency assertions live in `tests/agent/commands/test_memory_data_ops.py` (row 45).

## Security considerations

- N/A: test.

## Rollback considerations

- N/A: revert the Phase 3 commit; the routing assertions are a Phase 5 commit.

## Validation plan

| Target | Strategy | Command | Expected outcome |
|---|---|---|---|
| `tests/agent/commands/test_cmd_memory.py` | Unit | `uv run pytest tests/agent/commands/test_cmd_memory.py tests/agent/commands/test_memory_rebuild_guard.py tests/agent/commands/test_memory_status.py tests/agent/commands/test_memory_consistency.py -q` | Registry approval, async handlers, guidance names registered commands, postcondition before success |
| Same area | Static grep gate (AC-5) | `rg -n "SQLiteHelper" scripts/agent/commands/` | No Memory maintenance construction remains |

## Completion criteria

- The test fails if a run is authorized by a flag alone, if success is reported before the postcondition, or if a command mixin still reaches SQLite directly.

## Out of Scope

- The handler implementations, the store accessors.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Replace flag-based approval with registry approval expectations | Completed | — | 20261124-180503 | Phase 3 Approval expectations are the registry decision: a run with no recorded grant is refused, the flags are asserted as recorded grants on the job. The fixture owns one MaintenanceJobRegistry and the command path reaches it. |
| 2 | Replace the direct-SQLite mocks with the service-layer path | Completed | 20261125-003636 | 20261125-003636 | Phase 5 Phase 5 part done: the fixture builds the context through the store accessor path (mock MemoryStore on MemoryServices) and owns one MaintenanceJobRegistry that the command path reaches; no direct SQLiteHelper mock remains in this file and the AC-5 grep gate over scripts/agent/commands/ is empty. |
| 3 | Assert the postcondition and the corrected guidance | Completed | — | 20261124-192923 | Phase 3, Phase 4 Phase 3 part done: the repair guidance names /memory reindex --fts and --vec, and the run reports the job id and terminal state. The postcondition-before-success assertion is the Phase 4 part. Phase 4 part done: TestMemoryRunsAsTrackedJobs asserts the check table is emitted before the success line, and that an unverified postcondition reports the check result with no success line while the job record carries verified=False. 17 tests in this file pass. |
| 4 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261125-003636 | 20261125-003636 | Phase 3 files pass: test_cmd_memory.py 15, test_memory_rebuild_guard.py 14, test_memory_consistency.py 28. The service-layer routing assertion is the Phase 5 part. Phase 4 gates: ruff, ruff format and the targeted pytest pass. The service-layer routing assertion is the Phase 5 part, and the mypy findings in this file are the pre-existing baseline from the MagicMock-typed fixtures, present at HEAD as well. Phase 5 part done: the service-layer routing assertion (reindex routes to MemoryRebuildOps.reindex) and the postcondition-before-success assertion are in place; 17 tests pass. |

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
- **Requirement ID**: REQ-003 (approval levels), REQ-004 (verified result), REQ-005 (Memory service-layer boundary), REQ-006 (tracked Memory work), REQ-009 (guidance names registered commands)
- **Source issue**: issues/20261119-145301_cliplc003_maintenance-job-framework.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261124-001800_cliplc003_maintenance-job-framework.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261124-122732
- **Related target files**: `tests/agent/commands/test_cmd_memory.py`