# Test Audit — Detailed Workflow

## Workflow position

This is a standalone, auxiliary workflow — it is not a phase of the
issue → plan → implementation-procedure → code pipeline. It is invoked directly by
filename (`prompts/07_test-audit.md`) to produce a QA review memo / test debt report /
stabilization work plan, not staged through `issues/` -> `plans/` -> `implementations/`.

- Input: none required (operates on the whole repository's test suite); optionally a
  scope hint from the user (a module or layer to focus on).
- Output: a Markdown report (`report-template.md`), plus optional GitHub Issue drafts;
  no source code changes by default.
- Workflow phase: `test-audit`

## Allowed file operations

- Read-only across the repository by default: source code, tests, configuration, CI
  definitions, and docs.
- Do not edit production code unless the user explicitly requests it.
- Writing is limited to the final Markdown report, saved per `report-template.md`
  Report Content Rules' destination logic — do not create a new report directory
  without an existing repository rule.

## Out of Scope

Apply `rules/ai-execution.md` Global Safety Restrictions (Base) and `AGENTS.md` Global
Rule 5 (no unrelated refactoring, cleanup, or broad formatting-only rewrites).
Additionally for this workflow, do not perform any of the following:
- changing configuration, environment variables, or feature flags solely to make a
  test runnable (see `safety.md` No test-only configuration changes)
- running a command `safety.md` classifies `Blocked`/`Not runnable`/`Prohibited`
- inferring `Pass` for an unexecuted or partially executed check (see `evidence.md`
  Result Classification)

---

## Step 0: Load Required Instructions

If not already loaded, read the following before starting:
- `routing.md`
- `AGENTS.md`
- `rules/toolchain.md`
- `rules/env.md`
- `rules/ai-execution.md`
- `skills/DESIGN.md` (Evidence labels, No source-code line numbers — needed for
  `evidence.md`'s Step 4 procedure)
- `SKILL.md` (this skill)
- this file
- `discovery.md`
- `safety.md`
- `evidence.md`
- `report-template.md`

Report progress at the start and end of each step, including its Phase Boundaries type
(Discovery / Execution / Analysis, per `SKILL.md`).

---

## Step 1: Discover Test Entry Points (Discovery)

Follow `discovery.md` Test Entry Point Discovery in full. Output the full candidate
command list — do not execute any of them here.

---

## Step 2: Safety Evaluation (Analysis)

Follow `safety.md` Safety Evaluation in full: classify every Step 1 command as `Safe`
/ `Safe with isolated infrastructure` / `Blocked` / `Not runnable` / `Prohibited`. Do
not run any command in this step. This also defines the Full-Suite Execution Scope for
Step 3 (`safety.md`).

---

## Step 3: Execute Safe Commands (Execution)

Run every command Step 2 classified `Safe` or `Safe with isolated infrastructure`,
applying `safety.md` Full-Suite Execution Scope and Abort Conditions.

This includes, if present and cleared by Step 2:
- unit tests
- integration tests
- e2e tests
- smoke tests
- schema / migration tests
- CLI tests
- API tests
- lint
- type checks
- import boundary checks
- formatting checks
- config/schema consistency checks

Important:
- Do not run only one test command if the repository clearly has multiple validation layers.
- If tests need to be run in a specific order, infer and follow that order.

For each executed command, record: exact command, purpose, and its Result
Classification (`evidence.md`). For a `Fail` or `Partial` result, also record the
failing test names — defer determinism/root-cause analysis to Step 4; do not classify
flaky-vs-deterministic or root cause here.

---

## Step 4: Failure Reproduction Confirmation (Execution)

For every `Fail`/`Partial` result from Step 3, apply `evidence.md` Evidence Criteria
for Root Cause and Flaky Classification: re-run in isolation, record the
deterministic/flaky determination with its evidence ratio, and record the root cause
with its cited evidence location and confidence label.

For each confirmed failure, record: failing test name/file, failure type, stack trace
summary, deterministic-or-flaky (with evidence), root cause (with evidence), and — if
the root cause is an environment or setup issue — the required env vars or services
(refer to `rules/env.md` for this repository's environment spec).

---

## Step 5: Gap Analysis (Analysis)

Follow `discovery.md` Gap Analysis in full: Missing or weak tests, and Inconsistent or
outdated tests. Do not execute any new command in this step.

---

## Step 6: Consolidate Findings (Analysis)

Merge Step 4's confirmed failures and Step 5's gaps/inconsistencies into a single
Finding list. Assign each a `F-{NNN}` ID, a category, and a severity, per
`evidence.md` Finding Categories and Finding, Task, and Test Case IDs. Do not execute
any new command in this step.

Report the consolidated Finding list before proceeding to Step 7 — this is the single
source Step 7's Tasks and Test Cases must cite by ID.

---

## Step 7: Convert to Implementation Plan (Analysis)

For every Finding from Step 6, create one or more Tasks (`T-{NNN}`, citing
`Addresses: F-{NNN}`) with Priority and Effort assigned per `SKILL.md` Priority and
Effort, and one or more Test Cases (`TC-{NNN}`, citing `Task:`/`Finding:`) per
`evidence.md` Finding, Task, and Test Case IDs.

Do not leave a Finding unaddressed without saying so explicitly.

---

## Step 8: Final Report (Analysis)

Follow `report-template.md` in full: assemble the Report Template using Steps 1-7's
already-derived IDs and content, per Report Content Rules. Do not re-derive or
re-analyze anything here. Generate the optional GitHub Issue Drafts section only when
the user explicitly requests it.

---

## Important Rules

These rules MUST be followed, in addition to `evidence.md`'s classification procedures:
- Do not silently ignore skipped or blocked tests.
- If CI and local commands differ, report that explicitly.
- Repository-defined commands SHOULD be preferred over invented commands.
- If a service dependency is missing, explain exactly what blocked execution.
- For missing tests, tie each proposal to concrete code paths or documented behavior,
  and to a Finding ID.
- Regression tests SHOULD be preferred for bug-like mismatches.
- Do not give vague advice such as "increase coverage".
- Every proposed test addition or update MUST be actionable and traceable to a Task ID.

## Test-Specific Guidance

- In Step 3, use quiet/short-traceback modes (e.g. `pytest -q --tb=short`) and read
  coverage from a summary (`coverage.xml` or the summary line) rather than verbose
  per-line reports. Do not read full output for passing runs.
- In Step 4, keep stack trace summaries to the minimum lines needed to identify the
  cause; do not paste full tracebacks.
- Redirect each validation command's output to a file and extract only
  `FAIL`/`ERROR` lines via `grep`, rather than reading the full raw stream.
- Perform Step 1 discovery sequentially; return only the identified commands and
  structure, not full file contents.
- Perform Step 5 gap analysis sequentially by layer (`discovery.md` Gap Analysis).
  Return only each layer's findings, not the source read, so one layer's
  investigation does not accumulate into the next.
- Read shared files in Step 0 only once per session.
- In Steps 6-7, reference findings by Finding ID rather than re-quoting evidence or
  source excerpts already recorded in Step 3/4/5.
- Include all failures, blocking issues, and important validation results even in
  concise reports.

## Output format

See `report-template.md` for the exact final-report structure — this phase does not
generate a single Markdown document with a fixed structure ahead of time; the report
is Step 8's output.
