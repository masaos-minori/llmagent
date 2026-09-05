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

Use `Bash (grep)` + `Read` when the search needs fewer than 3 queries; spawn `Agent
(Explore)` once a review needs 3 or more queries or spans more than one package (same
threshold as `skills/python-documentation/workflow.md` Tool selection rules).
Run a tool to confirm a finding before reporting it; do not present a suspected issue as
confirmed without evidence.

Within a Phase, run its listed tools in the order they appear in the Phase's own `Do` list
(each tool confirms the check immediately above it). If a tool is unavailable in the current
environment, record the affected checks as `Needs Confirmation` (per `skills/DESIGN.md`
Shared Vocabulary) and continue with the remaining checks — do not stop the review.

---

## Phase 1: Scope and Intake

Identify the reviewed unit: PR, diff, patch, or a named set of files.

Do:
- determine the diff boundary (`git diff <base>...<head>` or the stated file list)
- identify the change's stated intent (PR description, commit message, or user request)
- identify out-of-scope files per `skills/DESIGN.md` Out-of-scope paths (generated code, vendored code, build outputs)

**Completed when**: the diff boundary and stated intent are both recorded.
**Stop and ask the user before Phase 2 when**: no diff boundary can be determined (no PR,
diff, or file list is identifiable) — there is nothing to review. Every later Phase's
"tool unavailable" case (see Toolchain above) is handled by recording `Needs Confirmation`
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

Run this phase only when the user requests issue conversion; otherwise Phase 9's report is
the final output. Three sub-steps, applied in order: group findings (10a), draft each issue
(10b), then check for sensitive content (10c). Delegate the actual issue authoring to
`skills/issue-creator/SKILL.md`, which owns the grouping/splitting criteria and the field
list — this phase only decides which findings feed it.

### Step 10a: Group findings into issues

Use one issue per actionable task; group findings only when they meet
`skills/issue-creator/workflow.md` Phase 2's "Group tasks into one issue only when" criteria
(e.g. same file, must be tested together) — otherwise split them.

### Step 10b: Draft each issue

Include reason for change, implementation intent, acceptance criteria, out of scope, and
testing expectations, per `skills/issue-creator/SKILL.md` Issue Structure.

### Step 10c: Check for sensitive content

Avoid Markdown that breaks when copied (see `skills/issue-creator/workflow.md` Step 9b
Markdown safety rules). Do not include secrets or unnecessary code blocks.

**Completed when**: every grouped finding from 10a has a drafted issue from 10b that has
passed the 10c check.
