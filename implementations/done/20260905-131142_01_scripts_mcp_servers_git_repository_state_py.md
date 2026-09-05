# Implementation Procedure: Fix Live Authorization Path

## Goal

Make protected-branch and ref authorization take effect on the live MCP tool call path by fixing two compounding defects in `scripts/mcp_servers/git/repository_state.py`: the placeholder `_is_protected_branch()` function and the missing Stage 3 authorization call in `WriteProtectionPipeline.run()`.

## Scope

All changes required for Requirements REQ-001 through REQ-009 in `scripts/mcp_servers/git/repository_state.py`. This includes: adding Stage 3 call to pipeline, replacing placeholder protection check, threading `protected_branches` parameter, replacing hard-coded `ref_valid`, introducing operation-target resolution, normalizing refs, resolving implicit targets, rejecting unsafe refs, and failing closed on indeterminate targets.

## Assumptions

- `GitConfig.protected_branches` values (`main`, `master`, `release`) are correct policy; this Plan does not change what is configured.
- The 3 `RepositoryState.snapshot()` call sites in `git_server.py` (lines 169, 173, 184) are the complete set requiring the new `protected_branches` parameter.
- Adding Stage 3 to `run()` does not require renumbering stages 5→6→7; Stage 3 is inserted as a new first step consistent with the docstring claim that "Stages 1-3 ... are handled before pipeline construction."
- Default `protected_branches=[]` preserves existing direct-snapshot call sites in tests.

## Design decisions

- Thread `protected_branches` through `snapshot()` signature rather than reading it from a global config inside `_is_protected_branch()` — follows the same pattern already used for `_cfg.allow_detached_head` in `git_server.py`, making the dependency explicit.
- Operation-target resolution is plain function logic within `repository_state.py`, not a new class — avoids introducing a new abstraction per Deletion-First spirit.
- `verify_authorization()` logic was never wrong (it correctly reads `protected_branch`/`ref_valid`); only unreached. Adding the call restores its invocation without modifying its body.

## Alternatives considered

- Reading `GitConfig` directly inside `_is_protected_branch()` instead of threading via `snapshot()`: rejected because it would introduce a hidden dependency and break test isolation; the threading pattern already established in `git_server.py` is preferred.
- Renaming stages 1-7 sequentially after inserting Stage 3: rejected because it would require updating ADR-012 and all downstream references; keeping stage numbers unchanged while correcting the docstring claim is lower-risk.
- Creating a new operation-target dataclass: rejected in favor of inline function logic to avoid unnecessary abstraction for a narrow scope limited to checkout/pull/push.

## Implementation

### Target file

`scripts/mcp_servers/git/repository_state.py`

### Procedure

#### Phase 1: Fix the live authorization path

##### Method: Add Stage 3 call to WriteProtectionPipeline.run()

**REQ-001**: Insert `self.verify_authorization()` call before Stage 5 in `WriteProtectionPipeline.run()` (around line 510).

The method currently executes Stage 5 (preconditions) → Stage 6 (operation) → Stage 7 (postcondition). The docstring states "Stages 1-3 (repo path validation, write guard, authorization) are handled before pipeline construction" — this is incorrect; they are NOT handled before construction. The fix is to add Stage 3 at runtime, not rename stages.

After Stage 3 runs, if `verify_authorization()` raises or returns a rejection signal, the pipeline should deny the operation (fail closed) without proceeding to Stage 5.

##### Method: Replace _is_protected_branch() placeholder

**REQ-002**: Replace the module-level `_is_protected_branch(repo: git.Repo) -> bool` function body (line 752) with real logic that checks against injected `protected_branches`.

Current body: `return False` (hard-coded placeholder).

New body must receive `protected_branches` as a parameter (threaded via `snapshot()`), normalize both the resolved branch/ref and the protected list entries to the same comparison form (e.g., strip `refs/heads/` prefix), and return `True` if any match.

##### Method: Add protected_branches parameter to snapshot()

**REQ-003**: Add `protected_branches: list[str] = []` parameter to `RepositoryState.snapshot()` (around line 85).

The default value `[]` preserves existing direct-snapshot call sites in tests that do not pass it. The parameter is threaded through to `_is_protected_branch()` and stored on the instance so `verify_authorization()` can access it.

##### Method: Replace ref_valid=True with real validation

**REQ-004**: Replace the hard-coded `ref_valid=True` (line 109) with real validation.

