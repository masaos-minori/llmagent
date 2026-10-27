# Python Refactoring — Path B (Higher-Impact Change)

Load this file only after `workflow.md` Step 2 classifies the change as Path B (criteria:
`SKILL.md` Routing).

---

## Step 3 depth: Preparation

- `rg` and the deploy-reference search (`deploy/`, `conf.d/`, `init.d/`) MUST run every
  time — see `workflow.md` Step 2 and Refactoring-Specific Guidance.
- Run `pydeps` (import graph), `PYTHONPATH=scripts uv run lint-imports` (module boundaries),
  and `ast-grep` (structural usage search), each under `validation.md` Conditional Validation
  handling (a skipped check MUST NOT be reported as passed).

`discovery.md` investigations still apply (`workflow.md` Step 3).

---

## Step 4 depth: Behavior Lock

- Run `mutmut` when configured and supported (`validation.md` Conditional Validation; scoping:
  `workflow.md` Refactoring-Specific Guidance): no surviving mutations in the refactored
  paths, or each documented as equivalent (`report-template.md`). Otherwise report `Not run`;
  mutation coverage MUST NOT be treated as satisfied.

---

## Note for Path C

See `path-c.md`, opening paragraph, for how Path C's required tool depth relates to
this Path's Step 3/4.
