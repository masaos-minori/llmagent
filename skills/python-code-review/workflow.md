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
| Project checkers (table below) | 2–7 | Re-use the repository's own structural checks as evidence; each runs only for the diff type it covers |
| `uv run python tools/run_validation_gates.py --base <base>` | 2–7 | One-shot alternative: selects and runs the gates the changed files need |

Project checkers (from `routing.md` "When to run which tool"; run those whose trigger
matches the diff and list each with its result under Commands run):

| Diff touches | Run |
|---|---|
| a DB schema DDL, a `*_db_path` config key, `ATTACH`/`load_vec` | `uv run python tools/check_db_separation.py` |
| a `scripts/**/*.py` module (new, or grown) | `uv run python tools/check_module_size.py` |
| a `patch("module.Symbol")` in `tests/`, or a moved symbol import in `scripts/` | `uv run python tools/check_mock_patch_targets.py` |
| a `# noqa` / `# type: ignore` / `# nosec` | `uv run python tools/check_suppression_justification.py` |
| `scripts/agent/`, `scripts/eventbus/`, `scripts/mcp_servers/`, `scripts/db/config.py`, `config/agent.toml` | `uv run python tools/generate_reference_table.py --check` |
| a `docs/*.md` file | `uv run python tools/check_docs_quality.py` and `uv run python tools/check_docs_structure.py` |
| a `skills/*.md`, `rules/*.md`, or `prompts/*.md` file | `uv run python tools/check_skills_references.py` |

Checkers are read-only. A checker failure is evidence for a finding (cite its output); a
checker that cannot run is `Needs confirmation`.

Apply `skills/DESIGN.md` Agent (Explore) threshold.
Run a tool to confirm a finding before reporting it; MUST NOT present a suspected issue as confirmed without evidence.

Within a Phase, run its tools after the manual checks in that Phase's list, so a tool
confirms or refutes a finding the manual checks produced rather than replacing them. Run
Python tools through `uv run`, and pass touched files explicitly (a bare `uv run mypy`
does not cover `tools/`). If a tool is unavailable in the current
environment, record the affected checks as `Needs confirmation` (per `skills/DESIGN.md`
Evidence labels) and continue with the remaining checks — MUST NOT stop the review.

---

## Phase 1: Scope and Intake

Identify the reviewed unit: PR, diff, patch, or a named set of files.

Do:
- determine the diff boundary (`git diff <base>...<head>`, `gh pr diff` for a PR, or the stated file list)
- confirm the working tree is at `<head>` (`git rev-parse HEAD` against the head being reviewed) before any tool runs: the tools check the working tree, not the diff. If it is not, MUST NOT `git checkout`, `git switch`, or `gh pr checkout` in the user's working tree (it would change files). Either create a temporary read-only worktree outside the repository for the head (`git worktree add --detach <scratchpad dir>/review-<sha> <head>`, run the tools inside it, then remove it with `git worktree remove` — only that worktree, never `rm -rf`), or, if that is not possible, record that the tool results describe a different version and carry them as `Needs confirmation`
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
- check performance and concurrency hazards in changed code: unbounded loops or growth, N+1 queries, repeated I/O in hot paths, shared mutable state without synchronization, race windows between check and use
- check the change against `rules/coding.md` Prohibited patterns; each match is a finding
- check public contracts against the `skills/DESIGN.md` Pythonic safety constraints, applied here as review criteria (typing correctness, `Any` usage, optional-value handling, protocol conformance)
- import direction, circular imports, and cross-layer access are checked in Phase 3, not here
- run `ruff check` / `mypy` or `pyright` on touched files to confirm type and lint findings

**Completed when**: every check above has been applied to each changed function in
the diff, and `ruff check`/`mypy`/`pyright` have been run on touched files.

---

## Phase 3: Architecture and Boundaries

Do:
- verify dependency direction matches the repository's layering rules (e.g. `.importlinter`)
- check import direction and circular-import risk introduced by the change
- check responsibility boundaries and cross-layer access (e.g. domain code reaching into infra directly)
- flag new cross-layer imports or widened public surface without justification
- check whether the change introduces an abstraction (`Protocol`, `abc.ABC`, factory) without a concrete requirement
- run `PYTHONPATH=scripts uv run lint-imports` to confirm the dependency-direction findings
- run the project checkers from the Toolchain table whose trigger matches the diff
  (`check_db_separation`, `check_module_size`, `generate_reference_table --check`, ...)

**Completed when**: dependency direction, import-cycle, boundary, and abstraction-
introduction checks have been applied to every changed import/interface in the diff,
`lint-imports` has been run (or recorded as unavailable), and each matching project
checker has been run or recorded `Needs confirmation`.

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
- check input validation at trust boundaries (HTTP and MCP inputs, file paths, subprocess arguments), and authorization or approval checks on tool-executing paths
- check SQLite and sqlite-vec usage: parameterized queries, transaction scope and commit/rollback on error paths, connection lifetime, and the 4DB separation (no cross-DB access; see `tools/check_db_separation.py`)
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
  production path, MUST NOT run the tests — record the affected checks as `Needs confirmation`
- run `pytest` on the affected test targets: the tests under each changed file's module
  path plus any test that `rg` shows importing a changed symbol (`pytest --testmon`
  when available), to confirm the claimed pass/fail state
- before reporting a failing test as a finding, re-run it once in isolation; a failure
  that does not reproduce is reported as `Needs confirmation`, not as a confirmed finding
- check CI quality gates and type-checking coverage for the touched paths: read the
  workflows under `.github/workflows/` (notably `ci.yml`), `.pre-commit-config.yaml`, and
  `tox.ini`, and confirm each touched path is covered by lint, type-check, test, and
  `lint-imports` gates (for example, `mypy`'s configured `files` scope omits `tools/`)

**Completed when**: test coverage has been checked for every critical/edge/failure
path touched by the diff, CI gate coverage has been checked for the touched paths from
those files, and `pytest` has been run (or recorded `Needs confirmation` because
isolation could not be confirmed) to confirm the claimed pass/fail state.

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
- an evidence label (exact spelling from `skills/DESIGN.md` Evidence labels) and a
  confidence level per `skills/DESIGN.md` Confidence levels
- a severity per `skills/DESIGN.md` Severity levels, assessed as if the finding is true

A Critical or High finding with Low confidence is also copied to the report's Open
Questions with the confirmation needed. Then sort the findings by severity and assign IDs
`F-001`, `F-002`, ... in that order.

**Completed when**: every finding carried forward from Phases 2-7 has concrete
evidence, an evidence label/confidence level, a severity, and an ID assigned.

---

## Phase 9: Report Writing

Use the Output Format defined in `SKILL.md`, including its no-findings form when nothing
survives Phase 8. Group findings by severity. MUST NOT over-report style-only issues. Keep recommendations actionable; for suggested tests, specify the exact
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
