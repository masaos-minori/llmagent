# Implementation Procedure

## Goal

Harden the git-mcp write path in `GitService` (`scripts/mcp_servers/git/git_service.py`): reject force-push ref forms via an allow-list, evaluate the protected-branch rule against the operation destination, feed the write-protection pipeline its real inputs, report the actually-rejected branch name, and drop the deprecated `RepoValidationResult` container. Driven by `REQ-001` (allow-list ref validation), `REQ-002` (destination-based protected-branch decision), `REQ-005` (pipeline inputs + single snapshot), `REQ-007` (actual branch name in errors), and `REQ-008` (remove `RepoValidationResult`).

## Scope

Modifies only `scripts/mcp_servers/git/git_service.py`. Cross-file effects are dependencies, not targets:

- `scripts/mcp_servers/git/repository_state.py` — `verify_authorization()` becomes destination-aware and its in-pipeline snapshots are removed (`implementations/20261007-170610_02_scripts_mcp_servers_git_repository_state_py.md`, REQ-002/003/006). This document only FORWARDS inputs to `WriteProtectionPipeline.run()`; it does not change the pipeline body.
- `scripts/mcp_servers/git/git_tools.py`, `git_models.py`, `format_output.py` — `branch` becomes required (REQ-004); handled in their own documents.
- `tests/mcp_servers/git/test_git_service_dispatch.py`, `test_repository_state.py` — new/updated tests; own documents.

## Assumptions

- The allow-list applies to write-operation `branch`/`remote` arguments only; read-tool ref args (`git_log.branch`, `git_diff.commit`, `git_show.ref`) keep the current option-injection-only `_validate_ref()` so read behavior does not regress (`git_show` defaults `ref="HEAD"`, which the allow-list would reject).
- `requested_branch` is `None` for `git_add`/`git_commit` (destination = current HEAD) and `req.branch` for `git_checkout`/`git_pull`/`git_push` (destination = the named branch).
- `RepositoryState.snapshot()` is already taken once in `_run_tool()` (line 234); the second/third snapshots live inside `run()` and are removed by the repository_state document.

## Design decisions

- **Separate validators, shared entry.** Keep `_validate_ref()` as the read-tool option-injection check; add `_validate_ref_allowlist()` for write `branch`/`remote`. One helper per concern avoids threading a mode flag through the read path and keeps the read calls byte-for-byte unchanged.
- **Destination computed at the handler, consumed at Stage 3.** Each write handler passes `requested_branch` (and `active_ref`, `protected_branches`) into `_run_tool()` → `run()`. The destination comparison itself stays in `verify_authorization()` (repository_state), consistent with "Stage 3 is the single authoritative protected-branch check".
- **`_validate_repo()` returns `(ok, error)`.** Replaces the `RepoValidationResult` dataclass with a plain tuple; `_run_tool()` consumes it identically (`if not ok: raise ValueError(err)`). No behavior change beyond dropping the deprecated wrapper.
- **Retain tested guards.** `_is_safe_ref`, `_check_protected_branch`, and `_check_repo_path()` are left in place (resolved UNK-03; they have test callers and are dead on the request path).

## Alternatives considered

- **Single `_validate_ref()` with a `write_mode: bool` param.** Rejected: it forces every read call site to pass a flag and risks regressing read tools; a separate helper isolates the write contract.
- **Inline repo/write checks into `_run_tool()` and delete `_validate_repo()`.** Rejected: `_validate_repo()` is referenced by `test_git_service_dispatch.py` (REQ-007 regression) and `test_git_security_compliance.py`; keeping it (rewritten) preserves those tests.
- **Fix the hard-coded `'main'` in `_check_protected_branch()` for REQ-007.** Rejected: it is dead code with a locked assertion (`test_check_protected_branch` expects the literal `"[DENIED] 'main' is a protected branch"`); changing it breaks the test for zero functional gain. REQ-007 applies to the live paths only.

## Implementation

### Target file

`scripts/mcp_servers/git/git_service.py`

### Procedure

1. Add the allow-list validators (REQ-001).
2. Route the allow-list through the write handlers' `branch`/`remote` checks; leave read handlers on `_validate_ref()` (REQ-001).
3. Forward pipeline inputs from `_run_tool()` and each write handler (REQ-002, REQ-005).
4. Report the actual rejected branch name in the live protected-branch and ref errors (REQ-007).
5. Remove `RepoValidationResult` and rewrite `_validate_repo()` + its consumer (REQ-008).

