# Implementation Procedure: Documentation Clarification on Process Cleanup

## Goal
Clarify in relevant documentation that "when `start_new_session=True` is used, child processes may not be cleaned up via process group termination".

## Scope
- `docs/05_agent_10_01_operations-and-observability-startup-and-health.md`

## Assumptions
- The user needs to be aware of potential orphan processes when using certain configurations.

## Design decisions
- Place the information under the "Shutdown" or "Operational Verification" sections where lifecycle management is discussed.

## Alternatives considered
- N/A

## Implementation

### Target file
- `docs/05_agent_10_01_operations-and-observability-startup-and-health.md`

### Procedure
1. Open `docs/05_agent_10_01_operations-and-observability-startup-and-health.md`.
2. Locate the section discussing shutdown or MCP subprocesses.
3. Add the following note: "Note: When `start_new_session=True` is used, child processes may not be cleaned up via process group termination."

### Method
Append text to the identified documentation file.

### Details
Targeting the end of the "Startup Procedure" or "Operational Verification" section.

## Compatibility considerations
N/A

## Security considerations
N/A

## Rollback considerations
N/A

## Validation plan
- Manual review of the updated documentation to ensure clarity and correct placement.

## Out of scope
- Updating all other documentation files.

## Traceability
- Workflow phase: plan-to-implementation-procedure
- Source issue: N/A
- Source requirement: N/A
- Source plan: plans/20260731-085048_plan.md
- Source implementation procedure: N/A
- Generated at: 20260731-212541
- Related target files: docs/05_agent_10_01_operations-and-observability-startup-and-health.md
