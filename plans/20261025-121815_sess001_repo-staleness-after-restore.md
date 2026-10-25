# sess001 — SessionMessageRepository stays bound to pre-restore session_id

**Source issue**: `issues/20261025-115501_sess001_repo-staleness-after-restore.md`

> Path B (bug with tests + docs): full analysis — Historical, Architecture,
> Dependency, Operational. Verification evidence: repro test
> `/tmp/opencode/test_repo_staleness.py` fails exactly as the issue predicts
> (`rows = [(101, 'in original session'), (101, 'turn in restored session')]`).
> Confidence for root cause: High. Full suite baseline at verification time:
> 10082 passed, 9 skipped (green).

## Goal

Make message persistence attribute writes to the Agent's *current* `session_id`, so
that after `restore_session()` new turns are written to the restored session, `/history`
reads the same session the writer writes to, and the post-restore
`UNIQUE constraint failed: sessions.session_id` no longer occurs.

## Priority

P2 (Medium) — data misattribution with explicit failure at read time; no crash,
recoverable, but silently corrupts session attribution after every
restore-then-persist sequence in an existing REPL session.

## Scope

In scope:
- `scripts/agent/session.py` — staleness-aware `_message_repo` binding.
- `scripts/agent/session_message_repo.py` — read-only `session_id` accessor.
- `tests/agent/test_session_restore.py` — real-DB regression test.
- `docs/23_agent/agent_09_01_data-layer-session-db.md`,
  `docs/23_agent/agent_04_01_state-and-persistence-state-model.md`.