### Method

#### Step 1 — Allow-list validators (REQ-001)

Add two methods to `GitService`, adjacent to `_validate_ref()` (line 122):

- `_validate_ref_allowlist(self, ref: str) -> tuple[bool, str]` — returns `(False, msg)` when `ref` contains any of `+ : ^ ~ ? * [` backslash, `..`, `@{`, any whitespace, or a control character; starts with `refs/`; or equals `HEAD`; else `(True, "")`. Accept simple names like `main`, `feature/x`. Return a message naming the ref: `f"[DENIED] Ref {ref!r} is not a valid simple branch name"`.
- `_validate_remote(self, remote: str) -> tuple[bool, str]` — accepts `[A-Za-z0-9._-]+` only; else rejects naming the remote.

Model the reject set on `git check-ref-format --branch` (see Plan `Design` > "Ref validation model"). Do NOT modify `_validate_ref()` — read tools depend on its current behavior.

#### Step 2 — Route through write handlers (REQ-001)

In the three write handlers, replace the `_validate_ref()` call on `req.branch` with `_validate_ref_allowlist(req.branch)`, and the `_validate_ref()` call on `req.remote` with `_validate_remote(req.remote)`:

- `git_checkout` (line 349): `self._validate_ref(req.branch)` → `self._validate_ref_allowlist(req.branch)`.
- `git_pull` (lines 382, 388): `req.branch` → `_validate_ref_allowlist`; `req.remote` → `_validate_remote`.
- `git_push` (lines 416, 422): `req.branch` → `_validate_ref_allowlist`; `req.remote` → `_validate_remote`.

Leave `_validate_ref()` calls on `git_log.branch` (268), `git_diff.commit` (284), `git_show.ref` (304) unchanged.

#### Step 3 — Forward pipeline inputs (REQ-002, REQ-005)

- Extend `_run_tool()` signature (line 214) to accept `requested_branch: str | None = None` and `protected_branches: list[str] | None = None` (keep existing `active_ref`, `dry_run`).
- Update the `pipeline.run(...)` call (lines 242-247) to forward all three: `requested_branch=requested_branch, protected_branches=self._protected_branches, active_ref=active_ref`. The signature already accepts them (repository_state line 298-306); they currently default to `None`/`""`.
- In each write handler, pass `requested_branch` into `_run_tool()`:
  - `git_checkout` (after 372): `requested_branch=req.branch`.
  - `git_pull` (after 405): `requested_branch=req.branch`.
  - `git_push` (after 439): `requested_branch=req.branch`.
  - `git_add` / `git_commit`: pass nothing (defaults to `None` → Stage 3 evaluates current HEAD). Keep their existing `active_ref` (unset → `""`).

`active_ref` is already passed for checkout/pull/push (`active_ref=req.branch`); leave it.

#### Step 4 — Actual branch name in errors (REQ-007)

- In `_validate_protected()` (line 130), change the protected-branch message from `"[DENIED] branch is a protected branch"` to `f"[DENIED] {branch!r} is a protected branch"`. This is the live pre-pipeline path for pull/push/checkout.
- The allow-list/ref messages from Step 1 already name the ref.
- Do NOT touch `_check_protected_branch()` (line 200): dead code, retained, locked test.

#### Step 5 — Remove `RepoValidationResult` (REQ-008)

- Delete the `RepoValidationResult` dataclass (lines 56-70, including its `__post_init__` `DeprecationWarning`).
- Rewrite `_validate_repo()` (lines 109-120) to return `tuple[bool, str]`:

  ```python
  async def _validate_repo(self, req_repo_path: str, tool_name: str) -> tuple[bool, str]:
      ok, err = self._is_within_allowed_paths(req_repo_path)
      if not ok:
          return False, err
      if tool_name in _WRITE_TOOLS and self._read_only:
          return False, "[DENIED] git-mcp is configured with read_only=true"
      return True, ""
  ```

- Update the consumer in `_run_tool()` (lines 231-233):

  ```python
  ok, err = await self._validate_repo(repo_path, tool_name)
  if not ok:
      raise ValueError(err)
  ```

- Confirm no other caller references `RepoValidationResult` before deleting (re-run `rg RepoValidationResult scripts/ tests/`).

## Compatibility considerations

