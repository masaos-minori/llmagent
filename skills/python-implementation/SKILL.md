---
name: python-implementation
description: |
  Use this skill PROACTIVELY when implementing or modifying Python code.
  Covers: architecture enforcement, dependency impact analysis, semantic refactor safety,
  repository convention extraction, runtime contract validation, operational observability,
  security validation, scope control, and repository knowledge compression.
  Apply when adding features, changing business logic, creating modules, refactoring,
  or writing production Python code.
---

# Python Implementation Skill

## Purpose

Implement Python code consistently and safely according to the project's conventions,
using the full toolchain to enforce architecture, security, and observability at every step.

## Primary goals

- produce readable, maintainable Python code
- preserve existing architecture and public interfaces unless explicitly asked to change them
- follow project conventions before introducing new patterns
- minimize unnecessary churn in unrelated files
- prefer small, verifiable changes over large speculative rewrites

---

## Toolchain

| Tool | Phase | Role |
|---|---|---|
| `rg` | Repository Intelligence | Search for patterns, call sites, symbol definitions |
| `ast-grep` | Repository Intelligence | Structural code search: find usages, classes, exceptions by shape |
| `pydeps` | Repository Intelligence | Visualize import graphs; assess blast radius |
| `git` | Repository Intelligence | Review history; stage selectively |
| `import-linter` | Architecture Boundary Analysis | Enforce module boundary rules |
| `libcst` | Semantic Safe Modification | CST-based code transforms |
| `pydantic` | Runtime Contract Validation | Define and validate data models |
| `schemathesis` | Runtime Contract Validation | Property-based HTTP API contract testing |
| `structlog` | Observability Injection | Structured log context |
| `opentelemetry-api` / `-sdk` | Observability Injection | Structured tracing for production code paths |
| `bandit` | Security Validation | Static security analysis |
| `ruff` | Validation Orchestration | Format and lint |
| `mypy` | Validation Orchestration | Type check |
| `pytest` | Validation Orchestration | Behavior verification |
| `pre-commit` | Validation Orchestration | Final gate |
| `diff-cover` | Scope Control | Coverage scoped to changed lines |
| `pytest-benchmark` | Scope Control | Performance regression guard |

---

## Phase overview

| Phase | Name | Mandatory | Skip when |
|---|---|---|---|
| 1 | Task Classification | yes | — |
| 2 | Repository Intelligence | yes | — |
| 3 | Architecture Boundary Analysis | yes | — |
| 4 | Convention Extraction | yes | — |
| 5 | Semantic Safe Modification | yes | — |
| 6 | Runtime Contract Validation | MCP changes only | Task does not touch MCP endpoints |
| 7 | Observability Injection | no | Not yet adopted project-wide; skip unless explicitly requested |
| 8 | Security Validation | yes, if file I/O / subprocess / SQL changed | Pure business logic changes only |
| 9 | Validation Orchestration | yes | — |
| 10 | Scope Control | diff-cover: yes; benchmark: optional | Benchmark: only for known hot paths |
| 11 | Production Readiness | yes | — |
| 12 | Knowledge Compression | yes | — |

**Fast path** — for small, self-contained bug fixes (≤ 2 files, no interface change):
skip Phases 3, 6, 7, 10 (benchmark); run 1, 2, 4, 5, 8, 9, 11, 12.

---

See `workflow.md` for detailed phase content.
See `rules/coding.md` for prohibited behavior and conventions.
See `rules/toolchain.md` for the standard validation sequence.

## Composes with

- `python-lint-typecheck` — run if Phase 9 reveals lint/type errors not caused by the task
- `python-test-and-fix` — run if Phase 9 reveals test failures not caused by the task
- `deploy` — run after Phase 11 if scripts/ or config/ files changed

## Improvement feedback

After running this skill, if a phase was unnecessary or a step was missing:
update the Mandatory/Skip columns in the phase overview table above.
