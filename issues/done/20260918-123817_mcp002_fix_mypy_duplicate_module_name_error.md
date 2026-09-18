# Fix myPy "Source file found twice under different module names" error for `shared.tool_constants`

## Priority
High

## Summary
Resolve myPy configuration conflict where `scripts/shared/tool_constants.py` is detected under two different module names (`shared.tool_constants` and `scripts.shared.tool_constants`), blocking all myPy type checking across the project.

## Background
myPy reports the following error for every file checked:

```
scripts/shared/tool_constants.py: error: Source file found twice under different module names: "shared.tool_constants" and "scripts.shared.tool_constants"
```

This error prevents myPy from performing any further type checking. The root cause is a conflict between myPy's `mypy_path = scripts` setting and the `files = ["scripts/"]` setting in `pyproject.toml`.

The codebase consistently imports using `from shared.tool_constants import ...` (without the `scripts.` prefix). At runtime, this works correctly because `PYTHONPATH=scripts` makes `shared.tool_constants` resolve to `scripts/shared/tool_constants.py`. However, myPy interprets both `shared.tool_constants` (via `mypy_path`) and `scripts.shared.tool_constants` (via `files`) as valid module names for the same physical file.

## Problem
Every invocation of myPy fails with the duplicate-module-name error, making type checking impossible for the entire project. This blocks CI pipelines and developer workflows that rely on myPy for static analysis.

## Reason for Change
Without resolving this, no myPy-based tooling can function. The error affects all Python files in the project, not just `tool_audit.py`.

## Implementation Intent
Fix the myPy configuration in `pyproject.toml` to eliminate the duplicate module detection.

**Root cause:** myPy detects `shared.tool_constants` through two independent mechanisms:
1. Via `mypy_path = scripts`: `shared.tool_constants` resolves to `scripts/shared/tool_constants.py`
2. Via `files = ["scripts/"]`: myPy scans `scripts/` and finds `shared` as a top-level package (because `scripts/shared/__init__.py` exists), so `shared.tool_constants` also resolves to `scripts/shared/tool_constants.py`

Both paths lead to the same file, hence the duplicate detection.

**Correct solution:** Add `--no-namespace-packages` flag to myPy invocations. This disables PEP 420 namespace package support, preventing myPy from treating `shared` as a top-level package when scanning `scripts/`. Verified working on all previously failing files:
- `scripts/agent/services/config_reload.py` → OK
- `scripts/agent/orchestrator.py` → OK
- `scripts/agent/tool_audit.py` → OK
- `scripts/agent/services/config_section_reload.py` → OK
- `scripts/agent/services/config_service_sync.py` → OK

**Invalid approaches (tested and rejected):**
- Approach A: Removing `mypy_path = scripts` — does NOT work; `files = ["scripts/"]` still detects `shared` as top-level package
- Approach B: Adding `shared/` to myPy's ignore list — does NOT work; myPy detects duplicate before applying overrides
- `--explicit-package-bases` — does NOT work; same error persists
- `--follow-imports=silent` — does NOT work; error still reported
- Excluding `scripts/shared/tool_constants.py` via `exclude` — does NOT work; same reason
- `namespace_packages = true` in config — does NOT work; same reason

## Target Files or Areas
- `pyproject.toml` (myPy configuration section)
- Any CI/CD scripts or developer documentation that invoke myPy directly

## Required Changes
- [ ] Add `--no-namespace-packages` flag to myPy invocation in `pyproject.toml` (via `[tool.mypy]` section or CLI wrapper)
- [ ] Verify myPy runs cleanly on all affected files
- [ ] Confirm no regressions in import resolution for other `shared.*` modules
- [ ] Update any CI/CD scripts that invoke myPy directly to include the flag

## Constraints
- Must not break existing import patterns (`from shared.X import Y`)
- Must not require changes to source code import statements
- Must preserve compatibility with the editable install (`__editable__.llmagent-0.1.0.finder.__path_hook__`)

## Acceptance Criteria
- myPy runs without the "Source file found twice" error on all previously failing files
- All existing `from shared.*` imports continue to resolve correctly
- No new myPy errors introduced by the configuration change
- `--no-namespace-packages` flag is documented in any relevant CI/CD or developer setup docs

## Testing Expectations
- Run `PYTHONPATH=scripts uv run mypy --no-namespace-packages scripts/agent/services/config_reload.py` — clean
- Run `PYTHONPATH=scripts uv run mypy --no-namespace-packages scripts/agent/orchestrator.py` — clean
- Run `PYTHONPATH=scripts uv run mypy --no-namespace-packages scripts/agent/tool_audit.py` — clean
- Verify no regressions: confirm `from shared.tool_constants import ...` still works at runtime

## Documentation Impact
Update any internal documentation referencing myPy configuration if needed.

## Out of Scope
- Changing import styles in source code (keep `from shared.X import Y`)
- Modifying the editable install configuration unless absolutely necessary
- Adding `__init__.py` files to resolve the conflict (this would change the package structure)

## Dependencies
None. This is a self-contained configuration fix.

## Unresolved Questions
- Does `--no-namespace-packages` affect myPy's ability to handle other namespace packages in the project?
- Should the flag be added to `pyproject.toml` via a custom myPy wrapper script, or via a CLI option in the `[tool.mypy]` section?

## AI Implementation Instruction
1. Read `pyproject.toml` myPy section to understand current configuration.
2. Test `--no-namespace-packages` flag: `PYTHONPATH=scripts uv run mypy --no-namespace-packages scripts/agent/services/config_reload.py` — must pass clean.
3. If the flag works, add it to the myPy invocation method used by the project (CI/CD, dev scripts, etc.).
4. Verify myPy passes on all three previously-failing files plus additional files.
5. Do NOT modify source code import statements.
6. Do NOT try removing `mypy_path = scripts` or adding `shared/` to ignore lists — these were tested and confirmed invalid during adversarial verification.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20260918-123817
- **Related target files**: pyproject.toml
