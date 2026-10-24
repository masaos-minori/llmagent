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
AST-safe tools, validate that behavior/API/side effects are unchanged, then report the
evidence. See `workflow.md`'s opening for the safety-over-speed priority statement.
This is a reactive workflow — see Core rules below.

---

## Phase overview

| Step | Name | Goal / AI Action |
|---|---|---|
| 0 | Load required instructions | Read the files `workflow.md` Step 0 lists (rules, this skill, `workflow.md`, `validation.md`, `report-template.md`); `discovery.md` is loaded at Step 2, the matching `path-*.md` after classification. |
| 1 | Identify target files | Confirm every specified target file path exists before starting; process one file (or approved atomic migration group) at a time. |
| 2 | Refactoring intent declaration | Run the preliminary `rg` caller/deploy search, declare goal, expected behavior change, and Path A/B/C classification (see Routing below); stop and record as a proposal if any behavior change is expected. |
| 3 | Preparation | Map blast radius at the depth the Path classification calls for (`path-a.md`/`path-b.md`/`path-c.md`), re-classifying upward if needed; run Technical Debt Discovery, Responsibility Analysis, and Documentation Drift Detection (`discovery.md`, scaled to the Path). |
| 4 | Behavior lock | Establish coverage/characterization baseline at the depth the Path classification calls for; capture Architecture Baseline for Path C (`path-c.md`). |
| 5 | Side-effect inventory | Record the pre-transformation side-effect baseline (`validation.md`). |
| 6 | Transformation | Apply the Deletion-First Evaluation before any new abstraction, then transform with AST-safe tooling. |
| 7 | Validation | Run Required and Conditional validation (`validation.md`), plus Path C's Architecture Comparison Validation (`path-c.md`). |
| 8 | Incremental migration | Classify diff hunks and keep each logical group independently rollback-safe. |
| 9 | CI gate | Run the full repository validation sequence. |
| 10 | Report results | Report per `report-template.md`; the refactor is complete only once its Completion Gate passes. |

See `workflow.md` for the detailed per-step procedure and multi-file/atomic-migration-group
rules.

---

## Routing (Path Classification)

Classify the change as Path A, Path B, or Path C in Step 2, before Step 3, using the
preliminary `rg` caller/deploy-reference search that `workflow.md` Step 2 requires. This
gates how much tooling depth Steps 3 and 4 apply — it does not skip Steps 3, 4, or 7
themselves, nor reduce Step 7's Required validation, nor skip the Completion gate. If
Step 3's full impact mapping meets a higher Path's criteria, re-classify upward and
re-declare per `workflow.md` Step 3; never downgrade.

"Files affected" below counts source files only; characterization tests added under
`tests/` for the target (`workflow.md` Step 4) do not by themselves raise the Path.
"Referenced in deploy scripts" means the target's module path or symbol appears under
`deploy/`, `conf.d/`, or `init.d/` (`deploy/deploy.sh` is the main file).

### [Path A] Minor change
**Criteria (Must satisfy ALL):**
- [ ] Affects a single target source file
- [ ] No import boundary changes (no new cross-layer imports)
- [ ] `Expected behavior change: none` (per the Step 2 declaration)
- [ ] Not referenced in deploy scripts

**Execution path:** load `path-a.md` — skip `pydeps`/`import-linter`/`ast-grep` (Step 3)
and `mutmut` (Step 4); Steps 3, 4, 7, and the Completion gate still run.

### [Path B] Higher-impact change
**Criteria (Satisfies ANY):**
- [ ] Affects more than one source file
- [ ] Changes an import boundary or module layer
- [ ] Referenced in deploy scripts
- [ ] Touches shared/extracted logic used by more than one caller

**Execution path:** load `path-b.md` — run `pydeps`/`import-linter`/`ast-grep` (Step 3)
and `mutmut` when available (Step 4), each subject to `validation.md` Conditional
Validation's reporting rules.