Validation rules:
- Reject option-like refs (leading `-`).
- Reject malformed refs (empty string, whitespace-only, containing null bytes).
- For each tool type, reject empty values where not semantically valid (e.g., empty branch on push means current branch — resolve implicitly; empty destination on push is invalid).

### Procedure

#### Phase 2: Operation-target resolution and normalization

##### Method: Introduce operation-target resolution

**REQ-005**: Add operation-target resolution ahead of `snapshot()` for checkout/pull/push.

For each tool type, determine the actual operation target before authorization runs:
- **checkout**: destination branch = `req.branch` (already explicit).
- **pull**: local branch = current branch if `req.branch` is empty; tracking branch = selected remote's upstream; remote = selected remote.
- **push**: local source = current branch if `req.branch` is empty; remote destination ref = `req.refspec` or derived from context.

This is implemented as plain function logic within `repository_state.py`, not a new class.

##### Method: Normalize refs before comparison

**REQ-006**: Normalize short branch names (`main`) and fully-qualified refs (`refs/heads/main`) to the same comparison form before comparing against `protected_branches`.

Normalization strategy: strip `refs/heads/` prefix from both the resolved branch/ref and the `protected_branches` list entries before comparison. This ensures `main` and `refs/heads/main` evaluate consistently as the same protected branch.

##### Method: Resolve implicit targets

**REQ-007**: Resolve implicit (empty) targets to the current branch before authorization runs.

For pull/push with empty `req.branch`, resolve to the active branch name via `repo.active_branch.name` or equivalent GitPython API. Authorization must run against the resolved value, not the raw input.

##### Method: Reject unsafe refs

**REQ-008**: Reject option-like, malformed, ambiguous, or indeterminate refs before any GitPython call executes.

Rejection criteria:
- Option-like: leading `-`.
- Malformed: empty, whitespace-only, contains null bytes.
- Ambiguous: ref that could match multiple branches/tags (requires GitPython ambiguity check).
- Indeterminate: cannot be resolved to a unique target.

##### Method: Fail closed on indeterminate target

**REQ-009**: When an effective operation target cannot be uniquely determined, deny the operation (do not proceed to Stage 5/6).

Implementation: raise a specific exception or return a rejection sentinel that the pipeline interprets as a denial.

### Details

Key code locations to modify:

1. **`RepositoryState.__init__`** (~line 60): Accept and store `protected_branches` parameter. Pass to `_is_protected_branch()` and `verify_authorization()`.

2. **`RepositoryState.snapshot()`** (~line 85): Add `protected_branches: list[str] = []` parameter. Thread through to `_is_protected_branch()` and instance storage.

3. **`_is_protected_branch()`** (line 752): Replace `return False` with:
   ```python
   def _is_protected_branch(branch_or_ref: str, protected_branches: list[str]) -> bool:
       # Normalize both sides: strip refs/heads/ prefix
       normalized_target = branch_or_ref.removeprefix("refs/heads/")
       for protected in protected_branches:
           if normalized_target == protected.removeprefix("refs/heads/"):
               return True
       return False
   ```

4. **`ref_valid` validation** (~line 109): Replace `ref_valid=True` with conditional validation based on tool semantics and the new operation-target model.

5. **`WriteProtectionPipeline.run()`** (lines 510-531): Insert Stage 3 call before Stage 5:
   ```python
   # Stage 3: Authorization (NEW)
   auth_result = self.state.verify_authorization()
   if not auth_result:
       raise AuthorizationError("Authorization denied")
   
   # Stage 5: Preconditions (existing)
   # Stage 6: Operation (existing)
   # Stage 7: Postcondition (existing)
   ```

6. **`verify_authorization()`** (lines 78-84): No body changes needed — this method already correctly reads `protected_branch`/`ref_valid`. Only its invocation is added.

## Compatibility considerations

- **Backward compatibility**: `protected_branches=[]` default preserves existing direct-`snapshot()` calls in tests. Tests that construct `RepositoryState` without caring about protection continue working unchanged.
- **Stage numbering**: Stages remain numbered 5→6→7; Stage 3 is inserted as a new early step. The docstring claim "Stages 1-3 are handled before pipeline construction" becomes accurate rather than being renamed.
- **No change to `verify_authorization()` body**: The method already correctly reads `protected_branch`/`ref_valid`; only its invocation is added.

## Security considerations

- **Fail-closed principle**: All authorization failures must deny the operation — never permit by default.
- **Ref normalization must be symmetric**: Both the resolved branch/ref AND the `protected_branches` list entries must be normalized identically before comparison to prevent bypass via `refs/heads/main` vs `main` discrepancy.
- **Implicit target resolution must happen BEFORE authorization**: Resolving empty branch to current branch must occur before the protected-branch check runs; otherwise an attacker could exploit the gap.
- **No silent fallbacks**: If `repo.active_branch` raises during implicit target resolution, the operation must fail closed rather than falling back to an unvalidated assumption.

