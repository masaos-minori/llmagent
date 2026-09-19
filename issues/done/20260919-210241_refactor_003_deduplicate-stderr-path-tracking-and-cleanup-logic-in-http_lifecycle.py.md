# Deduplicate stderr-path tracking and cleanup logic in http_lifecycle.py

## Priority
Medium

## Summary
`scripts/agent/http_lifecycle.py`'s `HttpServerLifecycleManager` maintains its own
`_stderr_log_paths` dict that duplicates state already owned by
`StderrLogManager._log_paths`, and reaches into that collaborator's private attribute
directly to populate it. The same three-step cleanup sequence (read stderr tail, pop
`_http_procs`, pop `_http_pgids`) is also repeated across multiple branches of
`_create_and_validate_proc` and `_health_poll_until_ready`. Consolidate the duplicated
state and repeated cleanup sequences into single, reusable code paths.

## Background
`http_lifecycle.py` is a composition facade produced by an earlier module-split
refactor (see `issues/done/20260915-102515_refactor_http_lifecycle_module_split.md`)
and most recently had its own dead-code/duplication pass in
`issues/done/20260919-115306_refactor_002_consolidate_remaining_http_lifecycle_duplication_and_dead_code.md`
(commit `8020c683`). That pass removed the unused `ProcessSnapshotProvider` module and
delegated `shutdown_all()` to `ShutdownCoordinator`, but did not touch the
stderr-path duplication or the repeated cleanup blocks identified here.

## Problem
Two independent, evidence-based issues in the current file (confirmed by reading
`scripts/agent/http_lifecycle.py` and `scripts/agent/http_lifecycle_stderr_log_manager.py`,
and by `uv run radon cc scripts/agent/http_lifecycle.py -s -n B`):

1. **Duplicated state / encapsulation break** — `HttpServerLifecycleManager.__init__`
   declares `self._stderr_log_paths: dict[str, str] = {}` (`http_lifecycle.py:87`).
   `_open_stderr_log` (`http_lifecycle.py:90-96`) populates it by reading
   `self._stderr_log_manager._log_paths` — a private attribute of the collaborator
   `StderrLogManager` (`http_lifecycle_stderr_log_manager.py:30`) — instead of using a
   public accessor. The two dicts are then kept in sync manually via five separate
   `.pop(server_key, None)` call sites (`http_lifecycle.py:176, 278, 305, 331, 476`),
   with no single owner of the mapping.
2. **Repeated cleanup blocks** — `_create_and_validate_proc`
   (`http_lifecycle.py:244-336`, radon complexity B(9)) repeats the same
   "close stderr handle, pop `_stderr_files`, pop `_stderr_log_paths`" sequence in
   three separate except/failure branches (lines 275-278, 302-306, 327-334).
   `_health_poll_until_ready` (`http_lifecycle.py:338-423`, radon complexity B(6))
   repeats the same "cleanup resources, pop `_http_procs`, pop `_http_pgids`, build
   `StartupFailure`, raise `HttpStartupError`" sequence across its early-exit,
   shutdown-requested, and timeout branches (lines 372-387, 399-410, 412-423).
   Additionally, `_read_stderr_for_cleanup` (`http_lifecycle.py:167-169`) is a
   pure one-line passthrough to `_read_stderr_tail` (`http_lifecycle.py:98-110`)
   with no added behavior.

## Reason for Change
The duplicated `_stderr_log_paths` state and its five independent pop-sites are a
maintenance risk: a future change that adds or removes a failure path in
`_create_and_validate_proc` or `_health_poll_until_ready` can forget one of the
pop-sites and leave `_stderr_log_paths` out of sync with `StderrLogManager`'s own
bookkeeping, silently corrupting `get_process_info`/`get_process_snapshot` output
(these read `_stderr_log_paths` directly, `http_lifecycle.py:193`) without any test
failure pinpointing the cause. The repeated cleanup-and-raise blocks in
`_health_poll_until_ready` and `_create_and_validate_proc` are the direct cause of
their radon B-grade complexity and make the three failure branches harder to verify
stay behaviorally identical as the file evolves.

## Implementation Intent
Give `StderrLogManager` sole ownership of the server-key → log-path mapping and have
`HttpServerLifecycleManager` read through a public accessor instead of maintaining a
parallel dict — remove `HttpServerLifecycleManager._stderr_log_paths` if the
accessor covers every existing read site, or reduce it to a thin cache with one
clearly-owned invalidation path if a parallel dict is still needed for another reason.
Extract the repeated "read stderr tail, drop tracked process/pgid entries, build and
raise `HttpStartupError`" sequence in `_health_poll_until_ready` into one helper method
used by all three branches, and likewise extract the repeated stderr-handle-and-tracking
cleanup in `_create_and_validate_proc`'s three failure paths into one helper. Remove
`_read_stderr_for_cleanup` and call `_read_stderr_tail` directly at its call site.
Preserve the existing public behavior of `start`, `restart`, `shutdown_all`,
`get_process_info`, `get_process_snapshot`, and `list_processes` exactly — this is an
internal-structure change, not a behavior change.

## Target Files or Areas
- `scripts/agent/http_lifecycle.py`
- `scripts/agent/http_lifecycle_stderr_log_manager.py` (only if a new public accessor
  for `_log_paths` is added there)

## Required Changes
- Add a public accessor on `StderrLogManager` for a server's tracked log path (or
  confirm `get_log_path`/equivalent already suffices) and route
  `HttpServerLifecycleManager` reads through it instead of `_log_paths` direct access.
