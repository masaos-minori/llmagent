# Python Refactoring — Path B (Higher-Impact Change)

Load this file only after `workflow.md` Step 2 classifies the change as Path B (criteria:
`SKILL.md` Routing).

---

## Step 3 depth: Preparation

- `rg` and the deploy-reference search (`deploy/`, `conf.d/`, `init.d/`) MUST run every
  time — see `workflow.md` Step 2 and Refactoring-Specific Guidance.
- Run `pydeps` to inspect the import graph, `PYTHONPATH=scripts uv run lint-imports`
  (`import-linter`, per `rules/toolchain.md`) to verify module boundaries, and `ast-grep` for structural usage search — each subject to the
  Conditional Validation handling defined in `validation.md` (report why unavailable,
  use an alternative if one exists; a skipped check MUST NOT be reported as passed).

`discovery.md`'s Technical Debt Discovery, Responsibility Analysis, and Documentation
Drift Detection still apply — not Path-gated (`workflow.md` Step 3).

---

## Step 4 depth: Behavior Lock

- Run `mutmut` when the repository configures and supports it (per `validation.md`
  Conditional Validation; scoping rules: `workflow.md` Refactoring-Specific Guidance). When run, ensure there are no surviving mutations in the
  refactored paths, or that every surviving mutation is documented as equivalent
  (`report-template.md` format). When unavailable, report `Not run` — mutation
  coverage MUST NOT be treated as satisfied in that case.

---

## Note for Path C

See `path-c.md`, opening paragraph, for how Path C's required tool depth relates to
this Path's Step 3/4.
