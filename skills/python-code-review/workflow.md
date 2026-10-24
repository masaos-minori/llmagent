# Python Code Review — Detailed Workflow

## Toolchain

| Tool | Phase | Role |
|---|---|---|
| `Bash` (`git diff`, `git log`, `git rev-parse`) | 1 Scope | Identify the reviewed diff, PR, or patch boundary, and confirm the working tree is at the reviewed head |
| `Bash` (`gh pr view`, `gh pr diff`) | 1 Scope | Read a PR's description and diff when the review target is a PR |
| `Bash` (`grep`, `rg`) | 2–7 | Cross-search symbols, call sites, config keys, and patterns |
| `Read` | 2–7 | Read individual files in full detail before judging them |
| `Agent` (Explore) | 2–4 | Broad search when the review spans many files or packages |
| `ruff check`, `mypy` / `pyright` | 2, 4 | Confirm type-safety and lint findings are real, not speculative |
| `PYTHONPATH=scripts uv run lint-imports` | 3 | Confirm dependency-direction findings against `.importlinter` (command per `rules/toolchain.md`) |
| `bandit` | 5 | Confirm security findings with static analysis where available |
| `pytest` | 6 | Confirm claimed test coverage or failure actually reproduces, only after Phase 6's isolation check |
| `uv run python tools/check_docs_consistency.py --domain <domain>` | 7 | Ground a doc/code mismatch in config keys, ports, and symbols (see `routing.md` Tools) |

Apply `skills/DESIGN.md` Agent (Explore) threshold.
Run a tool to confirm a finding before reporting it; MUST NOT present a suspected issue as confirmed without evidence.

Within a Phase, run its tools after the manual checks in that Phase's list, so a tool
confirms or refutes a finding the manual checks produced rather than replacing them. Run
Python tools through `uv run`, and pass touched files explicitly (a bare `uv run mypy`
does not cover `tools/`). If a tool is unavailable in the current
environment, record the affected checks as `Needs Confirmation` (per `skills/DESIGN.md`
Shared Vocabulary) and continue with the remaining checks — MUST NOT stop the review.

---

## Phase 1: Scope and Intake

Identify the reviewed unit: PR, diff, patch, or a named set of files.

Do:
- determine the diff boundary (`git diff <base>...<head>`, `gh pr diff` for a PR, or the stated file list)
- confirm the working tree is at `<head>` (`git rev-parse HEAD` against the head being reviewed) before any tool runs: the tools check the working tree, not the diff. If it is not, record that the tool results describe a different version and carry them as `Needs Confirmation`
- identify the change's stated intent (PR description, commit message, or user request)
- identify out-of-scope files per `skills/DESIGN.md` Out-of-scope paths (generated code, vendored code, build outputs)
- when the target is a file list with no diff (a review of existing code), treat every function in those files as changed for the Phases below
- for a large diff, review in risk order — public contracts, persistence, async/resource handling, error handling first — and record any file left unreviewed so the report can state it

**Completed when**: the diff boundary, the working-tree/head check, and the stated intent
are all recorded.
**Stop and ask the user before Phase 2 when**: no diff boundary can be determined (no PR,
diff, or file list is identifiable); there is nothing to review. Every later Phase's
"tool unavailable" case (see Toolchain) is handled by recording `Needs Confirmation`
and continuing, not by stopping here.

---

## Phase 2: Correctness and Data Consistency

Do:
- trace each changed function for edge cases: empty input, `None`, boundary values, concurrent access
- check state transitions, idempotency, caching invalidation, and data consistency
- check import direction and circular-import risk introduced by the change
- check responsibility boundaries and cross-layer access (e.g. domain code reaching into infra directly)
- check public contracts against `skills/DESIGN.md` Pythonic safety constraints (typing correctness, `Any` usage, optional-value handling, protocol conformance)
- run `ruff check` / `mypy` or `pyright` on touched files to confirm type and lint findings

**Completed when**: every check above has been applied to each changed function in
the diff, and `ruff check`/`mypy`/`pyright` have been run on touched files.

---

## Phase 3: Architecture and Boundaries

Do:
- verify dependency direction matches the repository's layering rules (e.g. `.importlinter`)
- flag new cross-layer imports or widened public surface without justification
- check whether the change introduces an abstraction (`Protocol`, `abc.ABC`, factory) without a concrete requirement
- run `PYTHONPATH=scripts uv run lint-imports` to confirm the dependency-direction findings

**Completed when**: dependency direction and abstraction-introduction checks have
been applied to every changed import/interface in the diff, and `lint-imports` has been
run (or recorded as unavailable).

---

## Phase 4: Async/Sync Boundaries and Resource Lifecycle

Check compliance with `skills/DESIGN.md` Pythonic safety constraints:
- check for blocking calls inside `async def` without an executor boundary
- check file, socket, DB connection, HTTP client, subprocess, and async task cleanup (`with` / `async with`)
- check for resource leaks on early-return and exception paths

**Completed when**: every changed `async def`/resource-acquiring code path in the
diff has been checked for blocking calls and cleanup on both normal and exception
paths.

---

## Phase 5: Error Handling, Configuration, and Logging