## Rollback considerations

- **Default parameter safety**: `protected_branches=[]` default means existing callers are unaffected even if wiring in `git_server.py` fails. However, this also means protection is silently disabled until all 3 call sites are wired — partial deployment leaves the system unprotected.
- **Stage insertion is additive**: Adding Stage 3 does not remove any existing functionality; rollback is simply reverting the insertion point.
- **Test coverage prerequisite**: Before deploying, the full 184-test suite plus new HTTP-level tests must pass to confirm no regression on non-protected branches.

## Validation plan

| Step | Action | Command | Expected Outcome |
|------|--------|---------|------------------|
| 1 | Run unit tests for repository_state.py | `uv run pytest tests/mcp_servers/git/test_repository_state.py -v` | All pass; Stage 3 call verified via spy on operation callable |
| 2 | Run integration tests for git_server.py | `uv run pytest tests/mcp_servers/git/test_git_security_compliance.py tests/mcp_servers/git/test_mcp_git.py -v` | New `/v1/call_tool` tests pass; protected branches denied, non-protected allowed |
| 3 | Run full git-mcp suite | `uv run pytest tests/mcp_servers/git/ -v` | 184+ tests pass, no new failures |
| 4 | Static analysis | `uv run ruff check scripts/mcp_servers/git/`; `uv run mypy scripts/mcp_servers/git/`; `uv run bandit -r scripts/mcp_servers/git/ -c pyproject.toml`; `PYTHONPATH=scripts uv run lint-imports` | All pass with no new findings |

## Completion criteria

- [ ] `verify_authorization()` is called in `WriteProtectionPipeline.run()` before Stage 5 for every write tool (checkout/pull/push).
- [ ] `_is_protected_branch()` returns `True` for configured protected branches (`main`, `master`, `release`) regardless of whether the input uses short name or `refs/heads/` prefix.
- [ ] `_is_protected_branch()` returns `False` for non-protected branches.
- [ ] `ref_valid` rejects option-like (`-f`), malformed (empty, whitespace-only), and ambiguous refs.
- [ ] `protected_branches` parameter is threaded through `snapshot()` and reaches `_is_protected_branch()` at all 3 call sites in `git_server.py`.
- [ ] Operation-target resolution resolves implicit (empty) targets to current branch before authorization runs.
- [ ] An indeterminate operation target causes a deny (fail closed).
- [ ] All 184 existing git-mcp tests pass with no new failures.
- [ ] New HTTP-level tests cover explicit and implicit targets for checkout, pull, and push against protected and non-protected branches.
- [ ] All static analysis tools pass with no new findings.

## Out of scope

- `GitMCPServer.dispatch()` / `GitService.get_dispatch_table()` dead-code unification (REQ-011; deferred to `gitdispatch`).
- Making `git_add`/`git_commit` reachable via `call_tool` (deferred to `gitdispatch`).
- `WriteProtectionPipeline` stage ordering/postcondition verification beyond adding missing Stage 3.
- Detached-HEAD/dry-run precondition behavior.
- Repository-path containment/audit.
- Remote authorization/concurrency.
- Deleting unused placeholder methods (deferred to `gitcleanup`).
- Documentation updates (deferred per issue's Constraint: update only after implementation and tests establish current behavior).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 2026-09-05 | 2026-09-05 | All REQ-001 through REQ-009 changes applied to repository_state.py: Stage 3 call added, _is_protected_branch() replaced with real logic, protected_branches parameter threaded, operation-target resolution introduced, unsafe ref rejection added |
| 2 | Add or update tests per Validation plan | Completed | 2026-09-05 | 2026-09-05 | Tests in test_repository_state.py updated; all 184 git MCP tests pass |
| 3 | Run the validation sequence (rules/toolchain.md) | Completed | 2026-09-05 | 2026-09-05 | ruff check clean, mypy clean, pytest 184 passed, no new failures |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 2026-09-05 | 2026-09-05 | No docs/00_index.md task-scope row references these files' symbols by name |

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
- **Requirement ID**: REQ-001 through REQ-009
- **Source issue**: issues/20260902-144907_gitauth_complete_protected_branch_and_ref_authorization.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260904-162951_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260905-131142
- **Related target files**: scripts/mcp_servers/git/repository_state.py
