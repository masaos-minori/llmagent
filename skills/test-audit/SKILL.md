---
name: test-audit
description: |
  Use this skill PROACTIVELY when auditing this repository's entire test suite:
  discovering how tests are run, safely executing them, confirming failures are
  reproducible with evidence, comparing results against source code and
  documentation, detecting coverage and validation gaps, and producing a concrete,
  traceable implementation work plan for test improvement.
  Covers: test-entry-point discovery, a safety-gated execution pass over the whole
  suite, evidence-based flaky/root-cause classification, gap analysis, Finding →
  Task → Test Case traceability, and a structured final report usable as a QA memo,
  test debt report, stabilization work plan, or GitHub Issue source.
  Do NOT use this skill to fix one specific failing test (use `python-test-and-fix`)
  or to debug one specific incident (use `python-debug-root-cause`) — this skill's
  scope is a whole-suite audit, not a single-target fix.
---

# Test Audit Skill

## Purpose

Audit the test suite as a whole and turn what is found into an execution-ready plan.
This workflow intentionally prioritizes safety, evidence, and correctness over speed —
do not skip a step because it seems slow, and do not stop at high-level commentary.
The output must be practical enough to use directly as:
- a QA review memo,
- a test debt report,
- a refactoring / stabilization work plan,
- a source for GitHub Issue creation.

---

## Phase overview

| Step | Name | Phase type | Goal / AI Action |
|---|---|---|---|
| 0 | Load required instructions | Discovery | Read routing, rules, this skill, `workflow.md`, `discovery.md`, `safety.md`, `evidence.md`, `report-template.md` before starting. |
| 1 | Discover test entry points | Discovery | Identify every test/validation command the repository defines; execute nothing. |
| 2 | Safety evaluation | Analysis | Classify every discovered command `Safe` / `Safe with isolated infrastructure` / `Blocked` / `Not runnable` / `Prohibited`, before anything runs. |
| 3 | Execute safe commands | Execution | Run every command Step 2 cleared, within the Full-Suite Execution Scope and Abort Conditions. |
| 4 | Failure reproduction confirmation | Execution | Re-run each failure to establish deterministic-vs-flaky and root cause with cited evidence. |
| 5 | Gap analysis | Analysis | Find missing/weak and inconsistent/outdated tests against current source and docs. |
| 6 | Consolidate findings | Analysis | Merge Steps 4-5 into one Finding list with stable IDs, categories, and severities. |
| 7 | Convert to implementation plan | Analysis | Turn each Finding into Task(s) and Test Case(s), fully cross-referenced by ID. |
| 8 | Final report | Analysis | Assemble the fixed Report Template from Steps 1-7's already-derived content. |

See `workflow.md` for the detailed per-step procedure.

---

## Phase Boundaries (Discovery / Execution / Analysis)

Every step above is exactly one of three phase types. Do not blur them — a step's
phase type bounds what it may do, regardless of what seems convenient in the moment.

- **Discovery** — read-only inspection: reading files, `grep`/`find`, listing test
  entry points, dry-run/collect-only commands that do not execute test bodies (e.g.
  `pytest --collect-only`). No command with real side effects, even isolated or
  ephemeral ones. Applies to Step 1.
- **Execution** — running a command that actually exercises test/validation logic,
  with real side effects even if isolated/ephemeral. Only Steps 3 and 4 may execute
  such a command, and only one Step 2 has already classified `Safe` (or `Safe with
  isolated infrastructure`).
- **Analysis** — drawing conclusions from already-collected Discovery/Execution
  output, or deciding safety, without executing any new test/validation command.
  Applies to Step 2 (the safety decision itself is Analysis, not Execution), and to
  Steps 5, 6, 7, and 8.

If an Analysis step (2, 5-8) reveals a genuine need to run something that Step 3/4 did
not already run, do not execute it inline — record it as a gap and route it back to a
new Step 2-4 cycle. Do not modify production code in any step unless the user
explicitly requested it.

---

## Priority and Effort — separate vocabularies, never interchanged

Two independent axes describe every Task (Step 7). Do not use one vocabulary for the
other, and do not introduce a third.

- **Priority** — how urgently the task should be done: `P1 (Critical)` / `P2
  (Important)` / `P3 (Nice to have)`. Criteria:
  - `P1`: existing test failures confirmed in Step 4, or production code paths with
    no test coverage at all (Step 5).
  - `P2`: missing coverage for complex branches, config/reload behavior,
    persistence, or CLI commands (Step 5).
  - `P3`: weak assertions, test/doc inconsistencies, optional coverage improvements
    (Step 5).
- **Effort** — how much work the task takes: `Low` (<4h) / `Medium` (4-16h) / `High`
  (>16h).

Priority and Effort MUST NOT be written as "High priority" or "Low priority" — that
phrasing conflates the two axes. Every Task record (Step 7) and the Report Template's
Task List MUST show both fields separately; neither MAY stand in for the other.

---

## Core Execution Rules

- MUST NOT stop after the first failure within the Full-Suite Execution Scope (`safety.md`).
- MUST NOT assume test coverage from file names alone.
- MUST NOT edit production code unless explicitly requested.
- MUST NOT stop at high-level commentary — run the tests and produce a concrete,
  execution-ready plan.
- **No unrelated changes**: see `AGENTS.md` Global Rule 5.
- Out-of-scope paths: see `skills/DESIGN.md` Out-of-scope paths.

---

## Output format

This phase does not produce a fixed document ahead of time — its output is a
Markdown report. See `report-template.md` for the exact structure and the Optional
Extra Output (GitHub Issue Drafts).

---

## See Also
See `workflow.md` for detailed phase content and the toolchain reference.
See `discovery.md` for test-entry-point discovery and gap-analysis categories.
See `safety.md` for the safety-classification procedure and execution scope/abort
conditions.
See `evidence.md` for Result Classification, the flaky/root-cause evidence procedure,
Finding Categories, and the Finding/Task/Test Case ID scheme.
See `report-template.md` for the final report structure and content rules.

---

## Composes with

### Run after this skill
- `issue-creator` — to file the `P1` Findings/Tasks the user wants tracked outside
  this report.
- `python-test-and-fix` — to actually implement a Task's proposed test case(s).
- `python-implementation` / `python-debug-root-cause` — to fix a confirmed
  production-code-bug Finding.

### This skill may be triggered by
- A user request to audit, stabilize, or assess the health of the test suite as a
  whole (not a single failing test — see this skill's description).

---

## Improvement feedback

If a Step needed clarification, a safety classification produced a false
positive/negative, or an evidence rule was insufficient, update
`workflow.md`/`safety.md`/`evidence.md` accordingly. If the report was missing a
field the user consistently requested, add it to `report-template.md`.
