## Goal

Add `--no-namespace-packages` flag to myPy invocations to eliminate the "Source file found twice under different module names" error caused by `shared.tool_constants` being detected via both `mypy_path = scripts` and `files = ["scripts/"]`. (REQ-004)

## Scope

- Modify `.github/workflows/ci.yml`: add `--no-namespace-packages` to CI myPy step at line 27

## Assumptions

- `--no-namespace-packages` is available in the myPy version used by CI (confirmed: myPy 2.1.0 supports it)
- The CI workflow uses `uv run mypy scripts/` without any additional flags

## Design decisions

- Add `--no-namespace-packages` directly to the CI workflow's `run:` command rather than creating a separate wrapper script, because:
  1. It is the simplest approach with minimal maintenance burden
  2. The CI environment already has myPy installed via `uv run`
  3. Consistent with how the flag would be added to local workflows

## Alternatives considered

- Creating a wrapper script (e.g., `scripts/run_mypy.sh`): rejected because it adds unnecessary complexity for a single-flag addition
- Modifying `pyproject.toml`'s `[tool.mypy]` section: rejected because the flag is CLI-only, not a TOML setting

## Implementation
### Target file

`.github/workflows/ci.yml`

### Procedure

1. At line 27, change `uv run mypy scripts/` to `uv run mypy --no-namespace-packages scripts/`

### Method

Single-line edit in the CI workflow YAML file.

### Details

```diff
--- a/.github/workflows/ci.yml
+++ b/.github/workflows/ci.yml
@@ -24,7 +24,7 @@ jobs:
       - name: Type check
-        run: uv run mypy scripts/
+        run: uv run mypy --no-namespace-packages scripts/
```

## Compatibility considerations

- Backward-compatible: `--no-namespace-packages` disables PEP 420 namespace package support, preventing myPy from finding `shared` as a top-level package when scanning `scripts/`. This eliminates the duplicate detection without changing runtime behavior.

## Security considerations

No new secrets exposure or unsafe operations introduced. The flag only affects myPy's internal package resolution logic.

## Rollback considerations

Revert the one-line diff above. CI will return to its previous state where myPy fails with the duplicate-module-name error.

## Validation plan

- Unit: Confirm `--no-namespace-packages` flag is present at line 27 after the edit.
- Integration: CI pipeline passes with the updated myPy step.
- Regression: `uv run ruff check .github/workflows/ci.yml` clean.

## Completion criteria

- [ ] `.github/workflows/ci.yml` line 27 includes `--no-namespace-packages`.
- [ ] CI pipeline passes with the updated myPy step.
- [ ] All validation checks pass.

## Out of scope

- Modifying `pyproject.toml`'s `[tool.mypy]` section.
- Modifying `tox.ini`'s typecheck command.
- Changing import styles in source code.

## execution_status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add `--no-namespace-packages` flag to CI workflow myPy step | Pending | — | — | |
| 2 | Verify CI workflow passes | Pending | — | — | |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: REQ-004
- **Source issue**: issues/20260918-123817_mcp002_fix_mypy_duplicate_module_name_error.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260918-124909_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260918-164928
- **Related target files**: .github/workflows/ci.yml

(End of file - total 113 lines)
