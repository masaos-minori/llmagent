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

MUST NOT use this skill for:
- speculative or design-first documentation,
- non-Python targets,
- new code or architecture design,
- marketing or end-user content,
- documentation not verified from implementation,
- rewriting docs without reading the existing document first,
- revising the procedure itself of a `skills/*.md`, `rules/*.md`, or `prompts/*.md` file (correcting a step, adding a missing branch): that is a workflow edit, not documentation of code behavior — see `routing.md` "Documentation row exception". The skill still applies to a `skills/*.md` edit that documents actual code behavior and to any `docs/*.md` edit.

---

## Documentation Language

See `skills/DESIGN.md` Output language. The documents written or edited are English. The Phase 10
Final Report is chat output: write it in the conversation language (`AGENTS.md` Role), keeping
file names, symbols, commands, and evidence labels untranslated.

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

See `workflow.md` for per-phase tool guidance, lint tools, evidence rules, boundaries, and gates. Phase 1 chooses a scoped or full mode (`workflow.md` Mode): a scoped update of named sections skips Phases 3, 6, and 7. Phase 9 runs the docs checkers from `routing.md`, and Phase 8c registers Known Issues and Needs confirmation items in the governance inventory.

---

## Core Documentation Rules

- **Source of truth**: code, configuration, tests, and CI/CD are factual evidence; documentation describes intent, boundaries, constraints, and known issues, not a copy of implementation detail.
- **Evidence first**: use the evidence labels defined in `skills/DESIGN.md` Shared Vocabulary (Evidence labels).
- **No hallucination**: missing behavior or framework patterns MUST NOT be invented without evidence — see `skills/DESIGN.md` Evidence labels for how to mark unclear behavior.
- **Remove or compress implementation-derived details**: see `skills/DESIGN.md` Avoid implementation-reference duplication.
- **No line numbers, no config values, no counts**: see `skills/DESIGN.md` No source-code line numbers, No concrete configuration values, No implementation counts.
- **Docs content policy**: remove implementation-detail content and retain design-intent content per `skills/DESIGN.md` Docs content policy — remove, Docs content policy — retain.
- **Minimal diff**: fix errors, fill gaps, reduce duplication — see `AGENTS.md`, section "Global Rule 5" (no unrelated rewrite).
- **Respect boundaries**: MUST NOT expand scope, expose secrets (see `skills/DESIGN.md` No secrets in output), paste long code blocks, infer behavior from `requirements.txt` alone, trust claims in any overview document (a README, if one exists, or `docs/00_index.md`) unverified (verify against the actual code or config the document describes instead), or document private members as public API.

See `workflow.md` for the full rule set and evidence-tracking fields.

---

## Dependency Management

Applies only when the document being written or edited describes dependencies, installation, runtime, or delivery (in either mode; `workflow.md` Mode). A design-intent document that does not (for example one on component responsibilities) skips this section and the dependency items of Phases 2, 3, 6, 7, and 9. This skill MUST stay package-manager-neutral. For any Python dependency-management system
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

Repository-specific evidence to verify, not a rule for other repositories:

- `pyproject.toml` is the likely direct dependency declaration source
- `uv.lock` is the likely resolved dependency record
- verify this relationship from the repository before documenting it
- MUST NOT conclude that CI/CD or production uses uv only because `uv.lock` exists

See `workflow.md` Evidence and Source of Truth, and Boundaries.

---

## Composes with

- `python-implementation` — document new modules or changed interfaces after implementation
- `git-commit-and-sync` — the written files stay uncommitted; use it to commit and push them on request

## Called by

- `python-implementation` — when its Phase 12 (Knowledge Compression) requires documentation updates
- `code-implementation` — Step 5, only when a changed file has a matching
  `docs/00_index.md` task-scope row
- `python-code-review` — when its Documentation Notes require an update to existing docs
- `python-design` — when a design task reviews or updates existing documentation
- `prompts/08_document-sync.md` — the design-docs refactor workflow (multi-document, see `workflow.md` Multi-file processing)

---

## Final Rule

Produce traceable, maintainable documentation from real Python code, configuration, tests,
and CI/CD evidence, not plausible documentation.

When in doubt, prioritize: correctness, evidence, traceability, maintainability, readability.
