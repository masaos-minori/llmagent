---
name: python-documentation
description: |
  Use this skill proactively whenever writing or modifying Python documentation.
---

# Python Documentation Skill

## When to use
Use this skill only for documenting an existing Python repository from actual code, config, tests, and CI/CD.

---

## Toolchain

| Tool | Primary phases | Role |
|---|---|---|
| `Bash` (`find`, `ls`, `grep`) | 1 Scope – 7 Quality | discover structure; cross-search symbols, config, patterns |
| `Read` | 2 Inventory – 9 Consistency | read individual files in detail |
| `Agent` (Explore) | 2 Inventory, 4 Architecture | broad search when 3+ queries are needed |
| `Write` | 8 Write Docs | create new documentation files |
| `Edit` | 8 Write Docs, 9 Consistency | apply minimal-diff updates to existing docs |
| `WebFetch` | 3 Runtime, 6 Config | fetch external library docs (only when necessary) |

## Phase overview

| Phase | Name | Goal |
|-------|------|------|
| 1 | Scope | fix target scope before analysis starts |
| 2 | Inventory | build a repository map before writing anything |
| 3 | Runtime and Entrypoints | find how the system is installed, started, and tested |
| 4 | Architecture | explain package responsibilities and dependency flow |
| 5 | Interfaces | describe what is exposed to users or other systems |
| 6 | Configuration and Operations | document how behavior is controlled at runtime |
| 7 | Quality and Delivery | document how the code is verified and delivered |
| 8 | Write Docs | convert analysis into maintainable documentation |
| 9 | Consistency Review | remove contradictions across docs and code |
| 10 | Final Report | return results in a strict final format |

See `workflow.md` for per-phase tool guidance and detailed gates.

## When not to use
Do not use this skill for:
- speculative or design-first documentation
- non-Python targets
- new code or architecture design
- marketing or end-user content
- anything not verified from implementation

---

## Rules

### 1. Source of Truth
- Code and config files are the source of truth; docs are supporting references.
- If docs and code conflict, code wins.

### 2. Evidence First
- Every important statement must include file-path evidence (module, class, function, route, config key, env var).
- Do not make unsupported claims.

### 3. No Hallucination
- Do not invent missing behavior.
- Do not assume framework patterns without evidence.
- Do not treat dead code, unused code, or dead migrations as active behavior.

### 4. Explicit Uncertainty
Label every claim: `Confirmed` (directly verified), `Inferred` (strongly supported), or `Unknown` (cannot be confirmed).

### 5. Minimal Diff
- Fix errors, fill gaps, reduce duplication. Do not rewrite unnecessarily.

### 6. Boundaries
- Do not expand scope beyond the requested target.
- Do not expose secrets.
- Do not paste long code blocks unless essential.
- Do not infer runtime behavior from `requirements.txt` alone.
- Do not trust README claims without verification.
- Do not document private methods or private functions (names starting with `_`).

### 7. Track Evidence
During analysis, track for each item: path, kind, why_it_matters, confirmed_facts, open_questions.

---

## Before Writing

### 1. Inventory First
Identify: main directories, Python packages, config files, entrypoints, public interfaces, test structure, CI/CD and Docker presence.

### 2. Read in Order
README → `pyproject.toml` / `setup.*` → entrypoints → route/command registration → config loading → services/domain/models → repositories/DB/integrations → tests → CI/CD/Docker/migrations.

---

## Composes with

- `python-issue-to-plan` — document existing architecture during planning phase
- `python-implementation` — document new modules or changed interfaces after implementation

## Called by

- `python-issue-to-plan` — when a plan needs documentation analysis of existing codebase
- `python-implementation` — when Phase 12 (Knowledge Compression) requires doc updates

---

## Final Rule
You are not writing plausible documentation.
You are producing traceable documentation from real Python code.

When in doubt, prioritize:

1. correctness
2. evidence
3. traceability
4. maintainability
5. readability
