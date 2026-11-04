# Extract shared bootstrap, repo-root, and git helpers for tools/

## Priority
Medium

## Summary
Replace the copy-pasted bootstrap, repository-root, and git-subprocess code in `tools/` with one shared helper module, and settle how tools are invoked.

## Background
Confirmed by repository evidence on 2026-11-04:

- `if __package__ in (None, ""): sys.path.insert(0, str(Path(__file__).resolve().parent.parent))` appears in 27 files under `tools/` (for example `check_adr_structure.py`, `manage_frontmatter.py`).
- `REPO_ROOT = Path(__file__).resolve().parent.parent` is defined in 23 files.
- 8 files call `git` through `subprocess` with their own wrappers (`check_adr_preservation.py`, `classify_changes.py`, `check_workitem_traceability.py`, `rename_doc.py`, `scan_change_consumers.py`, `module_nodes.py`, `run_validation_gates.py`, `manage_binaries.py`).
- Invocation is mixed: `.pre-commit-config.yaml` runs `uv run python -m tools.*`, while most `.github/workflows/ci.yml` steps run `uv run python tools/<name>.py`. The path form is why the `sys.path` bootstrap exists.

## Problem
The same code is repeated and has already diverged in behavior details (each git wrapper handles errors and encoding on its own). Any fix must be applied in many places.

## Reason for Change
Maintenance risk. Not urgent; best done after tests and type checks cover `tools/`.

## Implementation Intent
Introduce one small private helper module (repo root resolution, a `git` runner with a uniform error and encoding policy, and exit-code constants shared with the CLI-convention issue). Migrate files incrementally, only when they are otherwise touched or in small batches, and decide first whether CI moves to `-m tools.*` so the `sys.path` bootstrap can be dropped.

## Target Files or Areas
- New private helper module under `tools/` (name: to be decided)
- The 27 bootstrap files, the 23 `REPO_ROOT` files, and the 8 git-wrapper files listed above
- `.github/workflows/ci.yml` (invocation form)
- `tools/TOOL_DESCRIPTIONS.md` (private helper entry)

## Required Changes
- Decide and document the supported invocation form (`-m tools.<name>` versus `tools/<name>.py`).
- Add the helper with tests; migrate files in small batches, removing the local copies.
- Remove the `sys.path` bootstrap from migrated files only after their CI and pre-commit calls use the chosen form.

## Constraints
- Behavior of every migrated tool must stay identical, including exit codes and output.
- Helper module name must start with `_` per the existing private-module convention and be listed in `TOOL_DESCRIPTIONS.md`.
- Do not migrate in one large change.

## Acceptance Criteria
- A single implementation of repo-root resolution and the git runner exists, with tests.
- No migrated file keeps a local copy of either.
- Every CI step and pre-commit hook uses the documented invocation form.
- `uv run pytest tests/tools -q` and the validation gates pass after each batch.

## Testing Expectations
- Unit tests for the helper (success, git failure, non-UTF-8 output); the existing `tests/tools` suite as a regression guard; run both invocation forms for one migrated tool.

## Documentation Impact
Update `tools/TOOL_DESCRIPTIONS.md` (new helper entry, invocation convention) and any doc stating how tools are called.

## Out of Scope
- Changing any tool's functionality.
- Splitting large tools (separate issue).

## Dependencies
- Depends on `issues/20261104-152002_toolmypy001_add-tools-to-mypy-scope.md` and `issues/20261104-152002_toolstest001_add-tests-for-untested-tools.md` (land first).
- Shares exit-code constants with `issues/20261104-152002_toolcli001_define-cli-and-exit-code-convention.md`.

## Unresolved Questions
- Which invocation form to standardize on: unknown (decision needed).
- Whether any consumer outside the repository calls `tools/<name>.py` by path: unknown.

## AI Implementation Instruction
Migrate a few files per change and run the whole `tests/tools` suite each time. Do not alter behavior while moving code.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261104-152002
- **Related target files**: `tools/check_adr_structure.py`, `tools/manage_frontmatter.py`, `tools/run_validation_gates.py`, `tools/classify_changes.py`, `.github/workflows/ci.yml`, `tools/TOOL_DESCRIPTIONS.md`
