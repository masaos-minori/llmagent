# sess001 — SessionMessageRepository stays bound to pre-restore session_id

**Source issue**: `issues/20261025-115501_sess001_repo-staleness-after-restore.md`

> Path B (bug with tests + docs): full analysis — Historical, Architecture,
> Dependency, Operational. Verification evidence: repro test
> `/tmp/opencode/test_repo_staleness.py` fails exactly as the issue predicts
> (`rows = [(101, 'in original session'), (101, 'turn in restored session')]`).
> Confidence for root cause: High. Full suite baseline at verification time:
> 10082 passed, 9 skipped (green).

## Verification findings (re-verified against HEAD 05f555ee0, 2026-10-25)

Confirmed:
- Core defect reproduces on HEAD: repro test `/tmp/opencode/test_repo_staleness.py`
  fails with `{100: [], 101: ['in original session', 'turn in restored session']}`.
- `AgentSession._message_repo` lazy property + setter exist at
  `scripts/agent/session.py:35-45`; `start()` rebinds at lines 151-153.
- `restore_session()` reassignment site is `scripts/agent/services/session_restore.py:97`
  (not 105); it is the only `session.session_id` reassignment outside `start()`.
- `session_persister.py` reads `ctx.session.session_id` per call (lines 62/70, 178/197)
  and `save_diagnostic` passes the id per call — both inherit the fix.
- Gate test set green: 86 passed. `tests/agent/test_session*.py` = 4 files / 78 tests
  (the "186 tests" figure was wrong). `.importlinter` has 6 contracts.
- Only session-row INSERT site is `AgentSession.start()` (session.py:137).

Corrected (claims that did not match HEAD):
- The facade class is `AgentSession`, not `Agent`.
- `_ensure_session_created()`, `_persist_turn()`, `_get_or_create_message_repo()`,
  `_reload_session_messages()`, `_trim_messages()`, `_session_created` do not exist in
  the codebase; the claimed post-restore `UNIQUE constraint failed` path has no code
  basis and is removed (AC-002 rewritten).
- `_message_repo` is already a get/set property in HEAD; the remaining work is adding
  the id-mismatch rebuild to the existing getter.
- `SessionMessageRepository.session_id` is a public attribute assigned in `__init__`
  (line 48), not a private `_session_id`; a read-only property would rename public
  API for no benefit. The getter compares the public attribute directly;
  `session_message_repo.py` moves to the not-edited list.
- `agent.web_runtime`, `agent_web/main.py`, `agent.desktop` do not exist; verified
  importers of `agent.session` are `agent/context.py`,
  `agent/commands/session_title.py`, `agent/repl_input_loop.py` plus tests.
- `ChatSessionProtocol`, `build_chat_session`, `set_chat_session_factory` do not exist;
  contract row rewritten to the real `AgentSession` public API.

## Goal

Make message persistence attribute writes to the AgentSession's *current*
`session_id`, so that after `restore_session()` new turns are written to the restored
session, `/history` and `/session list` read the same session the writer writes to.

## Priority

P2 (Medium) — data misattribution with explicit failure at read time; no crash,
recoverable, but silently corrupts session attribution after every
restore-then-persist sequence in an existing REPL session.

## Scope

In scope:
- `scripts/agent/session.py` — staleness-aware `_message_repo` binding.
- `tests/agent/test_session_restore.py` — real-DB regression test.
- `docs/23_agent/agent_09_01_data-layer-session-db.md`,
  `docs/23_agent/agent_04_01_state-and-persistence-state-model.md`.

