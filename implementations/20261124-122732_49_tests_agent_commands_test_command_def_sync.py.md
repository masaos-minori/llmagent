## Goal

Assert that the `/jobs` `CommandDef` handler resolves on the registry and that the new handler has a command definition, so the sync between the definition list and the registry holds for the job commands (REQ-010; AC-7).

## Scope
**Release unit**: R2-job-commands (Phase 2)

- In scope: the handler-mapping and `/help` coverage expectations.

## Assumptions

- The test already requires every `CommandDef.handler` to exist on the registry and every registry `_cmd_*` to have a `CommandDef`; the change is that the job commands and `_cmd_jobs` are now part of the expected set.

## Design decisions

- Extend the existing expectations rather than adding a new test file, because this file is the contract that keeps the definition list and the registry in sync.

## Alternatives considered

- Hard-coding the handler name in a new test — rejected: it would duplicate the contract already asserted here.

## Implementation
### Target file
`tests/agent/commands/test_command_def_sync.py`

### Procedure
1. Include `/jobs` and its subcommands in the definition set the test walks.
2. Assert the handler name matches the value registered in `command_defs_list.py` (row 9) and resolves to `_cmd_jobs` in an existing mixin (row 10).
3. Keep the `/help` coverage expectations for the new command.

### Method

- No new fixture; the test builds the registry through the existing path.

### Details

- N/A: no other expectation changes.

## Compatibility considerations

- Runs with rows 9, 10, 53, 56, 63 in the same phase; the handler name must match exactly or this test fails.

## Security considerations

- N/A: test.

## Rollback considerations

- N/A: revert the Phase 2 commit.

## Validation plan

| Target | Strategy | Command | Expected outcome |
|---|---|---|---|
| `tests/agent/commands/test_command_def_sync.py` | Unit | `uv run pytest tests/agent/commands/test_command_def_sync.py -q` | `/jobs` handler mapping and `/help` coverage pass |

## Completion criteria

- The test fails if a job command has a definition without a handler, or a handler without a definition.

## Out of Scope

- The registration list, the handler implementation.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Extend the handler-mapping and `/help` expectations | Pending | — | — | Phase 2 |
| 2 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |

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
- **Requirement ID**: REQ-010 (every registered command has a handler in the registry)
- **Source issue**: issues/20261119-145301_cliplc003_maintenance-job-framework.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261124-001800_cliplc003_maintenance-job-framework.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261124-122732
- **Related target files**: `tests/agent/commands/test_command_def_sync.py`
