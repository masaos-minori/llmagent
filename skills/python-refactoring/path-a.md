# Python Refactoring — Path A (Minor Change)

Load this file only after `workflow.md` Step 2 classifies the change as Path A (criteria:
`SKILL.md` Routing; what Path gating does and does not skip: `workflow.md` Step 2).

---

## Step 3 depth: Preparation

- `rg` and the deploy-reference search (`deploy/`, `conf.d/`, `init.d/`) MUST run every
  time — see `workflow.md` Step 2 and Refactoring-Specific Guidance.
- Skip `pydeps`, `import-linter`, and `ast-grep`; record `N/A: Path A` for each in the
  impact scope table.

`discovery.md` investigations still apply (`workflow.md` Step 3).

---

## Step 4 depth: Behavior Lock

- Skip `mutmut`; record `Not run: Path A` in the manifest and rely on the
  characterization tests and coverage baseline instead.
