# Implementation Procedure: Add configurable timeouts to git-mcp pull/pull output helpers

## Goal

Give `pull`/`push` a configurable timeout so a slow or hung network operation fails fast instead of blocking indefinitely (`REQ-003`: add timeouts to push and pull).

## Scope

Modify `format_output.py` only: `format_pull()` and `format_push()`.

- In-Scope: add a configurable timeout parameter to `format_pull()`/`format_push()`; wire it from `GitConfig`; document where enforcement occurs.
- Out-of-Scope: the `asyncio.to_thread()` dispatch (`git_service.py`, `REQ-001`); the lock (`repository_state.py`, `REQ-002`); tests; docs.

## Assumptions

- `format_pull()` (line 179) and `format_push()` (line 201) are **synchronous** functions invoked via the `op()` lambda inside `WriteProtectionPipeline.run()`.
- The blocking calls are `state._repo.git.pull(*pull_args)` (line 192) and `state._repo.git.push(req.remote, "--", branch)` (line 208).
- The timeout value should be configurable via `GitConfig` (plan assumption: e.g. `push_timeout`/`pull_timeout`).

## Design decisions

- **Add an optional `timeout` parameter** to `format_pull()`/`format_push()` threaded from `GitConfig`.
- **Enforce the timeout at the async boundary.** Because these functions are synchronous, `asyncio.wait_for()` cannot wrap them directly; the timeout must be applied where the op runs on the event loop — i.e. around the `asyncio.to_thread(...)` call in `git_service.py` (`REQ-001`). This file exposes the parameter; enforcement lives one layer up.

## Alternatives considered

- **Make `format_pull`/`format_push` async.** More invasive (signature change propagates through `git_service.py`'s `op` lambdas and `repository_state.py`'s `op` typing); rejected in favour of a sync function + boundary enforcement.

## Implementation

### Target file

`scripts/mcp_servers/git/format_output.py`

### Procedure

1. Add an optional `timeout: float | None = None` parameter to `format_pull(state, req, cfg)` and `format_push(state, req, cfg)`.
2. Read the timeout from `cfg` (e.g. `cfg.push_timeout` / `cfg.pull_timeout`) when the caller does not pass one explicitly.
3. Keep the blocking GitPython call as-is (`state._repo.git.pull/push`); the timeout is enforced by the caller around the `to_thread` dispatch (see `REQ-001` in `git_service.py`). Document this dependency in the function's docstring.
4. On timeout, a clear `TimeoutError` is raised by `asyncio.wait_for` at the enforcement site; surface it unchanged.

### Method

Signature extension + config wiring; enforcement delegated to the async call site.

### Details

- **Needs confirmation (Plan Gap):** the plan says "use `asyncio.wait_for()`" inside `format_output.py`, but `format_pull`/`format_push` are synchronous and `asyncio.wait_for()` requires an awaitable. The timeout therefore cannot be enforced *inside* these sync functions; it must be enforced at the async `to_thread` boundary in `git_service.py`. This file's responsibility is exposing the timeout parameter and documenting where enforcement occurs. Confirm the intended enforcement site with the implementer.
- `GitConfig` shape (whether `push_timeout`/`pull_timeout` already exist) must be verified before referencing it.

## Compatibility considerations

- Backwards compatible: `timeout` defaults to `None` (no enforcement) so existing callers are unaffected until configured.
- Depends on `REQ-001` for actual enforcement timing.

## Security considerations

- No security impact; a timeout is a reliability/availability control, not an access control.

## Rollback considerations

- Remove the `timeout` parameter and revert to the original signatures.

## Validation plan

- Integration test with a slow fake Git operation asserting a `TimeoutError` is raised past the configured timeout (`tests/mcp_servers/git/test_repository_state.py`).
- ruff and mypy pass.

## Completion criteria

- `format_pull()`/`format_push()` accept a configurable timeout and a slow operation raises `TimeoutError` when exceeded.
- Lint/type checks pass.

## Out of scope

- Dispatch (`git_service.py`), lock (`repository_state.py`), tests, docs.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add timeout param to format_pull/format_push | Pending | — | — | See Plan Gap re: enforcement site |
| 2 | Add/update tests per Validation plan | Pending | — | — | REQ-003 timeout integration test |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | ruff, mypy, targeted pytest |
| 4 | Update documentation, if in scope | Pending | — | — | N/A: out of scope for this file |

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
- **Requirement ID**: `REQ-003` — add timeouts to push and pull
- **Source issue**: `issues/done/20261007-154016_gitasync01_move-git-mcp-blocking-operations-off-the-event-loop.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261008-160546_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261008-234721
- **Related target files**: `scripts/mcp_servers/git/format_output.py`
