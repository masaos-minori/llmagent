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
See `skills/DESIGN.md`, section "Safety-over-speed priority".
The output MUST be usable directly as each of: a QA review memo, a test debt report, a refactoring / stabilization work plan, and a source for GitHub Issue creation.

---

## Phase overview

| Step | Name | Phase type | Goal / AI Action |
|---|---|---|---|
| 0 | Load required instructions | Discovery | Read every file listed in `workflow.md` Step 0 before starting. |
| 1 | Discover test entry points | Discovery | Identify every test/validation command the repository defines and record the audited revision (`HEAD`, `git status --short`); execute nothing. |
| 2 | Safety evaluation | Analysis | Classify every discovered command `Safe` / `Safe with isolated infrastructure` / `Blocked` / `Not runnable` / `Prohibited`, before anything runs: isolation scope, exempt tests, port collisions with running services, and commands that would modify tracked files. |
| 3 | Execute safe commands | Execution | Run every command Step 2 cleared, within the Full-Suite Execution Scope and Abort Conditions. |
| 4 | Failure reproduction confirmation | Execution | Re-run each failure to establish deterministic-vs-flaky and root cause with cited evidence. |
| 5 | Gap analysis | Analysis | Find missing/weak and inconsistent/outdated tests against current source and docs. |
| 6 | Consolidate findings | Analysis | Merge Steps 4-5 into one Finding list with stable IDs, categories, and severities. |
| 7 | Convert to implementation plan | Analysis | Turn each Finding into Task(s) and Test Case(s), fully cross-referenced by ID. |
| 8 | Final report | Analysis | Assemble the fixed Report Template from Steps 1-7's already-derived content. |

See `workflow.md` for the detailed per-step procedure.

---

## Phase Boundaries (Discovery / Execution / Analysis)

Every step above is exactly one of three phase types. MUST NOT blur them — a step's
phase type bounds what it may do.

- **Discovery** — read-only inspection: reading files, `grep`/`find`, listing test
  entry points. No command with real side effects, even isolated or ephemeral ones —
  this includes `pytest --collect-only`, which imports `conftest.py` and every test
  module and is therefore an Execution command. Applies to Step 1.
- **Execution** — running a command that actually exercises test/validation logic,
  with real side effects even if isolated/ephemeral. Only Steps 3 and 4 may execute
  such a command, and only one Step 2 has already classified `Safe` (or `Safe with
  isolated infrastructure`).
- **Analysis** — drawing conclusions from already-collected output, or deciding
  safety, without executing any new test/validation command. Applies to Step 2 (the safety decision itself is Analysis) and Steps 5, 6, 7, and 8.

If an Analysis step (2, 5-8) reveals a genuine need to run something that Step 3/4 did
not already run, MUST NOT execute it inline — record it as a gap and route it back to a
new Step 2-4 cycle, scoped to only the newly-identified command(s), not a full re-run
of Step 3. This audit tolerates at most 3 such Step 2-4 re-entry cycles in one run
(per `AGENTS.md` Loop Prevention > Attempt Limit); if a 4th genuine need surfaces,
stop routing back and record it as an unexecuted gap in the Step 8 report. MUST NOT
modify production code in any step unless the user explicitly requested it.

---

## Priority and Effort — separate vocabularies, never interchanged

Two independent axes describe every Task (Step 7). MUST NOT use one vocabulary for the
other or introduce a third. (A Finding's Severity is a property of the Finding, not a
Task axis.)

- **Priority** — how urgently the task should be done: `P1 (Critical)` / `P2
  (Important)` / `P3 (Nice to have)`. Criteria:
  - `P1`: an existing test failure confirmed in Step 4, or a Finding of severity
    `Critical` or `High`.
  - `P2`: a Finding of severity `Medium` (e.g. missing coverage for complex branches,
    config/reload behavior, persistence, or CLI commands; fragile tests).
  - `P3`: a Finding of severity `Low` or `Informational` (e.g. weak assertions,
    test/doc inconsistencies, optional coverage improvements).

  Severity belongs to the Finding (Step 6, `skills/DESIGN.md` Severity levels, which this
  skill MUST NOT replace); Priority belongs to the Task. A Task's Priority is the highest
  tier among the Findings it addresses. A code path without tests is `Critical`/`High`
  only when a failure there would meet that tier's definition in `skills/DESIGN.md`;
  absence of tests alone is not enough.
- **Effort** — how much work the task takes: `Low` (<4h) / `Medium` (4-16h) / `High`
  (>16h).

Priority and Effort MUST NOT be written as "High priority" or "Low priority" — that
phrasing conflates the two axes. Every Task record (Step 7) and the Report Template's
Task List MUST show both fields separately; neither MAY stand in for the other.

---

## Core Execution Rules

- Full-Suite Execution Scope: see `safety.md` Full-Suite Execution Scope and Abort Conditions.
- MUST NOT assume test coverage from file names alone — open the matching
  test file and confirm it actually exercises the behavior in question before
  crediting it as coverage.
- Production code: see Phase Boundaries above.
- MUST NOT stop at high-level commentary — run the tests and produce a concrete,
  execution-ready plan.
- No unrelated changes: `AGENTS.md` Global Rule 5. Out-of-scope paths: `skills/DESIGN.md` Out-of-scope paths.

---

## Output format

The output is a Markdown report. See `report-template.md` for the exact structure and
the Optional Extra Output (GitHub Issue Drafts). Write the report in English, per
`skills/DESIGN.md` Output language (a Japanese-language conversation does not change
this); keep identifiers, commands, and evidence labels untranslated. The chat summary
that accompanies it follows the chat language.

---

## See Also
- `workflow.md`: detailed phase content and the toolchain reference
- `discovery.md`: test-entry-point discovery and gap-analysis categories
- `safety.md`: safety-classification procedure and execution scope/abort conditions
- `evidence.md`: Result Classification, flaky/root-cause evidence procedure, Finding Categories, ID scheme
- `report-template.md`: final report structure and content rules

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

If a Step needed clarification, a safety classification was a false positive/negative, or an evidence rule was insufficient, update
`workflow.md`/`safety.md`/`evidence.md`. If the report lacked a field the user consistently requested, add it to `report-template.md`.
