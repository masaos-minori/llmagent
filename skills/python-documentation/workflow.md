# Python Documentation — Detailed Workflow

## Project lint tools

See `routing.md` Tools → "When to run which tool" for the checkers to run when modifying
`docs/`. MUST NOT hardcode tool names or invocations here. Phase 9 requires running them.

## Repository documentation conventions

A document under `docs/` follows `docs/00_governance/governance_00_document-guide.md`, which
routes to the policy (`governance_01`), metadata conventions (`governance_02`), issue and
uncertainty management (`governance_03`), and the documentation checks (`governance_04`).
Read only the governance documents for the area being edited (`AGENTS.md` Global Rule 1).
In short: English only (`skills/DESIGN.md` Output language), YAML Front Matter and a Keywords
section, and the heading, table, and code-fence rules the docs checkers enforce. A rename or
move uses `tools/rename_doc.py` (dry-run first), not manual edits.

## Dependency topics are conditional

The dependency-management items in Phases 2, 3, 6, 7, and 9, the dependency categories under
Evidence and Source of Truth, and the dependency bullets in Boundaries apply only under the
condition in `SKILL.md` Dependency Management. Otherwise skip them; their Gate items are
`N/A: no dependency content`. This applies in both modes below.

## Mode: scoped or full

Decide in Phase 1 and record it in the Final Report.

- **Scoped**: the task edits only sections of an existing document that describe named code,
  for example a `code-implementation` Step 5 call for changed files matched by a
  `docs/00_index.md` row, or a request that names a section or file. Run Phase 1; Phase 2
  limited to the existing document, the named code, and the files the section cites; Phases 4
  and 5 for the named area only; then Phases 8, 9, and 10. Skip Phases 3, 6, and 7 (and the
  dependency-management inventory in Phase 2) unless the section itself describes runtime,
  configuration, delivery, or dependencies. A skipped phase's Gate is `N/A: scoped`.
- **Full**: a whole-document review or sync, a new document, or a task whose claims depend on
  other areas. Run all ten phases.
- If a scoped task finds that the section's claims depend on files outside the named area,
  say so and widen only that part; this is not an automatic switch to full mode.

---

## Toolchain

| Tool | Phase | Role |
|---|---|---|
| `Bash` (`ls`, `fd`) | 1 Scope, 2 Inventory | discover directory layout and identify target files |
| `Bash` (`rg`) | 2 Inventory – 7 Quality | cross-search symbols, import paths, env vars, config keys |
| `Read` | 2 Inventory – 9 Consistency | read individual files in full detail |
| `Agent` (Explore) | 2 Inventory, 4 Architecture | broad codebase exploration when 3+ targeted queries are needed |
| `Write` | 8 Write Docs | create new documentation files from scratch |
| `Edit` | 8 Write Docs, 9 Consistency | apply minimal-diff updates to existing documentation |
| `WebFetch` | 3 Runtime, 6 Config | fetch external library or framework docs (only when necessary) |

### Tool selection rules
- Apply `skills/DESIGN.md` Agent (Explore) threshold.
- Use `Edit` over `Write` whenever the doc file already exists — preserve existing content.
- `WebFetch` is a last resort; most behavior SHOULD be confirmable from the local codebase.
- Per `rules/ai-execution.md` Tool Usage: MUST NOT re-run the same `grep`/`find` query against unchanged files expecting a different result.
- Per `rules/ai-execution.md` Repository Tool Usage #8, a `grep`/`find` with no matches is not proof of absence — record `Needs confirmation`.

---

## Multi-file processing

