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

## Adversarial Verification Results

Verified against current source on 2026-10-09. All core claims hold; one
target-file discrepancy surfaced.

### Confirmed
- `check_workflow_definition` (`scripts/agent/services/workflow_schema.py:30-33`)
  checks only `.exists()`; invalid JSON, wrong shape, and missing required
  stages pass it.
- Content validation already lives in the loader: `workflow_loader.py`
  `_validate()` raises `WorkflowLoadError` for missing keys, wrong types,
  empty/duplicate stages, missing required stages, and bad `retry_policy`;
  `load()` raises `WorkflowLoadError` on parse errors and non-object JSON.
- Startup call site: `startup_component_init.py:_check_workflow_definition`
  calls `check_workflow_definition()`.
- Last line of defense: `orchestrator.py:128-133` catches
  `WorkflowLoadError`/`FileNotFoundError` and re-raises `RuntimeError` naming
  the file and cause.
- The loader is side-effect free (pure read + in-memory construct), so it can
  be called from the preflight.

### Discrepancy (needs resolution)
- This issue lists `tests/agent/test_startup_workflow_preflight.py` as the
  test target, but that file mocks `check_workflow_definition` and only tests
  the wrapper `_check_workflow_definition`. Real-function content tests live in
  `tests/agent/test_repl_health.py::TestCheckWorkflowDefinition`. Content
  validation tests (malformed JSON, missing required stage) should be added to
  `test_repl_health.py`, where the real function is exercised with real tmp
  files.

### Open decision (owner)
- The issue frames this as a decision ("decide whether the preflight should
  also validate the content"). Both paths are fatal with comparable messages
  (preflight now vs. Orchestrator constructor). Proceeding in the issue's YES
  direction, but final sign-off is the owner's.

### Recorded decisions (2026-10-09)
- Test target: `tests/agent/test_repl_health.py` (real function), not
  `test_startup_workflow_preflight.py` (wrapper-only).
- Direction: proceed with content validation (owner to confirm final sign-off).
