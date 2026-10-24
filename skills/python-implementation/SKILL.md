---
name: python-implementation
description: |
  Use this skill proactively whenever implementing or modifying Python code.
  Apply it to feature development, business logic changes, module creation,
  production code updates, and refactoring that changes implementation behavior.
---

# Python Implementation Skill

## When to use

- adding features, changing business logic, creating new Python modules
- modifying existing production Python code
- refactoring that changes implementation details
- extending existing interfaces or behaviors
- integrating with repository-specific conventions

Use this skill by default for production Python work.

## When not to use

- documentation-only or configuration-only work with no code change
- structural refactoring with no behavior change — see `routing.md` Task → skill
  mapping (Refactor / rename / CST row); if Phase 1 classifies the task that way, stop
  and hand it to `python-refactoring`

---

## Phase overview

| Phase | Name | Goal |
|---|---|---|
| 1 | Task Classification | task type (structural-only refactors go to `python-refactoring`); interface / runtime / security impact |
| 2 | Repository Intelligence | modules, entry points, tests, downstream dependencies, blast radius (`rules/toolchain.md` Impact-radius check) |
| 3 | Architecture Boundary Analysis | layer boundaries, dependency direction violations |
| 4 | Convention Extraction | naming, typing (PEP 484/526), error handling, logging helpers, test style |
| 5 | Semantic Safe Modification | smallest change (see `workflow.md` Phase 5 Step 5c "keep diffs small and intentional"); preserve unrelated behavior; Step 5e adds the tests for the change (delegated to `python-test-and-fix`) |
| 6 | Runtime Contract Validation | request/response contracts, MCP endpoint compatibility (MCP changes only; isolated instance only, never a live service) |
| 7 | Observability Injection | structured logging via the repository's `fmt_kvlog` helper and `logging`; tracing only through the existing optional `shared/otel_tracer.py` (skip unless the task needs it) |
| 8 | Security Validation | Apply `skills/DESIGN.md` Pythonic safety constraints (dynamic execution); `bandit`; manual check of SQL string building and unvalidated deserialization where `bandit` cannot see |
| 9 | Validation Orchestration | After the production-isolation check, run `pytest`, `ruff check`, `mypy`/`pyright`, `lint-imports`, the project gates (`tools/run_validation_gates.py`), `tools/check_compat_shims.py`, and `pre-commit`; separate task-caused from pre-existing failures |
| 10 | Scope Control | diff proportional to task; Per `rules/toolchain.md` §7 (Diff-scoped coverage); benchmark only on hot paths |
| 11 | Production Readiness | Apply `skills/DESIGN.md` Pythonic safety constraints (no placeholders, no debug artifacts); strict typing; docstrings updated for non-obvious or public-facing APIs only (PEP 257) |
| 12 | Knowledge Compression | report documentation needs; edit docs only when the task requires it or the user asks (then via `python-documentation` and the docs checkers) |

See `workflow.md` for phase details, commands, and tools.

---

## Fast path

Use only for small, self-contained bug fixes satisfying ALL of:
- ≤ 2 source files changed (a reproducing test does not count)
- no public or runtime-facing interface change
- no architecture boundary change: no import statement added, removed, or moved (this is checkable without Phase 3; if any import changes, leave the Fast path and run Phase 3)
- no MCP endpoint change
- no performance benchmarking needed

Run phases: 1 → 2 → 4 → 5 (including Step 5e, the reproducing test) → 8 → 9 → 10 (diff-cover only, no benchmark) → 11 → 12. Skip 3, 6, 7, and Phase 10's benchmark.
Even in Fast path, passing `ruff`, `mypy/pyright`, and the tests in Phase 9 is mandatory, as is the Phase 10 diff-cover threshold.

---

## Core implementation rules

### Code Correctness & Architecture
- Prefer existing repository patterns over new local inventions
- Prefer typed, explicit, maintainable code
- Prefer small, reviewable diffs
- Scope discipline: see `AGENTS.md` Global Rule 5.
- When a requirement is uncertain, inspect the repository (Phase 2) before writing code —
  uncertainty is a signal to investigate, not approval of any interpretation
- Extract naming, typing, and error-handling conventions from nearby code (Phase 4); MUST NOT
  assume a convention applies
- Treat the task as complete only after Phase 9 validation (`pytest`, `ruff`, `mypy`, plus
  the other Phase 9 gates) passes
- Compatibility policy: keep the existing public interface working unless the task
  allows changing it, but do not add compatibility shims, aliases, or dead re-exports to do
  so — when an interface changes, update every caller in the same change
  (`tools/check_compat_shims.py` fails on leftovers)
- Out-of-scope paths: see `skills/DESIGN.md` Out-of-scope paths.

### Pythonic Code Quality & Safety Constraints
See `skills/DESIGN.md` Pythonic safety constraints (mutable defaults, exception handling,
typed data, resource management, dynamic execution, async safety) — apply in full.

### Code Comments
Write a comment only for a non-obvious WHY (a hidden constraint, a workaround's reason, or
surprising behavior) that cannot be recovered by reading the code. MUST NOT write:
- WHAT the code does (e.g. `# get the user ID`)
- change history (e.g. "added X", "previously implemented as Y")
- task/ticket ID references (e.g. `(UZU-XXXX)`)

### Production Readiness
See `skills/DESIGN.md` Pythonic safety constraints (no placeholders, no debug artifacts) —
apply before moving to Phase 11.

---

## Composition rules

- `python-lint-typecheck` — Phase 9 reveals lint/type errors (task-caused: fix; pre-existing: record)
- `python-test-and-fix` — Step 5e writes the tests for the change (bug: Path A; new feature: Path B); also Phase 9 test failures
- `python-refactoring` — Phase 1 classifies the task as structure-only
- `python-documentation` — Phase 12 when documentation must change (task requires it or the user asks)
- `python-code-review` — optional self-review of the diff after Phase 11 when the user asks
- `mcp-server-add` — Phase 11 when a new MCP server was added
- `git-commit-and-sync` — to stage, commit, and push on request; this skill never commits on its own
- `deploy` — after Phase 11 if `scripts/` or `config/` changed
- `issue-to-plan` — if implementation starts from an approved plan in `plans/`, verify scope against the plan before Phase 5
- `code-implementation` — calls this skill in its Step 3 (Implement the feature) when executing an approved implementation procedure from `implementations/*.md`; verify scope against that procedure document, not just the Plan, before Phase 5

---

## Improvement feedback

After using this skill:
- if a phase was unnecessary, update the mandatory or skip conditions
- if a needed step was missing, add it
- if the fast path was too broad or too narrow, refine its conditions

Update phase definitions here and detailed procedures in `workflow.md` as needed.
