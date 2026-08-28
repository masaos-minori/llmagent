---
name: python-documentation
description: |
  Use this skill proactively whenever writing or modifying Python documentation from an existing Python repository.
---

# Python Documentation Skill

## When to use

Use this skill only for documenting an existing Python repository from actual code, configuration, tests, and CI/CD.

Use it when the task is to:
- review docs against implementation,
- update design/operational docs from verified behavior,
- document public interfaces and runtime behavior,
- correct doc/code mismatches,
- reduce stale implementation-derived detail in docs.

## When not to use

Do not use this skill for:
- speculative or design-first documentation,
- non-Python targets,
- new code or architecture design,
- marketing or end-user content,
- documentation not verified from implementation,
- rewriting docs without reading the existing document first.

---

## Documentation Language

See `skills/DESIGN.md` Output language.

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

See `workflow.md` for per-phase tool guidance, lint tools, evidence rules, boundaries, and gates.

---

## Core Documentation Rules

- **Source of truth**: code, configuration, tests, and CI/CD are factual evidence; documentation describes intent, boundaries, constraints, and known issues, not a copy of implementation detail.
- **Evidence first**: use the evidence labels defined in `skills/DESIGN.md` Shared Vocabulary (Evidence labels).
- **No hallucination**: missing behavior or framework patterns MUST NOT be invented without evidence — see `skills/DESIGN.md` Evidence labels for how to mark unclear behavior.
- **Remove or compress implementation-derived details**: see `skills/DESIGN.md` Avoid implementation-reference duplication.
- **No line numbers, no config values, no counts**: see `skills/DESIGN.md` No source-code line numbers, No concrete configuration values, No implementation counts.
- **Minimal diff**: fix errors, fill gaps, reduce duplication; documents MUST NOT be rewritten or reorganized unless the task explicitly asks for it.
- **Respect boundaries**: MUST NOT expand scope, expose secrets, paste long code blocks, infer behavior from `requirements.txt` alone, trust README claims unverified, or document private members as public API.

See `workflow.md` for the full rule set and evidence-tracking fields.

---

## Dependency Management

This skill MUST stay package-manager-neutral. For any Python dependency-management system
encountered, the skill MUST:

- identify the authoritative source of direct dependency declarations (e.g. `pyproject.toml`)
- identify the lockfile or other source of resolved dependencies (e.g. `uv.lock`)
- determine whether `requirements.txt` is authoritative, manually maintained, generated, or unused
- never assume `requirements.txt` exists or is required
- never treat a lockfile as design documentation
- avoid copying complete dependency lists, exact resolved versions, or dependency counts into
  documentation
- verify the actual dependency workflow from CI/CD, container definitions, build scripts, and
  contributor instructions

### Example: uv-managed repositories

Treat the following as repository-specific evidence to verify, not as a package-manager rule to
assume for other repositories:

- `pyproject.toml` is the likely direct dependency declaration source
- `uv.lock` is the likely resolved dependency record
- verify this relationship from the repository before documenting it
- do not conclude that CI/CD or production uses uv only because `uv.lock` exists

See `workflow.md` Evidence and Source of Truth, and Boundaries, for the full dependency-evidence
rule set.

---

## Composes with

- `issue-to-plan` — document existing architecture during planning phase
- `python-implementation` — document new modules or changed interfaces after implementation

## Called by

- `issue-to-plan` — when a plan needs documentation analysis of an existing codebase
- `python-implementation` — when Phase 12 requires documentation updates
- `code-implementation` — Step 5, only when a changed file has a matching
  `docs/00_index.md` task-scope row

---

## Final Rule

You are not writing plausible documentation — you are producing traceable, maintainable
documentation from real Python code, configuration, tests, and CI/CD evidence.

When in doubt, prioritize: correctness, evidence, traceability, maintainability, readability.
