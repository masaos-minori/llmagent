# Python Refactoring — Path A (Minor Change)

Load this file only after `workflow.md` Step 2 classifies the current change as Path A
(see `SKILL.md` Routing for classification criteria; see `workflow.md` Step 2 for what
Path gating does and does not skip).

---

## Step 3 depth: Preparation

- Use `rg` to find symbol usages (MUST run every time, not conditional — see
  `workflow.md` Step 3).
- Check whether the target files are referenced in `deploy.sh` (MUST run every time).
- Skip `pydeps`, `import-linter`, and `ast-grep`; record `N/A: Path A` for each in the
  impact scope table.

`discovery.md`'s Technical Debt Discovery, Responsibility Analysis, and Documentation
Drift Detection still apply (not Path-gated; see `workflow.md` Step 3).

---

## Step 4 depth: Behavior Lock

- Skip `mutmut`; record `Not run: Path A` in the manifest and rely on the
  characterization tests and coverage baseline instead.
