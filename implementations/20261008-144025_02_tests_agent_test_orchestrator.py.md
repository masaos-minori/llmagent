## Goal
Add construction-failure tests and rewrite every wrapper-based call in the Orchestrator unit tests to call the owning component, keeping each test's intent and assertions (REQ-003, REQ-004 of the Plan).

## Scope
- Edit the Orchestrator unit test module only: add the failure tests and change the call target at each wrapper call site; do not change assertions or fixtures beyond what a call-target change needs.

## Assumptions
- The wrappers delegate with identical arguments, so a call-target change preserves behavior.
- Tests patch only the state store, loader, and engine names on the orchestrator module; none patch the names the removal will drop.

## Design decisions
- Add tests first and confirm they fail against the fallback.
- Change call targets mechanically; run the module after each group (compression, workflow task, process turn, ephemeral messages, memory injection and prompt sync, discard-and-log, pause state, workflow engine).

## Alternatives considered
- Keeping wrappers only for tests: rejected; the policy forbids compatibility layers.

## Implementation
### Target file
tests/agent/test_orchestrator.py

### Procedure
1. Add tests: with the loader patched to raise the load error, construction raises a runtime error whose message contains the definition path and the cause text; with the loader raising a missing-file error the same; and no engine is built (the engine class is not called).
2. Run them and confirm they fail against the fallback.
3. Apply the replacement map group by group, running the module after each group.
4. Confirm no wrapper name remains in the file.

### Method
Replacement map (each wrapper call becomes a call to the owning component, with identical arguments and assertions): history compression, ephemeral-message clearing, memory injection, user-message append, and system-prompt sync go to the conversation state manager's public methods of the same name without the leading underscore; the background-task discard-and-log wrapper goes to the background task monitor's task-done method; the pause-state property goes to the monitor's pause-state property; the workflow-task initialization goes to the workflow adapter's private method of the same name (same signature); the workflow-engine wrapper goes to the adapter's turn-execution method with the arguments (line, turn start time, empty session id); and the orchestrator's own turn-processing method goes to the adapter's identical turn-processing method (same signature).

### Details
- No production behavior change in this file.

## Compatibility considerations
- Fake values only.

## Security considerations
- `uv run ruff format` and `ruff check` on the file; `uv run pytest tests/agent/test_orchestrator.py -q --timeout=60`.

## Rollback considerations
- Revert the commit.

## Validation plan
- The new tests exist and fail before the production change and pass after; no wrapper call remains; all other tests in the module keep passing (REQ-003, REQ-004).

## Completion criteria
- Other test modules (procedure 03 covers the integration module); production code.

## Out of scope
REQ-003 (rewrite wrapper callers), REQ-004 (failure tests)

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
- **Requirement ID**: tests/agent/test_orchestrator.py
- **Source issue**: issues/20261007-153934_wfstartup01_stop-agent-startup-when-workflow-loading-fails.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261008-143632_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261008-144025
- **Related target files**: | 1 | Add the construction-failure tests | Pending | — | — | |
| 2 | Rewrite wrapper-based calls group by group | Pending | — | — | |
| 3 | Run the module | Pending | — | — | |
