# Implementation Procedure: Git-Specific Approval Preview for build_preview() (REQ-003)

## Goal

Add a git_* case to build_preview() in scripts/agent/tool_result_formatter.py that shows a purpose-built preview naming the repository path and target branch/remote instead of falling through to the generic JSON-dump case.

## Scope

Add a dedicated git_* branch to build_preview() before the final fallback (`return _json_dumps(args)[:300]`). Read repo_path, branch, remote from args and format them consistently with the existing move_file branch pattern ("{source} → {destination}").

## Assumptions

- git_* tool args consistently include repo_path; branch and remote keys vary per tool (git_checkout uses branch, git_push uses remote) — the preview case must handle both.
- The move_file branch pattern ("{source} → {destination}", lines ~73-74) is the correct model to follow.
- _preview_file_path() cannot be reused unmodified because git tool args use repo_path (not path/file_path).

## Design decisions

- Mirror the move_file branch pattern: build a string with meaningful parts separated by a consistent delimiter. Use "@" after repo_path to indicate "at repository" (analogous to how SSH URLs work).
- Branch and remote are optional — include only when present in args.
- Keep the preview format simple and consistent with existing patterns; future adjustments can be made in a follow-up PR based on operator feedback.

## Alternatives considered

- Reuse _preview_file_path() with a key remapping layer. Rejected: git tool args use different key names (repo_path vs path/file_path), making remapping fragile and unclear.
- Format as an SSH-style URL (e.g., "git@host:path"). Rejected: the Plan explicitly models on move_file's "{source} → {destination}" pattern, not SSH URL formatting.

## Implementation

### Target file

`scripts/agent/tool_result_formatter.py`

### Procedure

Add `git_*` case to `build_preview()` before the final fallback.

### Method

Insert a new branch between the existing `github_*` branch and the final fallback:

```python
if tool_name.startswith("git_"):
    repo = args.get("repo_path", "?")
    branch = args.get("branch")
    remote = args.get("remote")
    parts = [f"git@{repo}"]
    if branch:
        parts.append(f"branch={branch}")
    if remote:
        parts.append(f"remote={remote}")
    return " ".join(parts)
```

### Details

The full build_preview() function after modification:

```python
def build_preview(tool_name: str, args: dict[str, Any]) -> str:
    """Build a human-readable operation preview shown before approval prompts."""
    if tool_name in ("write_file", "edit_file"):
        return _preview_file_write(args)
    if tool_name in ("delete_file", "delete_directory", "create_directory"):
        return _preview_file_path(args)
    if tool_name == "move_file":
        return f"{args.get('source', '?')} → {args.get('destination', '?')}"
    if tool_name == "shell_run":
        return _preview_shell_cmd(args)
    if tool_name.startswith("github_"):
        return build_github_preview(args)
    if tool_name.startswith("git_"):
        repo = args.get("repo_path", "?")
        branch = args.get("branch")
        remote = args.get("remote")
        parts = [f"git@{repo}"]
        if branch:
            parts.append(f"branch={branch}")
        if remote:
            parts.append(f"remote={remote}")
        return " ".join(parts)
    return _json_dumps(args)[:300]
```

Example outputs:
- git_checkout: `git@https://github.com/example/repo branch=main`
- git_push: `git@https://github.com/example/repo remote=origin`
- git_log: `git@https://github.com/example/repo`

## Compatibility considerations

- This changes the preview output format for git_* tools from a raw JSON dump to a structured string. Operators will see clearer information before approving.
- No impact on any other tool category's preview behavior.

## Security considerations

- This is a security improvement: operators can now recognize what they are approving without needing to parse raw JSON. Reduces risk of approving unintended operations due to unclear preview.

## Rollback considerations

- If the preview format needs adjustment, remove the git_* branch and revert to the previous fallback. The underlying tool execution is unaffected.

## Validation plan

- Unit test for the new build_preview() git case:
  1. git_checkout with repo_path + branch → non-empty, non-JSON-dump preview containing "git@" and "branch="
  2. git_push with repo_path + remote → non-empty, non-JSON-dump preview containing "git@" and "remote="
  3. git_log with repo_path only → non-empty, non-JSON-dump preview containing "git@" but no "branch=" or "remote="
  4. Unknown git tool (no repo_path) → preview with "?" placeholder

## Completion criteria

- build_preview() has a git_* branch before the final fallback.
- Preview includes repo_path prefixed with "git@", plus branch= and/or remote= when present.
- Unit test covers all four scenarios above.
- Existing tool categories' previews remain unchanged.

## Out of scope

- Extending git-specific preview to any tool category other than git_*.
- Modifying _preview_file_path() or _preview_file_write().
- Adding preview for github_* tools (already handled by build_github_preview()).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add git_* case to build_preview() in scripts/agent/tool_result_formatter.py | Completed | 20260831-150523 | 20260831-150523 | Already implemented on disk (commit `e8f0086bf`, prior session), matching this document's Method/Details exactly — `git_*` branch inserted before the final fallback, producing `git@{repo_path}` plus optional `branch=`/`remote=` parts. |
| 2 | Write unit test for the new build_preview() git case | Completed | 20260831-150523 | 20260831-150523 | Already present in `tests/agent/test_tool_result_formatter.py::TestBuildPreview` (`test_git_checkout_with_repo_and_branch`, `test_git_push_with_repo_and_remote`, `test_git_log_with_repo_only`, `test_git_tool_missing_repo_path_shows_placeholder`), covering all four Validation-plan scenarios. `uv run pytest tests/agent/test_tool_result_formatter.py -k git` — 9 passed. `ruff check`/`mypy` clean on the file. |

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
- **Requirement ID**: REQ-003
- **Source issue**: issues/20260828-163234_mcp004_approval_risk_hierarchy_gaps.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260829-150209_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260829-205709
- **Related target files**: scripts/agent/tool_result_formatter.py
