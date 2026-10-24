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

Output language: see `skills/DESIGN.md` Output language. The review report itself is a
generated document and is written in English; when it is shown in the chat, the
surrounding conversation stays in the chat language (`AGENTS.md` Role). Files written in
Phase 10 (`issues/*.md`) are English. Identifiers, commands, and evidence labels are never
translated.

## Required loads (Step 0)

Before Phase 1, load `skills/DESIGN.md` (Evidence labels, Confidence levels, Severity
levels, Shared Vocabulary, Pythonic safety constraints, Out-of-scope paths, No secrets in
output, Output language) and `rules/coding.md` (conventions and Prohibited patterns). The
other skills `routing.md` points to for a task are not loaded here; load
`skills/issue-creator/SKILL.md` + `workflow.md` only when Phase 10 runs.

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
| 2 | Correctness and Data Consistency | Edge cases, state transitions, typing, `rules/coding.md` prohibited patterns, performance and concurrency hazards |
| 3 | Architecture and Boundaries | Dependency direction, import cycles, layering, unjustified abstractions, project checkers |
| 4 | Async/Sync and Resource Lifecycle | Blocking calls in async paths, resource cleanup |
| 5 | Error Handling, Configuration, and Logging | Exceptions, retries, fail-fast/fail-open, secret exposure, trust-boundary security, SQLite/sqlite-vec usage |
| 6 | Tests and CI | Coverage of critical behavior, failure paths, CI gates (`.github/workflows/`, pre-commit, `tox.ini`) |
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
  never as Medium or above. Style-only findings must not crowd out substantive ones: the
  cap is that a review reports no more style-only findings than Medium+ findings (a
  proportionality guard against noise, a judgment threshold of this skill rather than a
  project standard); when there are no Medium+ findings, report style-only findings only
  if the user asked for them.
- Respect project conventions (see `rules/coding.md`) and explain trade-offs. A change
  that matches a `rules/coding.md` Prohibited pattern is a finding.
- Evidence labels use the exact spelling in `skills/DESIGN.md` Evidence labels (for example
  `Needs confirmation`); a check that could not be run or confirmed is labeled that way.
- Severity is assessed as if the finding is true; Confidence reports how sure the review
  is. A Critical or High finding with Low confidence MUST also appear under Open
  Questions with the confirmation needed.
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
- Commands run: each tool and project checker with its result, or `Needs confirmation`
  when it was unavailable or could not be run safely

### Summary

- Overall assessment:
- Highest-risk area:
- Recommended next step:

### Findings

Group by severity: Critical, High, Medium, Low, Informational.

For each finding:

- ID: `F-{NNN}` (zero-padded, sequential across the report, assigned after sorting by
  severity so `F-001` is the most severe); Open Questions, Suggested Tests,
  Documentation Notes, and Phase 10 cite findings by this ID
- Title:
- Severity:
- Confidence:
- Evidence label:
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

When no finding survives Phase 8, still output Review Scope and Summary, write
`Findings: none` under Findings, and state what was covered (phases run, commands and
checkers with results) and what remains `Needs confirmation`, so a clean result is
distinguishable from a shallow review. The Final Recommendation is then `proceed` only if
no check is left unconfirmed in a high-risk area; otherwise `investigate further`.

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
