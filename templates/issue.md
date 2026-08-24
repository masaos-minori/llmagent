# Issue Input Template (Canonical)

Use this exact Markdown structure for every `issues/*.md` file. It is the canonical
contract between the producer (`skills/issue-creator`) and the consumer
(`skills/issue-to-plan`, Step 2's extraction list) — both reference this file instead
of maintaining their own copy of the field list, so the two skills cannot drift apart.

Use this structure unless the user requests another format.

```markdown
# <Issue Title>

## Priority
High / Medium / Low

## Summary
Briefly describe the task and the intended outcome.

## Background
Why this requirement exists (prior context, history, related decisions). Use
`N/A: {short reason}` if there is no background beyond the Summary.

## Problem
The concrete problem being solved, stated separately from the general Summary. Use
`N/A: {short reason}` if this issue is not problem-driven (e.g. a proposal).

## Reason for Change
Explain why this change is needed now.

## Implementation Intent
Explain how the work should be approached at a high level.

## Target Files or Areas
List only likely relevant files or areas. Use `Unknown` if not confirmed.

## Required Changes
List concrete changes as small, actionable bullets.

## Constraints
Technical or domain constraints and limitations that bound the solution space
(compatibility, performance, security, operational). Use `N/A: {short reason}` if none.

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

## Dependencies
Other issues, plans, or external work this issue depends on, or that depend on it. Use
`N/A: none` if there are none.

## Unresolved Questions
Open questions or assumptions that still need confirmation before or during
implementation. Use `N/A: none` if there are none.

## AI Implementation Instruction
Concise constraints for an AI coding agent implementing this issue.
```

## Field notes

- `Background` and `Problem` are separate from `Summary`: `Summary` is the quick
  overview; `Background`/`Problem` exist for issues where the "why" and the "what's
  broken" need more than a sentence. When they add nothing beyond `Summary`, mark them
  `N/A: covered by Summary` rather than duplicating it.
- `Constraints`, `Dependencies`, and `Unresolved Questions` may be `N/A` — do not invent
  content to fill them.
- `skills/issue-to-plan` Step 2 classifies each extracted field's evidence basis
  (`Explicit in issue` / `Confirmed by repository evidence` / `Derived from confirmed
  evidence` / `Needs confirmation`); an `N/A` field is `Explicit in issue` by
  definition and carries no Unknown.
