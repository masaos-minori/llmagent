# Implementation Procedure: Move the blocking git-mcp write path off the event loop

## Goal

Move the blocking git-mcp write path off the asyncio event loop so `/health` and other read handlers stay responsive during a network `push`/`pull` (`REQ-001`: wrap write operations in `asyncio.to_thread()`).

## Scope

Modify `GitService._run_tool()` in `scripts/mcp_servers/git/git_service.py` only.

- In-Scope: dispatch the write pipeline via `asyncio.to_thread()`; add `import asyncio` if absent; keep read-only tools synchronous.
- Out-of-Scope: modifying `WriteProtectionPipeline` (lives in `repository_state.py`, covered by `REQ-002`); adding timeouts (`format_output.py`, `REQ-003`); tests (`tests/mcp_servers/git/test_repository_state.py`); docs (`docs/22_mcp/mcp_04_05_git.md`, `REQ-004`).

## Assumptions

- `_run_tool` is an `async def` coroutine (currently `scripts/mcp_servers/git/git_service.py:220`) and can `await`.
- `WriteProtectionPipeline.run()` (defined in `repository_state.py:321`) is a synchronous method that runs the mutating Git `op()` inside the per-repo lock; moving the whole call to a worker thread preserves its internal ordering.
- Read-only tools already return via `_wrap_git_op` and need no change.

## Design decisions

- **Wrap the `pipeline.run(...)` call in `await asyncio.to_thread(pipeline.run, ...)`** at the write branch of `_run_tool`. This moves the entire pipeline body (authorization re-check → precondition → execution → postcondition) to a worker thread while keeping the event loop free.
- **Preserve the lock scope unchanged.** The per-repo lock stays around the full pipeline body inside the worker thread; only *where* it is acquired moves off the loop. See Compatibility considerations re: `REQ-002`.
- **Leave read tools untouched.** `_wrap_git_op` for read tools stays synchronous (fast, no network I/O).

## Alternatives considered

- **Make `WriteProtectionPipeline.run()` itself async and `await asyncio.to_thread(op)` inside it.** More invasive (changes a shared class used by every write tool) and would require awaiting from `git_service.py`; rejected in favour of the call-site wrapper, which localises the change to this file.
- **Keep the synchronous `pipeline.run(...)` call.** Rejected — this is the exact event-loop stall the plan removes.

## Implementation

### Target file

`scripts/mcp_servers/git/git_service.py`

### Procedure

1. Ensure `import asyncio` is present at the top of the file (it is not currently imported).
2. In `_run_tool`, locate the write branch (currently `scripts/mcp_servers/git/git_service.py:249-260`), where the code builds `pipeline = WriteProtectionPipeline(state)` and then calls `pipeline_result = pipeline.run(tool_name, lambda: op(state.repo, state), dry_run, self._allow_detached_head, requested_branch=..., protected_branches=..., active_ref=...)` synchronously.
3. Replace the synchronous call with an awaited, thread-dispatched call:
   ```python
   pipeline_result = await asyncio.to_thread(
       pipeline.run,
       tool_name,
       lambda: op(state.repo, state),
       dry_run,
       self._allow_detached_head,
       requested_branch=requested_branch,
       protected_branches=protected_branches,
       active_ref=active_ref,
   )
   ```
4. Do not touch the read branch (`return self._wrap_git_op(...)`, currently line 248).

### Method

Call-site wrapping in the async `_run_tool` coroutine.

### Details

- `WriteProtectionPipeline` and its `run()` method live in `repository_state.py`; this file only *invokes* them. No modification instructions for `repository_state.py` are included here (that is `REQ-002`).
- The `op` lambda (`lambda: op(state.repo, state)`) performs the blocking GitPython call (`format_pull`/`format_push` → `state._repo.git.pull/push`). Wrapping `pipeline.run` in `to_thread` moves that call to a worker thread.
- **Needs confirmation (Plan Gap):** `REQ-001` and `REQ-002` interact on the per-repo lock. Moving `pipeline.run()` into a worker thread means the lock is acquired *inside* that thread. An `asyncio.Lock` cannot be acquired from a worker thread (`got Future attached to a different event loop`). Resolve in the implementation — either keep a `threading.Lock` for in-thread serialization (since `run()` now always runs in a worker thread) or acquire the `asyncio.Lock` at the async level around the `to_thread` call. Do not acquire `asyncio.Lock` from the worker thread.

## Compatibility considerations

- Output is unchanged; only execution location/time shifts. `/health` and read tools remain responsive during a write.
- Cross-file dependency: the lock serialisation contract lives in `repository_state.py` (`REQ-002`). Changing the lock type there must remain compatible with the lock now being acquired inside a worker thread (see the Plan Gap above).

## Security considerations

- No change to the write-protection security model. Stages 1-3 (repo-path validation, write guard, authorization) run before `pipeline.run()` as before; the pipeline body still enforces preconditions/postconditions inside the worker thread.

## Rollback considerations

- Revert the single call-site change back to the synchronous `pipeline.run(...)` assignment and remove the added `import asyncio`.

## Validation plan

- Lint/type: run ruff and mypy over `scripts/mcp_servers/git/`.
- Targeted pytest: an async test with a slow fake Git operation asserting the write path is dispatched via `asyncio.to_thread()` and that `/health` responds concurrently (see `tests/mcp_servers/git/test_repository_state.py`).

## Completion criteria

- The write branch of `_run_tool` awaits `asyncio.to_thread(pipeline.run, ...)`; a blocking push/pull no longer runs on the event loop thread.
- Read tools still return synchronously via `_wrap_git_op`.
- ruff and mypy pass; the REQ-001 async test passes.

## Out of scope

- `repository_state.py` lock change (`REQ-002`), `format_output.py` timeout (`REQ-003`), tests, and docs.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the `asyncio.to_thread()` write dispatch in `_run_tool` | Pending | — | — | See Plan Gap re: lock serialization with REQ-002 |
| 2 | Add/update tests per Validation plan | Pending | — | — | REQ-001 async test in test_repository_state.py |
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
- **Requirement ID**: `REQ-001` — wrap the blocking write path in `asyncio.to_thread()`
- **Source issue**: `issues/done/20261007-154016_gitasync01_move-git-mcp-blocking-operations-off-the-event-loop.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261008-160546_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261008-234721
- **Related target files**: `scripts/mcp_servers/git/git_service.py`
