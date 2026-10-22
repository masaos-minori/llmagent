## Goal
Replace the `read_json_file` example in a section comment of `tools/check_compat_shims.py` with a description that names no symbol, with no behavior change (REQ-006).

## Scope
- One comment line (the second case of the removed-name reintroduction rule); no code change.

## Assumptions
- The comment sits above the removed-name reintroduction check and is not parsed by any tool or test (verified: tests exercise functions, not comments).
- No real example of "a name that remains in source but is no longer the current production path" exists today.

## Design decisions
- Replace "(e.g. `read_json_file`)" with "(for example a function that is still defined but superseded)".

## Alternatives considered
N/A: one-comment edit.

## Implementation
### Target file
`tools/check_compat_shims.py`

### Procedure
1. Edit the comment line containing "(e.g. `read_json_file`)" as described, keeping line length within 88 characters.

### Method
- Comment-only edit; confirm with `git diff` that no code line changed.

### Details
- Follow `routing.md` "Adding a new tool" validation for a modified tool file.

## Compatibility considerations
No behavior change; the tool's output is identical.

## Security considerations
N/A: comment only.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run pytest tests/tools/test_check_compat_shims.py -q`, `uv run python tools/check_compat_shims.py` (All checks passed).
- `uv run ruff format tools/check_compat_shims.py`, `uv run ruff check tools/check_compat_shims.py`, `uv run mypy tools/check_compat_shims.py`, `uv run bandit tools/check_compat_shims.py`.
- `rg read_json_file tools` returns no match.

## Completion criteria
- The comment names no symbol, the tool's tests and run pass, and the diff contains only the comment change.

## Out of Scope
- Any code change and the context-aware check itself.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Reword the comment | Completed | 20261022-115451 | 20261022-115451 | Changed: tools/check_compat_shims.py (comment only) |
| 2 | Run the tool tests and the tool | Completed | 20261022-115451 | 20261022-115451 | validated; full suite 9689 passed, 14 skipped; ruff, mypy, bandit on edited tools pass; docs checkers pass; check_compat_shims tests (84) pass |
| 3 | Run the tool validation sequence per `routing.md` | Completed | 20261022-115451 | 20261022-115451 | validated; full suite 9689 passed, 14 skipped; ruff, mypy, bandit on edited tools pass; docs checkers pass; check_compat_shims tests (84) pass |

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
- **Requirement ID**: `REQ-006` (symbol-free example in the tool comment)
- **Source issue**: `issues/20261021-104152_glossex_decouple-the-glossary-and-checks-from-removed-symbols.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261022-094501_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261022-101645
- **Related target files**: tools/check_compat_shims.py