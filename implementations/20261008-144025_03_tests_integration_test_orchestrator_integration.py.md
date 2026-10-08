## Goal
Rewrite every wrapper-based call in the Orchestrator integration tests to call the owning component (REQ-003 of the Plan).

## Scope
- Edit the integration test module only, at the wrapper call sites.

## Assumptions
- Same assumptions as the unit test procedure.

## Design decisions
- Mechanical call-target change; assertions unchanged.

## Alternatives considered
- Leaving the integration tests on the wrappers: rejected; the wrappers are being deleted.

## Implementation
### Target file
tests/integration/test_orchestrator_integration.py

### Procedure
1. Apply the replacement map to each call site (history compression, turn processing, workflow task initialization, memory injection, user-message append, system-prompt sync).
2. Run the module.

### Method
Replacement map (each wrapper call becomes a call to the owning component, with identical arguments and assertions): history compression, ephemeral-message clearing, memory injection, user-message append, and system-prompt sync go to the conversation state manager's public methods of the same name without the leading underscore; the background-task discard-and-log wrapper goes to the background task monitor's task-done method; the pause-state property goes to the monitor's pause-state property; the workflow-task initialization goes to the workflow adapter's private method of the same name (same signature); the workflow-engine wrapper goes to the adapter's turn-execution method with the arguments (line, turn start time, empty session id); and the orchestrator's own turn-processing method goes to the adapter's identical turn-processing method (same signature).

### Details
- No production behavior change.

## Compatibility considerations
- Fake values only.

## Security considerations
- `uv run ruff format` and `ruff check` on the file; `uv run pytest tests/integration/test_orchestrator_integration.py -q --timeout=60`.

## Rollback considerations
- Revert the commit.

## Validation plan
- No wrapper call remains; the module passes (REQ-003).

## Completion criteria
- Production code and other modules.

## Out of scope
REQ-003 (rewrite wrapper callers)

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|


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
- **Requirement ID**: tests/integration/test_orchestrator_integration.py
- **Source issue**: issues/20261007-153934_wfstartup01_stop-agent-startup-when-workflow-loading-fails.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261008-143632_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261008-144025
- **Related target files**: | 1 | Rewrite wrapper-based calls | Pending | — | — | |
| 2 | Run the module | Pending | — | — | |
