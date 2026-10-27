---
name: python-refactoring
description: |
  Use this skill PROACTIVELY when refactoring existing Python source files without
  changing external behavior, public APIs, or visible output. Execute the refactor
  through the mandatory staged process (Phase overview Step 0 through Step 10) gated by
  a Path A/B/C impact classification that scales tooling depth and architectural
  safeguards to blast radius. Covers:
  refactoring-intent declaration, behavior locking via characterization tests and
  mutation testing, Deletion-First evaluation before introducing new abstractions,
  side-effect/public-API/exception-behavior preservation checks, incremental
  migration, and a structured final report with a completion gate.
  Use for structural changes: module splits/merges, import-cycle removal, cross-file
  renames, class hierarchy restructuring, and public API migration.
  Do NOT use this skill for feature development, intentional behavior changes, or bug
  fixes that change output — see `routing.md` Task → skill mapping (Feature / bug fix /
  new module row).
---

# Python Refactoring Skill

## Purpose

Refactor existing Python source files without changing external behavior: lock current
behavior with tests, classify the change's blast radius (Path A/B/C), transform with
AST-safe tools, validate behavior/API/side effects, then report the evidence. Reactive
workflow (Core rules below); safety-over-speed: `skills/DESIGN.md`.

---

## Phase overview

| Step | Name | Goal / AI Action |
|---|---|---|
| 0 | Load required instructions | Read the files `workflow.md` Step 0 lists (rules, this skill, `workflow.md`, `validation.md`, `report-template.md`); `discovery.md` is loaded at Step 2, the matching `path-*.md` after classification. |
| 1 | Identify target files | Confirm every specified target file path exists before starting; process one file (or approved atomic migration group) at a time. |
| 2 | Refactoring intent declaration | Run the preliminary `rg` caller/deploy search, declare goal, expected behavior change, and Path A/B/C classification (see Routing below); stop and record as a proposal if any behavior change is expected. |
| 3 | Preparation | Map blast radius at the depth the Path classification calls for (`path-a.md`/`path-b.md`/`path-c.md`), re-classifying upward if needed; run Technical Debt Discovery, Responsibility Analysis, and Documentation Drift Detection (`discovery.md`, scaled to the Path). |
| 4 | Behavior lock | Establish coverage/characterization baseline and the `radon cc` complexity baseline at the depth the Path classification calls for; capture Architecture Baseline for Path C (`path-c.md`). |
| 5 | Side-effect inventory | Record the pre-transformation side-effect baseline (`validation.md`). |
| 6 | Transformation | Apply the Deletion-First Evaluation before any new abstraction, then transform with AST-safe tooling. |
| 7 | Validation | Run Required and Conditional validation (`validation.md`), plus Path C's Architecture Comparison Validation (`path-c.md`). |
| 8 | Incremental migration | Classify diff hunks and keep each logical group independently rollback-safe. |
| 9 | CI gate | Run the gates the change requires: scoped `pre-commit`, `lint-imports`, and diff-cover at 90% on changed lines (`workflow.md` Step 9). |
| 10 | Report results | Report per `report-template.md`; the refactor is complete only once its Completion Gate passes. |

Per-step procedure and multi-file/atomic-migration-group rules: `workflow.md`.

---

## Routing (Path Classification)

Classify in Step 2 (before Step 3) using the preliminary `rg` caller/deploy search of
`workflow.md` Step 2. The Path gates only the tooling depth of Steps 3 and 4; Steps 3, 4, 7,
Step 7's Required validation, and the Completion gate always run. If Step 3's impact mapping
meets a higher Path's criteria, re-classify upward and re-declare (`workflow.md` Step 3);
never downgrade.

"Files affected" counts source files only (characterization tests under `tests/` do not raise
the Path). "Referenced in deploy scripts": the target's module path or symbol appears under
`deploy/`, `conf.d/`, or `init.d/`.

### [Path A] Minor change
**Criteria (Must satisfy ALL):**
- [ ] Affects a single target source file
- [ ] No import boundary changes (no new cross-layer imports)
- [ ] `Expected behavior change: none` (per the Step 2 declaration)
- [ ] Not referenced in deploy scripts

**Load:** `path-a.md` (skips `pydeps`/`import-linter`/`ast-grep` and `mutmut`).

### [Path B] Higher-impact change
**Criteria (Satisfies ANY):**
- [ ] Affects more than one source file
- [ ] Changes an import boundary or module layer
- [ ] Referenced in deploy scripts
- [ ] Touches shared/extracted logic used by more than one caller (callers are counted per
      `workflow.md` Step 2: distinct non-test files that use a symbol the refactor changes)