When the task names more than one target document (directly, or via a caller
such as `prompts/08_document-sync.md` Step 1), apply `rules/ai-execution.md` Sequential
Target Processing (Base): process one document's Phases 1-10 completely (through Phase
10's Final Report) before starting Phase 1 for the next — MUST NOT batch-inventory
(Phase 2) or batch-write (Phase 8) several documents before finishing any one of them
(each Phase 9 review then sees the prior document's completed edits).

## Core Principles
- Observe before writing
- Evidence before summary
- Inventory before interpretation
- Keep unknowns visible
- Minimal diff: see `SKILL.md` "Minimal diff" and `AGENTS.md` Global Rule 5.
- Separate facts from assumptions

## Gate failure handling

Every Phase below ends with a `### Gate` checklist. If any Gate item is unchecked, redo the `### Do` action it depends on and re-check only that
item before starting the next Phase — MUST NOT proceed with a known-unmet Gate item. Per
`AGENTS.md` Loop Prevention > Attempt Limit, at most 3 redo-and-recheck attempts per Gate
item; if it still cannot be checked after 3 attempts, or the missing evidence cannot be
obtained (the repository does not expose it), record it as an Open Question (Phase 10)
instead of leaving the item silently unchecked or retrying indefinitely.

---

## Phase 1. Scope
### Goal
Fix the target scope before analysis starts.

### Do
- identify repository root, target paths, and expected deliverables
- identify exclusions per `skills/DESIGN.md` Out-of-scope paths (plus repo-specific generated/vendor files)
- note whether existing docs should be updated or created
- choose and record the mode (scoped or full; see Mode above)

### Gate
- [ ] scope is clear
- [ ] exclusions are clear
- [ ] deliverables are clear
- [ ] the mode is recorded

---

## Phase 2. Inventory
### Goal
Build a repository map before writing anything.

### Do
- list major directories and Python packages
- (dependency content only) inspect `pyproject.toml`, applicable lockfiles (e.g. `uv.lock`),
  legacy packaging files (`setup.py`, `setup.cfg`), and `requirements*` files only when present
- inspect CI/CD, Dockerfiles, build scripts, and contributor instructions for the
  dependency-management commands they actually use
- identify test directories, CI/CD files, Docker files, migration files
- determine whether the repo is an app, service, library, worker, or monorepo
- determine, from the evidence above: the authoritative direct dependency declaration, the resolved dependency source, generated or exported dependency files, development/test/production dependency boundaries, the package manager used by each operational environment (development, CI/CD, containers, production), and the commands used to update, validate, install, or synchronize dependencies

### Output
- repository inventory, major file list, packaging/runtime summary
- dependency-management summary: authoritative declaration source, resolved dependency source,
  generated exports (if any), and per-environment package manager and commands

### Read in order

Read in this order, unless the existing documentation's table of contents groups topics
differently — then follow the existing document's order:

1. existing target documentation
2. the documentation entry points: `docs/00_index.md` and the area's `<area>_00_document-guide.md`
   (there is no repository-root `README.md`; read one only if the task names it)
3. `pyproject.toml` / `setup.*`
4. entrypoints
5. route or command registration
6. configuration loading
7. services, domain models, and repositories
8. integrations and DB access
9. tests
10. CI/CD, Docker, deployment, and migrations

MUST NOT write documentation before reading the existing target document.

### Gate
- [ ] package structure is understood; packaging files and major runtime files are identified
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
  commands such as `uv sync`, `uv run`, `uv lock`, and lockfile validation options — MUST NOT add
  these commands to project documentation unless they are verified in the repository

### Gate
- [ ] install path is known
- [ ] minimum startup path is known
- [ ] test path is known
- [ ] external runtime dependencies are visible
- [ ] a traceable dependency synchronization path is known for each operational environment; lockfile validation behavior is known, when a lockfile is used

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
- list HTTP routes, CLI commands, workers, schedulers, batch jobs, tasks
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
- vulnerability or license scanning: document it only if the repository actually configures one
  (the `bandit` scan is code scanning, not dependency scanning); do not record the absence of a
  scanner as a Known Issue unless the task asks for a dependency-security review
- if any of the above cannot be confirmed, record the gap as an open question or `Known Issue`;
  MUST NOT invent a workflow

### Gate
- [ ] test strategy is documented
- [ ] CI/CD is documented
- [ ] quality tools are documented
- [ ] dependency consistency checks and clean-environment sync are documented or recorded as
      open questions; scanning is documented only if configured

---

## Phase 8. Write Docs
### Goal
Convert analysis into maintainable documentation.

Sub-steps: writing policy (8a), removing implementation-derived detail (8b), separating
uncertainty (8c).

### Step 8a: Writing policy

- use evidence-based wording; state a claim once and reference it elsewhere (see Step 8b
  for what to drop); avoid duplication
- MUST NOT hide uncertainty; keep changes minimal if docs already exist
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
- full ASCII file trees, per-file descriptions, symbol index tables, implementation-location
  mappings, literal port numbers — see `skills/DESIGN.md` Docs content policy — remove

Keep: design intent, responsibility boundaries, architectural constraints, non-negotiable
invariants, failure behavior (fail-fast/fail-open), security and operational constraints,
data consistency rules, Known Issues, Needs confirmation items, deprecated behavior relevant
to migration/compatibility, behavior verified by tests, operationally observed behavior,
component responsibility, state ownership, allowed dependency direction, and reasons for
process/configuration separation (see `skills/DESIGN.md` Docs content policy — retain),
the dependency source-of-truth decision, dependency ownership, supported Python-version
constraints when operationally relevant, dependency-group boundaries, lockfile update and
validation policy, compatibility constraints, external export requirements, known dependency
conflicts, and unresolved differences between environments.

Replace removed content with a concise source reference (e.g. "Full configuration keys and default values are in the implementation's config definitions and actual config files.").

**Completed when**: none of the "Normally remove" categories above appear in the draft
outside of a "Keep" category or a source reference.

### Step 8c: Separate uncertainty

- keep important invariants explicit; separate current behavior from design intent where useful
- move unresolved uncertainty to Needs confirmation, unresolved conflicts to Known Issues
- register each item in the active inventories of
  `docs/00_governance/governance_03_issue-and-uncertainty-management.md` (Known Issues in
  Part 1, Needs confirmation in Part 2; the entry fields are defined there). When an item
  is resolved, remove both the inline marker and its inventory entry.
  `tools/check_needs_confirmation_inventory.py` enforces Part 2 (Phase 9)

**Completed when**: every item identified during Phases 1–7 as uncertain or conflicting
has been placed in Needs confirmation or Known Issues and registered in the inventory —
none remain stated as plain fact.

### Step 8d: Register a new document

Applies when the task creates a new `docs/*.md` file (an edit of an existing document needs only
its Front Matter kept valid). Take the requirements from the governance documents for the area
(`governance_00` to `governance_02`) and the checkers' output, not from memory:

- **Front Matter**: `title`, `area`, `tags`, `related` (basenames, no self-reference, no
  duplicates) and a `## Keywords` body section (`governance_02`); `schemas/doc_front_matter.json`
  is the schema the checkers use.
- **Navigation**: add the document where readers find it: the area's `<area>_00_document-guide.md`
  and, for a task-scope row, `docs/00_index.md` "Document References by Task". An ADR is also
  registered in `docs/10_adr/adr_01_index.md`. The exact set of required registrations is
  whatever the governance documents and `tools/check_docs_structure.py` demand: if they do not
  say, record the question as an Open Question instead of guessing.
- **Links**: each internal `.md` link must resolve; a rename or move uses `tools/rename_doc.py`.

### Gate
- [ ] every document in Phase 1's deliverables list is written or updated (coverage is judged
      against that list)
