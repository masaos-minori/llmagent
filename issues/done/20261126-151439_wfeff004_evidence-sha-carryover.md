# Carry verification evidence between phases by commit SHA

## Priority
Medium

## Summary
The same target files are verified against current source in `issue-to-plan`, again in `plan-to-implementation-procedure`, and again in `code-implementation`. Record the revision at which each claim was verified and let a later phase skip the re-read when the relevant files are unchanged since that revision.

## Background
Evidence (`Explicit in code`, by reading the workflows): `skills/issue-to-plan/workflow.md` Step 2 and Step 3 verify claims and have a same-cycle dedup rule; `skills/plan-to-implementation-procedure/workflow.md` Step 3a and `skills/code-implementation/workflow.md` Step 3a each re-verify the Plan's or procedure's claims, and `rules/ai-execution.md` "Adversarial Verification (Base)" requires it. A Plan's `Repository Evidence` entries end with `(checked in Step N)` and name no revision, so a later phase cannot tell whether anything changed.

The dedup rule of `issue-to-plan` is limited to one cycle (`workflow.md` Step 2, "Same-cycle dedup"), so each later phase repeats the reads even when the repository has not moved.

## Problem
Repeated reading of unchanged files costs time and tokens in every phase. The cost grows with the number of target rows (a recent Plan had 38).

## Reason for Change
Efficiency without lowering the verification standard; not urgent.

## Implementation Intent
Make a claim's evidence content-addressed: store the commit SHA (and the list of files the claim depends on) with the evidence, and let a later phase confirm with `git` that those files are unchanged since then. A changed or uncommitted file always gets the full verification that exists today.

## Target Files or Areas
- `templates/plan.md` (an evidence-revision field or convention)
- `rules/ai-execution.md` (Adversarial Verification (Base): the unchanged-since rule)
- `skills/issue-to-plan/workflow.md`, `skills/plan-to-implementation-procedure/workflow.md`, `skills/code-implementation/workflow.md`
- `tools/` (a read-only freshness checker, name to be chosen)

## Required Changes
- Define where the verification revision is recorded (for example one line in the Plan's Traceability plus the file set per claim) and how issue-to-plan writes it.
- Add a read-only tool that, given a Plan or procedure, lists the files whose last commit is newer than the recorded revision or that have working-tree changes.
- Add the skip rule to the two later phases: an unchanged file is cited as verified at the recorded revision; any changed, uncommitted, or unrecorded file is verified in full as today.
- Keep the stale detector and the target-file revalidation steps as they are.

## Constraints
- The claim's dependencies count, not only the target file: callers, tests, and imported symbols that the claim relies on must also be in the recorded file set.
- A skip must never apply across an uncommitted change in a recorded file.
- The rule must not weaken `rules/ai-execution.md` Adversarial Verification (Base) for new claims.

## Acceptance Criteria
- [ ] A Plan records the revision and file set of its verified claims.
- [ ] The tool reports changed, uncommitted, and unrecorded files for a Plan.
- [ ] A later phase re-reads only the reported files and cites the revision for the rest.
- [ ] A claim whose dependency file changed is verified in full.

## Testing Expectations
Unit tests for the tool on a temporary git repository (unchanged, committed change, working-tree change, unrecorded file); ruff, mypy, bandit; `tools/check_tool_descriptions_sync.py`; a documented dry run on one existing Plan.

## Documentation Impact
Yes. `templates/plan.md`, the three workflows, `rules/ai-execution.md`, and `tools/TOOL_DESCRIPTIONS.md`.

## Out of Scope
- Changing what is verified or the stale detector.
- Caching verification results outside the repository.

## Dependencies
- N/A: none

## Unresolved Questions
- `不明`: how to record the dependency set per claim without making Plans much longer.
- `不明`: whether an amend of the Frozen Plan (`tools/amend_plan.py`) must refresh the recorded revision.

## AI Implementation Instruction
Propose the recording format first and stop for confirmation. Do not weaken any existing verification step.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261126-151439
- **Related target files**: `templates/plan.md`, `rules/ai-execution.md`, `skills/issue-to-plan/workflow.md`, `skills/plan-to-implementation-procedure/workflow.md`, `skills/code-implementation/workflow.md`