### [Path C] Architectural refactoring
**Criteria (Satisfies ANY):**
- [ ] Module relocation
- [ ] Module merge or split
- [ ] Responsibility or ownership transfer
- [ ] Dependency-direction change
- [ ] Architectural boundary change

If a change satisfies any Path C criterion, classify it as Path C even if it also
satisfies a Path B criterion (e.g. an import-boundary change that is a byproduct of a
relocation, merge, split, ownership transfer, or boundary change is Path C, not Path B);
a narrower import-direction fix that is not part of such a structural change remains
Path B.

**Execution path:** load `path-c.md` — apply at least Path B's Step 3/4 depth, plus the
pre-implementation approval checklist, Architecture Baseline (Step 4 addendum),
Architecture Comparison Validation (Step 7 addendum), mandatory ADR, and Path C
Completion Requirements (Step 10 addendum) it defines.

---

## Core Execution Rules

### Core rules
- Change only one feature or one responsibility at a time.
- Keep every change small — as a concrete bound, never worsen the `radon cc` grade of a
  touched function (`rules/toolchain.md` reports grade C or worse with `-n C`). A function
  already at grade C or worse that the target requires touching is refactored toward a
  lower grade only for the part in scope; restructuring the whole function is recorded
  as a Proposal.
- If a change may alter behavior, MUST NOT implement it — record it as a proposal
  instead (see `report-template.md` "Proposals not implemented").
- Minimize changes to exception handling, state, side effects, I/O, and concurrency.
- MUST NOT refactor code unless explicitly instructed via a target file or issue — this
  workflow is reactive, not proactive.

### Refactoring rules
- For the function(s) this task targets, give each one responsibility: MUST NOT leave
  fetching, transformation, decision logic, and persistence mixed in a targeted
  function — extract each concern. Untouched functions are out of scope (one
  responsibility change at a time, per Core rules).
- Reduce nesting and branching in targeted functions. Complexity is measured by
  `radon cc` grade (cyclomatic complexity, not line count); lower it where the
  targeted change allows, and MUST NOT raise it.
- Prefer early returns and small helper functions when they improve clarity.
- Use clear and explicit names.
- Extract shared logic only when it should evolve together later.
- Avoid unnecessary abstraction — see `workflow.md` Step 6 Deletion-First Evaluation.

### Type safety rules
- Add explicit type annotations where needed.
- A runtime boundary check or `None` guard is allowed only when it provably leaves
  exception types, messages, ordering, and return values unchanged (`validation.md`
  Exception behavior freeze); otherwise record it as a Proposal and use a static
  annotation only.
- MUST NOT introduce `Any`, unnecessary casts, or unsafe assertions — existing ones in
  untouched code stay as they are (record as a Finding if relevant).
- Keep input validation separate from internal logic, within the targeted functions.

### Process rules
- **One file at a time**: see `workflow.md` Multi-file processing (atomic migration
  groups are the one exception, per `path-c.md`).
- **Reporting is required**: see `report-template.md`. A cycle MUST NOT be reported
  complete while its Completion Gate has an unsatisfied item.
- Out-of-scope paths: see `skills/DESIGN.md` Out-of-scope paths.

---

## Output format

Output is refactored source code plus a structured chat report (structure and
Completion Gate: see `report-template.md`); no single generated document.

---

## See Also
See `workflow.md` for detailed phase content, commands, and the toolchain reference.
See `path-a.md` / `path-b.md` / `path-c.md` for Path-specific depth and requirements.
See `discovery.md` for the Finding/Drift/Responsibility-Analysis vocabulary.
See `validation.md` for the test/type/API/side-effect checklist.
See `report-template.md` for the final report structure and completion gate.

---

## Composes with

### Run after this skill
- `git-commit-and-sync` — when the user asks to stage, commit, or push the result;
  this skill never commits on its own (`workflow.md` Step 8).
- `deploy` — run `deploy`'s Phase 2-3 after `workflow.md` Step 9 (CI gate) if
  `scripts/` files were added, removed, or renamed.
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