**Load:** `path-b.md` (`pydeps`/`import-linter`/`ast-grep` in Step 3, `mutmut` in Step 4 when
available; reporting per `validation.md` Conditional Validation).

### [Path C] Architectural refactoring
**Criteria (Satisfies ANY):**
- [ ] Module relocation
- [ ] Module merge or split
- [ ] Responsibility or ownership transfer
- [ ] Dependency-direction change
- [ ] Architectural boundary change

Path C wins over Path B when both apply (an import-boundary change that is a byproduct of a
relocation, merge, split, ownership transfer, or boundary change is Path C); a narrower
import-direction fix outside such a change stays Path B.

**Load:** `path-c.md` (at least Path B's Step 3/4 depth, plus its approval checklist,
Architecture Baseline, Architecture Comparison Validation, mandatory ADR, and Completion
Requirements).

---

## Core Execution Rules

### Core rules
- Change only one feature or one responsibility at a time.
- Keep every change small: never worsen the `radon cc` grade of a touched function
  (baseline: `workflow.md` Step 4; check: `validation.md` Complexity check). For a function
  already at grade C or worse, lower the grade only for the part in scope; restructuring the
  whole function is a Proposal.
- If a change may alter behavior, MUST NOT implement it — record it as a proposal
  instead (see `report-template.md` "Proposals not implemented").
- Minimize changes to exception handling, state, side effects, I/O, and concurrency.
- MUST NOT refactor code unless explicitly instructed via a target file or issue — this
  workflow is reactive, not proactive.

### Refactoring rules
- Targeted functions get one responsibility: MUST NOT leave fetching, transformation,
  decision logic, and persistence mixed in one; extract each concern. Untouched functions are
  out of scope.
- Reduce nesting and branching in targeted functions (`radon cc` grade, not line count);
  MUST NOT raise it.
- Prefer early returns and small helper functions when they improve clarity.
- Use clear and explicit names.
- Extract shared logic only when it should evolve together later.
- Avoid unnecessary abstraction — see `workflow.md` Step 6 Deletion-First Evaluation.

### Type safety rules
- Add explicit type annotations where needed.
- A runtime boundary check or `None` guard only when it provably leaves exception types,
  messages, ordering, and return values unchanged (`validation.md` Exception behavior
  freeze); otherwise a Proposal plus a static annotation only.
- MUST NOT introduce `Any`, unnecessary casts, or unsafe assertions (existing ones in
  untouched code stay; record as a Finding if relevant).
- Keep input validation separate from internal logic, within the targeted functions.

### Process rules
- **One file at a time**: see `workflow.md` Multi-file processing (atomic migration
  groups are the one exception, per `path-c.md`).
- **Reporting is required**: see `report-template.md`. A cycle MUST NOT be reported
  complete while its Completion Gate has an unsatisfied item.
- Out-of-scope paths: see `skills/DESIGN.md` Out-of-scope paths.

---

## Output format

Refactored source code plus a structured chat report (`report-template.md`: structure and
Completion Gate); no generated document.

---

## Composes with

### Run after this skill
- `git-commit-and-sync` — when the user asks to stage, commit, or push the result;
  this skill never commits on its own (`workflow.md` Step 8).
- `deploy` — after `git-commit-and-sync` (it deploys a pushed HEAD), when `scripts/` files
  were added, removed, or renamed (`workflow.md` Special Cases). Only on the user's
  request; this skill never starts it.
- `issue-creator` — to file the report's Proposals and Findings, when the user asks.
- `python-documentation` — if public interfaces or module names changed, update
  corresponding docs.

### Use separately if needed
- `python-implementation` — only if the refactor reveals a feature gap requiring new
  code.

### This skill may be triggered by
- `python-debug-root-cause` — when a failure's root cause is a structural issue.
- `python-code-review` — when a review finding requires structural change without
  behavior change.
- `python-lint-typecheck` — when a quality fix requires restructuring modules to
  eliminate an architectural or import-cycle violation.
- `python-test-and-fix` — when resolving a failure or adding a test exposes
  architectural debt requiring a structural rewrite.
- `issue-to-plan` — when a plan's implementation involves structural module changes.

---

## Improvement feedback

After running this skill:
- if a Path's classification criteria were too strict or too loose, update Routing
  above
- if a Step needed clarification, or a Path-specific depth rule produced a false
  positive/negative, update `workflow.md` or the relevant `path-*.md` file
- if the report was missing a field the user consistently requested, add it to
  `report-template.md`

MUST NOT weaken safety requirements without explicit justification.
