# Implementation: shared/git_helper.py — structured RepoInfoResult (req 70)

## Goal

Replace `dict | None` return with `RepoInfoResult` frozen dataclass so callers
can inspect structured failure reasons instead of just getting `None`.

## Changes

### `scripts/shared/git_helper.py`
- Add `from dataclasses import dataclass` and `from enum import StrEnum` to imports
- Add `FailureReason(StrEnum)` with 5 values
- Add `RepoInfoResult(frozen=True)` dataclass: success, data, failure_reason
- Change `get_repo_info()` return type to `RepoInfoResult`
- Replace all `return None` with `RepoInfoResult(success=False, failure_reason=...)`
- Split `git.exc.InvalidGitRepositoryError` from generic `git.exc.GitError`

### `scripts/agent/services/context_view.py`
- Update caller: `git_info["branch"] if git_info else None`
  → `repo_result.data["branch"] if repo_result.success else None`

### `tests/test_git_helper.py`
- Import FailureReason, RepoInfoResult
- Replace all `is None` / `is not None` with `.success`, `.data`, `.failure_reason`

### `docs/06_shared_03_runtime_and_execution.md`
- Update §7 git_helper API reference to show RepoInfoResult return type

### `docs/06_shared_90_inconsistencies_and_known_issues.md`
- Update EXCEPT-01 to reflect new structured result design
