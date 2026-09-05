# Python Code Review — Detailed Workflow

## Toolchain

| Tool | Phase | Role |
|---|---|---|
| `Bash` (`git diff`, `git log`) | 1 Scope | Identify the reviewed diff, PR, or patch boundary |
| `Bash` (`grep`, `rg`) | 2–7 | Cross-search symbols, call sites, config keys, and patterns |
| `Read` | 2–7 | Read individual files in full detail before judging them |
| `Agent` (Explore) | 2–4 | Broad search when the review spans many files or packages |
| `ruff check`, `mypy` / `pyright` | 2, 4 | Confirm type-safety and lint findings are real, not speculative |
| `bandit` | 5 | Confirm security findings with static analysis where available |
| `pytest` | 6 | Confirm claimed test coverage or failure actually reproduces |

Prefer `Bash (grep)` + `Read` for targeted lookups before spawning `Agent (Explore)`.
Run a tool to confirm a finding before reporting it; do not present a suspected issue as
confirmed without evidence.

---

## Phase 1: Scope and Intake

Identify the reviewed unit: PR, diff, patch, or a named set of files.

Do:
- determine the diff boundary (`git diff <base>...<head>` or the stated file list)
- identify the change's stated intent (PR description, commit message, or user request)
- identify out-of-scope files per `skills/DESIGN.md` Out-of-scope paths (generated code, vendored code, build outputs)

---

## Phase 2: Correctness and Data Consistency

Do:
- trace each changed function for edge cases: empty input, `None`, boundary values, concurrent access
- check state transitions, idempotency, caching invalidation, and data consistency
- check import direction and circular-import risk introduced by the change
- check responsibility boundaries and cross-layer access (e.g. domain code reaching into infra directly)
- check public contracts against `skills/DESIGN.md` Pythonic safety constraints (typing correctness, `Any` usage, optional-value handling, protocol conformance)
- run `ruff check` / `mypy` or `pyright` on touched files to confirm type and lint findings

---

## Phase 3: Architecture and Boundaries

Do:
- verify dependency direction matches the repository's layering rules (e.g. `.importlinter`)
- flag new cross-layer imports or widened public surface without justification
- check whether the change introduces an abstraction (`Protocol`, `abc.ABC`, factory) without a concrete requirement

---

## Phase 4: Async/Sync Boundaries and Resource Lifecycle

Check compliance with `skills/DESIGN.md` Pythonic safety constraints:
- check for blocking calls inside `async def` without an executor boundary
- check file, socket, DB connection, HTTP client, subprocess, and async task cleanup (`with` / `async with`)
- check for resource leaks on early-return and exception paths

---

## Phase 5: Error Handling, Configuration, and Logging

Check compliance with `skills/DESIGN.md` Pythonic safety constraints (exception handling,
unsafe dynamic execution) in addition to:
- check exception handling: overly broad `except Exception`, swallowed errors, missing re-raise
- check retries, timeouts, and fail-fast vs. fail-open behavior
- check configuration ownership, startup-only vs. runtime-reloadable settings, and safe defaults
- check logging and diagnostics for secret exposure risk
- run `bandit` where available to confirm security findings (e.g. `eval`/`exec`, `pickle`, `subprocess(shell=True)`, SQL string interpolation)

---

## Phase 6: Tests and CI

Do:
- verify tests exist for critical behavior, edge cases, and failure paths introduced or touched by the change
- run `pytest` on the affected test targets to confirm claimed pass/fail state
- check CI quality gates and type-checking coverage for the touched paths

---

## Phase 7: Documentation Mismatches

Do:
- identify documentation that now contradicts the changed behavior
- ground every mismatch claim in the current implementation, not in memory of prior versions
- avoid implementation-reference duplication: see `skills/DESIGN.md` Avoid implementation-reference duplication and Docs content policy — remove

---

## Phase 8: Evidence, Confidence, and Severity Assignment

For every finding, attach:
- concrete evidence: file path, class/function/method/route/command/config key, test name, or CI workflow, and the observed current behavior
- an evidence label and confidence level per `skills/DESIGN.md` Shared Vocabulary
- a severity per `SKILL.md` Severity

---

## Phase 9: Report Writing

Use the Output Format defined in `SKILL.md`. Group findings by severity. Do not over-report
style-only issues. Keep recommendations actionable; for suggested tests, specify the exact
behavior or failure mode to verify.

---

## Phase 10: GitHub Issue Conversion

When converting findings into GitHub issues:
- use one issue per actionable task; group related findings only when they must be fixed together
- include reason for change, implementation intent, acceptance criteria, out of scope, and testing expectations
- avoid Markdown that breaks when copied
- do not include secrets or unnecessary code blocks
