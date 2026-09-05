# Python Documentation — Detailed Workflow

## Project lint tools

See `routing.md` Tools → "When to run which tool" for the checkers to run when modifying
`docs/` — do not hardcode tool names or invocations here; that table is the single source of
truth and is kept in sync with `tools/`.

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
- Apply `skills/DESIGN.md` Agent (Explore) threshold.
- Use `Edit` over `Write` whenever the doc file already exists — preserve existing content.
- `WebFetch` is a last resort; most behavior SHOULD be confirmable from the local codebase.
- Apply `rules/ai-execution.md` Tool Usage's idempotent-command rule: do not re-run the
  same `grep`/`find` query against unchanged files expecting a different result.
- Per `rules/ai-execution.md` Repository Tool Usage #8, a `grep`/`find` command returning
  no matches is not proof that something doesn't exist — record it as `Needs Confirmation`
  (see Boundaries' static-import-search rule below) rather than asserting absence from
  empty output alone.

---

## Multi-file processing

When the current task names more than one target document (directly, or via a caller
such as `prompts/08_document-sync.md` Step 1), apply `rules/ai-execution.md` Sequential
Target Processing (Base): process one document's Phases 1-10 completely (through Phase
10's Final Report) before starting Phase 1 for the next — do not batch-inventory
(Phase 2) or batch-write (Phase 8) several documents before finishing any one of them.
This also prevents two documents processed in the same batch from producing
conflicting Known Issues/Needs Confirmation entries for the same underlying code, since
each document's Phase 9 Consistency Review sees the prior document's completed edits.

## Core Principles
- Observe before writing
- Evidence before summary
- Inventory before interpretation
- Keep unknowns visible
- Minimal diff: see `SKILL.md` "Minimal diff" and `AGENTS.md` Global Rule 5.
- Separate facts from assumptions

## Gate failure handling

Every Phase below ends with a `### Gate` checklist. This rule applies to all of them and is
not repeated per Phase: if any Gate item is unchecked, redo the `### Do` action that item
depends on and re-check only that item (not the full Gate) before starting the next
Phase — do not proceed with a known-unmet Gate item. Per `AGENTS.md` Loop Prevention >
Attempt Limit, at most 3 redo-and-recheck attempts per Gate item; if it still cannot be
checked after 3 attempts, or the missing evidence cannot be obtained (the repository
genuinely does not expose it), record it as an Open Question (Phase 10) instead of
leaving the Gate item silently unchecked or retrying indefinitely.

---

## Phase 1. Scope
### Goal
Fix the target scope before analysis starts.

### Do
- identify repository root and target paths
- identify exclusions per `skills/DESIGN.md` Out-of-scope paths (plus repo-specific generated/vendor files)
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
- inspect `pyproject.toml`, applicable lockfiles (e.g. `uv.lock`), legacy packaging files
  (`setup.py`, `setup.cfg`), and `requirements*` files only when present
- inspect CI/CD, Dockerfiles, build scripts, and contributor instructions for the
  dependency-management commands they actually use
- identify test directories, CI/CD files, Docker files, migration files
- determine whether the repo is an app, service, library, worker, or monorepo
- determine, from the evidence above:
  - the authoritative direct dependency declaration
  - the resolved dependency source
  - generated or exported dependency files
  - development, test, and production dependency boundaries
  - the package manager used by each operational environment (development, CI/CD, containers,
    production)
  - the commands used to update, validate, install, or synchronize dependencies

### Output
- repository inventory
- major file list
- packaging/runtime summary
- dependency-management summary: authoritative declaration source, resolved dependency source,
  generated exports (if any), and per-environment package manager and commands

### Read in order

Read in this order, unless the existing documentation's own table of contents groups
topics in a different order than below — in that case, follow the existing document's
order instead, so review proceeds section-by-section against the doc being updated:

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
- [ ] the authoritative direct dependency declaration and the resolved dependency source are
      identified
- [ ] the package manager and dependency-management commands used by each operational
      environment are identified

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
- verify the actual dependency installation or synchronization path used by development, CI/CD,
  containers, and production; for uv-managed repositories this means inspecting actual uses of
  commands such as `uv sync`, `uv run`, `uv lock`, and lockfile validation options — do not add
  these commands to project documentation unless they are verified in the repository

### Gate
- [ ] install path is known
- [ ] minimum startup path is known
- [ ] test path is known
- [ ] external runtime dependencies are visible
- [ ] a traceable dependency synchronization path is known for each operational environment
- [ ] lockfile validation behavior is known, when a lockfile is used

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
- identify dependency groups and optional dependencies, and how development-only dependencies
  are excluded from production
- identify lockfile ownership and update procedures, and dependency upgrade/validation procedures
- determine whether pip-compatible files (e.g. a generated `requirements.txt`) are generated for
  external systems, and whether such exports are committed to the repository or created during
  build or deployment

### Gate
- [ ] important config is listed
- [ ] secrets are not exposed
- [ ] runtime dependencies are documented
- [ ] dependency-group boundaries, lockfile ownership, and export generation are documented
      (ownership, constraints, and change impact — not complete package lists)

---

## Phase 7. Quality and Delivery
### Goal
Document how the code is verified and delivered.

### Do
- inspect tests, fixtures, `conftest.py`, markers
- inspect lint / format / typecheck setup
- inspect CI/CD and pre-commit
- identify build, publish, release, or image creation paths
- verify consistency checks between dependency declarations and lockfiles
- verify clean-environment dependency synchronization
- verify CI/CD dependency installation commands
- verify vulnerability and license scanning support for the repository's actual dependency format
- if any of the above cannot be confirmed, record the gap as an open question or `Known Issue`;
  do not invent a workflow

### Gate
- [ ] test strategy is documented
- [ ] CI/CD is documented
- [ ] quality tools are documented
- [ ] dependency consistency checks, clean-environment sync, and dependency-related scanning are
      documented or recorded as open questions

---

## Phase 8. Write Docs
### Goal
Convert analysis into maintainable documentation.

This phase has three sub-steps: writing policy (8a), removing implementation-derived
detail (8b), then separating uncertainty (8c).

### Step 8a: Writing policy

- use evidence-based wording; state a claim once and reference it elsewhere rather than
  restating it (see Step 8b for what to drop); avoid duplication
- do not hide uncertainty; keep changes minimal if docs already exist
- preserve useful existing context
- Output language: see `skills/DESIGN.md` §Output language.
- keep changes small and reviewable

**Completed when**: the draft follows the rules above, in whatever order is natural for
the document being written.

### Step 8b: Remove or compress implementation-derived details

Documentation SHOULD NOT copy details mechanically confirmable from source code, command help,
configuration, or generated schemas.

Normally remove, compress, or replace with source references:
- complete file lists, complete public method lists, full function signatures
- constructor parameter tables, public attribute tables
- TypedDict, dataclass, DTO, and Pydantic model full field listings
- complete CLI argument tables, complete configuration key tables, and concrete config values
  (see `skills/DESIGN.md` No concrete configuration values)
- JSON examples that simply mirror DTO or schema fields
- import lists, module-level constant listings
- source-code line numbers (see `skills/DESIGN.md` No source-code line numbers)
- counts of modules, tools, servers, states, fields, tests, or documents
  (see `skills/DESIGN.md` No implementation counts)
- complete direct dependency lists, complete transitive dependency lists, exact lockfile
  contents, dependency-tree output, dependency counts, and generated `requirements.txt`
  contents
- exact resolved dependency versions, unless needed to explain a verified compatibility
  constraint, migration issue, or operational problem
- full ASCII file trees, per-file descriptions embedded in a tree or table,
  class/function/method index tables, implementation-location mappings ("this behavior is
  implemented in `{file}`"), and literal port numbers (see `skills/DESIGN.md` Docs content
  policy — remove)

Keep: design intent, responsibility boundaries, architectural constraints, non-negotiable
invariants, failure behavior (fail-fast/fail-open), security and operational constraints,
data consistency rules, Known Issues, Needs Confirmation items, deprecated behavior relevant
to migration/compatibility, behavior verified by tests, operationally observed behavior,
component responsibility, state ownership, allowed dependency direction, and reasons for
process/configuration separation (see `skills/DESIGN.md` Docs content policy — retain),
the dependency source-of-truth decision, dependency ownership, supported Python-version
constraints when operationally relevant, dependency-group boundaries, lockfile update and
validation policy, compatibility constraints, external export requirements, known dependency
conflicts, and unresolved differences between environments.

Replace removed content with a concise source reference, e.g.:

- Full configuration keys and default values are documented in the implementation's config definitions and actual config files.
- This design document covers only config ownership, change impact, restart requirements, failure behavior, and operational notes.

**Completed when**: none of the "Normally remove" categories above appear in the draft
outside of a "Keep" category or a source reference.

### Step 8c: Separate uncertainty

- keep important invariants explicit; separate current behavior from design intent where useful
- move unresolved uncertainty to Needs Confirmation, unresolved conflicts to Known Issues

**Completed when**: every item identified during Phases 1–7 as uncertain or conflicting
has been placed in Needs Confirmation or Known Issues — none remain stated as plain fact.

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
- direct dependency declarations and lockfiles are consistent with each other
- documented installation commands match CI/CD and container definitions
- generated dependency exports are not described as authoritative sources
- development-only dependencies are not described as production requirements
- lockfile entries are not described as direct application dependencies without supporting
  evidence

When dependency files and operational commands conflict:
- document the currently verified behavior
- preserve documented design intent separately
- record unresolved conflicts as `Known Issues`
- use `Needs Confirmation` when authority or intended behavior cannot be verified

### Gate
- [ ] major inconsistencies are removed
- [ ] docs are traceable back to code
- [ ] dependency declarations, lockfiles, and documented commands are consistent, or conflicts
      are recorded as `Known Issues` / `Needs Confirmation`

---

## Evidence and Source of Truth

Code, configuration, tests, and CI/CD are factual evidence for implemented behavior.
Documentation SHOULD describe design intent, responsibility boundaries, architectural
constraints, operational notes, failure behavior, confirmed behavior, known issues, and
unresolved questions.

When code and documentation conflict:
- update documentation if the implemented behavior is clearly correct and current
- register or update a Known Issue if the conflict cannot be resolved immediately
- mark the item `Needs confirmation` if the implementation may be incomplete, buggy, provisional, or ambiguous
- do not silently replace documented design intent with possibly buggy behavior

Important behavioral claims MUST be traceable to evidence: public behavior, configuration
ownership, runtime entrypoints, failure behavior, operational constraints, security-sensitive
behavior, persistence/migration behavior, and documentation/code mismatch corrections. Do not
add evidence labels to every sentence.

Use the evidence labels defined in `skills/DESIGN.md` Shared Vocabulary. When using
`Needs confirmation`, include the required fields defined by the governance documentation.

Do not invent missing behavior or assume framework patterns without evidence.

### Dependency evidence categories

- **Declared dependency evidence**: project metadata such as `pyproject.toml`.
- **Resolved dependency evidence**: lockfiles such as `uv.lock`.
- **Installed-environment evidence**: verified environment inspection or clean-environment
  synchronization.
- **Operational evidence**: CI/CD, containers, deployment definitions, and build scripts.
- **Compatibility export evidence**: generated files such as `requirements.txt`.

No single dependency file proves all dependency-management claims; a claim about actual
operational behavior (e.g. "CI/CD installs dependencies with X") requires operational evidence,
not only declared or resolved dependency evidence.

### Evidence tracking during analysis

During analysis, track for each meaningful item: path, kind, why it matters, confirmed facts,
evidence label, open questions, and target document.

---

## Boundaries

See `SKILL.md` "Respect boundaries" for scope, secrets, long code blocks, `requirements.txt`
inference, README trust, and private-API documentation boundaries.

- Require `requirements.txt` only when Phase 2's inventory found no other verified
  dependency-management workflow.
- Treat a generated dependency export (e.g. a generated `requirements.txt`) as read-only
  evidence — edit the authoritative declaration or lockfile instead, per Phase 2's findings.
- Leave lockfiles as-is during documentation-only work; regenerate one only when dependency
  maintenance is explicitly in scope for the current task.
- When a static import search finds no reference to a dependency, record it as
  `Needs Confirmation` (see Evidence and Source of Truth) rather than classifying it Unused —
  a static search alone cannot confirm dynamic or optional usage.
- Base a "direct usage" or "production inclusion" claim on Phase 2's declared/operational
  evidence categories, not on lockfile membership alone.
- Change dependency declarations only when the task's scope explicitly includes dependency
  maintenance — never merely to simplify documentation.
- Out-of-scope paths: see `skills/DESIGN.md` Out-of-scope paths.

---

## Phase 10. Final Report
### Goal
Return results in a strict final format.

**This documentation task is complete when, and only when**: the Final Gate below is
fully checked (or its unmet items are recorded as Open Questions per Gate failure
handling's Attempt Limit), and every section of the Final Report Format is populated
from what Phases 1-9 already recorded — do not re-derive or re-run a check merely to
produce this report.

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

Cross-check against each Phase's gate stated above — do not re-derive them, just confirm:

- [ ] Phase 3 gate met: setup-to-start path is traceable
- [ ] Phase 4 gate met: entrypoints and dependencies are traceable
- [ ] Phase 8 gate met: unknowns remain visible
- [ ] Phase 9 gate met: docs do not conflict with implementation

---

## Final Rule
Do not try to sound complete.
Try to be correct, traceable, and maintainable.
