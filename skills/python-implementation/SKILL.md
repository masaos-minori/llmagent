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

Implement Python code consistently and safely; follow project conventions before introducing new patterns; prefer small, verifiable changes.

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

## Composes with

- `python-lint-typecheck` — run if Phase 9 reveals lint/type errors not caused by the task
- `python-test-and-fix` — run if Phase 9 reveals test failures not caused by the task
- `deploy` — run after Phase 11 if scripts/ or config/ files changed

## Improvement feedback

After running this skill, if a phase was unnecessary or a step was missing:
update the Mandatory/Skip columns in the phase overview table above.
