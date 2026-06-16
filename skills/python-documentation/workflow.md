# Python Documentation — Detailed Workflow

## Toolchain

| Tool | Phase | Role |
|---|---|---|
| | | |

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
