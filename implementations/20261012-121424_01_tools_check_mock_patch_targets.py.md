## Goal
- Let `find_ineffective_patch_targets` skip a patch call whose own physical line carries `# mock-patch-ok: <reason>` with a non-empty reason (`REQ-003`).

## Scope
- Only `tools/check_mock_patch_targets.py`. Its tests are procedure 02 and its inventory entry is procedure 03.

## Assumptions
- The `ast` `lineno` of a `patch(...)` `Call` node is the line holding `patch(`, which is where the marker is written.
- `find_ineffective_patch_targets` already holds the file text (`text`), so no new file read is needed.

## Design decisions
- The marker is line-local and needs a non-empty reason, so one comment cannot silence another patch and a bare marker does not suppress.
- The candidate-module heuristic, the report-only exit code, and the output formats stay unchanged.

## Alternatives considered
N/A: the Plan Design section already fixed the approach for this row.

## Implementation
### Target file
`tools/check_mock_patch_targets.py`

### Procedure
1. Add `import re` and a module constant `_SUPPRESSION_RE = re.compile(r"#\s*mock-patch-ok:\s*(\S.*)$")`.
2. Add `_has_suppression_marker(line: str) -> bool` returning whether the regex matches.
3. In `find_ineffective_patch_targets`, build `lines = text.splitlines()` once per test file and, for each `(lineno, target)`, `continue` when `_has_suppression_marker(lines[lineno - 1])` is true (guard `1 <= lineno <= len(lines)`).
4. Extend the module docstring with a short marker section (syntax, line-local, reason required).

### Method
- Evaluate the marker before the importer loop so a suppressed patch produces no finding for any importer.
- Use `re.search` on the single physical line; do not look at neighbouring lines.

### Details
- A patch call spanning several lines is matched on the line of its `patch(` token only.
- Keep `from __future__ import annotations` style and type hints; no new CLI option.

## Compatibility considerations
- Without markers the output is identical to today's, so existing callers and tests are unaffected.

## Security considerations
N/A: no input handling, credentials, or I/O boundary is touched.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- Tests are added in procedure 02.
- `uv run ruff format --check tools/check_mock_patch_targets.py`, `uv run ruff check tools`, `uv run mypy tools/check_mock_patch_targets.py`.
- `uv run python tools/check_mock_patch_targets.py` still reports findings until procedures 07 to 09 add markers.

## Completion criteria
- A marker with a non-empty reason on the `patch(` line suppresses that patch's findings; all other behavior is unchanged; ruff and mypy are clean.

## Out of scope
- Changing the candidate-module heuristic or the exit code; wiring the checker into hooks or CI.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement marker support in `find_ineffective_patch_targets` and update the module docstring | Pending | — | — | |
| 2 | Run the validation sequence (`rules/toolchain.md`) for the touched files (tests come from procedure 02) | Pending | — | — | |

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
- **Requirement ID**: `REQ-003` (inline suppression marker with a mandatory reason)
- **Source issue**: issues/20261012-120426_mock001_fix-ineffective-mock-patch-targets-in-tests.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261012-120856_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261012-121424
- **Related target files**: tools/check_mock_patch_targets.py
