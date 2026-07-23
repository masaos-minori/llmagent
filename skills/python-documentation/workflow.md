# Python Documentation — Detailed Workflow

## Project lint tools

Run these when modifying `docs/`.

| Tool | Target | When to run |
|---|---|---|
| `python tools/check_docs_consistency.py` | `docs/*.md` | After documentation consistency-sensitive changes |
| `python tools/check_mcp_docs_consistency.py` | `docs/04_mcp_*.md` | After MCP documentation changes |
| `python tools/gen_rag_reference.py` | RAG reference documentation | Needs confirmation before use; verify the current output target before running |

Note: Do not run `python tools/gen_rag_reference.py` blindly. The configured output target
may refer to an old split-document path. Verify the current target before use.

---

## Toolchain

| Tool | Phase | Role |
|---|---|---|
| `Bash` (`ls`, `find`) | 1 Scope, 2 Inventory | discover directory layout and identify target files |
| `Bash` (`grep`) | 2 Inventory – 7 Quality | cross-search symbols, import paths, env vars, config keys |
| `Read` | 2 Inventory – 9 Consistency | read individual files in full detail |
| `Agent` (Explore) | 2 Inventory, 4 Architecture | broad codebase exploration when 3+ targeted queries are needed |
| `Write` | 8 Write Docs | create new documentation files from scratch |
| `Edit` | 8 Write Docs, 9 Consistency | apply minimal-diff updates to existing documentation |
| `WebFetch` | 3 Runtime, 6 Config | fetch external library or framework docs (only when necessary) |

### Tool selection rules
- Prefer `Bash (grep/find)` + `Read` for targeted lookups before spawning `Agent (Explore)`.
- Spawn `Agent (Explore)` only when the search spans many directories or requires 3+ queries.
- Use `Edit` over `Write` whenever the doc file already exists — preserve existing content.
- `WebFetch` is a last resort; most behavior should be confirmable from the local codebase.

---

## Core Principles
- Observe before writing
- Evidence before summary
- Inventory before interpretation
- Keep unknowns visible
- Prefer minimal edits over full rewrites
- Separate facts from assumptions

---

## Phase 1. Scope
### Goal
Fix the target scope before analysis starts.

### Do
- identify repository root and target paths
- identify exclusions (`.venv`, `__pycache__`, build outputs, generated files, vendor)
- identify expected deliverables
- note whether existing docs should be updated or created

### Gate
- [ ] scope is clear
- [ ] exclusions are clear
- [ ] deliverables are clear

---

## Phase 2. Inventory
### Goal
Build a repository map before writing anything.

### Do
- list major directories and Python packages
- inspect `pyproject.toml`, `setup.cfg`, `setup.py`, `requirements*`
- identify test directories, CI/CD files, Docker files, migration files
- determine whether the repo is an app, service, library, worker, or monorepo

### Output
- repository inventory
- major file list
- packaging/runtime summary

### Read in order

Unless the task scope requires otherwise, read in this order:

1. existing target documentation
2. `README` or project overview
3. `pyproject.toml` / `setup.*`
4. entrypoints
5. route or command registration
6. configuration loading
7. services, domain models, and repositories
8. integrations and DB access
9. tests
10. CI/CD, Docker, deployment, and migrations

Do not write documentation before reading the existing target document.

### Gate
- [ ] package structure is understood
- [ ] packaging files are identified
- [ ] major runtime files are identified

---

## Phase 3. Runtime and Entrypoints
### Goal
Find how the system is installed, started, and tested.

### Do
- determine Python version requirements
- determine install method
- identify entrypoints (`__main__.py`, `main.py`, `app.py`, `manage.py`, console scripts)
- identify API / CLI / worker / scheduler execution paths
- inspect Docker and CI for actual run/test commands

### Gate
- [ ] install path is known
- [ ] minimum startup path is known
- [ ] test path is known
- [ ] external runtime dependencies are visible

---

## Phase 4. Architecture
### Goal
Explain package responsibilities and dependency flow.

### Do
- map package/module responsibilities
- identify service / domain / infra boundaries
- identify DB / ORM / queue / external integrations
- trace important imports and call paths

### Gate
- [ ] major modules are listed
- [ ] responsibilities are clear
- [ ] dependency flow is explainable

---

## Phase 5. Interfaces
### Goal
Describe what is exposed to users or other systems.

### Do
- list HTTP routes
- list CLI commands
- list workers, schedulers, batch jobs, tasks
- identify public library APIs if applicable
- trace major request/job flows

### Gate
- [ ] interfaces are listed
- [ ] key flows are explainable
- [ ] auth / error / external I/O behavior is identified where relevant

---

## Phase 6. Configuration and Operations
### Goal
Document how behavior is controlled at runtime.

### Do
- identify env vars and settings modules
- inspect `.env`, config classes, settings loaders
- identify DB / cache / broker / external service config
- identify logging, retry, timeout, migrations, startup hooks

### Gate
- [ ] important config is listed
- [ ] secrets are not exposed
- [ ] runtime dependencies are documented

---

## Phase 7. Quality and Delivery
### Goal
Document how the code is verified and delivered.

