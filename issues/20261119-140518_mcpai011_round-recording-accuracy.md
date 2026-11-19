# Correct Agent round execution recording

## Priority
Medium

## Summary
Record the actual scheduling mode and side-effect presence of each execution round instead of a constant parallel mode and side effects inferred from serialization events.

## Background
Source: consolidated review backlog (`memo-issue.md`, Issue 11). `scripts/agent/tool_run_recorder.py` exists and its docstring describes round-level serialization recording (`Explicit in code`); the constant-mode and inference claims are from the review and `Needs confirmation`.

## Problem
A sequential plan can be recorded as parallel and an unconflicted single write can be omitted from side-effect reporting because no serialization event occurred, making telemetry inaccurate.

## Reason for Change
Operational telemetry and incident review accuracy; observability only, no data-integrity risk.

## Implementation Intent
Derive the recorded mode from the actual execution plan and side-effect presence from `PreparedToolCall.spec.is_write`; keep serialization events as conflict diagnostics only.

## Target Files or Areas
- `scripts/agent/tool_run_recorder.py`
- Agent scheduler and recorder tests under `tests/agent/`

## Required Changes
- Derive mode from the plan; derive side-effect presence from approved tool metadata; keep scheduling and display modes consistent; preserve serialization events as diagnostics.

## Constraints
- Counters read by `commands/cmd_mcp.py` keep their meaning.

## Acceptance Criteria
- [ ] Sequential plans are not recorded as parallel.
- [ ] A single unconflicted write is recorded as side-effecting.
- [ ] A forced-serial read-only plan is not marked as a write.
- [ ] Recorded mode matches the scheduler's plan.

## Testing Expectations
- Concurrent read-only plan, sequential write plan, single write without conflicts, and forced-serial read-only plan; run ruff, mypy, and the full test suite.

## Documentation Impact
Not required unless a document describes the recorded fields (`Needs confirmation`).

## Out of Scope
- Scheduler behavior and resource scopes (`issues/20261119-140520_mcpai013_github-resource-scope-refine.md`).

## Dependencies
- Independent. Re-run its tests after `issues/20261119-140511_mcpai004_logical-idempotency-key-replay.md` if `PreparedToolCall` changes affect recorder inputs. Recommended input for validating `issues/20261119-140520_mcpai013_github-resource-scope-refine.md`.
- Sibling check: archived `issues/done/20261118-141420_toolrun001_round-completion-cancellation-window.md` touched round recording; re-verify against it.

## Unresolved Questions
N/A: none

## AI Implementation Instruction
Keep the change inside the recorder and its tests; write the four plan-shape tests first.

## Traceability
- **Workflow phase**: `issue-creator`
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261119-140518
- **Related target files**: `scripts/agent/tool_run_recorder.py`
