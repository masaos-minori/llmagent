## Goal

Assert that the Memory consistency check result is part of the reported job outcome, so a run that did not verify cannot report success (REQ-004; AC-4).

## Scope
**Release unit**: R4-verified-results (Phase 4)

- In scope: the tests that exercise the consistency check before the success line.

## Assumptions

- The consistency check itself is unchanged; what changes is where its result is reported — in the job outcome rather than as a separate line before the success message.

## Design decisions

- Assert the ordering: the outcome reports the check result, and the success line is emitted only when the postcondition is true. A test that asserts only the check output cannot show the ordering.

## Alternatives considered

- Keeping the existing success-line assertions — rejected: they lock the pre-framework behavior the requirement removes.

## Implementation
### Target file
`tests/agent/commands/test_memory_consistency.py`

### Procedure
1. Assert the consistency result is carried into the job outcome before any success line.
2. Add a case where the postcondition fails and the reported outcome is the check result, not success.

### Method

- Use the factory-built context so the job record is the same instance the handler uses.

### Details

- N/A: no other assertion changes.

## Compatibility considerations

- Runs with row 5 in the same release unit; the result shape is defined by row 5 (`RebuildResult.verified`).

## Security considerations

- N/A: test.

## Rollback considerations

- N/A: revert the Phase 4 commit.

## Validation plan

| Target | Strategy | Command | Expected outcome |
|---|---|---|---|
| `tests/agent/commands/test_memory_consistency.py` | Unit | `uv run pytest tests/agent/commands/test_memory_consistency.py -q` | Consistency outcome is part of the reported job result |

## Completion criteria

- The test fails when a run reports success without the postcondition being measured.

## Out of Scope

- The handler implementation, the registry.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Assert the consistency result is folded into the job outcome | Completed | — | 20261124-192923 | Phase 4 Phase 3 part recorded: the async call sites in this file are awaited and the fixture now supplies the real registry, so the run and its job record are the same instance. Phase 4 adds the ordering assertion and the failed-postcondition case. Phase 4 part done: TestCmdMemoryRebuild asserts the check result is folded into the reported outcome, that the check table is emitted before the success line, and that an unverified run reports the check with no success line. 30 tests pass. |
| 2 | Run the validation sequence (`rules/toolchain.md`) | Completed | — | 20261124-192923 | ruff and ruff format clean; the file is at its pre-existing mypy baseline from the fixture-typed mixins. Targeted pytest passes. No docs row is affected: the repair guidance is not named in any chapter document. |

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
- **Requirement ID**: REQ-004 (verified result before the success line)
- **Source issue**: issues/20261119-145301_cliplc003_maintenance-job-framework.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261124-001800_cliplc003_maintenance-job-framework.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261124-122732
- **Related target files**: `tests/agent/commands/test_memory_consistency.py`