Check compliance with `skills/DESIGN.md` Pythonic safety constraints (exception handling,
unsafe dynamic execution) in addition to:
- check exception handling: overly broad `except Exception`, swallowed errors, missing re-raise
- check retries, timeouts, and fail-fast vs. fail-open behavior
- check configuration ownership, startup-only vs. runtime-reloadable settings, and safe defaults
- check logging and diagnostics for secret exposure risk
- check input validation at trust boundaries (HTTP and MCP inputs, file paths, subprocess arguments)
- run `bandit` where available to confirm security findings (e.g. `eval`/`exec`, `pickle`, `subprocess(shell=True)`, SQL string interpolation)

**Completed when**: every changed error-handling/config/logging code path has been
checked, and `bandit` has been run where available.

---

## Phase 6: Tests and CI

Do:
- verify tests exist for critical behavior, edge cases, and failure paths introduced or touched by the change
- before running any test, confirm the suite cannot touch production state, per
  `skills/test-audit/safety.md` "Verify the test suite's own isolation before classifying
  `Safe`" (production paths from `rules/env.md`, the isolation mechanism in `conftest.py`,
  and the markers for tests that start real subprocesses); if no isolation covers a
  production path, MUST NOT run the tests — record the affected checks as `Needs Confirmation`
- run `pytest` on the affected test targets: the tests under each changed file's module
  path plus any test that `rg` shows importing a changed symbol (`pytest --testmon`
  when available), to confirm the claimed pass/fail state
- before reporting a failing test as a finding, re-run it once in isolation; a failure
  that does not reproduce is reported as `Needs Confirmation`, not as a confirmed finding
- check CI quality gates and type-checking coverage for the touched paths

**Completed when**: test coverage has been checked for every critical/edge/failure
path touched by the diff, and `pytest` has been run (or recorded `Needs Confirmation`
because isolation could not be confirmed) to confirm the claimed pass/fail state.

---

## Phase 7: Documentation Mismatches

Do:
- identify documentation that now contradicts the changed behavior
- ground every mismatch claim in the current implementation, not in memory of prior versions; for config keys, ports, and symbols, run `uv run python tools/check_docs_consistency.py --domain <domain>` (domains per `routing.md` Tools)
- avoid implementation-reference duplication: see `skills/DESIGN.md` Avoid implementation-reference duplication and Docs content policy — remove

**Completed when**: every doc claim about the changed behavior has been checked
against the current implementation, not against a prior-version recollection.

---

## Phase 8: Evidence, Confidence, and Severity Assignment

For every finding, attach:
- concrete evidence per `SKILL.md` Evidence Rules
- an evidence label and confidence level per `skills/DESIGN.md` Shared Vocabulary
- a severity per `skills/DESIGN.md` Severity levels

**Completed when**: every finding carried forward from Phases 2-7 has concrete
evidence, an evidence label/confidence level, and a severity assigned.

---

## Phase 9: Report Writing

Use the Output Format defined in `SKILL.md`. Group findings by severity. MUST NOT over-report
style-only issues. Keep recommendations actionable; for suggested tests, specify the exact
behavior or failure mode to verify.

**Completed when**: the report follows `SKILL.md`'s Output Format, findings are
grouped by severity, and no style-only issue is over-reported.

---

## Phase 10: Issue Conversion

Run this phase only when the user requests issue conversion; otherwise Phase 9's report is
the final output. This phase writes files: `skills/issue-creator/SKILL.md` writes one
Markdown file per issue under `issues/` (it does not post to GitHub). Writing them is this
skill's designated output phase, not a violation of the analysis-only constraint
(`skills/DESIGN.md`).

Delegate issue authoring entirely to `skills/issue-creator/SKILL.md`: it owns the field
list (`templates/issue.md`), the grouping/splitting criteria, the sibling-issue check, the
filename, and the verification. When it is called from here, its "Input from review
findings" (`skills/issue-creator/workflow.md`) defines how each finding's location,
evidence, confidence, and suggested fix map into the issue — do not restate that mapping
or a field list here. Apply in order: choose the findings (10a), then run `issue-creator`
(10b), then check the written files (10c).

### Step 10a: Choose the findings that feed `issue-creator`

- Feed findings of severity `Critical`, `High`, and `Medium`; feed `Low` or
  `Informational` findings only if the user asked for them.
- A finding whose confidence is below confirmed is still fed, and `issue-creator` records
  it under `Unresolved Questions`; an Open Question from the report is fed only if it
  blocks a fed finding.
- Hand the chosen findings to `issue-creator` together; its Phase 2 decides grouping and
  splitting — do not group them here.

### Step 10b: Run `issue-creator`

Follow `skills/issue-creator/SKILL.md` and `workflow.md` for each issue. Report each
written path and Priority in the final answer, as its Phase 10 requires.

### Step 10c: Check the written files for sensitive content

Follow `skills/DESIGN.md` No secrets in output on each written file, and confirm no code
block or evidence excerpt copied from the review contains a secret or a production value.

**Completed when**: every chosen finding is covered by a written issue file (or reported
as `Blocked` by `issue-creator`), and each file passed the 10c check.
