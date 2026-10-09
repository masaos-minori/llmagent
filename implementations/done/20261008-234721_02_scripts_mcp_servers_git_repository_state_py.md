# Implementation Procedure: Replace the per-repo git-mcp write lock with an event-loop-safe lock

## Goal

Replace the per-repository write lock with an event-loop-safe lock so concurrent writes are serialised without risking deadlock or a total event-loop stall (`REQ-002`: replace `threading.Lock` with `asyncio.Lock`).

## Scope

Modify `repository_state.py` only: `_repo_locks`, `_get_repo_lock()`, and the lock acquisition inside `WriteProtectionPipeline.run()`.

- In-Scope: `dict[str, threading.Lock]` → `dict[str, asyncio.Lock]`; `_get_repo_lock()` returns `asyncio.Lock`; add `import asyncio` if absent.
- Out-of-Scope: the call site that wraps `run()` in `asyncio.to_thread()` (`git_service.py`, `REQ-001`); timeouts (`format_output.py`, `REQ-003`); tests; docs.

## Assumptions

- `_repo_locks` is module-level state keyed by canonical repo path (`repository_state.py:37`); `_get_repo_lock(path)` caches one lock per path (`repository_state.py:41`).
- The lock is held only around the pipeline body (precondition → execution → postcondition), never across an `await` in normal operation.

## Design decisions

- **Change the declared type** `_repo_locks: dict[str, threading.Lock]` → `dict[str, asyncio.Lock]` and make `_get_repo_lock()` construct `asyncio.Lock()` instances.
- **Keep the acquisition site unchanged structurally** — the lock is still acquired around the pipeline body; only its type changes (matches plan decision detail #4).

## Alternatives considered

- **Keep `threading.Lock` and rely on worker-thread execution.** Viable only if `REQ-001` always runs `run()` in a worker thread; but the plan explicitly requires an `asyncio.Lock`, so this is rejected as it leaves the stated requirement unmet.

## Implementation

### Target file

`scripts/mcp_servers/git/repository_state.py`

### Procedure

1. Ensure `import asyncio` is present (currently only `import threading` at line 15).
2. Change the module-level declaration (line 37): `_repo_locks: dict[str, threading.Lock] = {}` → `_repo_locks: dict[str, asyncio.Lock] = {}`.
3. Update `_get_repo_lock()` (line 41) to create `asyncio.Lock()` instead of `threading.Lock()`, and update its return annotation.
4. Verify every acquisition of the per-repo lock (inside `WriteProtectionPipeline.run()`, around line 360) still works with the new type.

### Method

Type + constructor swap on the per-repo lock registry.

### Details

- **Needs confirmation (Plan Gap):** `asyncio.Lock` is bound to the running event loop and **cannot** be acquired from a worker thread. If `REQ-001` moves `pipeline.run()` into `asyncio.to_thread()` (`git_service.py`), the lock is acquired inside that worker thread and this will raise `got Future attached to a different event loop`. Coordinate with the `git_service.py` change: either keep `threading.Lock` for in-thread serialization, or acquire the `asyncio.Lock` at the async level in `_run_tool`. Do not acquire `asyncio.Lock` from the worker thread.
- `_registry_guard` (module-level, guards the `_repo_locks` cache) — confirm whether it should stay a `threading.Lock` (fast dict-guard) or also move to async; do not change it unless the serialization model changes.

## Compatibility considerations

- Behavioural outcome (per-repo mutual exclusion) is preserved; only the lock primitive changes.
- Directly coupled with `REQ-001`: the two changes must be consistent about *which thread* acquires the lock. Implement together or gate verification on both.

## Security considerations

- No change to access control or write-protection outcomes; the lock only serialises writers.

## Rollback considerations

- Restore `threading.Lock` in the two sites and remove `import asyncio`.

## Validation plan

- Unit test asserting `_get_repo_lock()` returns an `asyncio.Lock` instance (`tests/mcp_servers/git/test_repository_state.py`).
- ruff and mypy pass.

## Completion criteria

- `_repo_locks` / `_get_repo_lock()` use `asyncio.Lock`; no `threading.Lock` is acquired from async code paths.
- The unit test and lint/type checks pass.

## Out of scope

- Call-site dispatch (`git_service.py`, `REQ-001`), timeouts, tests, docs.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Replace threading.Lock with asyncio.Lock in _repo_locks/_get_repo_lock | Pending | — | — | See Plan Gap re: acquisition thread |
| 2 | Add/update tests per Validation plan | Pending | — | — | REQ-002 lock-type unit test |
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
- **Requirement ID**: `REQ-002` — replace `threading.Lock` with `asyncio.Lock`
- **Source issue**: `issues/done/20261007-154016_gitasync01_move-git-mcp-blocking-operations-off-the-event-loop.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261008-160546_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261008-234721
- **Related target files**: `scripts/mcp_servers/git/repository_state.py`
