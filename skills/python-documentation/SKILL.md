---
name: python-documentation
description: |
  Strictly inspect an existing Python repository and produce concise, evidence-based documentation from source code, configuration, tests, and CI/CD.
  Treat implementation as the only source of truth, reject unsupported claims, keep uncertainty explicit, minimize unnecessary edits, and follow the required reporting format exactly.
---

# Python Documentation Skill

## When to use
Use this skill only for documenting an existing Python repository from actual code, config, tests, and CI/C*.

## When not to use
Do not use this skill for:
- speculative or design-first documentation
- non-Python targets
- new code or architecture design
- marketing or end-user content
- anything not verified from implementation

---

## Core Rules

### 1. Source of Truth
- Trust Python source code and config files first
- README, comments, and docs are only supporting references
- If docs and code conflict, code wins

### 2. Evidence First
- Important statements must include file-path evidence
- When possible, reference:
  - package / module names
  - classes / functions
  - routes / commands / tasks
  - config keys
  - environment variables
- Do not make unsupported claims

### 3. No Hallucination
- Do not invent missing behavior
- Do not assume framework patterns without evidence
- Do not treat unused code as active behavior

### 4. Explicit Uncertainty
Use these labels:
- Confirmed = directly verified in code
- Inferred = strongly supported by multiple clues
- Unknown = cannot be confirmed

### 5. Minimal Diff
- If docs already exist, do not rewrite everything unnecessarily
- Fix errors, fill gaps, reduce duplication
- Prefer minimal changes with maximum clarity

---

## Working Method

### 1. Inventory First
Before writing, identify:
- main directories
- Python packages
- config files
- entrypoints
- public interfaces
- test structure
- CI/CD and Docker presence

### 2. Read in Order
Read in this order when possible:

1. README / docs
2. `pyproject.toml`, `setup.cfg`, `setup.py`, `requirements*`
3. entrypoints (`__main__.py`, `main.py`, `app.py`, `manage.py`, console scripts)
4. route / command / worker registration
5. config loading
6. services / domain / models
7. repositories / DB / integrations
8. tests / `conftest.py`
9. CI/CD / Docker / migrations / release files

### 3. Keep Evidence Notes
Track:
- `path`
- `kind`
- `why_it_matters`
- `confirmed_facts`
- `open_questions`

### 4. Separate These Clearly
- Fact = directly visible in implementation
- Interpretation = strongly supported conclusion
- Proposal = improvement suggestion

### 5. Keep Unknowns Visible
- Record unresolved items in `docs/known-unknowns.md`
- Do not hide uncertainty, especially when multiple entrypoints exist

---

## Never Do These
- Do not document features not confirmed by code
- Do not trust README claims without verification
- Do not infer runtime behavior from `requirements.txt` alone
- Do not treat dead code, dead tasks, or dead migrations as active behavior
- Do not expose secrets
- Do not paste long code blocks unless necessary
- Do not expand scope beyond the requested target

---

## Output Style
Use this structure when possible:

1. Overview
2. Scope
3. Evidence Reviewed
4. Implementation Facts
5. Notes / Caveats
6. Unknowns

Style:
- concise
- professional
- maintenance-friendly
- evidence-based
- uncertainty labeled as `Confirmed`, `Inferred`, or `Unknown`

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
