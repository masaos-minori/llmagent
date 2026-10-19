## Goal
Make the check tool pin the new default (`rag` and `session` only) instead of `rag` only, while still rejecting any wider default, an unregistered vec0 table, and an unsanctioned `load_vec=True` (`REQ-004`).

## Scope
- The `_DEFAULT_LOAD_VEC_RE` pattern, the problem message in `check_vec_loading`, and the module docstring text (check 4 and the Rule line).
- `VEC_TABLES`, `LOAD_VEC_SANCTIONED`, and the other checks stay as they are.

## Assumptions
- The helper expression is exactly `self._default_load_vec = resolved in ("rag", "session")` as written by the helper procedure.

## Design decisions
- Pin the exact expression with a regex: any other membership set (for example adding `workflow`) fails the check, so the tool keeps enforcing the scope instead of being loosened.
- No new data structure: the allowed set is expressed once, in the regex and its message.

## Alternatives considered
Deriving the allowed set from `VEC_TABLES` and evaluating the helper at import time was rejected: it would couple the tool to importing `db.helper` and hide the pinned text.

## Implementation
### Target file
`tools/check_db_separation.py`

### Procedure
1. Replace `_DEFAULT_LOAD_VEC_RE` with a pattern matching `self._default_load_vec = resolved in ("rag", "session")` (quotes either kind, whitespace tolerant).
2. Update the message in `check_vec_loading` to name the new expression.
3. Update the module docstring: check 4 ("loads the extension by default only for `rag` and `session`") and keep the Rule line pointing at INV-08.

### Method
- Keep `_LOAD_VEC_TRUE_RE`, `LOAD_VEC_SANCTIONED`, and the sanctioned-site loop unchanged.
- Edit the helper (`scripts/db/helper.py`) and this tool in the same commit; `test_live_repository_has_no_violations` fails if only one of them changes.

### Details
- `tools/TOOL_DESCRIPTIONS.md` already describes the check as "sqlite-vec scope"; no description change is needed, but run `uv run python tools/check_tool_descriptions_sync.py` as `routing.md` requires for any `tools/` edit.
- Follow `routing.md` Adding a new tool validation: ruff format and check, `uv run mypy tools/check_db_separation.py`, `uv run bandit tools/check_db_separation.py`, and a smoke run on the live repository.

## Compatibility considerations
Exit codes and output format unchanged; CI `lint` job and the pre-deploy check keep running it.

## Security considerations
N/A: static check only.

## Rollback considerations
Revert the commit together with the helper change.

## Validation plan
- `uv run ruff format tools/check_db_separation.py && uv run ruff check tools/check_db_separation.py`
- `uv run mypy tools/check_db_separation.py`
- `uv run bandit tools/check_db_separation.py`
- `uv run python tools/check_db_separation.py` (exit 0 on the live repository)
- `uv run python tools/check_tool_descriptions_sync.py`

## Completion criteria
- The tool passes on the repository with the new helper default.
- The tool fails when the helper expression is the old `rag`-only form or adds another target (covered by the tests procedure).

## Out of scope
- Changing `VEC_TABLES` or `LOAD_VEC_SANCTIONED`
- Other checks in the tool

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Replace the default-load regex, its message, and the module docstring text | Pending | — | — | |
| 2 | Add or update tests (separate procedure for `tests/tools/test_check_db_separation.py`) | Pending | — | — | |
| 3 | Run the `routing.md` tool validation sequence and the smoke run | Pending | — | — | |

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
- **Requirement ID**: `REQ-004` (pin the new default)
- **Source issue**: issues/20261019-092704_mem001_session-sqlite-vec-not-loaded-at-runtime.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261019-094625_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261019-095521
- **Related target files**: tools/check_db_separation.py
