# Report once before a long wait in progress reporting

## Priority
Low

## Summary
Add a rule to the shared Progress Reporting text that an operation expected to take long (a full test run, a long build, a background command) is announced in one line before the wait starts, stating what is awaited and the expected duration, so a multi-minute silence is not mistaken for a stall.

## Background
- `Explicit in code`: `rules/ai-execution.md` "Progress Reporting (Base)" says to report once per step, in one line, after the step completes, and to omit the report when the step finished as expected. It has no case for a step that runs for minutes inside a single step, and the sections "Tool Usage" and "Command Results" do not mention waits either.
- `Operationally observed` (2026-10-30): the session ran the full test suite about eight times (427 to 493 seconds each) and several other long commands, often in the background. During those waits the interface repeatedly reported that the user had not heard from the assistant for a while, and the assistant had to add an ad hoc status line each time.
- `Explicit in code`: `skills/code-implementation/workflow.md` Step 4 requires the full-suite run in every cycle, so the long wait is part of the normal workflow rather than an exception.

## Problem
The reporting rule is built around step boundaries. A long wait inside a step produces no output, which reads as a stall to the user and invites unplanned status messages that repeat information or interrupt the work.

## Reason for Change
The wait is predictable (the suite's duration is known to within a minute), the fix is one sentence of rule, and it applies to every workflow that cites the shared Progress Reporting text.

## Implementation Intent
Keep the existing cadence and add one narrow case. Before a command expected to take longer than a stated threshold, or any command started in the background, emit a single line saying what is being waited on and the expected duration. Do not add periodic polling messages; when a background command's completion is delivered by the platform, report its result in one line. The threshold and wording live in the shared rule, so each workflow inherits them through its existing reference to "Progress Reporting (Base)".

## Target Files or Areas
- `rules/ai-execution.md` (Progress Reporting (Base))
- `skills/code-implementation/workflow.md` (Step 4, a one-line reference, only if the shared rule alone does not reach it)

## Required Changes
- Add the before-a-long-wait line to Progress Reporting (Base), with a stated threshold and the content of the line.
- State that polling messages are not added while waiting.
- Reference it from `code-implementation` Step 4 only if needed.

## Constraints
- The rule must not increase the number of messages for ordinary short steps.
- It must not conflict with `rules/ai-execution.md` "Output" (state the conclusion once, no repeated summaries).
- English text in rules.

## Acceptance Criteria
- `rules/ai-execution.md` contains the rule with a stated threshold, and no workflow file restates it.
- `check_skills_references.py` and `check_skills_heading_cycles.py` pass.
- A review of the rule against `rules/ai-execution.md` "Output" and "Progress Reporting (Base)" finds no contradiction.

## Testing Expectations
- Skill and rules checkers named in `routing.md` for the changed files.
- A read-through of one `code-implementation` cycle with a full-suite run, confirming that the rule yields one announcement line and one result line for the wait.

## Documentation Impact
Yes, limited to `rules/ai-execution.md`: intent and the single new case. No other documentation.

## Out of Scope
- Changing the platform's own "has not heard" notice or how background completion is delivered.
- Changing which steps run the full suite (`issues/20261030-191057_flowimp002_plan-release-units.md` covers batching).

## Dependencies
N/A: none. `rules/ai-execution.md` is mentioned in the open plans `20261030-113553_wftaskapi001_consolidate-task-persistence.md`, `20261030-114041_wfrecovery001_workflow-recovery-state-machine.md`, and `20261030-114516_wflease001_stale-attempt-lease.md` only as a referenced rule, not as a change target (checked with `rg` over `issues/*.md` and `plans/*.md`, 2026-10-30).

## Unresolved Questions
- `不明`: the right threshold; a value of about one minute is a proposal, not a measurement.
- `不明`: whether the announcement should be a separate message or can ride on the preceding tool call description.
- Assumption: the interface's "has not heard" notice is triggered by elapsed silence, so a single line before the wait is enough to prevent most of them.

## AI Implementation Instruction
Edit `rules/ai-execution.md` (and at most one line in the named workflow) only. Do not add polling or periodic messages, and do not restate the rule in other files. Stop and report if the wording conflicts with the existing "Output" section.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261030-191820
- **Related target files**: `rules/ai-execution.md`, `skills/code-implementation/workflow.md`