Out of scope:
- Historical data cleanup/backfill for already-misattributed rows.
- `_turn_counter` staleness after restore (Unknowns U-002).
- The `_ensure_session_created` exception-handling rewrite (sess002's scope).
- `purge_old_sessions` boundary (sess005's scope).

## Background

Audit finding (sess001). The REPL creates one `Agent` per user session;
`/restore` reassigns `ctx.session.session_id` on the live `Agent`. Message
persistence uses a lazily created `SessionMessageRepository` that binds the id at
construction. Code reading confirmed the mechanism; a real-DB repro test confirmed
the failure end to end (2026-10-25). `session_persister.py` and `DiagnosticStore`
read the live `session_id` per call, so the issue's Unresolved Question about them is
resolved: they inherit the fix.

## Problem

`Agent._message_repo` is a lazy singleton bound forever to the `session_id` value at
first message access. `restore_session()` reassigns `session_id` (and resets
`_session_created`) but never rebinds the cached repo. Consequences after a restore in
a session that already persisted messages:

- new user/assistant rows are attributed to the original (pre-restore) session id;
- the restored session is never updated, so `/history` (which builds a fresh repo via
  `load_messages()`) shows only the old snapshot — the new turn is invisible;
- the next turn's `_ensure_session_created()` tries to re-insert the original id and
  fails with `UNIQUE constraint failed: sessions.session_id`, logged and swallowed;
- mock-based unit tests cannot catch this because mocks do not enforce DB constraints.

## Reason for Change

Verified defect: repro test writes `('in original session', 101)` and
`('turn in restored session', 101)` against a real SQLite DB — the restored
session's messages are attributed to the wrong session. Every
restore-then-persist sequence in an existing REPL session misattributes data and
degrades `/history`.

## Implementation Intent

Make the facade own its binding: `_message_repo` becomes a staleness-aware lazy
cache that rebuilds when the cached repo's bound id differs from the Agent's current
`session_id`, while keeping direct assignment (`agent._message_repo = repo`) working.
Expose the repo's binding through a read-only `session_id` property (single source of
truth). `session_restore.py` stays a pure state reassignment — no service reaches into
`Agent` internals.

## Requirements

| ID | Requirement | Priority | Target |
|---|---|---|---|
| REQ-001 | The message repo used by `Agent` must be bound to the *current* `session_id` at use time; a change of `session_id` must not leave a stale repo behind. | must | scripts/agent/session.py, scripts/agent/session_message_repo.py |
| REQ-002 | After `restore_session()`, subsequent message persistence must be attributed to the restored session id, with a real-DB regression test. | must | tests/agent/test_session_restore.py |
| REQ-003 | `start()` behavior and `Agent` public API unchanged; direct assignment `agent._message_repo = repo` keeps working; existing mock-based session/restore tests pass unchanged. | must | scripts/agent/session.py |
| REQ-004 | Restore remains non-destructive: both original and restored session rows survive. | must | scripts/agent/services/session_restore.py (verify only) |
| REQ-005 | Documentation updated for persistence binding semantics and the state model. | should | docs/23_agent/agent_09_01_data-layer-session-db.md, docs/23_agent/agent_04_01_state-and-persistence-state-model.md |

## Implementation Target Files

> One row per directly affected file. "Contract / Exports to Keep" freezes the public contract.

| File | Action | Contract / Exports to Keep |
|---|---|---|
| scripts/agent/session.py | modify | Public API unchanged: `Agent.start(...)`, `ChatSessionProtocol`, `build_chat_session`, `set_chat_session_factory`, `_ensure_session_created` behavior (session-row creation on first persistence). `_message_repo` remains a settable attribute (getter rebuilds only when the cached repo's `session_id` differs from `self.session_id`). `agent.session.SQLiteHelper` remains the import name used for session-row creation. |
| scripts/agent/session_message_repo.py | modify | Constructor signature `SessionMessageRepository(session_id, ...)` unchanged; all query methods unchanged; add read-only `session_id` property. |
| tests/agent/test_session_restore.py | modify | Existing mock tests unchanged; add real-DB regression tests (see Tests). |
| docs/23_agent/agent_09_01_data-layer-session-db.md | modify | Document persistence binding semantics: the message repo follows the Agent's current `session_id`. |
| docs/23_agent/agent_04_01_state-and-persistence-state-model.md | modify | Document `session_id` mutability across restore and its effect on persistence attribution. |

Not edited (verified no change needed): `scripts/agent/services/session_restore.py`,
`scripts/agent/session_persister.py`, `docs/41_db/db_04_api_and_operations-module-boundaries-and-helper.md`
(mapped by `docs/00_index.md` "Session / DB persistence", but module boundaries are
untouched).

## Reference Files

- `scripts/agent/session.py` — `_get_or_create_message_repo()` lazy cache + setter; `start()`.
- `scripts/agent/session_message_repo.py` — repo binds `_session_id` in `__init__` (documented read-only).
- `scripts/agent/services/session_restore.py:105` — `restore_session()` reassignment site; "history/stats preserved exactly" must not change.
- `scripts/agent/session_persister.py` — reads `ctx.session.session_id` per call (inherits fix).
- `tests/agent/test_history_compression_consistency.py` — compatibility constraint: assigns `s._message_repo = SessionMessageRepository(session_id=1)` (line 112), patches `agent.session.SQLiteHelper` (line 107); fixture pattern (in-memory sqlite + `_SCHEMA_SQL`) reused for the new regression test.
- `tests/agent/test_session_restore.py` — existing mock-based restore tests.
- `docs/00_index.md` — task-scope mapping "Session / DB persistence".

## Acceptance Criteria

| ID | Criterion | Maps to |
|---|---|---|
| AC-001 | Repro scenario passes: post-restore persistence attributed to the restored id; reader and writer use the same session. | REQ-001, REQ-002 |
| AC-002 | Post-restore turn no longer triggers the swallowed `UNIQUE constraint failed` (clean `_ensure_session_created`). | REQ-001 |
| AC-003 | Both session rows present after restore (non-destructive). | REQ-004 |
| AC-004 | `test_history_compression_consistency.py` and all `tests/agent/test_session*.py` tests pass without modification. | REQ-003 |
| AC-005 | `lint-imports` 6 kept / 0 broken; bandit 0 new findings on changed files. | REQ-001 |
| AC-006 | Both docs updated; docs checker passes. | REQ-005 |

## Tests

New regression test (real schema, deterministic):
- `tests/agent/test_session_restore.py::test_persist_after_restore_attributes_to_restored_id`
  — in-memory `sqlite3` + `_SCHEMA_SQL`, both `agent.session.SQLiteHelper` and
  `agent.session_message_repo.SQLiteHelper` patched (pattern from
  `test_history_compression_consistency.py`): persist turn in session A →
  `restore_session()` to new id B → persist turn → assert the new `session_messages`
  row has `session_id = B`; assert both `sessions` rows (A, B) exist; assert no
  `IntegrityError` path on the post-restore turn.

Characterization guards (must stay green, unmodified):
- `tests/agent/test_session_restore.py` existing mock tests;
- `tests/agent/test_history_compression_consistency.py` injection pattern;
- `tests/agent/test_session_message_repo.py`;
- `tests/agent/test_regression_diagnostic_persist.py`.

Execution order: targeted run (Phase 1 gate) → selected set `tests/agent/test_session*.py`
(186 tests, green at baseline) → full suite.

## Documentation Impact

- `docs/23_agent/agent_09_01_data-layer-session-db.md` — session persistence
  attribution semantics (repo follows current `session_id`).
- `docs/23_agent/agent_04_01_state-and-persistence-state-model.md` — state model:
  `session_id` is mutable on restore; persistence follows the current value.
- `db_04` from the `docs/00_index.md` "Session / DB persistence" mapping: verified no
  change needed (no module-boundary change).
- English per `skills/DESIGN.md` output-language rule; docs checker must pass.

## Assumptions

| Assumption | Confidence | Verification |
|---|---|---|
| In-memory sqlite + `_SCHEMA_SQL` fixture is the accepted pattern for repo-level DB tests. | High | Already used by `test_history_compression_consistency.py`. |
| No code outside `scripts/agent/` reads `Agent._message_repo`. | High | grep across `scripts/` and `tests/`: only `session.py` internals + the compression test. |
| `Agent.session_id` only changes via `start()` and `session_restore.py`. | Medium | grep assignments to `session_id` during Phase 1. |

## Unknowns

| ID | Question | Confidence | Blocking | Verification Steps |
|---|---|---|---|---|
| U-001 | Whether production DB already holds misattributed rows from past restore-then-persist sequences (issue claims one row at `session_id = 101`; not independently queried). | Low | No (fix stands regardless) | Read-only query on `/opt/llm/db/session.sqlite` for orphans in `session_messages` vs `sessions` before any backfill decision; out of scope for this plan. |
| U-002 | `_turn_counter` staleness after restore (counter carried from the original session; `restore_session()` does not reset it). Issue lists it as related but out of scope. | High (confirmed by code reading) | No | File a follow-up issue if desired. |
| U-003 | Do desktop/agent-web paths ever call `restore_session()` on an `Agent` with an already-bound repo, or always fresh instances? | Medium | No | Inspect `agent_web/` restore wiring during Phase 1; fix covers both designs regardless. |

## Affected areas

- `agent.session.Agent` persistence path: `_persist_turn`, `_ensure_session_created`,
  `_reload_session_messages`, `_trim_messages` — all use `self._message_repo`.
- `agent.services.session_restore` — trigger site (unmodified under chosen design).
- Inherited, no extra fix: `agent.session_persister` (per-call `ctx.session.session_id`),
  `DiagnosticStore.save_diagnostic` (per-call id argument).
- Importers of `agent.session` (churn/dependency analysis): `agent.web_runtime`
  (17 commits/30d on `agent_09_01` doc side, `agent_web/main.py` hot path),
  `agent.repl`, `agent.desktop` — behavior-compatible change; no signature changes.
- DB `/opt/llm/db/session.sqlite` not locked by a live process at audit time (fuser:
  none). No service restart, no migration, no env/config change required.
- Ordering dependency: sess002 (`unreachable-sqlite-error-fallback`) touches the same
  `_ensure_session_created()` region of `session.py`; sess001 lands first, sess002
  rebases onto it.

## Design

Chosen approach — staleness-aware lazy cache in `Agent` + read-only `session_id`
property on the repo:

- `session_message_repo.py`: add `session_id` read-only `@property` returning
  `_session_id` (constructor docstring already declares it a read-only reference;
  makes the repo's binding the single source of truth).
- `session.py`: `_message_repo` getter rebuilds the cached repo when
  `cached.session_id != self.session_id`; setter stores an injected repo verbatim
  (preserves the compression-test injection pattern). `start()` keeps its existing
  repo assignment — after it, cached binding equals current id, so the getter is a
  no-op. First persistence call after `restore_session()` detects the mismatch and
  rebuilds for the restored id.
- `session_restore.py`: no change. Rebinding is owned by the facade; the service does
  not touch `Agent` internals (Architecture analysis: a service mutating facade
  internals is a layering smell; the issue's alternative "rebind from
  session_restore" was rejected for this reason).

Rejected alternatives:
- Rebind from `session_restore.py` — couples service to private internals.
- Fresh repo on every property access — discards injected repos, breaks
  `test_history_compression_consistency.py:112`.
- Pass `session_id` per call into repo methods — API churn across all repo callers,
  disproportionate for this bug.

## Implementation steps

> Phase-gated: each phase leaves the suite green.

1. Phase 1 — accessor + staleness-aware cache (`session_message_repo.py`,
   `session.py`): add `session_id` property; convert `_message_repo` lazy attribute to
   get/set property with id-mismatch rebuild. Gate:
   `uv run pytest tests/agent/test_session_restore.py tests/agent/test_history_compression_consistency.py tests/agent/test_session_message_repo.py -x -q`.
2. Phase 2 — regression test in `tests/agent/test_session_restore.py` (real-DB, red
   before Phase 1 if run first; green after; evidence recorded).
3. Phase 3 — docs: update the two docs named in Implementation Target Files.
4. Phase 4 — full validation sequence (`rules/toolchain.md`), then single commit.

## Validation plan

- Targeted: `uv run pytest tests/agent/test_session_restore.py
  tests/agent/test_history_compression_consistency.py tests/agent/test_session_message_repo.py
  tests/agent/test_regression_diagnostic_persist.py -x -q`.
- Selected set: `uv run pytest tests/agent/test_session*.py` (186 tests, green at
  baseline).
- Full: `uv run pytest tests/ -q` (baseline 10082 passed / 9 skipped) +
  `rules/toolchain.md` sequence; `lint-imports` must stay 6 kept / 0 broken.
- Static: bandit on the two changed source files — baseline 0 findings each, must
  stay 0 (whole-`scripts/` pre-existing 8 Medium / 38 High out of scope; radon cc on
  `session.py` all grade A pre-change).
- Repro closure: `/tmp/opencode/test_repo_staleness.py` must pass after the fix.

## Risks

| Risk | Severity | Likelihood | Mitigation |
|---|---|---|---|
| Breaking `_message_repo` direct-assignment tests (`test_history_compression_consistency.py:112`) when converting to a property. | High | Medium | REQ-003 freezes assignability; setter stores injected repo verbatim; Phase 1 gate runs that test. |
| Injected repo whose bound id differs from current `session_id` gets silently rebuilt (mock semantics change). | Medium | Low | Only observed usage injects a matching id; characterization test guards. |
| Collision with sess002 in the `_ensure_session_created()` region of `session.py`. | Medium | High | Ordering: sess001 lands first; sess002 rebases. |
| Name confusion between `SessionMessageRepository.session_id` (property) and `Agent.session_id` (plain attribute). | Low | Low | Property only on the repo; docstring states read-only binding; docs updated. |

## Execution Status

| Item | Status |
|---|---|
| Plan | Frozen |
| Phase 1 (accessor + staleness cache) | Pending |
| Phase 2 (regression test) | Pending |
| Phase 3 (docs) | Pending |
| Phase 4 (full validation) | Pending |

## Traceability

- Implementation step 1 → REQ-001, REQ-003 (gate run enforces the injection constraint).
- Implementation step 2 → REQ-002, REQ-004; encodes AC-001..AC-003.
- Implementation step 3 → REQ-005 (AC-006).
- Implementation step 4 → AC-004, AC-005.

Requirement traceability:

| Requirement | Test / Evidence | Acceptance Criterion |
|---|---|---|
| REQ-001 | Phase 1 gate + repro closure | AC-001, AC-002, AC-005 |
| REQ-002 | `test_persist_after_restore_attributes_to_restored_id` | AC-001 |
| REQ-003 | Unmodified `test_session*.py` 186-test set + compression test | AC-004 |
| REQ-004 | Regression test row-survival assertions | AC-003 |
| REQ-005 | Docs diff + docs checker | AC-006 |
