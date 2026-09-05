## Goal
Add the remote authorization check (`REQ-004`) to `format_pull()`/`format_push()`
before their mutating GitPython calls, and include the redacted resolved remote
identity in the audit-facing return value (`REQ-008`).

## Scope
- In scope: `format_pull()` (line 160) and `format_push()` (line 181) only — resolve
  `req.remote`'s current URL via `repository_state.py`'s new helper (a separate row),
  check it against `GitConfig.allowed_remote_urls`, reject before the mutating call
  if unauthorized.
- Out of scope: the resolve/normalize/redact helper implementation itself and the
  per-repo lock/HEAD-recheck (all in `repository_state.py`, a separate row); the
  `GitConfig.allowed_remote_urls` field definition (`git_models.py`, a separate row).

## Assumptions
- `REQ-009`'s dependency (`gitauth`'s structured operation-target model) has not
  landed in the codebase as of this writing (confirmed via `rg`, no
  `selected_remote`/`OperationTarget` symbols exist) — per the Plan's own Risk
  mitigation, the actual wiring of REQ-009 (consuming that model's "selected remote"/
  "remote destination ref" instead of `req.remote` directly) must be re-verified
  against `gitauth`'s landed interface at implementation time. Until then, `req.remote`
  (the field already validated by `_validate_ref`, per Background) is the best
  available "selected remote" input.

## Design decisions
- **`format_pull`/`format_push` resolve `GitConfig` internally** via
  `GitConfig.load()` (already an existing, idempotent entry point — see
  `git_models.py:63-65`) rather than requiring the caller (`git_server.py`, not an
  `Implementation Target Files` row) to thread `_cfg.allowed_remote_urls` through as
  a new parameter — unlike `allow_detached_head`, which `git_server.py`'s
  `_format_checkout` already threads explicitly from its module-level `_cfg`.
  Threading a new parameter here would require editing `git_server.py`'s
  `_format_pull`/`_format_push` static methods (lines 334-353) and their lambda call
  sites (lines 259-260) — out of this Plan's frozen scope, and, if instead given a
  default of `[]`, would silently reject every remote in production (since the real
  live-path caller would never pass the configured list) rather than actually
  enforcing `REQ-004` — a functional regression, not a safe default. Internal
  `GitConfig.load()` keeps the row self-contained and functionally correct.
- Authorization check placed immediately before the existing mutating call
  (`state._repo.git.fetch(...)`/`git.pull(...)` at line 164/168 for `format_pull`;
  `state._repo.git.push(...)` at line 187 for `format_push`) — reject before any
  GitPython call executes, consistent with `REQ-004`'s "cannot target an
  unauthorized remote" (AC-1).

## Alternatives considered
- Accepting `allowed_remote_urls`/`cfg` as an optional function parameter (defaulting
  to `None` → internally calling `GitConfig.load()` if not supplied) was considered
  as a middle ground for testability — adopted as part of Method below: the
  production call site (`git_server.py`) needs no change since it omits the optional
  arg, while tests can inject a `GitConfig` instance directly without touching disk.
- Threading via `RepositoryState` (extending `state` with a `cfg` attribute at
  snapshot time) was considered and rejected: `RepositoryState.snapshot()`'s
  signature change would also require a `git_server.py` call-site edit
  (`RepositoryState.snapshot(resolved, protected_branches=_cfg.protected_branches,
  active_ref=active_ref)`, lines 255/268) to pass `allowed_remote_urls` — same
  out-of-scope problem as the caller-threading alternative above.

## Implementation
### Target file
`scripts/mcp_servers/git/format_output.py`

### Procedure
1. Import `GitConfig` from `mcp_servers.git.git_models` (already imports several
   sibling classes from this module at lines 16-25).
2. In `format_pull()` (line 160-179) and `format_push()` (line 181-193), before the
   existing mutating call, resolve the remote URL via `repository_state.py`'s new
   helper (import it alongside `RepositoryState` at line 26), check against
   `(cfg or GitConfig.load()).allowed_remote_urls`, and raise/return a rejection if
   unauthorized.
3. Include the redacted resolved URL in the function's return value in a way the
   caller's audit path can surface it (see Non-blocking evidence gap below — the
   exact audit-record wiring is `RepositoryState.audit()`, Stage 8, which currently
   only includes `RepositoryState` fields, not the format function's return value
   content beyond the raw string result).

