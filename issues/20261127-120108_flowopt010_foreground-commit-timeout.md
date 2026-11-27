# Run commits in the foreground with the maximum hook timeout

## Priority
Low

## Summary
State in the commit workflow that `git commit` runs its pre-commit hooks in the foreground with the longest allowed timeout, so no wait-and-poll turns are needed.

## Background
Evidence (`Explicit in code`, by observation): the pre-commit hooks of a commit took about two to three minutes on 2026-11-27 (whole-repository mypy and other checks). With the default 120 s command timeout the commit moved to the background and needed extra check-in turns; with a 600000 ms foreground timeout the commit would have returned in one call. The exact hook duration was not instrumented (`不明`).

## Problem
The workflow does not say how to run a long commit, so each commit adds waiting turns.

## Reason for Change
Turns and tokens per commit; no correctness risk.

## Implementation Intent
One sentence in Phase 6 of the commit skill.

## Target Files or Areas
- `skills/git-commit-and-sync/workflow.md`

## Required Changes
- In Phase 6 add: run `git commit` in the foreground with the maximum command timeout (600000 ms); use a background run only when it exceeds it.
- Keep within the file's size ceiling.

## Constraints
- `skills/git-commit-and-sync/workflow.md` ceiling 22947 B (22706 B on 2026-11-27).
- The sentence must not weaken the hook-failure handling.

## Acceptance Criteria
- [ ] Phase 6 states the rule.
- [ ] The skill checks pass and the file is within its ceiling.

## Testing Expectations
`tools/check_skill_size.py`, `tools/check_skills_references.py`, `tools/check_skills_heading_cycles.py`.

## Documentation Impact
Yes. One sentence in the workflow.

## Out of Scope
- Changing hook contents or their duration.

## Dependencies
N/A: none

## Unresolved Questions
- `不明`: whether this belongs in the commit skill or in a shared tool-usage rule (`rules/ai-execution.md` Tool Usage), because the timeout limit is a property of the agent environment.

## AI Implementation Instruction
Edit one sentence; if the limit is environment-specific, say so in the sentence.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261127-120108
- **Related target files**: `skills/git-commit-and-sync/workflow.md`
