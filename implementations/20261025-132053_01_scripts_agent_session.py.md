# Implementation Procedure — scripts/agent/session.py

## Goal

Make `AgentSession._message_repo` staleness-aware so message persistence always
binds the *current* `session_id` (REQ-001, message repo must not outlive a
`session_id` change): rebuild the cached repo when its bound id no longer matches
the facade's `session_id`.

## Scope

- Modify the `_message_repo` getter in `scripts/agent/session.py` (lines 35-41) to
  rebuild on id mismatch.
- No other file is modified by this procedure (regression test is
  `implementations/20261025-132053_02_tests_agent_test_session_restore.py.md`).

## Assumptions

- `AgentSession.session_id` is only reassigned at `session.py:148` (`start()`) and
  `scripts/agent/services/session_restore.py:97` (verified 2026-10-25 against HEAD
  05f555ee0).
- `SessionMessageRepository.session_id` is a public attribute assigned in `__init__`
  (`session_message_repo.py:48`); reading it for the comparison requires no repo
  change (verified).
- Caveat (Needs confirmation, non-blocking): after a rebuild the
  `stat_skipped_no_session` / `stat_skipped_invalid_role` counters restart at 0 on the
  new repo. `skipped_no_session_count` / `skipped_invalid_role_count` therefore
  reflect the *live* repo only; this matches the issue's requirement that the counters
  "refer to the live repo" and is documented by the docs rows (03/04).

## Design decisions

- Facade owns the binding: the getter is the single rebuild point; `session_restore.py`
  stays a pure state reassignment (layering rule from the Plan's Architecture
  analysis — a service must not reach into facade internals).
- Lazy rebuild on first access: no eager rebind hook in `restore_session()`; the first
  persistence call after the id change pays the rebuild.

## Alternatives considered

- Rebind from `session_restore.py` — rejected: couples a service to facade internals.
- Fresh repo on every property access — rejected: discards injected repos, breaks
  `tests/agent/test_history_compression_consistency.py:112`.
- Rename repo `session_id` to private + read-only property — rejected (verification
  finding): the attribute is already public; renaming churns public API for no
  benefit.

## Implementation
### Target file
`scripts/agent/session.py`

### Procedure
Extend the existing `_message_repo` property getter (lines 35-41) so the lazy cache
is rebuilt not only when `self._repo is None` but also when the cached repo's bound
`session_id` differs from `self.session_id`.

### Method
Change the getter body's condition from:

```python
if self._repo is None:
```

to:

```python
if self._repo is None or self._repo.session_id != self.session_id:
```

keeping the existing construction call (`SessionMessageRepository(self.session_id,
strict_mode=self._strict_mode)`) and the `return self._repo` line unchanged.

### Details
- The class-level `_repo: SessionMessageRepository | None = None` (line 33) and the
  `@_message_repo.setter` (lines 43-45) stay exactly as they are; the setter must
  continue to store an injected repo verbatim (compression-test injection pattern).
- `start()` (lines 124-153) is untouched: its repo assignment at lines 151-153 makes
  cached id equal current id, so the getter is a no-op afterwards.
- Update the getter's docstring/comment to state the rebuild-on-mismatch semantics.
- No signature, import, or public-method changes; `agent.session.SQLiteHelper` remains
  the import name for session-row creation.

## Compatibility considerations

- `tests/agent/test_history_compression_consistency.py:110-112` sets
  `s.session_id = 1` before injecting `SessionMessageRepository(session_id=1)`; ids
  match, so the injected repo survives (characterization gate).
- Mock-based tests in `tests/agent/test_session_restore.py` do not touch the real
  property and pass unchanged.
- `session_persister.py` and `DiagnosticStore` read the id per call and inherit the
  fix without modification.
- Counter-reset-on-rebuild caveat: see Assumptions.

## Security considerations

N/A: no new input handling, no privilege or data-boundary change; the change only
routes writes to the correct existing session row.

## Rollback considerations

Revert the single commit; the change is one condition in one getter with no schema or
data migration.

## Validation plan

- Phase 1 gate: `uv run pytest tests/agent/test_session_restore.py
  tests/agent/test_history_compression_consistency.py tests/agent/test_session_message_repo.py -x -q`.
- Selected set: `tests/agent/test_session_memory_boundary.py`,
  `tests/agent/test_session_message_repo.py`, `tests/agent/test_session_persister.py`,
  `tests/agent/test_session_restore.py` (4 files, 78 tests green at baseline) +
  `tests/agent/test_history_compression_consistency.py`,
  `tests/agent/test_regression_diagnostic_persist.py`.
- Repro closure: `/tmp/opencode/test_repo_staleness.py` must pass after the change
  (confirmed failing before).
- Full sequence per `rules/toolchain.md`; `lint-imports` stays 6 kept / 0 broken;
  bandit/ruff/mypy clean on the changed file.

## Completion criteria

- Post-restore `save`/`save_many` write under the restored `session_id`
  (AC-001: repro passes; AC-002: no skipped-save warnings, counter increments, or
  sqlite3 errors on the post-restore turn).
- All characterization tests pass unmodified (AC-004); static checks report no new
  findings (AC-005).

## Out of Scope

- The real-DB regression test (procedure 02).
- Documentation updates (procedures 03, 04).
- Backfill/cleanup of already-misattributed historical rows; turn-counter staleness
  (plan U-002).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add the id-mismatch rebuild to the `_message_repo` getter | Pending | — | — | |
| 2 | Run the Phase 1 gate test set | Pending | — | — | characterization only; new tests live in procedure 02 |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Confirm repro closure: `/tmp/opencode/test_repo_staleness.py` passes | Pending | — | — | |

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
- **Requirement ID**: REQ-001 (message repo bound to the current `session_id` at use time)
- **Source issue**: `issues/done/20261025-115501_sess001_repo-staleness-after-restore.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261025-121815_sess001_repo-staleness-after-restore.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261025-132053
- **Related target files**: scripts/agent/session.py
