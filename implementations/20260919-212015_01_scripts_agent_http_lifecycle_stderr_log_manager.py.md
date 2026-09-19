## Goal
Add a public API to `StderrLogManager` for the server-key -> log-path mapping it
already owns internally (`_log_paths`), so `HttpServerLifecycleManager` and
`ShutdownCoordinator` (implemented in Steps 02/03 of this pass) can stop reading and
mutating that private dict directly (`REQ-001`).

## Scope
- In scope: add `get_log_path(server_key: str) -> str | None`,
  `forget(server_key: str) -> None`, and `clear() -> None` public methods to
  `StderrLogManager`.
- Out of scope: any change to `open_log`, `read_tail`, `rotate_log`, or the private
  `_log_paths`/`_log_files` attributes' internal representation. No change to callers
  (`http_lifecycle.py`, `http_lifecycle_shutdown_coordinator.py`) — those are handled
  in Steps 02/03 of this pass.

## Assumptions
- Method names `get_log_path`/`forget`/`clear` were chosen in the Plan's Design
  section (`plans/20260919-211529_plan.md` > Assumptions) to map 1:1 onto the three
  existing access patterns (single read, single pop, bulk clear) with no other
  naming convention in this file to conflict with — confirmed by reading the full
  file: only `open_log`, `read_tail`, `rotate_log` are currently public.

## Design decisions
- `get_log_path` returns `self._log_paths.get(server_key)` (returns `None` for an
  unknown key, matching the existing `.get(server_key, "")`-then-empty-string pattern
  callers currently use, but as `None` — callers already null-check equivalent
  results, see Step 02).
- `forget` does `self._log_paths.pop(server_key, None)` — a no-op if the key is
  absent, matching every current `.pop(server_key, None)` call site being replaced.
- `clear` does `self._log_paths.clear()` — matches the one bulk-clear call site in
  `ShutdownCoordinator.shutdown_all()` being replaced in Step 03.
- None of the three methods touch `_log_files` (the open file-handle dict) — that
  remains a separate concern already owned entirely within this class.

## Alternatives considered
- Expose a read-only `Mapping` view of `_log_paths` instead of a `get`/`forget`/`clear`
  method triplet: rejected because it would require callers to change their
  read/pop/clear call shape more than a method-per-pattern replacement does, and would
  not give `forget`/`clear` a clear owner-side implementation point for any future
  validation (e.g. logging on removal).

## Implementation
### Target file
scripts/agent/http_lifecycle_stderr_log_manager.py

### Procedure
1. Add `get_log_path`, `forget`, and `clear` methods to the `StderrLogManager` class,
   placed after `rotate_log` (the last existing method).
2. Add a one-line docstring to each, consistent with the existing methods' docstring
   style in this file.

### Method
Insert after `rotate_log` (currently ending at line 117):

```python
def get_log_path(self, server_key: str) -> str | None:
    """Return the tracked stderr log path for a server key, or None if untracked."""
    return self._log_paths.get(server_key)

def forget(self, server_key: str) -> None:
    """Remove the tracked stderr log path for a server key, if present."""
    self._log_paths.pop(server_key, None)

def clear(self) -> None:
    """Remove all tracked stderr log paths."""
    self._log_paths.clear()
```

### Details
- No change to `__init__`, `open_log`, `read_tail`, or `rotate_log`.
- No new imports required (uses only the existing `dict` built-in methods).
- Type signature matches this file's existing `from __future__ import annotations`
  style (no `Optional[...]`, use `str | None`).

## Compatibility considerations
Purely additive — three new public methods on a class with no existing external
subclasses (confirmed: `rg "class.*StderrLogManager" scripts/` shows only this
definition; `rg "StderrLogManager(" scripts/` shows only direct instantiation in
`http_lifecycle.py`). No existing caller or test is affected by this step alone —
Steps 02/03 route their existing call sites through the new methods.

## Security considerations
N/A: no new I/O, no new external input handled — these methods only read/mutate an
in-memory `dict` already populated exclusively from `open_log`'s existing,
already-reviewed path-construction logic.

## Rollback considerations
Revert this file's diff; the three new methods have no other file depending on them
until Steps 02/03 of this pass are also applied (see `plans/20260919-211529_plan.md`
Implementation steps, Phase 1 precedes Phase 2). No data migration, no config
change, no restart-order dependency.

## Validation plan
- New unit tests for the three methods are added in Step 04 of this pass
  (`tests/agent/test_http_lifecycle_stderr_log_manager.py`) — this document's own
  Validation plan is limited to this file's own correctness.
- `uv run mypy scripts/agent/http_lifecycle_stderr_log_manager.py` — confirm the new
  methods type-check cleanly.
- `uv run ruff check scripts/agent/http_lifecycle_stderr_log_manager.py` — confirm
  formatting/lint compliance.
- `uv run pytest tests/agent/test_http_lifecycle_stderr_log_manager.py -v` — confirm
  no regression in the file's existing tests.

## Completion criteria
- `StderrLogManager.get_log_path`, `.forget`, and `.clear` exist with the signatures
  above.
- `uv run mypy scripts/agent/http_lifecycle_stderr_log_manager.py` passes with no new
  errors.
- Existing tests in `tests/agent/test_http_lifecycle_stderr_log_manager.py` still pass
  unmodified (this step does not touch that test file — see Step 04).

## Out of scope
- Fixing the pre-existing bandit B108 finding at this file's line 46 (hardcoded `/tmp`
  path) — confirmed pre-existing and unrelated during this Plan's Step 5 baseline scan
  (`plans/20260919-211529_plan.md` Scope > Out-of-Scope).
- Any change to `open_log`, `read_tail`, or `rotate_log`.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20260920-070828 | 20260920-070828 | Added get_log_path/forget/clear to StderrLogManager. Step 2.5 stale_detector.py CLI produced no output (no __main__ entry point); direct library call mis-extracted target file as '/tmp' due to a Target-file regex bug requiring backtick-wrapping — manually re-verified target file/symbols/line numbers against current source instead (all matched, not stale). |
| 2 | Add or update tests per Validation plan | Completed | 20260920-070828 | 20260920-070828 | Targeted tests/agent/test_http_lifecycle_stderr_log_manager.py: 16 passed. Full suite (pytest --testmon tests/): 7710 passed, 119 failed, 22 skipped — all 119 failures pre-existing/unrelated (eventbus, mcp_servers/git|shell|mdq, shared config validation); none in tests/agent/; this change is purely additive (12 lines, 3 new methods, no existing code touched). |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20260920-070843 | 20260920-070843 | ruff format/check clean; pyright clean (0 errors); mypy blocked by pre-existing unrelated module-collision error in scripts/shared/tool_constants.py (reproduces on scripts/ and on an untouched file — not caused by this change); lint-imports pre-existing unrelated shared->agent boundary violation (shared.production_config_validator); bandit pre-existing B108 at line 46 (documented in Out of scope). |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20260920-070843 | 20260920-070843 | N/A: no docs/00_index.md task-scope mapping for scripts/agent/http_lifecycle_stderr_log_manager.py (rg confirms no reference); Out of scope section already stated no documentation update in scope. |

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
- **Requirement ID**: `REQ-001` (consolidate stderr-log-path ownership into `StderrLogManager`)
- **Source issue**: issues/20260919-210241_refactor_003_deduplicate-stderr-path-tracking-and-cleanup-logic-in-http_lifecycle.py.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260919-211529_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260919-212015
- **Related target files**: scripts/agent/http_lifecycle_stderr_log_manager.py