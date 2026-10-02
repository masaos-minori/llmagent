# Implementation Procedure: repl.py — remove redundant subprocess termination on startup failure

## Goal

Remove the `hasattr`-based subprocess collection and the redundant termination loop from
`AgentREPL.run()`'s startup-failure handler in `scripts/agent/repl.py`, relying solely on
`StartupOrchestrator.run()`'s internal `lifecycle.shutdown_all()` for subprocess cleanup on
startup failure.

## Scope

In scope: delete the `all_procs` collection (the `hasattr` introspection) and the `for proc
in all_procs:` termination loop from the `except Exception` block in `run()`, replacing them
with a fatal message followed immediately by `raise`. Keep the surrounding `try/except/finally`
structure and the `finally` block (`await self._shutdown.close_resources()`) unchanged.

Out of scope: changing how subprocesses are spawned or health-checked; refactoring the normal
REPL shutdown path (`ResourceShutdownCoordinator`); modifying `scripts/agent/startup.py`
(reference-only); rewriting the failure-path test in `tests/agent/test_repl.py` (companion
document, seq 02).

## Assumptions

- `lifecycle.shutdown_all()` terminates every spawned subprocess (confirmed by
  `tests/agent/test_http_lifecycle_shutdown_coordinator.py`, which calls `terminator(proc)`
  on each).
- The local variable `_spawned_subprocesses` in `repl.py` is always empty on the exception
  path, because `startup.run()` has not returned yet when the `except` runs.
- No subclass overrides of `AgentREPL.run()` depend on the current exception-handling
  behavior.
- Removing the loop leaves `return (cmds, orchestrator, spawned_subprocesses)` intact, so the
  success-path return contract is preserved.

## Design decisions

- Single authoritative shutdown path: rely on `StartupOrchestrator.run()`'s `shutdown_all()`
  rather than a second introspection-based backstop. `shutdown_all()` catches
  OSError/TimeoutError per process and continues, so it will not raise mid-loop.
- Minimal, structure-preserving edit: remove only the fragile `hasattr` collection and the
  redundant loop; retain the fatal-message-and-raise shape and the existing `finally` block so
  control flow and resource-close ordering are unchanged.
- No new symbol, abstraction, or interface change (Path A: ≤ 3 files).

## Alternatives considered

Option (b) — have `startup.run()` propagate the process list reliably and terminate there once.
Rejected in favor of option (a) by owner confirmation during issue-to-plan Step 8; `startup.py`
stays out of scope and is reference-only.

## Implementation

### Target file

`scripts/agent/repl.py`

### Procedure

Replace the body of the `except Exception as e:` block in `AgentREPL.run()` (current lines
126-134) with a fatal message followed immediately by `raise`, deleting the `all_procs`
collection and the termination loop. Leave the `try` (line 124) and the `finally` block
(lines 135-136) untouched.

Before:

```python
        except Exception as e:
            self._view.write_fatal(f"Startup failed: {e}")
            all_procs = _spawned_subprocesses
            if hasattr(startup, "_spawned_subprocesses"):
                all_procs = list(all_procs) + list(startup._spawned_subprocesses)
            for proc in all_procs:
                if proc.poll() is None:
                    proc.terminate()
            raise
        finally:
            await self._shutdown.close_resources()
```

After:

```python
        except Exception as e:
            self._view.write_fatal(f"Startup failed: {e}")
            raise
        finally:
            await self._shutdown.close_resources()
```

### Method

1. Open `scripts/agent/repl.py`; locate `async def run()` (currently line 110) and its
   `try/except/finally` (lines 124-136).
2. Delete lines 128-133: the `all_procs = _spawned_subprocesses` assignment, the
   `if hasattr(startup, "_spawned_subprocesses"):` block, and the `for proc in all_procs:`
   termination loop.
3. Retain line 127 (`self._view.write_fatal(...)`) and line 134 (`raise`), plus the `finally`
   block.
