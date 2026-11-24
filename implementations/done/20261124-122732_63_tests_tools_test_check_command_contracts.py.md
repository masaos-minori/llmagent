## Goal

Extend the command-contract expectations to the job commands, so the contract check covers the registered set as it now is (REQ-010; AC-7).

## Scope
**Release unit**: R2-job-commands (Phase 2)

- In scope: the contract expectations in `tests/tools/test_check_command_contracts.py`, which build `CommandDef` instances and call the checker imported from `tools.check_docs_consistency` (`:17`).

## Assumptions

- The checker itself is unchanged; the test's expected registry fixture gains the `/jobs` entries so the contract and coverage paths exercise the new command.

## Design decisions

- Keep the test read-only: it asserts the checker accepts the job commands, it does not enforce behavior the registry decides.

## Alternatives considered

- Adding a separate test file for the job-command contract — rejected: this file is the contract test for `check_command_contracts`; a second file would duplicate the fixture.

## Implementation
### Target file
`tests/tools/test_check_command_contracts.py`

### Procedure
1. Add the `/jobs` `CommandDef` and its `SubcommandSpec` entries to the fixture the test walks.
2. Keep the existing expectations for the other commands unchanged.

### Method

- No new fixture; extend `_REGISTRY`.

### Details

- The coverage expectations for the Built-in Command Index row are in `tests/tools/test_check_docs_consistency_checks.py` (row 64, covered by row 35); this row does not duplicate them.
- The fixture entry is written identically to the registered definition and a test compares the two, so a drift between the fixture and `_COMMANDS` is reported rather than hidden; the positive fixture chapter is extended with the two usage lines.
- A test asserts that the two usage lines appear as code spans in `agent_07_07`, which is the part the Phase 2 gate needs; the chapter text itself is row 23's work.

## Compatibility considerations

- Runs with row 9 in the same phase; the test's entries must match the registered names and subcommands exactly.

## Security considerations

- N/A: test.

## Rollback considerations

- N/A: revert the Phase 2 commit.

## Validation plan

| Target | Strategy | Command | Expected outcome |
|---|---|---|---|
| `tests/tools/test_check_command_contracts.py` | Unit | `uv run pytest tests/tools/test_check_command_contracts.py -q` | Contract expectations pass with the job commands |
| Same area | Checker | `uv run python tools/check_docs_consistency.py` | Command coverage and contract pass |

## Completion criteria

- The contract checker accepts `/jobs`, `/jobs status <id>`, and `/jobs cancel <id>`, and the test reports no gap.

## Out of Scope

- The registration list, the coverage test (row 64), the documentation rows.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Extend the contract fixture to the job commands | Completed | — | 20261124-165333 | Phase 2 Fixture extended with the /jobs CommandDef written identically to the registered entry, plus a fixture-vs-registry comparison test and an assertion that both usage lines appear as code spans in the chapter. |
| 2 | Run the validation sequence (`rules/toolchain.md`) | Completed | — | 20261124-165333 | 11 tests pass, including the live-docs test; the checker reports no command-contract finding. |

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
- **Requirement ID**: REQ-010 (command contract for the registered set)
- **Source issue**: issues/20261119-145301_cliplc003_maintenance-job-framework.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261124-001800_cliplc003_maintenance-job-framework.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261124-122732
- **Related target files**: `tests/tools/test_check_command_contracts.py`