Out of scope:
- Historical data cleanup/backfill for already-misattributed rows.
- `_turn_counter` staleness after restore (Unknowns U-002).
- The `_ensure_session_created` exception-handling rewrite (sess002's scope).
- `purge_old_sessions` boundary (sess005's scope).

## Background

Audit finding (sess001). The REPL creates one `AgentSession` per user session;
`/restore` reassigns `ctx.session.session_id` on the live `AgentSession`
(`session_restore.py:97`). Message persistence uses a lazily created
`SessionMessageRepository` that binds the id at construction. Code reading confirmed
the mechanism; a real-DB repro test confirmed the failure end to end (2026-10-25).
`session_persister.py` and `DiagnosticStore` read the live `session_id` per call, so
the issue's Unresolved Question about them is resolved: they inherit the fix.

## Problem

`AgentSession._message_repo` (session.py:35-45) is a lazy singleton: its getter builds
the repo once and keeps it forever, bound to the `session_id` value at first message
access. `restore_session()` reassigns `session_id` but never rebinds the cached repo.
Consequences after a restore in a session that already persisted messages:

- new user/assistant rows are attributed to the original (pre-restore) session id;
- the restored session is never updated, so `/history` shows only the snapshot that
  was loaded at restore time and `/session list` message counts for the restored
  session miss the new turns;
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
| REQ-001 | The message repo used by `AgentSession` must be bound to the *current* `session_id` at use time; a change of `session_id` must not leave a stale repo behind. | must | scripts/agent/session.py |
| REQ-002 | After `restore_session()`, subsequent message persistence must be attributed to the restored session id, with a real-DB regression test. | must | tests/agent/test_session_restore.py |
| REQ-003 | `start()` behavior and `AgentSession` public API unchanged; direct assignment `agent._message_repo = repo` keeps working; existing mock-based session/restore tests pass unchanged. | must | scripts/agent/session.py |
| REQ-004 | Restore remains non-destructive: both original and restored session rows survive. | must | scripts/agent/services/session_restore.py (verify only) |
| REQ-005 | Documentation updated for persistence binding semantics and the state model. | should | docs/23_agent/agent_09_01_data-layer-session-db.md, docs/23_agent/agent_04_01_state-and-persistence-state-model.md |

## Implementation Target Files

> One row per directly affected file. "Contract / Exports to Keep" freezes the public contract.

| File | Action | Contract / Exports to Keep |
|---|---|---|
| scripts/agent/session.py | modify | Public API unchanged: `AgentSession.start`, `save`, `save_many`, `replace_messages`, `save_diagnostic`, `fetch_messages`, `count_messages_up_to`, `set_title`, `list_sessions`, `undo_last_turn`, `delete_session`, `skipped_no_session_count`, `skipped_invalid_role_count`. `_message_repo` remains a settable attribute (existing getter/setter at lines 35-45; getter rebuilds only when the cached repo's `session_id` differs from `self.session_id`). `start()` keeps creating the session row and rebinding the repo. `agent.session.SQLiteHelper` remains the import name used for session-row creation. |
| tests/agent/test_session_restore.py | modify | Existing mock tests unchanged; add real-DB regression tests (see Tests). |
| docs/23_agent/agent_09_01_data-layer-session-db.md | modify | Document persistence binding semantics: the message repo follows the AgentSession's current `session_id`. |
| docs/23_agent/agent_04_01_state-and-persistence-state-model.md | modify | Document `session_id` mutability across restore and its effect on persistence attribution. |

Not edited (verified no change needed): `scripts/agent/session_message_repo.py`
(`session_id` is a public attribute assigned in `__init__` line 48; the staleness check
compares it directly — renaming it to a private attribute plus a read-only property
would churn public API for no benefit),
`scripts/agent/services/session_restore.py`,
`scripts/agent/session_persister.py`, `docs/41_db/db_04_api_and_operations-module-boundaries-and-helper.md`
(mapped by `docs/00_index.md` "Session / DB persistence", but module boundaries are
untouched).

## Reference Files

- `scripts/agent/session.py:35-45` — `_message_repo` lazy property (getter + setter);
  `start()` lines 124-153 (session-row INSERT at 137, repo rebind at 151-153).
- `scripts/agent/session_message_repo.py` — repo binds public `self.session_id` in
  `__init__` (line 48); `save`/`save_many` use the bound id per call.
- `scripts/agent/services/session_restore.py:97` — `restore_session()` reassignment
  site; "history/stats preserved exactly" must not change.
- `scripts/agent/session_persister.py` — reads `ctx.session.session_id` per call
  (lines 62/70, 178/197) (inherits fix).
- `tests/agent/test_history_compression_consistency.py` — compatibility constraint:
  `s.session_id = 1` then `s._message_repo = SessionMessageRepository(session_id=1)`
  (lines 110-112), patches `agent.session.SQLiteHelper` and
  `agent.session_message_repo.SQLiteHelper` (lines 107-108); fixture pattern
  (in-memory sqlite + `_SCHEMA_SQL`) reused for the new regression test.
- `tests/agent/test_session_restore.py` — existing mock-based restore tests.
- `docs/00_index.md` — task-scope mapping "Session / DB persistence".

## Acceptance Criteria

| ID | Criterion | Maps to |
|---|---|---|
| AC-001 | Repro scenario passes: post-restore persistence attributed to the restored id; reader and writer use the same session. | REQ-001, REQ-002 |
| AC-002 | Post-restore turn completes without `Persistence skipped` warnings, role-count counter increments, or sqlite3 errors. | REQ-001 |
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
  reassign `session_id` to restored id B (as `restore_session()` does) → persist turn
  → assert the new `messages` row has `session_id = B`; assert both `sessions` rows
  (A, B) exist; assert no `IntegrityError` path on the post-restore turn.

Characterization guards (must stay green, unmodified):
- `tests/agent/test_session_restore.py` existing mock tests;
- `tests/agent/test_history_compression_consistency.py` injection pattern;
- `tests/agent/test_session_message_repo.py`;
- `tests/agent/test_regression_diagnostic_persist.py`.

Execution order: targeted run (Phase 1 gate) → selected set `tests/agent/test_session*.py`
(4 files, 78 tests, green at baseline) → full suite.

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
| No code outside `scripts/agent/session.py` internals reads `_message_repo` except the compression test injection. | High | Re-verified 2026-10-25: grep across `scripts/` and `tests/` — only `session.py` internals + `test_history_compression_consistency.py:112`. |
| `AgentSession.session_id` only changes via `start()` (session.py:148) and `session_restore.py:97`. | High | Re-verified 2026-10-25: grep of `session.session_id =` assignments — only these two production sites. |

## Unknowns

| ID | Question | Confidence | Blocking | Verification Steps |
|---|---|---|---|---|
| U-001 | Whether production DB already holds misattributed rows from past restore-then-persist sequences (issue claims one row at `session_id = 101`; not independently queried). | Low | No (fix stands regardless) | Read-only query on `/opt/llm/db/session.sqlite` for orphans in `messages` vs `sessions` before any backfill decision; out of scope for this plan. |
| U-002 | Turn-counter staleness after restore: the orchestrator keeps its own turn counter (`tests/integration/test_orchestrator_integration.py:226`), and `restore_session()` only calls `reset_session_stats(ctx)`. Whether that reset covers the counter is out of scope here. | Medium | No | File a follow-up issue if desired. |
| U-003 | ~~Do desktop/agent-web paths call `restore_session()` on a live session?~~ Resolved 2026-10-25: `agent.web_runtime`, `agent_web/`, `agent.desktop` do not exist in `scripts/`. Verified importers of `agent.session`: `agent/context.py`, `agent/commands/session_title.py`, `agent/repl_input_loop.py` plus tests. | High | No | None needed. |

## Affected areas

- `agent.session.AgentSession` persistence path: `save`, `save_many`,
  `replace_messages`, `fetch_messages`, `count_messages_up_to`,
  `skipped_no_session_count`, `skipped_invalid_role_count` — all route through
  `self._message_repo`.
- `agent.services.session_restore` — trigger site (unmodified under chosen design).
- Inherited, no extra fix: `agent.session_persister` (per-call `ctx.session.session_id`),
  `DiagnosticStore.save_diagnostic` (per-call id argument).
- Importers of `agent.session` (verified 2026-10-25): `agent/context.py` (owns
  `AgentSession()` at line 318), `agent/commands/session_title.py`,
  `agent/repl_input_loop.py` — behavior-compatible change; no signature changes.
- DB `/opt/llm/db/session.sqlite` not locked by a live process at audit time (fuser:
  none). No service restart, no migration, no env/config change required.
- Ordering dependency: sess002 (`unreachable-sqlite-error-fallback`) claimed the same
  `session.py` region; its claimed target (`_ensure_session_created`) does not exist —
  sess002 must be re-verified against HEAD before landing; sess001 lands first.

## Design

Chosen approach — staleness-aware rebuild in the existing `_message_repo` getter:

- `session.py`: the getter (already present at lines 35-45) rebuilds the cached repo
  when `self._repo is not None and self._repo.session_id != self.session_id`; the
  setter stores an injected repo verbatim (preserves the compression-test injection
  pattern). `start()` keeps its existing repo assignment — after it, cached binding
  equals current id, so the getter is a no-op. First persistence call after
  `restore_session()` detects the mismatch and rebuilds for the restored id.
- `session_message_repo.py`: no change. `session_id` stays a public attribute; the
  getter reads it for the comparison.
- `session_restore.py`: no change. Rebinding is owned by the facade; the service does
  not touch `AgentSession` internals (Architecture analysis: a service mutating facade
  internals is a layering smell; the issue's alternative "rebind from
  session_restore" was rejected for this reason).

Rejected alternatives:
- Rebind from `session_restore.py` — couples service to private internals.
- Fresh repo on every property access — discards injected repos, breaks
  `test_history_compression_consistency.py:112`.
- Rename `SessionMessageRepository.session_id` to private + read-only property —
  verified 2026-10-25: the attribute is already public; renaming churns public API
  for no behavioral benefit.
- Pass `session_id` per call into repo methods — API churn across all repo callers,
  disproportionate for this bug.

## Implementation steps

> Phase-gated: each phase leaves the suite green.

1. Phase 1 — staleness-aware getter (`session.py`): add the id-mismatch rebuild to the
   existing `_message_repo` getter (getter/setter already exist in HEAD; no repo
   change). Gate:
   `uv run pytest tests/agent/test_session_restore.py tests/agent/test_history_compression_consistency.py tests/agent/test_session_message_repo.py -x -q`.
2. Phase 2 — regression test in `tests/agent/test_session_restore.py` (real-DB, red
   before Phase 1 if run first; green after; evidence recorded).
3. Phase 3 — docs: update the two docs named in Implementation Target Files.
4. Phase 4 — full validation sequence (`rules/toolchain.md`), then single commit.

## Validation plan

- Targeted: `uv run pytest tests/agent/test_session_restore.py
  tests/agent/test_history_compression_consistency.py tests/agent/test_session_message_repo.py
  tests/agent/test_regression_diagnostic_persist.py -x -q`.
- Selected set: `uv run pytest tests/agent/test_session_memory_boundary.py
  tests/agent/test_session_message_repo.py tests/agent/test_session_persister.py
  tests/agent/test_session_restore.py` (4 files, 78 tests, green at baseline).
- Full: `uv run pytest tests/ -q` (plan-generation baseline claimed 10082 passed /
  9 skipped; not re-run in this verification pass) +
  `rules/toolchain.md` sequence; `lint-imports` must stay 6 kept / 0 broken
  (.importlinter contract count confirmed: 6).
- Static: bandit on the changed source file (`session.py`) — baseline 0 findings,
  must stay 0 (whole-`scripts/` pre-existing 8 Medium / 38 High out of scope; radon cc on
  `session.py` all grade A pre-change).
- Repro closure: `/tmp/opencode/test_repo_staleness.py` must pass after the fix
  (confirmed failing at HEAD 05f555ee0 before the fix).

## Risks

| Risk | Severity | Likelihood | Mitigation |
|---|---|---|---|
| Injected repo whose bound id differs from current `session_id` gets silently rebuilt (mock semantics change). | Medium | Low | Only observed usage (`test_history_compression_consistency.py:110-112`) injects a matching id (`session_id = 1` set before injection); characterization test guards. |
| Collision with sess002 in `session.py`. | Medium | Medium | sess002's original target region (`_ensure_session_created`) does not exist; re-verify sess002 against HEAD before landing; sess001 lands first. |
| Getter rebuild triggers when `session_id` is None and an injected repo has a non-None id. | Low | Low | Rebuild condition `self._repo is not None and self._repo.session_id != self.session_id` matches the compression-test pattern exactly (ids equal there). |

## Execution Status

Table structure, status/type vocabulary, and general guidance: see
`templates/execution-status.md`.

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Phase 1: staleness-aware `_message_repo` getter rebuild (`scripts/agent/session.py`) | In Progress | — | — | re-verified against HEAD 05f555ee0 2026-10-25; corrections reflected in this plan |
| 2 | Phase 2: real-DB regression test (`tests/agent/test_session_restore.py`) | In Progress | — | — | `REQ-002`, `REQ-004` |
| 3 | Phase 3: docs updates (two `docs/23_agent/` files) | In Progress | — | — | `REQ-005` |
| 4 | Phase 4: full validation sequence, single commit | Pending | — | — | gate only; modifies no file |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| implementations/20261025-132053_01_scripts_agent_session.py.md | 1 | Procedure | Pending | — | — |
| implementations/20261025-132053_02_tests_agent_test_session_restore.py.md | 2 | Procedure | Pending | — | — |
| implementations/20261025-132053_03_docs_23_agent_agent_09_01_data-layer-session-db.md.md | 3 | Procedure | Pending | — | — |
| implementations/20261025-132053_04_docs_23_agent_agent_04_01_state-and-persistence-state-model.md.md | 3 | Procedure | Pending | — | — |

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
| REQ-003 | Unmodified `test_session*.py` 78-test set + compression test | AC-004 |
| REQ-004 | Regression test row-survival assertions | AC-003 |
| REQ-005 | Docs diff + docs checker | AC-006 |