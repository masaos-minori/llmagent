# Implementation: Rewrite `tests/test_github_mcp_service.py` for fail_open removal (Phase A-2)

## Goal

Update every test in `tests/test_github_mcp_service.py` that currently relies on `allowed_repos_mode="fail_open"` to bypass the repo-allowlist check, so the file keeps passing once `GitHubConfig.allowed_repos_mode` is removed (Phase A-1) and `_assert_allowed_repo()` becomes fail-closed-only (empty `allowed_repos` always denies).

## Scope

**In:**
- `class TestAssertAllowedRepo` (lines 53-123): delete tests that exist specifically to exercise `fail_open` behavior; keep/simplify tests that exercise fail-closed behavior (already the sole remaining mode) by dropping the now-nonexistent `allowed_repos_mode` key
- All other test functions/methods across the file (~24 call sites, confirmed by direct inspection) that pass `{"allowed_repos": [], "allowed_repos_mode": "fail_open", ...}` purely to let an unrelated guard-method test (`_assert_allowed_path`, `_assert_max_file_size`, `_write_github_audit_log`, `_resolve_and_check_branch`, or a full `fmt_*`/`create_*`/`push_*`/`delete_*` service call) proceed without a `GitHubAuthorizationError`: replace with an explicit non-empty `allowed_repos` list containing the exact `owner/repo` slug the test body actually uses
- `_make_service()`'s default fallback (`cfg or {"allowed_repos_mode": "fail_open"}`, line 35): change to a default that remains permissive for tests that don't care about the repo check, without using the removed field (see Method)

**Out:**
- `TestAssertAllowedPath`, `TestAssertMaxFileSize` test bodies themselves (their actual assertions) — only their `_make_service()`/`cfg` setup changes, not what they test
- No behavior change to `_assert_allowed_repo()` beyond what Phase A-1 already specifies

## Assumptions

1. Confirmed by direct inspection (not inference) of every `"allowed_repos": []` occurrence in the file: two literal `owner`/`repo` pairs are in use, not one uniform pair —
   - `owner="org"`, `repo="repo"` — used in `TestGitHubDryRun` and the `fmt_create_*` / `fmt_merge_*` / `fmt_push_files` / `fmt_delete_file` / `fmt_add_issue_comment` / `fmt_update_pull_request` call sites (lines ~477-824)
   - `owner="a"`, `repo="b"` — used in the pre-flight-check tests (`test_create_or_update_file_denies_*`, `test_push_files_denies_*`, `test_delete_repo_file_denies_*`, `test_*_empty_branch_protected_raises`, `test_push_files_writes_audit_log_on_success`) at lines ~238-441
2. `TestAssertAllowedRepo` itself already contains the authoritative tests for fail-closed empty/non-empty list behavior (`test_fail_closed_is_default_when_mode_absent`, `test_fail_closed_empty_list_denies_all`, `test_fail_closed_nonempty_list_allows_listed_repo`, `test_fail_closed_nonempty_list_denies_unlisted_repo`) — these already do not depend on `fail_open` and require no behavior change, only removal of the now-nonexistent `allowed_repos_mode` keyword where present.
3. `_make_service()`'s current default (`cfg or {"allowed_repos_mode": "fail_open"}`) is reached by exactly 4 zero-arg call sites, all in `TestResolveAndCheckBranch` (lines 337, 345, 363, 379) — confirmed by `grep -n "_make_service()" tests/test_github_mcp_service.py`. All 4 call `svc._resolve_and_check_branch(...)` directly, which does not invoke `_assert_allowed_repo()` — so the default's `allowed_repos` value is inert for these specific tests, and updating it to any non-empty placeholder is safe.

## Implementation

### Target file

`tests/test_github_mcp_service.py`

### Procedure

1. In `TestAssertAllowedRepo`:
   - Delete `test_fail_open_empty_list_allows_all` (tests behavior that no longer exists).
   - In the remaining tests, remove the `"allowed_repos_mode": "fail_open"` key wherever `allowed_repos` is already non-empty (these keys are inert — deleting them changes nothing): `test_repo_in_allowlist_passes`, `test_repo_not_in_allowlist_denied`, `test_empty_owner_is_denied`, `test_empty_repo_is_denied`, `test_slash_only_slug_is_denied`, `test_owner_with_slash_multiple_parts_is_denied`.
   - In `test_fail_closed_empty_list_denies_all`, remove the now-redundant `"allowed_repos_mode": "fail_closed"` key (fail-closed is unconditional; the key is inert).
2. For each of the ~17 `owner="org"`/`repo="repo"` call sites (lines ~477-824): replace `{"allowed_repos": [], "allowed_repos_mode": "fail_open"}` with `{"allowed_repos": ["org/repo"]}`.
3. For each of the ~7 `owner="a"`/`repo="b"` call sites (lines ~238-441): replace `{"allowed_repos": [], "allowed_repos_mode": "fail_open", ...other keys...}` with `{"allowed_repos": ["a/b"], ...other keys...}` (preserve all other keys in the same dict unchanged — `protected_branches`, `path_denylist`, `max_file_size_kb`, `audit_log_path` where present).
4. Re-run `grep -n '"allowed_repos": \[\]' tests/test_github_mcp_service.py` after the edits — expect 0 remaining matches outside `TestAssertAllowedRepo`'s intentional fail-closed-empty-list tests (which correctly keep `allowed_repos: []` since they test the deny-all path itself).
5. Update `_make_service()`'s default: change `raw = cfg or {"allowed_repos_mode": "fail_open"}` to `raw = cfg or {"allowed_repos": ["org/repo"]}` (or remove the fallback if no zero-arg callers remain per Assumption 3).
6. Run the full file: `uv run pytest tests/test_github_mcp_service.py -v` — fix any remaining failure by locating the specific `owner`/`repo` slug the failing test uses and adding it to that test's `allowed_repos`.

### Method

Mechanical find-and-replace guided by the two confirmed owner/repo literal groups, followed by an exhaustive test run to catch any site missed by the two groups above (e.g., a third literal pair not yet identified).

### Details

- The key insight that keeps this from being a 1:1 blind find-replace: `allowed_repos_mode` is completely inert whenever `allowed_repos` is non-empty (mode only branches on the empty-list case), so any site with a non-empty `allowed_repos` needs no change beyond dropping the now-nonexistent keyword. Only the ~24 sites with `allowed_repos: []` need a real value substitution.
- Preserve dict key order and surrounding formatting where practical to keep the diff minimal and reviewable.
- If step 6 surfaces a test using a third owner/repo literal not covered above, add that literal directly rather than defaulting to `"org/repo"` for every site — the goal is each test remaining a faithful, minimal-scope check of its own concern.

## Validation plan

```bash
uv run ruff check tests/test_github_mcp_service.py
uv run mypy tests/test_github_mcp_service.py
uv run pytest tests/test_github_mcp_service.py -v
grep -n '"allowed_repos_mode"' tests/test_github_mcp_service.py   # expect no output
```

Expected outcome: all tests in the file pass; no remaining reference to `allowed_repos_mode` anywhere in the file.
