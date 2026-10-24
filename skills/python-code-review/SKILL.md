---
name: python-code-review
description: |
  Review existing Python code for correctness, architecture, type safety,
  error handling, resource lifecycle, configuration, tests, CI, and maintainability.
  MUST NOT implement or refactor unless explicitly requested.
---

# Python Code Review Skill

## Purpose

Review first; MUST NOT change code unless the user explicitly asks for implementation (see `skills/DESIGN.md` Analysis-only phase constraint).

Output language: see `skills/DESIGN.md` Output language.

## When to use

Use this skill for:

- reviewing existing Python code, PRs, patches, or diffs
- finding correctness, runtime, type-safety, and maintainability issues
- checking architecture, dependency direction, and responsibility boundaries
- reviewing async/sync boundaries and resource lifecycle
- reviewing error handling, retries, logging, configuration, tests, and CI
- identifying documentation/code mismatches grounded in implementation evidence
- converting review findings into actionable issues, when the user asks (via `issue-creator`)

## When not to use

MUST NOT use this skill for:

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
| 10 | Issue Conversion | Only on request: write `issues/*.md` files from findings via `issue-creator` |

See `workflow.md` for detailed phase content and tooling.

---

## Core Review Rules (Strictly Enforced for AI)

- Classify findings using the Evidence labels and Confidence levels in `skills/DESIGN.md` Shared Vocabulary; MUST NOT introduce a separate fact/interpretation/issue/question system.
- Verify a README or doc claim against the current implementation (Phase 7) before citing it as evidence.
- Report a style-only issue (naming, formatting, import order) as Low or Informational only,
  never as Medium or above. Report at most as many style-only findings as there are Medium+
  findings in the same review; when there are none, report style-only findings only if the
  user asked for them.
- Respect project conventions (see `rules/coding.md`) and explain trade-offs.
- Follow `skills/DESIGN.md` No secrets in output.
- Keep recommendations actionable; for tests, specify the behavior or failure mode to verify.

---

## Evidence Rules

Every finding of severity Medium or above, and every finding a recommendation relies on,
MUST include concrete evidence such as file path; class, function,
method, route, command, or config key; test name or CI workflow; and observed current behavior.

## Severity

See `skills/DESIGN.md` Severity levels.

---

## Output Format

Use this format unless the user requests another format.

### Review Scope

- Reviewed: the diff boundary or file list
- Not reviewed: files left out (out-of-scope paths, or skipped in a large diff) and why
- Working tree vs reviewed head: matched, or the mismatch (`workflow.md` Phase 1)
- Commands run: each tool with its result, or `Needs Confirmation` when it was
  unavailable or could not be run safely

### Summary

- Overall assessment:
- Highest-risk area:
- Recommended next step:

### Findings

Group by severity: Critical, High, Medium, Low, Informational.

For each finding:

- ID: `F-{NNN}` (zero-padded, sequential across the report); Open Questions, Suggested
  Tests, Documentation Notes, and Phase 10 cite findings by this ID
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
- `issue-creator` — Phase 10 delegates issue authoring to it

## Called by

- None: no other skill invokes this skill. It is selected directly from `routing.md`
  ("Code review / PR review").

---

## Improvement feedback

After running this skill:
- if a severity or confidence definition caused disagreement, refine its definition here
- if a review phase produced no useful findings for a task type, note the condition in `workflow.md`
- if a finding pattern recurred across reviews, add it as an explicit check in `workflow.md`

---

## Final Rule

Produce evidence-based Python code review from real code, configuration, tests, CI, and documentation context.

Prioritize: correctness, safety, evidence, operational reliability, type safety, testability,
maintainability, readability.
