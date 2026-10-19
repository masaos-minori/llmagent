## Goal
Add tests proving the check tool accepts the new default and rejects the old rule and any wider default (`REQ-004`).

## Scope
- Three new test functions and one small helper appended to the file; existing tests stay untouched.

## Assumptions
- `check_vec_loading` reads `SCRIPTS_DIR / "db" / "helper.py"` and walks `SCRIPTS_DIR`, so tests redirect `SCRIPTS_DIR` and `REPO_ROOT` with `monkeypatch`, the way `test_detects_attach_and_qualified_access` does.

## Design decisions
- Write a fake `scripts/db/helper.py` containing only the assignment line under test; the sanctioned-site walk then sees no other files.

## Alternatives considered
N/A: tests of one check function.

## Implementation
### Target file
`tests/tools/test_check_db_separation.py`

### Procedure
1. Add `_fake_scripts` (new): creates `scripts/db/helper.py` under `tmp_path` with a given assignment line and monkeypatches `mod.SCRIPTS_DIR` and `mod.REPO_ROOT`.
2. `test_default_load_vec_rule_accepts_rag_and_session` (new): the new expression yields no problem.
3. `test_default_load_vec_rule_rejects_rag_only` (new): the old `resolved == "rag"` expression yields a `[vec-scope]` problem.
4. `test_default_load_vec_rule_rejects_extra_target` (new): `resolved in ("rag", "session", "workflow")` yields a `[vec-scope]` problem.

### Method
- Call `mod.check_vec_loading()` and assert on the `[vec-scope]` text.
- Keep `test_live_repository_has_no_violations` as the end-to-end guard.

### Details
- Write the fake helper text with the exact indentation the regex tolerates (it matches the assignment, not the surrounding class).

## Compatibility considerations
N/A: tests only.

## Security considerations
N/A: tests only.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run pytest tests/tools/test_check_db_separation.py -q`
- `uv run ruff format tests/tools/test_check_db_separation.py && uv run ruff check tests/tools/test_check_db_separation.py`

## Completion criteria
- The three new tests pass with the updated tool and fail against the old regex.
- `test_live_repository_has_no_violations` passes.

## Out of scope
- Tests for other checks
- Changing the tool

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add the helper and three tests | Completed | 20261019-101422 | 20261019-101422 |  |
| 2 | Run the validation sequence (`rules/toolchain.md`) for the test file | Completed | 20261019-101422 | 20261019-101422 |  |

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
- **Requirement ID**: `REQ-004` (check-tool tests)
- **Source issue**: issues/20261019-092704_mem001_session-sqlite-vec-not-loaded-at-runtime.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261019-094625_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261019-095521
- **Related target files**: tests/tools/test_check_db_separation.py