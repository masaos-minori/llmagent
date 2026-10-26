## Goal
Add explicit resource cleanup for `git.Repo` in `RepositoryState` to prevent file descriptor leaks under sustained load.

## Priority
Medium

## Scope
- **In-Scope**: Add `close()` method to `RepositoryState`; add context manager support (`__enter__`/`__exit__`); ensure `git.Repo` is closed after pipeline completion
- **Out-of-Scope**: Changes to GitPython's `git.Repo` behavior; changes to the snapshot capture logic itself
- **Dependencies**: N/A: none

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

## Reason for Change
Holding a live `git.Repo` reference without cleanup violates the principle of least resource retention. The snapshot captures immutable state; the `git.Repo` object is only needed during the pipeline execution, not after.

## Implementation Intent
1. Close the `git.Repo` reference after the pipeline completes, or
2. Use a weak reference pattern to allow garbage collection, or
3. Explicitly close the `git.Repo` in a `__del__` method or context manager.

## Requirements
- `REQ-001`: `RepositoryState` must have a `close()` method that closes the underlying `git.Repo`
- `REQ-002`: `RepositoryState` must support context manager pattern (`with RepositoryState.snapshot(...) as state:`)
- `REQ-003`: `git.Repo` file descriptors must be released after the pipeline completes

## Implementation Target Files
**Freeze status**: Frozen

This table is the canonical, frozen source of implementation scope for this Plan. Once
`Frozen`, `Implementation steps`, `Acceptance criteria`, and every downstream
`plan-to-implementation-procedure` document MUST reference file paths only from this
table — no other file may be treated as a modification target.

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| scripts/mcp_servers/git/repository_state.py | Modify | Add `close()` method and context manager support | REQ-001, REQ-002 | Confirmed: `_repo` at line 43 is never explicitly closed; `snapshot()` at lines 58-87 creates `git.Repo` without cleanup (checked in Step 3) | Unit test for `close()` method | Needs confirmation |

Rules (see `rules/workflow-lifecycle.md` Implementation Target Files Validation (Plan Freeze) for the full validation procedure):
- One row per file. A directory, glob pattern (`*`, `**`), component/module name, file
  group, or a vague phrase (e.g. "related files", "as necessary", "etc.") MUST NOT
  appear as a row — list each file individually by its exact repository-relative path.
- Record a test, configuration, schema, migration, deployment, or documentation file as
  its own row when it requires modification — do not fold it into the row for the
  source file it accompanies.
- `Validation Status` is `Verified` or `Needs confirmation` per row; every row must be
  `Verified` before this section may be marked `Frozen`.

## Reference Files
Files that must be read to implement the targets above, but MUST NOT be modified. Same
one-file-per-row discipline as `Implementation Target Files` above — no directories,
glob patterns, components, file groups, or vague phrases.

| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| scripts/mcp_servers/git/write_protection_pipeline.py | Verify pipeline uses RepositoryState and needs cleanup integration | REQ-003 |
| tests/mcp_servers/git/test_repository_state.py | Verify existing RepositoryState usage patterns | REQ-001 |

## Acceptance Criteria
- `git.Repo` file descriptors are released after the pipeline completes (REQ-003)
- No file descriptor leaks under sustained load (REQ-003)
- Existing code paths that use `repo` property continue to work (REQ-002)

## Tests
- Unit test: verify `git.Repo` is closed after pipeline completion (REQ-003)
- Integration test: verify no file descriptor leak under sustained load (REQ-003)
- Regression test: ensure `repo` property still works for direct access (REQ-002)

## Documentation Impact
Update `RepositoryState` docstring to document the resource lifecycle and the need for explicit cleanup.

## Assumptions
- GitPython 3.x provides `git.Repo.close()` method for resource cleanup
- The existing `repo` property is used by downstream code and must be preserved
- Context manager pattern is preferred over `__del__` for deterministic cleanup

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | Does GitPython's `git.Repo` have a `close()` method? | Need to verify GitPython version compatibility | Check GitPython documentation | False |
| UNK-02 | Are there any code paths that retain `RepositoryState` beyond the request? | Need to check git-mcp server for long-lived RepositoryState references | Review git-mcp server code | False |

