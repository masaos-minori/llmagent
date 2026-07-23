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

Do not use it for speculative or design-first documentation.

---

## Documentation Language

Write design documentation in Japanese unless the target repository explicitly requires another language.

Keep file names, symbols, commands, configuration keys, and evidence labels in their original form.

---

## Toolchain

| Tool | Primary phases | Role |
|---|---|---|
| `Bash` (`find`, `ls`, `grep`) | 1 Scope – 7 Quality | Discover structure; cross-search symbols, configuration, and patterns |
| `Read` | 2 Inventory – 9 Consistency | Read individual files in detail |
| `Agent` (Explore) | 2 Inventory, 4 Architecture | Broad search when three or more independent queries are needed |
| `Write` | 8 Write Docs | Create new documentation files when necessary |
| `Edit` | 8 Write Docs, 9 Consistency | Apply minimal-diff updates to existing documentation |
| `WebFetch` | 3 Runtime, 6 Config | Fetch external library documentation only when necessary |

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

See `workflow.md` for per-phase tool guidance and detailed gates.

---

## Project lint tools

Run these when modifying `docs/`.

| Tool | Target | When to run |
|---|---|---|
| `python tools/check_docs_consistency.py` | `docs/*.md` | After documentation consistency-sensitive changes |
| `python tools/check_mcp_docs_consistency.py` | `docs/04_mcp_*.md` | After MCP documentation changes |
| `python tools/gen_rag_reference.py` | RAG reference documentation | Needs confirmation before use; verify the current output target before running |

Note: Do not run `python tools/gen_rag_reference.py` blindly. The configured output target may refer to an old split-document path. Verify the current target before use.

---

## When not to use

Do not use this skill for:
- speculative or design-first documentation,
- non-Python targets,
- new code or architecture design,
- marketing or end-user content,
- documentation not verified from implementation,
- rewriting documentation without reading the existing document first.

---

## Rules

### 1. Source of Truth and Documentation Role

Code, configuration files, tests, and CI/CD are factual evidence for implemented behavior.

Documentation should describe:
- design intent,
- responsibility boundaries,
- architectural constraints,
- operational notes,
- failure behavior,
- confirmed behavior,
- known issues,
- unresolved questions.

When code and documentation conflict:
- update documentation if the implemented behavior is clearly correct and current,
- register or update a Known Issue if the conflict cannot be resolved immediately,
- mark the item as Needs confirmation if the implementation may be incomplete, buggy, provisional, or ambiguous,
- do not silently replace documented design intent with possibly buggy behavior.

### 2. Evidence First

Important behavioral claims must be traceable to evidence.

Use evidence for:
- public behavior,
- configuration ownership,
- runtime entrypoints,
- failure behavior,
- operational constraints,
- security-sensitive behavior,
- persistence or migration behavior,
- documentation/code mismatch corrections.

Do not add evidence labels to every sentence.

### 3. Use Existing Evidence Labels

Use the repository's established evidence labels:

- `Explicit in code`
- `Strongly implied by code`
- `Documentation only`
- `Needs confirmation`
- `Deprecated`
- `Verified by test`
- `Operationally observed`

Do not introduce a parallel label system such as `Confirmed`, `Inferred`, or `Unknown`.

When using `Needs confirmation`, include the required fields defined by the governance documentation.

### 4. No Hallucination

Do not invent missing behavior.

Do not assume framework patterns without evidence.

Do not treat dead code, unused code, stale migrations, or obsolete documentation as active behavior.

If behavior cannot be confirmed, mark it as Needs confirmation instead of presenting it as fact.

### 5. Remove or Compress Implementation-derived Details

Design documentation should not copy details that can be mechanically confirmed from source code, command help, configuration files, or generated schemas.

Normally remove, compress, or replace with source references:
- complete file lists,
- complete public method lists,
- full function signatures,
- constructor parameter tables,
- public attribute tables,
- TypedDict, dataclass, DTO, and Pydantic model full field listings,
- complete CLI argument tables,
- complete configuration key tables,
- JSON examples that simply mirror DTO or schema fields,
- import lists,
- module-level constant listings.

Keep:
- design intent,
- responsibility boundaries,
- architectural constraints,
- non-negotiable invariants,
- failure behavior,
- fail-fast and fail-open behavior,
- security constraints,
- operational constraints,
- data consistency rules,
- Known Issues,
- Needs Confirmation items,
- deprecated behavior relevant to migration or compatibility,
- behavior verified by tests,
- operationally observed behavior.

### 6. Minimal Diff

Fix errors, fill gaps, reduce duplication, and improve clarity.

Do not rewrite unnecessarily.

Do not reorganize documents broadly unless the task explicitly asks for it.

### 7. Boundaries

Do not expand scope beyond the requested target.

Do not expose secrets.

Do not paste long code blocks unless essential.

Do not infer runtime behavior from `requirements.txt` alone.

Do not trust README claims without verification.

Do not document private methods, private functions, private attributes, or private classes as supported public APIs.

Private names starting with `_` are out of scope unless they are necessary to explain lifecycle, safety, failure behavior, or an invariant. In that case, describe the behavior at component level instead of exposing the private API as public.

Files under `__pycache__` are out of scope.

### 8. Track Evidence During Analysis

During analysis, track for each meaningful item:

- path,
- kind,
- why_it_matters,
- confirmed_facts,
- evidence_label,
- open_questions,
- target_document.

---

## Before Writing

### 1. Inventory First

Identify:
- main directories,
- Python packages,
- configuration files,
- entrypoints,
- public interfaces,
- test structure,
- CI/CD files,
- Docker or deployment assets,
- migration files if relevant.

### 2. Read in Order

Read in this order unless the task scope requires otherwise:

1. existing target documentation,
2. `README` or project overview,
3. `pyproject.toml` / `setup.*`,
4. entrypoints,
5. route or command registration,
6. configuration loading,
7. services, domain models, and repositories,
8. integrations and DB access,
9. tests,
10. CI/CD, Docker, deployment, and migrations.

Do not write documentation before reading the existing target document.

---

## Writing Guidance

When updating design documentation:

- preserve useful existing context,
- prefer Japanese prose for design text,
- avoid full implementation reference tables,
- keep important invariants explicit,
- separate current behavior from design intent where useful,
- move unresolved uncertainty to Needs Confirmation,
- move unresolved conflicts to Known Issues,
- keep changes small and reviewable.

When removing implementation-derived content, replace it with concise source references where necessary.

Example:

- 完全な設定キーとデフォルト値は、実装上の設定定義および実際の設定ファイルを参照する。
- この設計書では、設定の所有者、変更時の影響、再起動要否、失敗時の挙動、運用上の注意のみを扱う。

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

You are producing traceable, maintainable documentation from real Python code, configuration, tests, and CI/CD evidence.

When in doubt, prioritize:

1. correctness
2. evidence
3. traceability
4. maintainability
5. readability
