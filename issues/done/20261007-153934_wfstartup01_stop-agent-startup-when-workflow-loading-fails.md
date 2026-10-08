# Stop agent startup when workflow loading fails

## Priority
High

## Summary
Treat a workflow load failure as a fatal startup error instead of continuing in a fallback mode with no approval or stage control, and align the Orchestrator's documentation with its real structure.

## Background
Source: local investigation notes (memo1.md, ISSUE-05), consolidating AGENT-003 (raised from Medium to High) and an earlier finding. ADR-001 INV-01/05 make the Workflow Engine mandatory; ADR-004 requires fail-closed behavior.

## Problem
- `Orchestrator.__init__` catches `WorkflowLoadError` and `FileNotFoundError` and continues with `_FALLBACK_WORKFLOW_DEF` (`require_approval=False`, no stages) (Explicit in code — `scripts/agent/orchestrator.py`, `_FALLBACK_WORKFLOW_DEF`, `_fallback_mode`).
- `handle_turn()` notifies via `on_error` and then still runs `_execute_turn()`.
- Documentation (agent_01 / 02 / 03_01 / 12) states that a RuntimeError stops startup, the opposite of the implementation.
- The module docstring mentions `turnd_coordinator.py` (TurnCoordinator), which is not wired in (likely a typo for `turn`); many backward-compatibility delegation wrappers remain, contrary to the repository's no-compatibility-layer policy.

## Reason for Change
- Without a workflow, approval, stage control, and task recording are all absent, yet turns still execute, so operations may run without approval (contradicts ADR-001 INV-01/05 and ADR-004 fail-closed).
- A misconfiguration that only logs a warning goes unnoticed by operators.
- Docstrings naming non-existent components mislead maintainers.

## Implementation Intent
- A workflow load failure is a fatal startup error; the Agent does not run without the approval foundation.
- Make the Orchestrator description match reality and remove compatibility wrappers after fixing their test callers.

## Target Files or Areas
- `scripts/agent/orchestrator.py`
- Tests that call the delegation wrappers
- agent_01 / 02 / 03_01 / 12 documentation, ADR-001, ADR-004 Known Deviations

## Required Changes
- Remove the try/except in `__init__`; raise `WorkflowLoadError` as `RuntimeError` with the file path and cause.
- Remove `_FALLBACK_WORKFLOW_DEF`, `_fallback_mode`, and the fallback branch in `handle_turn()`.
- Remove TurnCoordinator from the module and class docstrings if unused; consolidate the duplicated component list.
- Rewrite tests that use the delegation wrappers to call components directly, then delete the wrappers.

## Constraints
- No backward-compatibility layers.
- Do not weaken any other startup validation.

## Acceptance Criteria
- Starting with `default.json` missing or malformed makes the Agent exit with a non-zero code (test).
- The name `_fallback_mode` no longer appears in code.

## Testing Expectations
- Startup failure tests; update existing orchestrator tests; ruff, mypy, targeted pytest.

## Documentation Impact
Update the agent documents named above only if wording must change after the fix; remove Known Issue AGENT-003 from the ledger on completion and update ADR-001/ADR-004 Known Deviations.

## Out of Scope
- Approval policy enforcement in configuration validation (separate issue).
- Changes to workflow engine internals.

## Dependencies
- Related to the approval-policy validation issue; handling both completes the approval policy.

## Unresolved Questions
- Whether fallback mode really lets tools run without approval (confirm via `workflow_engine_adapter.py` and `workflow/engine.py`); this is the top-priority confirmation and decides whether High is retained.
- Whether the startup preflight already checks the workflow file's existence (if so, fallback is reached only for malformed content).

## AI Implementation Instruction
Remove the fallback path rather than gating it. Do not touch unrelated Orchestrator logic. Report first if the open questions show that approval is not bypassed in fallback mode.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261007-153934
- **Related target files**: `scripts/agent/orchestrator.py`