4. Confirm the resulting block reads exactly the "After" snippet above.

### Details

- Requirements: REQ-001 (remove `hasattr` introspection + termination loop),
  REQ-002 (each subprocess terminated exactly once via `shutdown_all()`).
- Evidence (verified against current source): `hasattr` at line 129; termination loop at
  lines 131-133. `startup.run()` calls `lifecycle.shutdown_all()` on its own exception path at
  `scripts/agent/startup.py:81`, so subprocesses are already dead before this handler runs —
  the loop is provably redundant.
- The local `_spawned_subprocesses` (declared line 123, unpacked line 125) becomes unused on
  this path after removal. Leave the declaration as-is to stay within the frozen scope; do not
  touch line 125 unless a separate follow-up is filed.
- Reference files read (not modified): `scripts/agent/startup.py` (confirms `shutdown_all()`
  at :81), `tests/agent/test_startup_rollback.py`,
  `tests/agent/test_http_lifecycle_shutdown_coordinator.py`.

## Compatibility considerations

- Success-path return contract `(cmds, orchestrator, spawned_subprocesses)` preserved.
- Normal REPL shutdown path (`ResourceShutdownCoordinator`) untouched.
- No caller was found that relied on repl.py's backstop termination specifically rather than
  `shutdown_all()`; if one existed it would be an additional target file (none discovered).

## Security considerations

N/A: no new secrets, credentials, network access, or input handling. Consolidating to a single
authoritative terminator slightly improves the orphan-process posture on the failure path.

## Rollback considerations

Revert the single edit to `repl.py` (restore lines 128-133) via `git checkout scripts/agent/
repl.py` or by reverting the commit. Behavior returns to the pre-change state.

## Validation plan

| Target | Strategy | Command | Expected |
|---|---|---|---|
| scripts/agent/repl.py | Format + lint | `uv run ruff format scripts/agent/repl.py` then `uv run ruff check scripts/agent/repl.py` | Clean (no errors) |
| scripts/agent/repl.py | Type check | `uv run mypy scripts/agent/repl.py` | No new type errors |
| tests/agent/test_startup_rollback.py | Regression (subprocess leak / double-terminate) | `uv run pytest tests/agent/test_startup_rollback.py` | All pass |
| tests/agent/test_repl.py::TestAgentREPLRunSubprocessTermination | Regression (success path only) | `uv run pytest tests/agent/test_repl.py::TestAgentREPLRunSubprocessTermination` | Success-path test passes |

Note: the failure-path assertion rewrite in `tests/agent/test_repl.py` is scoped to the
companion procedure document (seq 02); here we only assert the success-path test still passes.

## Completion criteria

- The `hasattr` block and termination loop are gone from `repl.py`; `rg 'hasattr'
  scripts/agent/repl.py` returns 0 matches (was 1).
- `rg 'shutdown_all' scripts/agent/repl.py` returns 0 matches (termination fully owned by
  `startup.py`).
- `ruff` and `mypy` are clean on the file.
- Existing rollback tests and the success-path test pass.

## Out of scope

- Modifying `scripts/agent/startup.py` (reference only).
- Rewriting the failure-path test in `tests/agent/test_repl.py` (companion document, seq 02).
- Any `docs/*.md` update.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Remove the `hasattr` collection and termination loop from `repl.py`'s startup-failure handler | Completed | 20261002-114635 | 20261002-114635 | Per Implementation > Procedure/Method/Details |
| 2 | Confirm success-path test still passes (failure-path rewrite is companion doc seq 02) | Completed | 20261002-114635 | 20261002-114635 |  |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261002-114635 | 20261002-114635 |  |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20261002-114635 | 20261002-114635 | N/A: no docs in scope |

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
- **Requirement ID**: REQ-001, REQ-002
- **Source issue**: issues/done/20260930-161945_repl001_startup_failure_subprocess_cleanup_hasattr_introspection.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261001-103625_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261002-070533
- **Related target files**: scripts/agent/repl.py