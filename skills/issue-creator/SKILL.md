---
name: issue-creator
description: |
  Create clear, actionable GitHub Issues from requests, review findings, investigation notes,
  implementation plans, or documentation tasks. Use this skill when converting work into
  issue-ready Markdown. Do not implement changes unless explicitly requested.
---

# Issue Creator Skill

## Purpose

Create issues only. Do not implement, refactor, or edit project files unless the user explicitly asks for implementation.

Write issue bodies in English unless the user requests another language. If the target design or documentation must be Japanese, state that requirement inside the issue.

Keep Markdown safe to copy and paste. Avoid nested triple-backtick code blocks inside issue templates unless absolutely necessary.

## When to use

Use this skill for:

- converting a task list into GitHub Issues
- converting review findings into actionable issues
- converting implementation plans into issues
- converting documentation cleanup work into issues
- splitting large work into smaller tasks
- grouping tightly related tasks that should be done together
- writing acceptance criteria, out-of-scope notes, and testing expectations
- preparing AI implementation instructions for coding agents

## When not to use

Do not use this skill for:

- direct code implementation
- speculative issues without evidence or context
- creating issues from unclear requirements without marking assumptions
- bulk issue generation that mixes unrelated concerns
- writing long implementation manuals inside issues

---

## Phase overview

| Phase | Name | Goal |
|---|---|---|
| 1 | Classify and Frame | Identify the work's source, scope, and whether assumptions are needed |
| 2 | Task Grouping | Decide whether to split into multiple issues or group into one |
| 3 | Draft Reason and Intent | Write Reason for Change and Implementation Intent |
| 4 | Scope and Boundaries | Define Target Files, Required Changes, and Out of Scope |
| 5 | Acceptance Criteria and Testing | Define verifiable criteria and testing expectations |
| 6 | Documentation Impact | Assess doc impact and apply documentation cleanup rules |
| 7 | Priority Assignment | Assign High / Medium / Low |
| 8 | AI Implementation Instruction | Write concise constraints for an AI coding agent |
| 9 | Evidence, Markdown Safety, Final Checklist | Verify evidence, copy-paste safety, and completeness |

See `workflow.md` for detailed phase content, task grouping rules, documentation cleanup
rules, markdown safety rules, and the final checklist.

---

## Core Principles

- One issue should represent one actionable task.
- Group tasks only when they must be completed together or are safer to review together.
- Prefer small, reviewable issues over broad, vague issues.
- Each issue must explain both the reason for change and the implementation intent.
- Acceptance criteria must be concrete and verifiable.
- Out-of-scope items must be explicit.
- Testing expectations must be included when code behavior may change.
- Documentation-related issues must avoid adding implementation-reference duplication.
- Do not include secrets, credentials, private tokens, or sensitive data.

---

## Issue Structure

Use this structure unless the user requests another format.

```markdown
# <Issue Title>

## Priority
High / Medium / Low

## Summary
Briefly describe the task and the intended outcome.

## Reason for Change
Explain why this change is needed.

## Implementation Intent
Explain how the work should be approached at a high level.

## Target Files or Areas
List only likely relevant files or areas. Use `Unknown` if not confirmed.

## Required Changes
List concrete changes as small, actionable bullets.

## Acceptance Criteria
List verifiable completion criteria.

## Testing Expectations
Unit / integration / regression tests, type checks, lint checks, documentation
consistency checks, or manual verification. Use `Not required` only when the
task is documentation-only or clearly does not affect behavior.

## Documentation Impact
State whether documentation must be updated, and what kind of information
should be documented (intent, boundaries, constraints, failure behavior,
operational notes, Known Issues, Needs Confirmation items).

## Out of Scope
List what must not be changed in this issue.

## AI Implementation Instruction
Concise constraints for an AI coding agent implementing this issue.
```

---

## Priority Guidance

- **High** — correctness, data integrity, security-sensitive behavior, startup/deployment failure, workflow execution, public API behavior, production reliability, critical documentation/code mismatch.
- **Medium** — maintainability, testability, type safety, unclear ownership, ambiguous configuration behavior, non-critical documentation/code mismatch.
- **Low** — wording cleanup, small metadata cleanup, minor formatting, non-blocking consistency improvements.

See `workflow.md` Phase 7 for the full guidance.

---

## Composes with

- `python-issue-to-plan` — issues produced here may seed a plan, or a plan's steps may be converted into issues
- `python-code-review` — review findings are converted into issues via this skill

## Called by

- `python-code-review` — GitHub Issue Conversion step
- `python-documentation` — when documentation cleanup work should be tracked as issues rather than performed immediately

---

## Improvement feedback

After running this skill:
- if a priority definition caused disagreement, refine it in `workflow.md` Phase 7
- if a grouping decision was wrong, refine the grouping rules in `workflow.md` Phase 2
- if the Issue Structure was missing a field the user consistently requested, add it here

---

## Final Rule

You are not writing vague task notes.

You are creating actionable, reviewable, and implementation-ready GitHub Issues.

When in doubt, prioritize: clarity, actionability, reviewability, minimal scope, testability,
documentation safety.
