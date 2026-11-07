# Clean dead parameters in the retry and exit-status path

## Priority
Low

## Summary
Three small dead or misleading pieces remain in the retry/exit path: a status-mapping function accepts an `error_kind` argument it never uses, a stage runner declares a default timeout that every call site overrides, and the retry policy field named `backoff_sec` implements a constant wait. Remove or make each honest.

## Background
Code review evidence (Verified):
- The adapter's exit-status mapping takes both an exit reason and an error kind but branches only on the exit reason; the error-kind argument is unread.
- The engine's stage runner signature declares a default timeout value; the engine always passes the configured per-stage timeout explicitly, so the default is unreachable magic number.
- The retry policy's `backoff_sec` is applied as a flat sleep between attempts (no growth), which the name does not convey. Loader tests pin the shipped definition's `retry_on` and numeric policy values; none pin a growing-backoff semantics.
- Context: retry semantics were reshaped by `issues/done/20261030-105723_wfretry001_timeout-retry-failure-propagation.md` (resolved); these are leftovers of that reshaping.

## Problem
Unused parameters and unreachable defaults invite wrong assumptions: a future caller may believe exit status varies by error kind, or that tuning `backoff_sec` yields exponential behavior. Each is a small maintenance trap in an area that already received repeated rework.

## Reason for Change
Opportunistic clarity fixes with minimal blast radius, best taken while the retry area is stable. Individually trivial; grouped because they are the same retry-path review result and safer to land as one small commit.

## Implementation Intent
- Exit-status mapping: drop the unused argument (it is an internal helper, not a public API) or use it — dropping is preferred unless the owner wants kind-based statuses.
- Stage runner: remove the unreachable default so the timeout is always the configured value.
- Backoff: either rename/document the field as a constant inter-attempt delay, or (only if the owner wants it) implement growth — the default posture is document-as-is, not new behavior.

## Target Files or Areas
- scripts/agent/workflow_engine_adapter.py (exit-status mapping)
- scripts/agent/workflow/workflow_engine.py (stage runner default, backoff application)
- scripts/agent/workflow/workflow_loader.py and config/workflows/default.json (only if backoff semantics or naming change)

## Required Changes
- Remove the unused parameter and its call-site argument.
- Remove the unreachable default timeout.
- Record the constant-wait semantics of `backoff_sec` in the definition docs or rename with loader compatibility kept.

## Constraints
- No change to retry behavior, attempt counts, or status outcomes for existing configurations.
- `config/workflows/default.json` stays loadable; loader validation rules unchanged.
- Internal helper signatures may change; public loader/config keys may not (renaming a config key is out of scope).

## Acceptance Criteria
- No unread parameters remain in the exit-status path.
- The stage runner has no timeout default value.
- Backoff documentation matches implemented constant-wait behavior.

## Testing Expectations
- Existing retry/exit-status tests remain green (behavior unchanged).
- Ruff/mypy clean on touched files.

## Documentation Impact
The retry-policy description in the workflow-engine documentation must state the wait semantics plainly (constant delay between attempts). No config-key documentation change unless a rename is chosen (then loader compatibility rules apply).

## Out of Scope
- Implementing exponential backoff (owner decision required first).
- Retry-policy schema changes.
- The halt-status semantics themselves.

## Dependencies
- Context: `issues/done/20261030-105723_wfretry001_timeout-retry-failure-propagation.md` (resolved; re-verify current source against it).

## Unresolved Questions
- Does the owner want kind-based exit statuses (would flip the unused-argument fix into a feature)? Default assumption: no, drop the argument.

## AI Implementation Instruction
Land as one small commit; no behavior changes. If the backoff rename is chosen, keep the existing config key readable by the loader and record the decision — do not silently accept two key spellings.

## Traceability
- **Workflow phase**: python-code-review
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261107-203227
- **Related target files**: scripts/agent/workflow_engine_adapter.py, scripts/agent/workflow/workflow_engine.py, scripts/agent/workflow/workflow_loader.py, config/workflows/default.json