- Read-tool ref validation is unchanged; `git_show.ref="HEAD"` and tag refs still pass via `_validate_ref()`.
- `branch` becoming required (REQ-004, in `git_tools.py`/`git_models.py`) means `git_pull`/`git_push` without `branch` now fail schema validation; affected test constructions using `branch=""` must be updated (own documents).
- Retained guards keep their existing public signatures and tests intact.

## Security considerations

- The allow-list is stricter than the old reject-list: it rejects `HEAD`, `refs/...`, and structural tokens, closing the force-push-via-`branch` path ADR-012 exists to prevent. It applies only to write `branch`/`remote`, never to read refs.
- Destination-based protection (forwarded `requested_branch`) makes Stage 3 reject a protected destination even if the pre-pipeline `_validate_protected()` were bypassed (REQ-002). Fail-closed: an empty/`None` `requested_branch` for commit/add falls back to the current-HEAD check.
- Removing `RepoValidationResult` removes a deprecation surface but changes no access decision.

## Rollback considerations

- Revert the single commit touching `git_service.py`. The `_validate_ref()` read path is untouched, so read tools are unaffected by any partial change.
- If the allow-list over-rejects a legitimate simple name, narrow the reject set to the Plan's enumerated tokens plus structural rules (`git check-ref-format --branch`); do not widen back to the old reject-only check.

## Validation plan

| Target | Strategy | Command | Expected |
|---|---|---|---|
| Allow-list validator | Unit | `uv run pytest tests/mcp_servers/git/test_git_service_dispatch.py -v` | `+main`, `feature:main`, `HEAD:main`, `refs/heads/main`, `main~1`, `main..`, `a b`, `a\b`, `a@{1}`, `[x]`, `\0`, `HEAD` rejected; plain `main`/`feature/x` passes; read-tool `ref="HEAD"` still passes |
| Pipeline inputs | Integration | `uv run pytest tests/mcp_servers/git/test_repository_state.py -v` | `run()` receives `protected_branches`/`requested_branch`/`active_ref`; protected destination rejected at Stage 3 |
| `RepoValidationResult` removal | Unit | `uv run pytest tests/mcp_servers/git/ -k "repo or dispatch"` | No `RepoValidationResult` reference remains; `_validate_repo` regression test passes |
| Whole git-mcp module | Full suite | `uv run pytest tests/mcp_servers/git/ -v` | No new failures |
| Toolchain | Static/type/security | `uv run ruff check scripts/`, `uv run mypy --no-namespace-packages scripts/`, `PYTHONPATH=scripts uv run lint-imports`, `uv run bandit -r scripts/ -c pyproject.toml` | Clean per `rules/toolchain.md` |

## Completion criteria

- Every malicious push ref form is rejected by `_validate_ref_allowlist()` before any GitPython call; simple names pass; read-tool refs are unaffected.
- Each write handler forwards the correct `requested_branch` (named branch for pull/push/checkout, `None` for commit/add) and `protected_branches`/`active_ref` to `run()`.
- Live protected-branch and ref error messages name the actually-rejected branch; `_check_protected_branch()` is unchanged.
- `RepoValidationResult` is fully removed; `_validate_repo()` returns `(ok, error)` and `_run_tool()` consumes it.
- Full git-mcp suite and toolchain pass with no new failures.

## Out of scope

- `repository_state.py` changes (destination-aware `verify_authorization()`, single-snapshot) — own document.
- `branch` required in schema/models and `format_push()` fallback — REQ-004, own documents.
- Audit record / error-path changes (separate issue).
- `_check_repo_path()` vs `_is_within_allowed_paths()` reconciliation (`Needs confirmation`).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | REQ-001/002/005/007/008 in git_service.py |
| 2 | Add or update tests per Validation plan | Pending | — | — | dispatch + repository_state docs own the test rows |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | N/A: doc updates are Rows 8-10 |

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
- **Requirement ID**: `REQ-001` (allow-list ref validation for write `branch`/`remote`), `REQ-002` (route protected-branch decision to destination), `REQ-005` (forward pipeline inputs + single snapshot), `REQ-007` (report actual rejected branch name), `REQ-008` (remove `RepoValidationResult` + rewrite `_validate_repo`)
- **Source issue**: `issues/20261007-153840_gitref01_fix-git-mcp-ref-validation-and-protected-branch-check.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261007-162035_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261007-170610
- **Related target files**: `scripts/mcp_servers/git/git_service.py`
