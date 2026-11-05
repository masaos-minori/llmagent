# Bring tools/ under the mypy gate

## Priority
Medium

## Summary
Add `tools/` to the mypy scope used by pyproject, CI, and the pre-commit hook, after fixing the type errors that currently exist there.

## Background
Confirmed by repository evidence on 2026-11-04:

- `[tool.mypy] files` in `pyproject.toml` is `["scripts/", "tests/eventbus"]`. `.github/workflows/ci.yml` and `rules/toolchain.md` run `uv run mypy --no-namespace-packages scripts/ tests/eventbus`. `tools/` is not type-checked anywhere.
- The pre-commit `mypy` hook (`.pre-commit-config.yaml`) passes no explicit paths (`pass_filenames: false`), so it follows the `files` setting in `pyproject.toml`.
- Running `uv run mypy --no-namespace-packages tools` (read-only) on 66 source files reports 2 errors in 1 file: `tools/check_canonical_source_registry.py:851` and `:854`, `"object" has no attribute "extend"` (`attr-defined`). Two `annotation-unchecked` notes appear in `tools/manage_workitem_stage.py` (lines 1394 and 1411); they are notes, not errors.

## Problem
`tools/` holds about 25,000 lines of CI and workflow tooling that gates commits, yet type regressions in it are never caught. The cost to close the gap is small today and grows with each unchecked change.

## Reason for Change
Maintenance risk only; no incident is known. Doing it now is cheap because only one file needs a fix.

## Implementation Intent
Fix the existing errors, then widen the mypy scope in one place and align every documented invocation. Keep the scope change and the fix in the same change set so the gate never turns red.

## Target Files or Areas
- `tools/check_canonical_source_registry.py`
- `pyproject.toml` (`[tool.mypy]`)
- `.github/workflows/ci.yml`, `.pre-commit-config.yaml`
- `rules/toolchain.md`, `routing.md` (documented mypy commands)
- `tools/run_validation_gates.py` (`TOOLCHAIN_GATES` `mypy` gate, command tuple lists `scripts/` and `tests/eventbus`; located 2026-11-05)
- Further places that state the scope, found by adversarial verification on 2026-11-05: `tox.ini` (`typecheck` command), `rules/coding.md` (Tool configuration and mypy note), `skills/python-lint-typecheck/workflow.md` (scope text and the Step 6 command), and `routing.md` "Adding a new tool" step 2 (says `tools/` is not covered).

## Required Changes
- Fix the two `attr-defined` errors with real typing (no blanket `# type: ignore`).
- Add `tools/` to the mypy scope in `pyproject.toml` and the CI command.
- Update the documented command in `rules/toolchain.md` and any other place that states the scope.
- Confirm the `--no-namespace-packages` behavior still avoids the "Source file found twice" failure with `tools` included.

## Constraints
- Do not add suppressions without justification (`check_suppression_justification.py` applies).
- Keep `warn_unused_ignores` behavior consistent with CI.
- CI and pre-commit run time increase: not measured; record it.

## Acceptance Criteria
- `uv run mypy --no-namespace-packages scripts/ tests/eventbus tools` reports no errors.
- `pyproject.toml`, `ci.yml`, and `rules/toolchain.md` state the same scope.
- The pre-commit hook type-checks `tools/` without a separate configuration.

## Testing Expectations
- Run the new mypy command and `uv run python tools/run_validation_gates.py`.
- Run `uv run pytest tests/tools -q` to confirm the typing fix changes no behavior.

## Documentation Impact
Update the toolchain documentation for the new scope (operational notes only).

## Out of Scope
- Enabling stricter mypy options.
- Typing `tests/` beyond `tests/eventbus`.

## Dependencies
- This issue must land before `issues/20261104-152002_toolcommon001_shared-helper-for-tools.md`, `issues/20261104-152906_toolreport001_share-report-model-and-renderers.md`, and `issues/20261104-152906_toolwrite001_make-mutating-tools-dry-run-and-atomic.md`, so their refactors are type-checked. (Corrected by adversarial verification on 2026-11-05: the original text said toolcommon001 should land first, which contradicts toolcommon001's own Dependencies.)

## Unresolved Questions
- Extra CI and pre-commit time from checking `tools/`: a warm-cache run of `uv run mypy --no-namespace-packages scripts/ tests/eventbus tools` took 0.8 s on 2026-11-05 (557 files, no "Source file found twice", the same 2 errors only); the cold run with `--no-incremental` is unmeasured.

## AI Implementation Instruction
Fix the typing at the source of the `object` inference rather than silencing it. Change the scope only after the command is clean.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261104-152002
- **Related target files**: `tools/check_canonical_source_registry.py`, `pyproject.toml`, `.github/workflows/ci.yml`, `.pre-commit-config.yaml`, `rules/toolchain.md`
