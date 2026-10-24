# Test Audit — Detailed Workflow

## Workflow position

This is a standalone, auxiliary workflow, not a phase of the
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
- Production code: see `SKILL.md` Phase Boundaries.
- Writing is limited to the final Markdown report, saved per `report-template.md`
  Report Content Rules' destination logic — MUST NOT create a new report directory
  without an existing repository rule or the user's instruction — and to command output
  files in a temporary directory outside the repository (Step 3).
- The audit changes no tracked file: see `safety.md` "Commands that modify the working
  tree".

## Out of Scope

Apply `rules/ai-execution.md` Global Safety Restrictions (Base) and `AGENTS.md` Global
Rule 5 (no unrelated refactoring, cleanup, or broad formatting-only rewrites).
Additionally for this workflow, MUST NOT perform any of the following:
- changing configuration, environment variables, or feature flags solely to make a
  test runnable (see `safety.md` No test-only configuration changes)
- running a command `safety.md` classifies `Blocked`/`Not runnable`/`Prohibited`
- inferring `Pass` for an unexecuted or partially executed check (see `evidence.md`
  Result Classification)

---

## Toolchain

Per `rules/ai-execution.md` Repository Tool Usage, prefer repository-defined commands
over invented ones. The candidate sources Step 1 draws from — every command still goes
through Step 2's safety evaluation before it runs:

| Source | What it supplies |
|---|---|
| `rules/toolchain.md` | the standard validation sequence (format, lint, type, architecture, security, test) and the coverage command sequence |
| `routing.md` Tools → "When to run which tool" | repository checkers (docs, DB separation, module size, tool-description sync, and others) |
| `pyproject.toml`, CI workflows | pytest configuration, markers, plugins, and the commands CI runs |
| `tools/run_validation_gates.py` | an on-demand runner for the routing checkers (fast mode) and, with `--full`, the standard sequence including the full test suite — if used, do not also run the same commands separately |
| `uv run pytest` options such as `--testmon` | impact-based selection, for Step 4 re-runs only |

If CI and the local commands differ, report that explicitly (see Important Rules).

---

## Step 0: Load Required Instructions

