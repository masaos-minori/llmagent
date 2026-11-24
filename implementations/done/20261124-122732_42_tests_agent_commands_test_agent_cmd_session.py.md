## Goal

Update the Session command tests so maintenance calls are asserted as job-recorded runs with verified or interrupted outcomes, and the renamed RAG vector subcommand is the name used (REQ-001, REQ-004, REQ-007; AC-1, AC-4, AC-8).

## Scope
**Release unit**: R6-rag-vector-contract (Phase 6); the job-record and outcome assertions are R1-registry-core (Phase 1)

- In scope: the assertions that pin the current message text and dispatch shape, including the `rag-rebuild-vec` references at `tests/agent/commands/test_agent_cmd_session.py:1158,1175`.

## Assumptions

- The message must report the job id and the terminal state, so the test asserts the reported state rather than a fixed success string.
- The retired name is not an alias, so the test must not accept it.

## Design decisions

- Assert the outcome through the job record, not through a captured print, so an interrupted run and a verified run are distinguished in the test — that is the behavior AC-4 requires.

## Alternatives considered

- Keeping the string assertions and adding the job id to the expected text — rejected: the string is not the contract; the verified/interrupted distinction is.

## Implementation
### Target file
`tests/agent/commands/test_agent_cmd_session.py`

### Procedure
1. Replace the `rag-rebuild-vec` references at `:1158,1175` with the renamed subcommand.
2. Assert that a maintenance call through `db_dispatch` records a job and reports the job id and terminal state.
3. Add an interrupted-outcome case: a run stopped at a progress callback reports `cancelled`, not success.

### Method

- Use the existing fixture that builds the registry through the factory path, so the test exercises the single registry instance.

### Details

- N/A: no other assertion in the file changes.

### Companion test files

- None; this row is its own document. It is named by rows 3 and 4.

## Compatibility considerations

- Runs with rows 3, 20, 22 in the same phase; the message format comes from row 4.

## Security considerations

- N/A: test.

## Rollback considerations

- N/A: revert the Phase 6 commit; the job-record assertions are a Phase 1 commit.

## Validation plan

| Target | Strategy | Command | Expected outcome |
|---|---|---|---|
| `tests/agent/commands/test_agent_cmd_session.py` | Unit | `uv run pytest tests/agent/commands/test_agent_cmd_session.py -q` | Job-recorded calls, verified and interrupted outcomes, renamed subcommand |

## Completion criteria

- The test fails if a maintenance run is not recorded, if success is reported before the postcondition, or if the retired name is accepted.

## Out of Scope

- The command implementation, the service layer.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add the job-record and outcome assertions | Completed | — | 20261124-192923 | Phase 1 Phase 1 part done: TestCmdSessionJobRecords asserts a maintenance call records a job and reports job {job_id} {terminal state}, and that a run stopped at a progress callback reports cancelled. 78 passed. Deviation: the existing fixture builds the registry directly on ctx.services rather than through the factory path, and the fixture patches the approval answer; message assertions that no longer hold (Purged, kept active session 1) compare the emitted line with the job record instead. Phase 4 part: the reported outcome is compared with the job record, and the measured postcondition values are asserted through the end-to-end purge test (rows_before and rows_after equal the rows the connection still holds); an unverified run is asserted to produce no success line. 79 tests pass. |
| 2 | Replace the retired subcommand name | Completed | 20261125-002740 | 20261125-002740 | Phase 6 Phase 6 (R6) done: TestCmdSessionRagPruneVec asserts the renamed subcommand, the measured pruned and remaining counts through the job record, a stopped run reported as cancelled, and that the retired name records no job. The FTS tests now assert the job record instead of the fixed success line. |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261125-002740 | 20261125-002740 | Phase 1 part: ruff and targeted pytest pass. Phase 4 part: ruff and ruff format clean; the file's existing mypy baseline is unchanged apart from the same nullable-`AppServices` union-attr pattern the file already uses. Two fixture connections now carry sqlite3.Row because the service postcondition counts through count_table. Phase 6 part: ruff and ruff format clean; 91 tests pass in tests/agent/commands. |

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
- **Requirement ID**: REQ-001 (job commands), REQ-004 (verified result before the success line), REQ-007 (name matching behavior)
- **Source issue**: issues/20261119-145301_cliplc003_maintenance-job-framework.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261124-001800_cliplc003_maintenance-job-framework.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261124-122732
- **Related target files**: `tests/agent/commands/test_agent_cmd_session.py`