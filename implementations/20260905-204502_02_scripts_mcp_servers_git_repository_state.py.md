## Goal
Add the URL-based remote-resolution/normalization/credential-redaction helper
(`REQ-001`, `REQ-003`), a per-canonical-repository-path lock registry serializing
concurrent writes (`REQ-005`), and a HEAD-identity re-check immediately before the
mutating Git call (`REQ-006`), all inside `WriteProtectionPipeline`/`RepositoryState`
— the sole owner of both.

## Scope
- In scope: a remote-URL resolve/normalize/redact helper function; a process-wide
  `dict[str, asyncio.Lock]` registry keyed by canonical repo path, acquired/released
  around `WriteProtectionPipeline.run()`'s authorization-through-execution window;
  re-capturing HEAD identity immediately before Stage 6's `op()` call and rejecting on
  drift; an inline code comment documenting the lock's process-local limitation
  (`REQ-007`).
- Out of scope: reading `GitConfig.allowed_remote_urls` and rejecting an
  unauthorized remote (`REQ-004`, lives in `format_output.py` — this file only
  provides the resolve/normalize/redact primitive that row consumes); consuming
  `gitauth`'s operation-target model (`REQ-009`, also a `format_output.py` concern).

## Assumptions
- `REQ-009`'s dependency (`gitauth`'s structured operation-target model,
  `plans/20260904-162951_plan.md` REQ-005) has not landed in the codebase as of this
  writing — confirmed via `rg -n "selected_remote|OperationTarget|remote_destination_ref"
  scripts/mcp_servers/git/` returning no matches. This file's helper (resolve/
  normalize/redact by remote *name*) does not itself depend on that model; only
  `format_output.py`'s consumption of it (REQ-009) does, per the Plan's own Risks
  section mitigation ("re-verify gitauth's actual landed interface immediately before
  implementing REQ-009").
- The lock scope is process-local (`asyncio.Lock`), per the Plan's UNK-01 resolution
  (default, since git-mcp runs as a single FastAPI process per
  `MCPServer.run_http()` — no multi-worker deployment evidence found).

## Design decisions
- **Lock acquisition lives entirely inside `WriteProtectionPipeline.run()`**, keyed by
  `self._state.path` (already the canonical, resolved repo path captured at
  `RepositoryState.snapshot()` time). `run()` is currently `def run(` (sync, called
  as `pipeline.run(req.name, handler)` without `await` from `git_server.py`'s
  `_dispatch_git_tool`) — to avoid any caller-side signature change (`git_server.py`
  is not an `Implementation Target Files` row), the registry uses `threading.Lock`
  (not `asyncio.Lock`; the Plan's REQ-005 names `asyncio.Lock` only as an example of
  "a process-wide dict[...]", not a hard requirement), acquired via a plain `with
  _get_repo_lock(path):` block wrapping `run()`'s body — this requires no change to
  `run()`'s signature or any caller.
- **HEAD-identity re-check (`REQ-006`) lives inside `run()`, immediately before Stage
  6's `op()` call** — re-run `RepositoryState.snapshot(self._state.path,
  protected_branches=..., active_ref=...)` (or a lighter HEAD-only re-read) and
  compare `head_type`/`active_branch` against `self._state`'s values captured at
  construction; reject with a new `"Stage 5b"` (or fold into Stage 5) result on
  mismatch. This is self-contained: no new parameter is needed from the caller since
  `self._state` already carries the authorized-time identity.
- **Redaction helper is purpose-built**, not a reuse of `scripts/shared/logger.py`'s
  `register_secret` (that mechanism redacts registered secret *values* from log
  records; here the input is an arbitrary remote URL whose credential portion must be
  stripped before it is ever stored in an audit dict or raised in an exception
  message) — a small regex against the `scheme://user:token@host/...` shape,
  replacing the `user:token@` (or `user@`) segment with `***@`.

## Alternatives considered
- Threading `allowed_remote_urls`/lock state through `git_server.py`'s call site (as
  `allow_detached_head` is threaded into `format_checkout` today) was considered and
  rejected for the *lock and HEAD-recheck* concerns specifically: `git_server.py` is
  not an `Implementation Target Files` row in this Plan, and both concerns can be
  made fully self-contained within `WriteProtectionPipeline.run()` without any caller
  change, so no additional-target-file discovery applies to this row.
- `asyncio.Lock` (the Plan's example primitive) was considered and rejected in favor
  of `threading.Lock`: `run()` is called synchronously (no `await`) from
  `git_server.py`'s async `_dispatch_git_tool` (confirmed via `rg -n "result =
  pipeline.run"` showing no `await`), so introducing `asyncio.Lock` would require
  making `run()` `async def` and adding `await` at that call site — an edit to a file
  outside this Plan's frozen scope. `threading.Lock` serializes correctly without any
  signature change.
- A cross-process lock (file lock) for `REQ-005` was considered and rejected per the
  Plan's own Design/UNK-01 resolution — no evidence of a multi-worker deployment.

## Implementation
### Target file
`scripts/mcp_servers/git/repository_state.py`

### Procedure
1. Add a module-level lock registry and a `_get_repo_lock(path: str) -> asyncio.Lock`
   helper near the top of the file (after the existing module-level `logger =
   logging.getLogger(__name__)` at line 45).
2. Add a `_resolve_remote_url(repo: git.Repo, remote_name: str) -> str | None` helper
   (returns `None` if the remote does not exist) and a `_redact_remote_url(url: str)
   -> str` helper, near `_is_protected_branch`/`_validate_ref` (module-level helpers
   already used by `RepositoryState.snapshot()`).
3. In `WriteProtectionPipeline.run()` (line 547), wrap the body in `with
   _get_repo_lock(self._state.path):` (`threading.Lock`, no signature change to
   `run()` — see Alternatives considered).
4. Immediately before line 568's `# Stage 6: Execute the operation`, add the
   HEAD-identity re-check: re-snapshot and compare against `self._state`.

### Method
- Reuse `RepositoryState.snapshot()` (already the single source of truth for HEAD
  identity capture, line 85) for the re-check rather than a second, independent
  HEAD-reading code path.
- Reuse `git.Repo`'s already-open handle (`state.repo`, via the `repo` property at
  line 124) for remote resolution — `repo.remotes[name].url` per the Plan's
  Implementation intent — wrapping the `IndexError`/lookup failure as "remote
  unknown" rather than letting it propagate.

