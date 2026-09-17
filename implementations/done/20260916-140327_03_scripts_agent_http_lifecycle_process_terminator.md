## Goal

Delete `ProcessTerminator.terminate()` — confirmed zero callers anywhere in `scripts/`/`tests/`. Keep `terminate_with_timeout()` as the sole public termination method.

## Scope

- Delete the `terminate()` method from `ProcessTerminator` class.
- Update the module docstring to reflect that only `terminate_with_timeout()` is the public termination method.

## Assumptions

- `rg` confirms all `.terminate(` matches are either `subprocess.Popen.terminate()` or the unrelated `terminate_method()` local variable inside `terminate_with_timeout()` — none reference `ProcessTerminator.terminate()`.
- Only `terminate_with_timeout()` (L125-217) is ever invoked as a caller target.

## Design decisions

- Use `git rm` or direct deletion — the method has zero callers so no migration is needed.
- Do not deprecate first — dead code removal is cleaner than adding a deprecated marker.

## Alternatives considered

- Deprecating `terminate()` first and removing later — rejected because there are zero callers; deprecation adds unnecessary churn.

## Implementation
### Target file

`scripts/agent/http_lifecycle_process_terminator.py`

### Procedure

1. Delete the `terminate()` method (L36-92) from `ProcessTerminator` class.
2. Update the module docstring to state that only `terminate_with_timeout()` is the public termination method.

### Method

Current `terminate()` method (L36-92):
- Sends SIGTERM to process group via `os.killpg(pgid, signal.SIGTERM)`.
- Waits up to `timeout` seconds for process exit.
- Escalates to SIGKILL if timeout elapses.

This logic overlaps significantly with `terminate_with_timeout()` (L125-217), which also performs SIGTERM → SIGKILL escalation but with additional fallback paths when pgid is unavailable. Since `terminate_with_timeout()` subsumes all functionality of `terminate()` plus handles edge cases (missing pgid, ProcessLookupError during SIGTERM), keeping both is redundant.

Required changes:
1. Remove lines L36-92 entirely (the `terminate` method definition through its closing indentation).
2. Update the module docstring (L1-6): change "Owns terminate-then-kill escalation logic currently inline in HttpServerLifecycleManager.start()." to "Owns terminate-then-kill escalation logic via `terminate_with_timeout()`."

### Details

After deletion, the remaining `ProcessTerminator` class will have two methods:
- `__init__()` — constructor (L25-34)
- `wait_exited()` — wait for process exit (L94-123)
- `terminate_with_timeout()` — primary termination method (L125-216)

The class docstring should remain unchanged — it describes the class's responsibility, not individual methods.

## Compatibility considerations

- No external callers exist for `terminate()` — confirmed by `rg` across `scripts/`/`tests/`.
- Internal callers within `terminate_with_timeout()` at L173-L178 and L186-L191 reference `getattr(proc, "terminate", None)` — this is `subprocess.Popen.terminate()`, NOT `ProcessTerminator.terminate()`. These references are correct and must not be changed.

## Security considerations

- No security impact — removing unused code does not introduce vulnerabilities.
- The `# nosec B603` suppressions in `terminate_with_timeout()` remain valid.

## Rollback considerations

- If `terminate()` is found to have a hidden caller after deletion, restore it from git history.
- The deletion is safe to revert since no behavior changes are introduced.

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `http_lifecycle_process_terminator.py` | Unit (existing regression) | `uv run pytest tests/agent/test_http_lifecycle_process_terminator.py -q` | No regression from `terminate()` deletion |
| `http_lifecycle_process_terminator.py` | Static analysis | `uv run ruff check scripts/agent/http_lifecycle_process_terminator.py` | Clean |
| `http_lifecycle_process_terminator.py` | Type check | `uv run mypy scripts/agent/http_lifecycle_process_terminator.py` | Pass (no new regressions) |

## Completion criteria

- `terminate()` method is deleted; `terminate_with_timeout()` remains as the sole public termination method.
- `uv run ruff check scripts/agent/http_lifecycle_process_terminator.py` passes clean.
- `uv run mypy scripts/agent/http_lifecycle_process_terminator.py` passes (no new regressions vs pre-existing errors).
- `uv run pytest tests/agent/test_http_lifecycle_process_terminator.py -q` passes.

## Out of scope

- Adding a 3-state enum return type for `terminate_with_timeout()` — tracked as UNK-01, explicitly out of scope per the Issue.
- Modifying `terminate_with_timeout()`'s behavior — only `terminate()` deletion is in scope.
- Updating `HttpServerLifecycleManager` imports — no import changes needed since `terminate()` was never imported externally.

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
- **Requirement ID**: REQ-007
- **Source issue**: issues/20260915-102515_refactor_http_lifecycle_module_split.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260916-140327_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260916-140327
- **Related target files**: scripts/agent/http_lifecycle_process_terminator.py
