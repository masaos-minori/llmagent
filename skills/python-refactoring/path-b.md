# Python Refactoring — Path B (Higher-Impact Change)

Load this file only after `workflow.md` Step 2 classifies the current change as Path B
(see `SKILL.md` Routing for the full classification criteria).

---

## Step 3 depth: Preparation

- `rg` and the `deploy.sh` reference check MUST run every time — see `workflow.md`
  Refactoring-Specific Guidance.
- Run `pydeps` to inspect the import graph, `import-linter` to verify module
  boundaries, and `ast-grep` for structural usage search — each subject to the
  Conditional Validation handling defined in `validation.md` (report why unavailable,
  use an alternative if one exists; a skipped check MUST NOT be reported as passed).

`discovery.md`'s Technical Debt Discovery, Responsibility Analysis, and Documentation
Drift Detection all still apply — they are not Path-gated (see `workflow.md` Step 3).

---

## Step 4 depth: Behavior Lock

- Run `mutmut` when the repository configures and supports it (per `validation.md`
  Conditional Validation). When run, ensure there are no surviving mutations in the
  refactored paths, or that every surviving mutation is documented as equivalent
  (`report-template.md` format). When unavailable, report `Not run` — mutation
  coverage MUST NOT be treated as satisfied in that case.

---

## Note for Path C

Path C applies at least this Path's Step 3/4 depth (Path C's criteria entail the
import-boundary/dependency-direction conditions Path B already tests for) — see
`path-c.md`.
