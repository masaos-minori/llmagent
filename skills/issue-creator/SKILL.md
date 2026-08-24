---
name: issue-creator
description: |
  Create clear, actionable GitHub Issues from requests, review findings, investigation notes,
  implementation plans, or documentation tasks. Use this skill when converting work into
  issue-ready Markdown. Do not implement changes unless explicitly requested.
---

# Issue Creator Skill

## Purpose

Create issues only — see `skills/DESIGN.md` Analysis-only phase constraint. Proceed to
implementation only when the user explicitly asks for it.

Exception to `skills/DESIGN.md` Output language: write issue bodies in English (GitHub issues are consumed by AI coding agents and international tooling), unless the user requests another language. If the target design or documentation must be Japanese, state that requirement inside the issue.

See `workflow.md` Phase 9 for markdown-safety rules.

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
| 3 | Draft Reason and Intent | Write Background, Problem, Reason for Change, and Implementation Intent |
| 4 | Scope and Boundaries | Define Target Files, Required Changes, Constraints, Out of Scope, and Dependencies |
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
- Documentation-related issues must follow `skills/DESIGN.md` Avoid implementation-reference duplication.
- Do not include secrets, credentials, private tokens, or sensitive data.

---

## Issue Structure

Use the exact Markdown structure defined in `templates/issue.md`. It is the shared
contract with `skills/issue-to-plan`'s Step 2 extraction — do not maintain a separate
copy of the field list here.

---

## Priority Guidance

See `workflow.md` Phase 7 for the High / Medium / Low criteria.

---

## Composes with

- `issue-to-plan` — issues produced here may seed a plan directly, or a plan's steps may be converted into issues
- `python-code-review` — review findings are converted into issues via this skill

## Called by

- `python-code-review` — GitHub Issue Conversion step
- `python-documentation` — when documentation cleanup work should be tracked as issues rather than performed immediately

---

## Improvement feedback

After running this skill:
- if a priority definition caused disagreement, refine it in `workflow.md` Phase 7
- if a grouping decision was wrong, refine the grouping rules in `workflow.md` Phase 2
- if the Issue Structure was missing a field the user consistently requested, add it to
  `templates/issue.md` (not here) so `skills/issue-to-plan` picks up the same change

---

## Final Rule

You are not writing vague task notes.

You are creating actionable, reviewable, and implementation-ready GitHub Issues.

When in doubt, prioritize: clarity, actionability, reviewability, minimal scope, testability,
documentation safety.