### Do
- inspect tests, fixtures, `conftest.py`, markers
- inspect lint / format / typecheck setup
- inspect CI/CD and pre-commit
- identify build, publish, release, or image creation paths

### Gate
- [ ] test strategy is documented
- [ ] CI/CD is documented
- [ ] quality tools are documented

---

## Phase 8. Write Docs
### Goal
Convert analysis into maintainable documentation.

### Rules
- use evidence-based wording
- keep docs concise and maintainable
- avoid duplication
- do not hide uncertainty
- keep changes minimal if docs already exist
- preserve useful existing context; prefer Japanese prose for design text
- avoid full implementation reference tables
- keep important invariants explicit
- separate current behavior from design intent where useful
- move unresolved uncertainty to Needs Confirmation, and unresolved conflicts to Known Issues
- keep changes small and reviewable

### Remove or compress implementation-derived details

Documentation should not copy details that can be mechanically confirmed from source code,
command help, configuration files, or generated schemas.

Normally remove, compress, or replace with source references:
- complete file lists, complete public method lists, full function signatures
- constructor parameter tables, public attribute tables
- TypedDict, dataclass, DTO, and Pydantic model full field listings
- complete CLI argument tables, complete configuration key tables
- JSON examples that simply mirror DTO or schema fields
- import lists, module-level constant listings

Keep: design intent, responsibility boundaries, architectural constraints, non-negotiable
invariants, failure behavior (fail-fast/fail-open), security and operational constraints,
data consistency rules, Known Issues, Needs Confirmation items, deprecated behavior relevant
to migration/compatibility, behavior verified by tests, operationally observed behavior.

When removing implementation-derived content, replace it with a concise source reference.
Example:

- 完全な設定キーとデフォルト値は、実装上の設定定義および実際の設定ファイルを参照する。
- この設計書では、設定の所有者、変更時の影響、再起動要否、失敗時の挙動、運用上の注意のみを扱う。

### Gate
- [ ] required docs are covered
- [ ] README points to detailed docs
- [ ] unknowns are recorded explicitly

---

## Phase 9. Consistency Review
### Goal
Remove contradictions across docs and code.

### Check
- file names, module names, and commands match implementation
- run/test instructions match config and CI
- inferred content is labeled
- no secrets are included
- no unsupported claims remain

### Gate
- [ ] major inconsistencies are removed
- [ ] docs are traceable back to code

---

## Evidence and Source of Truth

Code, configuration files, tests, and CI/CD are factual evidence for implemented behavior.
Documentation should describe design intent, responsibility boundaries, architectural
constraints, operational notes, failure behavior, confirmed behavior, known issues, and
unresolved questions.

When code and documentation conflict:
- update documentation if the implemented behavior is clearly correct and current
- register or update a Known Issue if the conflict cannot be resolved immediately
- mark the item `Needs confirmation` if the implementation may be incomplete, buggy, provisional, or ambiguous
- do not silently replace documented design intent with possibly buggy behavior

Important behavioral claims must be traceable to evidence: public behavior, configuration
ownership, runtime entrypoints, failure behavior, operational constraints, security-sensitive
behavior, persistence/migration behavior, and documentation/code mismatch corrections. Do not
add evidence labels to every sentence.

Use the repository's established evidence labels: `Explicit in code`, `Strongly implied by code`,
`Documentation only`, `Needs confirmation`, `Deprecated`, `Verified by test`, `Operationally observed`.
Do not introduce a parallel label system such as `Confirmed`, `Inferred`, or `Unknown`. When using
`Needs confirmation`, include the required fields defined by the governance documentation.

Do not invent missing behavior or assume framework patterns without evidence. Do not treat dead
code, unused code, stale migrations, or obsolete documentation as active behavior. If behavior
cannot be confirmed, mark it `Needs confirmation` instead of presenting it as fact.

### Evidence tracking during analysis

During analysis, track for each meaningful item: path, kind, why it matters, confirmed facts,
evidence label, open questions, and target document.

---

## Boundaries

- Do not expand scope beyond the requested target.
- Do not expose secrets.
- Do not paste long code blocks unless essential.
- Do not infer runtime behavior from `requirements.txt` alone.
- Do not trust README claims without verification.
- Do not document private methods, functions, attributes, or classes as supported public APIs.
  Private names starting with `_` are out of scope unless necessary to explain lifecycle,
  safety, failure behavior, or an invariant — in that case, describe the behavior at
  component level instead of exposing the private API as public.
- Files under `__pycache__` are out of scope.

---

## Phase 10. Final Report
### Goal
Return results in a strict final format.

### Final Report Format
#### Updated / Created Files
- files created
- files updated

#### Confirmed Findings
- implementation facts verified from code

#### Inferred Findings
- high-confidence conclusions

#### Open Questions
- unresolved items still needing evidence

#### Next Recommended Deep-Dive
- next modules / packages / paths to inspect

### Final Gate
- [ ] setup-to-start path is understandable
- [ ] entrypoints and dependencies are traceable
- [ ] unknowns remain visible
- [ ] docs do not conflict with implementation

---

## Final Rule
Do not try to sound complete.
Try to be correct, traceable, and maintainable.