### Details
- `_resolve_remote_url`: `repo.remotes[name].url if name in [r.name for r in
  repo.remotes] else None` (or `try/except IndexError`) — normalize via a simple
  scheme+host+path lowercase-host comparison (exact normalization rule left to
  implementation time; note as a Non-blocking evidence gap below).
- `_redact_remote_url`: regex `re.sub(r"://[^@/]+@", "://***@", url)`.
- Lock registry: `_repo_locks: dict[str, threading.Lock] = {}` plus a single
  `_registry_guard = threading.Lock()` held only while getting-or-creating a path's
  entry (to avoid two threads creating distinct `Lock` objects for the same path
  under concurrent first access), released immediately after — the per-path lock
  itself is then held for the full `run()` body.
- HEAD re-check: compare `pre_state.head_type`/`pre_state.active_branch` (captured at
  Stage 4, i.e. `self._state`) against a fresh `RepositoryState.snapshot(self._state.path,
  protected_branches=protected_branches, active_ref=active_ref)` taken just before
  Stage 6; reject via `PipelineResult.reject(self._state, "Stage 5b", ...)` on
  mismatch (introduces a new stage label; document it alongside the existing Stage
  3/5/6/7 docstring at line 531).
- REQ-007: add an inline comment on the lock registry declaration, e.g. "# This lock
  is process-local: it does not constrain a `git` process running outside this
  MCP server (e.g. a human's local `git` CLI) — see Plan
  plans/20260904-192131_plan.md REQ-007."
- Classify as **Non-blocking** (per Step 3c) and proceed: the exact URL
  normalization rule (case-folding, trailing-`.git`, SSH `git@host:path` vs.
  `ssh://` forms) is not fully specified by the Plan and should be confirmed against
  `gitauth`'s landed interface (REQ-009 dependency, consumed in `format_output.py`)
  before finalizing.

## Compatibility considerations
- `WriteProtectionPipeline.run()`'s signature is unchanged (still sync `def run(`) —
  no caller-side edit is needed anywhere, including `git_server.py`.
- Existing callers of `RepositoryState.snapshot()` are unaffected — no signature
  change to that method.

## Security considerations
- Credential redaction (`REQ-003`) must run before the resolved URL reaches any
  logger call, exception message, or the `audit()` dict (Stage 8) — the redaction
  helper must be applied at the point of resolution, not deferred to a later
  formatting step, to avoid an unredacted value transiently existing in a variable
  that a future change might log.
- The lock registry is an unbounded `dict` keyed by repo path — acceptable since
  `allowed_repo_paths` already bounds the set of distinct paths this server will ever
  see (fixed by config, not attacker-controlled), so this is not a memory-exhaustion
  vector.

## Rollback considerations
- The lock, HEAD-recheck, and redaction helpers are additive and independently
  revertable; reverting the lock alone re-exposes the pre-existing (already present)
  concurrent-write race — no new regression beyond restoring current behavior.

## Validation plan
- `uv run pytest tests/mcp_servers/git/test_repository_state.py -v` (existing suite,
  per Plan's Validation plan row) plus new cases for `_resolve_remote_url`/
  `_redact_remote_url` and lock get-or-create idempotency.
- `uv run pytest tests/mcp_servers/git/test_git_concurrency.py -v` (new file, separate
  row) exercises the lock/HEAD-recheck behavior end-to-end.
- `uv run ruff check`, `uv run mypy`, `uv run bandit -r scripts/mcp_servers/git/ -c
  pyproject.toml`, `PYTHONPATH=scripts uv run lint-imports` per the Plan's Tests
  section.

## Completion criteria
- A remote name resolves to its current URL with credentials redacted before use in
  any log/audit field; concurrent writes to the same repo path are serialized via the
  new lock while independent repo paths are not; a HEAD-identity change between
  authorization and Stage 6 execution is rejected; the lock's process-local
  limitation is documented inline.

## Out of scope
- Reading `GitConfig.allowed_remote_urls` and the actual authorization
  accept/reject decision (`REQ-004`) — that logic lives in `format_output.py`'s row,
  which consumes this file's resolve/redact helper.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | |

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
- **Requirement ID**: REQ-001, REQ-003, REQ-005, REQ-006, REQ-007
- **Source issue**: issues/20260902-144912_gitremote_define_remote_authorization_and_concurrency_control.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260904-192131_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260905-204502
- **Related target files**: scripts/mcp_servers/git/repository_state.py