## Affected areas
`skills/DESIGN.md` Change-impact table, extended with `Churn (30d)` and `Bus Factor`
columns. The `File` column here MUST be a subset of `Implementation Target Files`'
rows — this table analyzes change-impact risk for those same files; it is not a
separate scope-of-record.

| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| scripts/mcp_servers/git/repository_state.py | Modify | Low | N/A | N/A | No impact |

## Design
- **Approach**: Add `close()` method to `RepositoryState` that calls `self._repo.close()` if `_repo` is not None; add context manager support (`__enter__`/`__exit__`) for deterministic cleanup
- **Rationale**: Context manager pattern is preferred over `__del__` for deterministic cleanup. The `close()` method allows callers to explicitly release resources when they're done with the `RepositoryState`.
- **Alternative considered**: Using weak references — this would allow garbage collection but doesn't provide deterministic cleanup, which is important for file descriptor management.

## Implementation steps
1. **Phase 1: Preparation**
   - [ ] Verify test file path exists under `tests/mcp_servers/git/` (Requirement ID: REQ-001; File Path: tests/mcp_servers/git/test_repository_state.py)
2. **Phase 2: Core Logic Implementation**
   - [ ] Add `close()` method to `RepositoryState` that calls `self._repo.close()` if `_repo` is not None (Requirement ID: REQ-001; File Path: scripts/mcp_servers/git/repository_state.py)
   - [ ] Add context manager support (`__enter__`/`__exit__`) to `RepositoryState` (Requirement ID: REQ-002; File Path: scripts/mcp_servers/git/repository_state.py)
   - [ ] Update `snapshot()` to return a context-managed object (Requirement ID: REQ-002; File Path: scripts/mcp_servers/git/repository_state.py)
   - [ ] Update `RepositoryState` docstring to document the resource lifecycle (Requirement ID: REQ-001; File Path: scripts/mcp_servers/git/repository_state.py)
3. **Phase 3: Testing & Verification**
   - [ ] Run lint/type checks on modified files (Requirement ID: REQ-001; File Path: scripts/mcp_servers/git/repository_state.py)

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| scripts/mcp_servers/git/repository_state.py | Unit test | uv run pytest tests/mcp_servers/git/test_repository_state.py -v | Test passes; git.Repo is closed after pipeline completion |
| scripts/mcp_servers/git/repository_state.py | Lint check | uv run ruff check scripts/mcp_servers/git/repository_state.py | Clean (no findings) |
| scripts/mcp_servers/git/repository_state.py | Type check | uv run mypy scripts/mcp_servers/git/repository_state.py | Clean (no type errors) |

## Risks
- **Risk**: Adding `close()` method may break existing code that relies on the `repo` property after the pipeline completes → **Mitigation**: Only call `close()` when explicitly requested; the `repo` property continues to work until `close()` is called
- **Risk**: Context manager pattern may require changes to all callers of `RepositoryState.snapshot()` → **Mitigation**: Provide both context manager and non-context manager usage patterns; document the recommended approach

## Execution Status

Table structure, status/type vocabulary, and general guidance: see
`templates/execution-status.md`. Default rows for a freshly generated Plan (replace
with the Plan's actual steps once Implementation steps are broken down):

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Phase 1: Preparation — verify test file path | Pending | — | — | |
| 2 | Phase 2: Core Logic — add close() and context manager | Pending | — | — | |
| 3 | Phase 3: Testing & Verification — add unit test and run checks | Pending | — | — | |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: issue-to-plan
- **Source issue**: issues/20261026-220730_mcp005-repositorystate-repo-no-cleanup.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261026-223348
- **Related target files**: scripts/mcp_servers/git/repository_state.py

### Requirement Traceability
See `templates/requirement-traceability.md` for the canonical column format.

| Requirement ID | Source Issue Section | Target File | Implementation Step | Acceptance Criterion | Test or Validation Item | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Problem, Acceptance Criteria | scripts/mcp_servers/git/repository_state.py | Phase 2 | close() method added | Unit test for close() method | Confirmed by repository evidence |
| REQ-002 | Problem, Acceptance Criteria | scripts/mcp_servers/git/repository_state.py | Phase 2 | Context manager support | Regression test for repo property | Confirmed by repository evidence |
| REQ-003 | Reason for Change, Acceptance Criteria | scripts/mcp_servers/git/repository_state.py | Phase 3 | File descriptors released | Integration test for FD leak | Needs confirmation |