- [ ] a new document is registered per Step 8d, or the registration question is recorded
- [ ] unknowns are recorded explicitly

---

## Phase 9. Consistency Review
### Goal
Remove contradictions across docs and code.

### Check
- file names, module names, and commands match implementation; run/test instructions match config and CI
- inferred content is labeled; no unsupported claims remain
- no secrets are included (See `skills/DESIGN.md`, section "No secrets in output")
- (dependency content only) declarations and lockfiles are consistent; installation commands match CI/CD and container definitions
- generated dependency exports are not described as authoritative sources
- development-only dependencies are not described as production requirements
- lockfile entries are not described as direct application dependencies without supporting
  evidence

When dependency files and operational commands conflict:
- document the currently verified behavior
- preserve documented design intent separately
- record unresolved conflicts as `Known Issues`
- use `Needs confirmation` when authority or intended behavior cannot be verified

### Run the docs checkers

Run every row of `routing.md` Tools → "When to run which tool" that the change triggers:
a `docs/*.md` file added or edited, a domain's docs touched, a "Needs confirmation" marker
added, resolved, or removed, a Front Matter gap, a rename. `AGENTS.md` Global Rule 9: manual
review does not substitute for them.
`uv run python tools/run_validation_gates.py` can run the ones the changed files trigger.
A failure returns to Phase 8 for that item (Gate failure handling applies); do not edit the
checker or its baseline to pass. Record each command and its result for Phase 10.

