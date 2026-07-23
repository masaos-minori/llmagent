---
name: python-documentation
description: |
  Use this skill proactively whenever writing or modifying Python documentation from an existing Python repository.
---

# Python Documentation Skill

## When to use

Use this skill only for documenting an existing Python repository from actual code, configuration files, tests, and CI/CD.

Use it when the task is to:
- review existing documentation against implementation,
- update design or operational documentation from verified behavior,
- document public interfaces and runtime behavior,
- correct documentation/code mismatches,
- reduce stale implementation-derived details in documentation.

## When not to use

Do not use this skill for:
- speculative or design-first documentation,
- non-Python targets,
- new code or architecture design,
- marketing or end-user content,
- documentation not verified from implementation,
- rewriting documentation without reading the existing document first.

---

## Documentation Language

Write design documentation in Japanese unless the target repository explicitly requires another language.

Keep file names, symbols, commands, configuration keys, and evidence labels in their original form.

---

## Phase overview

| Phase | Name | Goal |
|---|---|---|
| 1 | Scope | Fix target scope before analysis starts |
| 2 | Inventory | Build a repository map before writing anything |
| 3 | Runtime and Entrypoints | Find how the system is installed, started, and tested |
| 4 | Architecture | Explain package responsibilities, ownership boundaries, and dependency flow |
| 5 | Interfaces | Describe user-facing or system-facing public interfaces |
| 6 | Configuration and Operations | Document how behavior is controlled at runtime and what changes affect operation |
| 7 | Quality and Delivery | Document how the code is verified and delivered |
| 8 | Write Docs | Convert analysis into maintainable documentation |
| 9 | Consistency Review | Remove contradictions across docs and code |
| 10 | Final Report | Return results in a strict final format |

See `workflow.md` for per-phase tool guidance, the project lint tools, evidence rules,
boundaries, and detailed gates.

---

## Core Documentation Rules (Strictly Enforced for AI)

- **Source of truth**: code, configuration, tests, and CI/CD are factual evidence; documentation describes intent, boundaries, constraints, and known issues, not a copy of implementation detail.
- **Evidence first**: use the repository's existing evidence labels (`Explicit in code`, `Needs confirmation`, etc.); do not introduce a parallel label system.
- **No hallucination**: do not invent missing behavior or assume framework patterns without evidence; mark unclear behavior `Needs confirmation` instead of stating it as fact.
- **Remove or compress implementation-derived details**: do not copy file lists, full method/field/config-key tables, or JSON examples that mirror schema fields — replace with a concise source reference.
- **Minimal diff**: fix errors, fill gaps, reduce duplication; do not rewrite or reorganize documents unless the task explicitly asks for it.
- **Respect boundaries**: do not expand scope, expose secrets, paste long code blocks, infer behavior from `requirements.txt` alone, trust README claims unverified, or document private members as public API.

See `workflow.md` for the full rule set and evidence-tracking fields.

---

## Composes with

- `python-issue-to-plan` — document existing architecture during planning phase
- `python-implementation` — document new modules or changed interfaces after implementation

## Called by

- `python-issue-to-plan` — when a plan needs documentation analysis of an existing codebase
- `python-implementation` — when Phase 12 requires documentation updates

---

## Final Rule

You are not writing plausible documentation.

You are producing traceable, maintainable documentation from real Python code, configuration,
tests, and CI/CD evidence.

When in doubt, prioritize: correctness, evidence, traceability, maintainability, readability.
