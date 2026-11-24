## Goal

Assert that the retired RAG vector subcommand stays unregistered after the rename, so the rename does not reintroduce the old name as an alias (REQ-007; AC-8).

## Scope
**Release unit**: R6-rag-vector-contract (Phase 6)

- In scope: the removed-command expectations.

## Assumptions

- The decision is `/session rag-prune-vec` (plan decision OD-01, 2026-11-24); the retired name is not an alias, so it stays in the removed set.

## Design decisions

- Add `rag-rebuild-vec` to the removed-name expectations rather than removing the check, because the plan's decision is that the old name must not resolve.

## Alternatives considered

- Treating the rename as a removal of the command and dropping it from the registry — rejected: the operation is still registered, only under a name that matches what it does.

## Implementation
### Target file
`tests/agent/commands/test_removed_commands.py`

### Procedure
1. Add the retired vector subcommand name to the set the test asserts is unregistered.
2. Keep the other removed-command expectations unchanged.

### Method

- No new fixture; the test reads the registered command set from `command_defs_list.py` (row 9).

### Details

- N/A: no other expectation changes.

## Compatibility considerations

- Runs with row 9 in the same phase; the completion set (row 11) must not offer the retired name either.

## Security considerations

- N/A: test.

## Rollback considerations

- N/A: revert the Phase 6 commit.

## Validation plan

| Target | Strategy | Command | Expected outcome |
|---|---|---|---|
| `tests/agent/commands/test_removed_commands.py` | Unit | `uv run pytest tests/agent/commands/test_removed_commands.py -q` | The retired name stays unregistered |

## Completion criteria

- The test fails if the retired name is registered as an alias or appears in the completion candidates.

## Out of Scope

- The registration list, the guidance text.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add the retired subcommand to the removed-name expectations | Completed | 20261125-002740 | 20261125-002740 | Phase 6 Phase 6 (R6) done: TestRemovedRagVectorSubcommand asserts the retired name is not registered as a subcommand and does not appear in the /session help text, while the renamed name is. |
| 2 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261125-002740 | 20261125-002740 | Phase 6 part: ruff and ruff format clean; the file's tests pass. |

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
- **Requirement ID**: REQ-007 (name matching behavior)
- **Source issue**: issues/20261119-145301_cliplc003_maintenance-job-framework.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261124-001800_cliplc003_maintenance-job-framework.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261124-122732
- **Related target files**: `tests/agent/commands/test_removed_commands.py`