---
name: python-code-review
description: |
  Review existing Python code for correctness, architecture, type safety,
  error handling, resource lifecycle, configuration, tests, CI, and maintainability.
  Do not implement or refactor unless explicitly requested.
---

# Python Code Review Skill

## Rule

Review first. Do not change code unless the user explicitly asks for implementation.

Write review reports in Japanese unless requested otherwise.
Keep file names, symbols, commands, config keys, and evidence labels in their original form.

## Use When

Use this skill for:

- reviewing existing Python code, PRs, patches, or diffs
- finding correctness, runtime, type-safety, and maintainability issues
- checking architecture, dependency direction, and responsibility boundaries
- reviewing async/sync boundaries and resource lifecycle
- reviewing error handling, retries, logging, configuration, tests, and CI
- identifying documentation/code mismatches grounded in implementation evidence
- converting review findings into actionable GitHub issues

Do not use this skill for:

- direct implementation-only requests
- greenfield design without code to review
- tiny syntax fixes
- non-Python targets
- speculative findings without evidence

## Review Focus

Check the following when relevant:

- correctness and edge cases
- state transitions, idempotency, caching, and data consistency
- import direction and circular import risk
- responsibility boundaries and cross-layer access
- public contracts, typing, `Any`, optional values, and protocol usage
- async/sync boundaries and blocking calls
- exceptions, retries, timeouts, fail-fast/fail-open behavior
- file, socket, DB, HTTP client, subprocess, and async task cleanup
- configuration ownership, startup behavior, reload boundaries, and safe defaults
- logging, diagnostics, and secret exposure risk
- tests for critical behavior, edge cases, and failure paths
- CI quality gates and type-checking coverage

## Evidence Rules

Every significant finding must include concrete evidence such as:

- file path
- class, function, method, route, command, or config key
- test name or CI workflow
- observed current behavior

Use existing repository evidence labels when available:

- `Explicit in code`
- `Strongly implied by code`
- `Documentation only`
- `Needs confirmation`
- `Deprecated`
- `Verified by test`
- `Operationally observed`

If behavior is unclear, mark it as `Needs confirmation` and state what must be checked.

Use confidence levels:

- High: directly verified
- Medium: strongly implied
- Low: plausible but requires confirmation

## Severity

Use these severities:

- Critical: data loss, security exposure, destructive unintended action, production startup failure, silent corruption
- High: normal-use runtime failure, incorrect result, broken workflow, major operational risk, missing validation at trust boundaries
- Medium: maintainability risk, unclear ownership, type-safety degradation, incomplete failure handling, fragile tests, ambiguous config behavior
- Low: naming, localized duplication, minor typing or documentation cleanup
- Informational: observation with no immediate action

## Documentation Guidance

When reviewing or recommending documentation updates:

- focus on intent, boundaries, constraints, decisions, operational notes, known issues, and Needs Confirmation items
- do not recommend copying exhaustive method lists, DTO field tables, full config key tables, file catalogs, or long command examples into design documents
- keep documentation recommendations concise and implementation-grounded

## Rules

- Do not implement unless explicitly requested.
- Separate fact, interpretation, suspected issue, and open question.
- Do not treat dead code as active behavior.
- Do not trust README or old docs without implementation verification.
- Do not over-report style-only issues.
- Respect project conventions and explain trade-offs.
- Protect secrets and sensitive data.
- Keep recommendations actionable.
- For tests, specify the behavior or failure mode to verify.

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

## GitHub Issue Conversion

When converting findings into GitHub issues:

- use one issue per actionable task
- group related findings only when they must be fixed together
- include reason for change, implementation intent, acceptance criteria, out of scope, and testing expectations
- avoid Markdown that breaks when copied
- do not include secrets or unnecessary code blocks

## Final Rule

Produce evidence-based Python code review from real code, configuration, tests, CI, and documentation context.

Prioritize:

1. correctness
2. safety
3. evidence
4. operational reliability
5. type safety
6. testability
7. maintainability
8. readability
