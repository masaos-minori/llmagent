## Goal
Move the validator's unit tests out of the shared test tree to mirror the module's new location. (REQ-003 of the Plan)

## Scope
- Only this file's change as described below; behavior of the validator is unchanged.

## Assumptions
- The user chose to move the validator module into the agent package (not to inject its dependencies) and, for the shared documents, a one-line pointer to the agent configuration document.
- Procedures are applied in sequence number order; the module move (01) and test move (06) come first so later rows build on the new paths.

## Design decisions
- Mechanical path change only; no backward-compatibility re-export at the old path.

## Alternatives considered
- Injecting the validator's dependencies from the agent side: rejected by the user's choice.

## Implementation
### Target file
tests/shared/test_production_config_validator.py

### Procedure
1. Run `git mv tests/shared/test_production_config_validator.py tests/agent/test_production_config_validator.py` (this row records the removal; procedure 07 records the new file).

### Method
Mechanical edit or `git mv`; no change to function bodies or assertions.

### Details
The move keeps history; the content change is recorded in procedure 07.

## Compatibility considerations
- No behavior change; the old path disappears, so every importer is updated in the same change.

## Security considerations
- None: no validation rule changes.

## Rollback considerations
- Revert the commit.

## Validation plan
- `ls tests/shared/test_production_config_validator.py` fails after the move.

## Completion criteria
- The old test path no longer exists.

## Out of scope
- Any change to validation rules and any file not listed in the Plan.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Apply the change described in Implementation | Completed | 20261008-161340 | 20261008-161340 |  |
| 2 | Run the validation commands | Completed | 20261008-161340 | 20261008-161340 |  |

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
- **Requirement ID**: REQ-003
- **Source issue**: issues/20261008-115809_shareddeps01_remove-agent-imports-from-the-shared-production-config-validator.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261008-155632_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261008-160214
- **Related target files**: tests/shared/test_production_config_validator.py