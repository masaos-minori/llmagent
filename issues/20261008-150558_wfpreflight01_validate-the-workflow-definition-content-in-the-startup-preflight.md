# Validate the workflow definition content in the startup preflight

## Priority
Low

## Summary
The startup preflight only checks that the default workflow definition file exists; a malformed file passes the preflight and is rejected later by the Orchestrator constructor. Decide whether the preflight should also validate the content so the failure is reported by the preflight with its usual message.

## Background
Found while making a workflow load failure fatal. The preflight check raises a runtime error for a missing file, and the Orchestrator constructor now raises one for a file that exists but cannot be loaded.

## Problem
- The preflight function checks `default.json` existence only; invalid JSON, a wrong shape, or missing required stages pass it.
- The failure is still fatal (the constructor fails), but it is reported from a different place and message than the other preflight failures, and some preflight-time cleanup or reporting that runs only for preflight failures does not run.

## Reason for Change
Consistent, early failure reporting helps operators; the check is cheap and the loader already contains the validation.

## Implementation Intent
- Have the preflight load the definition through the same loader (or a validation function from it) and raise a runtime error naming the file and cause; keep the constructor's own error as the last line of defense.

## Target Files or Areas
- `scripts/agent/services/workflow_schema.py` (the preflight check)
- `tests/agent/test_startup_workflow_preflight.py`

## Required Changes
- Extend the check to validate content with the loader; reuse the loader's error text.
- Add tests for a malformed file and a file missing a required stage.

## Constraints
- Do not duplicate the loader's validation rules; call into it.
- Keep the existing preflight messages for the missing-file case.

## Acceptance Criteria
- A malformed definition makes the preflight raise a runtime error naming the file and cause, before the Orchestrator is constructed.
- Existing preflight and Orchestrator tests pass.

## Testing Expectations
Unit tests for the preflight with malformed and incomplete definitions; the agent test directory; the full suite once.

## Documentation Impact
Only if the startup documentation lists what the preflight checks (verify and update).

## Out of Scope
- Changing the loader's validation rules or the Orchestrator's error.

## Dependencies
- Related to the Orchestrator change that removed the fallback mode.

## Unresolved Questions
- Whether operators rely on the preflight message format (unknown).

## AI Implementation Instruction
Reuse the loader; keep the change to the preflight and its tests. Report if the loader cannot be called without side effects.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/done/20261008-143632_plan.md
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261008-150558
- **Related target files**: `scripts/agent/services/workflow_schema.py`, `tests/agent/test_startup_workflow_preflight.py`
