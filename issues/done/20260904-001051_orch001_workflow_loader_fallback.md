# Add workflow loader fallback mode to Orchestrator.__init__

## Summary

Orchestrator.__init__ raises RuntimeError if WorkflowLoader fails, preventing REPL startup entirely. There's no fallback mode or graceful degradation. Any deployment without a valid workflow definition is completely broken.

## Background

Workflow definitions are loaded at REPL startup time. Missing workflow files cause hard crashes with no recovery path.

## Problem

No graceful degradation: users cannot start the REPL without a workflow definition, even if they want to use basic REPL functionality.

## Reason for Change

Deployment reliability: the REPL should have a minimum viable mode that works without workflows, allowing users to interact with the system even if workflow features are unavailable.

## Implementation Intent

Option A: Add a --no-workflow flag that skips workflow loading and disables workflow-dependent commands. Option B: Load a built-in default workflow if the configured one is missing. Option C: Log a warning and continue with limited functionality. Choose the approach that matches the project's operational philosophy — whether workflows are required or optional.

## Target Files or Areas

- scripts/agent/orchestrator.py
- scripts/agent/__main__.py (if CLI flag needed)

## Required Changes

- Add fallback mode for missing workflow definitions
- Either disable workflow commands or load a built-in default
- Update CLI argument parsing if a new flag is introduced

## Constraints

- Must not change the workflow loading behavior when a valid definition exists
- Must preserve existing error messages for intentional misconfiguration

## Out of Scope

- Adding new workflow formats
- Changing the workflow validation logic

## Dependencies

N/A: none

## Acceptance Criteria

- [ ] REPL starts without a workflow definition (in fallback mode)
- [ ] Workflow-dependent commands are disabled or show appropriate error
- [ ] Normal workflow loading continues to work unchanged

## Testing Expectations

- Integration test: start REPL without workflow file, verify graceful degradation
- Verify workflow commands show appropriate error messages

## Documentation Impact

Document the fallback mode behavior in the CLI help text and any relevant docs.

## Priority

Low

## AI Implementation Instruction

Add fallback mode only. Do not change workflow loading when a valid definition exists. Preserve existing error messages for intentional misconfiguration. Stop and report if the project's policy on workflow requirements is unclear.