If not already loaded, read the following before starting:
- `routing.md`
- `AGENTS.md`
- `rules/toolchain.md`
- `rules/env.md`
- `rules/ai-execution.md`
- `skills/DESIGN.md` (Evidence labels, No source-code line numbers, Docs content
  policy — remove — needed for `evidence.md`'s Step 4 procedure)
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
command list — MUST NOT execute any of them here.

Record the audited baseline with read-only git commands: `git rev-parse HEAD` and
`git status --short`. Step 8 reports it (`report-template.md` `# 1`), so the report says
which code was audited.

---

## Step 2: Safety Evaluation (Analysis)

Follow `safety.md` Safety Evaluation in full: classify every Step 1 command as `Safe`
/ `Safe with isolated infrastructure` / `Blocked` / `Not runnable` / `Prohibited`. MUST NOT run any command in this step. This also defines the Full-Suite Execution Scope for
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

Lint and formatting run in their check-only forms (`safety.md` "Commands that modify the
working tree"), never the `--fix` or in-place forms.

MUST NOT run only one test command if the repository clearly has multiple validation
layers. If tests need to be run in a specific order, follow the order the repository
defines (`rules/toolchain.md`, CI workflows); MUST NOT invent one.

Do not enable `--reruns` (`pytest-rerunfailures`) here: a failure that passes on rerun
would be reported as a pass and hide the flakiness Step 4 must classify.

Run pytest the way CI does (`.github/workflows/ci.yml`: `uv run pytest -v`, and
`uv run coverage run -m pytest tests/` for coverage): one process, no `-n`. Do not add
`-n` (`pytest-xdist`) in Step 3 or Step 4; it changes test ordering relative to the
`--randomly-seed` recorded here.

If `rules/toolchain.md` defines a coverage command sequence, include it as a candidate
in Step 1. Once Step 2 clears it, it MUST serve as the run of the test suite it wraps —
one execution, not a plain run plus a coverage run. Record the overall and per-module
coverage figures from its summary; Step 5 reads them from there. If it was not cleared,
record coverage as not measured.

A full run can take several minutes and exceed a foreground command's time limit. Run it
in the background with output redirected to a file in a temporary directory outside the
repository (`mktemp -d`), and read only the summary line and the `FAIL`/`ERROR` lines.

After the run, repeat `git rev-parse HEAD` and `git status --short` and compare them with
Step 1's baseline. A tracked file that changed during the run (another session, or a
command that wrote to it) makes every result that depends on that file `Needs
confirmation`; if a command of this audit modified a tracked file, stop and report which
command and file.

For each executed command, record: exact command, purpose, and its Result
Classification (`evidence.md`), per `rules/ai-execution.md` Repository Tool Usage
rule 10. For a pytest run, also record the `--randomly-seed` value when the header
prints one. For a `Fail` or `Partial` result, also record the failing test names. MUST
NOT classify flaky-vs-deterministic or root cause here; defer to Step 4.

---

## Step 4: Failure Reproduction Confirmation (Execution)

For every `Fail`/`Partial` result from Step 3, apply `evidence.md` Evidence Criteria
for Root Cause and Flaky Classification: re-run in isolation, record the
deterministic/flaky determination with its evidence ratio, and record the root cause
with its cited evidence location and confidence label.

Re-run by node id (one test), not by file. When the failing set is large (a rule of thumb
proposed here: more than 10 tests), group the failures by identical failure signature and
re-run one representative per signature; report the others as `same signature as F-{NNN},
not individually re-run`.

For each confirmed failure, record: failing test name/file, failure type, stack trace
summary, deterministic-or-flaky (with evidence), root cause (with evidence), and — if
the root cause is an environment or setup issue — the required env vars or services
(refer to `rules/env.md` for this repository's environment spec).

---

## Step 5: Gap Analysis (Analysis)

Follow `discovery.md` Gap Analysis in full: Missing or weak tests, and Inconsistent or
outdated tests.

---

## Step 6: Consolidate Findings (Analysis)

Merge Step 4's confirmed failures and Step 5's gaps/inconsistencies into a single
Finding list. Assign each a `F-{NNN}` ID (per `evidence.md` Finding, Task, and Test
Case IDs), a category (per `evidence.md` Finding Categories), and a severity (per
`skills/DESIGN.md` Severity levels).

Report the consolidated Finding list before proceeding to Step 7; Step 7's Tasks and
Test Cases MUST cite it by ID.

---

## Step 7: Convert to Implementation Plan (Analysis)

For every Finding from Step 6, create one or more Tasks (`T-{NNN}`, citing
`Addresses: F-{NNN}`) with Priority and Effort assigned per `SKILL.md` Priority and
Effort, and one or more Test Cases (`TC-{NNN}`, citing `Task:`/`Finding:`) per
`evidence.md` Finding, Task, and Test Case IDs.

MUST NOT leave a Finding unaddressed without saying so explicitly.

---

## Step 8: Final Report (Analysis)

Follow `report-template.md` in full: assemble the Report Template using Steps 1-7's
already-derived IDs and content, per Report Content Rules. MUST NOT re-derive or
re-analyze anything here. Generate the optional GitHub Issue Drafts section only when
the user explicitly requests it.

---

## Important Rules

These rules MUST be followed, in addition to `evidence.md`'s classification procedures:
- MUST NOT silently ignore skipped or blocked tests — instead, record each one
  explicitly in the audit findings using `evidence.md`'s classification procedures,
  with the reason it was skipped or blocked.
- If CI and local commands differ, report that explicitly.
- Prefer repository-defined commands over invented ones, per `rules/ai-execution.md`
  Repository Tool Usage rule 5.
- If a service dependency is missing, explain exactly what blocked execution.
- For missing tests, tie each proposal to concrete code paths or documented behavior,
  and to a Finding ID.
- Regression tests SHOULD be preferred for bug-like mismatches.
- MUST NOT give vague advice such as "increase coverage".
- Every proposed test addition or update MUST be actionable and traceable to a Task ID.

## Test-Specific Guidance

- In Step 3, use quiet/short-traceback modes (e.g. `pytest -q --tb=short`) and read
  coverage from a summary (`coverage.xml` or the summary line) rather than verbose
  per-line reports. MUST NOT read full output for passing runs.
- In Step 4, keep stack trace summaries to the minimum lines needed to identify the
  cause; MUST NOT paste full tracebacks.
- Redirect each validation command's output to a file and extract only
  `FAIL`/`ERROR` lines via `grep`, rather than reading the full raw stream.
- Perform Step 1 discovery sequentially; return only the identified commands and
  structure, not full file contents.
- Perform Step 5 gap analysis sequentially by layer: see `discovery.md` Gap Analysis.
- Shared-file re-reading: see `rules/ai-execution.md` Context Reading.
- In Steps 6-7, reference findings by Finding ID rather than re-quoting evidence or
  source excerpts already recorded in Step 3/4/5.
- Include all failures, blocking issues, and important validation results even in
  concise reports.

## Output format

See `report-template.md` for the exact final-report structure; the report is Step 8's
output.
