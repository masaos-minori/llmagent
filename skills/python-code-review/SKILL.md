---
name: python-code-review
description: |
  Review existing Python code for correctness, architecture, type safety,
  error handling, resource lifecycle, configuration, tests, CI, and maintainability.
  Do not implement or refactor unless explicitly requested.
---

# Python Code Review Skill

## Purpose

Review first. Do not change code unless the user explicitly asks for implementation.

Write review reports in Japanese unless requested otherwise.
Keep file names, symbols, commands, config keys, and evidence labels in their original form.

## When to use

Use this skill for:

- reviewing existing Python code, PRs, patches, or diffs
- finding correctness, runtime, type-safety, and maintainability issues
- checking architecture, dependency direction, and responsibility boundaries
- reviewing async/sync boundaries and resource lifecycle
- reviewing error handling, retries, logging, configuration, tests, and CI
- identifying documentation/code mismatches grounded in implementation evidence
- converting review findings into actionable GitHub issues

## When not to use

Do not use this skill for:

- direct implementation-only requests
- greenfield design without code to review
- tiny syntax fixes
- non-Python targets
- speculative findings without evidence

---

## Phase overview

| Phase | Name | Goal |
|---|---|---|
| 1 | Scope and Intake | Fix the reviewed diff/PR/file boundary and its stated intent |
| 2 | Correctness and Data Consistency | Edge cases, state transitions, typing, import direction |
| 3 | Architecture and Boundaries | Dependency direction, layering, unjustified abstractions |
| 4 | Async/Sync and Resource Lifecycle | Blocking calls in async paths, resource cleanup |
| 5 | Error Handling, Configuration, and Logging | Exceptions, retries, fail-fast/fail-open, secret exposure |
| 6 | Tests and CI | Coverage of critical behavior, failure paths, CI gates |
| 7 | Documentation Mismatches | Evidence-grounded doc/code contradictions |
| 8 | Evidence, Confidence, and Severity Assignment | Attach evidence, confidence, and severity to each finding |
| 9 | Report Writing | Produce the Output Format below |
| 10 | GitHub Issue Conversion | Convert findings into actionable issues |

See `workflow.md` for detailed phase content and tooling.

---

## Core Review Rules (Strictly Enforced for AI)

- Do not implement unless explicitly requested.
- Separate fact, interpretation, suspected issue, and open question.
- Do not treat dead code as active behavior.
- Do not trust README or old docs without implementation verification.
- Do not over-report style-only issues.
- Respect project conventions and explain trade-offs.
- Protect secrets and sensitive data.
- Keep recommendations actionable; for tests, specify the behavior or failure mode to verify.

---

## Evidence Rules

Every significant finding must include concrete evidence such as file path; class, function,
method, route, command, or config key; test name or CI workflow; and observed current behavior.

Use existing repository evidence labels when available: `Explicit in code`, `Strongly implied
by code`, `Documentation only`, `Needs confirmation`, `Deprecated`, `Verified by test`,
`Operationally observed`. If behavior is unclear, mark it `Needs confirmation` and state what
must be checked.

Use confidence levels: **High** (directly verified), **Medium** (strongly implied), **Low**
(plausible but requires confirmation).

## Severity

Use these severities: **Critical** (data loss, security exposure, destructive unintended
action, production startup failure, silent corruption), **High** (normal-use runtime failure,
incorrect result, broken workflow, major operational risk, missing validation at trust
boundaries), **Medium** (maintainability risk, unclear ownership, type-safety degradation,
incomplete failure handling, fragile tests, ambiguous config behavior), **Low** (naming,
localized duplication, minor typing or documentation cleanup), **Informational** (observation
with no immediate action).

---

## Output Format

Use this format unless the user requests another format.

### Summary

- Overall assessment:
- Highest-risk area:
- Recommended next step:

### Findings

Group by severity: Critical, High, Medium, Low, Informational.

For each finding:

- Title:
- Severity:
- Confidence:
- Evidence:
- Current behavior:
- Impact:
- Recommended action:

### Open Questions

- Question:
- Why it matters:
- Required confirmation:

### Suggested Tests

- Test target:
- Behavior to verify:
- Failure mode:

### Documentation Notes

- Target document:
- Required update:
- Reason:

### Final Recommendation

State whether to proceed, fix first, or investigate further.

---

## Composes with

- `python-implementation` — run if a finding requires a feature-level code change to fix
- `python-refactoring` — run if a finding requires structural changes without behavior change
- `python-documentation` — run if Documentation Notes require an update to existing docs

## Called by

- `python-issue-to-plan` — when a plan needs a review of existing code before scoping changes

---

## Improvement feedback

After running this skill:
- if a severity or confidence definition caused disagreement, refine its definition here
- if a review phase produced no useful findings for a task type, note the condition in `workflow.md`
- if a finding pattern recurred across reviews, add it as an explicit check in `workflow.md`

---

## Final Rule

Produce evidence-based Python code review from real code, configuration, tests, CI, and
documentation context.

Prioritize: correctness, safety, evidence, operational reliability, type safety, testability,
maintainability, readability.
