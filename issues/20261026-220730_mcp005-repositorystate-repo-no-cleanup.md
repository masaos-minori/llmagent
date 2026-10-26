# RepositoryState._repo holds live git.Repo reference without cleanup

## Priority
Medium

## Summary
`RepositoryState._repo` holds a strong reference to a `git.Repo` instance that is never explicitly closed or cleaned up, potentially leaking file descriptors and GitPython internal resources.

## Background
The `RepositoryState` dataclass in `repository_state.py` has a `_repo` field (line 43) that stores a `git.Repo` reference:

```python
_repo: git.Repo | None = field(default=None, repr=False, compare=False)
```

The `snapshot()` class method (lines 58-87) creates a `git.Repo` instance and passes it to the constructor:

```python
repo = git.Repo(path_str, search_parent_directories=False)
...
return cls(..., _repo=repo)
```

The `repo` property (lines 95-103) exposes this reference:

```python
@property
def repo(self) -> git.Repo:
    if self._repo is None:
        raise RuntimeError("RepositoryState has no attached git.Repo")
    return self._repo
```

The `verify_postcondition` method (lines 155-177) accesses `post_state._repo` directly.

## Problem
The `git.Repo` object holds file descriptors to the `.git` directory and may hold locks on the repository. When `RepositoryState` is serialized via `_serialize_state` (line 135 of `git_server.py`), the `_repo` field is excluded from serialization (due to `repr=False, compare=False`), but the reference is still held in memory.

The problem manifests in two scenarios:

1. **Long-lived RepositoryState instances**: If a `RepositoryState` is cached or retained beyond the request lifecycle, the `git.Repo` file descriptors remain open. This can lead to file descriptor exhaustion under sustained load.

2. **Git lock contention**: GitPython's `git.Repo` may hold locks on the `.git` directory. If the same repository is accessed concurrently by multiple requests, the locks can conflict, causing `OSError` or `IOError` from GitPython.

3. **Memory leak**: The `git.Repo` object holds references to the working tree, index, and packed refs. These are not garbage-collected until the `RepositoryState` is destroyed, which may be much later than the request completes.

## Reason for Change
Holding a live `git.Repo` reference without cleanup violates the principle of least resource retention. The snapshot captures immutable state; the `git.Repo` object is only needed during the pipeline execution, not after.

## Implementation Intent
1. Close the `git.Repo` reference after the pipeline completes, or
2. Use a weak reference pattern to allow garbage collection, or
3. Explicitly close the `git.Repo` in a `__del__` method or context manager.

## Target Files or Areas
- `scripts/mcp_servers/git/repository_state.py` — `RepositoryState._repo` field (line 43), `snapshot()` method (lines 58-87), `repo` property (lines 95-103)

## Required Changes
- Add a `close()` method to `RepositoryState` that closes the underlying `git.Repo`
- Ensure the `git.Repo` is closed after the pipeline completes (in `call_tool` or pipeline wrapper)
- Consider using a context manager pattern (`with RepositoryState.snapshot(...) as state:`)
- Document the resource lifecycle in the `RepositoryState` docstring

## Constraints
- Must not change the existing snapshot semantics (the snapshot must capture the same state)
- Must preserve the `repo` property for code paths that need direct access

## Acceptance Criteria
- `git.Repo` file descriptors are released after the pipeline completes
- No file descriptor leaks under sustained load
- Existing code paths that use `repo` property continue to work

## Testing Expectations
- Unit test: verify `git.Repo` is closed after pipeline completion
- Integration test: verify no file descriptor leak under sustained load
- Regression test: ensure `repo` property still works for direct access

## Documentation Impact
Update `RepositoryState` docstring to document the resource lifecycle and the need for explicit cleanup.

## Out of Scope
- Changes to GitPython's `git.Repo` behavior
- Changes to the snapshot capture logic itself

## Dependencies
N/A: none

## Unresolved Questions
- Does GitPython's `git.Repo` have a `close()` method?
- Are there any code paths that retain `RepositoryState` beyond the request?

## AI Implementation Instruction
In `scripts/mcp_servers/git/repository_state.py`, add a `close()` method to `RepositoryState` that closes the underlying `git.Repo`. Ensure the `git.Repo` is closed after the pipeline completes. Do not modify any other MCP server's resource management.

## Traceability
- **Workflow phase**: python-code-review
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261026-220730
- **Related target files**: scripts/mcp_servers/git/repository_state.py
