# Run ruff check in the local validation gates so lint errors do not reach master

## Priority
Medium

## Summary
`ruff check scripts/` can fail on master without any local gate noticing. Add it to the checks that run before a commit (or make the commit hook reliably present), so a lint error is caught locally and not first by the required CI `lint` check.

## Background
The CI `lint` job (`.github/workflows/ci.yml`) runs `ruff format --check scripts/`, `ruff check scripts/`, mypy and a security scan, and is a required status check on master (branch protection contexts: `test`, `lint`). The repository also declares a `ruff` pre-commit hook in `.pre-commit-config.yaml`, and `rules/toolchain.md` section 1 documents `uv run ruff check scripts/` as the lint step. `skills/git-commit-and-sync` runs `tools/run_validation_gates.py` before committing.

## Problem
Evidence (verified 2026-11-15):
- The `lint` job failed on every master CI run in the sampled history (25 runs, from 2026-11-14 04:27 UTC until the fix landed at 2026-11-15 09:08 UTC). The cause was seven `I001` import-order errors in `scripts/rag/ingestion/` (`chunk_grouping.py`, `chunk_japanese.py`, `document_persistence.py`, `embedding.py`, `file_routing.py`, `pipeline_utils.py`, `transaction_commit.py`). A local `ruff check` at the pre-fix commit reported the same error, so it was detectable locally.
- This checkout has no git pre-commit hook: `.git/hooks/` holds only `*.sample` files and `core.hooksPath` is unset. The `ruff` hook in `.pre-commit-config.yaml` therefore never runs at commit time here. No document found by `grep` tells a contributor to run `pre-commit install`.
- `tools/run_validation_gates.py` does not run ruff: `parse_precommit_hooks` skips hooks without an `entry` (remote repos such as ruff), so the pre-commit gate only covers the local tool hooks.
- The result: the required `lint` check blocked the merge of an unrelated PR (#17) and was the only place the error surfaced.

## Reason for Change
A required check that no local step mirrors means every lint regression is found late, after a push, and blocks unrelated work. The fix itself was trivial (`ruff check scripts/ --fix`); the cost was the delay and a master that was red for over a day.

## Implementation Intent
Make the local pre-commit gate cover what the CI `lint` job checks for ruff, with the least new machinery. Decide between two options (see Unresolved Questions): have `tools/run_validation_gates.py` run `ruff check` (and `ruff format --check`) when `scripts/` Python files changed, or document and verify installing the git hook. Keep the gate fast: scope it to changed files where ruff allows it.

## Target Files or Areas
- `tools/run_validation_gates.py` (and its tests under `tests/tools/`)
- `.pre-commit-config.yaml`
- `rules/toolchain.md` (section 1 and the pre-commit section)
- `skills/git-commit-and-sync/workflow.md` (Phase 4), only if the gate description changes

## Required Changes
- Make a ruff failure (`ruff check`, and `ruff format --check`) on changed `scripts/` Python files a `Fail` in `tools/run_validation_gates.py`, or install and verify the git pre-commit hook as the chosen alternative.
- Add tests for the chosen gate behaviour, including a changed file with an import-order error producing `Fail`.
- Update `rules/toolchain.md` so the documented pre-commit step matches the behaviour.

## Constraints
- The gate must use the repository's pinned ruff (`uv run ruff`), the same version the CI job uses.
- The runtime added to the gate must stay small; it must not run ruff over the whole repository when only a few files changed.
- Do not change the ruff configuration or the isort settings in this issue.
- The parity check between pre-commit hooks and validation gates (`check validation gates and pre-commit hooks stay in parity`) must keep passing.

## Acceptance Criteria
- With a deliberate `I001` error in a changed `scripts/` file, the pre-commit gate (the one `git-commit-and-sync` Phase 4 runs) reports `Fail` and names the file.
- With no ruff finding in changed files, the gate reports no ruff `Fail`.
- `rules/toolchain.md` and the gate description agree on what runs.
- The tests for the new behaviour pass; the full suite and the CI `lint` job still pass.

## Testing Expectations
Unit tests for the new gate entry in `tests/tools/` (a passing and a failing changed-file case); `uv run mypy` and `uv run ruff check` on the touched tools; the parity checker; one manual run of the gate against a file with a deliberate import-order error, reverted afterwards.

## Documentation Impact
`rules/toolchain.md`: state which ruff checks the pre-commit gate runs and, if the hook route is chosen, how a contributor installs it. No other `docs/` change.

## Out of Scope
- Fixing lint errors other than the seven already fixed.
- Mypy, bandit or other CI `lint` job steps (only if a separate issue asks for them).
- Changing branch protection or the required checks.
- Making CI itself run the local gate.

## Dependencies
N/A: none

## Unresolved Questions
- 不明: which option is preferred, running ruff inside `tools/run_validation_gates.py` or installing the git hook (the hook also covers commits made outside the skill flow, but depends on each checkout installing it)?
- 不明: whether other checkouts or machines have the hook installed. Only this checkout was inspected.
- 不明: whether the red `lint` job before 2026-11-14 04:27 UTC was the same cause; the sampled history starts there.

## AI Implementation Instruction
Read `tools/run_validation_gates.py` and its tests first. Reuse its existing changed-file selection and the way it reports `Pass`/`Fail`; do not add a second runner. Run `uv run ruff` from the project environment. Keep the change inside `tools/`, its tests and `rules/toolchain.md`, and follow `rules/toolchain.md` for the validation sequence.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261115-183024
- **Related target files**: tools/run_validation_gates.py, .pre-commit-config.yaml, rules/toolchain.md, skills/git-commit-and-sync/workflow.md
