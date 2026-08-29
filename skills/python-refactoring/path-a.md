# Python Refactoring — Path A (Minor Change)

Load this file only after `workflow.md` Step 2 classifies the current change as Path A
(see `SKILL.md` Routing for classification criteria; see `workflow.md` Step 2 for what
Path gating does and does not skip).

---

## Step 3 depth: Preparation

- `rg` and the `deploy.sh` reference check MUST run every time — see `workflow.md`
  Refactoring-Specific Guidance.
- Skip `pydeps`, `import-linter`, and `ast-grep`; record `N/A: Path A` for each in the
  impact scope table.

`discovery.md`'s Technical Debt Discovery, Responsibility Analysis, and Documentation
Drift Detection still apply (not Path-gated; see `workflow.md` Step 3).

---

## Step 4 depth: Behavior Lock

- Skip `mutmut`; record `Not run: Path A` in the manifest and rely on the
  characterization tests and coverage baseline instead.