### Method
- Add an optional `cfg: GitConfig | None = None` parameter to both functions
  (test-injectable; `None` → `GitConfig.load()` internally) rather than a required
  parameter, so the existing call sites in `git_server.py`
  (`format_pull(state, pull_req)` / `format_push(state, push_req)`, lines 342/353)
  continue to work unchanged (Compatibility).
- Reuse `repository_state.py`'s new `_resolve_remote_url`/`_redact_remote_url`
  helpers (that row) rather than duplicating URL-parsing logic here.

### Details
- `format_pull(state: RepositoryState, req: GitPullRequest, cfg: GitConfig | None =
  None) -> str`: after existing docstring (line 161), before line 164's
  `state._repo.git.fetch(...)`, add: resolve `req.remote`'s URL, redact for any
  later logging, and reject (`raise GitServiceError(...)`, consistent with this
  file's existing `GitServiceError` import at line 15) if the redacted-comparison
  normalized URL is not in `(cfg or GitConfig.load()).allowed_remote_urls`.
- `format_push(state: RepositoryState, req: GitPushRequest, cfg: GitConfig | None =
  None) -> str`: same pattern before line 187's `state._repo.git.push(...)`.
- `REQ-008` (audit): since `format_pull`/`format_push` currently only return a
  formatted string (no structured metadata channel back to `RepositoryState.audit()`
  at Stage 8), and `audit()` lives in a different target file's scope
  (`repository_state.py`), the redacted remote identity's inclusion in the actual
  audit record requires a coordinated field addition there. Classify as
  **Non-blocking**: this row adds the redacted value to the raised
  `GitServiceError` message on rejection (satisfying "resolved remote identity...
  for pull/push operations" for the rejection path) and documents, in a code
  comment, that full audit-record inclusion on the *success* path depends on
  `repository_state.py`'s `audit()` gaining a corresponding field — flag this
  coordination point for confirmation at implementation time rather than silently
  narrowing `REQ-008`'s scope.

## Compatibility considerations
- New `cfg` parameter is optional with a safe default (`None` → `GitConfig.load()`)
  — no existing call site (`git_server.py`'s two call sites) requires any change.
- `GitConfig.load()` being called per-invocation (rather than once at server startup)
  re-reads and re-parses `config/git_mcp_server.toml` on every `pull`/`push` call
  when `cfg` is not injected — acceptable for a low-frequency write operation, but
  worth noting as a minor perf cost versus the module-level `_cfg` singleton pattern
  `git_server.py` uses for every other config read.

## Security considerations
- Rejection must occur strictly before the mutating `git.fetch`/`git.pull`/`git.push`
  call — an authorization check written after the mutating call would defeat
  `REQ-004`'s purpose entirely.
- The redacted (not raw) URL must be the only form that ever reaches the raised
  exception message, log call, or eventual audit field — per `REQ-003`.

## Rollback considerations
- Reverting this row alone (after `repository_state.py`'s helper row lands) simply
  restores the pre-existing unauthorized-remote behavior — no partial-state hazard,
  since the check is inserted, not replacing existing logic.

## Validation plan
- `uv run pytest tests/mcp_servers/git/test_format_output.py -v` (existing suite).
- `uv run pytest tests/mcp_servers/git/test_git_security_compliance.py -v` (new
  remote-authorization/credential-redaction cases, a separate row, exercise this
  file's behavior through the live HTTP path).
- `uv run ruff check`, `uv run mypy`, `uv run bandit -r scripts/mcp_servers/git/ -c
  pyproject.toml`, `PYTHONPATH=scripts uv run lint-imports`.

## Completion criteria
- `format_pull`/`format_push` reject an unauthorized/unknown/changed remote before
  any mutating GitPython call, with the redacted remote identity present in the
  rejection message; `AC-1`, `AC-2`, `AC-3` hold for both functions.

## Out of scope
- The resolve/normalize/redact helper implementation, the per-repo lock, and the
  HEAD-recheck (`repository_state.py`, a separate row); the `GitConfig` field
  definition (`git_models.py`, a separate row); full success-path audit-record
  wiring beyond this row's rejection-path inclusion (flagged as Non-blocking above).

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
- **Requirement ID**: REQ-004, REQ-008, REQ-009
- **Source issue**: issues/20260902-144912_gitremote_define_remote_authorization_and_concurrency_control.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260904-192131_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260905-204502
- **Related target files**: scripts/mcp_servers/git/format_output.py
