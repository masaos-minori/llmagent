## Goal
- Remove the two mypy `attr-defined` errors at `CanonicalSourceRegistry.validate_all` by typing its `result` dict, so `tools/` can join the mypy scope (`REQ-001`: fix the errors with real typing; `REQ-005`: no suppression, no behavior change).

## Scope
**Release unit**: N/A: not part of a release unit

- In scope: one annotation in `validate_all` of `tools/check_canonical_source_registry.py`.
- Plan: `plans/20261105-105442_toolmypy001_add-tools-to-mypy-scope.md`, Plan step 1 (Phase 1). It runs first: the scope widening in the later documents must not land before this one.

## Assumptions
- `Any` is already imported (`from typing import Any`, line 24), and `validate_all` already declares the return type `dict[str, Any]` (verified by `uv run mypy --no-namespace-packages scripts/ tests/eventbus tools`, 2026-11-05: exactly two errors, at lines 851 and 854).
- The existing tests in `tests/tools/test_check_canonical_source_registry.py` cover `validate_all`; a type annotation changes no runtime behavior, so no new test is added.
- Plan overlap: no other open Plan targets this file.

## Design decisions
- Annotate the literal as `result: dict[str, Any] = {...}`, matching the declared return type; a TypedDict is a larger change than the Plan asks for.

## Alternatives considered
N/A: a `# type: ignore` is forbidden by `REQ-005`, and a TypedDict is out of scope.

## Implementation
### Target file
`tools/check_canonical_source_registry.py`

### Procedure
1. In `validate_all`, change `result = {` to `result: dict[str, Any] = {`, leaving the keys (`valid`, `errors`, `warnings`, `summary`) and every later line unchanged.
2. Run `uv run mypy --no-namespace-packages tools` and confirm no error is reported for this file.

### Method
- A single-line edit; mypy then infers `result["errors"]` as `Any`, so `.extend(...)` type-checks.

### Details
- Do not touch `generate_report` or any other method.
- Do not add an import; do not add a suppression comment.

## Compatibility considerations
N/A: annotation only; the returned dict and the checker's output are unchanged.

## Security considerations
N/A: no input handling or trust boundary changes.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run mypy --no-namespace-packages tools` reports no error in this file.
- `uv run pytest tests/tools/test_check_canonical_source_registry.py -q` passes.
- `uv run ruff format` and `uv run ruff check` on the file are clean; `uv run python tools/check_suppression_justification.py` reports no new suppression.

## Completion criteria
- The two `attr-defined` errors are gone and no `# type: ignore` was added.
- The file's tests pass unchanged.

## Out of Scope
- The two `annotation-unchecked` notes in `tools/manage_workitem_stage.py`, stricter mypy options, and any other change to this tool.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Annotate `result` in `validate_all` | Pending | — | — | |
| 2 | Run mypy, the file's tests, ruff, and the suppression check (`rules/toolchain.md`) | Pending | — | — | |

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
- **Requirement ID**: `REQ-001` (fix the typing errors), `REQ-005` (no suppression, no behavior change)
- **Source issue**: issues/20261104-152002_toolmypy001_add-tools-to-mypy-scope.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261105-105442_toolmypy001_add-tools-to-mypy-scope.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261105-133115
- **Related target files**: `tools/check_canonical_source_registry.py`