- Remove or consolidate `HttpServerLifecycleManager._stderr_log_paths` so there is one
  owner of the server-key → log-path mapping; update every current read/pop site
  (`http_lifecycle.py:93, 100, 176, 193, 278, 305, 331, 476`) accordingly.
- Extract the repeated cleanup-and-raise sequence in `_health_poll_until_ready`'s
  early-exit, shutdown-requested, and timeout branches into one private helper.
- Extract the repeated stderr-handle-and-tracking cleanup in
  `_create_and_validate_proc`'s three failure branches into one private helper.
- Remove `_read_stderr_for_cleanup` and call `_read_stderr_tail` directly from
  `_cleanup_server_resources`.

## Constraints
- Preserve the existing `ShutdownCoordinator` integration (`shutdown_all` delegation)
  and `ProcessInfoSnapshot` field contract unchanged — both were finalized in the prior
  `refactor_002` pass.
- Do not change `HttpServerLifecycleManager`'s public method signatures
  (`start`, `restart`, `shutdown_all`, `verify_running`, `verify_running_async`,
  `get_process_info`, `get_process_snapshot`, `list_processes`).

## Acceptance Criteria
- `StderrLogManager._log_paths` is no longer read from outside
  `http_lifecycle_stderr_log_manager.py`.
- `uv run radon cc scripts/agent/http_lifecycle.py -s -n B` reports no B-or-worse
  grade for `_create_and_validate_proc` or `_health_poll_until_ready` (both drop to
  grade A or are restructured such that the extracted helpers carry the complexity
  instead).
- `_read_stderr_for_cleanup` no longer exists as a separate method.
- All existing tests in `tests/agent/test_lifecycle.py`,
  `tests/agent/test_http_lifecycle_integration.py`, and
  `tests/agent/test_http_lifecycle_shutdown_coordinator.py` pass unmodified in intent
  (test bodies may be updated only where they assert against the removed
  `_stderr_log_paths` internal attribute directly, per Testing Expectations below).

## Testing Expectations
- Run the full `rules/toolchain.md` Standard validation sequence (format, lint,
  mypy, `lint-imports`, `ast-grep` constraint checks, bandit, pytest, diff-cover,
  pre-commit) after the change.
- Targeted: `uv run pytest tests/agent/test_lifecycle.py
  tests/agent/test_http_lifecycle_integration.py
  tests/agent/test_http_lifecycle_shutdown_coordinator.py -v`.
- Any test asserting directly against `mgr._http_mgr._stderr_log_paths` or
  `mgr._stderr_log_paths` (e.g. `tests/agent/test_lifecycle.py:455, 483, 832, 1191,
  1197, 1204, 1213`; `tests/agent/test_http_lifecycle_integration.py:225, 233, 442,
  484, 500, 566, 716, 728`) must be updated to assert through the new accessor if the
  attribute is removed or renamed — do not delete the assertion's intent.
- Re-run `uv run radon cc scripts/agent/http_lifecycle.py -s -n B` as part of
  verification (see Acceptance Criteria).

## Documentation Impact
None expected. `docs/05_agent_14_reference-api-generated.md` and
`docs/01_overview-files-03-scripts.md` document `http_lifecycle.py` at the module/class
level only, not at the level of internal private-attribute duplication; no known claim
in either doc references `_stderr_log_paths` or `_read_stderr_for_cleanup`. Re-run
`uv run python tools/check_docs_consistency.py --domain agent` after the change to
confirm no drift was introduced.

## Out of Scope
- The two stale `http_lifecycle_process_snapshot.py` references left in
  `docs/01_overview-files-03-scripts.md:40` and
  `docs/05_agent_14_reference-api-generated.md:77` after that file's deletion in
  `8020c683` — that is a separate documentation-cleanup task, not part of this
  refactor.
- Any change to `http_lifecycle_command_validator.py`, `http_lifecycle_health_checker.py`,
  `http_lifecycle_process_terminator.py`, or `http_lifecycle_shutdown_coordinator.py`
  beyond what a new `StderrLogManager` accessor requires.
- Any behavior change to health-check timing, retry counts, or startup-timeout
  semantics.

## Dependencies
N/A: none

## Unresolved Questions
- Whether `StderrLogManager` should expose the accessor as a single
  `get_log_path(server_key) -> str | None` method or a read-only mapping view —
  left to the implementer's judgment within Implementation Intent's constraint that
  `StderrLogManager` remains sole owner of the mapping.

## AI Implementation Instruction
Read `scripts/agent/http_lifecycle.py` and `scripts/agent/http_lifecycle_stderr_log_manager.py`
in full before editing. Make only the changes listed under Required Changes — do not
touch the other five `http_lifecycle_*.py` modules, `factory.py`, or
`lifecycle_protocol.py` except to update an import if a symbol is removed. Do not
change any public method signature or externally observable behavior (health-poll
timing, exception types/messages in `StartupFailure`, `ProcessInfoSnapshot` field
values). If a test asserts against an internal attribute being removed, update that
test's assertion to use the new accessor rather than deleting the test. Stop and
report back if `StderrLogManager` already exposes a suitable public accessor and no
new one is needed — do not add a redundant one.

## Traceability
- **Workflow phase**: `issue-creator`
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20260919-210241
- **Related target files**: scripts/agent/http_lifecycle.py, scripts/agent/http_lifecycle_stderr_log_manager.py