A pass counts only if the checker actually examined the target
(`rules/ai-execution.md` Repository Tool Usage #8): a pattern that matches no file passes
silently (for example `check_docs_structure.py "23_agent/x_*.md"` without the `docs/` prefix; the
issue `docs010` tracks this). Pass paths or globs exactly as the checker documents them
(repo-root-relative, e.g. `docs/23_agent/<file>.md`), and confirm from its output or by a quick
check (`ls <pattern>` matches at least one file) that the changed file was in scope. A pass with
no confirmed target is recorded as `Needs confirmation`, not as passed.

### Gate
- [ ] major inconsistencies are removed
- [ ] the applicable docs checkers ran, each confirmed to have examined the changed file, and
      pass, or each failure is recorded as an Open Question with its output
- [ ] docs are traceable back to code
- [ ] dependency declarations, lockfiles, and documented commands are consistent, or conflicts
      are recorded as `Known Issues` / `Needs confirmation`

---

## Phase 10. Final Report
### Goal
Return results in a strict final format.

**This documentation task is complete when, and only when**: the Final Gate below is
fully checked (or its unmet items are recorded as Open Questions per Gate failure
handling's Attempt Limit), and every section of the Final Report Format is populated
from what Phases 1-9 already recorded — MUST NOT re-derive or re-run a check merely to produce this report.

### Final Report Format

Write the report in the conversation language (`SKILL.md` Documentation Language); the documents
themselves are English.

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

#### Checks Run
- each docs checker command and its result (Phase 9), or `N/A` with the reason

#### Inventory Changes
- Known Issues and Needs confirmation entries added or removed in
  `governance_03_issue-and-uncertainty-management.md`, or `None`

#### Mode and Next Steps
- the mode (scoped or full); the files are uncommitted, so `git-commit-and-sync` commits
  them

### Final Gate

Confirm the key Phase gates listed below against the Phase gates stated above; MUST NOT re-derive:

- [ ] Phase 3 gate met (`N/A: scoped` or `N/A: no dependency content` when Phase 3 did not run)
- [ ] Phase 4 gate met (entrypoints belong to Phase 3's gate)
- [ ] Phase 8 gate met: unknowns visible and registered; a new document is registered (Step 8d)
- [ ] Phase 9 gate met: no conflict with implementation; the applicable docs checkers pass, each confirmed to have examined the changed file

---

## Evidence and Source of Truth

Source of truth: `SKILL.md` Core Documentation Rules. Documentation SHOULD describe design intent, responsibility boundaries, architectural
constraints, operational notes, failure behavior, confirmed behavior, known issues, and
unresolved questions.

When code and documentation conflict:
- update documentation if the implemented behavior is clearly correct and current
- register or update a Known Issue if the conflict cannot be resolved immediately
- mark the item `Needs confirmation` if the implementation may be incomplete, buggy, provisional, or ambiguous
- MUST NOT silently replace documented design intent with possibly buggy behavior

Important behavioral claims MUST be traceable to evidence: public behavior, configuration
ownership, runtime entrypoints, failure behavior, operational constraints, security-sensitive
behavior, persistence/migration behavior, and documentation/code mismatch corrections. MUST NOT
add evidence labels to every sentence.

Use the evidence labels defined in `skills/DESIGN.md` Shared Vocabulary. When using
`Needs confirmation`, include the required fields defined by the governance documentation.

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
evidence label, open questions, and target document. Keep this as a working list in your own
notes (not a file in the repository); it feeds Phase 10's Confirmed Findings, Inferred Findings,
and Open Questions. Do not paste the raw list into the documents.

---

## Boundaries

See `SKILL.md` "Respect boundaries" (scope, secrets, long code blocks, `requirements.txt` inference, README trust, private API).

- Require `requirements.txt` only when Phase 2's inventory found no other verified
  dependency-management workflow.
- Treat a generated dependency export (e.g. a generated `requirements.txt`) as read-only
  evidence — edit the authoritative declaration or lockfile instead, per Phase 2's findings.
- Leave lockfiles as-is during documentation-only work; regenerate one only when dependency
  maintenance is explicitly in scope for the current task.
- When a static import search finds no reference to a dependency, record it as
  `Needs confirmation` (see Evidence and Source of Truth) rather than classifying it Unused —
  a static search alone cannot confirm dynamic or optional usage.
- Base a "direct usage" or "production inclusion" claim on Phase 2's declared/operational
  evidence categories, not on lockfile membership alone.
- Change dependency declarations only when the task's scope explicitly includes dependency
  maintenance — never merely to simplify documentation.
- Out-of-scope paths: see `skills/DESIGN.md` Out-of-scope paths.

---

## Final Rule
MUST NOT try to sound complete.
Try to be correct, traceable, and maintainable.
